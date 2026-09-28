#!/usr/bin/env python3
"""
Research Forum Orchestrator
===========================
Runs AI research agents that search literature (OpenAlex), analyze data (KNA),
and critically review each other's findings in a shared forum.

v2.1 (2026-09-25). Every agent run goes through claude_cli.run_claude (pinned
model and effort, per-role tools, isolation, event log, private sidecar,
failure classes) inside a staging run (staging.begin, commit or rollback), so
a failed run leaves no trace in forum/ or knowledge/ and an accepted run keeps
only what its role may write. After an accepted run the orchestrator writes
the post's identity and provenance into its frontmatter. Round and arc
identity are read back from that frontmatter (forum_index), so a round that
stopped partway resumes at its missing roles. Stage 2 mechanisms run only
when their forum_config.stage2 flag is on.

Exit codes: 0 done, 1 a run failed or a check stopped the round (rerun with
--resume to run the missing roles), 75 usage limit (knowledge/arc_status.json
state paused_usage_limit).

Usage:
    python3 run_forum.py                       # 1 round, all agents
    python3 run_forum.py --rounds 3            # 3 rounds of discussion
    python3 run_forum.py --agent scout         # Run only Scout
    python3 run_forum.py --topic "legislative polarization in Korea"
    python3 run_forum.py --resume              # Continue from existing posts
    python3 run_forum.py --dry-run             # Preview prompts only
    python3 run_forum.py --comment "Focus on committee gatekeeping next" --by researcher
    python3 run_forum.py --resume --allow-model-change   # run although the arc's model differs
    python3 run_forum.py --resume --allow-data-change    # run although the KNA data changed mid-arc

Data pin (A1, 2026-09-26). The arc records a fingerprint of the KNA data when
it opens, and every round refuses to run on different data unless
--allow-data-change is passed (recorded). The pinned fingerprint and a ready
data availability sentence are in arc_status.json under data_fingerprint.
Data pitfall flags (A2). After each Analyst post the orchestrator scans the
post's code blocks against knowledge/data_pitfalls.md and shows the matches
to the Critic as 'Data pitfall flags' (flag only).
"""

import argparse
import atexit
import json
import re
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import os
import shutil

import claude_cli
import forum_index
import staging

BASE_DIR = Path(__file__).resolve().parent
FORUM_DIR = BASE_DIR / "forum"
LOGS_DIR = BASE_DIR / "logs"
WORKSPACE_DIR = BASE_DIR / "workspace"
AGENTS_FILE = BASE_DIR / "agents.json"
SUMMARIES_DIR = BASE_DIR / "summaries"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"

# The KNA CLI is found on PATH. This location is added to the agent's PATH
# only when the CLI is not on PATH already.
KNA_CLI_FALLBACK = Path("/usr/local/bin/kna")

AGENT_MESSAGE = ("Execute your research task now. Read the system prompt, query data or literature, "
                 "write your forum post.")

ROUND_ORDER_OVERRIDE = None   # set from --order
EFFORT_OVERRIDE = None        # set from --effort


def load_config():
    """forum_config block of agents.json plus the season number."""
    with open(AGENTS_FILE) as f:
        data = json.load(f)
    cfg = dict(data.get("forum_config", {}))
    cfg["season"] = data.get("season", 1)
    return cfg


def load_agents():
    """Agents in posting order. The order is Scout, Analyst, Critic
    (forum_config.round_order), and --order scout-first states it for a run."""
    with open(AGENTS_FILE) as f:
        data = json.load(f)
    agents = data["agents"]
    order = ROUND_ORDER_OVERRIDE or data.get("forum_config", {}).get("round_order")
    if order:
        by_id = {a["id"]: a for a in agents}
        ordered = [by_id[i] for i in order if i in by_id]
        ordered += [a for a in agents if a["id"] not in order]
        agents = ordered
    return agents


# ==========================================================================
# Small file helpers
# ==========================================================================

def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    if not Path(path).exists():
        return rows
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _norm(s) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip().lower())


def _stage2(cfg: dict, flag: str) -> bool:
    """forum_config.stage2.<flag>, false when absent (D-01)."""
    return bool((cfg.get("stage2") or {}).get(flag, False))


# ==========================================================================
# Arc 2 reflection-commitment guardrails (C2 / C3 / C9).
# Added 2026-04-20 per post_conference_reflection_2026-04-20.md.
# ==========================================================================

TOPIC_GATE_FILE = BASE_DIR / "topic_gate.md"
RETREATS_LEDGER = KNOWLEDGE_DIR / "retreats.jsonl"
ACTIVE_ARC_FILE = KNOWLEDGE_DIR / "active_arc.json"
ARC_STATUS_FILE = KNOWLEDGE_DIR / "arc_status.json"
HUMAN_CONTEXT_FILE = KNOWLEDGE_DIR / "human_context.md"
WAIVERS_FILE = KNOWLEDGE_DIR / "waivers.jsonl"
GATE_EVENTS_FILE = KNOWLEDGE_DIR / "gate_events.jsonl"
GATE_CANDIDATES_FILE = KNOWLEDGE_DIR / "gate_candidates.jsonl"
ARCHIVE_DIR = KNOWLEDGE_DIR / "archive"

GATE_FIELDS = ("seed", "identification", "exclusion_criteria", "prior", "falsifier",
               "decision_rule", "decision_rule_expr", "sesoi", "null_paper", "premise",
               "premise_source", "premise_override", "human_rationale",
               "drafted_by", "signed_by", "signed")

# Gate fields compared with knowledge/gate_candidates.jsonl when an entry says
# the researcher drafted it (M08). null_paper is a yes/no field and would
# match any candidate, so it is left out.
CANDIDATE_MATCH_FIELDS = ("prior", "falsifier", "decision_rule", "sesoi", "premise",
                          "exclusion_criteria", "human_rationale")
CANDIDATE_MATCH_RATIO = 90
CANDIDATE_MIN_WORDS = 5

# Model and CLI of the arcs opened before active_arc.json recorded them,
# reconstructed from session transcripts read on 2026-09-24. It is a record
# only. An arc without a model key is not model-locked.
LEGACY_ARC_PROVENANCE = {
    4: {"model": "claude-fable-5", "claude_code_version": "2.1.241"},
    5: {"model": "claude-fable-5", "claude_code_version": "2.1.241"},
}

# arc_status actions and states that close an arc (run_arc.CLOSED_ACTIONS and
# CLOSED_STATES). A closed arc runs no further rounds, and a researcher note
# written after it waits for the next arc.
ARC_CLOSED_ACTIONS = ("stop", "draft_and_stop", "close_no_paper", "closed_no_paper")
ARC_CLOSED_STATES = ("closed", "closed_no_paper", "draft_blocked")
# arc_status states that hold every run until they are acknowledged
# (run_arc.py --ack-stop): an external write, or a changed researcher-owned file.
ACK_STATES = ("external_write", "researcher_file_changed")


def _parse_gate_entry(entry_text: str) -> dict:
    """Parse one H2 block of topic_gate.md into a dict of its fields.

    A field runs from 'name:' to the next line that starts with a known field
    name, or to the end of the block. Free text may therefore span several
    lines and may itself contain a line such as 'Why: because ...'."""
    names = "|".join(sorted(GATE_FIELDS, key=len, reverse=True))
    start = re.compile(r"^(" + names + r"):[ \t]*", re.MULTILINE | re.IGNORECASE)
    marks = list(start.finditer(entry_text))
    fields = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(entry_text)
        value = re.sub(r"(?m)^---[ \t]*$", "", entry_text[m.end():end])
        fields[m.group(1).lower()] = re.sub(r"\s+", " ", value).strip()
    return fields


# A dry run with --topic previews the arc its gate entry would open, without
# writing active_arc.json (preview_arc). None otherwise.
PREVIEW_ARC = None


def get_active_arc() -> dict:
    """The topic_gate entry that opened the current arc (Season 2), or the
    previewed arc during a dry run with --topic."""
    if PREVIEW_ARC is not None:
        return dict(PREVIEW_ARC)
    if ACTIVE_ARC_FILE.exists():
        try:
            return json.loads(ACTIVE_ARC_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def _arc_number(value):
    """6 from 6, '6', 'arc6' or 'Arc 6'. None when there is no number."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    m = re.search(r"\d+", str(value))
    return int(m.group(0)) if m else None


def _next_arc_number(prev: dict) -> int:
    nums = list(forum_index.LEGACY_ARCS)
    n = _arc_number(prev.get("arc_id", prev.get("arc")))
    if n is not None:
        nums.append(n)
    for m in forum_index.index(forum_dir=FORUM_DIR):
        if isinstance(m.get("arc"), int):
            nums.append(m["arc"])
    return max(nums) + 1


def arc_of_round(round_num: int, arc: dict | None = None):
    """Arc number of a round. From the active arc's start round on it is the
    active arc's number, before that the static legacy table's. None when
    unknown."""
    arc = get_active_arc() if arc is None else arc
    start = _int(arc.get("start_round"))
    if start is not None and round_num >= start:
        v = arc.get("arc", arc.get("arc_id"))
        n = _arc_number(v)
        if n is not None:
            return n
        if v:
            return v
    for num, (first, last) in forum_index.LEGACY_ARCS.items():
        if first <= round_num <= last:
            return num
    return None


def _arc_id(round_num: int, arc: dict | None = None) -> str | None:
    """arc_id string for claude_cli (call budget, transcript folder)."""
    v = arc_of_round(round_num, arc)
    return str(v) if v is not None else None


def _update_arc_status(**kw) -> None:
    """Merge keys into knowledge/arc_status.json (run_arc writes it too)."""
    st = _read_json(ARC_STATUS_FILE)
    st.update(kw)
    st["ts"] = _now()
    ARC_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ARC_STATUS_FILE.write_text(json.dumps(st, ensure_ascii=False, indent=2))


def _log_gate_event(seed: str, start_round, result: str, reason: str = "",
                    fields: dict | None = None) -> None:
    """One row per topic-gate check in knowledge/gate_events.jsonl (M08)."""
    row = {"ts": _now(), "seed": (seed or "")[:200], "start_round": start_round,
           "result": result, "reason": reason}
    if fields:
        row.update({k: fields.get(k) for k in ("drafted_by", "signed_by", "signed")})
    try:
        _append_jsonl(GATE_EVENTS_FILE, row)
    except OSError as e:
        print(f"  [Topic Gate] could not log the gate event: {e}")


def _gate_block(seed: str, start_round, reason: str, message: str, fields: dict | None = None):
    _log_gate_event(seed, start_round, "block", reason, fields)
    raise SystemExit(message)


def _drafted_by_researcher(value) -> bool:
    return _norm(value).startswith("researcher")


def _candidate_match(fields: dict):
    """(field, candidate id, score) when an entry marked drafted_by researcher
    repeats a Claude-proposed candidate from knowledge/gate_candidates.jsonl
    (token-set ratio of 90 or more), else None."""
    if not _drafted_by_researcher(fields.get("drafted_by")) or not GATE_CANDIDATES_FILE.exists():
        return None
    try:
        from rapidfuzz import fuzz
    except ImportError:
        print("  [Topic Gate] rapidfuzz not installed, gate_candidates.jsonl match skipped")
        return None
    for n, row in enumerate(_read_jsonl(GATE_CANDIDATES_FILE), 1):
        cand = row.get("fields") if isinstance(row.get("fields"), dict) else row
        for k in CANDIDATE_MATCH_FIELDS:
            a, b = str(fields.get(k) or ""), str(cand.get(k) or "")
            if len(a.split()) < CANDIDATE_MIN_WORDS or len(b.split()) < CANDIDATE_MIN_WORDS:
                continue
            score = fuzz.token_set_ratio(a, b)
            if score >= CANDIDATE_MATCH_RATIO:
                return k, row.get("id") or f"line {n}", score
    return None


def _same_arc(prev: dict, fields: dict, start_round: int) -> bool:
    """A gate check for the arc already open at this round (a relaunch of
    the opening round), not a new arc."""
    return _int(prev.get("start_round")) == start_round and _norm(prev.get("seed")) == _norm(fields.get("seed"))


def check_topic_gate(seed_topic: str, start_round: int, total_existing: int, bypass: bool = False) -> None:
    """C2 (Pepinsky 2026): refuse to open a new research thread without a
    signed topic_gate.md entry for the current seed topic.

    Triggers whenever a seed topic is supplied via --topic, on the grounds
    that --topic is the explicit marker of a new research thread. The
    researcher opts out by omitting --topic (continuation) or by passing
    --bypass-topic-gate (explicit override).

    Each entry in topic_gate.md is an H2 block beginning with "## " and
    containing a line "seed: <seed_topic>" plus a "signed: <ISO-date>" line.
    Season 2 entries also need prior, falsifier, drafted_by and signed_by
    (D-10: who drafted and who signed is recorded, never assumed). A passing
    entry is written to knowledge/active_arc.json with the arc id, the start
    round, the pinned model and the CLI version (the model lock), the
    fingerprint of the KNA data in $KBL_DATA (the data pin, A1), pending
    researcher notes are bound to the arc, and every check is logged to
    knowledge/gate_events.jsonl.
    """
    if not seed_topic:
        return
    if bypass:
        _log_gate_event(seed_topic, start_round, "bypass", "--bypass-topic-gate")
        prev = get_active_arc()
        if _same_arc(prev, {"seed": seed_topic}, start_round):
            _update_arc_status(bypass_topic_gate=_now())
            return
        # A new seed opens a new thread, and it must not borrow the previous
        # arc's identity, call budget or signed conditions (E2E-13). It gets
        # its own arc number with no prior or falsifier, and its provenance
        # says no gate entry exists.
        cfg = load_config()
        n = _next_arc_number(prev)
        fields = {"seed": seed_topic, "start_round": start_round, "season": cfg.get("season", 1),
                  "arc": n, "arc_id": str(n), "opened": datetime.now().strftime("%Y-%m-%d %H:%M"),
                  "model": cfg.get("model"), "claude_code_version": claude_cli.cli_version(),
                  "drafted_by": "bypass: no gate entry", "signed_by": "bypass: no gate entry",
                  "bypass": True}
        fp = data_fingerprint()
        if fp:
            fields["data_fingerprint"] = fp
        ACTIVE_ARC_FILE.parent.mkdir(parents=True, exist_ok=True)
        ACTIVE_ARC_FILE.write_text(json.dumps(fields, ensure_ascii=False, indent=2))
        _bind_human_notes(start_round)
        status = {"seed": seed_topic, "start_round": start_round, "state": "running",
                  "reason": "thread opened with --bypass-topic-gate (no gate entry)",
                  "bypass_topic_gate": _now(), "ts": _now()}
        if fp:
            status["data_fingerprint"] = data_fingerprint_summary(fields)
        ARC_STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=2))
        print(f"  [Topic Gate] BYPASS: thread {n} from round {start_round} opened without a gate entry")
        return

    if not TOPIC_GATE_FILE.exists():
        _gate_block(
            seed_topic, start_round, "no topic_gate.md",
            "[BLOCKED · Topic Gate · C2]\n"
            "A new research thread (or fresh arc) cannot open without a signed\n"
            f"topic_gate.md at the repo root.\n"
            f"Seed topic: {seed_topic}\n"
            f"Expected file: {TOPIC_GATE_FILE}\n"
            "Fix: create topic_gate.md with an entry matching the seed topic\n"
            "(see template in the file, or use --bypass-topic-gate to skip\n"
            "under explicit researcher override)."
        )

    cfg = load_config()
    season = cfg.get("season", 1)
    fields = _find_gate_entry(seed_topic)
    if fields is None:
        _gate_block(
            seed_topic, start_round, "no matching signed entry",
            "[BLOCKED · Topic Gate · C2]\n"
            f"topic_gate.md exists but no signed entry matches seed topic:\n"
            f"  {seed_topic}\n"
            "Add a new H2 entry with `seed:` and `signed:` lines, or use\n"
            "--bypass-topic-gate for an explicit researcher override."
        )
    # Season 2: the gate supplies the axioms. No arc opens without a
    # stated prior and a falsifier (Zahavy 2026: axioms are the
    # bottleneck; the forum runs deduction and verification on them).
    if season >= 2:
        missing = [k for k in ("prior", "falsifier") if not fields.get(k)]
        if missing:
            _gate_block(
                seed_topic, start_round, f"missing {', '.join(missing)}",
                "[BLOCKED · Topic Gate · Season 2]\n"
                f"Signed entry found for '{seed_topic[:60]}' but it lacks: {', '.join(missing)}.\n"
                "Season 2 arcs require `prior:` (the belief this arc tests)\n"
                "and `falsifier:` (the concrete test that would overturn it). Add both\n"
                "to the entry in topic_gate.md, or pass --bypass-topic-gate.",
                fields)
        missing = [k for k in ("drafted_by", "signed_by") if not fields.get(k)]
        if missing:
            _gate_block(
                seed_topic, start_round, f"missing {', '.join(missing)}",
                "[BLOCKED · Topic Gate · Provenance (D-10)]\n"
                f"Signed entry found for '{seed_topic[:60]}' but it lacks: {', '.join(missing)}.\n"
                "Every Season 2 entry records who drafted it (`drafted_by:`) and who signed it\n"
                "(`signed_by:`), for example 'orchestrating Claude session (<model id>)' and\n"
                "'orchestrating Claude session, signed under the researcher's standing\n"
                "delegation of 2026-09-25'. Add both lines to the entry.",
                fields)
        hit = _candidate_match(fields)
        if hit:
            _gate_block(
                seed_topic, start_round, f"drafted_by researcher but {hit[0]} matches candidate {hit[1]}",
                "[BLOCKED · Topic Gate · Provenance (M08)]\n"
                f"The entry says drafted_by: {fields.get('drafted_by')}, but its `{hit[0]}` matches\n"
                f"a Claude-proposed candidate in knowledge/gate_candidates.jsonl ({hit[1]},\n"
                f"token-set ratio {hit[2]:.0f}). Record the entry as drafted by the orchestrating\n"
                "Claude session (and signed by whoever approved it), or rewrite the field.",
                fields)
        _stage2_gate_checks(seed_topic, start_round, fields, cfg)
    for k in ("drafted_by", "signed_by"):
        fields.setdefault(k, "unrecorded")

    prev = get_active_arc()
    fields["start_round"] = start_round
    fields["season"] = season
    new_arc = not _same_arc(prev, fields, start_round)
    if not new_arc:
        # The arc's opening round is being relaunched, so its id,
        # opening time and model lock are kept.
        for k in ("arc_id", "arc", "opened", "model", "claude_code_version", "data_fingerprint",
                  "data_fingerprint_changes"):
            if k in prev:
                fields[k] = prev[k]
    else:
        n = _next_arc_number(prev)
        fields["arc"] = n
        fields["arc_id"] = str(n)
        fields["opened"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        fields["model"] = cfg.get("model")
        fields["claude_code_version"] = claude_cli.cli_version()
        # A1: the arc pins the KNA data it opens on. check_data_pin compares
        # every later round with this fingerprint.
        fp = data_fingerprint()
        if fp:
            fields["data_fingerprint"] = fp
    ACTIVE_ARC_FILE.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_ARC_FILE.write_text(json.dumps(fields, ensure_ascii=False, indent=2))
    if new_arc:
        # A new arc starts its own status, as the bypass branch does, so its
        # failures, external writes and stops are never merged into the
        # previous arc's record (V-09).
        status = {"seed": fields.get("seed"), "start_round": start_round, "state": "running",
                  "reason": "arc opened from a signed topic_gate entry", "ts": _now()}
        if fields.get("data_fingerprint"):
            status["data_fingerprint"] = data_fingerprint_summary(fields)
        ARC_STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=2))
    _bind_human_notes(start_round)
    _log_gate_event(seed_topic, start_round, "pass", "", fields)
    print(f"  [Topic Gate · C2] Signed entry found for: {seed_topic[:80]}")
    print(f"  [Topic Gate] arc {fields.get('arc_id')} from round {start_round}, "
          f"model {fields.get('model')}, CLI {fields.get('claude_code_version')}, "
          f"data {(fields.get('data_fingerprint') or {}).get('id', 'not pinned')}")
    if season >= 2:
        print(f"  [Topic Gate · S2] prior: {fields['prior'][:70]}")
        print(f"  [Topic Gate · S2] falsifier: {fields['falsifier'][:70]}")
        print(f"  [Topic Gate · D-10] drafted by {fields['drafted_by'][:60]}, "
              f"signed by {fields['signed_by'][:60]}")


def preview_arc(seed_topic: str, start_round: int, bypass: bool = False) -> dict:
    """The arc a real run with this --topic would open, for a dry run. It is
    built as check_topic_gate builds it and never written. When the real run
    would be blocked (no matching signed entry, or a Season 2 entry without
    its prior, falsifier or provenance), that is printed."""
    prev = _read_json(ACTIVE_ARC_FILE)
    if bypass and _same_arc(prev, {"seed": seed_topic}, start_round):
        return dict(prev)            # a bypass relaunch keeps the open arc
    season = load_config().get("season", 1)
    fields = None if bypass else _find_gate_entry(seed_topic)
    if fields is None:
        print("  [Dry run] " + ("--bypass-topic-gate: a real run opens this thread without a gate entry."
                                if bypass else
                                "no signed topic_gate entry matches this seed. A real run would be blocked."))
        fields = {"seed": seed_topic}
        if bypass:
            fields.update(drafted_by="bypass: no gate entry", signed_by="bypass: no gate entry", bypass=True)
    elif season >= 2:
        missing = [k for k in ("prior", "falsifier", "drafted_by", "signed_by") if not fields.get(k)]
        if missing:
            print(f"  [Dry run] the matching entry lacks {', '.join(missing)}. A real run would be blocked.")
    for k in ("drafted_by", "signed_by"):
        fields.setdefault(k, "unrecorded")
    fields.update(start_round=start_round, season=season)
    if _same_arc(prev, fields, start_round):
        fields.update({k: prev[k] for k in ("arc_id", "arc") if k in prev})
    else:
        n = _next_arc_number(prev)
        fields.update(arc=n, arc_id=str(n))
    return fields


def _find_gate_entry(seed_topic: str) -> dict | None:
    """Fields of the first signed topic_gate.md entry whose seed matches
    seed_topic (a substring either way, since an entry may abbreviate the
    seed), or None. The template entry (seed: <...>) never matches."""
    if not seed_topic or not TOPIC_GATE_FILE.exists():
        return None
    normalized_seed = _norm(seed_topic)
    for entry in re.split(r"\n## ", TOPIC_GATE_FILE.read_text()):
        if "signed:" not in entry.lower():
            continue
        seed_line = re.search(r"^seed:\s*(.+)$", entry, re.MULTILINE | re.IGNORECASE)
        if not seed_line or seed_line.group(1).strip().startswith("<"):   # the template
            continue
        entry_seed = _norm(seed_line.group(1))
        if entry_seed in normalized_seed or normalized_seed in entry_seed:
            return _parse_gate_entry(entry)
    return None


def _stage2_gate_checks(seed_topic: str, start_round: int, fields: dict, cfg: dict) -> None:
    """Stage 2 gate fields (M15). Nothing happens while the flags are off.
    With binding_checks on, decision_rule and null_paper block and sesoi
    warns. With premise_check on, a failed premise check blocks unless the
    entry carries premise_override (premise_check.gate_status)."""
    if _stage2(cfg, "binding_checks"):
        missing = [k for k in ("decision_rule", "null_paper") if not fields.get(k)]
        if missing:
            _gate_block(
                seed_topic, start_round, f"missing {', '.join(missing)}",
                "[BLOCKED · Topic Gate · Stage 2]\n"
                f"stage2.binding_checks is on and the entry lacks: {', '.join(missing)}.",
                fields)
        if not fields.get("sesoi"):
            print("  [Topic Gate · S2] WARN: no sesoi (smallest effect of interest) in the entry")
    if _stage2(cfg, "premise_check"):
        import premise_check
        st = premise_check.gate_status(fields)
        if st.get("block"):
            _gate_block(
                seed_topic, start_round, "premise check failed",
                "[BLOCKED · Topic Gate · Premise]\n"
                f"The premise check for this entry failed ({st.get('path')}). Add premise_override\n"
                "with the reason the arc may open anyway, or revise the entry.",
                fields)
        if st.get("status") != "pass":
            print(f"  [Topic Gate · S2] premise check: {st.get('status')}")


def check_model_lock(cfg: dict, allow_change: bool = False) -> None:
    """M01. Refuse a round whose configured model differs from the model the
    active arc opened with, unless --allow-model-change (logged in
    arc_status). An arc without a model key is not enforced. A CLI version
    change is logged, never blocked."""
    arc = get_active_arc()
    have, want = arc.get("model"), cfg.get("model")
    if have and want and have != want:
        if not allow_change:
            raise SystemExit(
                "[BLOCKED · Model lock · M01]\n"
                f"The active arc (opened at round {arc.get('start_round', '?')}) runs on {have}, but\n"
                f"agents.json forum_config.model is {want}. Mixing models inside an arc breaks its\n"
                "baseline. Restore the model, open a new arc, or pass --allow-model-change\n"
                "(recorded in knowledge/arc_status.json).")
        _update_arc_status(allow_model_change=f"{_now()} {have} to {want}")
        print(f"  [Model lock] --allow-model-change: arc model {have}, running {want} (recorded)")
    ver_arc, ver_now = arc.get("claude_code_version"), claude_cli.cli_version()
    if ver_arc and ver_now and ver_arc != ver_now:
        changes = _read_json(ARC_STATUS_FILE).get("cli_version_changes") or []
        if not any(c.get("to") == ver_now for c in changes if isinstance(c, dict)):
            changes.append({"from": ver_arc, "to": ver_now, "ts": _now()})
            _update_arc_status(cli_version_changes=changes)
        print(f"  [Model lock] CLI version changed since the arc opened: {ver_arc} to {ver_now} (logged)")


# ==========================================================================
# Data version pinning (A1, 2026-09-26)
# ==========================================================================

DATA_SUFFIXES = (".parquet", ".csv")
_HASH_CACHE: dict = {}


def _sha256_file(path: Path) -> str:
    """sha256 of a file, cached in this process by (path, size, mtime), so
    check_topic_gate and check_data_pin in one run hash each file once. A new
    process always hashes again."""
    st = path.stat()
    key = (str(path.resolve()), st.st_size, st.st_mtime_ns)
    if key not in _HASH_CACHE:
        import hashlib
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        _HASH_CACHE[key] = h.hexdigest()
    return _HASH_CACHE[key]


def _git_in(d: Path, *args: str) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(d), *args], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def _kna_version() -> str | None:
    try:
        from importlib import metadata
        return metadata.version("kna")
    except Exception:
        return None


def data_fingerprint(data_dir=None) -> dict | None:
    """Fingerprint of the KNA data the forum reads: size and sha256 of every
    .parquet and .csv file at the top of $KBL_DATA, the kna data repository's
    git commit (with whether the data folder has uncommitted changes) and the
    installed kna package version. The id is a hash of the file list, so it
    changes exactly when a file's content changes. No path is recorded,
    because active_arc.json is public. None when KBL_DATA is not set."""
    d = data_dir or os.environ.get("KBL_DATA")
    if not d:
        return None
    d = Path(d).expanduser()
    files = {}
    if d.is_dir():
        for p in sorted(d.iterdir()):
            if p.is_file() and p.suffix.lower() in DATA_SUFFIXES:
                files[p.name] = {"size": p.stat().st_size, "sha256": _sha256_file(p)}
    import hashlib
    digest = hashlib.sha256(json.dumps(files, sort_keys=True).encode("utf-8")).hexdigest()
    commit = dirty = None
    top = _git_in(d, "rev-parse", "--show-toplevel") if d.is_dir() else None
    if top and Path(top).resolve() != BASE_DIR.resolve():
        commit = _git_in(d, "rev-parse", "HEAD")
        status = _git_in(d, "status", "--porcelain", "--", ".")
        dirty = bool(status) if status is not None else None
    return {"id": f"kbl-{digest[:12]}", "n_files": len(files), "files": files,
            "kna_git_commit": commit, "kna_git_dirty": dirty, "kna_version": _kna_version(),
            "computed": _now()}


def data_changes(old: dict | None, new: dict | None) -> list[str]:
    """One line per data file that was added, removed or changed between two
    fingerprints."""
    a, b = (old or {}).get("files") or {}, (new or {}).get("files") or {}
    out = []
    for name in sorted(set(a) | set(b)):
        if name not in b:
            out.append(f"removed {name}")
        elif name not in a:
            out.append(f"added {name}")
        elif a[name].get("sha256") != b[name].get("sha256"):
            out.append(f"changed {name} (size {a[name].get('size')} to {b[name].get('size')} bytes)")
    return out


def data_fingerprint_summary(arc: dict | None = None) -> dict | None:
    """The arc_status field draft_article can read (key data_fingerprint): the
    pinned fingerprint id, the kna data commit and package version, any
    allowed mid-arc change, and a ready data availability sentence."""
    arc = get_active_arc() if arc is None else arc
    fp = arc.get("data_fingerprint")
    if not fp:
        return None
    changes = list(arc.get("data_fingerprint_changes") or [])
    parts = [f"kna data commit {fp['kna_git_commit'][:7]}" if fp.get("kna_git_commit") else None,
             f"kna package {fp['kna_version']}" if fp.get("kna_version") else None]
    detail = ", ".join(p for p in parts if p)
    statement = (f"The analysis read {fp.get('n_files', 0)} KNA processed-data files with data fingerprint "
                 f"{fp['id']}{f' ({detail})' if detail else ''}, "
                 f"{'recorded after the arc had opened' if fp.get('pinned_late') else 'recorded when the arc opened'}.")
    if changes:
        first = changes[0].get("from")
        statement += (f" The data changed during the arc, from fingerprint {first} to {fp['id']}, and the "
                      f"change was allowed with --allow-data-change ({len(changes)} time(s), last on "
                      f"{str(changes[-1].get('ts'))[:10]}).")
    return {"id": fp["id"], "n_files": fp.get("n_files"), "kna_git_commit": fp.get("kna_git_commit"),
            "kna_git_dirty": fp.get("kna_git_dirty"), "kna_version": fp.get("kna_version"),
            "pinned": fp.get("computed"), "pinned_late": bool(fp.get("pinned_late")),
            "changes": [{k: c.get(k) for k in ("ts", "from", "to", "changes")} for c in changes],
            "statement": statement}


def _pop_arc_status_keys(*keys: str) -> None:
    st = _read_json(ARC_STATUS_FILE)
    if any(k in st for k in keys):
        for k in keys:
            st.pop(k, None)
        ARC_STATUS_FILE.write_text(json.dumps(st, ensure_ascii=False, indent=2))


def _write_active_arc(arc: dict) -> None:
    ACTIVE_ARC_FILE.parent.mkdir(parents=True, exist_ok=True)
    ACTIVE_ARC_FILE.write_text(json.dumps(arc, ensure_ascii=False, indent=2))


def check_data_pin(allow_change: bool = False) -> dict | None:
    """Before every round: recompute the $KBL_DATA fingerprint and compare it
    with the one the active arc pinned when it opened. A change refuses the
    round and names the changed files, unless --allow-data-change is passed,
    which records the change in active_arc.json, arc_status.json and
    knowledge/gate_events.jsonl and pins the new fingerprint. An arc opened
    before pinning existed is pinned now (pinned_late). Returns the pin."""
    arc = get_active_arc()
    if not arc.get("start_round"):
        return None
    now = data_fingerprint()
    if now is None:
        return None
    seed, start = arc.get("seed", ""), arc.get("start_round")
    pin = arc.get("data_fingerprint")
    if not pin:
        arc["data_fingerprint"] = {**now, "pinned_late": True}
        _write_active_arc(arc)
        _log_gate_event(seed, start, "data_pin", f"arc opened before data pinning, pinned late as {now['id']}")
        _update_arc_status(data_fingerprint=data_fingerprint_summary(arc))
        print(f"  [Data pin] arc {arc.get('arc_id', '?')} had no data fingerprint, pinned now as {now['id']}")
        return arc["data_fingerprint"]
    changes = data_changes(pin, now)
    if not changes:
        _pop_arc_status_keys("data_pin_refused")
        if (_read_json(ARC_STATUS_FILE).get("data_fingerprint") or {}).get("id") != pin.get("id"):
            _update_arc_status(data_fingerprint=data_fingerprint_summary(arc))
        print(f"  [Data pin] KNA data unchanged since the arc opened ({pin.get('id')}, {pin.get('n_files')} files)")
        return pin
    shown = "; ".join(changes[:10]) + (f"; and {len(changes) - 10} more" if len(changes) > 10 else "")
    if not allow_change:
        _log_gate_event(seed, start, "data_change_block", shown)
        _update_arc_status(data_pin_refused={"ts": _now(), "pinned": pin.get("id"), "now": now["id"],
                                             "changes": changes[:20]})
        claude_cli.notify("KNA forum: data changed mid-arc", f"{len(changes)} file(s) differ from the arc's pin "
                                                             f"{pin.get('id')}. Round refused.")
        raise SystemExit(
            "[BLOCKED · Data pin · A1]\n"
            f"The KNA data in $KBL_DATA changed since the active arc pinned it ({pin.get('id')} at "
            f"{str(pin.get('computed'))[:16]}, now {now['id']}):\n"
            + "\n".join(f"  - {c}" for c in changes[:20])
            + ("\n  - ..." if len(changes) > 20 else "")
            + "\nMixing data versions inside an arc breaks its numbers. Restore the pinned files, or rerun with\n"
              "--allow-data-change to continue on the new data (recorded in active_arc.json, arc_status.json\n"
              "and gate_events.jsonl, and disclosed in the paper's data availability statement).")
    entry = {"ts": _now(), "from": pin.get("id"), "to": now["id"], "changes": changes[:50],
             "by": "--allow-data-change"}
    arc["data_fingerprint_changes"] = list(arc.get("data_fingerprint_changes") or []) + [entry]
    arc["data_fingerprint"] = now
    _write_active_arc(arc)
    _log_gate_event(seed, start, "data_change_allowed", f"{pin.get('id')} to {now['id']}: {shown}")
    allowed = list(_read_json(ARC_STATUS_FILE).get("allow_data_change") or []) + [entry]
    _pop_arc_status_keys("data_pin_refused")
    _update_arc_status(allow_data_change=allowed[-20:], data_fingerprint=data_fingerprint_summary(arc))
    print(f"  [Data pin] --allow-data-change: {pin.get('id')} to {now['id']} ({len(changes)} file(s)), recorded")
    return now


def log_retreat(
    originating_round: int,
    overturning_round: int,
    flagged_by: str,
    finding: str,
    reason: str,
    from_status: str = "preliminary",
    to_status: str = "contested",
    new_evidence=None,
) -> None:
    """C3 (reflection report): record a retreat whenever a prior finding is
    overturned. Called from agent posts (via Bash) or by hand.

    Inside an agent run (KNA_STAGING_DIR set) the row goes to the run's
    staging directory. It reaches knowledge/retreats.jsonl only when the run
    is accepted and new_evidence resolves (an output file, a precheck id, a
    post line reference such as 084:44, or a DOI). Outside a run it is
    appended to the ledger directly."""
    staged = os.environ.get("KNA_STAGING_DIR")
    target = Path(staged) / "retreats.jsonl" if staged else RETREATS_LEDGER
    entry = {
        "ts": _now(),
        "originating_round": originating_round,
        "overturning_round": overturning_round,
        "flagged_by": flagged_by,
        "from_status": from_status,
        "to_status": to_status,
        "finding": finding.strip(),
        "reason": reason.strip(),
    }
    if new_evidence is not None:
        entry["new_evidence"] = new_evidence
    if os.environ.get("KNA_RUN_ID"):
        entry["run_id"] = os.environ["KNA_RUN_ID"]
    _append_jsonl(target, entry)
    where = " (staged)" if staged else ""
    print(f"  [Retreat · C3] R{originating_round} → R{overturning_round}: {finding[:60]}{where}")


_CROSSREF_CACHE: dict = {}


def verify_citations(post_path: Path) -> list[str]:
    """C9 (reflection report): scan a committed forum post for DOI and
    author-year citations; Crossref-verify each; return list of
    unverified citations as strings (empty list if all verified).

    DOIs come from prechecks.extract_dois (R-05 regex fix: stops at
    whitespace, brackets, quotes, '*' and '`', trailing punctuation removed).
    Author-year pattern: keep minimal here; agents are expected to include
    DOI-anchored references list at the bottom, so we focus on DOI checks.
    """
    # Use `requests` (bundles its own CA bundle via certifi) to avoid the
    # system-Python SSL CA problem that silently marked every real DOI as
    # unverified in the R21 run.
    import urllib.parse
    try:
        import requests  # type: ignore
    except ImportError:
        print(f"  [Citation Verify · C9] `requests` not installed; skipping verification on {post_path.name}")
        return []
    import prechecks

    text = post_path.read_text()
    dois = prechecks.extract_dois(text)
    unverified = []
    for doi in dois:
        if doi in _CROSSREF_CACHE:
            if not _CROSSREF_CACHE[doi]:
                unverified.append(doi)
            continue
        url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='/')}?mailto=kyusik.yang@nyu.edu"
        try:
            r = requests.get(
                url,
                headers={"User-Agent": "kna-research-agents/1.0 (mailto:kyusik.yang@nyu.edu)"},
                timeout=12,
            )
            ok = r.status_code == 200
        except Exception:
            ok = False
        _CROSSREF_CACHE[doi] = ok
        if not ok:
            unverified.append(doi)
    if unverified:
        print(f"  [Citation Verify · C9] {post_path.name}: {len(unverified)} unverified DOI(s)")
        for d in unverified[:5]:
            print(f"    - {d}")
    return unverified


def get_forum_posts():
    """Read all forum posts, sorted chronologically."""
    posts = sorted(FORUM_DIR.glob("*.md"))
    return posts


def get_topic_break_round():
    """Season 1 topic break marker (new topic starts from this round). Season 2
    takes the lower bound from active_arc.json start_round instead."""
    marker = KNOWLEDGE_DIR / "topic_break.txt"
    if marker.exists():
        try:
            return int(marker.read_text().strip())
        except ValueError:
            pass
    return 0


def _arc_start_round() -> int:
    """First round of the current thread. That is active_arc.start_round in
    Season 2 and the Season 1 topic_break marker otherwise (0 when neither
    exists)."""
    if load_config().get("season", 1) >= 2:
        return _int(get_active_arc().get("start_round")) or 0
    return get_topic_break_round()


def get_forum_state(current_round=1, n_agents=3, *, exclude=()):
    """Compile forum state with aggressive context compression.

    Strategy:
    - Only posts from the current thread's first round onwards
      (active_arc.start_round in Season 2)
    - Current round (N): full text of all posts so far
    - Previous round (N-1): full text
    - Rounds N-3 to N-2: round SUMMARY only
    - Older: omitted
    Rounds come from each post's frontmatter (forum_index), not its file
    index. n_agents is kept for callers and no longer used. exclude lists
    post paths to leave out (Stage 2 claim sheet and blinding)."""
    metas = forum_index.index(forum_dir=FORUM_DIR)
    if not metas:
        return "(No posts yet. You are starting a NEW research thread.)"

    thread_start = _arc_start_round()
    if thread_start > 0 and current_round >= thread_start:
        min_round = thread_start
    else:
        min_round = 1

    parts = []

    # If this is the first round of a new topic, say so explicitly
    if thread_start > 0 and current_round == thread_start:
        parts.append(
            "(This is a NEW research topic. Previous rounds covered different topics. "
            "Do NOT reference or respond to previous posts. Start fresh.)"
        )

    # 1. Include round summaries for N-3 and N-2 only (within current topic)
    if SUMMARIES_DIR.exists():
        for sf in sorted(SUMMARIES_DIR.glob("round_*.md")):
            rnd_num = int(re.search(r"(\d+)", sf.stem).group(1))
            if rnd_num >= min_round and current_round - 3 <= rnd_num <= current_round - 2:
                parts.append(f"--- Round {rnd_num} Summary ---\n{sf.read_text()}")

    # 2. Full text for current and previous round only (within current topic)
    skip = {Path(p).name for p in exclude}
    for m in metas:
        if m["round"] and m["round"] >= max(min_round, current_round - 1) and m["path"].name not in skip:
            parts.append(f"--- {m['path'].name} ---\n{m['path'].read_text()}")

    return "\n\n".join(parts)


def next_post_number():
    return forum_index.next_post_number(forum_dir=FORUM_DIR)


def get_knowledge_summary():
    """Summarize the literature knowledge base for agents."""
    log_file = KNOWLEDGE_DIR / "literature_log.jsonl"
    if not log_file.exists():
        return ""
    entries = []
    with open(log_file) as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    if not entries:
        return ""
    recent = entries[-30:]
    lines = ["\n## Literature Knowledge Base (recent entries)\n"]
    for e in recent:
        authors = ", ".join(e.get("authors", [])[:2])
        doi = e.get("doi", "")
        doi_str = f" doi:{doi}" if doi else ""
        lines.append(f"- [{e.get('year','')}] {e.get('title','')} ({authors}) [{e.get('source','')}]{doi_str}")
    lines.append(f"\n(Total: {len(entries)} entries in knowledge base)\n")
    return "\n".join(lines)


def get_relevant_abstracts(topic, max_abstracts=8):
    """Find abstracts relevant to the current topic via keyword matching."""
    abstracts_file = KNOWLEDGE_DIR / "abstracts.jsonl"
    if not abstracts_file.exists():
        return ""

    records = []
    with open(abstracts_file) as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    if not records or not topic:
        return ""

    # Simple keyword matching
    topic_words = set(topic.lower().split())
    scored = []
    for r in records:
        title = (r.get("title", "") or "").lower()
        abstract = (r.get("abstract", "") or "").lower()
        text = title + " " + abstract
        score = sum(1 for w in topic_words if w in text)
        if score > 0:
            scored.append((score, r))

    scored.sort(key=lambda x: -x[0])
    top = scored[:max_abstracts]

    if not top:
        return ""

    lines = ["\n## Relevant Abstracts from Knowledge Base\n"]
    for _, r in top:
        authors = ", ".join(r.get("authors", [])[:3])
        doi = r.get("doi", "")
        doi_str = f" (doi:{doi})" if doi else ""
        abstract = r.get("abstract", "")[:300]
        lines.append(
            f"### {r.get('title', '')} ({r.get('year', '?')})\n"
            f"*{authors}* - {r.get('journal', '')}{doi_str}\n"
            f"{abstract}...\n"
        )
    return "\n".join(lines)


def get_findings_tracker():
    """Load the cumulative findings tracker for agent context."""
    tracker_file = KNOWLEDGE_DIR / "findings.jsonl"
    if not tracker_file.exists():
        return ""
    findings = []
    with open(tracker_file) as f:
        for line in f:
            try:
                findings.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    if not findings:
        return ""
    # Season 2: the full ledger (1,200+ rows by R24) was 80% of every prompt
    # and buried the task. Show the active arc in full plus, from earlier
    # rounds, only what was not archived (pursue / revise / confirmed /
    # contested). The complete ledger stays in knowledge/findings.jsonl.
    cfg = load_config()
    trimmed_note = ""
    if cfg.get("season", 1) >= 2:
        start = int(get_active_arc().get("start_round") or 10**9)
        keep = []
        for f in findings:
            rnd = int(f.get("round") or 0)
            if rnd >= start or f.get("verdict") in ("pursue", "revise") \
                    or f.get("status") in ("confirmed", "contested"):
                keep.append(f)
        trimmed_note = (
            f"(Season 2 view: {len(keep)} of {len(findings)} ledger rows shown: "
            "the active arc in full, plus earlier pursue / revise / confirmed / contested findings. "
            "Archived Season 1 verdicts are omitted.)\n"
        )
        findings = keep
    lines = ["\n## Cumulative Findings Tracker\n", trimmed_note]
    lines.append("| # | Finding | Status | Round | Source |")
    lines.append("|---|---------|--------|-------|--------|")
    for i, f in enumerate(findings, 1):
        lines.append(
            f"| {i} | {f.get('finding', '')} | "
            f"**{f.get('status', 'preliminary')}** | "
            f"R{f.get('round', '?')} | {f.get('source', '')} |"
        )
    lines.append(
        "\nStatus key: preliminary (new), confirmed (cross-validated), "
        "contested (counter-evidence found), refined (updated by later round)\n"
    )
    return "\n".join(lines)


def _role_post(round_num: int, role: str) -> Path | None:
    """The round's post by one role (frontmatter identity, forum_index)."""
    for m in forum_index.index(forum_dir=FORUM_DIR):
        if m["round"] == round_num and m["role"] == role:
            return m["path"]
    return None


def update_findings_tracker(round_num, critic_post=None, run_id=None):
    """Append the round's Critic finding to knowledge/findings.jsonl once.

    The round comes from the Critic post's frontmatter, the verdict from the
    verdict of record (verdicts.jsonl, else the post's scoring block), and
    ledger_audit.append_unique skips a row whose (round, source, finding)
    key already exists, so a second call adds nothing."""
    import ledger_audit
    import verdict

    post = Path(critic_post) if critic_post else _role_post(round_num, "critic")
    if post is None or not post.exists():
        return
    rnd = forum_index.post_meta(post).get("round") or round_num
    record = verdict.verdict_of_record(rnd) or {}
    one_line = record.get("one_line")
    if not one_line:
        m = re.search(r'one_line:\s*"([^"]+)"', post.read_text(encoding="utf-8"))
        one_line = m.group(1) if m else None
    if not one_line:
        return
    row = {
        "finding": one_line,
        "status": "preliminary",
        "round": rnd,
        "source": post.name,
        "verdict": record.get("verdict") or "unknown",
    }
    rid = run_id or forum_index.read_frontmatter(post).get("run_id")
    if rid:
        row["run_id"] = rid
    if ledger_audit.append_unique(row, path=KNOWLEDGE_DIR / "findings.jsonl"):
        print(f"  [Ledger] R{rnd}: {row['verdict']} - {one_line[:60]}")


def get_existing_articles():
    """Load summaries of existing articles to prevent topic repetition."""
    articles_dir = BASE_DIR / "articles"
    if not articles_dir.exists():
        return ""

    articles = []
    for f in sorted(articles_dir.glob("*.md")):
        content = f.read_text()
        title = ""
        source_round = ""
        status = ""
        for line in content.split("\n"):
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"')
            elif line.startswith("source_round:"):
                source_round = line.split(":", 1)[1].strip()
            elif line.startswith("status:"):
                status = line.split(":", 1)[1].strip().strip('"')
        # Papers carry source_round. The conference proceedings and the
        # post-conference reflection are not papers and stay out.
        if title and source_round:
            articles.append(f"- Round {source_round}: \"{title}\" [{status}]")

    if not articles:
        return ""

    lines = ["\n## Existing Articles (DO NOT repeat these topics)\n"]
    lines.append(
        "The forum has already produced articles on the following topics. "
        "Your new research thread MUST explore a different question, dataset, "
        "or theoretical angle. Overlap with these topics should be minimal.\n"
    )
    lines.extend(articles)
    lines.append("")
    return "\n".join(lines)


# ==========================================================================
# Researcher notes (M04) and open waivers
# ==========================================================================

NOTE_HEADER_RE = re.compile(
    r"^### note \| ts: (?P<ts>.+?) \| source: (?P<source>.+?)(?: \| by: (?P<by>.+?))?"
    r" \| arc_start: (?P<arc>\S+)[ \t]*$",
    re.MULTILINE)


def _format_note(note: dict) -> str:
    by = f" | by: {note['by']}" if note.get("by") else ""
    return (f"### note | ts: {note['ts']} | source: {note['source']}{by} | arc_start: {note['arc_start']}\n\n"
            f"{note['text'].strip()}\n")


def _read_notes() -> tuple[str, list[dict]]:
    """(unheaded legacy text, notes) from knowledge/human_context.md."""
    if not HUMAN_CONTEXT_FILE.exists():
        return "", []
    raw = HUMAN_CONTEXT_FILE.read_text(encoding="utf-8")
    marks = list(NOTE_HEADER_RE.finditer(raw))
    legacy = raw[: marks[0].start()] if marks else raw
    notes = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(raw)
        notes.append({"ts": m.group("ts"), "source": m.group("source"), "by": m.group("by"),
                      "arc_start": m.group("arc"), "text": raw[m.end():end].strip()})
    return legacy.strip(), notes


def _write_notes(notes: list[dict], legacy: str = "") -> None:
    parts = ([legacy.rstrip() + "\n"] if legacy.strip() else []) + [_format_note(n) for n in notes]
    HUMAN_CONTEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    HUMAN_CONTEXT_FILE.write_text("\n".join(parts), encoding="utf-8")


def _arc_is_open() -> bool:
    """True while the active arc can still run rounds. An arc that run_arc
    closed (stop, draft_and_stop, closed_no_paper) is not open. Paused and
    failure-stopped arcs are still open, because they continue without a new
    topic-gate check."""
    arc = get_active_arc()
    if not arc.get("start_round"):
        return False
    st = _read_json(ARC_STATUS_FILE)
    if st.get("seed") is not None and not _same_arc(st, arc, _int(arc.get("start_round"))):
        return True    # the status belongs to an earlier arc
    if st.get("state") == "running" or st.get("pending_draft"):
        return True
    return not (st.get("action") in ARC_CLOSED_ACTIONS or st.get("state") in ARC_CLOSED_STATES)


def _bind_human_notes(start_round: int) -> None:
    """At arc open, bind pending researcher notes to the arc and move notes
    bound to an earlier arc (and any unheaded legacy text) to
    knowledge/archive/human_context_<ts>.md."""
    legacy, notes = _read_notes()
    keep, old, changed = [], [], bool(legacy)
    for n in notes:
        if n["arc_start"] == "pending":
            n = {**n, "arc_start": str(start_round)}
            changed = True
        bound = _int(n["arc_start"])
        if bound is not None and bound >= start_round:
            keep.append(n)
        else:
            old.append(n)
            changed = True
    if not changed:
        return
    if old or legacy:
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        dest = ARCHIVE_DIR / f"human_context_{datetime.now().strftime('%Y-%m-%dT%H%M%S')}.md"
        body = f"# Researcher notes archived when the arc opened at round {start_round}\n\n"
        if legacy:
            body += legacy.strip() + "\n\n"
        body += "\n".join(_format_note(n) for n in old)
        with open(dest, "a", encoding="utf-8") as f:
            f.write(body)
        print(f"  [Notes] archived {len(old) + (1 if legacy else 0)} note(s) from earlier arcs to {dest.name}")
    _write_notes(keep)


def researcher_notes_block(arc: dict) -> str:
    """Notes bound to the active arc, verbatim, with no framing instruction.
    Each note is attributed to whoever the note records (--by). A note that
    records no author says so, and none is presented as the researcher's
    unless it names the researcher."""
    start = _int(arc.get("start_round"))
    if start is None:
        return ""
    _, notes = _read_notes()
    out = []
    for n in notes:
        if _int(n["arc_start"]) == start and n["text"]:
            by = (n.get("by") or "").strip()
            if not by or by == "unrecorded":
                head = f"Note (from {n['source']}, dated {n['ts']}, author unrecorded)"
            else:
                who = "the researcher" if _norm(by) == "researcher" else by
                head = f"Note from {who} (from {n['source']}, dated {n['ts']})"
            out.append(f"\n## {head}\n\n{n['text']}\n")
    return "".join(out)


def waivers_block() -> str:
    """Open rows of knowledge/waivers.jsonl, one line each. A row counts as
    a researcher waiver only when the researcher recorded it
    (attributed_to_researcher true). Orchestrator suspensions say so."""
    rows = [r for r in _read_jsonl(WAIVERS_FILE) if r.get("status") == "open" and r.get("summary")]
    if not rows:
        return ""
    lines = ["\n## Open Suspensions and Waivers (knowledge/waivers.jsonl)\n"]
    for r in rows:
        if r.get("attributed_to_researcher") is True:
            who = f"researcher waiver recorded {r.get('recorded', '')}".rstrip()
        else:
            who = "suspended by the orchestrator, not a researcher decision"
        lines.append(f"- {r['summary']} ({who})")
    return "\n".join(lines) + "\n"


def arc_block_text(arc: dict, *, critic: bool = False, cfg: dict | None = None) -> str:
    """The arc's signed conditions with their provenance as recorded in
    topic_gate.md (D-10). Never says 'set by the researcher'. An
    active_arc.json that predates drafted_by and signed_by takes them from
    the matching topic_gate.md entry. The Stage 2 fields (decision_rule,
    sesoi, null_paper, premise) appear only while stage2.binding_checks is
    on. The Critic's block leaves out the round the arc opened at (M10a)."""
    if not (arc.get("prior") or arc.get("falsifier")):
        return ""
    cfg = cfg if cfg is not None else load_config()
    drafted = arc.get("drafted_by") or "unrecorded"
    signer = arc.get("signed_by") or "unrecorded"
    if "unrecorded" in (drafted, signer) and arc.get("seed"):
        entry = _find_gate_entry(arc["seed"]) or {}
        drafted = drafted if drafted != "unrecorded" else (entry.get("drafted_by") or "unrecorded")
        signer = signer if signer != "unrecorded" else (entry.get("signed_by") or "unrecorded")
    who = [f"drafted by {drafted}" if drafted != "unrecorded" else "drafter unrecorded",
           f"signed by {signer}" if signer != "unrecorded" else "signer unrecorded"]
    lines = [
        f"\n## Arc Prior and Falsifier (topic_gate.md entry, {who[0]}, {who[1]}, "
        f"signed {arc.get('signed', '?')})\n",
        f"- **Seed**: {arc.get('seed', '')}",
        f"- **Prior** (the belief this arc tests): {arc.get('prior', '')}",
        f"- **Falsifier** (the test that would overturn it): {arc.get('falsifier', '')}",
        f"- **Exclusion criteria**: {arc.get('exclusion_criteria', '')}",
    ]
    if _stage2(cfg, "binding_checks"):
        for key, label in (("decision_rule", "Decision rule"), ("sesoi", "Smallest effect of interest"),
                           ("null_paper", "Null result becomes the paper"), ("premise", "Premise")):
            if arc.get(key):
                lines.append(f"- **{label}**: {arc[key]}")
    if not critic:
        lines.append(f"- Arc opened at round {arc.get('start_round', '?')}.")
    lines.append("")
    lines.append("The prior and the falsifier are the arc's signed conditions, not yours to replace. "
                 "Test the prior, deepen it, or overturn it. Do not swap it for a different question.")
    return "\n".join(lines) + "\n"


# ==========================================================================
# Prompts
# ==========================================================================

def _block(manifest, label: str, text: str, source=None) -> str:
    """Record one injected prompt block in the manifest (M02) and return it."""
    if manifest is not None and text and text.strip():
        manifest.append(claude_cli.manifest_block(label, text, source))
    return text or ""


def build_prompt(agent, round_num, total_rounds, seed_topic=None, *, post_num=None, manifest=None):
    """Build system prompt for one agent run.

    manifest, when given, receives one claude_cli.manifest_block per injected
    block (it goes into the run's private sidecar)."""
    cfg = load_config()
    season = cfg.get("season", 1)
    aid = agent["id"]
    arc = get_active_arc() if season >= 2 else {}
    arc_start = _int(arc.get("start_round"))
    # An arc opens at active_arc.start_round, so a resumed opening round
    # still gets the opening instructions. A seed topic also marks one
    # (dry runs and --bypass-topic-gate do not write active_arc.json).
    is_opening = (arc_start is not None and round_num == arc_start) or bool(seed_topic)

    blind = (season >= 2 and aid == "data_analyst" and is_opening and _stage2(cfg, "prediction_cards")
             and bool(cfg.get("blind_opening_analyst")))
    claim_first = season >= 2 and aid == "critic" and _stage2(cfg, "claim_sheet_first")
    current = {m["role"]: m["path"] for m in forum_index.index(forum_dir=FORUM_DIR) if m["round"] == round_num}
    exclude = []
    if blind and current.get("literature_scout"):
        exclude.append(current["literature_scout"])
    if claim_first and current.get("data_analyst"):
        exclude.append(current["data_analyst"])

    forum_state = get_forum_state(current_round=round_num, exclude=exclude)
    if claim_first and current.get("data_analyst"):
        forum_state += (f"\n\n--- {current['data_analyst'].name} ---\n(The Analyst's post for this round is "
                        f"at forum/{current['data_analyst'].name}. Read it only in phase 2, after you have "
                        "written your provisional verdict.)")
    _block(manifest, "forum_state", forum_state, FORUM_DIR)
    knowledge = _block(manifest, "knowledge_summary", get_knowledge_summary(),
                       KNOWLEDGE_DIR / "literature_log.jsonl")
    abstracts = _block(manifest, "abstracts", get_relevant_abstracts(seed_topic) if seed_topic else "",
                       KNOWLEDGE_DIR / "abstracts.jsonl")
    if claim_first:
        findings = ("\n## Cumulative Findings Tracker\n\nThe findings ledger is at knowledge/findings.jsonl. "
                    "Read it only in phase 2.\n")
    else:
        findings = get_findings_tracker()
    _block(manifest, "findings", findings, KNOWLEDGE_DIR / "findings.jsonl")
    existing_articles = _block(manifest, "existing_articles", get_existing_articles(), BASE_DIR / "articles")
    notes = _block(manifest, "researcher_notes", researcher_notes_block(arc), HUMAN_CONTEXT_FILE)
    waivers = _block(manifest, "waivers", waivers_block(), WAIVERS_FILE)

    post_num = post_num or next_post_number()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    n_agents = len(load_agents())
    is_first_round = post_num <= n_agents
    order_ids = [a["id"] for a in load_agents()]
    position = order_ids.index(aid) if aid in order_ids else 0

    topic_line = ""
    if seed_topic:
        topic_line = f"\nForum seed topic: **{seed_topic}**\nOrient your first post around this topic, but you may explore related threads.\n"

    if season >= 2:
        task_instruction = season2_task(agent, position, is_opening, order_ids)
    elif is_first_round:
        task_instruction = (
            "This is the opening round. Start a new research thread based on your specialty. "
            "Be specific and substantive - pick a focused question, gather evidence, and report findings."
        )
    else:
        task_instruction = (
            "Read the existing posts carefully. You should:\n"
            "  (a) Respond to another agent's findings with your own evidence or perspective\n"
            "  (b) Extend someone's analysis with new data or literature\n"
            "  (c) Challenge a claim with counter-evidence\n"
            "  (d) Synthesize multiple threads into a research agenda\n"
            "  (e) Open a new question inspired by the discussion\n"
            "Engage substantively with at least one previous post."
        )
    _block(manifest, "task", task_instruction + topic_line, "run_forum.season2_task")

    arc_block = ""
    diversity_block = ""
    ledger_block = ""
    card_block = ""
    verdict_note = ""
    # A2: the Critic sees the automatic pitfall scan of this round's Analyst
    # post (flag only). It is recomputed here, so a resumed round gets it too.
    pitfall_block = ""
    if aid == "critic" and current.get("data_analyst"):
        pitfall_block = _block(manifest, "data_pitfall_flags", pitfall_flags_for(current["data_analyst"]),
                               KNOWLEDGE_DIR / "data_pitfalls.md")
    if season >= 2:
        # Monitor numbers (taxonomy shares, entropy, the retired bridge cap)
        # reach no agent (M10a, M20). The diversity check stays, except for a
        # claim-sheet-first Critic (M16).
        if not claim_first:
            try:
                import topic_diversity
                if aid == "literature_scout":
                    diversity_block = topic_diversity.prior_topics_for_scout()
                else:
                    diversity_block = topic_diversity.format_for_prompt(round_num)
            except Exception as e:  # guard must never block a round
                print(f"  [Diversity] unavailable: {e}")
        _block(manifest, "diversity", diversity_block, KNOWLEDGE_DIR / "topic_diversity.jsonl")
        if not blind:
            arc_block = _block(manifest, "arc_block", arc_block_text(arc, critic=aid == "critic", cfg=cfg),
                               ACTIVE_ARC_FILE)
        try:
            import verdict
            # A claim-sheet-first Critic sees no earlier verdicts (M16).
            verdict_note = _block(manifest, "verdict_note",
                                  verdict.prompt_note(round_num - 1) if round_num > 1 and not claim_first else "",
                                  KNOWLEDGE_DIR / "verdicts.jsonl")
        except Exception as e:
            print(f"  [Verdict] prompt note unavailable: {e}")
        if _stage2(cfg, "prediction_cards"):
            import prediction_card as pc
            if arc_start:
                ledger_block = _block(manifest, "quantities_ledger", pc.ledger_for_prompt(arc_start),
                                      KNOWLEDGE_DIR / "quantities.jsonl")
            card = pc.load_cards().get(int(round_num)) if blind else None
            if card:
                card_block = _block(
                    manifest, "analyst_card_view",
                    "\n## Committed Card (computation fields only)\n\n```json\n"
                    + json.dumps(pc.analyst_view(card), ensure_ascii=False, indent=2) + "\n```\n",
                    KNOWLEDGE_DIR / "prediction_cards" / f"R{int(round_num):02d}.json")

    agent_prompt = _block(manifest, "agent_prompt", agent["prompt"], "agents.json")
    stage2 = cfg.get("stage2") or {}
    addenda = "\n\n".join(_block(manifest, f"stage2_addendum:{flag}", text, "agents.json stage2_addenda")
                          for flag, text in (agent.get("stage2_addenda") or {}).items()
                          if stage2.get(flag) and text)

    # The Critic's prompt carries no round count or arc depth (M10a). It gets
    # the round only as the identifier log_retreat needs.
    if aid == "critic" and season >= 2:
        header = f"# Research Forum\n\n(Round id for log_retreat: {round_num}.)"
    else:
        header = f"# Research Forum - Round {round_num}"

    prompt = textwrap.dedent(f"""\
    {header}

    {agent_prompt}

    {addenda}

    ## Your Task
    {topic_line}
    {task_instruction}

    ## Output

    Write your post to this exact path:
    {FORUM_DIR}/{post_num:03d}_{aid}.md

    Post format:
    ```
    ---
    author: "{agent['name']}"
    date: "{ts}"
    type: [literature_scan / anomaly_report / data_report / review / research_agenda / response / synthesis]
    references: []
    ---

    # [Your Title]

    [Content: 500-1500 words. Show evidence. Be specific.]
    ```

    ## Rules

    - Every factual claim must be backed by a query (OpenAlex API call, KNA command, or pandas code).
    - Do NOT fabricate results. If a query returns nothing useful, say so.
    - When responding to another agent, reference their post filename.
    - Focus on what's INTERESTING, what's MISSING, and what's DOABLE.
    - Write in English. Korean terms (bill names, committee names, politician names) are fine.
    - Complete ALL items in your Completion Checklist before finishing.

    ## Current Forum State

    {forum_state}
    {knowledge}
    {abstracts}
    {findings}
    {existing_articles}
    {notes}
    {waivers}
    {arc_block}
    {card_block}
    {ledger_block}
    {verdict_note}
    {pitfall_block}
    {diversity_block}
    """)
    return prompt


def pitfall_flags_for(post: Path) -> str:
    """The 'Data pitfall flags' block for an Analyst post (empty without a
    match). Never raises, since the scan must not block a round."""
    try:
        import prechecks
        return prechecks.pitfall_flags_block(prechecks.pitfall_hits(Path(post).read_text(encoding="utf-8")),
                                             Path(post).name)
    except Exception as e:
        print(f"  [Pitfalls] scan unavailable: {e}")
        return ""


def record_pitfall_flags(post: Path, round_num: int, run_id: str | None) -> list[dict]:
    """A2: scan an accepted Analyst post's code blocks against the pitfall
    registry, print the matches, and log them to knowledge/pitfall_flags.jsonl
    and the run's private sidecar. Flag only."""
    try:
        import prechecks
        hits = prechecks.pitfall_hits(Path(post).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  [Pitfalls] scan unavailable: {e}")
        return []
    ids = sorted({h["id"] for h in hits})
    print(f"  [Pitfalls] {Path(post).name}: " + (f"{len(hits)} flag(s) ({', '.join(ids)}), shown to the Critic"
                                                 if hits else "no flags"))
    if hits:
        row = {"ts": _now(), "round": round_num, "post": Path(post).name, "run_id": run_id,
               "hits": [{"id": h["id"], "line": h["line"]} for h in hits]}
        try:
            _append_jsonl(KNOWLEDGE_DIR / "pitfall_flags.jsonl", row)
        except OSError as e:
            print(f"  [Pitfalls] could not log the flags: {e}")
        if run_id:
            claude_cli.update_sidecar(run_id, pitfall_flags=row["hits"])
    return hits


def season2_task(agent, position, is_opening, order_ids):
    """Per-role task text for Season 2 (literature-first question, prediction
    test, depth-first). See SEASON2.md for the rationale."""
    aid = agent["id"]
    if aid == "literature_scout":
        if is_opening:
            return (
                "SEASON 2, OPENING ROUND OF AN ARC. Derive the arc's first question from the arc prior below "
                "and the literature, and state it as ONE testable prediction for a measurable KNA quantity in a "
                "'Prediction to Test' subsection: what the literature predicts, what would count as failure. "
                "Cite the closest existing answer (DOI). Classify the gap as (a) standard prediction may fail in "
                "Korean data, (b) newly measurable, or (c) two literatures predict opposite things, in a 'Gap "
                "Type' subsection. Check the 'questions already taken' list: a restatement of a prior arc or "
                "article is a duplicate. Tell Analyst exactly what to compute. 'Studied abroad but not in Korea' "
                "and 'connect literatures X and Y' are not admissible. Use `type: research_agenda`."
            )
        return (
            "SEASON 2, CONTINUING ROUND: DEPTH FIRST. Do not open a new question while the arc's prediction "
            "is still being tested. Bring literature to bear on the standing result: the closest existing answer, "
            "the mechanism the literature would offer for the observed discrepancy, and the one test (preferably "
            "the arc falsifier) that would discriminate between explanations. Keep the 'Gap Type' subsection "
            "current. Use `type: literature_scan` or `response`."
        )
    if aid == "data_analyst":
        if is_opening:
            return (
                "SEASON 2, OPENING ROUND OF AN ARC: PREDICTION TEST. Read Scout's 'Prediction to Test'. Write "
                "the baseline (Scout's predicted value or sign, and the arc prior below) down BEFORE computing. "
                "Compute the quantity, code shown, and report baseline vs observed in substantive units with N in "
                "a 'Baseline vs Observed' table. A confirmed prediction is a result; a failed one is the arc's "
                "anomaly. Do not widen the question or add a second topic. If the Topic Diversity Check below says "
                "BLOCK, test only what is genuinely new and report the overlap. Use `type: data_report`."
            )
        return (
            "SEASON 2, CONTINUING ROUND: DEPTH FIRST. Attack the standing result with alternative measures, "
            "subsamples, placebo periods, the N>=10 guardrail, and above all the arc falsifier below. Present a "
            "'Survival Table' (test, what the prediction implied, result, survived / weakened / overturned). "
            "If the finding dies, say so; a retreat is a result. Use `type: data_report`."
        )
    if aid == "critic":
        # No round counts, depth rules, drafting triggers or monitor numbers
        # here (M10a). The label definitions live in the Critic prompt.
        return (
            "SEASON 2. Review in the order your prompt gives. Check whether the question repeats an earlier "
            "arc or article (the Topic Diversity Check below, when present), whether the prediction was stated "
            "before the data were touched and the test could have failed, whether the literature already answers "
            "it, and whether the arc falsifier has been tested. Then write the scoring block and return the same "
            "verdict and labels as your structured output, using the label definitions in your prompt. If the "
            "finding stands, Next Steps name the next kill test. Log any retreat with its new evidence."
        )
    return "Read the existing posts and respond substantively to at least one."


# ==========================================================================
# Agent runs (claude_cli + staging)
# ==========================================================================

class AgentRunFailed(RuntimeError):
    """A classified agent failure. The run's changes were rolled back."""

    def __init__(self, role: str, failure: str, result=None, quarantine=None, detail: str = ""):
        self.role, self.failure, self.result, self.quarantine = role, failure, result, quarantine
        super().__init__(f"{role} run failed ({failure}{': ' + detail if detail else ''})")


class RoundStopped(RuntimeError):
    """A check stopped the round before the next agent (Stage 2)."""


@dataclass
class AgentOutcome:
    post: Path
    run_id: str
    result: object                                # claude_cli.CallResult
    containment: dict = field(default_factory=dict)


def _agent_env() -> dict:
    """Extra environment for agents. KBL_DATA and PATH are inherited, and the
    KNA CLI's folder is added to PATH only when the CLI is not on it."""
    if shutil.which("kna") is None and KNA_CLI_FALLBACK.exists():
        return {"PATH": os.environ.get("PATH", "") + os.pathsep + str(KNA_CLI_FALLBACK.parent)}
    return {}


def _staged_call(agent, prompt_text, post: Path, round_num: int, *, user_message: str = AGENT_MESSAGE,
                 schema: dict | None = None, manifest=None, max_continuations: int = 2):
    """One agent call inside a staging run. Returns (CallResult, commit
    report). A failed call is rolled back (changes quarantined under
    knowledge/staging/failed_<run_id>/) and raises AgentRunFailed."""
    aid = agent["id"]
    run_id = claude_cli.new_run_id(aid, round_num)
    run = staging.begin(run_id, aid)
    try:
        res = claude_cli.run_claude(
            "agent", prompt_text, role=aid, user_message=user_message, schema=schema,
            expect_file=post, round_num=round_num, arc_id=_arc_id(round_num), effort=EFFORT_OVERRIDE,
            extra_env={**_agent_env(), **staging.env(run)}, max_continuations=max_continuations,
            prompt_manifest=manifest)
    except Exception as e:
        quarantine = staging.rollback(run, f"wrapper error: {e}")
        raise AgentRunFailed(aid, "auth_or_config", None, quarantine, str(e)) from e
    except BaseException:
        staging.rollback(run, "interrupted")
        raise
    # M04 (6): the posting order of the round goes into the private sidecar.
    claude_cli.update_sidecar(res.sidecar_path, posting_order=[a["id"] for a in load_agents()])
    failure, detail = res.failure, ""
    if res.ok and schema is not None and res.structured is None:
        # M10a: a Critic success without its structured verdict is a failed run.
        # The sidecar records it as a classified failure so run_arc counts it.
        failure, detail = "structured_missing", "no structured_output for --json-schema"
        claude_cli.update_sidecar(res.sidecar_path, ok=False, failure="unknown", cli_failure="ok",
                                  orchestrator_failure=failure)
    if failure != "ok":
        quarantine = staging.rollback(run, failure)
        raise AgentRunFailed(aid, failure, res, quarantine, detail)
    report = staging.commit(run, post, agent.get("writes") or [])
    res.containment = report
    for v in report.get("violations") or []:
        print(f"  [Staging] reverted {v.get('path')} ({v.get('change')}): {v.get('action')}")
    if report.get("retreats_merged"):
        print(f"  [Staging] {report['retreats_merged']} retreat(s) merged")
    for r in report.get("retreats_rejected") or []:
        print(f"  [Staging] retreat rejected ({r.get('rejected')}): {str(r.get('finding'))[:60]}")
    for d in report.get("dictionaries") or []:
        print(f"  [Staging] dictionary: {d}")
    return res, report


def _provenance_keys(agent, round_num: int, res, attempt: int | None = None) -> dict:
    """Orchestrator-owned frontmatter keys (forum_index.ORCHESTRATOR_KEYS)."""
    keys = {"round": round_num}
    arc = arc_of_round(round_num)
    if arc is not None:
        keys["arc"] = arc
    keys.update({
        "role": agent["id"],
        "run_id": res.run_id,
        "model": res.model,
        "models_used": list(res.models_used or []),
        "claude_code_version": res.cli_version,
        "effort": EFFORT_OVERRIDE or agent.get("effort"),
        "num_turns": res.num_turns,
        "terminal_reason": res.terminal_reason,
        "attempt": attempt if attempt is not None else res.attempts,
    })
    return keys


def _append_card_vs_observed(post: Path, round_num: int) -> None:
    """Stage 2 (prediction_cards): ingest the Analyst's results into the
    quantities ledger and append the orchestrator's Card vs Observed table."""
    import prediction_card as pc
    card = pc.load_cards().get(int(round_num))
    if not card:
        return
    arc = get_active_arc()
    pc.ingest_results(round_num, arc_start=_int(arc.get("start_round")), arc=arc.get("arc_id"))
    text = post.read_text(encoding="utf-8")
    if "## Card vs Observed" in text:
        return
    table = pc.compare_card(card, pc.load_results(round_num))
    with open(post, "a", encoding="utf-8") as f:
        f.write(("\n" if text.endswith("\n") else "\n\n") + table.rstrip() + "\n")
    print(f"  [Card] Card vs Observed appended to {post.name}")


def _lint_post(post: Path, run_id: str) -> list:
    """M02 leak lint in FLAG mode, which reports and never blocks. Hits go to the
    private sidecar with the pattern id and line, not the matched text."""
    try:
        import leak_lint
        hits = leak_lint.scan_text(post.read_text(encoding="utf-8"), path=post.name)
    except Exception as e:
        print(f"  [Leak lint] unavailable: {e}")
        return []
    if hits:
        ids = sorted({str(h.get("pattern_id")) for h in hits})
        print(f"  [Leak lint · FLAG] {post.name}: {len(hits)} hit(s), patterns {', '.join(ids)}")
        claude_cli.update_sidecar(run_id, leak_flags=[{k: h.get(k) for k in ("pattern_id", "source", "line", "block")}
                                                      for h in hits])
    return hits


def run_agent(agent, round_num, total_rounds, seed_topic=None, dry_run=False, *, post_num=None):
    """Execute one agent through claude_cli.run_claude inside a staging run.

    Returns the accepted run's AgentOutcome (None on a dry run). A failed run
    is rolled back and raises AgentRunFailed. Post-run order (M13): staging
    commit, frontmatter keys and the Card vs Observed table, then the leak
    lint."""
    aid = agent["id"]
    post_num = post_num or next_post_number()
    post = FORUM_DIR / f"{post_num:03d}_{aid}.md"
    manifest = []
    prompt_text = build_prompt(agent, round_num, total_rounds, seed_topic, post_num=post_num, manifest=manifest)
    effort = EFFORT_OVERRIDE or agent.get("effort")

    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  {agent['name']}")
    print(f"  Round {round_num} | Post #{post_num}")
    print(f"  Tools: {','.join(agent.get('allowed_tools') or [])}")
    if effort:
        print(f"  Effort: {effort}")
    print(f"{sep}")

    if dry_run:
        # Prompts stay out of workspace/, where later agents could read them.
        # The common rules are appended as claude_cli appends them to a real run.
        d = LOGS_DIR / "prompts"
        d.mkdir(parents=True, exist_ok=True)
        prompt_file = d / f"dryrun_r{round_num:02d}_{post_num:03d}_{aid}.md"
        rules = claude_cli.common_rules_text(load_config(), "agent")
        full = prompt_text.rstrip() + "\n" + (f"\n## Common Rules\n\n{rules}\n" if rules else "")
        prompt_file.write_text(full)
        print(prompt_text[:600] + "\n  ... (truncated)")
        print(f"  Full prompt written to {prompt_file}")
        return None

    schema = None
    if aid == "critic":
        import verdict
        schema = verdict.load_schema()
    print("  Running...")
    res, report = _staged_call(agent, prompt_text, post, round_num, schema=schema, manifest=manifest)
    forum_index.set_frontmatter_keys(post, _provenance_keys(agent, round_num, res))
    if aid == "data_analyst" and _stage2(load_config(), "prediction_cards"):
        try:
            _append_card_vs_observed(post, round_num)
        except Exception as e:
            print(f"  [Card] Card vs Observed failed (non-fatal): {e}")
    _lint_post(post, res.run_id)

    content = post.read_text()
    title = next((l for l in content.split("\n") if l.startswith("# ") and "---" not in l), "")
    print(f"  Posted: {post.name} ({len(content.split())} words, {res.attempts} attempt(s))")
    print(f"  {title}")
    return AgentOutcome(post=post, run_id=res.run_id, result=res, containment=report)


def _card_fix_run(agent, outcome: AgentOutcome, round_num: int, errors: list[str], total_rounds: int):
    """One Scout resume with the card's validation errors (M09). It counts
    against the same cap of two continuations as the Scout run itself."""
    import prediction_card as pc
    used = max(0, int(outcome.result.attempts or 1) - 1)
    if used >= 2:
        print("  [Card] no continuation left for a card fix")
        return None
    post = outcome.post
    post_num = forum_index.post_meta(post).get("post_num")
    prompt_text = build_prompt(agent, round_num, total_rounds, post_num=post_num)
    msg = pc.continuation_message(errors) + f"\nYour post is {post}. Edit that file in place."
    res, _ = _staged_call(agent, prompt_text, post, round_num, user_message=msg, max_continuations=0)
    forum_index.set_frontmatter_keys(post, {"attempt": int(outcome.result.attempts or 1) + res.attempts})
    return res


def _commit_scout_card(agent, outcome: AgentOutcome, round_num: int, total_rounds: int) -> None:
    """Stage 2 (prediction_cards): validate the Scout's card and commit it
    before the Analyst starts. An invalid card gets one fix run, then the
    round stops with 'no valid card'."""
    import prechecks
    import prediction_card as pc
    gate = get_active_arc()

    def check():
        card = pc.extract_card(outcome.post.read_text(encoding="utf-8"))
        return card, pc.validate(card, gate, pc.load_cards())

    card, errors = check()
    if errors:
        print(f"  [Card] {len(errors)} validation error(s): {'; '.join(errors[:3])}")
        _card_fix_run(agent, outcome, round_num, errors, total_rounds)
        card, errors = check()
    if errors:
        raise RoundStopped("no valid card: " + "; ".join(errors[:3]))
    events = prechecks.load_trace(outcome.result.events_paths)
    path = pc.commit_card(round_num, card, outcome.post, gate=gate,
                          data_exposed=pc.data_exposed_from_trace(events))
    print(f"  [Card] committed {path.name}")


def _ensure_card(round_num: int) -> None:
    """Stage 2 (prediction_cards): the Analyst never starts without a
    committed card. A resumed round commits a valid card from its Scout post,
    otherwise the round stops."""
    import prediction_card as pc
    if pc.load_cards().get(int(round_num)):
        return
    scout = _role_post(round_num, "literature_scout")
    if scout is None:
        raise RoundStopped(f"no Scout post in R{round_num}, so no card to commit")
    gate = get_active_arc()
    card = pc.extract_card(scout.read_text(encoding="utf-8"))
    errors = pc.validate(card, gate, pc.load_cards())
    if errors:
        raise RoundStopped("no valid card: " + "; ".join(errors[:3]))
    path = pc.commit_card(round_num, card, scout, gate=gate)
    print(f"  [Card] committed {path.name} from {scout.name}")


def _before_agent(role: str, round_num: int, cfg: dict) -> None:
    """Stage 2 hooks before an agent starts. Nothing runs while the flags are off."""
    if role == "data_analyst" and _stage2(cfg, "prediction_cards"):
        _ensure_card(round_num)
    if role == "critic" and _stage2(cfg, "claim_sheet_first"):
        try:
            import claim_sheet
            claim_sheet.build(round_num)
            print(f"  [Claim sheet] workspace/r{round_num}/claim_sheet.md written")
        except Exception as e:
            print(f"  [Claim sheet] failed (non-fatal): {e}")


def _after_post(agent, outcome: AgentOutcome, round_num: int, total_rounds: int, args, cfg: dict) -> None:
    """Hooks on an accepted post, keyed by the run's own post path and run id."""
    aid = agent["id"]
    post = outcome.post
    arc = get_active_arc()
    arc_start = _int(arc.get("start_round"))
    season2 = cfg.get("season", 1) >= 2

    # M10a: the structured output is the Critic's verdict of record.
    if aid == "critic":
        try:
            import verdict
            verdict.record(round_num, _arc_id(round_num, arc), post, outcome.result.structured,
                           outcome.run_id, events_paths=outcome.result.events_paths)
        except Exception as e:
            print(f"  [Verdict] record failed (non-fatal, the post's YAML block stands): {e}")

    # A2 · Data pitfall scan of the Analyst's code (flag only, shown to the Critic).
    if aid == "data_analyst":
        record_pitfall_flags(post, round_num, outcome.run_id)

    # C9 · Citation verification on the just-written post.
    if not args.skip_citation_verify:
        try:
            verify_citations(post)
        except Exception as e:
            print(f"  [Citation Verify · C9] error (non-fatal): {e}")

    # Stage 2 · Scripted prechecks (FLAG only).
    if _stage2(cfg, "prechecks"):
        try:
            import prechecks
            r = prechecks.run_all(post, aid, round_num, events=outcome.result.events_paths)
            print(f"  [Prechecks] {post.name}: {r.get('counts')}")
        except Exception as e:
            print(f"  [Prechecks] failed (non-fatal): {e}")

    if season2 and aid == "literature_scout":
        # Topic-diversity check on this run's own Scout post. The result is
        # injected into the Analyst's and Critic's prompts this round.
        try:
            import topic_diversity
            r = topic_diversity.check_post(post, round_num=round_num, arc_start=arc_start,
                                           run_id=outcome.run_id)
            print(f"  [Diversity] {post.name}: {r['status'].upper()} "
                  f"(max cosine {r.get('max_cosine') or 0:.2f}, prior items {r.get('n_prior')})")
        except Exception as e:
            print(f"  [Diversity] check failed (non-fatal): {e}")
        if _stage2(cfg, "prediction_cards"):
            _commit_scout_card(agent, outcome, round_num, total_rounds)
        if _stage2(cfg, "annotator") and arc_start == round_num:
            import taxonomy_monitor
            taxonomy_monitor.annotate_arc_opening(post, round_num=round_num, arc_id=_arc_id(round_num, arc))

    ext = (outcome.containment or {}).get("external_writes") or []
    if ext:
        # arc_status is tracked and pushed, so it gets repo-relative
        # locations only. The private patch file keeps the full detail.
        # last_round stays run_arc's last decided round (V-01), so the round
        # that stopped is decided after --ack-stop.
        _update_arc_status(state="external_write", reason=f"{aid} run {outcome.run_id} wrote outside the repo",
                           external_writes=_public_changes(ext)[:20], stopped_round=round_num)
        claude_cli.notify("KNA forum: external write", f"R{round_num} {aid} run {outcome.run_id} changed a "
                                                        "watched repository or data directory")
        print(f"  STOP: external write by {aid} ({len(ext)} change(s)). See logs/external_writes/.")
        sys.exit(1)
    _stop_on_researcher_owned((outcome.containment or {}).get("researcher_owned_changed") or [],
                              round_num, aid, outcome.run_id)


def _repo_rel(p) -> str:
    """A repo-relative path for tracked files (arc_status.json)."""
    try:
        return staging._rel(Path(p))
    except (ValueError, OSError):
        return Path(p).name


def _public_changes(changes: list[dict]) -> list[dict]:
    try:
        import write_guard
        return write_guard.public_changes(changes)
    except Exception:
        return [{"kind": c.get("kind"), "path": c.get("path")} for c in changes]


def _stop_on_researcher_owned(owned: list[dict], round_num: int, role: str, run_id) -> None:
    """A researcher-owned file (notes, waivers, topic_gate.md, the decision
    files) changed during an agent run. It is kept, since it may be the
    researcher's own edit, but nothing continues until someone has checked
    it (run_arc.py --ack-stop), because the change would reach later prompts
    and the next round commit."""
    if not owned:
        return
    paths = ", ".join(c.get("path", "?") for c in owned)
    _update_arc_status(state="researcher_file_changed",
                       reason=f"researcher-owned file(s) changed during the R{round_num} {role} run {run_id}: "
                              f"{paths}", researcher_owned_changes=owned[:20], stopped_round=round_num)
    claude_cli.notify("KNA forum: researcher-owned file changed",
                      f"R{round_num} {role} run {run_id}: {paths}. Check it, then run_arc.py --ack-stop "
                      f"--researcher-files keep or restore")
    print(f"  STOP: researcher-owned file(s) changed during the {role} run: {paths}. The start and end "
          f"versions are in knowledge/staging/. Check them, then rerun with python3 run_arc.py --ack-stop "
          f"--researcher-files keep (the changes stay) or --researcher-files restore (the start versions "
          f"come back).")
    sys.exit(1)


# ==========================================================================
# Human comments, round summaries, verdicts
# ==========================================================================

def add_human_comment(comment_text, topic=None, by=None):
    """Save a note as context (not as a forum post). This is the only writer
    of knowledge/human_context.md. by records who wrote the note (the
    researcher, or the orchestrating Claude session), and prompts attribute
    the note to it. The note is bound to the active arc while one is open,
    else marked pending and bound by check_topic_gate at the next arc open."""
    arc = get_active_arc()
    bound = str(arc["start_round"]) if (not topic and arc.get("start_round") and _arc_is_open()) else "pending"
    legacy, notes = _read_notes()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    by = re.sub(r"\s+", " ", str(by or "unrecorded")).replace("|", "/").strip() or "unrecorded"
    notes.append({"ts": ts, "source": "--comment", "by": by, "arc_start": bound, "text": comment_text.strip()})
    _write_notes(notes, legacy)
    where = f"the arc opened at round {bound}" if bound != "pending" else "the next arc (pending)"
    print(f"\n  Note saved for {where}. It is injected into agent prompts and may be quoted in public posts.")
    print(f"  Content: {comment_text[:100]}...")
    return HUMAN_CONTEXT_FILE


def generate_round_summary(round_num, topic=None):
    """Generate a summary for a completed round (claude_cli task 'summary').
    Returns the CallResult, or None when nothing ran."""
    SUMMARIES_DIR.mkdir(exist_ok=True)

    round_posts = forum_index.round_posts(round_num, forum_dir=FORUM_DIR)
    if not round_posts:
        return None

    forum_text = "\n\n".join(
        f"--- {p.name} ---\n{p.read_text()}" for p in round_posts
    )
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary_file = SUMMARIES_DIR / f"round_{round_num:02d}.md"

    prompt = textwrap.dedent(f"""\
    You are a research forum moderator. Summarize Round {round_num}.

    Write a SHORT summary (100-150 words max) followed by one punchline quote per agent.

    Write the summary to: {summary_file}

    Use this EXACT format:
    ```
    ---
    round: {round_num}
    date: "{ts}"
    topic: "[Write a SHORT descriptive title for this round, 5-8 words max. E.g., 'committee gatekeeping and bill survival' or 'legislator wealth and voting behavior'. NOT 'continuing discussion'.]"
    ---

    # Round {round_num} Summary

    [2-3 sentence overview of the round. What was the main question? What was discovered? What's unresolved?]

    ## Key Quotes

    > **Scout**: "[Most important single sentence from Scout's post - verbatim or near-verbatim]"

    > **Analyst**: "[Most striking finding or number from Analyst's post - verbatim or near-verbatim]"

    > **Critic**: "[Sharpest judgment or recommendation from Critic's post - verbatim or near-verbatim]"

    ## Findings Status

    | Finding | Status |
    |---------|--------|
    | [Key finding 1 from this round] | preliminary / confirmed / contested |
    | [Key finding 2] | preliminary / confirmed / contested |

    **Verdict**: [Critic's verdict if available] | **Next**: [One sentence on what Round N+1 should tackle]
    ```

    Rules:
    - Quotes should be the punchline of each agent's post - the one line a reader would remember
    - NEVER include inline coefficients (beta, SE, p-values) in quotes or overview text
    - Use substantive magnitude instead: "a 12 percentage-point penalty", "roughly twice as likely"
    - Findings Status: mark as "confirmed" if multiple agents agree, "contested" if disagreement exists, "preliminary" if new
    - Findings table: describe findings in plain language, no beta/SE/p notation
    - If a finding from a PREVIOUS round was addressed this round, update its status
    - Keep the overview to 2-3 sentences, not more
    - Total length under 200 words (excluding quotes and table)
    - No em dashes (---). Use commas or rephrase.

    ## Posts to Summarize

    {forum_text}
    """)

    print(f"\n  Generating Round {round_num} summary...")
    try:
        res = claude_cli.run_claude("summary", prompt, user_message="Write the round summary now.",
                                    expect_file=summary_file, round_num=round_num,
                                    arc_id=_arc_id(round_num))
    except claude_cli.ClaudeCLIError as e:
        print(f"  WARNING: Summary not generated ({e})")
        return None
    if summary_file.exists():
        print(f"  Summary: {summary_file.name}")
    else:
        print(f"  WARNING: Summary not generated ({res.failure})")
    return res


def _extract_verdict(round_num):
    """The round's verdict of record (verdicts.jsonl, else the Critic post's
    scoring block for legacy rounds)."""
    import verdict
    record = verdict.verdict_of_record(round_num)
    return record.get("verdict") if record else None


def _pause_usage_limit(round_num: int, role: str, res) -> None:
    """M11 pause-only policy. Records paused_usage_limit and exits 75."""
    resume = getattr(res, "resume_at", None)
    _update_arc_status(state="paused_usage_limit", resume_after=resume,
                       reason=f"usage limit during the R{round_num} {role} run",
                       paused_round=round_num, paused_role=role, run_id=getattr(res, "run_id", None))
    print(f"  PAUSED: usage limit during the R{round_num} {role} run"
          f"{f', resets {resume}' if resume else ''}. Rerun with --resume after the reset.")
    sys.exit(claude_cli.EXIT_USAGE_LIMIT)


def _stop_on_failure(err: AgentRunFailed, round_num: int) -> None:
    quarantine = _repo_rel(err.quarantine) if err.quarantine else None
    owned = staging.rollback_report(err.quarantine).get("researcher_owned_changed") or []
    if owned:
        _update_arc_status(last_failure={"round": round_num, "role": err.role, "failure": err.failure,
                                         "run_id": getattr(err.result, "run_id", None),
                                         "quarantine": quarantine, "ts": _now()})
        _stop_on_researcher_owned(owned, round_num, err.role, getattr(err.result, "run_id", None))
    if err.failure == "usage_limit":
        _pause_usage_limit(round_num, err.role, err.result)
    # quarantine is repo-relative: arc_status.json is tracked and pushed.
    _update_arc_status(last_failure={"round": round_num, "role": err.role, "failure": err.failure,
                                     "run_id": getattr(err.result, "run_id", None),
                                     "quarantine": quarantine, "ts": _now()})
    if err.result is None or getattr(err.result, "ok", False):
        # claude_cli alerts on the failures it classifies. These it did not see.
        claude_cli.notify(f"KNA forum: {err.failure}", f"R{round_num} {err.role}: {err}")
    print(f"  FATAL: {err}. Changes quarantined in {quarantine}.")
    print(f"  Rerun with --resume to run the missing role(s) of R{round_num}.")
    sys.exit(1)


def _record_verdict_from_sidecar(round_num: int, critic_post: Path, run_id: str | None) -> None:
    """Record a verdict that a stopped process never recorded, from the
    Critic run's sidecar (structured_output), else from the post's YAML."""
    import verdict
    if any(_int(r.get("round")) == round_num for r in verdict.load_rows()):
        return
    structured = None
    side = claude_cli.find_sidecar(run_id) if run_id else None
    if side is not None:
        structured = _read_json(side).get("structured_output")
    verdict.record(round_num, _arc_id(round_num), critic_post, structured, run_id or "unrecorded")


def _finish_round(rnd: int, critic_post: Path, run_id: str | None, args, cfg: dict, topic=None) -> None:
    """Post-round steps. The ledger and taxonomy steps are idempotent and
    run first, then the summary (exit 75 on a usage limit), then the
    verdict report."""
    update_findings_tracker(rnd, critic_post=critic_post, run_id=run_id)
    if cfg.get("season", 1) >= 2:
        try:
            import taxonomy_monitor
            taxonomy_monitor.record_round(rnd, post_path=critic_post,
                                          out_file=KNOWLEDGE_DIR / "taxonomy.jsonl")
        except Exception as e:
            print(f"  [Taxonomy] record failed (non-fatal): {e}")

    res = generate_round_summary(rnd, topic=topic)
    if res is not None and res.failure == "usage_limit":
        _pause_usage_limit(rnd, "summary", res)

    # Auto-draft article if Critic gave a "pursue" verdict.
    # Season 2 is depth-first: drafting waits for the researcher
    # (or --auto-draft) so one arc yields one paper, not one per pursue.
    verdict = _extract_verdict(rnd)
    auto_draft = args.auto_draft or cfg.get("auto_draft_on_pursue", True)
    if verdict == "pursue" and not auto_draft:
        print(f"\n  Verdict: PURSUE - Season 2 depth-first: not auto-drafting. "
              f"When the arc is done: python3 draft_article.py --round {rnd}")
    elif verdict == "pursue":
        print(f"\n  Verdict: PURSUE - auto-drafting article...")
        try:
            result = subprocess.run(
                [sys.executable, str(BASE_DIR / "draft_article.py"), "--round", str(rnd)],
                capture_output=True, text=True, timeout=4 * 3600,
                cwd=str(WORKSPACE_DIR),
            )
            if result.returncode == 0:
                print(f"  Article drafted successfully.")
            elif result.returncode == 2:
                print(f"  Article failed its paper gates (exit 2). See workspace/failed_drafts/.")
            elif result.returncode == claude_cli.EXIT_USAGE_LIMIT:
                print(f"  Article drafting paused at a usage limit (exit 75).")
            else:
                print(f"  Article drafting failed (exit {result.returncode}).")
                if result.stderr:
                    print(f"  {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print(f"  Article drafting timed out (>4h).")
    elif verdict:
        print(f"\n  Verdict: {verdict.upper()} - no article generated.")


def _complete_last_round(args, cfg: dict, order) -> None:
    """If the latest round is complete but its post-round steps never ran
    (for example a usage limit during the summary), run them now. Only for
    rounds after the legacy grid, whose Critic posts carry a run_id."""
    rnd = forum_index.current_round(forum_dir=FORUM_DIR)
    if rnd <= forum_index.LEGACY_LAST_ROUND or forum_index.missing_roles(rnd, order, forum_dir=FORUM_DIR):
        return
    if (SUMMARIES_DIR / f"round_{rnd:02d}.md").exists():
        return
    critic = _role_post(rnd, "critic")
    if critic is None:
        return
    run_id = forum_index.read_frontmatter(critic).get("run_id")
    print(f"  [Resume] R{rnd} is complete but its post-round steps did not finish. Running them now.")
    try:
        _record_verdict_from_sidecar(rnd, critic, run_id)
    except Exception as e:
        print(f"  [Verdict] backfill failed (non-fatal): {e}")
    _finish_round(rnd, critic, run_id, args, cfg)


def _lock_file() -> Path:
    return LOGS_DIR / "run_forum.lock"


def _pid_alive(pid) -> bool:
    """True while this pid is a running run_forum process. After a crash the
    pid may be reused by an unrelated process, which must not hold the lock
    (that would stop every later run until a person removed it)."""
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        pass
    except (TypeError, ValueError, OSError):
        return False
    try:
        out = subprocess.run(["ps", "-o", "command=", "-p", str(int(pid))],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return True                  # cannot tell, so the lock holds
    cmd = out.stdout.strip()
    if not cmd:
        return out.returncode == 0
    return "run_forum" in cmd


def _release_lock(path: Path) -> None:
    try:
        if _read_json(path).get("pid") == os.getpid():
            path.unlink()
    except OSError:
        pass


def _acquire_lock() -> None:
    """One run_forum at a time (logs/run_forum.lock holds the pid). A lock
    left by a process that no longer exists is taken over. The lock also
    tells _check_unfinished_runs that no other run can own a leftover
    staging snapshot."""
    path = _lock_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            pid = _read_json(path).get("pid")
            if pid == os.getpid():
                return
            if pid and _pid_alive(pid):
                raise SystemExit(f"[BLOCKED · Concurrent run] another run_forum process (pid {pid}) is "
                                 f"running. Wait for it to finish.")
            path.unlink(missing_ok=True)   # stale lock of a process that died
            continue
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps({"pid": os.getpid(), "started": _now()}))
        atexit.register(_release_lock, path)
        return
    raise SystemExit("[BLOCKED · Concurrent run] could not take logs/run_forum.lock")


def _run_role(run_id: str) -> str:
    """literature_scout from r31_literature_scout_20260925T101500_ab12cd."""
    m = re.match(r"^r\d+_(.+?)(?:_\d{8}T\d{6}_[0-9a-f]{6}|_t\d+)?$", run_id)
    return m.group(1) if m else "unknown"


def _commit_record_for(post: Path) -> dict | None:
    """The staging COMMIT.json whose post is this file, if any."""
    rel = f"forum/{post.name}"
    for f in sorted((KNOWLEDGE_DIR / "staging").glob("*/COMMIT.json")):
        rec = _read_json(f)
        if rec.get("post") == rel:
            return rec
    return None


def _recovered_keys(m: dict, rec: dict) -> dict:
    """Frontmatter keys for a post whose run was committed but never keyed:
    identity from the staging commit, provenance from the run's sidecar."""
    keys = {"round": m["round"], "role": m["role"], "run_id": rec.get("run_id")}
    arc = arc_of_round(m["round"])
    if arc is not None:
        keys["arc"] = arc
    side_path = claude_cli.find_sidecar(rec["run_id"]) if rec.get("run_id") else None
    side = _read_json(side_path) if side_path else {}
    if side:
        attempts = side.get("attempts")
        keys.update({
            "model": side.get("model"), "models_used": list(side.get("models_used") or []),
            "claude_code_version": side.get("cli_version"), "effort": side.get("effort"),
            "num_turns": side.get("num_turns"), "terminal_reason": side.get("terminal_reason"),
            "attempt": len(attempts) if isinstance(attempts, list) else attempts,
        })
    return keys


def _check_unfinished_runs(dry_run: bool = False) -> None:
    """Before any run: a staging snapshot left by a run whose process died
    (it never reached commit or rollback) is rolled back now with
    staging.recover, which quarantines the partial changes to
    knowledge/staging/failed_<run_id>/. The caller holds the run_forum lock,
    so no live run owns such a snapshot. An incomplete snapshot, or an agent
    post without orchestrator keys of unknown origin, refuses the start. A
    post whose run was committed but never keyed is keyed now, with its
    provenance from the run's sidecar."""
    problems = []
    for run_id in staging.leftover_snapshots():
        if dry_run:
            problems.append(f"run {run_id} left a staging snapshot (a real run recovers it first)")
            continue
        try:
            q = staging.recover(run_id, _run_role(run_id))
        except Exception as e:
            problems.append(f"run {run_id} stopped before its staging commit or rollback and could not be "
                            f"recovered automatically ({e}). Compare forum/ and knowledge/ with its snapshot "
                            f"in knowledge/staging/_snapshots/{run_id}/, restore what it changed, then move "
                            "the snapshot folder aside.")
            continue
        rel = _repo_rel(q)
        report = staging.rollback_report(q)
        _update_arc_status(last_failure={"run_id": run_id, "role": report.get("role"), "failure": "recovered",
                                         "quarantine": rel, "ts": _now()})
        claude_cli.notify("KNA forum: run recovered", f"run {run_id} stopped before its staging commit. "
                                                      f"Its partial changes are in {rel}.")
        print(f"  [Resume] recovered run {run_id}: its partial changes were moved to {rel}")
        owned = report.get("researcher_owned_changed") or []
        if owned:
            _update_arc_status(state="researcher_file_changed",
                               reason=f"recovered run {run_id} left researcher-owned file changes",
                               researcher_owned_changes=owned[:20])
            raise SystemExit(f"[BLOCKED · Researcher-owned files] run {run_id} changed "
                             f"{', '.join(c['path'] for c in owned)}. Check them (both versions are in {rel}), "
                             "then rerun with python3 run_arc.py --ack-stop --researcher-files keep or restore.")
    for m in forum_index.index(forum_dir=FORUM_DIR):
        if m["source"] != "inferred" or (m["post_num"] or 0) <= forum_index.LEGACY_LAST_POST \
                or m["role"] not in forum_index.ROLE_ORDER:
            continue
        rec = _commit_record_for(m["path"])
        if rec and not dry_run:
            forum_index.set_frontmatter_keys(m["path"], _recovered_keys(m, rec))
            print(f"  [Resume] keyed {m['path'].name} from its staging commit (run {rec.get('run_id')})")
        elif not rec:
            problems.append(f"{m['path'].name} has no orchestrator keys and no staging commit record. "
                            "Move it aside or add its round, role and run_id keys by hand.")
    if problems:
        text = "\n".join(f"  - {p}" for p in problems)
        if dry_run:
            print(f"  [Resume] WARNING:\n{text}")
            return
        raise SystemExit(f"[BLOCKED · Unfinished run]\n{text}")


def print_summary():
    """Print forum table of contents."""
    posts = get_forum_posts()
    if not posts:
        print("\n  Forum is empty.")
        return

    print(f"\n{'=' * 60}")
    print(f"  FORUM SUMMARY ({len(posts)} posts)")
    print(f"{'=' * 60}")

    for p in posts:
        content = p.read_text()
        title = "Untitled"
        author = "Unknown"
        post_type = ""
        for line in content.split("\n"):
            if line.startswith("# ") and "---" not in line:
                title = line[2:].strip()
            if line.startswith("author:"):
                author = line.split(":", 1)[1].strip().strip('"')
            if line.startswith("type:"):
                post_type = line.split(":", 1)[1].strip().strip("[]")
        wc = len(content.split())
        print(f"\n  {p.name} ({wc} words)")
        print(f"    {title}")
        print(f"    by {author} [{post_type}]")

    print(f"\n  Posts: {FORUM_DIR}/")
    print(f"  Logs:  {LOGS_DIR}/")
    print(f"  Summaries: {SUMMARIES_DIR}/")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="AI Research Forum Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          python3 run_forum.py --topic "committee gatekeeping in the 22nd Assembly"
          python3 run_forum.py --rounds 2 --topic "polarization trends"
          python3 run_forum.py --agent critic --resume
          python3 run_forum.py --comment "Focus on party discipline next round" --by researcher
        """),
    )
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--agent", type=str, default=None, help="Run only matching agent")
    parser.add_argument("--topic", type=str, default=None, help="Seed topic for round 1")
    parser.add_argument("--resume", action="store_true", help="Keep existing posts")
    parser.add_argument("--dry-run", action="store_true", help="Preview prompts only")
    parser.add_argument("--comment", type=str, default=None,
                        help="Add a note for the active arc (or the next arc when none is open). Notes are "
                             "injected into agent prompts verbatim and may be quoted in public posts.")
    parser.add_argument("--by", type=str, default=None,
                        help="Who writes the --comment note, for example 'researcher' or 'orchestrating "
                             "Claude session' (default: $KNA_ACTOR). Prompts attribute the note to it.")
    parser.add_argument("--bypass-topic-gate", action="store_true",
                        help="Override topic_gate.md requirement (C2). Use with researcher consent only.")
    parser.add_argument("--skip-citation-verify", action="store_true",
                        help="Skip Crossref verification of posted DOIs (C9). Default: verify.")
    parser.add_argument("--order", choices=["scout-first"], default=None,
                        help="Posting order for this run. The forum posts Scout, Analyst, Critic "
                             "(agents.json forum_config.round_order).")
    parser.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], default=None,
                        help="Override every agent's reasoning effort for this run (default: per-agent in agents.json).")
    parser.add_argument("--allow-model-change", action="store_true",
                        help="Run although forum_config.model differs from the model the active arc opened with "
                             "(recorded in knowledge/arc_status.json).")
    parser.add_argument("--allow-data-change", action="store_true",
                        help="Run although the KNA data in $KBL_DATA changed since the active arc pinned it "
                             "(recorded in active_arc.json, arc_status.json and gate_events.jsonl).")
    parser.add_argument("--auto-draft", action="store_true",
                        help="Draft an article immediately on a pursue verdict (Season 1 behavior). "
                             "Season 2 default is depth-first: draft manually with draft_article.py --round N.")
    args = parser.parse_args(argv)

    global ROUND_ORDER_OVERRIDE, EFFORT_OVERRIDE, PREVIEW_ARC
    PREVIEW_ARC = None
    if args.order == "scout-first":
        ROUND_ORDER_OVERRIDE = ["literature_scout", "data_analyst", "critic"]
    EFFORT_OVERRIDE = args.effort
    cfg = load_config()

    for d in (FORUM_DIR, LOGS_DIR, WORKSPACE_DIR, SUMMARIES_DIR):
        d.mkdir(exist_ok=True)

    # Handle human comment
    if args.comment:
        by = args.by or os.environ.get("KNA_ACTOR")
        if not by:
            raise SystemExit("--comment needs --by <who> (for example --by researcher, or --by 'orchestrating "
                             "Claude session'), or KNA_ACTOR set. Prompts attribute the note to it.")
        add_human_comment(args.comment, topic=args.topic, by=by)
        if args.rounds == 1 and not args.agent:
            print("  Comment added. Run with --resume to continue the forum.")
            return

    all_agents = load_agents()
    agents = all_agents

    if args.agent:
        agents = [a for a in agents if args.agent.lower() in a["id"]]
        if not agents:
            print(f"No agent matching '{args.agent}'. Available: {[a['id'] for a in load_agents()]}")
            sys.exit(1)

    # Handle existing posts
    existing = list(FORUM_DIR.glob("*.md"))
    if existing and not args.resume and not args.dry_run and not args.comment:
        print(f"\n  {len(existing)} existing posts found.")
        resp = input("  Clear for fresh start? (y/N): ").strip().lower()
        if resp == "y":
            for f in existing:
                f.unlink()
            for f in LOGS_DIR.glob("*.log"):
                f.unlink()
            print("  Cleared.")
        else:
            print("  Keeping. Use --resume to skip this prompt.")

    # M02: agents read the KNA data through $KBL_DATA, which has no default.
    if not args.dry_run and not os.environ.get("KBL_DATA"):
        raise SystemExit("KBL_DATA is not set. Point it at the KNA processed-data directory "
                         "(for example export KBL_DATA=<path>) and rerun.")

    if not args.dry_run:
        status = _read_json(ARC_STATUS_FILE)
        if status.get("state") in ACK_STATES:
            raise SystemExit(f"[BLOCKED · {status['state']}] {status.get('reason') or ''}\n"
                             "Check the change, then acknowledge it with python3 run_arc.py --ack-stop"
                             + (" --researcher-files keep|restore." if status["state"] == "researcher_file_changed" else "."))
        # One arc, one paper: a closed arc runs no further agent rounds. The
        # post-round steps (--rounds 0) still run, and --topic opens a new arc.
        if not args.topic and args.rounds > 0 and get_active_arc().get("start_round") and not _arc_is_open():
            raise SystemExit(f"[BLOCKED · Closed arc] the active arc (from round "
                             f"{get_active_arc().get('start_round')}) is closed (state {status.get('state')}, "
                             f"action {status.get('action')}). Open a new arc with --topic and a signed "
                             "topic_gate entry.")
        _acquire_lock()
    elif not args.topic and get_active_arc().get("start_round") and not _arc_is_open():
        print("  [Dry run] the active arc is closed. A real run without --topic would be refused.")

    _check_unfinished_runs(dry_run=args.dry_run)

    # Round plan from frontmatter identity (M12). An incomplete latest round
    # resumes at its missing roles, otherwise the next round runs every role.
    order = tuple(a["id"] for a in all_agents)
    by_id = {a["id"]: a for a in all_agents}
    wanted = {a["id"] for a in agents}
    start_round, first_roles = forum_index.next_round_plan(order, forum_dir=FORUM_DIR)
    total_rounds = start_round + args.rounds - 1
    if args.dry_run and args.topic:
        PREVIEW_ARC = preview_arc(args.topic, start_round, bypass=args.bypass_topic_gate)

    agent_names = ", ".join(a["name"] for a in agents)
    tools_info = " | ".join(f"{a['id']}:{','.join(a.get('allowed_tools', []))}" for a in agents)
    print(f"\n  Research Forum (Season {cfg.get('season', 1)})")
    print(f"  Agents: {agent_names}")
    print(f"  Tools:  {tools_info}")
    print(f"  Rounds: {args.rounds} (starting from round {start_round})")
    if list(first_roles) != list(order):
        print(f"  Resuming R{start_round} at its missing role(s): {', '.join(first_roles)}")
    if args.topic:
        print(f"  Topic:  {args.topic}")
    print()

    # C2 · Topic-gate precheck (Pepinsky 2026). Runs before the first round
    # and blocks if this run opens a fresh arc without a signed entry in
    # topic_gate.md. A new arc starts at a fresh round, so --topic on an
    # incomplete round is refused unless it relaunches that arc's opening.
    if args.topic and list(first_roles) != list(order) and not args.bypass_topic_gate:
        arc = get_active_arc()
        if not (_int(arc.get("start_round")) == start_round and _norm(arc.get("seed")) and
                (_norm(arc.get("seed")) in _norm(args.topic) or _norm(args.topic) in _norm(arc.get("seed")))):
            raise SystemExit(f"R{start_round} is incomplete (missing {', '.join(first_roles)}). Finish it with "
                             "--resume before opening a new arc with --topic.")
    if not args.dry_run:
        check_topic_gate(
            seed_topic=args.topic or "",
            start_round=start_round,
            total_existing=len(forum_index.all_posts(forum_dir=FORUM_DIR)),
            bypass=args.bypass_topic_gate,
        )
        # M01 model lock, before any agent runs.
        check_model_lock(cfg, allow_change=args.allow_model_change)
        # A1 data pin, before every round (the post-round steps alone read no data).
        if args.rounds > 0:
            check_data_pin(allow_change=args.allow_data_change)
        _complete_last_round(args, cfg, order)

    dry_post = next_post_number()
    for i in range(args.rounds):
        if not args.dry_run and i > 0:
            # A1: every later round of a multi-round invocation is checked
            # again, because the data can change while a round runs.
            check_data_pin(allow_change=args.allow_data_change)
        if args.dry_run:
            rnd, roles = (start_round, list(first_roles)) if i == 0 else (start_round + i, list(order))
        else:
            rnd, roles = forum_index.next_round_plan(order, forum_dir=FORUM_DIR)
        # --agent runs the selected roles among the round's missing ones, in
        # order, and never a role before an earlier missing role.
        selected = []
        for r in roles:
            if r not in wanted:
                break
            selected.append(r)
        print(f"\n{'#' * 60}")
        print(f"  ROUND {rnd}")
        print(f"{'#' * 60}")
        if not selected:
            print(f"  R{rnd} needs {roles[0] if roles else 'no role'} next, which is not selected. Nothing to run.")
            break
        roles = selected
        seed = args.topic if i == 0 else None

        critic_outcome = None
        for role in roles:
            agent = by_id[role]
            try:
                if not args.dry_run:
                    _before_agent(role, rnd, cfg)
                outcome = run_agent(agent, rnd, total_rounds, seed_topic=seed, dry_run=args.dry_run,
                                    post_num=dry_post if args.dry_run else None)
                if args.dry_run:
                    dry_post += 1
                    continue
                _after_post(agent, outcome, rnd, total_rounds, args, cfg)
            except AgentRunFailed as e:
                _stop_on_failure(e, rnd)
            except RoundStopped as e:
                _update_arc_status(last_failure={"round": rnd, "role": role, "failure": "round_stopped",
                                                 "reason": str(e), "ts": _now()})
                claude_cli.notify("KNA forum: round stopped", f"R{rnd} before {role}: {e}")
                print(f"  STOP: {e}")
                sys.exit(1)
            if role == "critic":
                critic_outcome = outcome

        if not args.dry_run and critic_outcome is not None \
                and not forum_index.missing_roles(rnd, order, forum_dir=FORUM_DIR):
            _finish_round(rnd, critic_outcome.post, critic_outcome.run_id, args, cfg, topic=seed)

    print_summary()


if __name__ == "__main__":
    main()

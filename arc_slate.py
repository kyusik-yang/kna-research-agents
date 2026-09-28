#!/usr/bin/env python3
"""Arc slate: up to three isolated Scout candidates for the next arc (M24).

A manual tool, run before a topic-gate entry is signed and outside run_arc.
Nothing in the forum calls it.

1. propose. Up to three non-posting Scout calls through claude_cli (task
   "slate", effort from forum_config.effort_by_task). Each call runs in a
   temporary directory outside the repository with literature tools only
   (WebFetch, WebSearch), so it has no file tool that could read forum/,
   knowledge/ or summaries/, and its event trace is checked for any access
   anyway. Each call is seeded with a different non-bridge opportunity
   pattern, weighted toward the patterns the last six arc openers used least
   (taxonomy_monitor.opener_report). Candidates are deduplicated with the
   topic-diversity guard, written to knowledge/slates/<slate_id>.md in random
   order with no ranking, and logged in knowledge/gate_candidates.jsonl.
2. record. One decision (accept, reject or modify) with a one-line reason per
   listed candidate, appended to knowledge/taste_log.jsonl with decided_by.
   The default decider is the orchestrating Claude session under the standing
   delegation (D-10). A decision the researcher made is recorded with
   --by researcher.
3. stub. Only after every listed candidate has a decision, appends a gate
   entry for an accepted or modified candidate to topic_gate.md with truthful
   provenance. Without --auto-sign the entry is unsigned (no signed_by or
   signed line), so it cannot open an arc until someone signs it. With
   --auto-sign (D-10, standing delegation of 2026-09-25) the orchestrating
   Claude session supplies the gate fields and the entry is signed under the
   delegation, never in the researcher's name. The Stage 2 fields
   (decision_rule, null_paper) are required only while
   forum_config.stage2.binding_checks is on, and a signed entry never
   carries a placeholder. auto_arc.py (the one-command pipeline) calls stub
   with its own truthful labels: drafted_by names the automatic gate drafter
   and its model, signed_by the automatic selector under the standing
   delegation. Neither label may name the researcher.

The taste log is not fed back into Scout prompts.

Usage:
    python3 arc_slate.py propose [--k 3] [--seed 8374] [--dry-run]
    python3 arc_slate.py record <slate_id> <candidate_id> accept|reject|modify "<reason>" [--by WHO]
    python3 arc_slate.py status <slate_id>
    python3 arc_slate.py stub <slate_id> <candidate_id> --round N [--auto-sign --prior ... --falsifier ...
                              --decision-rule ... --null-paper ... --identification ... --exclusion-criteria ...
                              --seed ... --premise ... --sesoi ... --drafted-by ... --signed-by ...]
"""

import argparse
import json
import random
import re
import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
FORUM_DIR = BASE_DIR / "forum"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
SLATES_DIR = KNOWLEDGE_DIR / "slates"
TASTE_LOG = KNOWLEDGE_DIR / "taste_log.jsonl"
GATE_CANDIDATES = KNOWLEDGE_DIR / "gate_candidates.jsonl"
TOPIC_GATE_FILE = BASE_DIR / "topic_gate.md"
DATA_SOURCES_FILE = BASE_DIR / "DATA_SOURCES.md"

MAX_K = 3
DEFAULT_SEED = 8374
SLATE_TOOLS = ["WebFetch", "WebSearch"]
DECISIONS = ("accept", "reject", "modify")
DELEGATION_DATE = "2026-09-25"
AUTO_SIGNED_BY = ("orchestrating Claude session, signed under the researcher's standing delegation "
                  f"of {DELEGATION_DATE}")
# Default decider in the taste log. Decisions default to the orchestrating
# session (D-10), never to the researcher.
AUTO_DECIDED_BY = f"orchestrating Claude session, under the researcher's standing delegation of {DELEGATION_DATE}"
# Paths a slate call must never touch (relative to the repository root).
DENIED_DIRS = ("forum/", "knowledge/", "summaries/")
FILE_TOOLS = {"Read", "Glob", "Grep", "Bash", "Edit", "Write", "MultiEdit", "NotebookEdit", "LS"}

LIT_SCHEMA = {
    "type": "object",
    "properties": {
        "citation": {"type": "string"},
        "doi": {"type": "string"},
        "quoted_prediction": {"type": "string"},
        "location": {"type": "string"},
        "quantity_match": {"type": "string", "enum": ["exact", "analogous", "inferred"]},
    },
    "required": ["doi", "quoted_prediction", "location", "quantity_match"],
}

CANDIDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["candidate", "none"]},
        "reason_if_none": {"type": "string"},
        "question": {"type": "string"},
        "quantity": {"type": "string"},
        "population": {"type": "string"},
        "comparison": {"type": "string"},
        "outcome": {"type": "string"},
        "prediction": {"type": "string"},
        "premise": {"type": "string"},
        "closest_existing_answer": {"type": "string"},
        "gap": {
            "type": "object",
            "properties": {
                "gap_type": {"type": "string", "enum": ["a", "b", "c"]},
                "lit_a": LIT_SCHEMA,
                "lit_b": LIT_SCHEMA,
                "theory_source": LIT_SCHEMA,
                "magnitude": {"type": "string"},
                "measure": {"type": "string"},
                "why_not_available_before": {"type": "string"},
                "data_available_since": {"type": "string"},
            },
            "required": ["gap_type"],
        },
    },
    "required": ["status"],
}

SLATE_PROMPT = """\
You are Scout, a literature agent for a public research forum that studies the
Korean National Assembly with the KNA database described below. You are
drafting ONE candidate research question for the forum's next arc. You work
alone: you have no access to the forum's posts, ledgers or earlier decisions,
and you should not try to find them.

Direction for this call. Look for a question whose motivation is of this kind:

  {pattern}: {definition}

Do not motivate the question by connecting two literatures, and do not treat
"studied abroad but not in Korea" as a gap.

What to return (structured output):
- question: one sentence.
- quantity, population, comparison, outcome: the measurable KNA quantity the
  question is about, stated so an analyst could compute it from the data below.
- prediction: the sharpest prediction for that quantity, with a direction and
  a magnitude that would count.
- premise: the factual claim the question takes for granted, which the data
  could show to be false.
- closest_existing_answer: the closest published answer, with a DOI.
- gap: gap_type and its evidence.
  (a) a standard prediction that may fail in Korean data: theory_source with
      doi, the quoted prediction (a verbatim sentence), its location
      (abstract, page or section) and quantity_match, plus the magnitude that
      would count.
  (b) something newly measurable: measure, why_not_available_before,
      data_available_since.
  (c) two literatures that predict opposite results for the same quantity:
      lit_a and lit_b, each with doi, a verbatim quoted_prediction, its
      location and quantity_match (exact, analogous or inferred). If either
      side is inferred, say so. Do not present an inferred rival as a stated
      prediction.
- Verify every DOI through api.crossref.org or api.openalex.org before you
  cite it. Quote only sentences you actually read.

If you find no prediction worth testing in this direction, return
status "none" with reason_if_none. That is a valid answer.

Data available to the forum:

{data_sources}
"""

PATTERN_DEFINITIONS = {
    "puzzle_contradiction": "an observed pattern contradicts a standard prediction",
    "explanation_gap": "the pattern is known but has no accepted mechanism",
    "scope_mismatch": "a theory is applied outside the conditions it assumes",
    "evidence_gap": "a claim exists but has never been measured properly",
    "failure_risk_gap": "an overlooked failure mode or risk",
    "resource_bottleneck": "a missing dataset, measure, or instrument",
}


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def _append_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def new_slate_id(day: str | None = None, slates_dir: Path | None = None) -> str:
    d = slates_dir or SLATES_DIR
    day = day or datetime.now().strftime("%Y-%m-%d")
    sid, k = day, 2
    while (d / f"{sid}.json").exists() or (d / f"{sid}.md").exists():
        sid, k = f"{day}_{k}", k + 1
    return sid


def load_slate(slate_id: str, slates_dir: Path | None = None) -> dict:
    p = (slates_dir or SLATES_DIR) / f"{slate_id}.json"
    if not p.exists():
        raise SystemExit(f"[arc_slate] no slate {slate_id} ({p})")
    return json.loads(p.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# Seeds
# --------------------------------------------------------------------------

def seed_patterns(k: int, rng: random.Random, counts: dict | None = None) -> tuple[list[str], dict]:
    """k distinct non-bridge opportunity patterns, sampled without replacement
    with weight 1 / (1 + uses among the last six arc openers)."""
    counts = counts or {}
    pool = list(PATTERN_DEFINITIONS)
    weights = {p: 1.0 / (1 + int(counts.get(p, 0))) for p in pool}
    chosen = []
    for _ in range(min(k, len(pool))):
        rest = [p for p in pool if p not in chosen]
        total = sum(weights[p] for p in rest)
        x, acc = rng.random() * total, 0.0
        for p in rest:
            acc += weights[p]
            if x <= acc:
                chosen.append(p)
                break
        else:
            chosen.append(rest[-1])
    return chosen, weights


def opener_counts() -> dict:
    try:
        import taxonomy_monitor
        return taxonomy_monitor.opener_report().get("opportunity_counts_all", {})
    except Exception as e:
        print(f"  [arc_slate] opener report unavailable, equal weights: {e}")
        return {}


# --------------------------------------------------------------------------
# Trace check
# --------------------------------------------------------------------------

def _events(path: Path) -> list[dict]:
    text = Path(path).read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            data = json.loads(text)
            return [e for e in data if isinstance(e, dict)]
        except json.JSONDecodeError:
            pass
    out = []
    for line in text.splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(e, dict):
            out.append(e)
    return out


def tool_uses(events: list[dict]) -> list[dict]:
    uses = []
    for e in events:
        msg = e.get("message") if isinstance(e.get("message"), dict) else {}
        for block in msg.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                uses.append({"name": block.get("name"), "input": block.get("input") or {}})
    return uses


def trace_violations(events_paths: list[Path], repo_root: Path | None = None) -> list[dict]:
    """Tool calls that used a file tool, or touched the repository or its
    forum/, knowledge/ or summaries/ folders."""
    root = str((repo_root or BASE_DIR).resolve())
    out = []
    for p in events_paths or []:
        if not Path(p).exists():
            continue
        for u in tool_uses(_events(Path(p))):
            blob = json.dumps(u["input"], ensure_ascii=False)
            reasons = []
            if u["name"] in FILE_TOOLS:
                reasons.append("file tool")
                if any(d in blob for d in DENIED_DIRS):
                    reasons.append("denied folder")
            if root in blob:
                reasons.append("repository path")
            if reasons:
                out.append({"tool": u["name"], "reasons": reasons, "input": blob[:300]})
    return out


# --------------------------------------------------------------------------
# Candidates
# --------------------------------------------------------------------------

def c_constructed(gap: dict | None) -> bool:
    if not gap or gap.get("gap_type") != "c":
        return False
    return any((gap.get(side) or {}).get("quantity_match") == "inferred" for side in ("lit_a", "lit_b"))


def candidate_text(c: dict) -> str:
    """Flat text for the diversity guard and the annotator."""
    gap = c.get("gap") or {}
    parts = [c.get("question", ""), c.get("prediction", "")]
    for k in ("quantity", "population", "comparison", "outcome"):
        if c.get(k):
            parts.append(f"{k.capitalize()}: {c[k]}.")
    if gap.get("gap_type"):
        parts.append(f"Gap type ({gap['gap_type']}).")
        for side in ("theory_source", "lit_a", "lit_b"):
            s = gap.get(side) or {}
            if s.get("quoted_prediction"):
                parts.append(f"{s.get('citation') or s.get('doi', '')}: \"{s['quoted_prediction']}\"")
        for k in ("magnitude", "measure", "why_not_available_before", "data_available_since"):
            if gap.get(k):
                parts.append(f"{gap[k]}")
    if c.get("premise"):
        parts.append(c["premise"])
    return " ".join(p for p in parts if p).strip()


def _next_round() -> int:
    try:
        import forum_index
        return forum_index.current_round() + 1
    except Exception:
        pass
    import topic_diversity as td
    posts = sorted(FORUM_DIR.glob("*.md"))
    return (td._post_round(posts[-1]) + 1) if posts else 1


def dedupe(cands: list[dict]) -> dict:
    """Mark candidates that restate an earlier arc (guard status block) or
    an earlier candidate in this slate (pairwise cosine at or above warn)."""
    import topic_diversity as td
    live = [c for c in cands if c["status"] == "candidate"]
    warn, block, source = td.thresholds()
    info = {"warn": warn, "block": block, "thresholds_source": source, "model": td.model_name(),
            "max_pairwise_cosine": None}
    if not live:
        return info
    nxt = _next_round()
    corpus = td.prior_corpus(nxt, nxt)
    E = td.embed([c["text"] for c in live])
    if corpus:
        C = td.embed([x["text"] for x in corpus])
        sims = C @ E.T
        for j, c in enumerate(live):
            i = int(sims[:, j].argmax())
            cos = float(sims[i, j])
            c["guard"] = {"nearest": corpus[i]["id"], "cosine": round(cos, 3),
                          "status": td.status_for(cos, warn, block)}
            if c["guard"]["status"] == "block":
                c["status"] = "removed"
                c["removed_reason"] = f"restates {corpus[i]['id']} (cosine {cos:.2f}, block {block:.2f})"
    P = E @ E.T
    kept = []
    for j, c in enumerate(live):
        if c["status"] != "candidate":
            continue
        dup = next((k for k in kept if float(P[k, j]) >= warn), None)
        if dup is not None:
            c["status"] = "removed"
            c["removed_reason"] = (f"duplicates {live[dup]['candidate_id']} within the slate "
                                   f"(cosine {float(P[dup, j]):.2f}, warn {warn:.2f})")
        else:
            kept.append(j)
    if len(kept) > 1:
        info["max_pairwise_cosine"] = round(max(float(P[a, b]) for a in kept for b in kept if a < b), 3)
    return info


def run_slate_call(pattern: str, data_sources: str, cid: str) -> dict:
    """One isolated Scout call. Returns the candidate dict (never raises)."""
    import claude_cli
    prompt = SLATE_PROMPT.format(pattern=pattern, definition=PATTERN_DEFINITIONS[pattern],
                                 data_sources=data_sources)
    workdir = Path(tempfile.mkdtemp(prefix="kna_slate_"))
    try:
        res = claude_cli.run_claude(
            "slate", prompt, user_message="Draft your one candidate now.",
            schema=CANDIDATE_SCHEMA, cwd=workdir, tools=list(SLATE_TOOLS),
        )
    except Exception as e:
        return {"candidate_id": cid, "seed_pattern": pattern, "status": "failed", "failure": str(e)}
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    out = {"candidate_id": cid, "seed_pattern": pattern, "run_id": getattr(res, "run_id", None),
           "model": getattr(res, "model", None), "failure": getattr(res, "failure", None)}
    violations = trace_violations(getattr(res, "events_paths", None) or [])
    out["trace_violations"] = violations
    data = getattr(res, "structured", None)
    if not getattr(res, "ok", False) or not isinstance(data, dict):
        out["status"] = "failed"
        return out
    out.update({k: data.get(k) for k in ("question", "quantity", "population", "comparison", "outcome",
                                         "prediction", "premise", "closest_existing_answer", "gap",
                                         "reason_if_none")})
    if violations:
        out["status"] = "removed"
        out["removed_reason"] = "trace shows access to the repository or a file tool"
    elif data.get("status") == "none":
        out["status"] = "none"
    else:
        out["status"] = "candidate"
    out["c_constructed"] = c_constructed(out.get("gap"))
    out["text"] = candidate_text(out)
    return out


# --------------------------------------------------------------------------
# Slate file
# --------------------------------------------------------------------------

def _gap_lines(gap: dict) -> list[str]:
    if not gap:
        return []
    lines = [f"- Gap type: ({gap.get('gap_type', '?')})"]
    for side in ("theory_source", "lit_a", "lit_b"):
        s = gap.get(side)
        if s:
            lines.append(f"  - {side}: {s.get('citation') or ''} doi:{s.get('doi', '')}. "
                         f"\"{s.get('quoted_prediction', '')}\" ({s.get('location', '')}, "
                         f"quantity match {s.get('quantity_match', '?')})")
    for k in ("magnitude", "measure", "why_not_available_before", "data_available_since"):
        if gap.get(k):
            lines.append(f"  - {k.replace('_', ' ')}: {gap[k]}")
    return lines


def render_slate(slate: dict) -> str:
    """Markdown for the reader. Random order, no ranking, and no arc-level
    commitment fields (those belong to the gate entry, written later)."""
    listed = [c for c in slate["candidates"] if c["status"] == "candidate"]
    order = {cid: i for i, cid in enumerate(slate["display_order"])}
    listed.sort(key=lambda c: order.get(c["candidate_id"], 99))
    d = slate["dedupe"]
    lines = [f"# Arc slate {slate['slate_id']}", "",
             f"Generated by arc_slate.py on {slate['ts'][:16].replace('T', ' ')}. Each candidate was drafted by an "
             "isolated Scout call through claude_cli (no access to forum posts or ledgers), seeded with one "
             "opportunity pattern. Candidates appear in random order. The order carries no meaning.", "",
             f"- Seed patterns: {', '.join(slate['seed_patterns'])}",
             f"- Maximum pairwise cosine among listed candidates: "
             f"{d['max_pairwise_cosine'] if d['max_pairwise_cosine'] is not None else 'n/a'} "
             f"(diversity warn {d['warn']:.2f}, {d['model']})", ""]
    for c in listed:
        lines += [f"## {c['candidate_id']}", ""]
        for k in ("question", "quantity", "population", "comparison", "outcome", "prediction", "premise",
                  "closest_existing_answer"):
            if c.get(k):
                lines.append(f"- {k.replace('_', ' ').capitalize()}: {c[k]}")
        lines += _gap_lines(c.get("gap") or {})
        if c.get("c_constructed"):
            lines.append("  - One side of this (c) contradiction is inferred, not quoted (c_constructed).")
        g = c.get("guard")
        if g:
            lines.append(f"- Nearest earlier forum item: {g['nearest']}, cosine {g['cosine']:.2f} ({g['status']})")
        lines.append("")
    others = [c for c in slate["candidates"] if c["status"] != "candidate"]
    if others:
        lines += ["## Not listed", ""]
        for c in others:
            why = c.get("removed_reason") or c.get("reason_if_none") or c.get("failure") or c["status"]
            lines.append(f"- {c['candidate_id']} ({c['seed_pattern']}): {c['status']}. {why}")
        lines.append("")
    lines += ["## Taste log", "",
              "Record accept, reject or modify with a one-line reason for every listed candidate. "
              "A gate entry can be written only after that.", "", "```",
              *[f"python3 arc_slate.py record {slate['slate_id']} {c['candidate_id']} accept|reject|modify \"<reason>\" "
                f"--by \"<who decided>\""
                for c in listed], "```", "",
              "Without --by the decision is recorded as the orchestrating Claude session's (standing "
              "delegation of " + DELEGATION_DATE + "). Pass --by researcher only for a decision the researcher "
              "made.", ""]
    return "\n".join(lines)


def propose(k: int = MAX_K, seed: int = DEFAULT_SEED, dry_run: bool = False,
            slates_dir: Path | None = None) -> dict:
    k = max(1, min(int(k), MAX_K))
    rng = random.Random(seed)
    counts = opener_counts()
    patterns, weights = seed_patterns(k, rng, counts)
    slates_dir = slates_dir or SLATES_DIR
    slate_id = new_slate_id(slates_dir=slates_dir)
    print(f"  [arc_slate] slate {slate_id}: seeds {', '.join(patterns)} (seed {seed})")
    if dry_run:
        print(SLATE_PROMPT.format(pattern=patterns[0], definition=PATTERN_DEFINITIONS[patterns[0]],
                                  data_sources="<DATA_SOURCES.md>"))
        return {"slate_id": slate_id, "seed_patterns": patterns, "weights": weights}
    data_sources = DATA_SOURCES_FILE.read_text(encoding="utf-8") if DATA_SOURCES_FILE.exists() else ""
    cands = [run_slate_call(p, data_sources, f"C{i + 1}") for i, p in enumerate(patterns)]
    info = dedupe(cands)
    listed = [c["candidate_id"] for c in cands if c["status"] == "candidate"]
    rng.shuffle(listed)
    slate = {"slate_id": slate_id, "ts": _now(), "seed": seed, "seed_patterns": patterns,
             "weights": weights, "opener_counts": counts, "candidates": cands, "display_order": listed,
             "dedupe": info, "stub": None}
    slates_dir.mkdir(parents=True, exist_ok=True)
    (slates_dir / f"{slate_id}.json").write_text(json.dumps(slate, ensure_ascii=False, indent=1), encoding="utf-8")
    (slates_dir / f"{slate_id}.md").write_text(render_slate(slate), encoding="utf-8")
    _append_jsonl(GATE_CANDIDATES, [{
        "ts": slate["ts"], "source": "arc_slate", "drafted_by": "claude", "slate_id": slate_id,
        "candidate_id": c["candidate_id"], "status": c["status"], "model": c.get("model"),
        "run_id": c.get("run_id"), "seed_pattern": c["seed_pattern"],
        **{f: c.get(f) for f in ("question", "quantity", "population", "comparison", "outcome", "prediction",
                                 "premise")},
        "gap_type": (c.get("gap") or {}).get("gap_type"), "c_constructed": c.get("c_constructed"),
        "text": c.get("text", ""),
    } for c in cands if c["status"] in ("candidate", "removed", "none")])
    print(f"  [arc_slate] wrote {slates_dir / (slate_id + '.md')} ({len(listed)} listed of {len(cands)})")
    return slate


# --------------------------------------------------------------------------
# Taste log and gate stub
# --------------------------------------------------------------------------

def record(slate_id: str, candidate_id: str, decision: str, reason: str, by: str = AUTO_DECIDED_BY,
           slates_dir: Path | None = None) -> dict:
    slate = load_slate(slate_id, slates_dir)
    listed = {c["candidate_id"] for c in slate["candidates"] if c["status"] == "candidate"}
    if candidate_id not in listed:
        raise SystemExit(f"[arc_slate] {candidate_id} is not a listed candidate of slate {slate_id}")
    if decision not in DECISIONS:
        raise SystemExit(f"[arc_slate] decision must be one of {', '.join(DECISIONS)}")
    reason = (reason or "").strip()
    if not reason or "\n" in reason:
        raise SystemExit("[arc_slate] the reason must be one non-empty line")
    by = (by or "").strip()
    if not by or "\n" in by or (by.startswith("<") and by.endswith(">")):
        raise SystemExit("[arc_slate] --by must name who decided, on one line (not the <placeholder>)")
    row = {"ts": _now(), "slate_id": slate_id, "candidate_id": candidate_id, "decision": decision,
           "reason": reason, "decided_by": by}
    _append_jsonl(TASTE_LOG, [row])
    return row


def decisions(slate_id: str) -> dict:
    """Latest decision per candidate of one slate."""
    out = {}
    for r in _read_jsonl(TASTE_LOG):
        if r.get("slate_id") == slate_id:
            out[r["candidate_id"]] = r
    return out


def missing_decisions(slate: dict) -> list[str]:
    have = decisions(slate["slate_id"])
    return [c["candidate_id"] for c in slate["candidates"]
            if c["status"] == "candidate" and c["candidate_id"] not in have]


STAGE1_GATE_FIELDS = ("identification", "exclusion_criteria", "prior", "falsifier")
STAGE2_GATE_FIELDS = ("decision_rule", "null_paper")
GATE_FIELD_ARGS = STAGE1_GATE_FIELDS + STAGE2_GATE_FIELDS
# Written when given, never required: sesoi (Stage 2), and seed and premise,
# which replace the candidate's question and premise.
OPTIONAL_GATE_FIELDS = ("sesoi",)
OVERRIDE_FIELDS = ("seed", "premise")
PLACEHOLDER = "<to be written before signing>"


def _binding_checks_on() -> bool:
    """forum_config.stage2.binding_checks. An unreadable config counts as on,
    so --auto-sign then asks for every field."""
    try:
        import claude_cli
        return bool((claude_cli.load_forum_config().get("stage2") or {}).get("binding_checks"))
    except Exception:
        return True


def _one_line(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


def stub_seed(cand: dict, fields: dict | None = None) -> str:
    """The seed line a stub writes: fields["seed"] when given, else the
    candidate's question, on one line."""
    return _one_line((fields or {}).get("seed") or cand.get("question"))


def render_stub(slate: dict, cand: dict, round_num: int, fields: dict, auto_sign: bool,
                session_model: str | None = None, drafted_by: str | None = None,
                signed_by: str | None = None) -> str:
    sid, cid = slate["slate_id"], cand["candidate_id"]
    slate_model = cand.get("model") or "model not recorded"
    candidate_note = (f"from arc_slate candidate {cid} of slate {sid} "
                      f"(candidate drafted by an isolated Scout call, {slate_model})")
    if drafted_by:
        drafted_by = f"{_one_line(drafted_by)}, {candidate_note}"
    elif auto_sign:
        who = "orchestrating Claude session" + (f" ({session_model})" if session_model else "")
        drafted_by = f"{who}, {candidate_note}"
    else:
        drafted_by = f"claude (arc_slate candidate {cid} of slate {sid}, {slate_model})"
    lines = [f"## R{round_num} - Arc opening drafted from arc_slate {sid} {cid}", "",
             f"seed: {stub_seed(cand, fields)}", ""]
    for f in GATE_FIELD_ARGS:
        if auto_sign and not fields.get(f):
            continue   # an optional Stage 2 field left out, never a placeholder in a signed entry
        lines += [f"{f}: {fields.get(f) or PLACEHOLDER}", ""]
    for f in OPTIONAL_GATE_FIELDS:
        if fields.get(f):
            lines += [f"{f}: {_one_line(fields[f])}", ""]
    premise = fields.get("premise") or cand.get("premise")
    if premise:
        lines += [f"premise: {_one_line(premise)}", ""]
    lines += [f"drafted_by: {drafted_by}", ""]
    if auto_sign:
        lines += [f"signed_by: {_one_line(signed_by) if signed_by else AUTO_SIGNED_BY}", "",
                  f"signed: {datetime.now().strftime('%Y-%m-%d')}", ""]
    return "\n".join(lines)


def insert_gate_entry(entry: str, gate_file: Path | None = None) -> None:
    """Insert above the newest existing arc entry, or append."""
    gate_file = gate_file or TOPIC_GATE_FILE
    raw = gate_file.read_text(encoding="utf-8") if gate_file.exists() else "# Topic Gate\n\n"
    m = re.search(r"^## R\d+", raw, re.MULTILINE)
    new = (raw[:m.start()] + entry + "\n" + raw[m.start():]) if m else (raw.rstrip("\n") + "\n\n" + entry)
    gate_file.write_text(new, encoding="utf-8")


def _names_researcher(who) -> bool:
    """True when a decided_by or signed_by value names the researcher (the
    rule run_forum uses for drafted_by)."""
    return re.sub(r"\s+", " ", str(who or "")).strip().lower().startswith("researcher")


def stub(slate_id: str, candidate_id: str, round_num: int, *, auto_sign: bool = False,
         fields: dict | None = None, session_model: str | None = None,
         slates_dir: Path | None = None, gate_file: Path | None = None,
         drafted_by: str | None = None, signed_by: str | None = None) -> str:
    slates_dir = slates_dir or SLATES_DIR
    slate = load_slate(slate_id, slates_dir)
    missing = missing_decisions(slate)
    if missing:
        raise SystemExit(f"[arc_slate] taste log incomplete for slate {slate_id}: no decision for "
                         f"{', '.join(missing)}. No gate entry written.")
    dec = decisions(slate_id).get(candidate_id)
    if not dec or dec["decision"] not in ("accept", "modify"):
        raise SystemExit(f"[arc_slate] {candidate_id} was not accepted or modified. No gate entry written.")
    cand = next(c for c in slate["candidates"] if c["candidate_id"] == candidate_id)
    fields = {k: v for k, v in (fields or {}).items() if v}
    if auto_sign and _names_researcher(dec.get("decided_by")):
        # D-10: the entry would say the session signed while the taste log
        # says the researcher chose the candidate. Only the researcher signs
        # a researcher decision.
        raise SystemExit(f"[arc_slate] {candidate_id} is recorded as decided by the researcher, so --auto-sign "
                         f"would sign it in the orchestrating session's name. Write the stub without "
                         f"--auto-sign for the researcher to sign, or record the decision with the true "
                         f"decider (--by). No gate entry written.")
    for label, value in (("drafted_by", drafted_by), ("signed_by", signed_by)):
        if value and _names_researcher(value):
            raise SystemExit(f"[arc_slate] a {label} override may not name the researcher (D-10). "
                             f"No gate entry written.")
    if signed_by and not auto_sign:
        raise SystemExit("[arc_slate] --signed-by needs --auto-sign. No gate entry written.")
    if auto_sign:
        # Stage 1 prompts never show decision_rule or null_paper, so they are
        # required only while stage2.binding_checks is on (V-03).
        needed = GATE_FIELD_ARGS if _binding_checks_on() else STAGE1_GATE_FIELDS
        absent = [f for f in needed if not fields.get(f)]
        if absent:
            raise SystemExit(f"[arc_slate] --auto-sign needs every gate field. Missing {', '.join(absent)}")
    seed = stub_seed(cand, fields)
    if not seed or seed.startswith("<"):
        raise SystemExit("[arc_slate] the entry has no usable seed. No gate entry written.")
    entry = render_stub(slate, cand, round_num, fields, auto_sign, session_model, drafted_by, signed_by)
    insert_gate_entry(entry, gate_file)
    slate["stub"] = {"ts": _now(), "candidate_id": candidate_id, "round": round_num, "auto_sign": auto_sign,
                     "seed": seed}
    (slates_dir / f"{slate_id}.json").write_text(json.dumps(slate, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  [arc_slate] gate entry for R{round_num} written ({'signed under delegation' if auto_sign else 'unsigned'})")
    return entry


def slate_for_seed(seed: str, slates_dir: Path | None = None) -> dict | None:
    """The slate whose gate stub carries this seed (for the arc-opening annotator)."""
    d = slates_dir or SLATES_DIR
    norm = re.sub(r"\s+", " ", (seed or "").strip().lower())
    if not norm or not d.exists():
        return None
    for p in sorted(d.glob("*.json"), reverse=True):
        try:
            s = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        st = s.get("stub") or {}
        if st.get("seed") and re.sub(r"\s+", " ", st["seed"].lower()) == norm:
            return s
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="Arc slate (manual tool, M24)")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("propose", help="Draft up to three isolated Scout candidates")
    p.add_argument("--k", type=int, default=MAX_K)
    p.add_argument("--seed", type=int, default=DEFAULT_SEED)
    p.add_argument("--dry-run", action="store_true", help="Print the seeds and prompt, make no call")
    r = sub.add_parser("record", help="Record a decision for one candidate")
    r.add_argument("slate_id"); r.add_argument("candidate_id")
    r.add_argument("decision", choices=DECISIONS); r.add_argument("reason")
    r.add_argument("--by", default=AUTO_DECIDED_BY,
                   help="Who decided (default: the orchestrating Claude session under the standing "
                        "delegation). Pass --by researcher for a decision the researcher made")
    s = sub.add_parser("status", help="Show which candidates still need a decision")
    s.add_argument("slate_id")
    st = sub.add_parser("stub", help="Write a gate entry for an accepted or modified candidate")
    st.add_argument("slate_id"); st.add_argument("candidate_id")
    st.add_argument("--round", type=int, required=True)
    st.add_argument("--auto-sign", action="store_true",
                    help="Sign under the standing delegation (D-10). Needs identification, "
                         "exclusion_criteria, prior and falsifier, plus decision_rule and null_paper "
                         "while stage2.binding_checks is on")
    st.add_argument("--session-model", default=None, help="Model of the orchestrating session, for drafted_by")
    st.add_argument("--drafted-by", default=None,
                    help="Who drafted the gate fields, when not the orchestrating session (never the researcher)")
    st.add_argument("--signed-by", default=None,
                    help="With --auto-sign: who signed under the standing delegation (never the researcher)")
    for f in GATE_FIELD_ARGS + OPTIONAL_GATE_FIELDS + OVERRIDE_FIELDS:
        st.add_argument("--" + f.replace("_", "-"), default=None)
    args = ap.parse_args()
    if args.cmd == "propose":
        propose(args.k, args.seed, args.dry_run)
    elif args.cmd == "record":
        print(json.dumps(record(args.slate_id, args.candidate_id, args.decision, args.reason, args.by),
                         ensure_ascii=False))
    elif args.cmd == "status":
        slate = load_slate(args.slate_id)
        print(json.dumps({"missing": missing_decisions(slate), "decisions": decisions(args.slate_id)},
                         ensure_ascii=False, indent=1))
    elif args.cmd == "stub":
        fields = {f: getattr(args, f) for f in GATE_FIELD_ARGS + OPTIONAL_GATE_FIELDS + OVERRIDE_FIELDS}
        print(stub(args.slate_id, args.candidate_id, args.round, auto_sign=args.auto_sign, fields=fields,
                   session_model=args.session_model, drafted_by=args.drafted_by, signed_by=args.signed_by))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()

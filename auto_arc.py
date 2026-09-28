#!/usr/bin/env python3
"""One-command arc pipeline: pick a topic, write and sign the topic gate, run
the arc to its end, draft, gate and publish, with no human step (2026-09-26).

    python3 auto_arc.py start     # choose a topic and run a new arc to the end
    python3 auto_arc.py resume    # continue a paused or running arc or a paused selection, or retry a
                                  # push that release_check blocked
    python3 auto_arc.py status    # current step, arc, round, verdicts and any pause reason

The researcher decided on 2026-09-26 that the forum runs fully automatically.
Topic-gate entries are drafted by an automatic drafter and signed under the
researcher's standing delegation of 2026-09-25 (D-10), and the record says
exactly that. Nothing is written or signed in the researcher's name.

start, step by step (each step is a row in knowledge/auto_runs.jsonl):
   1. refuse      an open arc (use resume), an incomplete forum round, a paused
                  selection (use resume, or --fresh), or a concurrent auto_arc
   2. data        KBL_DATA must hold data files. The fingerprint is logged here,
                  and check_topic_gate pins it when the arc opens (A1).
   3. slate       arc_slate.propose(k=3): three isolated Scout candidates
   4. filter      candidates with trace violations or a topic-diversity block
                  are dropped
   5. select      SELECTION_RULE (below). Every listed candidate gets accept or
                  reject with a one-line reason through arc_slate.record,
                  decided_by the automatic selector under the delegation.
   6. gate draft  ONE claude_cli call (task gate_draft, effort high, no tools,
                  a temporary folder outside the repository, --json-schema) for
                  seed, identification, exclusion_criteria, a directional
                  falsifiable prior, a falsifier with a numeric threshold, the
                  premise, and the Stage 2 fields only while
                  stage2.binding_checks is on. Its inputs are the candidate,
                  DATA_SOURCES.md, the pitfall registry and the questions
                  already taken.
   7. premise     ONE premise_check call, although stage2.premise_check is off.
                  A failed premise, or a draft that fails validation, moves to
                  the next candidate by the same rule. When a slate runs out,
                  one more slate is proposed, once, and then the pipeline stops
                  with an alert. The call runs before any arc exists, so a
                  guard compares the repository and the watched external
                  locations before and after it, and a write outside its
                  result file stops the pipeline unsigned.
   8. gate entry  arc_slate.stub --auto-sign writes the signed entry into
                  topic_gate.md. drafted_by names the automatic gate drafter and
                  its model, signed_by the automatic selector under the
                  standing delegation.
   9. arc         run_arc.py --topic <seed> runs rounds until its stop rule,
                  drafts the arc's one paper, applies the fail-closed paper
                  gates and publishes (commit, then push only after
                  release_check passes).
  10. report      the outcome is logged, and an alert goes out at the end or on
                  any pause or stop.

SELECTION_RULE. Rank the listed candidates by their maximum cosine similarity
to prior arcs and papers (the topic-diversity guard's nearest item, lowest
first). Break ties by how often the candidate's seed opportunity pattern was
used by recent arc openers (least used first), then by candidate id.

Usage limits pause (exit 75) and alert, never wait (pause-only policy). A
pause before the arc opened resumes at the same candidate. A pause inside the
arc resumes through run_arc.py.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in [str(Path(p).resolve()) for p in sys.path if p]:
    sys.path.insert(0, str(BASE_DIR))
import arc_slate  # noqa: E402
import claude_cli  # noqa: E402
import forum_index  # noqa: E402
import run_forum  # noqa: E402

KNOWLEDGE_DIR = BASE_DIR / "knowledge"
LOGS_DIR = BASE_DIR / "logs"
AUTO_RUNS = KNOWLEDGE_DIR / "auto_runs.jsonl"
ACTIVE_ARC_FILE = KNOWLEDGE_DIR / "active_arc.json"
ARC_STATUS_FILE = KNOWLEDGE_DIR / "arc_status.json"
TOPIC_GATE_FILE = BASE_DIR / "topic_gate.md"
DATA_SOURCES_FILE = BASE_DIR / "DATA_SOURCES.md"
PITFALLS_FILE = KNOWLEDGE_DIR / "data_pitfalls.md"
RUN_ARC = BASE_DIR / "run_arc.py"

EXIT_OK, EXIT_STOP, EXIT_USAGE_LIMIT = 0, 1, claude_cli.EXIT_USAGE_LIMIT
RUN_ARC_BUSY = 4                 # run_arc.EXIT_BUSY: another run_arc holds logs/run_arc.lock
SLATE_K = 3
# Rounds run_arc may run in one invocation. A round costs four CLI calls
# (three agents and the summary), so eight rounds leave room for the paper's
# calls inside the default max_calls_per_arc of 40. An arc that has not ended
# after eight rounds pauses with an alert, and resume continues it.
DEFAULT_MAX_ROUNDS = 8
GATE_DRAFT_TIMEOUT_S = 1800
DELEGATION = f"the researcher's standing delegation of {arc_slate.DELEGATION_DATE}"
AUTO_SELECTOR = f"auto_arc.py automatic selector, under {DELEGATION}"
AUTO_SIGNER = f"auto_arc.py automatic selector, signed under {DELEGATION}"
PRE_ARC_STEPS = ("slate", "select", "gate_draft", "premise_check", "candidate")
DIRECTIONS = ("positive", "negative")

GATE_PROMPT = """\
You are the automatic gate drafter of a public research forum that studies the Korean National
Assembly with the KNA data described below. A selector chose the candidate question below from
an isolated Scout slate. Draft the topic-gate entry that opens a new arc on it. You have no tools
and no data access. Use only what is written here.

Write each field as follows.
- seed: the arc's question in one sentence, at most 300 characters, on one line. Keep the
  candidate's question, sharpened if needed. It must not restate a question already taken.
- identification: one paragraph on the empirical design (name it: descriptive comparison, DiD, RD,
  placebo, cohort), the unit, the comparison and the KNA files and fields it uses. Respect every
  pitfall in the registry below, for example seniority at an Assembly comes from term_number and
  never from the lifetime reelection field, ruling or opposition from kna_blocs.bloc(label, date),
  and merges use the member uid.
- exclusion_criteria: what the arc will not become, numbered inline as (X1) text (X2) text.
- prior: the belief the arc tests, as a directional prediction about one measurable KNA quantity
  that the data could show to be false. Give the direction in prior_direction (positive: the
  quantity is larger in the named group or rises, negative: smaller or falls).
- falsifier: the concrete test that would overturn the prior, with a numeric threshold in
  substantive units written in the sentence (for example "the year-one gap lies inside plus or
  minus 1 percentage point"). Put the number in falsifier_threshold and its unit in
  falsifier_unit.
- premise: the factual claim the prior takes for granted, stated as one quantity with its expected
  value, which one computation on the KNA data can confirm or refute before the arc opens.
{stage2}
Style for every field: plain English, no em dashes, no double hyphens as dashes, no semicolons,
no statistics in parentheses, and never "pre-registered".

Candidate (drafted by an isolated Scout call):
{candidate}

Questions already taken (do not restate any of them):
{taken}

Data pitfall registry (knowledge/data_pitfalls.md):
{pitfalls}

Data available to the forum (DATA_SOURCES.md):
{data_sources}
"""

STAGE2_PROMPT = """- decision_rule: in words, which result of which test makes the headline pass or fail.
- sesoi: the smallest effect of interest in substantive units, with one sentence on why a smaller
  effect would not matter.
- null_paper: yes or no, whether an overturned prior with an equivalence result against the sesoi
  becomes the arc's paper.
"""


# --------------------------------------------------------------------------
# Small helpers (tests replace _run_arc_process, _propose, _premise_run, _now)
# --------------------------------------------------------------------------

def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _one_line(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


def _cfg() -> dict:
    return claude_cli.load_forum_config()


def _binding_checks_on(cfg: dict) -> bool:
    return bool((cfg.get("stage2") or {}).get("binding_checks"))


def new_run_id() -> str:
    return f"auto_{datetime.now().strftime('%Y%m%dT%H%M%S')}_{os.getpid() % 100000:05d}"


def log_step(run_id: str, step: str, status: str, detail: dict | None = None, ctx: dict | None = None) -> dict:
    """Append one row to knowledge/auto_runs.jsonl. Rows are public (knowledge/
    is committed), so they carry ids, seeds and reasons, never local paths."""
    row = {"ts": _now(), "run_id": run_id, "step": step, "status": status, "detail": detail or {}}
    if ctx is not None:
        row["ctx"] = ctx
    AUTO_RUNS.parent.mkdir(parents=True, exist_ok=True)
    with open(AUTO_RUNS, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    shown = detail.get("message") if isinstance(detail, dict) and detail.get("message") else ""
    print(f"  [auto] {step}: {status}{f' ({shown})' if shown else ''}")
    return row


def load_rows(run_id: str | None = None) -> list[dict]:
    if not AUTO_RUNS.exists():
        return []
    rows = []
    for line in AUTO_RUNS.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(r, dict) and (run_id is None or r.get("run_id") == run_id):
            rows.append(r)
    return rows


def last_run_rows() -> list[dict]:
    rows = load_rows()
    return load_rows(rows[-1]["run_id"]) if rows else []


def paused_selection() -> dict | None:
    """The last row of the latest run when it paused or stopped before its arc
    opened with a resumable context, else None."""
    rows = last_run_rows()
    if not rows:
        return None
    last = rows[-1]
    if last.get("status") in ("pause", "stop") and last.get("ctx") and last["ctx"].get("resumable"):
        return last
    return None


def notify(title: str, message: str) -> None:
    claude_cli.notify(f"KNA auto_arc: {title}", message)


# --------------------------------------------------------------------------
# Lock
# --------------------------------------------------------------------------

def _lock_path() -> Path:
    return LOGS_DIR / "auto_arc.lock"


def acquire_lock() -> Path:
    """One auto_arc at a time (logs/auto_arc.lock holds the pid). A lock left
    by a process that no longer runs auto_arc is taken over."""
    path = _lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            pid = _read_json(path).get("pid")
            if pid and pid != os.getpid() and _auto_arc_alive(pid):
                raise SystemExit(f"[auto_arc] another auto_arc (pid {pid}) is running. Wait for it, or check "
                                 f"python3 auto_arc.py status.")
            path.unlink(missing_ok=True)
            continue
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps({"pid": os.getpid(), "started": _now()}))
        return path
    raise SystemExit("[auto_arc] could not take logs/auto_arc.lock")


def _auto_arc_alive(pid) -> bool:
    """True while pid is a running auto_arc process. A pid that a crashed
    auto_arc left behind may belong to an unrelated process by now, and that
    process must not hold the lock. (run_forum._pid_alive cannot be used here,
    because it answers only for run_forum processes.)"""
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        pass
    except (TypeError, ValueError, OSError):
        return False
    return _is_auto_arc(pid)


def _is_auto_arc(pid) -> bool:
    try:
        out = subprocess.run(["ps", "-o", "command=", "-p", str(int(pid))], capture_output=True, text=True,
                             timeout=10).stdout
    except (OSError, subprocess.SubprocessError, ValueError):
        return True                  # cannot tell, so the lock holds
    return "auto_arc" in out


def release_lock(path: Path) -> None:
    try:
        if _read_json(path).get("pid") == os.getpid():
            path.unlink()
    except OSError:
        pass


# --------------------------------------------------------------------------
# Selection
# --------------------------------------------------------------------------

def _max_cosine(c: dict) -> float:
    g = c.get("guard") or {}
    try:
        return float(g.get("cosine")) if g.get("cosine") is not None else 0.0
    except (TypeError, ValueError):
        return 0.0


def eligible(slate: dict) -> tuple[list[dict], list[tuple[dict, str]]]:
    """(eligible candidates, [(listed candidate, reason dropped)]). Listed
    means status candidate in the slate. A trace violation or a diversity
    block drops a listed candidate (propose normally removes both already)."""
    keep, dropped = [], []
    for c in slate.get("candidates") or []:
        if c.get("status") != "candidate":
            continue
        if c.get("trace_violations"):
            dropped.append((c, "dropped because its trace shows access to the repository or a file tool"))
        elif (c.get("guard") or {}).get("status") == "block":
            dropped.append((c, f"dropped because of a topic-diversity block against "
                               f"{(c.get('guard') or {}).get('nearest')}"))
        else:
            keep.append(c)
    return keep, dropped


def rank(cands: list[dict], opener_counts: dict | None = None) -> list[dict]:
    """SELECTION_RULE: lowest maximum cosine to prior arcs and papers, then the
    least-used seed opportunity pattern among recent openers, then id."""
    counts = opener_counts or {}
    return sorted(cands, key=lambda c: (round(_max_cosine(c), 6), int(counts.get(c.get("seed_pattern"), 0)),
                                        str(c.get("candidate_id"))))


def _why(c: dict, counts: dict) -> str:
    return (f"maximum cosine to prior arcs and papers {_max_cosine(c):.2f}, opportunity pattern "
            f"{c.get('seed_pattern')} used {int(counts.get(c.get('seed_pattern'), 0))} time(s) by recent openers")


def record_selection(slate: dict, ranked: list[dict], dropped: list[tuple[dict, str]],
                     rejected: dict, after: str | None = None) -> str | None:
    """Give every listed candidate of the slate a decision through
    arc_slate.record: accept for the first ranked candidate not yet rejected,
    reject for the others with the reason. A candidate whose latest decision
    already says the same is not recorded again. Returns the accepted
    candidate id, or None when every candidate is rejected."""
    counts = slate.get("opener_counts") or {}
    sid = slate["slate_id"]
    have = arc_slate.decisions(sid)
    remaining = [c for c in ranked if c["candidate_id"] not in rejected]
    chosen = remaining[0] if remaining else None

    def put(cid: str, decision: str, reason: str) -> None:
        cur = have.get(cid) or {}
        if cur.get("decision") == decision and (decision == "accept" or cid not in rejected
                                                or cur.get("reason") == reason):
            return
        arc_slate.record(sid, cid, decision, reason, by=AUTO_SELECTOR)

    for c, reason in dropped:
        put(c["candidate_id"], "reject", reason)
    for c in ranked:
        cid = c["candidate_id"]
        if cid in rejected:
            put(cid, "reject", rejected[cid])
        elif chosen is not None and cid == chosen["candidate_id"]:
            lead = f"selected by the auto_arc rule after {after} was rejected" if after else \
                f"selected by the auto_arc rule, first of {len(remaining)} eligible"
            put(cid, "accept", f"{lead}, with {_why(c, counts)}")
        else:
            put(cid, "reject", f"not selected by the auto_arc rule, with {_why(c, counts)}, against "
                               f"{_max_cosine(chosen):.2f} for {chosen['candidate_id']}")
    return chosen["candidate_id"] if chosen else None


# --------------------------------------------------------------------------
# Gate draft
# --------------------------------------------------------------------------

def gate_schema(stage2: bool) -> dict:
    props = {
        "seed": {"type": "string"},
        "identification": {"type": "string"},
        "exclusion_criteria": {"type": "string"},
        "prior": {"type": "string"},
        "prior_direction": {"type": "string", "enum": list(DIRECTIONS)},
        "falsifier": {"type": "string"},
        "falsifier_threshold": {"type": "number"},
        "falsifier_unit": {"type": "string"},
        "premise": {"type": "string"},
    }
    required = list(props)
    if stage2:
        props.update({"decision_rule": {"type": "string"}, "sesoi": {"type": "string"},
                      "null_paper": {"type": "string", "enum": ["yes", "no"]}})
        required += ["decision_rule", "sesoi", "null_paper"]
    return {"type": "object", "properties": props, "required": required}


def existing_seeds(gate_file: Path | None = None) -> list[str]:
    """Seeds of every signed topic_gate.md entry (the template excluded)."""
    f = gate_file or TOPIC_GATE_FILE
    if not f.exists():
        return []
    out = []
    for entry in re.split(r"\n## ", f.read_text(encoding="utf-8")):
        m = re.search(r"^seed:\s*(.+)$", entry, re.MULTILINE | re.IGNORECASE)
        if m and not m.group(1).strip().startswith("<") and "signed:" in entry.lower():
            out.append(_one_line(m.group(1)))
    return out


def questions_taken() -> str:
    """Signed gate seeds and prior paper titles. Only the title lines of the
    topic-diversity list are kept, because its header addresses Scout."""
    lines = [f"- gate seed: {s}" for s in existing_seeds()]
    try:
        import topic_diversity
        lines += [f"- paper {ln.strip()[2:]}" for ln in topic_diversity.prior_topics_for_scout().splitlines()
                  if ln.strip().startswith("- R")]
    except Exception as e:
        lines.append(f"(paper titles unavailable: {e})")
    return "\n".join(lines) or "(none)"


def pitfall_registry_text() -> str:
    try:
        text = PITFALLS_FILE.read_text(encoding="utf-8")
    except OSError:
        return "(registry unavailable)"
    m = re.search(r"```json[ \t]*\n(.*?)^```", text, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else "(registry unavailable)"


def _tidy(s: str) -> str:
    """Public prose rules on drafted text: no em dash or double hyphen as a
    dash (a spaced hyphen instead), no semicolon joining clauses (two sentences
    instead), one line."""
    s = _one_line(s).replace("—", " - ").replace("–", " - ").replace(" -- ", " - ")
    s = re.sub(r"\s*;\s*([a-z])", lambda m: ". " + m.group(1).upper(), s)
    s = re.sub(r"\s*;\s*", ". ", s)
    return re.sub(r"\s{2,}", " ", s).strip()


def validate_gate(fields: dict | None, stage2: bool, taken: list[str]) -> list[str]:
    """Problems with a drafted gate (empty when it can be signed)."""
    if not isinstance(fields, dict):
        return ["no structured output"]
    errs = []
    need = list(gate_schema(stage2)["required"])
    for k in need:
        v = fields.get(k)
        if v is None or (isinstance(v, str) and not v.strip()):
            errs.append(f"missing {k}")
    if errs:
        return errs
    seed = _one_line(fields["seed"])
    if len(seed) > 300:
        errs.append("seed longer than 300 characters")
    if seed.startswith("<"):
        errs.append("seed is a placeholder")
    ns = seed.lower()
    for s in taken:
        if s and (s.lower() in ns or ns in s.lower()):
            errs.append(f"seed restates a signed gate seed ({s[:60]})")
            break
    if fields.get("prior_direction") not in DIRECTIONS:
        errs.append("prior_direction is not positive or negative")
    if _one_line(fields["prior"]).lower() == _one_line(fields["falsifier"]).lower():
        errs.append("prior and falsifier are the same text")
    if not re.search(r"\d", str(fields["falsifier"])):
        errs.append("falsifier states no numeric threshold")
    if not isinstance(fields.get("falsifier_threshold"), (int, float)) or isinstance(fields.get("falsifier_threshold"), bool):
        errs.append("falsifier_threshold is not a number")
    if "(X1)" not in str(fields["exclusion_criteria"]):
        errs.append("exclusion_criteria are not numbered (X1) (X2)")
    if re.search(r"pre-?registered", " ".join(str(v) for v in fields.values()), re.IGNORECASE):
        errs.append("uses 'pre-registered'")
    if stage2 and fields.get("null_paper") not in ("yes", "no"):
        errs.append("null_paper is not yes or no")
    return errs


def draft_gate(cand: dict, cfg: dict) -> dict:
    """ONE claude_cli call for the gate fields. Returns {"failure", "run_id",
    "model", "fields", "errors"}."""
    stage2 = _binding_checks_on(cfg)
    candidate = {k: cand.get(k) for k in ("candidate_id", "seed_pattern", "question", "quantity", "population",
                                          "comparison", "outcome", "prediction", "premise",
                                          "closest_existing_answer", "gap")}
    data_sources = DATA_SOURCES_FILE.read_text(encoding="utf-8") if DATA_SOURCES_FILE.exists() else "(missing)"
    prompt = GATE_PROMPT.format(stage2=STAGE2_PROMPT if stage2 else "", taken=questions_taken(),
                                candidate=json.dumps(candidate, ensure_ascii=False, indent=1),
                                pitfalls=pitfall_registry_text(), data_sources=data_sources)
    workdir = Path(tempfile.mkdtemp(prefix="kna_gate_draft_"))
    try:
        res = claude_cli.run_claude("gate_draft", prompt, user_message="Draft the gate entry now.",
                                    schema=gate_schema(stage2), cwd=workdir, tools=[],
                                    timeout_s=GATE_DRAFT_TIMEOUT_S, max_continuations=0)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    fields = res.structured if isinstance(res.structured, dict) else None
    out = {"failure": res.failure, "run_id": res.run_id, "model": res.model or cfg.get("model"),
           "resume_at": res.resume_at, "fields": None, "errors": []}
    if res.failure != "ok":
        return out
    errs = validate_gate(fields, stage2, existing_seeds())
    out["errors"] = errs
    if not errs:
        clean = {k: (_tidy(v) if isinstance(v, str) else v) for k, v in fields.items()}
        out["fields"] = clean
    return out


def _premise_run(gate: dict) -> dict:
    import premise_check
    return premise_check.run(gate, force=True)


# The premise check is an Analyst-role call with Bash and Write that runs
# before any arc exists, so no staging snapshot contains it. These guards
# compare the repository's changed and untracked files and the watched
# external locations (write_guard) before and after the call. The call may
# write only its result file under knowledge/premise_checks/ (its scratch
# folder, knowledge/staging/, is ignored by git).
PREMISE_WRITES = ("knowledge/premise_checks/",)


def _sha256(path: Path) -> str | None:
    import hashlib
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _tree_state() -> dict | None:
    """{repo-relative path: sha256 or None} for every changed, deleted or
    untracked (not ignored) file, or None outside a git work tree."""
    try:
        out = subprocess.run(["git", "status", "--porcelain", "-z", "--untracked-files=all"], cwd=str(BASE_DIR),
                             capture_output=True, timeout=300)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    state, entries, i = {}, out.stdout.decode("utf-8", "replace").split("\0"), 0
    while i < len(entries):
        e = entries[i]
        i += 1
        if len(e) < 4:
            continue
        if e[0] in "RC":
            i += 1                   # a rename or copy is followed by its source path
        path = e[3:]
        state[path] = _sha256(BASE_DIR / path) if (BASE_DIR / path).is_file() else None
    return state


def premise_guard_before() -> dict:
    try:
        import write_guard
        external = write_guard.guard_before()
    except Exception as e:
        print(f"  [auto] write guard unavailable ({e})")
        external = None
    return {"tree": _tree_state(), "external": external}


def premise_guard_after(before: dict, run_id: str | None) -> list[str]:
    """Repo-relative paths (and public labels of external locations) that the
    premise check changed outside PREMISE_WRITES. Empty when clean."""
    out = []
    t0, t1 = before.get("tree"), _tree_state()
    if t0 is not None and t1 is not None:
        for p in sorted(set(t0) | set(t1)):
            if t0.get(p, "absent") != t1.get(p, "absent") and not p.startswith(PREMISE_WRITES):
                out.append(p)
    if before.get("external") is not None:
        try:
            import write_guard
            changes = write_guard.guard_after(before["external"], run_id or "premise_check")
            out += [f"{c.get('where')}: {c.get('path') or c.get('kind')}" for c in write_guard.public_changes(changes)]
        except Exception as e:
            print(f"  [auto] write guard check failed ({e})")
    return out


def _propose(k: int, seed: int) -> dict:
    return arc_slate.propose(k=k, seed=seed)


def _slate_seed() -> int:
    """The slate seed: arc_slate's default plus the number of earlier slates,
    so repeated starts draw different pattern seeds reproducibly."""
    n = len(list(arc_slate.SLATES_DIR.glob("*.json"))) if arc_slate.SLATES_DIR.exists() else 0
    return arc_slate.DEFAULT_SEED + n


# --------------------------------------------------------------------------
# The pipeline
# --------------------------------------------------------------------------

def _stop(run_id: str, step: str, message: str, code: int = EXIT_STOP, ctx: dict | None = None,
          status: str = "stop", **detail) -> int:
    log_step(run_id, step, status, {"message": message, **detail}, ctx=ctx)
    notify("paused" if code == EXIT_USAGE_LIMIT else "stopped", message)
    print(f"  [auto] {'PAUSED' if code == EXIT_USAGE_LIMIT else 'STOP'}: {message}")
    return code


def _new_slate(run_id: str, ctx: dict) -> tuple[dict | None, int | None]:
    """Propose a slate. Returns (slate, None) or (None, exit code). A slate
    cut short by a usage limit pauses and is not counted, so resume proposes
    a fresh one."""
    extra = bool(ctx["slates"])
    seed = _slate_seed()
    slate = _propose(SLATE_K, seed)
    cands = slate.get("candidates") or []
    failures = [c.get("failure") for c in cands if c.get("status") == "failed"]
    detail = {"slate_id": slate.get("slate_id"), "extra": extra, "seed": seed,
              "listed": [c["candidate_id"] for c in cands if c.get("status") == "candidate"],
              "not_listed": {c["candidate_id"]: c.get("status") for c in cands if c.get("status") != "candidate"}}
    if "usage_limit" in failures:
        return None, _stop(run_id, "slate", "usage limit while proposing the slate. Resume after the reset "
                                            "(python3 auto_arc.py resume). The partial slate is not used.",
                           EXIT_USAGE_LIMIT, ctx={**ctx, "resumable": True}, status="pause", **detail)
    if "auth_or_config" in failures:
        return None, _stop(run_id, "slate", "a slate call failed with auth_or_config. Check the CLI login and "
                                            "agents.json, then resume.", ctx={**ctx, "resumable": True}, **detail)
    ctx["slates"].append(slate["slate_id"])
    ctx["extra_used"] = len(ctx["slates"]) > 1
    ctx["slate_id"] = slate["slate_id"]
    ctx["rejected"] = {}
    log_step(run_id, "slate", "ok", detail, ctx=ctx)
    return slate, None


def select_and_open(run_id: str, ctx: dict, args) -> int:
    """Steps 3 to 9. ctx holds the slates used (at most two, the second being
    the one extra slate), the current slate and the candidates rejected in
    it, so a pause resumes at the same candidate."""
    cfg = _cfg()
    slate = arc_slate.load_slate(ctx["slate_id"]) if ctx.get("slate_id") else None
    after = ctx.pop("after", None)
    cached = ctx.pop("draft", None)
    while True:
        if slate is None:
            if len(ctx["slates"]) >= 2:
                return _stop(run_id, "select", f"no candidate passed the gate draft and premise check in "
                                               f"{len(ctx['slates'])} slates ({', '.join(ctx['slates'])}). "
                                               f"Stopped without opening an arc.", ctx={**ctx, "resumable": False})
            slate, code = _new_slate(run_id, ctx)
            if code is not None:
                return code
            after = None
        ranked_all, dropped = eligible(slate)
        ranked = rank(ranked_all, slate.get("opener_counts"))
        cid = record_selection(slate, ranked, dropped, ctx["rejected"], after=after)
        log_step(run_id, "select", "ok" if cid else "exhausted",
                 {"slate_id": slate["slate_id"], "ranking": [c["candidate_id"] for c in ranked],
                  "dropped": [c["candidate_id"] for c, _ in dropped], "chosen": cid,
                  "cosines": {c["candidate_id"]: round(_max_cosine(c), 3) for c in ranked}}, ctx=ctx)
        if cid is None:
            slate = None               # the next pass proposes the extra slate, or stops
            continue
        cand = next(c for c in ranked if c["candidate_id"] == cid)
        result = try_candidate(run_id, ctx, slate, cand, cfg, cached)
        cached = None
        if result["outcome"] == "rejected":
            ctx["rejected"][cid] = result["reason"]
            after = cid
            continue
        if result["outcome"] != "ok":
            return result["code"]
        return open_arc(run_id, ctx, slate, cand, result, args)


def try_candidate(run_id: str, ctx: dict, slate: dict, cand: dict, cfg: dict, cached: dict | None = None) -> dict:
    """Gate draft and premise check for one candidate. outcome ok (with
    fields and drafter), rejected (with reason) or pause/stop (with code).
    cached is the draft of a run that paused in its premise check, so the
    resumed run does not draft the gate a second time."""
    cid, sid = cand["candidate_id"], slate["slate_id"]
    pause_ctx = {**ctx, "resumable": True, "candidate_id": cid}
    d = cached if cached and cached.get("candidate_id") == cid else draft_gate(cand, cfg)
    base = {"slate_id": sid, "candidate_id": cid, "run": d["run_id"], "model": d["model"]}
    if d["failure"] == "usage_limit":
        return {"outcome": "pause", "code": _stop(run_id, "gate_draft", f"usage limit in the gate draft for {cid}. "
                                                  f"Resume after {d.get('resume_at') or 'the reset'}.",
                                                  EXIT_USAGE_LIMIT, ctx=pause_ctx, status="pause", **base)}
    if d["failure"] != "ok":
        return {"outcome": "stop", "code": _stop(run_id, "gate_draft", f"the gate draft call for {cid} failed "
                                                 f"({d['failure']}). Resume retries the same candidate.",
                                                 ctx=pause_ctx, **base)}
    if d["errors"]:
        reason = f"gate draft failed validation ({', '.join(d['errors'][:4])})".replace(";", ",")
        log_step(run_id, "gate_draft", "rejected", {**base, "errors": d["errors"]}, ctx=ctx)
        return {"outcome": "rejected", "reason": reason}
    fields = d["fields"]
    drafter = f"automatic gate drafter (auto_arc.py gate_draft call, {d['model']}, run {d['run_id']})"
    log_step(run_id, "gate_draft", "ok", {**base, "seed": _one_line(fields["seed"]),
                                          "prior_direction": fields.get("prior_direction"),
                                          "falsifier_threshold": fields.get("falsifier_threshold"),
                                          "falsifier_unit": fields.get("falsifier_unit")}, ctx=ctx)
    gate = {"seed": _one_line(fields["seed"]), "premise": fields["premise"],
            "identification": fields["identification"], "drafted_by": drafter,
            "signed_by": "not signed yet (checked before signing)"}
    draft_ctx = {**pause_ctx, "draft": {"candidate_id": cid, "failure": "ok", "run_id": d["run_id"],
                                        "model": d["model"], "fields": fields, "errors": []}}
    guard = premise_guard_before()
    try:
        rec = _premise_run(gate)
    except ValueError as e:
        log_step(run_id, "premise_check", "rejected", {**base, "error": str(e)}, ctx=ctx)
        return {"outcome": "rejected", "reason": f"premise check could not run ({e})".replace(";", ",")}
    pbase = {"slate_id": sid, "candidate_id": cid, "run": rec.get("run_id"), "passes": rec.get("passes"),
             "value": rec.get("value"), "n": rec.get("n")}
    stray = premise_guard_after(guard, rec.get("run_id"))
    if stray:
        # A write outside the result file is an incident, not a failed
        # premise. Nothing is signed, and a person checks the files first.
        shown = ", ".join(stray[:10]) + (f" and {len(stray) - 10} more" if len(stray) > 10 else "")
        return {"outcome": "stop", "code": _stop(run_id, "premise_check", f"the premise check for {cid} changed "
                                                 f"files outside its result file ({shown}). No gate entry was "
                                                 f"written. Check the changes, then run python3 auto_arc.py "
                                                 f"start --fresh.", ctx={**ctx, "resumable": False},
                                                 changed=stray[:50], **pbase)}
    if rec.get("failure") == "usage_limit":
        return {"outcome": "pause", "code": _stop(run_id, "premise_check", f"usage limit in the premise check "
                                                  f"for {cid}. Resume after the reset.", EXIT_USAGE_LIMIT,
                                                  ctx=draft_ctx, status="pause", **pbase)}
    if rec.get("source") == "computed" and not rec.get("call_ok") and rec.get("failure") not in (None, "ok"):
        return {"outcome": "stop", "code": _stop(run_id, "premise_check", f"the premise check call for {cid} "
                                                 f"failed ({rec.get('failure')}). Resume retries the premise "
                                                 f"check of the same candidate.", ctx=draft_ctx, **pbase)}
    if rec.get("passes") is not True:
        why = ("the premise does not hold in the data" if rec.get("passes") is False
               else f"the premise check gave no usable result ({', '.join(rec.get('errors') or ['no result'])})")
        log_step(run_id, "premise_check", "rejected", {**pbase, "message": why}, ctx=ctx)
        value = f", computed value {rec.get('value')} with N {rec.get('n')}" if rec.get("value") is not None else ""
        return {"outcome": "rejected", "reason": f"premise check failed, {why}{value}".replace(";", ",")}
    log_step(run_id, "premise_check", "ok", pbase, ctx=ctx)
    return {"outcome": "ok", "fields": fields, "drafter": drafter, "premise": rec}


def open_arc(run_id: str, ctx: dict, slate: dict, cand: dict, result: dict, args) -> int:
    """Step 8 (signed gate entry) and step 9 (run_arc to the end)."""
    rnd, roles = forum_index.next_round_plan()
    if list(roles) != list(forum_index.ROLE_ORDER):
        return _stop(run_id, "gate_entry", f"R{rnd} is incomplete (missing {', '.join(roles)}). Finish it before "
                                           f"an arc opens.", ctx={**ctx, "resumable": True})
    fields = {k: v for k, v in result["fields"].items()
              if k in arc_slate.GATE_FIELD_ARGS + arc_slate.OPTIONAL_GATE_FIELDS + arc_slate.OVERRIDE_FIELDS}
    try:
        entry = arc_slate.stub(slate["slate_id"], cand["candidate_id"], rnd, auto_sign=True, fields=fields,
                               drafted_by=result["drafter"], signed_by=AUTO_SIGNER)
    except SystemExit as e:
        return _stop(run_id, "gate_entry", f"the gate entry was not written ({e})", ctx={**ctx, "resumable": True})
    seed = arc_slate.stub_seed(cand, fields)
    log_step(run_id, "gate_entry", "ok", {"slate_id": slate["slate_id"], "candidate_id": cand["candidate_id"],
                                          "round": rnd, "seed": seed, "drafted_by": result["drafter"],
                                          "signed_by": AUTO_SIGNER, "lines": entry.count("\n")})
    return run_arc(run_id, ["--topic", seed], args, opened=True)


def _run_arc_process(cmd: list[str]) -> int:
    """run_arc.py as a child process with its output on this terminal."""
    return subprocess.run(cmd, cwd=str(BASE_DIR)).returncode


def run_arc(run_id: str, extra: list[str], args, opened: bool = False) -> int:
    cmd = [sys.executable, "-u", str(RUN_ARC), *extra, "--max-rounds", str(args.max_rounds)]
    if args.no_push:
        cmd.append("--no-push")
    if getattr(args, "allow_data_change", False):
        cmd.append("--allow-data-change")
    cmd += list(getattr(args, "run_arc_args", None) or [])
    shown = [Path(c).name if c == str(RUN_ARC) else c for c in cmd[2:]]
    log_step(run_id, "run_arc", "started", {"args": shown, "opened_arc": opened})
    rc = _run_arc_process(cmd)
    return report(run_id, rc, no_push=args.no_push)


def outcome_of(rc: int, status: dict, arc: dict, no_push: bool = False) -> tuple[str, str, str]:
    """(outcome, alert title, message) from run_arc's exit code and arc_status."""
    state, reason = status.get("state"), status.get("reason") or ""
    push = status.get("push_blocked")
    arc_txt = f"Arc {arc.get('arc_id', '?')}"
    if rc == RUN_ARC_BUSY:
        return "busy", "busy", (f"another run_arc is running, so {arc_txt} was not continued by this run. "
                                f"Run python3 auto_arc.py resume after it finishes.")
    if rc == EXIT_USAGE_LIMIT or state == "paused_usage_limit":
        return "paused_usage_limit", "paused", (f"{arc_txt} paused at a usage limit "
                                               f"(resume after {status.get('resume_after') or 'the reset'}). "
                                               f"Run python3 auto_arc.py resume.")
    if status.get("article") and state == "stopped" and rc == 0:
        where = ("committed locally, push blocked by release_check (fix the problems, then python3 "
                 "auto_arc.py resume retries the push)") if push else \
            ("committed locally (--no-push)" if no_push else "published")
        return ("published_push_blocked" if push else "published"), "paper published" if not push else \
            "push blocked", f"{arc_txt} ended with a paper, {status['article']}, {where}. {reason}"
    if state == "draft_blocked":
        return "draft_blocked", "draft blocked", (f"{arc_txt} ended with a draft that failed its paper gates and "
                                                  f"was quarantined. {reason}")
    if state in ("external_write", "researcher_file_changed"):
        return state, "held", f"{arc_txt} is held ({state}). {reason}"
    if state == "running" and rc == 0:
        return "max_rounds", "paused", (f"{arc_txt} is still running after this invocation's rounds. "
                                        f"Run python3 auto_arc.py resume. {reason}")
    if state in ("stopped", "closed_no_paper") and rc == 0:
        return "closed", "arc closed", f"{arc_txt} closed without a paper. {reason}"
    return "stopped", "stopped", f"{arc_txt} stopped (run_arc exit {rc}). {reason}"


def report(run_id: str, rc: int, no_push: bool = False) -> int:
    status, arc = _read_json(ARC_STATUS_FILE), _read_json(ACTIVE_ARC_FILE)
    outcome, title, message = outcome_of(rc, status, arc, no_push)
    detail = {"message": message, "run_arc_exit": rc, "arc": arc.get("arc_id"), "state": status.get("state"),
              "last_round": status.get("last_round"), "verdict": status.get("verdict"),
              "article": status.get("article"), "push_blocked": bool(status.get("push_blocked")),
              "data_fingerprint": (status.get("data_fingerprint") or {}).get("id")}
    log_step(run_id, "outcome", outcome, detail)
    notify(title, message)
    return rc


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

def cmd_start(args) -> int:
    if run_forum._arc_is_open():
        st = _read_json(ARC_STATUS_FILE)
        print(f"  [auto] REFUSED: an arc is open (arc {_read_json(ACTIVE_ARC_FILE).get('arc_id', '?')}, state "
              f"{st.get('state')}). Continue it with python3 auto_arc.py resume.")
        return EXIT_STOP
    paused = paused_selection()
    if paused and not args.fresh:
        print(f"  [auto] REFUSED: the last auto run ({paused['run_id']}) paused before its arc opened, at "
              f"{paused['step']}. Continue it with python3 auto_arc.py resume, or start over with --fresh.")
        return EXIT_STOP
    rnd, roles = forum_index.next_round_plan()
    if list(roles) != list(forum_index.ROLE_ORDER):
        print(f"  [auto] REFUSED: R{rnd} is incomplete (missing {', '.join(roles)}). Finish it with "
              f"python3 run_forum.py --resume before a new arc opens.")
        return EXIT_STOP
    run_id = new_run_id()
    log_step(run_id, "start", "ok", {"round": rnd, "max_rounds": args.max_rounds, "no_push": args.no_push,
                                     "fresh": bool(args.fresh), "model": _cfg().get("model")})
    fp = run_forum.data_fingerprint()
    if not fp or not fp.get("n_files"):
        return _stop(run_id, "data", "KBL_DATA is not set or holds no .parquet or .csv file. Point it at the KNA "
                                     "processed-data directory.")
    prev = (_read_json(ACTIVE_ARC_FILE).get("data_fingerprint") or {}).get("id")
    log_step(run_id, "data", "ok", {"fingerprint": fp["id"], "n_files": fp["n_files"],
                                    "kna_git_commit": fp.get("kna_git_commit"), "kna_version": fp.get("kna_version"),
                                    "changed_since_last_arc": bool(prev and prev != fp["id"])})
    ctx = {"slates": [], "extra_used": False, "slate_id": None, "rejected": {}}
    return select_and_open(run_id, ctx, args)


def cmd_resume(args) -> int:
    arc = _read_json(ACTIVE_ARC_FILE)
    if arc.get("start_round") and run_forum._arc_is_open():
        rows = last_run_rows()
        run_id = rows[-1]["run_id"] if rows and rows[-1].get("step") in ("run_arc", "outcome", "resume") \
            else new_run_id()
        log_step(run_id, "resume", "ok", {"arc": arc.get("arc_id"), "state": _read_json(ARC_STATUS_FILE).get("state")})
        return run_arc(run_id, [], args)
    paused = paused_selection()
    if paused:
        ctx = dict(paused["ctx"])
        ctx.pop("resumable", None)
        cid = ctx.pop("candidate_id", None)
        log_step(paused["run_id"], "resume", "ok", {"step": paused["step"], "candidate_id": cid,
                                                    "slate_id": ctx.get("slate_id")}, ctx=ctx)
        return select_and_open(paused["run_id"], ctx, args)
    if _read_json(ARC_STATUS_FILE).get("push_blocked") and not args.no_push:
        return retry_push(new_run_id())
    print("  [auto] nothing to resume: no open arc, no paused selection and no blocked push. Start one with "
          "python3 auto_arc.py start.")
    return EXIT_STOP


def retry_push(run_id: str) -> int:
    """resume after a push that release_check blocked, once the arc has
    closed: run release_check again and push the local commits only if it
    passes (run_arc.push_checked, under the run_arc lock)."""
    import run_arc
    blocked = _read_json(ARC_STATUS_FILE).get("push_blocked") or {}
    label = blocked.get("commit") or "the local commits"
    log_step(run_id, "push", "started", {"commit": label, "blocked_at": blocked.get("at")})
    lock = run_arc.acquire_run_lock()
    if lock is None:
        return _stop(run_id, "push", "another run_arc is running. Retry with python3 auto_arc.py resume after it "
                                     "finishes.")
    try:
        pushed = run_arc.push_checked(label)
    finally:
        run_arc.release_run_lock(lock)
    if pushed:
        log_step(run_id, "push", "ok", {"commit": label, "message": "release_check passed and the commits were pushed"})
        notify("pushed", f"release_check passed and {label} was pushed.")
        return EXIT_OK
    reasons = (_read_json(ARC_STATUS_FILE).get("push_blocked") or {}).get("reasons") or []
    log_step(run_id, "push", "blocked", {"commit": label, "reasons": reasons[:20],
                                         "message": f"push still blocked ({len(reasons)} problem(s))"})
    return EXIT_STOP


def status_report() -> dict:
    arc, st = _read_json(ACTIVE_ARC_FILE), _read_json(ARC_STATUS_FILE)
    rows = last_run_rows()
    start = arc.get("start_round")
    verdicts = []
    try:
        import verdict
        for r in verdict.load_rows():
            if start and isinstance(r.get("round"), int) and r["round"] >= int(start):
                verdicts.append({"round": r["round"], "verdict": r.get("verdict"),
                                 "falsifier_tested": r.get("falsifier_tested")})
    except Exception:
        pass
    last = rows[-1] if rows else {}
    pause = None
    if st.get("state") in ("paused_usage_limit", "paused", "external_write", "researcher_file_changed",
                           "stopped", "draft_blocked") and run_forum._arc_is_open():
        pause = {"state": st.get("state"), "reason": st.get("reason"), "resume_after": st.get("resume_after")}
    elif last.get("status") in ("pause", "stop"):
        pause = {"state": f"auto_arc {last.get('status')} at {last.get('step')}",
                 "reason": (last.get("detail") or {}).get("message")}
    return {
        "auto_run": last.get("run_id"), "step": last.get("step"), "step_status": last.get("status"),
        "step_ts": last.get("ts"),
        "arc": {"arc_id": arc.get("arc_id"), "seed": arc.get("seed"), "start_round": start,
                "drafted_by": arc.get("drafted_by"), "signed_by": arc.get("signed_by"),
                "open": run_forum._arc_is_open()} if arc else None,
        "round": {"forum": forum_index.current_round(), "last_decided": st.get("last_round"),
                  "arc_depth": st.get("arc_depth"), "action": st.get("action")},
        "verdicts": verdicts, "state": st.get("state"), "reason": st.get("reason"),
        "article": st.get("article"), "pause": pause, "push_blocked": st.get("push_blocked"),
        "data_fingerprint": (st.get("data_fingerprint") or arc.get("data_fingerprint") or {}).get("id"),
    }


def cmd_status(args) -> int:
    s = status_report()
    if args.json:
        print(json.dumps(s, ensure_ascii=False, indent=1))
        return EXIT_OK
    print("auto_arc status")
    print(f"  step:     {s['step'] or 'none'} ({s['step_status'] or '-'}, {s['step_ts'] or '-'}) in "
          f"{s['auto_run'] or 'no auto run yet'}")
    a = s["arc"]
    if a:
        print(f"  arc:      {a['arc_id']} from R{a['start_round']} ({'open' if a['open'] else 'closed'}): {a['seed']}")
        print(f"            drafted by {a['drafted_by']}. Signed by {a['signed_by']}.")
    r = s["round"]
    print(f"  round:    forum at R{r['forum']}, last decided R{r['last_decided']}, depth {r['arc_depth']}, "
          f"action {r['action']}")
    v = ", ".join(f"R{x['round']} {x['verdict']} (falsifier {x['falsifier_tested']})" for x in s["verdicts"])
    print(f"  verdicts: {v or 'none in this arc'}")
    print(f"  state:    {s['state']}: {s['reason']}")
    if s["article"]:
        print(f"  paper:    {s['article']}")
    print(f"  data:     {s['data_fingerprint'] or 'not pinned'}")
    if s["pause"]:
        p = s["pause"]
        print(f"  pause:    {p['state']}: {p.get('reason')}"
              + (f" (resume after {p['resume_after']})" if p.get("resume_after") else ""))
    else:
        print("  pause:    none")
    if s["push_blocked"]:
        print(f"  push:     BLOCKED ({', '.join(s['push_blocked'].get('reasons') or [])[:300]}). Fix the "
              f"problems, then python3 auto_arc.py resume retries the push.")
    return EXIT_OK


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="One-command arc pipeline (start, resume, status)")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("start", "resume"):
        p = sub.add_parser(name)
        p.add_argument("--max-rounds", type=int, default=DEFAULT_MAX_ROUNDS,
                       help=f"rounds run_arc may run in this invocation (default {DEFAULT_MAX_ROUNDS})")
        p.add_argument("--no-push", action="store_true", help="commit locally, never push")
        p.add_argument("--allow-data-change", action="store_true",
                       help="pass --allow-data-change to run_arc (recorded)")
        if name == "start":
            p.add_argument("--fresh", action="store_true", help="start over although a selection is paused")
        else:
            p.add_argument("run_arc_args", nargs=argparse.REMAINDER,
                           help="after --, arguments for run_arc.py (for example -- --ack-stop)")
    s = sub.add_parser("status")
    s.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.cmd == "status":
        return cmd_status(args)
    if args.cmd not in ("start", "resume"):
        ap.print_help()
        return EXIT_STOP
    if getattr(args, "run_arc_args", None) and args.run_arc_args[:1] == ["--"]:
        args.run_arc_args = args.run_arc_args[1:]
    lock = acquire_lock()
    try:
        return cmd_start(args) if args.cmd == "start" else cmd_resume(args)
    finally:
        release_lock(lock)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Season 2 arc runner: one instruction, one arc, supervised to completion.

Runs forum rounds back to back and stops on the arc's own rules, so one
signed topic_gate entry (its drafted_by and signed_by lines record who drafted
and who signed it) opens an arc, one launch runs it, and the result is read.

v2.1 (2026-09-25). The verdict is the Critic's verdict of record from
verdict.py (knowledge/verdicts.jsonl, taken from the run's structured output),
not the first regex hit in the post. Round identity comes from the posts'
frontmatter through forum_index, so a resumed round is never counted twice.
Run failures are classified by claude_cli and read back from the run sidecars.

Stop rules (checked after every complete round, on the verdict of record):
  archive                                   -> arc closed. STOP.
  pursue + falsifier_tested yes + depth ok  -> draft the arc's one paper, STOP.
  pursue + falsifier_tested no              -> continue (the next round tests it).
  revise / no verdict                       -> continue.
  --max-rounds reached after a continue     -> the step ends with the arc still
                                               running (cron runs --max-rounds 1
                                               and the next step goes on).
A closed arc (archive stop, a drafted or blocked paper, closed_no_paper) runs
no further rounds, by the same rule run_forum applies (one arc, one paper).
A new arc needs --topic.
Depth is min_arc_rounds_before_draft rounds (default 3) until the researcher
decides D-11. With stage2.binding_checks on, the scripted kill-test depth is
reported next to it, and falsifier_tested comes from the scripted checks.
Switches that stay off until D-11 (forum_config keys):
  min_tests_before_draft  depth counts arc rounds with a new kill test instead
  null_paper_path         an overturned prior with a passed equivalence test
                          against the gate's sesoi drafts when null_paper is yes
  closed_no_paper         an arc that reaches max_arc_rounds (default 5)
                          without a draft closes as closed_no_paper

Failures (forum_config.failure_policy):
  usage limit (exit 75)            -> pause as paused_usage_limit with
                                      resume_after (default). With usage_limit
                                      "sleep_and_resume", a session limit that
                                      resets within usage_limit_max_wait_s is
                                      waited out and the round resumed.
  auth_or_config, max_calls_per_arc -> STOP at once.
  other classified run failures    -> resume the round, STOP once
                                      max_failed_runs_per_invocation is reached.
  exit without a recorded failure  -> STOP.
  external write, or a changed researcher-owned file (run_forum or a draft's
  figure script)                   -> STOP as external_write or
                                      researcher_file_changed, which holds
                                      until --ack-stop. A researcher_file_changed
                                      stop also needs --researcher-files keep
                                      or restore (restore puts back the
                                      start-of-run versions staging saved).
The findings ledger is checked first (ledger_audit), and a ledger with
duplicate keys refuses the run. Every stop and pause writes
knowledge/arc_status.json and sends an alert (claude_cli.notify). A complete
round that an earlier invocation never decided on is decided before any
launch, after its missing post-round steps (run_forum --rounds 0) have run.
A draft that did not run to a result (usage limit, error, --no-draft) is
kept as pending_draft and run first by the next invocation. A draft never
starts without its round summary, which draft_article's hand-coding check
reads.

Publishing (D-09, fully automatic). After every complete round the site is
rebuilt and the round is committed and pushed (disable with --no-push). A
draft that passes the paper gates (draft_article exit 0) is committed with
articles/ and docs/ and pushed. A draft that fails them (exit 2) stays in
workspace/failed_drafts/, and only forum/, summaries/ and knowledge/ are
committed, locally, with nothing pushed.
Release check (A3, 2026-09-26). Every push first runs release_check.py (the
full test suite, the tracked-file leak lint, the paper gates on every paper
changed against origin/main, a site build into a temporary directory, and
the docs/articles PDF check). If it fails, the commit stays local,
arc_status records push_blocked with the reasons, and an alert goes out. A
failing tree is never pushed. The next push runs the check again.
Data pin (A1). run_forum refuses a round whose KNA data differ from the
arc's pinned fingerprint. run_arc then stops with the changed files named,
and --allow-data-change passes the override to run_forum, which records it.
One run_arc at a time (logs/run_arc.lock). A second invocation while one
runs, for example a cron step during an auto_arc arc, exits 4 (EXIT_BUSY)
and changes nothing.

Usage:
    python3 run_arc.py --topic "<signed seed>"        # open a new arc and run it
    python3 run_arc.py                                # continue the active arc
    python3 run_arc.py --max-rounds 1 --no-draft      # single supervised step (cron)
    python3 run_arc.py --ack-stop                     # continue after checking an external write
    python3 run_arc.py --ack-stop --researcher-files restore   # undo a run's researcher-file changes
    python3 run_arc.py --allow-data-change            # continue on changed KNA data (recorded)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).parent
if str(BASE_DIR.resolve()) not in [str(Path(p).resolve()) for p in sys.path if p]:
    sys.path.insert(0, str(BASE_DIR.resolve()))
import claude_cli  # noqa: E402
import forum_index  # noqa: E402
import ledger_audit  # noqa: E402
import run_forum  # noqa: E402  (arc identity and the closed-arc rule, shared with the forum)
import staging  # noqa: E402  (the researcher-owned file list)
import verdict  # noqa: E402

FORUM_DIR = BASE_DIR / "forum"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
LOGS_DIR = BASE_DIR / "logs"
ARTICLES_DIR = BASE_DIR / "articles"
FAILED_DRAFTS_DIR = BASE_DIR / "workspace" / "failed_drafts"
ACTIVE_ARC_FILE = KNOWLEDGE_DIR / "active_arc.json"
ARC_STATUS_FILE = KNOWLEDGE_DIR / "arc_status.json"
FINDINGS_FILE = KNOWLEDGE_DIR / "findings.jsonl"
RUN_FORUM = BASE_DIR / "run_forum.py"
DRAFT_ARTICLE = BASE_DIR / "draft_article.py"
BUILD_SITE = BASE_DIR / "build_site.py"
RELEASE_CHECK = BASE_DIR / "release_check.py"
RELEASE_CHECK_TIMEOUT_S = 3600
# Exit status when another run_arc holds logs/run_arc.lock (0, 1, 2, 3 and 75
# are taken by the arc outcomes).
EXIT_BUSY = 4

# Season 2 opened with Arc 4 at R25 (the verdict distribution's season span).
SEASON2_FIRST_ROUND = forum_index.LEGACY_ARCS[4][0]
# draft_article runs up to 2 body calls (3600 s each), 2 gate-driven fix
# passes (1800 s each) and the figure calls.
DRAFT_TIMEOUT_S = 4 * 3600
USAGE_LIMIT_MARGIN_S = 120
DEFAULT_USAGE_LIMIT_MAX_WAIT_S = 6 * 3600
D11_DEFAULTS = {"min_tests_before_draft": None, "null_paper_path": False,
                "closed_no_paper": False, "max_arc_rounds": 5}

# What each kind of commit may carry. articles/ only with a paper that passed
# the gates. A blocked draft commits the forum state locally and never pushes.
ROUND_PATHS = ["forum/", "summaries/", "knowledge/", "docs/", "topic_gate.md"]
PAPER_PATHS = ROUND_PATHS + ["articles/"]
LOCAL_PATHS = ["forum/", "summaries/", "knowledge/"]

# Kept across status writes within one arc. disclosure.py reads the human
# action keys, and M11 records every wait. run_forum writes the external-write
# list, the last run failure and the CLI version log.
PERSISTENT_KEYS = ("override_gates", "force", "bypass_topic_gate", "allow_model_change",
                   "manual_rerun", "human_actions", "waits", "external_writes", "last_failure",
                   "cli_version_changes", "researcher_owned_changes", "stops_acknowledged",
                   "data_fingerprint", "allow_data_change", "push_blocked")
# Keys run_forum writes on its way to a failure exit. They are carried into
# the status run_arc writes for that exit.
FORUM_KEYS = ("external_writes", "last_failure", "paused_round", "paused_role",
              "researcher_owned_changes", "data_pin_refused")
# The last push attempt of this process (commit_round), read by finish().
LAST_PUSH: dict = {}
# Stops that hold until someone acknowledges them with --ack-stop. A run
# changed a watched repository or data directory, or a researcher-owned file.
ACK_STATES = ("external_write", "researcher_file_changed")
# Per-round fields carried into a resumed draft's status.
ROUND_FIELDS = ("last_round", "verdict", "verdict_critic", "falsifier_tested", "diversity",
                "arc_depth", "min_arc_rounds_before_draft", "kill_depth", "kill_depth_note",
                "depth_rule", "action", "one_line", "overrides", "verdict_distribution")


# --------------------------------------------------------------------------
# Small helpers (tests monkeypatch _now, _sleep, _git, _build_site, _run_logged)
# --------------------------------------------------------------------------

def _now() -> datetime:
    """Current time, timezone-aware."""
    return datetime.now(timezone.utc).astimezone()


def _iso(dt: datetime | None = None) -> str:
    return (dt or _now()).isoformat(timespec="seconds")


def _parse_iso(s) -> datetime | None:
    try:
        dt = datetime.fromisoformat(str(s))
    except (TypeError, ValueError):
        return None
    return dt if dt.tzinfo else dt.astimezone()


def _sleep(seconds: float) -> None:
    """Failure-policy wait. Skipped with KNA_NO_SLEEP=1."""
    if os.environ.get("KNA_NO_SLEEP") == "1":
        return
    time.sleep(seconds)


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


# --------------------------------------------------------------------------
# One run_arc at a time
# --------------------------------------------------------------------------

def _run_lock_path() -> Path:
    return LOGS_DIR / "run_arc.lock"


def _run_arc_alive(pid) -> bool:
    """True while pid is a running run_arc process. A pid left by a crashed
    run may belong to an unrelated process by now, which must not hold the
    lock."""
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        pass
    except (TypeError, ValueError, OSError):
        return False
    try:
        out = subprocess.run(["ps", "-o", "command=", "-p", str(int(pid))], capture_output=True, text=True,
                             timeout=10)
    except (OSError, subprocess.SubprocessError):
        return True                  # cannot tell, so the lock holds
    return "run_arc" in out.stdout if out.stdout.strip() else out.returncode == 0


def acquire_run_lock() -> Path | None:
    """logs/run_arc.lock with this pid, or None while another run_arc runs.
    Without it a cron step (auto_run.sh) could launch a round in the middle
    of an arc that auto_arc or a person is running, and its refusal by the
    run_forum lock would be written into that arc's status as a stop. A lock
    of a process that no longer runs run_arc is taken over."""
    path = _run_lock_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        try:
            fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            pid = _read_json(path).get("pid")
            if pid == os.getpid():
                return path
            if pid and _run_arc_alive(pid):
                return None
            path.unlink(missing_ok=True)
            continue
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps({"pid": os.getpid(), "started": _iso()}))
        return path
    return None


def release_run_lock(path: Path | None) -> None:
    try:
        if path is not None and _read_json(path).get("pid") == os.getpid():
            path.unlink()
    except OSError:
        pass


def _config() -> dict:
    """forum_config plus the season, through claude_cli's reader."""
    return claude_cli.load_forum_config()


def _policy(cfg: dict) -> dict:
    return {**claude_cli.DEFAULT_FAILURE_POLICY, **(cfg.get("failure_policy") or {})}


def _stage2(cfg: dict, flag: str) -> bool:
    return bool((cfg.get("stage2") or {}).get(flag, False))


def _yes(value) -> bool:
    return value is True or str(value or "").strip().lower().startswith("yes")


def d11_switches(cfg: dict) -> dict:
    """The D-11 switches from forum_config, off unless set."""
    sw = dict(D11_DEFAULTS)
    sw.update({k: cfg[k] for k in D11_DEFAULTS if cfg.get(k) is not None})
    return sw


def switch_errors(cfg: dict) -> list[str]:
    """The kill-test depth rule and the null-paper path read committed cards
    and results, so they refuse to run without the Stage 2 flags behind them."""
    sw = d11_switches(cfg)
    needs = [k for k in ("min_tests_before_draft", "null_paper_path") if sw[k]]
    if needs and not (_stage2(cfg, "prediction_cards") and _stage2(cfg, "binding_checks")):
        return [f"{' and '.join(needs)} need forum_config.stage2.prediction_cards and "
                f"stage2.binding_checks switched on"]
    return []


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(BASE_DIR), capture_output=True, text=True)


def _build_site() -> None:
    subprocess.run([sys.executable, str(BUILD_SITE)], capture_output=True, cwd=str(BASE_DIR))


def _run_logged(cmd: list[str], log_path: Path, timeout: int | None = None,
                label: str = "run") -> int | None:
    """Run a child script with its output appended to the arc log. Returns the
    exit code, or None when the timeout expired."""
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n===== run_arc {label} {datetime.now().isoformat(timespec='seconds')} =====\n")
        log.flush()
        try:
            proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=str(BASE_DIR),
                                  timeout=timeout)
        except subprocess.TimeoutExpired:
            log.write(f"\n===== run_arc {label} timed out after {timeout} s =====\n")
            return None
    return proc.returncode


# --------------------------------------------------------------------------
# Arc identity and state
# --------------------------------------------------------------------------

def active_arc() -> dict:
    return _read_json(ACTIVE_ARC_FILE)


def arc_start() -> int:
    try:
        return int(active_arc().get("start_round") or 1)
    except (TypeError, ValueError):
        return 1


def current_arc_id() -> str | None:
    """The arc id string the forum passes to claude_cli (str of forum_index's
    arc for the active arc's posts, else the active arc's arc_id key)."""
    start = arc_start()
    metas = [m for m in forum_index.index(forum_dir=FORUM_DIR) if (m["round"] or 0) >= start]
    if metas and metas[-1]["arc"] is not None:
        return str(metas[-1]["arc"])
    arc = active_arc()
    parsed = forum_index._parse_arc(arc.get("arc_id", arc.get("arc")))
    return str(parsed) if parsed is not None else None


def unevaluated_round(last_round) -> int | None:
    """The latest round of the active arc when it is complete but run_arc never
    decided on it. That happens when an invocation ended between the Critic
    post and the decision, for example on a usage limit in the round summary."""
    try:
        done = int(last_round) if last_round is not None else None
    except (TypeError, ValueError):
        done = None
    cur = forum_index.current_round(forum_dir=FORUM_DIR)
    if cur < arc_start() or (done is not None and cur <= done):
        return None
    return None if forum_index.missing_roles(cur, forum_dir=FORUM_DIR) else cur


def critic_state(round_num: int, cfg: dict | None = None) -> dict:
    """Verdict of record for the round, with the Critic post that carries it.

    The verdict is verdict.verdict_of_record's, which is already effective. A
    structured versus YAML verdict mismatch, or a Stage 2 override, has made it
    revise. round is the Critic post's frontmatter round (forum_index), which
    labels the commit. With stage2.binding_checks on, falsifier_tested and
    kill_depth come from the scripted checks on committed cards and results,
    never from the Critic."""
    cfg = cfg if cfg is not None else _config()
    out = {"source": None, "post": None, "round": round_num, "verdict": None,
           "verdict_critic": None, "falsifier_tested": None, "prior_status": None,
           "one_line": None, "overrides": [], "mismatch": [], "headline_claim_id": None,
           "verdict_source": None, "kill_depth": None, "binding": None}
    metas = [m for m in forum_index.index(forum_dir=FORUM_DIR)
             if m["round"] == round_num and m["role"] == "critic"]
    if not metas:
        return out
    meta = metas[-1]
    out.update(source=meta["path"].name, post=meta["path"], round=meta["round"])
    row = verdict.verdict_of_record(round_num) or {}
    ft = row.get("falsifier_tested")
    if isinstance(ft, bool):
        ft = "yes" if ft else "no"
    out.update(
        verdict=row.get("verdict") if row.get("verdict") in verdict.VERDICTS else None,
        verdict_critic=row.get("verdict_critic"),
        falsifier_tested=str(ft).strip().lower() if ft not in (None, "") else None,
        prior_status=row.get("prior_status"), one_line=row.get("one_line"),
        overrides=list(row.get("overrides") or []), mismatch=list(row.get("mismatch") or []),
        headline_claim_id=row.get("headline_claim_id"), verdict_source=row.get("source"))
    if not _stage2(cfg, "binding_checks"):
        return out
    bc = row.get("binding")
    if not bc:
        # A row recorded before the flag was on. Run the checks here, and a
        # pursue they do not support is not binding (M10b).
        try:
            full = verdict.binding_checks(round_num, current_arc_id(), critic=row)
            bc = full
            if out["verdict"] == "pursue" and full.get("overrides"):
                out["verdict"] = "revise"
                out["overrides"] += list(full["overrides"])
        except Exception as e:
            bc = None
            if out["verdict"] == "pursue":
                out["verdict"] = "revise"
                out["overrides"].append(f"binding checks failed to run: {e}")
    if bc:
        out["binding"] = {k: bc.get(k) for k in ("headline_claim_id", "falsifier_tested", "kill_depth",
                                                 "kill_rounds", "new_test_this_round", "null_ok")}
        out["kill_depth"] = bc.get("kill_depth")
        out["falsifier_tested"] = "yes" if bc.get("falsifier_tested") else "no"
        out["headline_claim_id"] = bc.get("headline_claim_id") or out["headline_claim_id"]
    return out


def diversity_state(round_num: int) -> str | None:
    f = KNOWLEDGE_DIR / "topic_diversity.jsonl"
    if not f.exists():
        return None
    rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("round") == round_num]
    return rows[-1]["status"] if rows else None


def equivalence_ok(rounds, gate: dict, headline: str | None = None) -> bool:
    """D-11 null-paper path. True when a carded (not exploratory) result in the
    arc passed a TOST (p < .05) with every equivalence margin inside the
    gate's sesoi. Restricted to the headline claim's specs when it is known."""
    import prediction_card as pc
    sesoi = pc._first_number((gate or {}).get("sesoi"))
    if sesoi is None:
        return False
    cards = pc.load_cards()
    for r in rounds:
        card = cards.get(r) or {}
        specs = {s.get("spec_id"): s for s in card.get("spec_plan") or []}
        for sid, res in pc.load_results(r).items():
            spec = specs.get(sid)
            if spec is None or str(sid).startswith("x_"):
                continue
            if headline and pc.spec_claim_id(card, spec) != headline:
                continue
            p, m = res.get("tost_p"), res.get("equivalence_margin")
            margins = [x for x in (m if isinstance(m, list) else [m]) if x is not None]
            try:
                if p is not None and margins and float(p) < 0.05 \
                        and all(abs(float(x)) <= abs(float(sesoi)) for x in margins):
                    return True
            except (TypeError, ValueError):
                continue
    return False


def verdict_distribution(start: int, round_num: int) -> str | None:
    """M10a verdict-distribution line, for arc_status only (never a prompt)."""
    try:
        return verdict.distribution_line(range(start, round_num + 1),
                                         range(min(SEASON2_FIRST_ROUND, start), round_num + 1))
    except Exception as e:
        print(f"  [arc] verdict distribution not computed: {e}")
        return None


# --------------------------------------------------------------------------
# Status and alerts
# --------------------------------------------------------------------------

def read_status() -> dict:
    return _read_json(ARC_STATUS_FILE)


def _same_arc(status: dict, arc: dict) -> bool:
    """Same arc by run_forum's rule: start_round compared as an integer and the
    seed with case and whitespace normalized. A legacy active_arc.json keeps
    start_round as a string ("28") while arc_status.json has 28."""
    return run_forum._same_arc(status, arc, run_forum._int(arc.get("start_round")))


def _write_status_file(data: dict) -> None:
    ARC_STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ARC_STATUS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def write_status(**kw) -> None:
    kw["ts"] = datetime.now().isoformat(timespec="seconds")
    arc = active_arc()
    kw.setdefault("seed", arc.get("seed"))
    kw.setdefault("start_round", arc.get("start_round"))
    prev = read_status()
    if _same_arc(prev, kw):
        for k in PERSISTENT_KEYS:
            if k in prev and k not in kw:
                kw[k] = prev[k]
    _write_status_file(kw)


def _append_waits(entries: list[dict], **update) -> None:
    """Add waits to arc_status (M11 records every wait with its reason)."""
    st = read_status()
    arc = active_arc()
    if not _same_arc(st, arc):
        st = {"seed": arc.get("seed"), "start_round": arc.get("start_round")}
    st.update(update, ts=datetime.now().isoformat(timespec="seconds"))
    st["waits"] = (list(st.get("waits") or []) + entries)[-50:]
    _write_status_file(st)


def record_wait(reason: str, seconds: float, **extra) -> dict:
    """Record one of run_arc's own waits in arc_status with state waiting, so
    a concurrent auto_run.sh does not start a second run meanwhile."""
    entry = {"reason": reason, "seconds": int(round(seconds)), "at": _iso(), **extra}
    _append_waits([entry], state="waiting", reason=f"waiting {int(round(seconds))} s ({reason})")
    print(f"  [arc] waiting {int(round(seconds))} s ({reason})")
    return entry


def record_run_waits(runs: list[dict]) -> None:
    """Copy the waits claude_cli made inside runs (overloaded, server error)
    from their sidecars into arc_status."""
    entries = [{"reason": w.get("reason"), "seconds": w.get("seconds"), "at": w.get("at"),
                "run_id": r.get("run_id"), "by": "claude_cli"}
               for r in runs for w in r.get("waits") or []]
    if entries:
        _append_waits(entries)


def _release_check() -> dict:
    """Run release_check.py --json. {"ok": bool, "failures": [str]}. Anything
    but a clean pass (a crash, a timeout, unreadable output) counts as a
    failure, so a push never goes out on an unchecked tree."""
    try:
        proc = subprocess.run([sys.executable, str(RELEASE_CHECK), "--json"], cwd=str(BASE_DIR),
                              capture_output=True, text=True, timeout=RELEASE_CHECK_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return {"ok": False, "failures": [f"release_check timed out after {RELEASE_CHECK_TIMEOUT_S} s"]}
    except OSError as e:
        return {"ok": False, "failures": [f"release_check could not run ({e})"]}
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        data = {}
    ok = proc.returncode == 0 and data.get("ok") is True
    failures = [str(f) for f in data.get("failures") or []]
    if not ok and not failures:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-1:] or ["no output"]
        failures = [f"release_check exited {proc.returncode} ({tail[0][:200]})"]
    return {"ok": ok, "failures": failures}


def _set_status_keys(**kw) -> None:
    """Merge keys into arc_status.json in place. A None value removes the key."""
    st = read_status()
    for k, v in kw.items():
        if v is None:
            st.pop(k, None)
        else:
            st[k] = v
    st["ts"] = datetime.now().isoformat(timespec="seconds")
    _write_status_file(st)


def push_checked(label: str) -> bool:
    """Push only after release_check passes (A3). On a failed check or a
    failed push the commit stays local, arc_status records push_blocked with
    the reasons, and an alert goes out. Returns True when pushed."""
    check = _release_check()
    if not check["ok"]:
        reasons = check["failures"][:20]
        LAST_PUSH.update(blocked=True, reasons=reasons)
        _set_status_keys(push_blocked={"at": _iso(), "commit": label, "reasons": reasons})
        claude_cli.notify("KNA arc: push blocked", f"release_check failed for {label} ({len(reasons)} "
                                                   f"problem(s), first: {reasons[0] if reasons else '?'}). "
                                                   f"The commit stays local.")
        print(f"  [arc] PUSH BLOCKED by release_check ({len(reasons)} problem(s)). The commit stays local:")
        for r in reasons[:10]:
            print(f"    - {r}")
        return False
    r = _git("push", "origin", "main")
    if r.returncode != 0:
        reasons = [f"git push failed: {(r.stderr or '').strip()[:200]}"]
        LAST_PUSH.update(blocked=True, reasons=reasons)
        _set_status_keys(push_blocked={"at": _iso(), "commit": label, "reasons": reasons})
        claude_cli.notify("KNA arc: push failed", f"{label}: {reasons[0]}")
        print(f"  [arc] PUSH FAILED: {reasons[0]}")
        return False
    LAST_PUSH.update(blocked=False, reasons=[])
    _set_status_keys(push_blocked=None)
    print("  [arc] release check passed, pushed")
    return True


def commit_round(round_num: int, label: str | None, push: bool, *,
                 paths: list[str] | None = None, build: bool = True) -> bool:
    """Commit (and push through the release check) under the round label.
    paths defaults to ROUND_PATHS."""
    if build:
        _build_site()
    _git("add", *(paths if paths is not None else ROUND_PATHS))
    msg = f"Auto: Season 2 R{round_num} ({label or 'no verdict'})"
    c = _git("commit", "-m", msg)
    if c.returncode != 0:
        print(f"  [arc] nothing to commit for R{round_num}")
        return False
    print(f"  [arc] committed: {msg}")
    if push:
        push_checked(msg)
    return True


def finish(code: int, state: str, reason: str, *, commit: dict | None = None, alert: bool = True,
           **fields) -> int:
    """End this invocation. Writes arc_status, commits if asked (after the
    status write, so the status is in the commit), prints and alerts. Every
    stop and pause goes through here (M11). A step that ends with the arc
    still running (alert=False) sends no alert."""
    write_status(state=state, reason=reason, **fields)
    if commit:
        LAST_PUSH.clear()
        commit_round(**commit)
        if LAST_PUSH.get("blocked"):
            reason += (" The push was blocked (release_check or git push failed) and the commit stays "
                       "local, see push_blocked in arc_status.")
    word = {"paused": "PAUSED", "paused_usage_limit": "PAUSED"}.get(state, "DONE" if code == 0 else "STOP")
    print(f"  [arc] {word}: {reason}")
    if alert:
        claude_cli.notify(f"KNA arc: {state}", reason)
    return code


def forum_keys() -> dict:
    """The FORUM_KEYS run_forum left in arc_status during the launch that
    just ended (they would be lost when run_arc rewrites the file)."""
    st = read_status()
    return {k: st[k] for k in FORUM_KEYS if k in st}


def arc_closed() -> bool:
    """True when the active arc has ended (an archive stop, a published or
    blocked draft, a close without a paper). This is run_forum's own rule
    (_arc_is_open), the one run_forum applies before it refuses a round
    without --topic. A status with a pending draft is still open (its draft
    runs first)."""
    return bool(active_arc().get("start_round")) and not run_forum._arc_is_open()


def _summary_path(round_num: int) -> Path:
    return BASE_DIR / "summaries" / f"round_{round_num:02d}.md"


def run_post_round(log_path: Path) -> int:
    """run_forum's post-round steps for the latest complete round (ledger,
    taxonomy, summary) without launching an agent (--rounds 0)."""
    cmd = [sys.executable, "-u", str(RUN_FORUM), "--resume", "--rounds", "0"]
    rc = _run_logged(cmd, log_path, label="post-round steps")
    return 1 if rc is None else rc


# --------------------------------------------------------------------------
# Failures read back from the run sidecars (claude_cli)
# --------------------------------------------------------------------------

def _sidecar_paths() -> set:
    return set(LOGS_DIR.glob("*/*.sidecar.json")) if LOGS_DIR.exists() else set()


def _new_runs(before: set) -> list[dict]:
    """Sidecars written since the `before` snapshot, oldest first."""
    runs = []
    for p in sorted(_sidecar_paths() - before, key=lambda q: (q.stat().st_mtime, q.name)):
        d = _read_json(p)
        if d:
            runs.append(d)
    return runs


def _failed(runs: list[dict]) -> list[dict]:
    return [r for r in runs if r.get("failure") not in (None, "ok")]


def _limit_kind(run: dict) -> str | None:
    for a in reversed(run.get("attempts") or []):
        if a.get("usage_limit_kind"):
            return a["usage_limit_kind"]
    return None


def _stop_reason(failed: list[dict]) -> str | None:
    """Failures that stop the arc at once: the per-arc call cap and
    auth_or_config."""
    for r in failed:
        if r.get("terminal_reason") == "max_calls_per_arc":
            return f"max_calls_per_arc reached ({r.get('budget_refused') or 'call refused by claude_cli'})"
    for r in failed:
        if r.get("failure") == "auth_or_config":
            return (f"auth_or_config failure in run {r.get('run_id')} "
                    f"({r.get('terminal_reason') or 'no terminal reason'})")
    return None


def calls_budget_reason(cfg: dict, arc_id: str | None) -> str | None:
    """max_calls_per_arc checked before a launch (claude_cli also enforces it
    per call)."""
    if not arc_id:
        return None
    cap = int(cfg.get("max_calls_per_arc") or claude_cli.DEFAULT_MAX_CALLS_PER_ARC)
    used = claude_cli.count_calls_in_arc(arc_id)
    if used >= cap:
        return f"max_calls_per_arc reached ({used} of {cap} CLI calls used in arc {arc_id})"
    return None


def _failure_wait(policy: dict, failed: list[dict]) -> tuple[str | None, int]:
    """Wait before resuming after a transient failure."""
    classes = {r.get("failure") for r in failed}
    if "overloaded" in classes:
        return "overloaded", int(policy.get("overloaded_wait_s") or 0)
    if "server_error" in classes:
        return "server_error", int(policy.get("server_error_wait_s") or 0)
    return None, 0


def usage_limit_decision(policy: dict, resume_at: str | None, kind: str | None,
                         waited_s: float = 0.0) -> tuple[str, float, str]:
    """("sleep", seconds, why) or ("pause", 0, why) after a usage limit.

    Pause-only is the default (D-12). With failure_policy.usage_limit
    "sleep_and_resume", a session limit whose reset plus 120 s falls within
    usage_limit_max_wait_s (default 6 h, counting what this invocation already
    waited) is waited out. Weekly limits and unknown reset times pause."""
    if str(policy.get("usage_limit") or "pause") != "sleep_and_resume":
        return "pause", 0.0, "pause-only policy"
    if kind == "weekly":
        return "pause", 0.0, "weekly limit"
    until = _parse_iso(resume_at)
    if until is None:
        return "pause", 0.0, "reset time unknown"
    wait = max(0.0, (until - _now()).total_seconds()) + USAGE_LIMIT_MARGIN_S
    ceiling = float(policy.get("usage_limit_max_wait_s") or DEFAULT_USAGE_LIMIT_MAX_WAIT_S)
    if waited_s + wait > ceiling:
        return "pause", 0.0, (f"reset in {wait / 3600:.1f} h is beyond the "
                              f"{ceiling / 3600:.1f} h wait ceiling")
    return "sleep", wait, f"session limit resets at {resume_at}"


# --------------------------------------------------------------------------
# Decision
# --------------------------------------------------------------------------

def decide(state: dict, arc_rounds: int, min_rounds: int, div_status: str | None, *,
           kill_depth: int | None = None, switches: dict | None = None,
           gate: dict | None = None) -> tuple[str, str]:
    """-> (action, reason); action in {continue, stop, draft_and_stop, close_no_paper}.

    state["verdict"] is the verdict of record, already effective. Depth is
    arc_rounds >= min_rounds, or with switches["min_tests_before_draft"] set
    (D-11), kill_depth >= that number. The null-paper path and closed_no_paper
    act only when their switches are on."""
    sw = dict(D11_DEFAULTS)
    sw.update({k: v for k, v in (switches or {}).items() if v is not None})
    v, ft = state.get("verdict"), state.get("falsifier_tested")
    if sw["min_tests_before_draft"]:
        need = int(sw["min_tests_before_draft"])
        depth_ok = kill_depth is not None and kill_depth >= need
        depth_txt = f"kill-test depth {kill_depth if kill_depth is not None else 'unknown'}/{need}"
    else:
        depth_ok = arc_rounds >= min_rounds
        depth_txt = f"arc depth {arc_rounds}/{min_rounds}"

    if v == "archive":
        # Name only the cause the Critic recorded (VV-03).
        ps = state.get("prior_status")
        if ft == "yes" and ps == "overturned":
            reason = "arc closed: falsifier tested, prior overturned, finding archived"
        elif ft == "yes":
            reason = f"arc closed: falsifier tested, finding archived (prior_status {ps or 'not recorded'})"
        else:
            reason = "arc closed: Critic archived the finding"
        if div_status == "block":
            # The guard's thresholds are uncalibrated, so a block is reported
            # next to the Critic's archive and never given as its reason (V-12).
            reason += ". The topic-diversity guard was at block, with provisional thresholds"
        return "stop", reason
    null_path = bool(sw["null_paper_path"]) and state.get("prior_status") == "overturned" \
        and _yes((gate or {}).get("null_paper")) and bool(state.get("equivalence_ok"))
    if null_path and depth_ok:
        return "draft_and_stop", (f"arc complete: null paper (prior overturned, equivalence against "
                                  f"the sesoi passed, null_paper yes) at {depth_txt}")
    if null_path:
        reason = f"null paper path open, but {depth_txt}: deepening"
    elif v == "pursue":
        if ft != "yes":
            reason = "pursue without falsifier test: continuing so Analyst runs the falsifier"
        elif not depth_ok:
            reason = f"pursue + falsifier tested, but {depth_txt}: deepening"
        else:
            return "draft_and_stop", "arc complete: pursue with falsifier tested at sufficient depth"
    elif v == "revise":
        reason = "revise: continuing"
    else:
        reason = "no verdict parsed: continuing (check the Critic post)"
    if sw["closed_no_paper"] and arc_rounds >= int(sw["max_arc_rounds"]):
        return "close_no_paper", (f"arc closed without a paper at max arc rounds "
                                  f"({arc_rounds}/{int(sw['max_arc_rounds'])}), last verdict "
                                  f"{v or 'none'} ({reason})")
    return "continue", reason


# --------------------------------------------------------------------------
# Forum rounds and drafting
# --------------------------------------------------------------------------

def run_round(topic: str | None, log_path: Path, allow_data_change: bool = False) -> int:
    cmd = [sys.executable, "-u", str(RUN_FORUM), "--resume", "--rounds", "1"]
    if topic:
        cmd += ["--topic", topic]
    if allow_data_change:
        cmd.append("--allow-data-change")
    rc = _run_logged(cmd, log_path, label="round launch")
    return 1 if rc is None else rc


def run_draft(round_num: int, log_path: Path, force: bool = False) -> int | None:
    cmd = [sys.executable, "-u", str(DRAFT_ARTICLE), "--round", str(round_num)]
    if force:
        cmd.append("--force")
    return _run_logged(cmd, log_path, timeout=DRAFT_TIMEOUT_S, label="draft")


def _articles(round_num: int) -> list[Path]:
    return sorted(ARTICLES_DIR.glob(f"*_r{round_num}.tex")) if ARTICLES_DIR.exists() else []


def _failed_draft(round_num: int) -> tuple[str | None, list]:
    """(repo-relative quarantine folder, failed blocking gates) of the latest
    failed draft for the round."""
    hits = [p for p in FAILED_DRAFTS_DIR.glob(f"*_r{round_num}*") if (p / "FAILED.json").exists()] \
        if FAILED_DRAFTS_DIR.exists() else []
    if not hits:
        return None, []
    latest = max(hits, key=lambda p: (p / "FAILED.json").stat().st_mtime)
    failed = _read_json(latest / "FAILED.json").get("failed_blocking") or []
    try:
        rel = str(latest.relative_to(BASE_DIR))
    except ValueError:
        rel = f"workspace/failed_drafts/{latest.name}"
    return rel, list(failed)


def draft_step(round_num: int, args, cfg: dict, log_path: Path, *, force: bool = False,
               fields: dict | None = None) -> int:
    """Draft the arc's paper. Publish (commit articles/ and docs/, push) only
    on draft_article exit 0. Exit 2 means the paper gates failed (D-09)."""
    fields = dict(fields or {})
    pending = {"round": round_num, "force": force}
    if args.no_draft:
        return finish(0, "stopped", f"arc complete at R{round_num}, drafting skipped (--no-draft). "
                                    f"The next run_arc invocation drafts.", pending_draft=pending, **fields)
    budget = calls_budget_reason(cfg, current_arc_id())
    if budget:
        return finish(1, "stopped", f"{budget}. The draft for R{round_num} was not started.",
                      pending_draft=pending, **fields)
    if not _summary_path(round_num).exists():
        # The round's post-round steps did not finish (for example a usage
        # limit in the summary). Run them first, so the summary exists and
        # draft_article's hand-coding check (C5) reads it.
        print(f"  [arc] summaries/round_{round_num:02d}.md is missing. Running the post-round steps first.")
        rc = run_post_round(log_path)
        if rc == claude_cli.EXIT_USAGE_LIMIT:
            return finish(rc, "paused_usage_limit", f"usage limit in the post-round steps of R{round_num}",
                          resume_after=read_status().get("resume_after"), pending_draft=pending,
                          **forum_keys(), **fields)
        if rc != 0:
            return finish(1, "stopped", f"the post-round steps of R{round_num} exited {rc} before the "
                                        f"draft (see the arc log)", pending_draft=pending,
                          **forum_keys(), **fields)
        if not _summary_path(round_num).exists():
            # Fail closed. Without the summary draft_article skips its C5
            # hand-coding dictionary check.
            return finish(1, "stopped", f"summaries/round_{round_num:02d}.md is still missing after the "
                                        f"post-round steps, so the draft for R{round_num} was not started",
                          pending_draft=pending, **forum_keys(), **fields)
    policy = _policy(cfg)
    waited = 0.0
    while True:
        seen = _sidecar_paths()
        print(f"  [arc] drafting the paper for R{round_num}")
        code = run_draft(round_num, log_path, force)
        runs = _new_runs(seen)
        record_run_waits(runs)
        if code != claude_cli.EXIT_USAGE_LIMIT:
            break
        limit = next((r for r in _failed(runs) if r.get("failure") == "usage_limit"), {})
        act, secs, why = usage_limit_decision(policy, limit.get("resume_at"), _limit_kind(limit), waited)
        if act == "pause":
            return finish(claude_cli.EXIT_USAGE_LIMIT, "paused_usage_limit",
                          f"usage limit while drafting R{round_num} ({why})",
                          resume_after=limit.get("resume_at"), pending_draft=pending, **fields)
        record_wait("usage_limit", secs, phase="draft", round=round_num,
                    resume_after=limit.get("resume_at"))
        claude_cli.notify("KNA arc: waiting", f"usage limit while drafting R{round_num}, "
                                              f"resuming after {limit.get('resume_at')}")
        _sleep(secs)
        waited += secs

    if code == 0:
        papers = _articles(round_num)
        if not papers:
            return finish(1, "stopped", f"draft_article exited 0 but articles/ has no paper for "
                                        f"R{round_num}", pending_draft=pending, **fields)
        return finish(0, "stopped", f"arc complete: the paper for R{round_num} passed the paper "
                                    f"gates and was published", article=papers[-1].name,
                      commit={"round_num": round_num, "label": "article", "push": not args.no_push,
                              "paths": PAPER_PATHS}, **fields)
    if code == 2:
        where, gates = _failed_draft(round_num)
        return finish(2, "draft_blocked",
                      f"the draft for R{round_num} failed blocking paper gates "
                      f"({', '.join(gates) or 'see FAILED.json'}) and was quarantined. "
                      f"Nothing from it is committed or pushed.",
                      failed_draft=where, failed_blocking=gates,
                      commit={"round_num": round_num, "label": "draft blocked", "push": False,
                              "paths": LOCAL_PATHS, "build": False}, **fields)
    if code == 3:
        # draft_article.EXIT_EXTERNAL_WRITE: a figure script wrote outside the
        # repository. The draft is quarantined and the arc holds until --ack-stop.
        where, _ = _failed_draft(round_num)
        ext = []
        if where:
            try:
                ext = json.loads((BASE_DIR / where / "EXTERNAL_WRITES.json").read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                ext = []
        return finish(3, "external_write",
                      f"a figure script wrote outside the repository while drafting R{round_num}. The draft "
                      f"was quarantined and nothing is published. Check logs/external_writes/, then rerun "
                      f"with --ack-stop.", failed_draft=where, external_writes=ext[:20],
                      pending_draft=pending, **fields)
    what = f"timed out after {DRAFT_TIMEOUT_S // 3600} h" if code is None else f"exited {code}"
    return finish(1, "stopped", f"draft_article {what} for R{round_num} (see the arc log)",
                  pending_draft=pending, **fields)


# --------------------------------------------------------------------------
# Researcher-owned files changed during a run (--researcher-files restore)
# --------------------------------------------------------------------------

def _restore_paths(change: dict) -> tuple[Path, Path, Path] | None:
    """(current file, saved start version, restored_away copy) for one
    researcher_owned_changes entry, or None when it names no researcher-owned
    file or its saved folder is not under knowledge/staging/."""
    rel, saved = change.get("path"), str(change.get("saved") or "")
    if rel not in staging.RESEARCHER_OWNED or not saved.startswith("knowledge/staging/") or ".." in saved:
        return None
    return BASE_DIR / rel, BASE_DIR / saved / "before" / rel, BASE_DIR / saved / "restored_away" / rel


def restore_problems(changes: list[dict]) -> list[str]:
    """Why a restore cannot run. Empty when every change can be undone."""
    if not changes:
        return ["the stop lists no changed files"]
    out = []
    for c in changes:
        paths = _restore_paths(c)
        if paths is None:
            out.append(f"{c.get('path', '?')} has no saved folder under knowledge/staging/")
        elif c.get("change") != "added" and not paths[1].exists():
            out.append(f"{c.get('path')} has no saved start version")
    return out


def restore_researcher_files(changes: list[dict]) -> list[dict]:
    """Put back the start-of-run version of each researcher-owned file the
    stopped run changed (staging saved it under <saved>/before/). The
    current version is first copied to <saved>/restored_away/, so nothing is
    lost. A file the run added has no start version and is moved there."""
    done = []
    for c in changes:
        current, before, away = _restore_paths(c)
        if current.exists():
            away.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(current, away)
        if before.exists():
            current.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(before, current)
            action = "start-of-run version restored"
        elif current.exists():
            current.unlink()
            action = "added by the run, moved to restored_away"
        else:
            action = "nothing to restore"
        done.append({"path": c.get("path"), "action": action})
        print(f"  [arc] {c.get('path')}: {action}")
    return done


# --------------------------------------------------------------------------
# Main loop
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """run() under logs/run_arc.lock. A second run_arc while one runs exits
    EXIT_BUSY without touching arc_status or sending an alert."""
    lock = acquire_run_lock()
    if lock is None:
        pid = _read_json(_run_lock_path()).get("pid")
        print(f"  [arc] REFUSED: another run_arc (pid {pid}) is running. Nothing was changed. Wait for it to "
              f"finish (python3 auto_arc.py status shows the arc).")
        return EXIT_BUSY
    try:
        return run(argv)
    finally:
        release_run_lock(lock)


def run(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Season 2 arc runner")
    ap.add_argument("--topic", default=None, help="Open a new arc with this signed seed")
    ap.add_argument("--max-rounds", type=int, default=5, help="Rounds this invocation may run (default 5)")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--no-draft", action="store_true", help="Do not auto-draft on completion")
    ap.add_argument("--ack-stop", action="store_true",
                    help="Acknowledge an external_write or researcher_file_changed stop after checking it "
                         "(recorded in arc_status), then continue")
    ap.add_argument("--allow-data-change", action="store_true",
                    help="Continue although the KNA data changed since the arc pinned them (run_forum "
                         "records the change in active_arc.json, arc_status.json and gate_events.jsonl)")
    ap.add_argument("--researcher-files", choices=("keep", "restore"), default=None,
                    help="With --ack-stop on a researcher_file_changed stop, keep the changed files as they "
                         "are or restore the versions from the start of the run")
    args = ap.parse_args(argv)

    cfg = _config()
    if cfg.get("season", 1) < 2:
        raise SystemExit("run_arc.py is a Season 2 tool; agents.json says season < 2.")
    policy = _policy(cfg)
    budget_max = int(policy.get("max_failed_runs_per_invocation") or 4)
    min_rounds = int(cfg.get("min_arc_rounds_before_draft", 3))
    switches = d11_switches(cfg)
    LOGS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    log_path = LOGS_DIR / f"arc_{stamp}.log"
    print(f"  [arc] log: {log_path}")

    # The last decided round (and a pending draft) of the active arc, kept in
    # every status this invocation writes.
    prev = read_status()
    same_arc = _same_arc(prev, active_arc())
    carried = {k: prev[k] for k in ROUND_FIELDS if k in prev} if same_arc else {}
    pending = prev.get("pending_draft") if same_arc and not args.topic else None
    if pending:
        carried["pending_draft"] = pending

    # An external write or a changed researcher-owned file holds the arc until
    # someone has looked at it. Checked before anything rewrites arc_status.
    if prev.get("state") in ACK_STATES:
        if not args.ack_stop:
            print(f"  [arc] REFUSED: the arc is stopped ({prev.get('state')}: {prev.get('reason')}). "
                  f"Check the change, then rerun with --ack-stop.")
            return 1
        ack = {"state": prev.get("state"), "reason": prev.get("reason"), "at": _iso()}
        if prev.get("state") == "researcher_file_changed":
            # V-07: a kept change reaches every later prompt with the authority
            # its text claims, so the acknowledger decides what stays.
            changes = prev.get("researcher_owned_changes") or []
            if args.researcher_files is None:
                print(f"  [arc] REFUSED: researcher-owned file(s) changed during a run "
                      f"({', '.join(c.get('path', '?') for c in changes) or 'see the reason'}). Rerun with "
                      f"--ack-stop --researcher-files keep (the changes stay and reach later prompts) or "
                      f"--researcher-files restore (the start-of-run versions come back).")
                return 1
            ack["researcher_files"] = args.researcher_files
            if args.researcher_files == "restore":
                problems = restore_problems(changes)
                if problems:
                    print(f"  [arc] REFUSED: cannot restore ({'; '.join(problems)}). Nothing was changed.")
                    return 1
                ack["restored"] = restore_researcher_files(changes)
        acks = list(prev.get("stops_acknowledged") or []) + [ack]
        write_status(state="running", reason=f"{prev.get('state')} stop acknowledged (--ack-stop)",
                     stops_acknowledged=acks[-20:], **carried)
        print(f"  [arc] {prev.get('state')} stop acknowledged"
              + (f" (researcher files: {args.researcher_files})" if "researcher_files" in ack else ""))

    # M05: a findings ledger with duplicate keys refuses the run.
    ledger = ledger_audit.check(FINDINGS_FILE)
    if not ledger["ok"]:
        return finish(1, "stopped", f"findings ledger has {ledger['duplicate_keys']} duplicate keys "
                                    f"({ledger['duplicate_rows']} duplicate rows). Run "
                                    f"python3 ledger_audit.py --dedupe before the arc continues.", **carried)
    errors = switch_errors(cfg)
    if errors:
        return finish(1, "stopped", "configuration refused. " + ". ".join(errors), **carried)

    if isinstance(pending, dict) and pending.get("round"):
        print(f"  [arc] resuming the pending draft for R{pending['round']}")
        return draft_step(int(pending["round"]), args, cfg, log_path, force=bool(pending.get("force")),
                          fields={k: v for k, v in carried.items() if k in ROUND_FIELDS})

    # One arc, one paper. A closed arc runs no further rounds (E2E-01).
    if not args.topic and arc_closed():
        print(f"  [arc] REFUSED: the active arc is closed (state {prev.get('state')}, action "
              f"{prev.get('action')}, last round R{prev.get('last_round')}: {prev.get('reason')}). "
              f"A new arc needs a signed topic_gate entry and --topic.")
        return 1

    topic = args.topic
    rounds_run = failures = 0
    waited = 0.0
    fields: dict = {} if topic else {k: v for k, v in carried.items() if k in ROUND_FIELDS}
    while rounds_run < args.max_rounds:
        rnd = None if topic else unevaluated_round(fields.get("last_round"))
        if rnd is not None:
            print(f"  [arc] R{rnd} is complete but was never decided on. Deciding it before any launch.")
            if not _summary_path(rnd).exists():
                # Its post-round steps did not finish (for example a usage
                # limit in the summary). They run first, so the decision reads
                # the backfilled verdict of record and a draft reads the summary.
                print(f"  [arc] summaries/round_{rnd:02d}.md is missing. Running the post-round steps first.")
                prc = run_post_round(log_path)
                if prc == claude_cli.EXIT_USAGE_LIMIT:
                    return finish(prc, "paused_usage_limit", f"usage limit in the post-round steps of R{rnd}",
                                  resume_after=read_status().get("resume_after"), rounds_run=rounds_run,
                                  **forum_keys(), **fields)
                if prc != 0:
                    return finish(1, "stopped", f"the post-round steps of R{rnd} exited {prc} (see the arc log)",
                                  rounds_run=rounds_run, **forum_keys(), **fields)
        else:
            rnd, roles = forum_index.next_round_plan(forum_dir=FORUM_DIR)
            budget = calls_budget_reason(cfg, None if topic else current_arc_id())
            if budget:
                return finish(1, "stopped", f"{budget}. R{rnd} was not launched.", rounds_run=rounds_run,
                              **fields)
            arc_before = ACTIVE_ARC_FILE.read_bytes() if ACTIVE_ARC_FILE.exists() else None
            seen = _sidecar_paths()
            print(f"  [arc] launching R{rnd} ({', '.join(roles)})")
            launched_at = _iso()
            rc = run_round(topic, log_path, allow_data_change=args.allow_data_change)
            if topic and (ACTIVE_ARC_FILE.read_bytes() if ACTIVE_ARC_FILE.exists() else None) != arc_before:
                topic = None   # the arc opened, so a relaunch continues it instead of reopening it
            runs = _new_runs(seen)
            record_run_waits(runs)
            failed = _failed(runs)
            limit = next((r for r in failed if r.get("failure") == "usage_limit"), None)

            if rc != 0:
                disk = read_status()
                refused = disk.get("data_pin_refused") or {}
                if refused and str(refused.get("ts") or "") >= launched_at[:19]:
                    # A1: run_forum refused the round because the KNA data
                    # changed since the arc pinned them.
                    changes = refused.get("changes") or []
                    return finish(1, "stopped", f"the KNA data changed since the arc pinned them "
                                                f"({refused.get('pinned')} to {refused.get('now')}, "
                                                f"{len(changes)} file(s): {'; '.join(changes[:3])}"
                                                f"{'; ...' if len(changes) > 3 else ''}). R{rnd} was not run. "
                                                f"Restore the pinned data, or rerun with --allow-data-change "
                                                f"(recorded).", rounds_run=rounds_run, **forum_keys(), **fields)
                if disk.get("state") in ACK_STATES:
                    # run_forum stopped on an external write or a changed
                    # researcher-owned file. Keep that state and its detail.
                    return finish(1, disk["state"], f"{disk['state']}: {disk.get('reason') or 'no reason'} "
                                                    f"at R{rnd}. Check it, then rerun with --ack-stop"
                                                    + (" --researcher-files keep|restore." if disk["state"] == "researcher_file_changed" else "."),
                                  rounds_run=rounds_run, **forum_keys(), **fields)

            if rc == claude_cli.EXIT_USAGE_LIMIT or (rc != 0 and limit):
                limit = limit or {}
                failures += max(1, len(failed))
                act, secs, why = usage_limit_decision(policy, limit.get("resume_at"), _limit_kind(limit),
                                                      waited)
                if act == "sleep" and failures >= budget_max:
                    act, why = "pause", f"failure budget of {budget_max} runs reached"
                if act == "pause":
                    return finish(claude_cli.EXIT_USAGE_LIMIT, "paused_usage_limit",
                                  f"usage limit at R{rnd} ({why})", resume_after=limit.get("resume_at"),
                                  last_run=limit.get("run_id"), rounds_run=rounds_run, **forum_keys(),
                                  **fields)
                record_wait("usage_limit", secs, round=rnd, resume_after=limit.get("resume_at"))
                claude_cli.notify("KNA arc: waiting", f"usage limit at R{rnd}, resuming after "
                                                      f"{limit.get('resume_at')}")
                _sleep(secs)
                waited += secs
                continue

            if rc != 0:
                stop = _stop_reason(failed)
                if stop:
                    return finish(1, "stopped", f"{stop} at R{rnd}", rounds_run=rounds_run, **forum_keys(),
                                  **fields)
                if not failed:
                    return finish(1, "stopped", f"run_forum exited {rc} at R{rnd} without a recorded run "
                                                f"failure (see the arc log)", rounds_run=rounds_run,
                                  **forum_keys(), **fields)
                failures += len(failed)
                classes = ", ".join(f"{r.get('role') or r.get('task')} {r.get('failure')}" for r in failed)
                if failures >= budget_max:
                    return finish(1, "stopped", f"failure budget reached with {failures} failed runs in this "
                                                f"invocation (max_failed_runs_per_invocation {budget_max}), "
                                                f"last at R{rnd} ({classes})", rounds_run=rounds_run,
                                  **forum_keys(), **fields)
                why, wait = _failure_wait(policy, failed)
                if wait:
                    record_wait(why, wait, round=rnd)
                    _sleep(wait)
                print(f"  [arc] R{rnd}: {classes}. Resuming the round ({failures}/{budget_max} failed runs).")
                continue

            topic = None
            missing = forum_index.missing_roles(rnd, forum_dir=FORUM_DIR)
            cur = forum_index.current_round(forum_dir=FORUM_DIR)
            if missing or cur != rnd:
                detail = f"missing {', '.join(missing)}" if missing else f"the forum is at R{cur}"
                return finish(1, "stopped", f"round R{rnd} is incomplete after a clean run_forum exit "
                                            f"({detail})", rounds_run=rounds_run, **fields)
            rounds_run += 1
        state = critic_state(rnd, cfg)
        if state["source"] is None:
            return finish(1, "stopped", f"no Critic post in R{rnd}", rounds_run=rounds_run, **fields)
        start = arc_start()
        arc_rounds = rnd - start + 1
        div = diversity_state(rnd)
        gate = active_arc()
        if switches["null_paper_path"]:
            state["equivalence_ok"] = equivalence_ok(range(start, rnd + 1), gate, state["headline_claim_id"])
        action, reason = decide(state, arc_rounds, min_rounds, div, kill_depth=state["kill_depth"],
                                switches=switches, gate=gate)
        fields = {
            "last_round": state["round"], "verdict": state["verdict"],
            "verdict_critic": state["verdict_critic"], "falsifier_tested": state["falsifier_tested"],
            "diversity": div, "arc_depth": arc_rounds, "min_arc_rounds_before_draft": min_rounds,
            "kill_depth": state["kill_depth"],
            "depth_rule": "kill_tests" if switches["min_tests_before_draft"] else "rounds",
            "action": action, "one_line": state["one_line"], "overrides": state["overrides"],
            "verdict_distribution": verdict_distribution(start, rnd),
        }
        if state["kill_depth"] is None:
            fields["kill_depth_note"] = "not computed (stage2.binding_checks is off)" \
                if not _stage2(cfg, "binding_checks") else "not computed (no binding checks for this round)"
        print(f"  [arc] R{state['round']}: verdict={state['verdict']} falsifier={state['falsifier_tested']} "
              f"diversity={div} arc_depth={arc_rounds} kill_depth={state['kill_depth']} "
              f"-> {action} ({reason})")
        commit = {"round_num": state["round"], "label": state["verdict"], "push": not args.no_push}

        if action == "continue":
            write_status(state="running", reason=reason, rounds_run=rounds_run, **fields)
            commit_round(**commit)
            continue
        if action == "stop":
            return finish(0, "stopped", reason, commit=commit, rounds_run=rounds_run, **fields)
        if action == "close_no_paper":
            headline = state["one_line"] or state["headline_claim_id"] or "(no headline recorded)"
            ledger_audit.append_unique({
                "finding": (f"Arc {current_arc_id() or '?'} closed without a paper at R{state['round']}, "
                            f"last headline \"{headline}\""),
                # The closure is the row's status. verdict keeps the Critic's
                # verdict of record, so the label set stays pursue/revise/archive,
                # and it is None when there is no verdict of record (V-12).
                "status": "closed_no_paper", "round": state["round"], "source": "run_arc",
                "verdict": state["verdict"], "reasons": [reason] + state["overrides"],
            }, path=FINDINGS_FILE)
            return finish(0, "closed_no_paper", reason, commit=commit, headline=headline,
                          rounds_run=rounds_run, **fields)
        # draft_and_stop. --force only when a D-11 depth rule allowed a draft
        # that draft_article's own round-count rule would refuse.
        force = arc_rounds < min_rounds
        write_status(state="drafting", reason=reason, rounds_run=rounds_run,
                     pending_draft={"round": rnd, "force": force}, **fields)
        commit_round(**commit)
        return draft_step(rnd, args, cfg, log_path, force=force, fields=fields)

    if rounds_run and fields.get("action") == "continue":
        # A supervised step (cron runs --max-rounds 1) that ended on a
        # continue decision leaves the arc running, so the next step goes on.
        return finish(0, "running", f"step done: R{fields.get('last_round')} decided continue, and this "
                                    f"invocation's max rounds ({args.max_rounds}) is reached. The next "
                                    f"invocation continues the arc.", alert=False,
                      rounds_run=rounds_run, **fields)
    return finish(0, "paused", f"max rounds ({args.max_rounds}) reached with no round decided in this "
                               f"invocation. Researcher review requested.", rounds_run=rounds_run, **fields)


if __name__ == "__main__":
    sys.exit(main())

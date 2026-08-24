#!/usr/bin/env python3
"""Season 2 arc runner: one instruction, one arc, supervised to completion.

Runs forum rounds back to back and stops on the arc's own rules, so the
researcher signs a topic_gate entry, launches this once, and reads the result.

Stop rules (checked after every round, from the Critic's scoring block):
  archive                                   -> arc closed (overturned prior,
                                               already-answered question, or
                                               duplicate topic). STOP.
  pursue + falsifier_tested yes + depth ok  -> draft the arc's one paper, STOP.
  pursue + falsifier_tested no              -> continue (Critic broke its own
                                               rule; the next round tests it).
  revise / anything else                    -> continue.
  --max-rounds reached                      -> STOP and flag for the researcher.
  agent failure after run_forum's retries   -> STOP and flag.

After every round the site is rebuilt and the round is committed and pushed
(disable with --no-push). Status lives in knowledge/arc_status.json.

Usage:
    python3 run_arc.py --topic "<signed seed>"        # open a new arc and run it
    python3 run_arc.py                                # continue the active arc
    python3 run_arc.py --max-rounds 1 --no-draft      # single supervised step (cron)
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
FORUM_DIR = BASE_DIR / "forum"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
LOGS_DIR = BASE_DIR / "logs"
AGENTS_FILE = BASE_DIR / "agents.json"
ACTIVE_ARC_FILE = KNOWLEDGE_DIR / "active_arc.json"
ARC_STATUS_FILE = KNOWLEDGE_DIR / "arc_status.json"


def _config() -> dict:
    with open(AGENTS_FILE) as f:
        data = json.load(f)
    cfg = dict(data.get("forum_config", {}))
    cfg["season"] = data.get("season", 1)
    cfg["n_agents"] = len(data["agents"])
    return cfg


def current_round(n_agents: int) -> int:
    return len(list(FORUM_DIR.glob("*.md"))) // n_agents


def critic_state(round_num: int, n_agents: int) -> dict:
    """Verdict, falsifier flag, and labels from the round's Critic post."""
    posts = sorted(FORUM_DIR.glob("*.md"))
    for p in posts[(round_num - 1) * n_agents: round_num * n_agents]:
        if "critic" not in p.name:
            continue
        text = p.read_text(encoding="utf-8")
        out = {"source": p.name}
        m = re.search(r"verdict:\s*(pursue|revise|archive)", text)
        out["verdict"] = m.group(1) if m else None
        m = re.search(r"falsifier_tested:\s*([A-Za-z_]+)", text)
        out["falsifier_tested"] = (m.group(1).lower() if m else None)
        m = re.search(r'one_line:\s*"([^"]+)"', text)
        out["one_line"] = m.group(1) if m else None
        return out
    return {"source": None, "verdict": None, "falsifier_tested": None, "one_line": None}


def diversity_state(round_num: int) -> str | None:
    f = KNOWLEDGE_DIR / "topic_diversity.jsonl"
    if not f.exists():
        return None
    rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if r.get("round") == round_num]
    return rows[-1]["status"] if rows else None


def write_status(**kw) -> None:
    kw["ts"] = datetime.now().isoformat(timespec="seconds")
    if ACTIVE_ARC_FILE.exists():
        try:
            arc = json.loads(ACTIVE_ARC_FILE.read_text())
            kw.setdefault("seed", arc.get("seed"))
            kw.setdefault("start_round", arc.get("start_round"))
        except Exception:
            pass
    ARC_STATUS_FILE.write_text(json.dumps(kw, ensure_ascii=False, indent=2))


def run_round(topic: str | None, log_path: Path) -> int:
    cmd = [sys.executable, "-u", str(BASE_DIR / "run_forum.py"), "--resume", "--rounds", "1"]
    if topic:
        cmd += ["--topic", topic]
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n===== run_arc round launch {datetime.now().isoformat(timespec='seconds')} =====\n")
        log.flush()
        proc = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=str(BASE_DIR))
    return proc.returncode


def commit_round(round_num: int, verdict: str | None, push: bool) -> None:
    subprocess.run([sys.executable, str(BASE_DIR / "build_site.py")],
                   capture_output=True, cwd=str(BASE_DIR))
    subprocess.run(["git", "add", "forum/", "summaries/", "knowledge/", "articles/", "docs/", "topic_gate.md"],
                   cwd=str(BASE_DIR), capture_output=True)
    msg = f"Auto: Season 2 R{round_num} ({verdict or 'no verdict'})"
    c = subprocess.run(["git", "commit", "-m", msg], cwd=str(BASE_DIR), capture_output=True, text=True)
    if c.returncode != 0:
        print(f"  [arc] nothing to commit for R{round_num}")
        return
    print(f"  [arc] committed: {msg}")
    if push:
        r = subprocess.run(["git", "push", "origin", "main"], cwd=str(BASE_DIR),
                           capture_output=True, text=True)
        print("  [arc] pushed" if r.returncode == 0 else f"  [arc] PUSH FAILED: {r.stderr[:200]}")


def decide(state: dict, arc_rounds: int, min_rounds: int, div_status: str | None) -> tuple[str, str]:
    """-> (action, reason); action in {continue, stop, draft_and_stop}."""
    v, ft = state.get("verdict"), state.get("falsifier_tested")
    if v == "archive":
        if div_status == "block":
            return "stop", "arc closed: duplicate topic (diversity block + archive)"
        if ft == "yes":
            return "stop", "arc closed: falsifier tested, finding archived (prior overturned or already answered)"
        return "stop", "arc closed: Critic archived the finding"
    if v == "pursue":
        if ft != "yes":
            return "continue", "pursue without falsifier test: continuing so Analyst runs the falsifier"
        if arc_rounds < min_rounds:
            return "continue", f"pursue + falsifier tested, but arc depth {arc_rounds}/{min_rounds}: deepening"
        return "draft_and_stop", "arc complete: pursue with falsifier tested at sufficient depth"
    if v == "revise":
        return "continue", "revise: continuing"
    return "continue", "no verdict parsed: continuing (check the Critic post)"


def main() -> None:
    ap = argparse.ArgumentParser(description="Season 2 arc runner")
    ap.add_argument("--topic", default=None, help="Open a new arc with this signed seed")
    ap.add_argument("--max-rounds", type=int, default=5, help="Rounds this invocation may run (default 5)")
    ap.add_argument("--no-push", action="store_true")
    ap.add_argument("--no-draft", action="store_true", help="Do not auto-draft on completion")
    args = ap.parse_args()

    cfg = _config()
    if cfg["season"] < 2:
        raise SystemExit("run_arc.py is a Season 2 tool; agents.json says season < 2.")
    n_agents = cfg["n_agents"]
    min_rounds = int(cfg.get("min_arc_rounds_before_draft", 3))
    LOGS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    log_path = LOGS_DIR / f"arc_{stamp}.log"
    print(f"  [arc] log: {log_path}")

    topic = args.topic
    for i in range(args.max_rounds):
        posts_before = len(list(FORUM_DIR.glob("*.md")))
        rc = run_round(topic, log_path)
        topic = None  # only the first round opens the arc
        rnd = current_round(n_agents)
        if rc != 0:
            write_status(state="stopped", reason=f"run_forum exit {rc} at R{rnd}", rounds_run=i + 1)
            raise SystemExit(f"  [arc] STOP: run_forum exited {rc} at R{rnd}; see {log_path}")
        posts_after = len(list(FORUM_DIR.glob("*.md")))
        if posts_after < posts_before + n_agents:
            # A phantom round: run_forum returned 0 but the round is short of
            # posts (R30 incident: API failures swallowed inside run_agent).
            write_status(state="stopped",
                         reason=f"round advanced only {posts_after - posts_before}/{n_agents} posts at R{rnd}",
                         rounds_run=i + 1)
            raise SystemExit(
                f"  [arc] STOP: round produced {posts_after - posts_before}/{n_agents} posts "
                f"(R{rnd}); researcher attention needed; see {log_path}")
        state = critic_state(rnd, n_agents)
        if state["source"] is None:
            write_status(state="stopped", reason=f"no Critic post in R{rnd}", rounds_run=i + 1)
            raise SystemExit(f"  [arc] STOP: no Critic post in R{rnd} after retries; see {log_path}")
        arc_start = 1
        if ACTIVE_ARC_FILE.exists():
            try:
                arc_start = int(json.loads(ACTIVE_ARC_FILE.read_text()).get("start_round") or 1)
            except Exception:
                pass
        arc_rounds = rnd - arc_start + 1
        div = diversity_state(rnd)
        action, reason = decide(state, arc_rounds, min_rounds, div)
        print(f"  [arc] R{rnd}: verdict={state['verdict']} falsifier={state['falsifier_tested']} "
              f"diversity={div} arc_depth={arc_rounds} -> {action} ({reason})")
        commit_round(rnd, state["verdict"], push=not args.no_push)
        write_status(state="running" if action == "continue" else "stopped",
                     last_round=rnd, verdict=state["verdict"],
                     falsifier_tested=state["falsifier_tested"], diversity=div,
                     arc_depth=arc_rounds, action=action, reason=reason,
                     one_line=state.get("one_line"), rounds_run=i + 1)
        if action == "draft_and_stop":
            if args.no_draft:
                print("  [arc] completion reached; drafting skipped (--no-draft)")
            else:
                d = subprocess.run([sys.executable, str(BASE_DIR / "draft_article.py"),
                                    "--round", str(rnd)],
                                   cwd=str(BASE_DIR), capture_output=True, text=True, timeout=3600)
                print("  [arc] article drafted" if d.returncode == 0
                      else f"  [arc] draft failed ({d.returncode}): {d.stderr[:200]}")
                commit_round(rnd, "article", push=not args.no_push)
            print(f"  [arc] DONE: {reason}")
            return
        if action == "stop":
            print(f"  [arc] DONE: {reason}")
            return
    write_status(state="paused", reason=f"max rounds ({args.max_rounds}) reached", verdict=None)
    print(f"  [arc] PAUSED: max rounds ({args.max_rounds}) reached; researcher review requested")


if __name__ == "__main__":
    main()

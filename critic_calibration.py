#!/usr/bin/env python3
"""Critic calibration set with known fates (M22). Manual invocation only.

knowledge/critic_calibration/ holds frozen claim sheets (M16 format) for
rounds whose fate is known, plus positive controls checked in the data before
inclusion:

    sheets/<id>.md              one claim sheet per item, no verdict text
    items.jsonl                 {"id", "sheet", "fate", "source_round"}, where fate is
                                known_overturn, positive_control, exploratory or retreated
    researcher_labels.jsonl     {"id", "verdict", "labeled_at"}, the researcher's
                                blind verdicts, collected before the first run
    runs.jsonl                  one report row per calibration run
    critic_ratings.jsonl        optional end-of-arc ratings by the researcher. No
                                Claude pass may stand in for them

run() refuses to start without the researcher's labels for every item or
when any sheet contains verdict text. It prints the call count, asks for
confirmation, checks the launch gate, then makes one non-posting Critic call
per item with the verdict schema. It reports agreement with the researcher,
the pursue rate, false archive on positive controls and false pursue on
known overturns. About 12 items detect only gross shifts, and the report
says so.

Usage:
    python3 critic_calibration.py check                   # sheet and label audit, no calls
    python3 critic_calibration.py run [--label NAME] [--prompt-file PATH]
"""

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CAL_DIR = BASE_DIR / "knowledge" / "critic_calibration"
AGENTS_FILE = BASE_DIR / "agents.json"

FATES = ("known_overturn", "positive_control", "exploratory", "retreated")
VERDICT_TEXT_RE = re.compile(r"\b(?:pursue|revise|archive|verdict|verdict_effective)\b|"
                             r"\b(?:research_novelty|empirical_rigor|theoretical_connection|actionability)\s*:",
                             re.IGNORECASE)
GROSS_SHIFT_NOTE = ("About 12 items detect only gross shifts in Critic behavior. Differences of one "
                    "or two items are within noise.")
USER_MESSAGE = ("Evaluate the claim sheet in your instructions and return your verdict through "
                "the structured output. Do not write any file.")


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


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_items(cal_dir: Path | None = None) -> list[dict]:
    return _read_jsonl((cal_dir or CAL_DIR) / "items.jsonl")


def load_labels(cal_dir: Path | None = None) -> dict:
    return {r["id"]: r.get("verdict") for r in _read_jsonl((cal_dir or CAL_DIR) / "researcher_labels.jsonl")
            if r.get("id")}


def sheet_problems(cal_dir: Path | None = None) -> list[str]:
    """Items whose sheet is missing or contains verdict text or scores."""
    d = cal_dir or CAL_DIR
    out = []
    for it in load_items(d):
        p = d / "sheets" / (it.get("sheet") or f"{it['id']}.md")
        if not p.exists():
            out.append(f"{it['id']}: sheet {p.name} missing")
            continue
        for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            m = VERDICT_TEXT_RE.search(line)
            if m:
                out.append(f"{it['id']}: verdict text '{m.group(0)}' at {p.name}:{i}")
                break
        if it.get("fate") not in FATES:
            out.append(f"{it['id']}: fate must be one of {list(FATES)}")
    return out


def preflight(cal_dir: Path | None = None) -> list[str]:
    """Reasons the calibration may not start (empty when it may)."""
    d = cal_dir or CAL_DIR
    items = load_items(d)
    if not items:
        return [f"no items in {d.name}/items.jsonl"]
    problems = sheet_problems(d)
    if not (d / "researcher_labels.jsonl").exists():
        problems.append("researcher_labels.jsonl is missing: collect the researcher's blind verdicts first")
    else:
        labels = load_labels(d)
        missing = [it["id"] for it in items if labels.get(it["id"]) not in ("pursue", "revise", "archive")]
        if missing:
            problems.append(f"researcher labels missing or invalid for: {', '.join(missing)}")
    return problems


def score(verdicts: dict, items: list[dict], labels: dict) -> dict:
    """Agreement and error rates for {item id: Critic verdict}."""
    ids = [it["id"] for it in items if verdicts.get(it["id"])]
    n = len(ids)
    fate = {it["id"]: it.get("fate") for it in items}
    agree = sum(1 for i in ids if verdicts[i] == labels.get(i))
    pos = [i for i in ids if fate[i] == "positive_control"]
    over = [i for i in ids if fate[i] == "known_overturn"]
    counts = Counter(verdicts[i] for i in ids)
    return {
        "n": n,
        "agreement": agree / n if n else None,
        "pursue_rate": counts["pursue"] / n if n else None,
        "verdict_counts": dict(counts),
        "false_archive_positive_controls": (sum(1 for i in pos if verdicts[i] == "archive"), len(pos)),
        "false_pursue_known_overturns": (sum(1 for i in over if verdicts[i] == "pursue"), len(over)),
        "note": GROSS_SHIFT_NOTE,
    }


def critic_prompt(prompt_file: Path | None = None) -> str:
    if prompt_file:
        return Path(prompt_file).read_text(encoding="utf-8")
    agents = json.loads(AGENTS_FILE.read_text(encoding="utf-8")).get("agents", [])
    critic = next((a for a in agents if a.get("id") == "critic"), {})
    return critic.get("prompt", "")


def run(*, label: str = "current", prompt_file: Path | None = None, confirm=input,
        runner=None, cal_dir: Path | None = None) -> dict:
    """Manual calibration run. Returns the report row appended to runs.jsonl."""
    import claude_cli
    import verdict as vd
    d = cal_dir or CAL_DIR
    problems = preflight(d)
    if problems:
        raise SystemExit("[Calibration] refusing to start:\n  - " + "\n  - ".join(problems))
    items, labels = load_items(d), load_labels(d)
    print(f"[Calibration] {len(items)} items, {len(items)} non-posting Critic calls, prompt '{label}'.")
    print(f"[Calibration] {GROSS_SHIFT_NOTE}")
    if str(confirm("Type yes to run: ")).strip().lower() != "yes":
        raise SystemExit("[Calibration] not confirmed, nothing run")
    open_, reason, resume_at = claude_cli.launch_gate()
    if not open_:
        raise SystemExit(f"[Calibration] {reason} (resets {resume_at})")
    runner = runner or claude_cli.run_claude
    base = critic_prompt(prompt_file)
    schema = vd.load_schema()
    verdicts, calls = {}, []
    for it in items:
        sheet = (d / "sheets" / (it.get("sheet") or f"{it['id']}.md")).read_text(encoding="utf-8")
        prompt = f"{base}\n\n# Calibration claim sheet ({it['id']})\n\n{sheet}"
        res = runner("agent", prompt, role="critic", tools=[], schema=schema,
                     user_message=USER_MESSAGE)
        v = vd.normalize(getattr(res, "structured", None) or {}).get("verdict")
        verdicts[it["id"]] = v if v in vd.VERDICTS else None
        calls.append({"id": it["id"], "run_id": getattr(res, "run_id", None),
                      "failure": getattr(res, "failure", None), "verdict": verdicts[it["id"]]})
        if getattr(res, "failure", None) == "usage_limit":
            print("[Calibration] usage limit reached, stopping early")
            break
    report = {"ts": _now_iso(), "label": label, "prompt_file": str(prompt_file) if prompt_file else "agents.json critic",
              **score(verdicts, items, labels), "calls": calls}
    with open(d / "runs.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(report, ensure_ascii=False) + "\n")
    print(json.dumps({k: report[k] for k in ("n", "agreement", "pursue_rate",
                                             "false_archive_positive_controls",
                                             "false_pursue_known_overturns")}, indent=1))
    return report


def main() -> None:
    ap = argparse.ArgumentParser(description="Critic calibration (manual only)")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("check", help="Audit sheets and labels without calls")
    r = sub.add_parser("run", help="Run the calibration (asks for confirmation)")
    r.add_argument("--label", default="current")
    r.add_argument("--prompt-file", type=Path, default=None)
    args = ap.parse_args()
    if args.cmd == "check":
        problems = preflight()
        print("ready" if not problems else "\n".join(problems))
        sys.exit(0 if not problems else 1)
    if args.cmd == "run":
        run(label=args.label, prompt_file=args.prompt_file)
        return
    ap.print_help()


if __name__ == "__main__":
    main()

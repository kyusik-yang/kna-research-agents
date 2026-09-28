#!/usr/bin/env python3
"""Premise check for a topic-gate entry (M15; Stage 2, stage2.premise_check).

An arc's prior can rest on a premise that the data already contradict (Arc 5
assumed a first-term passage gap that did not exist). Before the gate entry
is signed, one non-posting call in the Analyst role computes only the
premise quantity and writes knowledge/premise_checks/<seed slug>.json with
the premise, value, interval, N, script and whether the premise holds. A
premise backed by a cited published table (premise_source with a DOI and a
table or page) stands in with no call.

check_topic_gate derives the result path from the seed with result_path(),
never from a path written in topic_gate.md, and uses gate_status() to decide.
A premise that fails blocks the entry unless the entry carries
premise_override.

Usage:
    python3 premise_check.py run --seed "<seed as in topic_gate.md>"
    python3 premise_check.py status --seed "<seed>"
"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
PREMISE_DIR = KNOWLEDGE_DIR / "premise_checks"
STAGING_ROOT = KNOWLEDGE_DIR / "staging"
TOPIC_GATE_FILE = BASE_DIR / "topic_gate.md"

TASK = "premise_check"
TOOLS = ["Bash", "Read", "Write"]
RESULT_NAME = "premise_check.json"
RESULT_FIELDS = ("premise", "value", "ci", "n", "script", "passes")
DOI_RE = re.compile(r"\b10\.\d{4,9}/\S+")

PROMPT = """You are the Data Analyst of the KNA research forum, running a premise check.
This is not a forum round. Do not write a forum post and do not edit anything in forum/ or knowledge/.

Compute exactly one quantity, the one the premise below is about, from the KNA data
(KBL_DATA) or the kr-hearings data in data/. Do not test the prior or the falsifier,
and do not explore other quantities.

Premise:
{premise}

Arc context (for definitions only):
seed: {seed}
identification: {identification}

Write your script under {staging_dir}/ and run it. Then write {result_path} as JSON with
exactly these keys:
  "premise": the premise text as given above,
  "value": the computed quantity (number, in the units the premise uses),
  "ci": [low, high] 95 percent interval, or null if none is defined,
  "n": the number of observations behind the value,
  "script": the path of the script you ran,
  "passes": true if the computed value is consistent with the premise as stated, false otherwise,
  "definition": one sentence stating exactly how the quantity was computed.
"""


def slug(seed: str) -> str:
    """Stable file stem for a seed: ascii words plus a short hash of the
    whitespace-normalized seed, so Korean-only seeds still get a unique name."""
    norm = re.sub(r"\s+", " ", (seed or "").strip().lower())
    words = re.sub(r"[^a-z0-9]+", "-", norm).strip("-")[:60].strip("-")
    h = hashlib.sha1(norm.encode("utf-8")).hexdigest()[:8]
    return f"{words}-{h}" if words else h


def result_path(seed: str, premise_dir: Path | None = None) -> Path:
    return (premise_dir or PREMISE_DIR) / f"{slug(seed)}.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def published_source(gate: dict) -> dict | None:
    """{"doi", "table"} when the gate cites a published table for the premise."""
    src = gate.get("premise_source")
    if not src:
        return None
    if isinstance(src, dict):
        doi, table = src.get("doi"), src.get("table") or src.get("page")
    else:
        m = DOI_RE.search(str(src))
        doi = m.group(0).rstrip(".,;)") if m else None
        t = re.search(r"\b(?:table|tab\.|page|p\.)\s*[\w.-]+", str(src), re.IGNORECASE)
        table = t.group(0) if t else None
    return {"doi": doi, "table": table} if doi and table else None


def _public(value):
    """Repo-relative form of any absolute path under the repository inside a
    stored value. The result file sits in knowledge/, which is committed, and
    the script path the agent reports is absolute."""
    root = str(BASE_DIR.resolve()).rstrip("/") + "/"
    if isinstance(value, str):
        return value.replace(root, "").replace(str(BASE_DIR).rstrip("/") + "/", "")
    if isinstance(value, list):
        return [_public(v) for v in value]
    if isinstance(value, dict):
        return {k: _public(v) for k, v in value.items()}
    return value


def _validate_result(res: dict) -> list[str]:
    errs = [f"missing '{k}'" for k in RESULT_FIELDS if k not in res]
    if "passes" in res and not isinstance(res["passes"], bool):
        errs.append("'passes' must be true or false")
    if "value" in res and not isinstance(res["value"], (int, float)):
        errs.append("'value' must be a number")
    return errs


def run(gate: dict, *, force: bool = False, runner=None, premise_dir: Path | None = None,
        staging_root: Path | None = None) -> dict:
    """Run (or record) the premise check for one gate entry and write the
    result file. Returns the stored record. Raises ValueError when the entry
    states no premise and FileExistsError when a result exists (force=True
    re-runs and keeps the old file as <stem>.rev<k>.json)."""
    seed, premise = gate.get("seed"), (gate.get("premise") or "").strip()
    if not seed:
        raise ValueError("gate entry has no seed")
    if not premise:
        raise ValueError("gate entry states no premise; a premise check runs only on a stated premise")
    out = result_path(seed, premise_dir)
    if out.exists() and not force:
        raise FileExistsError(f"{out.name} exists; pass force=True to re-run")
    # auto_arc.py runs this check before it signs an entry, whether or not
    # stage2.premise_check is on (that flag only decides whether
    # check_topic_gate reads the result).
    record = {"seed": seed, "premise": premise, "ts": _now_iso(),
              "drafted_by": gate.get("drafted_by", "unrecorded"),
              "signed_by": gate.get("signed_by", "unrecorded")}
    src = published_source(gate)
    if src:
        record.update(source="published", premise_source=src, value=None, ci=None, n=None,
                      script=None, passes=gate.get("premise_holds", True) is not False,
                      note="premise backed by a cited published table; no call made")
    else:
        import claude_cli
        runner = runner or claude_cli.run_claude
        run_id = claude_cli.new_run_id("premise_check")
        stage = (staging_root or STAGING_ROOT) / run_id
        stage.mkdir(parents=True, exist_ok=True)
        res_file = stage / RESULT_NAME
        prompt = PROMPT.format(premise=premise, seed=seed,
                               identification=gate.get("identification", "(not given)"),
                               staging_dir=stage, result_path=res_file)
        call = runner(TASK, prompt, role="data_analyst", tools=list(TOOLS), expect_file=res_file,
                      extra_env={"KNA_RUN_ID": run_id, "KNA_STAGING_DIR": str(stage)},
                      user_message="Compute the premise quantity and write the result file now.")
        record.update(source="computed", run_id=getattr(call, "run_id", run_id),
                      call_ok=bool(getattr(call, "ok", False)),
                      failure=getattr(call, "failure", None))
        try:
            res = json.loads(res_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            res = {}
        errs = _validate_result(res) if res else ["no result file written"]
        record.update({k: _public(res.get(k)) for k in (*RESULT_FIELDS, "definition")})
        record["premise"] = premise
        record["errors"] = errs
        if errs:
            record["passes"] = None
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        k = 1
        while out.with_name(f"{out.stem}.rev{k}.json").exists():
            k += 1
        out.rename(out.with_name(f"{out.stem}.rev{k}.json"))
    out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  [Premise] {out.name}: passes={record.get('passes')} ({record['source']})")
    return record


def gate_status(gate: dict, premise_dir: Path | None = None) -> dict:
    """What check_topic_gate should do with the entry's premise.
    status: 'no_premise' (warn), 'missing' (no result yet, warn),
    'pass', 'override' (failed but premise_override present, pass with note),
    'fail' (block), 'error' (the check did not produce a usable result, warn)."""
    if not (gate.get("premise") or "").strip():
        return {"status": "no_premise", "block": False, "path": None}
    path = result_path(gate.get("seed", ""), premise_dir)
    try:
        rec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"status": "missing", "block": False, "path": str(path)}
    rel = path.name
    if rec.get("passes") is True:
        return {"status": "pass", "block": False, "path": rel, "record": rec}
    if rec.get("passes") is None:
        return {"status": "error", "block": False, "path": rel, "record": rec}
    if (gate.get("premise_override") or "").strip():
        return {"status": "override", "block": False, "path": rel, "record": rec,
                "override": gate["premise_override"]}
    return {"status": "fail", "block": True, "path": rel, "record": rec}


def find_gate_entry(seed: str, gate_file: Path | None = None) -> dict:
    """The topic_gate.md H2 entry whose seed matches (substring either way),
    parsed into every 'key: value' field it carries."""
    raw = (gate_file or TOPIC_GATE_FILE).read_text(encoding="utf-8")
    want = re.sub(r"\s+", " ", seed.strip().lower())
    for entry in re.split(r"\n## ", raw):
        m = re.search(r"^seed:\s*(.+)$", entry, re.MULTILINE | re.IGNORECASE)
        if not m:
            continue
        have = re.sub(r"\s+", " ", m.group(1).strip().lower())
        if have in want or want in have:
            fields = {}
            for fm in re.finditer(r"^([a-z_]+):\s*(.*?)(?=^[a-z_]+:\s|\Z)", entry,
                                  re.MULTILINE | re.DOTALL):
                fields[fm.group(1)] = re.sub(r"\s+", " ", fm.group(2)).strip()
            return fields
    raise KeyError(f"no topic_gate.md entry matches seed {seed[:60]!r}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Premise check for a topic-gate entry (Stage 2)")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("run", help="Compute (one non-posting call) or record the premise check")
    r.add_argument("--seed", required=True)
    r.add_argument("--force", action="store_true")
    s = sub.add_parser("status", help="Show what the topic gate would do with the premise")
    s.add_argument("--seed", required=True)
    args = ap.parse_args()
    if args.cmd not in ("run", "status"):
        ap.print_help()
        sys.exit(1)
    gate = find_gate_entry(args.seed)
    if args.cmd == "run":
        print(json.dumps(run(gate, force=args.force), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(gate_status(gate), ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()

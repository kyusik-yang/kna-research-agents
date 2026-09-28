#!/usr/bin/env python3
"""Scripted claim sheet for the Critic (M16; Stage 2, stage2.claim_sheet_first).

build(round_num) writes workspace/rNN/claim_sheet.md from files only: the
arc's gate entry, the committed prediction card, the precheck table, every
results file value with N, interval, sample flow and paths, the Analyst run's
containment report, the Analyst's 'Private Evidence' section and the Scout's
unverified citations. It carries no Scout or Analyst narrative, no ledger
verdicts, no earlier verdicts and no taxonomy numbers, so the Critic can form
a provisional verdict before reading the Analyst post.

order_check() and provisional_shift() audit the Critic's trace afterwards.
The provisional verdict (workspace/rNN/critic_provisional.json) must be
written before the first Read, Grep or Bash call touching the Analyst post
or the Analyst's scripts, and a verdict or score that moves after reading
must be backed by a check executed after reading. verdict.record() applies
both when the flag is on.

Usage:
    python3 claim_sheet.py build --round N      # write and print the sheet
"""

import argparse
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
FORUM_DIR = BASE_DIR / "forum"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
WORKSPACE_DIR = BASE_DIR / "workspace"
LOGS_DIR = BASE_DIR / "logs"
ACTIVE_ARC_FILE = KNOWLEDGE_DIR / "active_arc.json"

PROVISIONAL_NAME = "critic_provisional.json"
SCRIPT_EXT = (".py", ".R", ".r", ".sh", ".do")
GATE_KEYS = ("seed", "prior", "falsifier", "decision_rule", "decision_rule_expr", "sesoi",
             "null_paper", "premise", "identification", "drafted_by", "signed_by", "start_round")
RESULT_KEYS = ("estimate", "se", "ci_low", "ci_high", "n", "mde", "equivalence_margin", "tost_p")
EXCLUSION_RE = re.compile(r"\((?:X)?(\d+)\)\s*(.*?)(?=\s*\((?:X)?\d+\)\s|\Z)", re.DOTALL)
READ_CMD_RE = re.compile(r"\b(?:cat|head|tail|less|more|grep|rg|sed|awk|wc|diff|open)\b|python3?\b")
EXEC_RE = re.compile(r"\b(?:python3?|Rscript|bash|sh|uv run)\b\s+\S*\.(?:py|R|sh)\b")


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------

def _read_json(path: Path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _round_post(round_num: int, role: str) -> Path | None:
    try:
        import forum_index
        for p in forum_index.round_posts(round_num, forum_dir=FORUM_DIR):
            if role in p.name:
                return p
    except Exception:
        pass
    n = {"literature_scout": 1, "data_analyst": 2, "critic": 3}.get(role)
    if n is None:
        return None
    hits = sorted(FORUM_DIR.glob(f"{(round_num - 1) * 3 + n:03d}_{role}.md"))
    return hits[0] if hits else None


def private_evidence(post_text: str) -> str:
    """The body of the Analyst's '## ... Private Evidence' section, verbatim,
    or '' when the post has none."""
    m = re.search(r"^#{2,3}\s+(?:\d+\.\s*)?Private Evidence[^\n]*\n(.*?)(?=^#{1,3}\s|\Z)",
                  post_text or "", re.MULTILINE | re.DOTALL | re.IGNORECASE)
    return m.group(1).strip() if m else ""


def exclusion_items(text: str) -> list[tuple[str, str]]:
    """[(id, text)] for '(1) ...' or '(X1) ...' items, without truncation."""
    return [(f"X{m.group(1)}", re.sub(r"\s+", " ", m.group(2)).strip())
            for m in EXCLUSION_RE.finditer(text or "")]


def _containment(round_num: int, role: str = "data_analyst") -> dict | None:
    for d in (LOGS_DIR / f"r{int(round_num):02d}", LOGS_DIR / f"r{int(round_num)}"):
        for p in sorted(d.glob("*.sidecar.json")) if d.exists() else []:
            sc = _read_json(p)
            if sc.get("role") == role and sc.get("containment") is not None:
                return sc["containment"]
    return None


def analyst_scripts(round_num: int, results: dict | None = None) -> list[str]:
    """Script names of the Analyst's round: files under workspace/rNN/ plus
    every results file's script field (basenames, de-duplicated)."""
    names = []
    d = WORKSPACE_DIR / f"r{int(round_num)}"
    for p in sorted(d.rglob("*")) if d.exists() else []:
        if p.suffix in SCRIPT_EXT:
            names.append(p.name)
    if results is None:
        import prediction_card as pc
        results = pc.load_results(round_num)
    for res in (results or {}).values():
        if res.get("script"):
            names.append(Path(str(res["script"])).name)
    seen, out = set(), []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def _fmt(v) -> str:
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def _gate_section(gate: dict) -> list[str]:
    out = ["## Gate entry", ""]
    if not gate:
        return out + ["No active gate entry.", ""]
    for k in GATE_KEYS:
        if gate.get(k) not in (None, ""):
            out.append(f"- {k}: {gate[k]}")
    if "drafted_by" not in gate:
        out.append("- drafted_by: unrecorded")
    if "signed_by" not in gate:
        out.append("- signed_by: unrecorded")
    items = exclusion_items(gate.get("exclusion_criteria", ""))
    if items:
        out += ["", "Exclusions (verbatim, with ids):"]
        out += [f"- ({i}) {t}" for i, t in items]
    elif gate.get("exclusion_criteria"):
        out += ["", f"Exclusions: {gate['exclusion_criteria']}"]
    return out + [""]


def _card_section(round_num: int, card: dict | None, meta: dict | None) -> list[str]:
    out = ["## Committed card", ""]
    if not card:
        return out + [f"No card committed for R{round_num}.", ""]
    m = meta or {}
    out.append(f"R{int(round_num):02d}, sha256 {str(m.get('sha256') or '-')[:16]}, "
               f"committed {m.get('committed_at') or '-'}, data_exposed {m.get('data_exposed')}")
    out += ["", "```json", json.dumps(card, ensure_ascii=False, indent=2), "```", ""]
    return out


def _precheck_section(pre: dict) -> list[str]:
    out = ["## Prechecks", ""]
    posts = (pre or {}).get("posts") or {}
    if not posts:
        return out + ["No precheck results for this round.", ""]
    out += ["| Post | Rule | Status | Flagged items |", "|---|---|---|---|"]
    for name, post in sorted(posts.items()):
        for r in post.get("rules") or []:
            n = sum(1 for x in r.get("details") or [] if x.get("flag"))
            out.append(f"| {name} | {r.get('id')} {r.get('name', '')} | {r.get('status')} | {n} |")
    return out + [""]


def _results_section(card: dict | None, results: dict) -> list[str]:
    out = ["## Results files", ""]
    if not results:
        return out + ["No results files.", ""]
    roles = {s.get("spec_id"): s.get("role") for s in (card or {}).get("spec_plan") or []}
    out += ["| Spec | Role | Quantity | " + " | ".join(RESULT_KEYS) + " | Script | Output |",
            "|---|---|---|" + "---|" * len(RESULT_KEYS) + "---|---|"]
    flows = []
    for sid in sorted(results):
        res = results[sid]
        role = roles.get(sid) or ("exploratory" if sid.startswith("x_") else "not on card")
        if str(res.get("status", "")).lower() == "not_computable":
            vals = ["NOT COMPUTABLE: " + str(res.get("missing_variable") or "reason not given")] + \
                   ["-"] * (len(RESULT_KEYS) - 1)
        else:
            vals = [_fmt(res.get(k)) for k in RESULT_KEYS]
        out.append(f"| {sid} | {role} | {res.get('quantity_id') or '-'} | " + " | ".join(vals) +
                   f" | {res.get('script') or '-'} | {res.get('output') or '-'} |")
        if res.get("n_by_filter_step"):
            flows.append(f"- {sid}: {json.dumps(res['n_by_filter_step'], ensure_ascii=False)}")
    if flows:
        out += ["", "Sample flow (n_by_filter_step):"] + flows
    return out + [""]


def _containment_section(cont: dict | None) -> list[str]:
    out = ["## Containment (Analyst run)", ""]
    if cont is None:
        return out + ["No containment report recorded.", ""]
    viol = cont.get("violations") or []
    ext = cont.get("external_writes") or []
    out.append(f"Violations: {len(viol)}. External writes: {len(ext)}.")
    out += [f"- violation: {json.dumps(v, ensure_ascii=False)}" for v in viol[:20]]
    out += [f"- external write: {json.dumps(e, ensure_ascii=False)}" for e in ext[:20]]
    return out + [""]


def _unverified_citations(pre: dict, scout_name: str | None) -> list[str]:
    out = ["## Scout citations not verified by script", ""]
    post = ((pre or {}).get("posts") or {}).get(scout_name or "", {})
    items = []
    for r in post.get("rules") or []:
        if r.get("id") not in ("R-05", "R-11"):
            continue
        for x in r.get("details") or []:
            if x.get("flag"):
                items.append(f"- {r['id']}: {x.get('doi', '-')} ({x.get('result', '')})")
    return out + (items or ["None flagged."]) + [""]


def build(round_num: int, *, gate: dict | None = None, card: dict | None = None,
          card_meta: dict | None = None, results: dict | None = None,
          prechecks: dict | None = None, analyst_post: Path | None = None,
          scout_post: Path | None = None, containment: dict | None = None,
          write: bool = True, out_path: Path | None = None) -> str:
    """Build the round's claim sheet and (write=True) save it to
    workspace/rNN/claim_sheet.md. Every argument defaults to the file the
    orchestrator keeps for it."""
    import prediction_card as pc
    gate = gate if gate is not None else _read_json(ACTIVE_ARC_FILE)
    card = card if card is not None else pc.load_cards().get(int(round_num))
    if card_meta is None:
        card_meta = pc.card_meta().get(int(round_num)) or {}
        if card and not card_meta.get("sha256"):
            card_meta = {**card_meta, "sha256": pc.card_sha(card)}
    results = results if results is not None else pc.load_results(round_num)
    prechecks = prechecks if prechecks is not None else \
        _read_json(KNOWLEDGE_DIR / "prechecks" / f"R{int(round_num):02d}.json")
    analyst_post = analyst_post or _round_post(round_num, "data_analyst")
    scout_post = scout_post or _round_post(round_num, "literature_scout")
    containment = containment if containment is not None else _containment(round_num)
    lines = [f"# Claim sheet R{int(round_num):02d}", "",
             "Built by the orchestrator from files. It holds no Scout or Analyst narrative, no "
             "ledger verdicts, no earlier verdicts and no taxonomy numbers. Write "
             f"workspace/r{int(round_num)}/{PROVISIONAL_NAME} before opening the Analyst post "
             "or the Analyst's scripts.", ""]
    lines += _gate_section(gate)
    lines += _card_section(round_num, card, card_meta)
    lines += _precheck_section(prechecks)
    lines += _results_section(card, results)
    lines += _containment_section(containment)
    pe = private_evidence(Path(analyst_post).read_text(encoding="utf-8")) \
        if analyst_post and Path(analyst_post).exists() else ""
    lines += ["## Analyst Private Evidence (verbatim)", "", pe or "The Analyst post has no Private Evidence section.", ""]
    lines += _unverified_citations(prechecks, Path(scout_post).name if scout_post else None)
    text = "\n".join(lines).rstrip() + "\n"
    if write:
        path = out_path or WORKSPACE_DIR / f"r{int(round_num)}" / "claim_sheet.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return text


# --------------------------------------------------------------------------
# Trace audit
# --------------------------------------------------------------------------

def _touches(call: dict, names: list[str]) -> bool:
    inp = call.get("input") or {}
    name = call.get("name")
    if name in ("Read", "Grep", "Glob", "Edit", "NotebookRead"):
        blob = " ".join(str(inp.get(k, "")) for k in ("file_path", "path", "pattern", "glob"))
        return any(n in blob for n in names)
    if name == "Bash":
        cmd = str(inp.get("command", ""))
        return any(n in cmd for n in names) and bool(READ_CMD_RE.search(cmd) or EXEC_RE.search(cmd))
    return False


def _writes_provisional(call: dict) -> bool:
    inp = call.get("input") or {}
    if call.get("name") in ("Write", "Edit"):
        return str(inp.get("file_path", "")).endswith(PROVISIONAL_NAME)
    if call.get("name") == "Bash":
        cmd = str(inp.get("command", ""))
        return PROVISIONAL_NAME in cmd and bool(re.search(r">|\btee\b|json\.dump|write_text", cmd))
    return False


def order_check(events: list[dict], *, analyst_post_name: str | None,
                analyst_scripts: list[str] | None = None) -> dict:
    """Did the Critic write the provisional verdict before touching the
    Analyst post or the Analyst's scripts? Returns {"respected",
    "provisional_idx", "first_touch_idx", "first_touch", "checks_before_reading"}
    with tool-call indices into the trace."""
    from prechecks import tool_calls
    calls = tool_calls(events)
    names = [n for n in [analyst_post_name, *(analyst_scripts or [])] if n]
    prov = next((c["idx"] for c in calls if _writes_provisional(c)), None)
    touch = next((c for c in calls if names and _touches(c, names)), None)
    first = touch["idx"] if touch else None
    before = first if first is not None else len(calls)
    checks = [str(c["input"].get("command", ""))[:160] for c in calls[:before]
              if c["name"] == "Bash" and EXEC_RE.search(str(c["input"].get("command", "")))]
    respected = prov is not None and (first is None or prov < first)
    return {"respected": respected, "provisional_idx": prov, "first_touch_idx": first,
            "first_touch": ({"name": touch["name"], "input": {k: str(v)[:160] for k, v in
                                                              (touch.get("input") or {}).items()}}
                            if touch else None),
            "checks_before_reading": checks}


def provisional_shift(provisional: dict, final: dict, events: list[dict],
                      first_touch_idx: int | None) -> dict:
    """Compare the provisional and final verdicts. A move counts as backed
    when a script was executed after the first touch of the Analyst's work
    (or after the provisional write when there was no touch)."""
    from prechecks import tool_calls
    import verdict as vd
    p, f = vd.normalize(provisional or {}), vd.normalize(final or {})
    moved = [k for k in ("verdict", *vd.SCORE_FIELDS) if k in p and k in f and p[k] != f[k]]
    calls = tool_calls(events)
    start = first_touch_idx
    if start is None:
        start = next((c["idx"] for c in calls if _writes_provisional(c)), -1)
    after = [c for c in calls if c["idx"] > start and c["name"] == "Bash"
             and EXEC_RE.search(str(c["input"].get("command", "")))]
    rank = {"archive": 0, "revise": 1, "pursue": 2}
    direction = None
    if "verdict" in moved:
        direction = "up" if rank.get(f["verdict"], 1) > rank.get(p["verdict"], 1) else "down"
    elif moved:
        direction = "up" if sum(f[k] - p[k] for k in moved if k != "verdict") > 0 else "down"
    return {"moved": bool(moved), "fields_moved": moved,
            "from": {k: p.get(k) for k in moved}, "to": {k: f.get(k) for k in moved},
            "direction": direction, "check_after_reading": bool(after),
            "checks_after_reading": [str(c["input"].get("command", ""))[:160] for c in after[:5]]}


def main() -> None:
    ap = argparse.ArgumentParser(description="Claim sheet for the Critic (Stage 2)")
    sub = ap.add_subparsers(dest="cmd")
    b = sub.add_parser("build", help="Write workspace/rNN/claim_sheet.md")
    b.add_argument("--round", type=int, required=True)
    b.add_argument("--no-write", action="store_true")
    args = ap.parse_args()
    if args.cmd == "build":
        print(build(args.round, write=not args.no_write))
    else:
        ap.print_help()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
AI-use disclosure from logs (v2.1, M21, Stage 2 flag stage2.disclosure_appendix)
===============================================================================
Papers carried a one-line AI notice written by the drafting model. The AJPS
policy (updated 2026-08-11) asks for one consolidated footnote naming every
tool with its version, the approximate dates of use and the degree of human
oversight. A model asked to describe its own process makes things up, so this
module builds the disclosure from records only:

  - the M01 sidecars (logs/rNN/*.sidecar.json): role, model, CLI version,
    effort, turns, attempts, failure class, date
  - a static reconstruction for Arcs 4 and 5 (Season 2 ran before sidecars
    existed, so model and CLI version were read from the session transcripts
    on 2026-09-24), marked as reconstructed wherever it is used
  - the topic-gate entry's drafted_by and signed_by fields (D-10)
  - knowledge/arc_status.json (overrides such as --override-gates, --force,
    --bypass-topic-gate, --allow-model-change) and comment posts, listed as
    recorded overrides with an actor only where one was recorded, because the
    orchestrating Claude session can pass these flags too (D-09, D-10)
  - knowledge/verdicts.jsonl (verdict overrides) and knowledge/retreats.jsonl
    (archived or retreated findings, with ledger line ids)
  - git log of topic_gate.md (commit author, time, Claude co-author line)

The researcher's private rationale is never included (D-19 default). The
output is <stem>.disclosure.tex (footnote and appendix) and
<stem>.disclosure.json (the same rows for the articles page). leak_lint runs
on the tex before it is returned.

Usage:
    python3 disclosure.py --round 30 --stem 2026-08-24_r30 [--out DIR]
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
TOPIC_GATE = BASE_DIR / "topic_gate.md"

RECONSTRUCTED_NOTE = "reconstructed from session transcripts read on 2026-09-24"
# Season 2 Arcs 4 and 5 ran before the wrapper recorded provenance.
LEGACY_PROVENANCE = {
    "rounds": range(25, 31),
    "model": "claude-fable-5",
    "cli_version": "2.1.241",
}
# D-10 retro-annotation of the Arc 4 (R25) and Arc 5 (R28) gate entries.
LEGACY_GATE_PROVENANCE = {
    4: {"drafted_by": "orchestrating Claude session (claude-fable-5)",
        "signed_by": "researcher, selected from a Claude-drafted menu on 2026-08-24"},
    5: {"drafted_by": "orchestrating Claude session (claude-fable-5)",
        "signed_by": "researcher, selected from a Claude-drafted menu on 2026-08-24"},
}
ROLE_TASKS = {
    "literature_scout": "literature search and question framing",
    "data_analyst": "data analysis and estimation",
    "critic": "critique and verdicts",
    "drafter": "drafting the paper and its figure scripts",
}
# draft_article's wrapper tasks, shown as one drafting role.
DRAFT_TASKS = {"draft_body": "drafter", "draft_fix": "drafter", "figures": "drafter"}
ARC_STATUS_ACTIONS = {
    "override_gates": "--override-gates (publish despite failed paper gates)",
    "force": "--force (draft before the arc-depth rule allows)",
    "bypass_topic_gate": "--bypass-topic-gate",
    "allow_model_change": "--allow-model-change",
    "manual_rerun": "manual rerun",
}


def legacy_provenance(round_num: int) -> dict | None:
    """Static provenance for Season 2 rounds that predate the sidecars."""
    if round_num in LEGACY_PROVENANCE["rounds"]:
        return {"source": RECONSTRUCTED_NOTE, "model": LEGACY_PROVENANCE["model"],
                "cli_version": LEGACY_PROVENANCE["cli_version"]}
    return None


def tex_escape(s) -> str:
    s = "" if s is None else str(s)
    repl = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
            "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(repl.get(c, c) for c in s)


def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _read_jsonl(p: Path) -> list[tuple[int, dict]]:
    out = []
    try:
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                try:
                    out.append((n, json.loads(line)))
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return out


# ---------------------------------------------------------------------------
# Collect
# ---------------------------------------------------------------------------

def sidecar_rows(rounds: list[int], logs_dir: Path | None = None) -> list[dict]:
    rows = []
    d = logs_dir or LOGS_DIR
    for r in rounds:
        for sc in sorted((d / f"r{r:02d}").glob("*.sidecar.json")):
            data = _read_json(sc)
            if not data:
                continue
            task = data.get("task")
            role = data.get("role") if task == "agent" else DRAFT_TASKS.get(task, task or "helper")
            attempts = data.get("attempts") or []
            rows.append({
                "round": r, "date": str(data.get("created") or "")[:10], "role": role,
                "model": data.get("model") or data.get("requested_model"),
                "cli_version": data.get("cli_version"), "effort": data.get("effort"),
                "turns": data.get("num_turns"), "attempts": len(attempts),
                "outcome": data.get("failure") or "unknown", "source": "sidecar",
            })
    return rows


def reconstructed_rows(rounds: list[int], forum_dir: Path | None = None) -> list[dict]:
    """One row per round and role for rounds without sidecars, from the
    posts (date from the frontmatter) and the static provenance table."""
    import forum_index  # noqa: E402
    rows = []
    metas = forum_index.index(forum_dir=forum_dir) if forum_dir else forum_index.index()
    for m in metas:
        if m["round"] not in rounds or m["role"] not in forum_index.ROLE_ORDER:
            continue
        prov = legacy_provenance(m["round"]) or {}
        fm = forum_index.read_frontmatter(m["path"])
        rows.append({
            "round": m["round"], "date": str(fm.get("date") or "")[:10], "role": m["role"],
            "model": prov.get("model"), "cli_version": prov.get("cli_version"), "effort": None,
            "turns": None, "attempts": None, "outcome": "posted",
            "source": "reconstructed" if prov else "unrecorded",
        })
    return rows


def gate_provenance(arc, start_round: int | None, topic_gate: Path | None = None) -> dict:
    """drafted_by and signed_by of the arc's topic-gate entry ("unrecorded"
    when the entry predates D-10 and no static annotation exists)."""
    out = {"drafted_by": "unrecorded", "signed_by": "unrecorded", "signed": None}
    text = ""
    try:
        text = (topic_gate or TOPIC_GATE).read_text(encoding="utf-8")
    except OSError:
        pass
    if start_round is not None and text:
        m = re.search(rf"^## R{start_round}\b.*?(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
        if m:
            for key in ("drafted_by", "signed_by", "signed"):
                km = re.search(rf"^{key}:\s*(.+)$", m.group(0), re.MULTILINE)
                if km:
                    out[key] = km.group(1).strip()
    try:
        legacy = LEGACY_GATE_PROVENANCE.get(int(arc))
    except (TypeError, ValueError):
        legacy = None
    if legacy:
        for k, v in legacy.items():
            if out[k] == "unrecorded":
                out[k] = v
    return out


def gate_commits(since: str | None, until: str | None) -> list[dict]:
    """Commits that touched topic_gate.md in the arc's date span (read-only git)."""
    if not since:
        return []
    fmt = "%h%x1f%an%x1f%aI%x1f%B%x1e"
    cmd = ["git", "log", f"--format={fmt}", f"--since={since} 00:00", "--", "topic_gate.md"]
    if until:
        cmd.insert(3, f"--until={until} 23:59")
    try:
        out = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    commits = []
    for rec in out.split("\x1e"):
        parts = rec.strip().split("\x1f")
        if len(parts) < 4:
            continue
        commits.append({"commit": parts[0], "author": parts[1], "time": parts[2],
                        "claude_coauthor": bool(re.search(r"Co-Authored-By:\s*Claude", parts[3], re.I))})
    return commits


def _actor(by) -> str:
    return f"by {by}" if by else "actor not recorded"


def recorded_overrides(arc_status: dict | None, rounds: list[int], forum_dir: Path | None = None) -> list[str]:
    """Overrides in arc_status.json and comment posts in the arc's rounds.
    Nothing here is labeled a human action. The orchestrating Claude session
    runs run_arc and run_forum and can pass the same flags, so an actor is
    named only when the record holds one (a dict value or entry with "by")."""
    actions = []
    st = arc_status or {}
    for key, label in ARC_STATUS_ACTIONS.items():
        val = st.get(key)
        if not val:
            continue
        if isinstance(val, dict):
            when, by = val.get("ts"), val.get("by")
        else:
            when, by = (val if isinstance(val, str) else None), None
        actions.append(f"{label} ({', '.join(x for x in (when, _actor(by)) if x)})")
    for entry in st.get("human_actions") or []:
        if isinstance(entry, dict):
            text = " ".join(str(entry.get(k)) for k in ("action", "ts") if entry.get(k))
            if text:
                actions.append(f"{text} ({_actor(entry.get('by'))})")
        elif entry:
            actions.append(f"{entry} ({_actor(None)})")
    import forum_index  # noqa: E402
    metas = forum_index.index(forum_dir=forum_dir) if forum_dir else forum_index.index()
    for m in metas:
        if m["round"] in rounds and m["role"] not in forum_index.ROLE_ORDER:
            fm = forum_index.read_frontmatter(m["path"])
            author = str(fm.get("author") or "").strip()
            who = f"author recorded as {author}" if author else "author not recorded"
            actions.append(f"comment post {m['path'].name} ({str(fm.get('date') or '')[:10]}, {who})")
    return actions


def ledger_items(rounds: list[int], knowledge_dir: Path | None = None) -> dict:
    kd = knowledge_dir or KNOWLEDGE_DIR
    retreats = []
    for n, r in _read_jsonl(kd / "retreats.jsonl"):
        rnd = r.get("overturning_round") or r.get("originating_round")
        if rnd in rounds:
            retreats.append({"id": f"retreats.jsonl:{n}", "round": rnd,
                             "change": f"{r.get('from_status')} to {r.get('to_status')}",
                             "finding": str(r.get("finding") or "")[:160]})
    overrides = []
    for n, v in _read_jsonl(kd / "verdicts.jsonl"):
        if v.get("round") in rounds and (v.get("overrides") or v.get("mismatch")):
            overrides.append({"id": f"verdicts.jsonl:{n}", "round": v.get("round"),
                              "verdict": v.get("verdict"),
                              "overrides": v.get("overrides") or v.get("mismatch")})
    return {"retreats": retreats, "verdict_overrides": overrides}


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def _span(rows: list[dict]) -> tuple[str | None, str | None]:
    dates = sorted(r["date"] for r in rows if r.get("date"))
    return (dates[0], dates[-1]) if dates else (None, None)


def footnote_text(data: dict) -> str:
    rows = data["rows"]
    models = sorted({r["model"] for r in rows if r.get("model")})
    clis = sorted({r["cli_version"] for r in rows if r.get("cli_version")})
    roles = [r for r in ROLE_TASKS if any(x["role"] == r for x in rows)]
    first, last = _span(rows)
    gp = data["gate"]
    parts = [
        "AI-use disclosure. This paper was produced by AI research agents running Claude Code "
        f"(CLI version{'s' if len(clis) > 1 else ''} {', '.join(clis) or 'unrecorded'}) with the "
        f"model{'s' if len(models) > 1 else ''} {', '.join(models) or 'unrecorded'}"
        + ((f", on {first}" if first == last else f", between {first} and {last}") if first else "") + ".",
        "Tasks performed by AI: " + "; ".join(ROLE_TASKS[r] for r in roles) + "." if roles else "",
        f"The arc's prior and falsifier were drafted by {gp['drafted_by']} and signed by {gp['signed_by']}.",
        ("Papers from this arc predate the automated publication checks." if data["reconstructed"] else
         "Under the forum's publishing rule, a draft is published after automated checks only "
         "(citation, reference, overclaim and path gates), without a human review of the text."),
    ]
    if data["recorded_overrides"]:
        parts.append("Recorded overrides and comment posts: " + "; ".join(data["recorded_overrides"]) + ".")
    if data["reconstructed"]:
        parts.append(f"Model and CLI versions for this arc are {RECONSTRUCTED_NOTE}.")
    parts.append("Appendix Table~\\ref{tab:ai-use} lists every agent run.")
    return " ".join(p for p in parts if p)


def render_tex(data: dict) -> str:
    fn = footnote_text(data)
    # Escape everything except the \ref we add at the end.
    fn_tex = tex_escape(fn.replace("Appendix Table~\\ref{tab:ai-use}", "@@REF@@"))
    fn_tex = fn_tex.replace("@@REF@@", "Appendix Table~\\ref{tab:ai-use}")
    lines = [
        "% Generated by disclosure.py from logs and ledgers. Do not edit by hand.",
        "\\let\\thefootnote\\relax\\footnotetext{" + fn_tex + "}",
        "",
        "\\clearpage",
        "\\appendix",
        "\\section*{Appendix: AI Use and Oversight}",
        "\\begin{table}[H]",
        "\\centering\\footnotesize",
        "\\caption{Agent runs behind this paper}",
        "\\label{tab:ai-use}",
        "\\begin{tabular}{rllllrrl}",
        "\\toprule",
        "Round & Date & Role & Model & CLI & Turns & Attempts & Outcome \\\\",
        "\\midrule",
    ]
    for r in data["rows"]:
        cells = [r["round"], r.get("date") or "", r["role"], r.get("model") or "unrecorded",
                 r.get("cli_version") or "unrecorded",
                 "" if r.get("turns") is None else r["turns"],
                 "" if r.get("attempts") is None else r["attempts"], r.get("outcome") or ""]
        lines.append(" & ".join(tex_escape(c) for c in cells) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    if data["reconstructed"]:
        lines.append(f"\\par\\smallskip Model and CLI version {tex_escape(RECONSTRUCTED_NOTE)}. "
                     "Effort, turns and attempts were not recorded for these rounds.")
    lines.append("\\end{table}")
    if data["ledger"]["retreats"] or data["ledger"]["verdict_overrides"]:
        lines += ["", "\\noindent\\textbf{Archived or retreated findings.}", "\\begin{itemize}"]
        for x in data["ledger"]["retreats"]:
            lines.append(f"\\item {tex_escape(x['id'])} (R{x['round']}, {tex_escape(x['change'])}): "
                         f"{tex_escape(x['finding'])}")
        for x in data["ledger"]["verdict_overrides"]:
            lines.append(f"\\item {tex_escape(x['id'])} (R{x['round']}): verdict of record "
                         f"{tex_escape(x['verdict'])} after a scripted override")
        lines.append("\\end{itemize}")
    if data["gate_commits"]:
        lines += ["", "\\noindent\\textbf{Topic-gate commits.} " + "; ".join(
            f"{tex_escape(c['commit'])} by {tex_escape(c['author'])} at {tex_escape(c['time'])}"
            + (" (with a Claude co-author line)" if c["claude_coauthor"] else "")
            for c in data["gate_commits"]) + "."]
    return "\n".join(lines) + "\n"


def build(round_num: int, stem: str, *, arc=None, rounds: list[int] | None = None,
          out_dir: Path | None = None, logs_dir: Path | None = None,
          knowledge_dir: Path | None = None, forum_dir: Path | None = None,
          topic_gate: Path | None = None, write: bool = True) -> dict:
    """Build the disclosure for the paper drafted from round_num. Returns
    {"tex", "json", "footnote", "leak_hits", "paths"}."""
    import forum_index  # noqa: E402
    import leak_lint  # noqa: E402
    kd = knowledge_dir or KNOWLEDGE_DIR
    if arc is None:
        metas = forum_index.index(forum_dir=forum_dir) if forum_dir else forum_index.index()
        arc = next((m["arc"] for m in metas if m["round"] == round_num), None)
    if rounds is None:
        try:
            first, last = forum_index.LEGACY_ARCS[int(arc)]
            rounds = list(range(first, min(last, round_num) + 1))
        except (KeyError, TypeError, ValueError):
            metas = forum_index.index(forum_dir=forum_dir) if forum_dir else forum_index.index()
            rounds = sorted({m["round"] for m in metas if str(m["arc"]) == str(arc)
                             and m["round"] and m["round"] <= round_num}) or [round_num]
    rows = sidecar_rows(rounds, logs_dir)
    have = {r["round"] for r in rows if r["role"] in forum_index.ROLE_ORDER}
    missing = [r for r in rounds if r not in have]
    recon = reconstructed_rows(missing, forum_dir) if missing else []
    order = {r: i for i, r in enumerate(forum_index.ROLE_ORDER)}
    rows = sorted(rows + recon, key=lambda r: (r["round"], order.get(r["role"], 9), r.get("date") or ""))
    arc_status = _read_json(kd / "arc_status.json")
    first, last = _span(rows)
    data = {
        "stem": stem, "round": round_num, "arc": arc, "rounds": rounds,
        "generated": datetime.now().isoformat(timespec="seconds"),
        "rows": rows,
        "reconstructed": any(r["source"] == "reconstructed" for r in rows),
        "gate": gate_provenance(arc, rounds[0] if rounds else None, topic_gate),
        "recorded_overrides": recorded_overrides(arc_status, rounds, forum_dir),
        "ledger": ledger_items(rounds, kd),
        "gate_commits": gate_commits(first, last),
    }
    data["footnote"] = footnote_text(data)
    tex = render_tex(data)
    hits = leak_lint.scan_text(tex, path=f"{stem}.disclosure.tex")
    data["leak_hits"] = [{"line": h["line"], "pattern_id": h["pattern_id"]} for h in hits]
    paths = {}
    if write:
        od = Path(out_dir) if out_dir else BASE_DIR / "articles"
        od.mkdir(parents=True, exist_ok=True)
        paths["tex"] = od / f"{stem}.disclosure.tex"
        paths["json"] = od / f"{stem}.disclosure.json"
        paths["tex"].write_text(tex, encoding="utf-8")
        paths["json"].write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"tex": tex, "json": data, "footnote": data["footnote"], "leak_hits": data["leak_hits"],
            "paths": paths}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Build a paper's AI-use disclosure from logs.")
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--stem", required=True)
    ap.add_argument("--arc", default=None)
    ap.add_argument("--out", default=None, help="output directory (default: articles/)")
    ap.add_argument("--print", action="store_true", help="print the tex, write nothing")
    args = ap.parse_args(argv)
    res = build(args.round, args.stem, arc=args.arc, out_dir=Path(args.out) if args.out else None,
                write=not args.print)
    if args.print:
        print(res["tex"])
    else:
        print(f"wrote {res['paths'].get('tex')} ({len(res['json']['rows'])} rows, "
              f"{len(res['leak_hits'])} leak hits)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

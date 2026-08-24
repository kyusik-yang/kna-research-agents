#!/usr/bin/env python3
"""Research-taste taxonomy monitor (Season 2, since 2026-08-24).

Chen, Zhao, and Cohan (2026, arXiv:2607.01233) show that LLM research ideas
collapse onto a narrow region of "research taste": bridge-type motivations
(47-64% of LLM ideas vs 12.1% of human papers) and synthesis-type methods
(22-39% vs 5.1%), with lower entropy on both axes. They also show that prompt
wording does not move the distribution and that extended reasoning sharpens it.
The only defensible response is to measure the forum's own distribution and
let the Critic act on it. This module does the measuring.

Every Critic review in Season 2 carries three labels in its scoring block:

    opportunity_pattern: <one of OPPORTUNITY>
    method_paradigm:     <one of METHOD>
    operation:           <one of OPERATION>

The first two axes are Chen et al.'s taxonomy verbatim. The operation family
comes from their archetype analysis (integrate/unify dominate LLM ideas;
replace/decouple/formalize dominate human ideas).

Usage:
    python3 taxonomy_monitor.py report [--since ROUND]
    python3 taxonomy_monitor.py record --round N
    python3 taxonomy_monitor.py label-legacy      # Season 1 baseline via claude -p
"""

import argparse
import json
import math
import re
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
FORUM_DIR = BASE_DIR / "forum"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
ARTICLES_DIR = BASE_DIR / "articles"
WORKSPACE_DIR = BASE_DIR / "workspace"
AGENTS_FILE = BASE_DIR / "agents.json"
TAXONOMY_FILE = KNOWLEDGE_DIR / "taxonomy.jsonl"
LEGACY_FILE = KNOWLEDGE_DIR / "taxonomy_legacy.jsonl"
ACTIVE_ARC_FILE = KNOWLEDGE_DIR / "active_arc.json"
CLAUDE = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude")

OPPORTUNITY = [
    "puzzle_contradiction",   # observed pattern contradicts a standard prediction
    "explanation_gap",        # pattern is known but has no accepted mechanism
    "scope_mismatch",         # a theory is applied outside the conditions it assumes
    "evidence_gap",           # claim exists but has never been measured properly
    "bridge_opportunity",     # two literatures or evidence streams should be connected
    "failure_risk_gap",       # an overlooked failure mode or risk
    "resource_bottleneck",    # a missing dataset, measure, or instrument
]

METHOD = [
    "synthesis_unification",  # integrate or reconcile existing approaches
    "relax_extend_scope",     # relax an assumption or extend to new cases
    "robustification",        # make an existing result robust
    "formal_derivation",      # derive a formal model or proof
    "empirical_mapping",      # measure and map a phenomenon
    "artifact_system",        # build a dataset, measure, or tool
    "optimization_search",    # optimize or search over a design space
]

OPERATION = [
    "integrate", "unify", "extend",
    "replace", "decouple", "formalize", "measure",
    "other",
]

# Chen et al. (2026) reference distribution, main evaluation set (n = 11,683
# human ideas). Used only for the report header, never as a target.
HUMAN_BASELINE = {
    "bridge_share": 0.121,
    "synthesis_share": 0.051,
    "opportunity_entropy": 0.926,
    "method_entropy": 0.920,
    "llm_bridge_range": (0.471, 0.642),
    "llm_synthesis_range": (0.225, 0.387),
}

LABEL_RE = re.compile(
    r"^\s*(opportunity_pattern|method_paradigm|operation):\s*([A-Za-z_]+)",
    re.MULTILINE,
)


def parse_labels(text: str) -> dict | None:
    """Extract the three taxonomy labels from a Critic post. Returns None if
    no label line is present (Season 1 posts)."""
    found = {}
    for key, val in LABEL_RE.findall(text):
        found[key] = val.strip().lower()
    if not found:
        return None
    out = {
        "opportunity_pattern": found.get("opportunity_pattern"),
        "method_paradigm": found.get("method_paradigm"),
        "operation": found.get("operation"),
    }
    out["valid"] = (
        out["opportunity_pattern"] in OPPORTUNITY
        and out["method_paradigm"] in METHOD
        and out["operation"] in OPERATION
    )
    m = re.search(r"verdict:\s*(pursue|revise|archive)", text)
    out["verdict"] = m.group(1) if m else None
    m = re.search(r'one_line:\s*"([^"]+)"', text)
    out["one_line"] = m.group(1) if m else None
    return out


def _n_agents() -> int:
    try:
        with open(AGENTS_FILE) as f:
            return len(json.load(f)["agents"])
    except Exception:
        return 3


def load_entries(path: Path = TAXONOMY_FILE) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def record_round(round_num: int, forum_dir: Path = FORUM_DIR,
                 out_file: Path = TAXONOMY_FILE) -> dict | None:
    """Parse the Critic post of one round and append its labels."""
    posts = sorted(forum_dir.glob("*.md"))
    n = _n_agents()
    for p in posts[(round_num - 1) * n: round_num * n]:
        if "critic" not in p.name:
            continue
        labels = parse_labels(p.read_text(encoding="utf-8"))
        if labels is None:
            print(f"  [Taxonomy] R{round_num}: no labels in {p.name} (Season 1 format?)")
            return None
        if any(e.get("source") == p.name for e in load_entries(out_file)):
            return None
        entry = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "round": round_num,
            "source": p.name,
            **labels,
        }
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        flag = "" if labels["valid"] else "  (UNKNOWN LABEL, check spelling)"
        print(f"  [Taxonomy] R{round_num}: {labels['opportunity_pattern']} / "
              f"{labels['method_paradigm']} / {labels['operation']}{flag}")
        return entry
    return None


def normalized_entropy(counts: Counter, k: int) -> float:
    total = sum(counts.values())
    if total == 0 or k <= 1:
        return 0.0
    h = 0.0
    for c in counts.values():
        if c:
            p = c / total
            h -= p * math.log2(p)
    return h / math.log2(k)


def summarize(entries: list[dict]) -> dict:
    opp = Counter(e.get("opportunity_pattern") for e in entries if e.get("opportunity_pattern"))
    met = Counter(e.get("method_paradigm") for e in entries if e.get("method_paradigm"))
    ops = Counter(e.get("operation") for e in entries if e.get("operation"))
    n = len(entries)
    return {
        "n": n,
        "opportunity": dict(opp),
        "method": dict(met),
        "operation": dict(ops),
        "bridge_share": (opp.get("bridge_opportunity", 0) / n) if n else 0.0,
        "synthesis_share": (met.get("synthesis_unification", 0) / n) if n else 0.0,
        "integrate_unify_share": ((ops.get("integrate", 0) + ops.get("unify", 0)) / n) if n else 0.0,
        "opportunity_entropy": normalized_entropy(opp, len(OPPORTUNITY)),
        "method_entropy": normalized_entropy(met, len(METHOD)),
    }


def arc_start_round() -> int | None:
    if ACTIVE_ARC_FILE.exists():
        try:
            return int(json.loads(ACTIVE_ARC_FILE.read_text()).get("start_round"))
        except Exception:
            return None
    return None


def arc_summary(since: int | None = None) -> dict:
    entries = load_entries()
    if since is None:
        since = arc_start_round()
    if since is not None:
        entries = [e for e in entries if int(e.get("round", 0)) >= since]
    s = summarize(entries)
    s["since_round"] = since
    return s


def cap_active(summary: dict, threshold: float = 0.40, min_n: int = 3) -> bool:
    """The bridge cap fires once the arc has at least min_n labeled rounds and
    the bridge share is at or above threshold."""
    return summary["n"] >= min_n and summary["bridge_share"] >= threshold


def format_for_prompt(since: int | None = None, threshold: float = 0.40) -> str:
    """Block injected into Critic prompts (and, briefly, into all agents)."""
    s = arc_summary(since)
    hb = HUMAN_BASELINE
    lines = ["\n## Arc Research-Taste Monitor (Season 2)\n"]
    if s["n"] == 0:
        lines.append(
            "No labeled rounds in this arc yet. Human reference (Chen et al. 2026): "
            f"bridge {hb['bridge_share']:.0%}, synthesis {hb['synthesis_share']:.0%}, "
            f"opportunity entropy {hb['opportunity_entropy']:.2f}. "
            f"LLM ideation typically runs bridge {hb['llm_bridge_range'][0]:.0%}-{hb['llm_bridge_range'][1]:.0%}. "
            "Label honestly; the cap is off."
        )
        return "\n".join(lines) + "\n"
    lines.append(
        f"Labeled rounds in arc: {s['n']} (since R{s['since_round'] or 1}). "
        f"Bridge share {s['bridge_share']:.0%} (human reference {hb['bridge_share']:.0%}), "
        f"synthesis share {s['synthesis_share']:.0%} (human {hb['synthesis_share']:.0%}), "
        f"integrate/unify operations {s['integrate_unify_share']:.0%}. "
        f"Opportunity entropy {s['opportunity_entropy']:.2f} (human {hb['opportunity_entropy']:.2f}), "
        f"method entropy {s['method_entropy']:.2f} (human {hb['method_entropy']:.2f})."
    )
    if cap_active(s, threshold):
        lines.append(
            f"\n**BRIDGE CAP ACTIVE** (arc bridge share >= {threshold:.0%}). A proposal labeled "
            "bridge_opportunity + synthesis_unification in this round gets research_novelty "
            "capped at 2/4 and cannot receive a pursue verdict. Say so explicitly in the review."
        )
    else:
        lines.append("\nBridge cap: off.")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# Season 1 baseline: label the 12 articles and the pursue findings once.
# --------------------------------------------------------------------------

TAXONOMY_TEXT = f"""\
Two-axis research-taste taxonomy (Chen, Zhao, and Cohan 2026, arXiv:2607.01233).

OPPORTUNITY PATTERN (why the study is needed; pick exactly one):
- puzzle_contradiction: an observed pattern contradicts a standard prediction
- explanation_gap: the pattern is known but has no accepted mechanism
- scope_mismatch: a theory is applied outside the conditions it assumes
- evidence_gap: a claim exists but has never been measured properly
- bridge_opportunity: two literatures, methods, or evidence streams should be connected
- failure_risk_gap: an overlooked failure mode or risk
- resource_bottleneck: a missing dataset, measure, or instrument

METHOD PARADIGM (how the gap becomes a contribution; pick exactly one):
- synthesis_unification: integrate or reconcile existing approaches
- relax_extend_scope: relax an assumption or extend to new cases
- robustification: make an existing result robust
- formal_derivation: derive a formal model
- empirical_mapping: measure and map a phenomenon
- artifact_system: build a dataset, measure, or tool
- optimization_search: optimize or search over a design space

OPERATION (main verb of the one-sentence archetype; pick exactly one):
{", ".join(OPERATION)}
"""


def _article_items() -> list[dict]:
    items = []
    for f in sorted(ARTICLES_DIR.glob("2026-*_r*.md")):
        text = f.read_text(encoding="utf-8")
        title = ""
        m = re.search(r'^title:\s*"?(.+?)"?\s*$', text, re.MULTILINE)
        if m:
            title = m.group(1)
        body = re.sub(r"^---.*?---\s*", "", text, count=1, flags=re.DOTALL)
        items.append({"id": f.stem, "title": title, "text": body[:1500]})
    return items


def _scout_items() -> list[dict]:
    """Scout posts are the ideation-prone object: label their own framing."""
    items = []
    for f in sorted(FORUM_DIR.glob("*_literature_scout.md")):
        text = f.read_text(encoding="utf-8")
        body = re.sub(r"^---.*?---\s*", "", text, count=1, flags=re.DOTALL)
        m = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        title = m.group(1).strip() if m else f.stem
        items.append({"id": f.stem, "title": title, "text": body[:1800]})
    return items


def _pursue_items() -> list[dict]:
    items = []
    fpath = KNOWLEDGE_DIR / "findings.jsonl"
    if not fpath.exists():
        return items
    for line in fpath.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("verdict") == "pursue":
            items.append({"id": f"R{r.get('round')}_{r.get('source')}", "title": r.get("finding", ""), "text": ""})
    return items


def _label_batch(kind: str, items: list[dict]) -> list[dict]:
    listing = "\n\n".join(
        f"[{it['id']}] {it['title']}\n{it['text']}" if it["text"] else f"[{it['id']}] {it['title']}"
        for it in items
    )
    prompt = (
        "You are an annotator. Label each item below with the taxonomy. "
        "Judge the item's own framing, not what a better paper would have done. "
        "Output ONLY JSON lines, one per item, with keys id, opportunity_pattern, "
        "method_paradigm, operation. No prose.\n\n"
        + TAXONOMY_TEXT + "\n\nITEMS (" + kind + "):\n\n" + listing
    )
    WORKSPACE_DIR.mkdir(exist_ok=True)
    pfile = WORKSPACE_DIR / f"_prompt_taxonomy_{kind}.md"
    pfile.write_text(prompt, encoding="utf-8")
    cmd = [CLAUDE, "-p", "--output-format", "text",
           "--system-prompt-file", str(pfile),
           "Label every item now. JSON lines only."]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, cwd=str(WORKSPACE_DIR))
    out = []
    for line in res.stdout.splitlines():
        line = line.strip().strip("`")
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        d["kind"] = kind
        d["valid"] = (
            d.get("opportunity_pattern") in OPPORTUNITY
            and d.get("method_paradigm") in METHOD
            and d.get("operation") in OPERATION
        )
        out.append(d)
    if res.returncode != 0:
        print(f"  [Taxonomy] claude exit {res.returncode}: {res.stderr[:200]}")
    return out


def label_legacy() -> None:
    """Label Season 1 articles and pursue findings; write taxonomy_legacy.jsonl."""
    rows = []
    arts = _article_items()
    print(f"  Labeling {len(arts)} Season 1 articles...")
    rows += _label_batch("articles", arts)
    purs = _pursue_items()
    print(f"  Labeling {len(purs)} Season 1 pursue findings...")
    rows += _label_batch("pursue_findings", purs)
    scouts = _scout_items()
    print(f"  Labeling {len(scouts)} Season 1 Scout posts (proposals before the Critic filter)...")
    rows += _label_batch("scout_posts", scouts)
    LEGACY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LEGACY_FILE, "w", encoding="utf-8") as f:
        for r in rows:
            r["ts"] = datetime.now().isoformat(timespec="seconds")
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"  Wrote {len(rows)} labels to {LEGACY_FILE.name}")
    for kind in ("articles", "pursue_findings", "scout_posts"):
        sub = [r for r in rows if r.get("kind") == kind]
        if sub:
            print_report(summarize(sub), title=f"Season 1 baseline: {kind}")


def print_report(s: dict, title: str = "Arc research-taste report") -> None:
    hb = HUMAN_BASELINE
    print(f"\n  {title}")
    print(f"  n = {s['n']}")
    if s["n"] == 0:
        print("  (no labeled rounds)")
        return
    print(f"  bridge share      {s['bridge_share']:.1%}   (human {hb['bridge_share']:.1%}, LLM {hb['llm_bridge_range'][0]:.0%}-{hb['llm_bridge_range'][1]:.0%})")
    print(f"  synthesis share   {s['synthesis_share']:.1%}   (human {hb['synthesis_share']:.1%}, LLM {hb['llm_synthesis_range'][0]:.0%}-{hb['llm_synthesis_range'][1]:.0%})")
    print(f"  integrate/unify   {s['integrate_unify_share']:.1%}")
    print(f"  opp. entropy      {s['opportunity_entropy']:.3f}  (human {hb['opportunity_entropy']:.3f})")
    print(f"  method entropy    {s['method_entropy']:.3f}  (human {hb['method_entropy']:.3f})")
    for axis in ("opportunity", "method", "operation"):
        items = sorted(s[axis].items(), key=lambda kv: -kv[1])
        print(f"  {axis}: " + ", ".join(f"{k} {v}" for k, v in items))


def main() -> None:
    ap = argparse.ArgumentParser(description="Season 2 research-taste taxonomy monitor")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("report", help="Print the arc distribution")
    r.add_argument("--since", type=int, default=None, help="First round to include (default: active arc)")
    r.add_argument("--legacy", action="store_true", help="Report the Season 1 baseline instead")
    r.add_argument("--json", action="store_true")
    rec = sub.add_parser("record", help="Record labels from one round's Critic post")
    rec.add_argument("--round", type=int, required=True)
    sub.add_parser("label-legacy", help="Label Season 1 articles and pursue findings via claude -p")
    args = ap.parse_args()

    if args.cmd == "record":
        record_round(args.round)
    elif args.cmd == "label-legacy":
        label_legacy()
    else:
        if getattr(args, "legacy", False):
            rows = load_entries(LEGACY_FILE)
            for kind in ("articles", "pursue_findings", "scout_posts"):
                sub_rows = [x for x in rows if x.get("kind") == kind]
                s = summarize(sub_rows)
                if getattr(args, "json", False):
                    print(json.dumps({kind: s}, ensure_ascii=False))
                else:
                    print_report(s, title=f"Season 1 baseline: {kind}")
        else:
            s = arc_summary(getattr(args, "since", None))
            if getattr(args, "json", False):
                print(json.dumps(s, ensure_ascii=False))
            else:
                print_report(s)
                print("\n  cap active:", cap_active(s))


if __name__ == "__main__":
    main()

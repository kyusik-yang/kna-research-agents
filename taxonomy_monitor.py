#!/usr/bin/env python3
"""Research-taste taxonomy monitor (Season 2, since 2026-08-24, report-only since 2026-09-25).

Chen, Zhao, and Cohan (2026, arXiv:2607.01233) show that LLM research ideas
collapse onto a narrow region of "research taste": bridge-type motivations
(47-64% of LLM ideas vs 12.1% of human papers) and synthesis-type methods
(22-39% vs 5.1%), with lower entropy on both axes. This module measures the
forum's own distribution.

Two label sources:

- Critic rounds (unit critic_round). The Critic's scoring block carries
  opportunity_pattern, method_paradigm and operation. These are kept for
  comparison only.
- Arc openings (unit arc_opening, Stage 2 flag forum_config.stage2.annotator).
  One non-posting annotator call per arc, right after the opening Scout post,
  through claude_cli with no tools and a frozen prompt (ANNOTATOR_PROMPT, its
  sha256 is logged on every row). The annotator sees only the proposal text
  (Prediction to Test, Gap Type, card, and any arc_slate candidates) and the
  taxonomy definitions, never monitor numbers, verdicts or Critic text. It
  adds constructed_contradiction (a gap-type (c) contradiction whose rival
  prediction the proposer inferred), counted as a bridge variant, and
  identification_design.

Report-only. The bridge cap is retired from the Critic path, so
format_for_prompt no longer shows entropies, shares or cap status, and
nothing in the Critic path reads cap_active. Entropy and cap status go to the site and to
arc_slate.py only. cap_active keeps its signature for the report and tests.

Usage:
    python3 taxonomy_monitor.py report [--since ROUND] [--legacy] [--openers] [--json]
    python3 taxonomy_monitor.py record --round N [--post forum/NNN_critic.md]
    python3 taxonomy_monitor.py annotate forum/082_literature_scout.md --round 28 [--dry-run] [--force]
    python3 taxonomy_monitor.py label-openers [--dry-run]     # legacy arc openers, frozen prompt
    python3 taxonomy_monitor.py label-legacy [--dry-run]      # Season 1 items without a label
"""

import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
FORUM_DIR = BASE_DIR / "forum"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
ARTICLES_DIR = BASE_DIR / "articles"
AGENTS_FILE = BASE_DIR / "agents.json"
TAXONOMY_FILE = KNOWLEDGE_DIR / "taxonomy.jsonl"
LEGACY_FILE = KNOWLEDGE_DIR / "taxonomy_legacy.jsonl"
ACTIVE_ARC_FILE = KNOWLEDGE_DIR / "active_arc.json"
SEASON1_LAST_ROUND = 24

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

# Annotator-only label (M19/M20). The Critic keeps Chen et al.'s seven.
CONSTRUCTED = "constructed_contradiction"
ANNOTATOR_OPPORTUNITY = OPPORTUNITY + [CONSTRUCTED]
BRIDGE_VARIANTS = ("bridge_opportunity", CONSTRUCTED)

IDENTIFICATION_DESIGNS = [
    "descriptive",                 # counts, rates, correlations, no causal design
    "cross_sectional_regression",  # observational regression with controls
    "fixed_effects_panel",         # within-unit comparison over time
    "difference_in_differences",   # DiD or event study
    "regression_discontinuity",
    "instrumental_variables",
    "natural_experiment",          # as-if random assignment not covered above
    "matching_weighting",
    "measurement_validation",      # building or validating a measure
    "qualitative_or_case",
    "formal_model",
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

# Arc openers before the annotator existed, in order. Season 1 arcs per
# SEASON2.md (R1-R13, R14-R22, R23-R24), then Season 2 Arc 4 (R25) and Arc 5 (R28).
LEGACY_ARC_OPENERS = [
    ("001_literature_scout", 1),
    ("040_literature_scout", 14),
    ("067_literature_scout", 23),
    ("073_literature_scout", 25),
    ("082_literature_scout", 28),
]
OPENER_WINDOW = 6

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


def _config() -> dict:
    try:
        with open(AGENTS_FILE) as f:
            return json.load(f).get("forum_config", {})
    except Exception:
        return {}


def _n_agents() -> int:
    try:
        with open(AGENTS_FILE) as f:
            return len(json.load(f)["agents"])
    except Exception:
        return 3


def load_entries(path: Path | None = None) -> list[dict]:
    # Resolve defaults at call time so tests can monkeypatch the module paths.
    path = TAXONOMY_FILE if path is None else Path(path)
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


def _unit(row: dict) -> str:
    return row.get("unit") or "critic_round"


def _append(rows: list[dict], out_file: Path) -> None:
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "a", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def record_round(round_num: int, forum_dir: Path | None = None,
                 out_file: Path | None = None, post_path: Path | None = None) -> dict | None:
    """Parse the Critic post of one round and append its labels (comparison
    only). Pass post_path, the path the accepted Critic run returned, so the
    round is never located by file index."""
    forum_dir = FORUM_DIR if forum_dir is None else forum_dir
    out_file = TAXONOMY_FILE if out_file is None else out_file
    if post_path is not None:
        candidates = [Path(post_path)]
    else:
        posts = sorted(forum_dir.glob("*.md"))
        n = _n_agents()
        candidates = [p for p in posts[(round_num - 1) * n: round_num * n] if "critic" in p.name]
    for p in candidates:
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
            "unit": "critic_round",
            **labels,
        }
        _append([entry], out_file)
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
    """Shares and normalized entropies. constructed_contradiction counts as a
    bridge variant, so bridge_share and the opportunity entropy (over Chen et
    al.'s seven patterns) fold it into bridge_opportunity."""
    raw_opp = Counter(e.get("opportunity_pattern") for e in entries if e.get("opportunity_pattern"))
    opp = Counter()
    for k, v in raw_opp.items():
        opp["bridge_opportunity" if k == CONSTRUCTED else k] += v
    met = Counter(e.get("method_paradigm") for e in entries if e.get("method_paradigm"))
    ops = Counter(e.get("operation") for e in entries if e.get("operation"))
    n = len(entries)
    return {
        "n": n,
        "opportunity": dict(raw_opp),
        "method": dict(met),
        "operation": dict(ops),
        "bridge_share": (opp.get("bridge_opportunity", 0) / n) if n else 0.0,
        "constructed_share": (raw_opp.get(CONSTRUCTED, 0) / n) if n else 0.0,
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


def arc_summary(since: int | None = None, unit: str | None = "critic_round") -> dict:
    """Distribution over the active arc. unit=None mixes every label source."""
    entries = load_entries()
    if unit is not None:
        entries = [e for e in entries if _unit(e) == unit]
    if since is None:
        since = arc_start_round()
    if since is not None:
        entries = [e for e in entries if int(e.get("round", 0)) >= since]
    s = summarize(entries)
    s["since_round"] = since
    s["unit"] = unit
    return s


def cap_active(summary: dict, threshold: float = 0.40, min_n: int = 3) -> bool:
    """Report-only since 2026-09-25 (M20, pending D-15). The bridge cap no
    longer acts on the Critic. The value is shown on the site and passed to
    arc_slate.py. True once at least min_n labels exist and the bridge share
    is at or above threshold."""
    return summary["n"] >= min_n and summary["bridge_share"] >= threshold


# --------------------------------------------------------------------------
# Label definitions (no monitor numbers anywhere in this text)
# --------------------------------------------------------------------------

TAXONOMY_TEXT = f"""\
Two-axis research-taste taxonomy (Chen, Zhao, and Cohan 2026, arXiv:2607.01233).

OPPORTUNITY PATTERN, why the study is needed (pick exactly one):
- puzzle_contradiction: an observed pattern contradicts a standard prediction
- explanation_gap: the pattern is known but has no accepted mechanism
- scope_mismatch: a theory is applied outside the conditions it assumes
- evidence_gap: a claim exists but has never been measured properly
- bridge_opportunity: two literatures, methods, or evidence streams should be connected
- failure_risk_gap: an overlooked failure mode or risk
- resource_bottleneck: a missing dataset, measure, or instrument

METHOD PARADIGM, how the gap becomes a contribution (pick exactly one):
- synthesis_unification: integrate or reconcile existing approaches
- relax_extend_scope: relax an assumption or extend to new cases
- robustification: make an existing result robust
- formal_derivation: derive a formal model
- empirical_mapping: measure and map a phenomenon
- artifact_system: build a dataset, measure, or tool
- optimization_search: optimize or search over a design space

OPERATION, the main verb of the one-sentence archetype (pick exactly one):
{", ".join(OPERATION)}
"""


def format_for_prompt(since: int | None = None, threshold: float = 0.40) -> str:
    """Label definitions for an agent that writes taxonomy labels. Report-only
    since 2026-09-25 (M20): no shares, entropies, reference numbers or cap
    status, so the labels cannot respond to the display. The arguments are
    kept for signature compatibility and are ignored."""
    return ("\n## Research-taste labels (kept for comparison only)\n\n"
            "Label the round's proposal with one value per axis. The labels do not affect any verdict.\n\n"
            + TAXONOMY_TEXT + "\n")


# --------------------------------------------------------------------------
# Frozen annotator (M20)
# --------------------------------------------------------------------------

ANNOTATOR_PROMPT_VERSION = "taxonomy-annotator-v1 (2026-09-25)"
ANNOTATOR_PROMPT = TAXONOMY_TEXT + """
CONSTRUCTED CONTRADICTION (an extra opportunity value for this annotation):
- constructed_contradiction: the proposal says two literatures predict opposite
  results for the same quantity, but at least one side's prediction is not
  stated in the cited work. The proposer inferred or derived it (for example,
  an international literature set against a domestic literature that never
  estimated the quantity). Use it instead of puzzle_contradiction or
  bridge_opportunity whenever the rival prediction is inferred rather than
  quoted and located.

IDENTIFICATION DESIGN, how the proposal would separate its claim from
alternatives (pick exactly one):
- descriptive: counts, rates or correlations with no causal design
- cross_sectional_regression: observational regression with controls
- fixed_effects_panel: within-unit comparison over time
- difference_in_differences: difference-in-differences or event study
- regression_discontinuity: a cutoff in an assignment variable
- instrumental_variables: an instrument for the treatment
- natural_experiment: as-if random assignment not covered above
- matching_weighting: matching or weighting on observables
- measurement_validation: building or validating a measure
- qualitative_or_case: case study or qualitative comparison
- formal_model: a formal model or derivation
- other: none of the above

You are an annotator. You receive research proposals, each with an id. Label
every proposal on the four axes from its own text. Judge the framing the
proposal actually uses, not what a better proposal would have done, and not
whether it is a good idea. Return one item per proposal id, with exactly the
ids you were given.
"""
ANNOTATOR_PROMPT_SHA256 = hashlib.sha256(ANNOTATOR_PROMPT.encode("utf-8")).hexdigest()

ANNOTATOR_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "opportunity_pattern": {"type": "string", "enum": ANNOTATOR_OPPORTUNITY},
                    "method_paradigm": {"type": "string", "enum": METHOD},
                    "operation": {"type": "string", "enum": OPERATION},
                    "identification_design": {"type": "string", "enum": IDENTIFICATION_DESIGNS},
                },
                "required": ["id", "opportunity_pattern", "method_paradigm", "operation",
                             "identification_design"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["items"],
    "additionalProperties": False,
}


def validate_item(d: dict) -> bool:
    return (isinstance(d, dict)
            and d.get("opportunity_pattern") in ANNOTATOR_OPPORTUNITY
            and d.get("method_paradigm") in METHOD
            and d.get("operation") in OPERATION
            and d.get("identification_design") in IDENTIFICATION_DESIGNS)


def proposal_text(post_path: Path) -> str:
    """What the annotator sees for one Scout post: the Prediction to Test and
    Gap Type sections and the card (Season 1 posts: the body without code
    blocks, first 4,000 characters). No monitor output, verdict or Critic post."""
    import topic_diversity as td
    raw = Path(post_path).read_text(encoding="utf-8")
    sections = td.proposal_sections(raw)
    if not sections:
        return td.post_text(Path(post_path))
    card = td.extract_card(raw)
    return sections + ("\n\nCard:\n" + json.dumps(card, ensure_ascii=False, indent=1) if card else "")


def build_annotator_message(items: list[dict]) -> str:
    listing = "\n\n".join(f"[{it['id']}]\n{it['text']}" for it in items)
    return (f"Label these {len(items)} proposals. Ids: {', '.join(it['id'] for it in items)}.\n\n"
            + listing)


def annotate(items: list[dict], *, round_num: int | None = None, arc_id: str | None = None) -> tuple[list[dict], dict]:
    """One annotator call through claude_cli for a list of {"id", "text"}.
    Returns (valid labeled items, call info). Raises nothing on a failed call."""
    import claude_cli
    res = claude_cli.run_claude(
        "annotator", ANNOTATOR_PROMPT,
        user_message=build_annotator_message(items),
        schema=ANNOTATOR_SCHEMA, round_num=round_num, arc_id=arc_id,
    )
    info = {"run_id": getattr(res, "run_id", None), "model": getattr(res, "model", None),
            "failure": getattr(res, "failure", None), "ok": bool(getattr(res, "ok", False))}
    if not info["ok"] or not isinstance(getattr(res, "structured", None), dict):
        print(f"  [Taxonomy] annotator call failed ({info['failure']}), no labels recorded")
        return [], info
    wanted = {it["id"] for it in items}
    out, seen = [], set()
    for d in res.structured.get("items") or []:
        if not isinstance(d, dict) or d.get("id") not in wanted or d["id"] in seen:
            continue
        seen.add(d["id"])
        out.append({k: d.get(k) for k in ("id", "opportunity_pattern", "method_paradigm", "operation",
                                          "identification_design")} | {"valid": validate_item(d)})
    return out, info


def _slate_for_active_arc() -> dict | None:
    """The arc_slate slate whose gate stub opened the active arc, if any."""
    try:
        seed = json.loads(ACTIVE_ARC_FILE.read_text()).get("seed") if ACTIVE_ARC_FILE.exists() else None
        if not seed:
            return None
        import arc_slate
        return arc_slate.slate_for_seed(seed)
    except Exception:
        return None


def _stage2_annotator() -> bool:
    return bool((_config().get("stage2") or {}).get("annotator", False))


def annotate_arc_opening(post_path: Path, *, round_num: int, arc_id: str | None = None,
                         slate: dict | None = None, force: bool = False,
                         out_file: Path | None = None) -> list[dict] | None:
    """Label the arc's opening proposal, and the arc_slate candidates if a
    slate was used, in one annotator call. Stage 2 (forum_config.stage2.annotator).
    force=True runs it by hand. Report-only: never raises, never blocks."""
    if not force and not _stage2_annotator():
        return None
    out_file = TAXONOMY_FILE if out_file is None else out_file
    try:
        post_path = Path(post_path)
        if any(_unit(e) == "arc_opening" and e.get("source") == post_path.name for e in load_entries(out_file)):
            return None
        items = [{"id": post_path.stem, "text": proposal_text(post_path)}]
        if slate is None:
            slate = _slate_for_active_arc()
        slate_id = None
        if slate:
            slate_id = slate.get("slate_id")
            for c in slate.get("candidates") or []:
                if c.get("status") == "candidate":
                    items.append({"id": f"slate_{slate_id}_{c['candidate_id']}", "text": c.get("text", "")})
        labeled, info = annotate(items, round_num=round_num, arc_id=arc_id)
        rows = []
        ts = datetime.now().isoformat(timespec="seconds")
        for d in labeled:
            is_opening = d["id"] == post_path.stem
            rows.append({
                "ts": ts, "round": round_num, "arc": arc_id,
                "unit": "arc_opening" if is_opening else "slate_candidate",
                "source": post_path.name if is_opening else d["id"],
                "slate_id": slate_id,
                "opportunity_pattern": d["opportunity_pattern"], "method_paradigm": d["method_paradigm"],
                "operation": d["operation"], "identification_design": d["identification_design"],
                "valid": d["valid"], "annotator_prompt_version": ANNOTATOR_PROMPT_VERSION,
                "annotator_prompt_sha256": ANNOTATOR_PROMPT_SHA256,
                "run_id": info["run_id"], "model": info["model"],
            })
        if rows:
            _append(rows, out_file)
            print(f"  [Taxonomy] arc opening {post_path.name}: {rows[0]['opportunity_pattern']} / "
                  f"{rows[0]['method_paradigm']} / {rows[0]['operation']} / {rows[0]['identification_design']}")
        return rows
    except Exception as e:  # monitoring must never block a round
        print(f"  [Taxonomy] annotator unavailable (non-fatal): {e}")
        return None


# --------------------------------------------------------------------------
# Six-opener window (report for the site and arc_slate.py, never the Critic)
# --------------------------------------------------------------------------

def _legacy_labels() -> dict:
    return {r.get("id"): r for r in load_entries(LEGACY_FILE) if r.get("kind") == "scout_posts"}


def opener_labels(entries: list[dict] | None = None) -> list[dict]:
    """Every known arc opener in order with its best available label:
    the frozen annotator (arc_opening row), else the v1 legacy annotator, else
    the Critic's label for that round, else none."""
    entries = load_entries() if entries is None else entries
    annot = {e.get("source"): e for e in entries if _unit(e) == "arc_opening"}
    critic = {int(e.get("round", 0)): e for e in entries if _unit(e) == "critic_round"}
    legacy = _legacy_labels()
    openers = [(stem + ".md", rnd) for stem, rnd in LEGACY_ARC_OPENERS]
    known = {o for o, _ in openers}
    for e in entries:
        if _unit(e) == "arc_opening" and e.get("source") not in known:
            openers.append((e["source"], int(e.get("round", 0))))
            known.add(e["source"])
    out = []
    for name, rnd in sorted(openers, key=lambda x: x[1]):
        stem = name[:-3] if name.endswith(".md") else name
        if name in annot:
            row, source = annot[name], "annotator"
        elif stem in legacy:
            row, source = legacy[stem], "legacy_annotator"
        elif rnd in critic:
            row, source = critic[rnd], "critic"
        else:
            row, source = {}, "unlabeled"
        out.append({"post": name, "round": rnd, "label_source": source,
                    "opportunity_pattern": row.get("opportunity_pattern"),
                    "method_paradigm": row.get("method_paradigm"),
                    "operation": row.get("operation"),
                    "identification_design": row.get("identification_design")})
    return out


def opener_report(n: int = OPENER_WINDOW, threshold: float = 0.40) -> dict:
    """Distribution over the last n arc openers, with per-pattern counts that
    arc_slate.py uses to weight its seeds. Report-only."""
    window = opener_labels()[-n:]
    labeled = [w for w in window if w["opportunity_pattern"]]
    s = summarize(labeled)
    s["window"] = [{k: w[k] for k in ("post", "round", "label_source", "opportunity_pattern")} for w in window]
    s["label_sources"] = dict(Counter(w["label_source"] for w in window))
    s["cap_active_report_only"] = cap_active(s, threshold)
    s["opportunity_counts_all"] = {p: s["opportunity"].get(p, 0) for p in ANNOTATOR_OPPORTUNITY}
    return s


def monitor_report() -> dict:
    """Everything the site shows: the arc (Critic labels, comparison only), the
    opener window, and the human reference."""
    return {"arc_critic_labels": arc_summary(), "openers": opener_report(),
            "human_baseline": HUMAN_BASELINE, "bridge_cap": "retired from the Critic (report only)"}


# --------------------------------------------------------------------------
# Season 1 items without a label (frozen prompt, through claude_cli)
# --------------------------------------------------------------------------

def _article_items() -> list[dict]:
    import topic_diversity as td
    items = []
    for f in td.article_files(ARTICLES_DIR):
        if td._article_round(f) > SEASON1_LAST_ROUND:
            continue
        raw = f.read_text(encoding="utf-8")
        items.append({"id": f.stem, "text": td.tex_title(raw) + ". " + td.tex_abstract(raw)})
    return items


def _scout_items(max_round: int = SEASON1_LAST_ROUND) -> list[dict]:
    """Scout posts are the ideation-prone object, so label their own framing."""
    import topic_diversity as td
    items = []
    for f in sorted(FORUM_DIR.glob("*_literature_scout.md")):
        if td._round_of(f) > max_round:
            continue
        items.append({"id": f.stem, "text": proposal_text(f)})
    return items


def _pursue_items() -> list[dict]:
    """Season 1 pursue findings, one per (round, source, finding)."""
    items, seen = [], set()
    fpath = KNOWLEDGE_DIR / "findings.jsonl"
    if not fpath.exists():
        return items
    for line in fpath.read_text(encoding="utf-8").splitlines():
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        key = (r.get("round"), r.get("source"), r.get("finding"))
        if r.get("verdict") != "pursue" or key in seen or int(r.get("round") or 0) > SEASON1_LAST_ROUND:
            continue
        seen.add(key)
        items.append({"id": f"R{r.get('round')}_{r.get('source')}", "text": r.get("finding", "")})
    return items


def legacy_pursue_baseline(rows: list[dict] | None = None) -> list[dict]:
    """The Season 1 pursue baseline as corrected on 2026-09-26 (SEASON2.md
    erratum): one label row per distinct finding from a Critic post.

    The pursue_findings labels were made one per row of the undeduplicated
    ledger, and their ids read <n>_R<round>_<source post>. The deduplicated
    ledger holds one distinct Season 1 pursue finding per Critic post, so the
    first label of each (round, Critic post) stands for that finding. Labels
    of findings from Analyst or Scout posts are left out."""
    rows = load_entries(LEGACY_FILE) if rows is None else rows
    out, seen = [], set()
    for r in rows:
        if r.get("kind") != "pursue_findings":
            continue
        m = re.match(r"\d+_R(\d+)_(.+)$", str(r.get("id", "")))
        if not m or not m.group(2).endswith("_critic.md"):
            continue
        key = (int(m.group(1)), m.group(2))
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out


def _label_rows(kind: str, items: list[dict], dry_run: bool) -> list[dict]:
    if not items:
        return []
    if dry_run:
        print(f"  [dry-run] would label {len(items)} {kind} in one annotator call "
              f"(prompt sha256 {ANNOTATOR_PROMPT_SHA256[:12]})")
        return []
    labeled, info = annotate(items)
    ts = datetime.now().isoformat(timespec="seconds")
    return [dict(d, kind=kind, ts=ts, annotator_prompt_version=ANNOTATOR_PROMPT_VERSION,
                 annotator_prompt_sha256=ANNOTATOR_PROMPT_SHA256, run_id=info["run_id"], model=info["model"])
            for d in labeled]


def label_legacy(dry_run: bool = False) -> None:
    """Label Season 1 articles, pursue findings and Scout posts that have no
    label yet in taxonomy_legacy.jsonl. Existing labels are kept."""
    have = {(r.get("kind"), r.get("id")) for r in load_entries(LEGACY_FILE)}
    rows = []
    for kind, items in (("articles", _article_items()), ("pursue_findings", _pursue_items()),
                        ("scout_posts", _scout_items())):
        todo = [it for it in items if (kind, it["id"]) not in have]
        print(f"  {kind}: {len(items)} items, {len(todo)} without a label")
        rows += _label_rows(kind, todo, dry_run)
    if rows:
        _append(rows, LEGACY_FILE)
        print(f"  Appended {len(rows)} labels to {LEGACY_FILE.name}")


def label_openers(dry_run: bool = False, out_file: Path | None = None) -> None:
    """Label the legacy arc openers with the frozen annotator (unit arc_opening)."""
    out_file = TAXONOMY_FILE if out_file is None else out_file
    have = {e.get("source") for e in load_entries(out_file) if _unit(e) == "arc_opening"}
    todo = [(stem, rnd) for stem, rnd in LEGACY_ARC_OPENERS if stem + ".md" not in have
            and (FORUM_DIR / f"{stem}.md").exists()]
    items = [{"id": stem, "text": proposal_text(FORUM_DIR / f"{stem}.md")} for stem, _ in todo]
    print(f"  legacy arc openers without an annotator label: {len(items)}")
    if not items:
        return
    if dry_run:
        _label_rows("arc_openers", items, dry_run=True)
        return
    labeled, info = annotate(items)
    rnd_of = dict(todo)
    ts = datetime.now().isoformat(timespec="seconds")
    rows = [{"ts": ts, "round": rnd_of[d["id"]], "arc": None, "unit": "arc_opening",
             "source": d["id"] + ".md", "slate_id": None,
             "opportunity_pattern": d["opportunity_pattern"], "method_paradigm": d["method_paradigm"],
             "operation": d["operation"], "identification_design": d["identification_design"],
             "valid": d["valid"], "annotator_prompt_version": ANNOTATOR_PROMPT_VERSION,
             "annotator_prompt_sha256": ANNOTATOR_PROMPT_SHA256, "run_id": info["run_id"],
             "model": info["model"], "labeled_after_the_fact": True}
            for d in labeled]
    if rows:
        _append(rows, out_file)
        print(f"  Appended {len(rows)} arc-opening labels to {out_file.name}")


def print_report(s: dict, title: str = "Arc research-taste report") -> None:
    hb = HUMAN_BASELINE
    print(f"\n  {title}")
    print(f"  n = {s['n']}")
    if s["n"] == 0:
        print("  (no labeled rounds)")
        return
    print(f"  bridge share      {s['bridge_share']:.1%}   (human {hb['bridge_share']:.1%}, LLM {hb['llm_bridge_range'][0]:.0%}-{hb['llm_bridge_range'][1]:.0%})"
          f"   of which constructed {s.get('constructed_share', 0):.1%}")
    print(f"  synthesis share   {s['synthesis_share']:.1%}   (human {hb['synthesis_share']:.1%}, LLM {hb['llm_synthesis_range'][0]:.0%}-{hb['llm_synthesis_range'][1]:.0%})")
    print(f"  integrate/unify   {s['integrate_unify_share']:.1%}")
    print(f"  opp. entropy      {s['opportunity_entropy']:.3f}  (human {hb['opportunity_entropy']:.3f})")
    print(f"  method entropy    {s['method_entropy']:.3f}  (human {hb['method_entropy']:.3f})")
    for axis in ("opportunity", "method", "operation"):
        items = sorted(s[axis].items(), key=lambda kv: -kv[1])
        print(f"  {axis}: " + ", ".join(f"{k} {v}" for k, v in items))


def main() -> None:
    ap = argparse.ArgumentParser(description="Season 2 research-taste taxonomy monitor (report-only)")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("report", help="Print the arc distribution")
    r.add_argument("--since", type=int, default=None, help="First round to include (default: active arc)")
    r.add_argument("--legacy", action="store_true", help="Report the Season 1 baseline instead")
    r.add_argument("--openers", action="store_true", help="Report the six-opener window")
    r.add_argument("--json", action="store_true")
    rec = sub.add_parser("record", help="Record labels from one round's Critic post")
    rec.add_argument("--round", type=int, required=True)
    rec.add_argument("--post", default=None, help="The Critic post path (default: file-index lookup)")
    an = sub.add_parser("annotate", help="Label an arc-opening Scout post with the frozen annotator")
    an.add_argument("post")
    an.add_argument("--round", type=int, required=True)
    an.add_argument("--arc", default=None)
    an.add_argument("--force", action="store_true", help="Run even when stage2.annotator is off")
    an.add_argument("--dry-run", action="store_true", help="Print the message and schema, make no call")
    lo = sub.add_parser("label-openers", help="Label the legacy arc openers with the frozen annotator")
    lo.add_argument("--dry-run", action="store_true")
    ll = sub.add_parser("label-legacy", help="Label Season 1 items that have no label yet")
    ll.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if args.cmd == "record":
        record_round(args.round, post_path=Path(args.post) if args.post else None)
    elif args.cmd == "annotate":
        if args.dry_run:
            p = Path(args.post)
            print(f"# prompt {ANNOTATOR_PROMPT_VERSION} sha256 {ANNOTATOR_PROMPT_SHA256}\n")
            print(build_annotator_message([{"id": p.stem, "text": proposal_text(p)}]))
            print("\n# schema\n" + json.dumps(ANNOTATOR_SCHEMA, indent=1))
        else:
            annotate_arc_opening(Path(args.post), round_num=args.round, arc_id=args.arc, force=args.force)
    elif args.cmd == "label-openers":
        label_openers(dry_run=args.dry_run)
    elif args.cmd == "label-legacy":
        label_legacy(dry_run=args.dry_run)
    else:
        if getattr(args, "legacy", False):
            rows = load_entries(LEGACY_FILE)
            for kind in ("articles", "pursue_findings", "scout_posts"):
                if kind == "pursue_findings":
                    sub_rows = legacy_pursue_baseline(rows)
                    label = f"{kind} (deduplicated, Critic posts only)"
                else:
                    sub_rows = [x for x in rows if x.get("kind") == kind]
                    label = kind
                s = summarize(sub_rows)
                if getattr(args, "json", False):
                    print(json.dumps({kind: s}, ensure_ascii=False))
                else:
                    print_report(s, title=f"Season 1 baseline: {label}")
        elif getattr(args, "openers", False):
            s = opener_report()
            if getattr(args, "json", False):
                print(json.dumps(s, ensure_ascii=False))
            else:
                print_report(s, title=f"Last {OPENER_WINDOW} arc openers")
                print("  sources:", s["label_sources"])
                print("  cap (retired, report only):", s["cap_active_report_only"])
        else:
            s = arc_summary(getattr(args, "since", None))
            if getattr(args, "json", False):
                print(json.dumps(s, ensure_ascii=False))
            else:
                print_report(s, title="Arc research-taste report (Critic labels, comparison only)")
                print("\n  cap (retired, report only):", cap_active(s))


if __name__ == "__main__":
    main()

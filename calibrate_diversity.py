#!/usr/bin/env python3
"""Calibrate the topic-diversity guard on labeled pairs (M17).

Labeled pairs live in knowledge/diversity_calibration.jsonl (rows with
"row": "pair"). The file is the label store. Pairs added or edited there
(label, confirmed_by) are kept on every run, and SEED_PAIRS below only fill
in pairs the file does not have yet.

- repeat: a known Season 1 repeat (the R18-R22 shirking run and the R7
  re-run of the R1-R2 housing question).
- distinct: a cross-topic pair PROPOSED as clearly distinct. confirmed_by
  stays null until the researcher confirms it (D-15).
- same_topic_within_arc: Season 2 posts inside one arc. Reported as a
  sensitivity set ("extended"), not used for the primary proposal.

For Scout-vs-Scout, Scout-vs-paper and pooled pairs the script reports AUC
with a stratified bootstrap interval, proposes warn and block values on a
0.01 grid, and checks leave-one-out stability:

- warn = the largest grid value at or below every known repeat. It passes
  when at most 10 percent of distinct pairs score at or above it.
- block = the smallest grid value above every distinct pair and above warn,
  so no labeled distinct pair would be blocked.

It also replays the Season 2 Scout posts and the R19 regression case with
the new text and model, next to the statuses the v1 guard logged.

Proposed thresholds are PROVISIONAL. They are never written to agents.json
here. The researcher approves them first (D-15).

Usage:
    python3 calibrate_diversity.py              # compute, print, rewrite the calibration file
    python3 calibrate_diversity.py --dry-run    # compute and print only
    python3 calibrate_diversity.py --list       # print the labeled pairs
"""

import argparse
import json
import math
import os
import random
import sys
from datetime import datetime
from pathlib import Path

import topic_diversity as td

BASE_DIR = Path(__file__).parent
CAL_FILE = BASE_DIR / "knowledge" / "diversity_calibration.jsonl"
SEED = 8374
N_BOOT = 2000
MAX_DISTINCT_SHARE = 0.10
GRID = 0.01
OLD_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

S = "_literature_scout"
# (pair_id, a, b, label, source, note)
SEED_PAIRS = [
    # Known repeats named in the plan (M17) and the diagnosis.
    ("RSS01", "052" + S, "055" + S, "repeat", "plan_M17", "R18 vs R19 Scout, shirking run"),
    ("RSS02", "055" + S, "058" + S, "repeat", "plan_M17", "R19 vs R20 Scout, shirking run"),
    ("RSS03", "058" + S, "064" + S, "repeat", "plan_M17", "R20 vs R22 Scout, shirking run"),
    ("RSS04", "019" + S, "001" + S, "repeat", "plan_M17", "R7 vs R1 Scout, housing re-run"),
    ("RSS05", "019" + S, "004" + S, "repeat", "plan_M17", "R7 vs R2 Scout, housing re-run"),
    ("RSP01", "019" + S, "2026-03-31_r2", "repeat", "plan_M17", "R7 Scout vs R2 housing paper"),
    ("RSP02", "055" + S, "2026-04-18_r18", "repeat", "plan_M17", "R19 Scout vs R18 paper"),
    ("RSP03", "058" + S, "2026-04-19_r19", "repeat", "diagnosis", "R20 Scout vs R19 paper"),
    # Proposed distinct pairs (different topic clusters). Await confirmation.
    ("DSS01", "001" + S, "013" + S, "distinct", "proposed", "housing wealth R1 vs gender R5"),
    ("DSS02", "001" + S, "067" + S, "distinct", "proposed", "housing wealth R1 vs chair allocation R23"),
    ("DSS03", "004" + S, "034" + S, "distinct", "proposed", "housing R2 vs professional background R12"),
    ("DSS04", "007" + S, "013" + S, "distinct", "proposed", "special counsel R3 vs gender R5"),
    ("DSS05", "010" + S, "037" + S, "distinct", "proposed", "crisis accountability R4 vs career vocabulary R13"),
    ("DSS06", "013" + S, "052" + S, "distinct", "proposed", "gender R5 vs party dissolution and exits R18"),
    ("DSS07", "016" + S, "070" + S, "distinct", "proposed", "electoral pathway R6 vs chair allocation R24"),
    ("DSS08", "019" + S, "061" + S, "distinct", "proposed", "housing R7 vs attendance before exit R21"),
    ("DSS09", "025" + S, "064" + S, "distinct", "proposed", "special counsel hearings R9 vs NEC dates R22"),
    ("DSS10", "031" + S, "019" + S, "distinct", "proposed", "bill absorption R11 vs housing R7"),
    ("DSS11", "073" + S, "001" + S, "distinct", "proposed", "confirmation opposition R25 vs housing R1"),
    ("DSS12", "082" + S, "073" + S, "distinct", "proposed", "first-term passage R28 vs confirmation opposition R25"),
    ("DSP01", "001" + S, "2026-04-15_r13", "distinct", "proposed", "housing R1 vs vocabulary paper R13"),
    ("DSP02", "013" + S, "2026-04-06_r10", "distinct", "proposed", "gender R5 vs investigations paper R10"),
    ("DSP03", "007" + S, "2026-04-01_r6", "distinct", "proposed", "special counsel R3 vs quota paper R6"),
    ("DSP04", "052" + S, "2026-03-31_r2", "distinct", "proposed", "exits R18 vs housing paper R2"),
    ("DSP05", "067" + S, "2026-04-05_r8", "distinct", "proposed", "chair allocation R23 vs real estate paper R8"),
    ("DSP06", "034" + S, "2026-04-20_r22", "distinct", "proposed", "professional background R12 vs pre-exit paper R22"),
    ("DSP07", "019" + S, "2026-04-29_r24", "distinct", "proposed", "housing R7 vs chair allocation paper R24"),
    ("DSP08", "073" + S, "2026-04-01_r6", "distinct", "proposed", "confirmation opposition R25 vs quota paper R6"),
    ("DSP09", "082" + S, "2026-03-31_r4", "distinct", "proposed", "first-term passage R28 vs crisis displacement paper R4"),
    ("DSP10", "082" + S, "2026-08-24_r27", "distinct", "proposed", "first-term passage R28 vs confirmation audit paper R27"),
    ("DSP11", "073" + S, "2026-03-31_r2", "distinct", "proposed", "confirmation opposition R25 vs housing paper R2"),
    ("DSP12", "040" + S, "2026-04-15_r13", "distinct", "proposed", "progressive ambition R14 vs vocabulary paper R13"),
    # Same topic inside one Season 2 arc (sensitivity set only).
    ("WSS01", "076" + S, "073" + S, "same_topic_within_arc", "season2_arc4", "R26 vs R25 Scout"),
    ("WSS02", "079" + S, "073" + S, "same_topic_within_arc", "season2_arc4", "R27 vs R25 Scout"),
    ("WSS03", "085" + S, "082" + S, "same_topic_within_arc", "season2_arc5", "R29 vs R28 Scout"),
    ("WSS04", "088" + S, "082" + S, "same_topic_within_arc", "season2_arc5", "R30 vs R28 Scout"),
    ("WSP01", "073" + S, "2026-08-24_r27", "same_topic_within_arc", "season2_arc4", "R25 Scout vs Paper D"),
    ("WSP02", "082" + S, "2026-08-24_r30", "same_topic_within_arc", "season2_arc5", "R28 Scout vs Paper E"),
    ("WSP03", "085" + S, "2026-08-24_r30", "same_topic_within_arc", "season2_arc5", "R29 Scout vs Paper E"),
    ("WSP04", "088" + S, "2026-08-24_r30", "same_topic_within_arc", "season2_arc5", "R30 Scout vs Paper E"),
]

# Season 2 Scout posts and the arc they belong to (start round), plus the
# R19 regression case (Season 1, no arc: every earlier round is prior).
REPLAY_POSTS = [("073" + S, 25), ("076" + S, 25), ("079" + S, 25),
                ("082" + S, 28), ("085" + S, 28), ("088" + S, 28)]
REGRESSION_POSTS = [("055" + S, 19, "R19 Scout vs its prior corpus (includes the R18 paper)")]


# --------------------------------------------------------------------------
# Items and pairs
# --------------------------------------------------------------------------

def _kind(item_id: str) -> str:
    return "scout_post" if item_id.endswith(S) else "article"


def item_path(item_id: str) -> Path:
    if _kind(item_id) == "scout_post":
        return td.FORUM_DIR / f"{item_id}.md"
    return td.ARTICLES_DIR / f"{item_id}.tex"


def item_text(item_id: str) -> str:
    p = item_path(item_id)
    return td.post_text(p) if _kind(item_id) == "scout_post" else td.article_text(p)


def comparison_of(a: str, b: str) -> str:
    kinds = sorted((_kind(a), _kind(b)))
    return {("scout_post", "scout_post"): "scout_scout",
            ("article", "scout_post"): "scout_paper"}.get(tuple(kinds), "paper_paper")


def load_rows(path: Path | None = None) -> list[dict]:
    path = path or CAL_FILE
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


def labeled_pairs(rows: list[dict]) -> list[dict]:
    """Pairs from the file (label store) plus seed pairs it does not have."""
    pairs = {r["pair_id"]: dict(r) for r in rows if r.get("row") == "pair" and r.get("pair_id")}
    for pid, a, b, label, source, note in SEED_PAIRS:
        if pid not in pairs:
            pairs[pid] = {"row": "pair", "pair_id": pid, "a": a, "b": b, "label": label,
                          "source": source, "note": note,
                          "confirmed_by": None}
    for p in pairs.values():
        p["comparison"] = comparison_of(p["a"], p["b"])
    return sorted(pairs.values(), key=lambda p: p["pair_id"])


# --------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------

def auc(pos: list[float], neg: list[float]) -> float | None:
    """P(repeat scores above distinct), ties counted half."""
    if not pos or not neg:
        return None
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def bootstrap_auc(pos: list[float], neg: list[float], n_boot: int = N_BOOT, seed: int = SEED) -> list[float] | None:
    """Percentile 95 percent interval, resampling repeats and distinct pairs separately."""
    if not pos or not neg:
        return None
    rng = random.Random(seed)
    vals = []
    for _ in range(n_boot):
        bp = [rng.choice(pos) for _ in pos]
        bn = [rng.choice(neg) for _ in neg]
        vals.append(auc(bp, bn))
    vals.sort()
    lo = vals[int(0.025 * (n_boot - 1))]
    hi = vals[int(math.ceil(0.975 * (n_boot - 1)))]
    return [round(lo, 3), round(hi, 3)]


def _floor_grid(x: float) -> float:
    return round(math.floor(x / GRID + 1e-9) * GRID, 2)


def _above_grid(x: float) -> float:
    """Smallest grid value strictly above x."""
    return round((math.floor(x / GRID + 1e-9) + 1) * GRID, 2)


def propose(pos: list[float], neg: list[float]) -> dict:
    """warn at or below every repeat, block above every distinct pair and above warn."""
    if not pos or not neg:
        return {"warn": None, "block": None}
    warn = _floor_grid(min(pos))
    block = max(_above_grid(max(neg)), round(warn + GRID, 2))
    return {"warn": warn, "block": block}


def share_at_or_above(xs: list[float], t: float | None) -> float | None:
    if not xs or t is None:
        return None
    return round(sum(x >= t - 1e-12 for x in xs) / len(xs), 3)


def loo(pos: list[float], neg: list[float]) -> dict:
    """Leave-one-out range of the proposed values."""
    warns, blocks = [], []
    for i in range(len(pos)):
        p = propose(pos[:i] + pos[i + 1:], neg)
        warns.append(p["warn"]); blocks.append(p["block"])
    for i in range(len(neg)):
        p = propose(pos, neg[:i] + neg[i + 1:])
        warns.append(p["warn"]); blocks.append(p["block"])
    warns = [w for w in warns if w is not None]
    blocks = [b for b in blocks if b is not None]
    return {"warn_range": [min(warns), max(warns)] if warns else None,
            "block_range": [min(blocks), max(blocks)] if blocks else None,
            "n_distinct_warn_values": len(set(warns)), "n_distinct_block_values": len(set(blocks))}


def summarize(pairs: list[dict], comparison: str, extended: bool) -> dict:
    sel = [p for p in pairs if comparison == "pooled" or p["comparison"] == comparison]
    pos_labels = ("repeat", "same_topic_within_arc") if extended else ("repeat",)
    pos = [p["cosine"] for p in sel if p["label"] in pos_labels]
    neg = [p["cosine"] for p in sel if p["label"] == "distinct"]
    prop = propose(pos, neg)
    distinct_share = share_at_or_above(neg, prop["warn"])
    out = {
        "row": "summary", "comparison": comparison, "set": "extended" if extended else "primary",
        "n_repeat": len(pos), "n_distinct": len(neg),
        "n_distinct_confirmed": sum(1 for p in sel if p["label"] == "distinct" and p.get("confirmed_by")),
        "repeat_scores": sorted(round(x, 3) for x in pos),
        "distinct_scores": sorted(round(x, 3) for x in neg),
        "min_repeat": round(min(pos), 3) if pos else None,
        "max_distinct": round(max(neg), 3) if neg else None,
        "auc": round(auc(pos, neg), 3) if pos and neg else None,
        "auc_ci95": bootstrap_auc(pos, neg),
        "proposed_warn": prop["warn"], "proposed_block": prop["block"],
        "distinct_share_at_or_above_warn": distinct_share,
        "repeat_share_at_or_above_block": share_at_or_above(pos, prop["block"]),
        "criterion_pass": (distinct_share is not None and distinct_share <= MAX_DISTINCT_SHARE),
        "loo": loo(pos, neg) if pos and neg else None,
    }
    return out


# --------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------

def _old_rows() -> dict:
    """Last v1 row per post from knowledge/topic_diversity.jsonl."""
    out = {}
    if td.LOG_FILE.exists():
        for line in td.LOG_FILE.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("model", OLD_MODEL) == OLD_MODEL and r.get("post"):
                out[r["post"]] = r
    return out


def replay(warn: float, block: float, cfg_thresholds: tuple[float, float, str], name: str) -> list[dict]:
    old = _old_rows()
    rows = []
    for stem, arc_start, *note in [(s, a) for s, a in REPLAY_POSTS] + REGRESSION_POSTS:
        path = td.FORUM_DIR / f"{stem}.md"
        rnd = td._round_of(path)
        near = td.nearest(path, rnd, arc_start, name)
        o = old.get(path.name)
        rows.append({
            "row": "replay", "post": path.name, "round": rnd, "arc_start": arc_start,
            "case": "regression" if note else "season2_replay", "note": note[0] if note else None,
            "old": ({"model": OLD_MODEL, "status": o.get("status"), "max_cosine": o.get("max_cosine"),
                     "warn": o.get("warn"), "block": o.get("block")} if o else None),
            "new": {"max_cosine": near["max_cosine"], "nearest_post": near["nearest_post"],
                    "nearest_article": near["nearest_article"], "n_prior": near["n_prior"],
                    "status_at_proposed": td.status_for(near["max_cosine"], warn, block) if warn else None,
                    "status_at_forum_config": td.status_for(near["max_cosine"], cfg_thresholds[0], cfg_thresholds[1]),
                    "forum_config_thresholds": [cfg_thresholds[0], cfg_thresholds[1], cfg_thresholds[2]]},
        })
    return rows


def run(dry_run: bool = False, path: Path | None = None) -> dict:
    path = path or CAL_FILE
    rows = load_rows(path)
    pairs = labeled_pairs(rows)
    name = td.model_name()
    ids = sorted({p["a"] for p in pairs} | {p["b"] for p in pairs})
    missing = [i for i in ids if not item_path(i).exists()]
    if missing:
        print(f"  [Calibrate] skipping pairs with missing files: {', '.join(missing)}")
    ids = [i for i in ids if i not in missing]
    print(f"  [Calibrate] embedding {len(ids)} items with {name} (device {td._device() or 'auto'})...")
    E = td.embed([item_text(i) for i in ids], name)
    idx = {i: k for k, i in enumerate(ids)}
    run_id = datetime.now().strftime("cal_%Y%m%d_%H%M%S")
    scored = []
    for p in pairs:
        if p["a"] in missing or p["b"] in missing:
            continue
        p = dict(p)
        p.update({"cosine": round(float(E[idx[p["a"]]] @ E[idx[p["b"]]]), 4), "model": name,
                  "text_version": td.TEXT_VERSION, "run_id": run_id})
        scored.append(p)

    common = {"run_id": run_id, "ts": datetime.now().isoformat(timespec="seconds"), "model": name,
              "device": td._device() or "auto", "text_version": td.TEXT_VERSION}
    summaries = []
    for extended in (False, True):
        for comp in ("scout_scout", "scout_paper", "pooled"):
            s = summarize(scored, comp, extended)
            s.update(common)
            summaries.append(s)
    primary = next(s for s in summaries if s["comparison"] == "pooled" and s["set"] == "primary")
    warn, block = primary["proposed_warn"], primary["proposed_block"]
    cfg_t = td.thresholds()
    replays = [dict(r, **common) for r in replay(warn, block, cfg_t, name)]
    reg = [r for r in replays if r["case"] == "regression"]
    s2 = [r for r in replays if r["post"] in ("073" + S + ".md", "082" + S + ".md")]
    r19_flags = all(r["new"]["status_at_proposed"] in ("warn", "block") for r in reg)
    openers_clear = all(r["new"]["status_at_proposed"] == "clear" for r in s2)
    approvable = bool(primary["criterion_pass"] and r19_flags and openers_clear)
    rec = dict(common, **{
        "row": "recommendation", "warn": warn, "block": block,
        "basis": "pooled primary set (known repeats vs proposed distinct pairs)",
        "criterion_pass": primary["criterion_pass"],
        "regression_r19_flags": r19_flags,
        "openers_073_082_clear": openers_clear,
        "approval_recommended": approvable,
        "distinct_pairs_confirmed": primary["n_distinct_confirmed"], "distinct_pairs_total": primary["n_distinct"],
        "status": ("provisional, not approved (D-15). Not written to agents.json."
                   + ("" if approvable else " The values FAIL the M17 pass checks and should not be approved.")),
        "approved_by": None,
    })

    _print_report(scored, summaries, replays, rec)
    if not dry_run:
        keep = [r for r in rows if r.get("row") in ("summary", "replay", "recommendation")]
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for r in scored + keep + summaries + replays + [rec]:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"\n  Wrote {path}")
    return {"pairs": scored, "summaries": summaries, "replays": replays, "recommendation": rec}


def _print_report(pairs, summaries, replays, rec) -> None:
    print("\n  Labeled pairs")
    for p in pairs:
        conf = "" if p["label"] != "distinct" else ("  confirmed" if p.get("confirmed_by") else "  (unconfirmed)")
        print(f"  {p['pair_id']}  {p['comparison']:<11} {p['label']:<22} {p['cosine']:.3f}  {p['note']}{conf}")
    print("\n  Separation")
    for s in summaries:
        print(f"  [{s['set']:<8}] {s['comparison']:<11} repeats {s['n_repeat']:>2}  distinct {s['n_distinct']:>2}  "
              f"AUC {s['auc']} CI {s['auc_ci95']}  min repeat {s['min_repeat']}  max distinct {s['max_distinct']}  "
              f"warn {s['proposed_warn']} block {s['proposed_block']}  "
              f"distinct>=warn {s['distinct_share_at_or_above_warn']}  repeats>=block {s['repeat_share_at_or_above_block']}  "
              f"pass {s['criterion_pass']}  LOO {s['loo']}")
    print("\n  Replay (v1 MiniLM status vs v2 at the proposed thresholds)")
    for r in replays:
        o = r["old"] or {}
        n = r["new"]
        print(f"  {r['post']}  arc_start {r['arc_start']}  old {o.get('status')} {o.get('max_cosine')}  ->  "
              f"new max {n['max_cosine']} ({(n['nearest_post'] or {}).get('id')} / {(n['nearest_article'] or {}).get('id')})  "
              f"proposed: {n['status_at_proposed']}  forum_config: {n['status_at_forum_config']}")
    print(f"\n  PROPOSED (provisional, approval recommended: {rec['approval_recommended']}): "
          f"warn {rec['warn']}, block {rec['block']}  "
          f"criterion pass {rec['criterion_pass']}, R19 regression flags {rec['regression_r19_flags']}, "
          f"073/082 clear {rec['openers_073_082_clear']}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Calibrate the topic-diversity guard (M17)")
    ap.add_argument("--dry-run", action="store_true", help="Compute and print without writing the file")
    ap.add_argument("--list", action="store_true", help="Print the labeled pairs and exit")
    args = ap.parse_args()
    if args.list:
        for p in labeled_pairs(load_rows()):
            print(json.dumps({k: p.get(k) for k in ("pair_id", "a", "b", "comparison", "label", "source",
                                                   "confirmed_by", "note")}, ensure_ascii=False))
        return
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())

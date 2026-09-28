#!/usr/bin/env python3
"""Paper D, Version 2 rerun (2026-09-26).

Recomputes every number that Paper D (articles/2026-08-24_r27.tex) reports,
from the stored Arc 4 artifacts, under two codings of cohort 2:

  original      the `opposed` column of workspace/r25/analysis_sample_corrected.csv
                (R25 rule, cohort-2 ruling set {국민의힘, 미래통합당, 국민의당})
  miraehanguk   the Version 2 coding. As original, except that the six cohort-2
                pairs labelled 미래한국당 are coded supportive (ruling bloc).
                미래한국당 was absorbed into 미래통합당 (merger declared
                2020-05-28, party dissolved 2020-05-29), and 미래통합당 was
                renamed 국민의힘 on 2020-09-02, so by the 2023 hearings the
                label belongs to the president's party.
  kna_blocs     kna_blocs.bloc(party, first hearing date of the nominee), used
                only as a cross-check (its table rows are still
                needs_confirmation, so the call passes allow_unconfirmed=True).

Read-only on workspace/r25, workspace/r26 and workspace/dyads21_meta.parquet.
The only files written are results_v2.json and key_values.json next to this
script (and nothing at all when imported by tests/test_r25_rerun.py).

Two layouts. In the repository the inputs are the stored files named above.
Shipped as v2/rerun.py in replication/arc_4, the script reads the files the
package's round scripts rebuild (r25/, r26/, dyads21_meta.parquet and
knowledge/hand_coding/round_26.jsonl under the package root) and writes
v2/results_v2.json and v2/key_values.json. key_values.json holds every
numeric value of results_v2.json under a flat key, which replicate.py verify
compares with the values the repository run produced. The kna_blocs
cross-check needs the forum repository and is skipped in the package.

Estimator (as in workspace/r25/analyze.py and workspace/r26/dose_baseline.py):
OLS with committee fixed effects, standard errors clustered by legislator.
Version 2 clusters on leg_member_uid (the published scripts used leg_name; in
this sample the two give identical numbers, which the script checks). 90
percent intervals are the same fit at alpha = 0.10, as in
workspace/r27/consolidate.py. MDE is 2.8 times the SE, as in
workspace/r25/robust.py.

Run from anywhere:  python3 workspace/redesign_2026-09/v2_work/paper_d/rerun.py
"""

import json
import re
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")

HERE = Path(__file__).resolve().parent
# Package layout: this file is v2/rerun.py next to the package's MANIFEST.json.
PACKAGE = HERE.name == "v2" and (HERE.parent / "MANIFEST.json").exists()
if PACKAGE:
    ROOT = HERE.parent
    SAMPLE = ROOT / "r25/analysis_sample_corrected.csv"
    SNAPSHOT_SAMPLE = ROOT / "r25/analysis_sample.csv"
    ROSTER = ROOT / "r25/roster.csv"
    PANEL = ROOT / "r25/panel.csv"
    BUILD_PY = ROOT / "r25" / "build.py"
    COHORT3 = ROOT / "r26/cohort3_panel.csv"
    DYADS_META = ROOT / "dyads21_meta.parquet"
    DICT26 = ROOT / "knowledge/hand_coding/round_26.jsonl"
    OUT_DIR = HERE
else:
    ROOT = HERE.parents[3]
    R25 = ROOT / "workspace" / "r25"
    R26 = ROOT / "workspace" / "r26"
    SAMPLE = R25 / "analysis_sample_corrected.csv"
    SNAPSHOT_SAMPLE = R25 / "analysis_sample.csv"
    ROSTER = R25 / "roster.csv"
    PANEL = R25 / "panel.csv"
    BUILD_PY = R25 / "build.py"
    COHORT3 = R26 / "cohort3_panel.csv"
    DYADS_META = ROOT / "workspace" / "dyads21_meta.parquet"
    DICT26 = ROOT / "knowledge" / "hand_coding" / "round_26.jsonl"
    OUT_DIR = HERE
CORPUS_DYADS = ROOT / "data" / "dyads_16_22_v9.parquet"
CORPUS_SPEECHES = ROOT / "data" / "all_speeches_16_22_v9.parquet"
OUT = OUT_DIR / "results_v2.json"
FLAT_OUT = OUT_DIR / "key_values.json"

# R25 rule (workspace/r25/recode.py) and the Version 2 rule.
RULING_R25 = {1: {"더불어민주당", "더불어시민당"}, 2: {"국민의힘", "미래통합당", "국민의당"}}
RULING_V2 = {1: set(RULING_R25[1]), 2: RULING_R25[2] | {"미래한국당"}}
AFTER_AUDIT_YEAR = {1: "2021", 2: "2023", 3: "2022"}
CODINGS = ("original", "miraehanguk") if PACKAGE else ("original", "miraehanguk", "kna_blocs")


# ---------------------------------------------------------------------------
# Loading and coding
# ---------------------------------------------------------------------------

def load_sample():
    return pd.read_csv(SAMPLE, dtype={"leg_member_uid": str})


def treat_original(B):
    return B["opposed"].astype(int)


def treat_v2(B):
    t = B["opposed"].astype(int).copy()
    t[(B.cohort == 2) & (B.party == "미래한국당")] = 0
    rule = pd.Series([0 if p in RULING_V2[c] else 1 for c, p in zip(B.cohort, B.party)], index=B.index)
    assert (rule == t).all(), "the Version 2 recode must equal the rule-based coding"
    return t


def hearing_dates():
    """First hearing date per nominee, parsed from the H table in workspace/r25/build.py."""
    text = BUILD_PY.read_text(encoding="utf-8")
    out = {}
    for d, ck, nom, cohort in re.findall(r"\('(\d{4}-\d\d-\d\d)','(\w+)','([^']+)',\[[^\]]*\],(\d)", text):
        if nom not in out or d < out[nom][0]:
            out[nom] = (d, ck, int(cohort))
    return out


def treat_kna_blocs(B):
    sys.path.insert(0, str(ROOT))
    try:
        import kna_blocs
    finally:
        sys.path.remove(str(ROOT))
    dates = hearing_dates()
    vals = []
    for nom, party in zip(B.nominee, B.party):
        d = dates[nom][0]
        side = kna_blocs.bloc(party, d, allow_unconfirmed=True)
        vals.append(1 if side == "opposition" else 0)
    return pd.Series(vals, index=B.index)


# ---------------------------------------------------------------------------
# Estimation
# ---------------------------------------------------------------------------

def fit(S, y, x, cluster="leg_member_uid", scale=100.0):
    m = smf.ols(f"{y} ~ {x} + C(committee_key)", data=S).fit(
        cov_type="cluster", cov_kwds={"groups": S[cluster]})
    b, se = m.params[x] * scale, m.bse[x] * scale
    lo95, hi95 = (m.conf_int(alpha=0.05).loc[x] * scale).tolist()
    lo90, hi90 = (m.conf_int(alpha=0.10).loc[x] * scale).tolist()
    return {"b": b, "se": se, "p": float(m.pvalues[x]), "lo95": lo95, "hi95": hi95,
            "lo90": lo90, "hi90": hi90, "n": int(m.nobs), "clusters": int(S[cluster].nunique())}


def with_treat(B, t):
    S = B.copy()
    S["treat"] = t.values
    return S


def run_coding(B, t):
    S = with_treat(B, t)
    out = {"treat": t}
    out["pooled"] = fit(S, "d_share", "treat")
    out["placebo"] = fit(S, "d_placebo", "treat")
    out["cohort1"] = fit(S[S.cohort == 1], "d_share", "treat")
    out["cohort2"] = fit(S[S.cohort == 2], "d_share", "treat")
    out["mde"] = 2.8 * out["pooled"]["se"]
    return out


def run_all(B):
    out = {"original": run_coding(B, treat_original(B)),
           "miraehanguk": run_coding(B, treat_v2(B))}
    if "kna_blocs" in CODINGS:
        out["kna_blocs"] = run_coding(B, treat_kna_blocs(B))
    return out


def pair_diff(B, t1, t2):
    d = B[t1.values != t2.values][["cohort", "nominee", "committee_key", "leg_member_uid", "party"]].copy()
    d["t1"] = t1[t1.values != t2.values].values
    d["t2"] = t2[t1.values != t2.values].values
    return d


# ---------------------------------------------------------------------------
# Every quantity in the paper
# ---------------------------------------------------------------------------

def tost(e, margin):
    return bool(e["lo90"] > -margin and e["hi90"] < margin)


def secondary_outcomes(S):
    """Table 3 columns 2 and 3 (workspace/r25/robust.py definitions) and column 1."""
    S = S.copy()
    S["cnt_b"] = S.share_before * S.n_before
    S["cnt_a"] = S.share_after * S.n_after
    S["d_logcnt"] = np.log1p(S.cnt_a) - np.log1p(S.cnt_b)
    S["nshare_b"] = S.share_before / (1 - S.unnamed_before)
    S["nshare_a"] = S.share_after / (1 - S.unnamed_after)
    S["d_nshare"] = S.nshare_a - S.nshare_b
    out = {}
    L = S.dropna(subset=["d_logcnt"])
    out["log_count"] = fit(L, "d_logcnt", "treat", scale=1.0)
    N = S.dropna(subset=["d_nshare"])
    out["named_share"] = fit(N, "d_nshare", "treat")
    return out


def dose_frame(B, key="leg_member_uid"):
    R = pd.read_csv(ROSTER, dtype={"leg_member_uid": str})
    R = R[R.cohort > 0].copy()
    R["ministry"] = R.committee_key + "|" + R.nominee.replace({"변창흠": "노형욱"})
    dose = R.groupby(["cohort", key, "ministry"]).n_q.sum().reset_index().rename(columns={"n_q": "dose"})
    D = B.merge(dose, on=["cohort", key, "ministry"], how="left")
    assert len(D) == len(B) and D.dose.notna().all()
    D["dose_z"] = D.groupby(["cohort", "committee_key"]).dose.transform(
        lambda s: (s - s.mean()) / s.std(ddof=0))
    return D


def dose_block(D, t):
    """Table 5. D carries dose and dose_z (standardized over all pairs, as in
    workspace/r26/dose_baseline.py). The log-dose column is not in a saved round
    script. log(1 + count) standardized within cohort-committee cells among
    opposition pairs reproduces the published value under the original coding,
    and that definition is used here."""
    S = with_treat(D, t)
    S = S[S.treat == 1].copy()
    S["ldose"] = np.log1p(S.dose)
    S["ldose_z"] = S.groupby(["cohort", "committee_key"]).ldose.transform(
        lambda s: (s - s.mean()) / s.std(ddof=0))
    S["top"] = S.groupby(["cohort", "committee_key"]).dose.transform(
        lambda s: (s >= s.quantile(2 / 3)).astype(int))
    c1 = S[S.cohort == 1]
    out = {
        "pooled_z": fit(S, "d_share", "dose_z"),
        "cohort1_z": fit(c1, "d_share", "dose_z"),
        "pooled_logdose": fit(S, "d_share", "ldose_z"),
        "cohort1_raw": fit(c1, "d_share", "dose"),
        "pooled_raw": fit(S, "d_share", "dose"),
        "placebo_z": fit(S, "d_placebo", "dose_z"),
        "excl_gender_family_z": fit(S[S.committee_key != "gender_family"], "d_share", "dose_z"),
        "top_tercile_pooled": fit(S, "d_share", "top"),
        "top_tercile_cohort1": fit(c1, "d_share", "top"),
    }
    out["mde_pooled_z"] = 2.8 * out["pooled_z"]["se"]
    out["n_opposition"] = int(len(S))
    return out


def levels_block(B, t):
    S = with_treat(B, t)
    c1 = S[S.cohort == 1]
    gf = c1[c1.committee_key == "gender_family"]
    raw = lambda X: 100 * (X[X.treat == 1].share_before.mean() - X[X.treat == 0].share_before.mean())
    return {
        "cohort1": fit(c1, "share_before", "treat"),
        "pooled": fit(S, "share_before", "treat"),
        "pooled_placebo": fit(S, "placebo_before", "treat"),
        "raw_gap_cohort1": raw(c1),
        "raw_gap_cohort1_excl_gf": raw(c1[c1.committee_key != "gender_family"]),
        "gf_cohort1_mean_share_before": float(gf.share_before.mean()),
        "gf_cohort1_pairs": int(len(gf)),
        "gf_cohort1_opposed": int(gf.treat.sum()),
    }


def retention(coding):
    """Share of legislator-ministry units present in both audits, by side (panel.csv)."""
    P = pd.read_csv(PANEL, dtype={"leg_member_uid": str})
    P["ministry"] = P.committee_key + "|" + P.nominee.replace({"변창흠": "노형욱"})
    P = P.sort_values("nominee").drop_duplicates(["cohort", "leg_name", "ministry"], keep="last")
    P = P[P.party != "무소속"].copy()
    rule = RULING_V2 if coding == "miraehanguk" else RULING_R25
    P["treat"] = [0 if p in rule[c] else 1 for c, p in zip(P.cohort, P.party)]
    g = P.groupby("treat").in_both.agg(["mean", "size"])
    c2 = P[P.cohort == 2]
    return {"opposed_rate": float(g.loc[1, "mean"]), "opposed_units": int(g.loc[1, "size"]),
            "supportive_rate": float(g.loc[0, "mean"]), "supportive_units": int(g.loc[0, "size"]),
            "cohort2_units": int(len(c2)),
            "cohort2_disagree_with_snapshot": int((c2.treat != c2.opposed_party).sum())}


def snapshot_retention():
    """Retention as workspace/r25/robust.py computed it (term-snapshot opposed_party, the
    source of the Version 1 Table 1 retention rows)."""
    P = pd.read_csv(PANEL, dtype={"leg_member_uid": str})
    P["ministry"] = P.committee_key + "|" + P.nominee.replace({"변창흠": "노형욱"})
    P = P.sort_values("nominee").drop_duplicates(["cohort", "leg_name", "ministry"], keep="last")
    P = P[P.ruling != "independent"]
    g = P.groupby("opposed_party").in_both.agg(["mean", "size"])
    return {"opposed_rate": float(g.loc[1, "mean"]), "opposed_units": int(g.loc[1, "size"]),
            "supportive_rate": float(g.loc[0, "mean"]), "supportive_units": int(g.loc[0, "size"])}


def audit_gaps():
    """Days from each nominee's first hearing to the first post-hearing audit day of its committee."""
    d = pd.read_parquet(DYADS_META, columns=["committee_key", "hearing_type", "date", "witness_name",
                                             "witness_role", "agenda"])
    a = d[d.hearing_type == "국정감사"]
    start = a.assign(year=a.date.str[:4]).groupby(["committee_key", "year"]).date.min().to_dict()
    rows = []
    for nom, (hd, ck, cohort) in hearing_dates().items():
        if cohort == 0:
            continue
        ad = start[(ck, AFTER_AUDIT_YEAR[cohort])]
        rows.append({"cohort": cohort, "nominee": nom, "hearing": hd, "audit_start": ad,
                     "days": (pd.Timestamp(ad) - pd.Timestamp(hd)).days})
    P3 = pd.read_csv(COHORT3)
    q = d[(d.date >= "2022-04-20") & (d.date <= "2022-05-31") & (d.hearing_type == "상임위원회")
          & d.agenda.str.contains("인사청문", na=False) & (d.witness_role == "minister_nominee")]
    first = q.groupby("witness_name").date.min()
    for nom, ck in P3[P3.withdrawn == 0].drop_duplicates("nominee")[["nominee", "committee_key"]].values:
        ad = start[(ck, "2022")]
        rows.append({"cohort": 3, "nominee": nom, "hearing": first[nom], "audit_start": ad,
                     "days": (pd.Timestamp(ad) - pd.Timestamp(first[nom])).days})
    G = pd.DataFrame(rows)
    return {int(c): {"min_days": int(g.days.min()), "max_days": int(g.days.max()),
                     "min_months": round(g.days.min() / 30.44, 1), "max_months": round(g.days.max() / 30.44, 1),
                     "nominees": int(len(g))}
            for c, g in G.groupby("cohort")}, G


def corpus_totals():
    import pyarrow.parquet as pq
    out = {}
    for k, p in (("dyads", CORPUS_DYADS), ("speech_acts", CORPUS_SPEECHES)):
        out[k] = pq.ParquetFile(p).metadata.num_rows if p.exists() else None
    return out


def descriptives(B, t, D):
    R = pd.read_csv(ROSTER, dtype={"leg_member_uid": str})
    P3 = pd.read_csv(COHORT3)
    S3 = P3[P3.in_both]
    S = with_treat(D, t)
    c1opp = S[(S.cohort == 1) & (S.treat == 1)]
    with open(DICT26, encoding="utf-8") as f:
        d26 = [json.loads(l) for l in f if l.strip()]
    return {
        "roster_rows_c1c2": int(len(R)),
        "roster_rows_c1c2_withdrawn": int((R.cohort == 0).sum()),
        "roster_rows_c3": len(d26),
        "roster_rows_c3_withdrawn": sum(int(r["withdrawn"]) for r in d26),
        "pairs_pooled": int(len(B)), "clusters_pooled": int(B.leg_member_uid.nunique()),
        "clusters_by_name": int(B.leg_name.nunique()),
        "pairs_cohort1": int((B.cohort == 1).sum()), "pairs_cohort2": int((B.cohort == 2).sum()),
        "pairs_cohort3": int(len(S3)), "cohort3_supportive": int((S3.opposed == 0).sum()),
        "cohort3_opposed": int((S3.opposed == 1).sum()),
        "cohort1_opposed": int(S[(S.cohort == 1)].treat.sum()),
        "cohort1_supportive": int((S[(S.cohort == 1)].treat == 0).sum()),
        "cohort2_opposed": int(S[(S.cohort == 2)].treat.sum()),
        "cohort2_supportive": int((S[(S.cohort == 2)].treat == 0).sum()),
        "dose_median_c1_opp": float(c1opp.dose.median()),
        "dose_q25_c1_opp": float(c1opp.dose.quantile(0.25)),
        "dose_q75_c1_opp": float(c1opp.dose.quantile(0.75)),
        "speech_coded_opposed_pairs": int(B.opposed_speech.sum()),
        "speech_vs_party_agree_pairs": int((B.opposed_speech.values == t.values).sum()),
    }


def homonym_check(B, t):
    Dn = dose_frame(B, key="leg_name").sort_values(["cohort", "leg_member_uid", "ministry"])
    Du = dose_frame(B, key="leg_member_uid").sort_values(["cohort", "leg_member_uid", "ministry"])
    diff = Du[Dn.dose.values != Du.dose.values]
    tt = with_treat(B, t).set_index(["cohort", "leg_member_uid", "ministry"]).treat
    return {"rows_with_different_dose": int(len(diff)),
            "those_rows_opposed": [int(tt.loc[(c, u, m)]) for c, u, m in
                                   diff[["cohort", "leg_member_uid", "ministry"]].values]}


def paper_quantities():
    B = load_sample()
    res = {"inputs": {p.name: str(p.relative_to(ROOT)) for p in
                      (SAMPLE, SNAPSHOT_SAMPLE, ROSTER, PANEL, COHORT3, DICT26)}}
    allc = run_all(B)
    res["cluster_check_uid_equals_name"] = all(
        abs(fit(with_treat(B, allc[c]["treat"]), "d_share", "treat", cluster="leg_name")["se"]
            - allc[c]["pooled"]["se"]) < 1e-9 for c in CODINGS)
    res["pair_diff_original_vs_v2"] = pair_diff(B, allc["original"]["treat"],
                                                allc["miraehanguk"]["treat"]).to_dict("records")
    if "kna_blocs" in allc:
        res["pair_diff_v2_vs_kna_blocs"] = len(pair_diff(B, allc["miraehanguk"]["treat"],
                                                         allc["kna_blocs"]["treat"]))
    D = dose_frame(B)
    for c in ("original", "miraehanguk"):
        t = allc[c]["treat"]
        S = with_treat(B, t)
        r = {k: v for k, v in allc[c].items() if k != "treat"}
        r["tost"] = {f"{w}_{m}": tost(r[w], m) for w in ("pooled", "placebo") for m in (5.0, 2.5)}
        r["main_minus_placebo_abs"] = abs(r["pooled"]["b"] - r["placebo"]["b"])
        r["own_speech"] = fit(S.assign(treat=S.opposed_speech), "d_share", "treat")
        r["secondary"] = secondary_outcomes(S)
        r["levels"] = levels_block(B, t)
        r["dose"] = dose_block(D, t)
        r["retention"] = retention(c)
        r["descriptives"] = descriptives(B, t, D)
        r["homonym"] = homonym_check(B, t)
        res[c] = r
    # Published Table 3 columns 2 and 3 were computed on the term-snapshot coding.
    A = pd.read_csv(SNAPSHOT_SAMPLE, dtype={"leg_member_uid": str})
    res["snapshot_table3"] = secondary_outcomes(A.assign(treat=A.opposed_party))
    res["snapshot_retention"] = snapshot_retention()
    P3 = pd.read_csv(COHORT3, dtype={"leg_member_uid": str})
    S3 = P3[P3.in_both].rename(columns={"opposed": "treat"})
    res["cohort3"] = {"main": fit(S3, "d_share", "treat"), "placebo": fit(S3, "d_placebo", "treat")}
    gaps, _ = audit_gaps()
    res["audit_gaps"] = gaps
    res["corpus"] = corpus_totals()
    return res


def _jsonable(o):
    if isinstance(o, dict):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def flat_values(res):
    """Every numeric value of results_v2.json under a flat key joined by "/",
    except the file names in "inputs" and the kna_blocs cross-check, which
    needs the forum repository. Booleans become 0 or 1, NaN is dropped."""
    out = {}

    def walk(o, key):
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{key}/{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{key}/{i}")
        elif isinstance(o, bool):
            out[key] = int(o)
        elif isinstance(o, (int, float)) and o == o:
            out[key] = o

    for k, v in res.items():
        if k == "inputs" or "kna_blocs" in k:
            continue
        walk(v, k)
    return out


def main():
    res = _jsonable(paper_quantities())
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    FLAT_OUT.write_text(json.dumps(flat_values(res), ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                        encoding="utf-8")
    v2, o = res["miraehanguk"], res["original"]
    f = lambda e: f"{e['b']:+.2f} ({e['se']:.2f}) p={e['p']:.3f} 95% [{e['lo95']:+.2f}, {e['hi95']:+.2f}] N={e['n']}/{e['clusters']}"
    print("cluster uid == name:", res["cluster_check_uid_equals_name"])
    print("pairs recoded original -> v2:", len(res["pair_diff_original_vs_v2"]),
          "| v2 vs kna_blocs differing pairs:", res.get("pair_diff_v2_vs_kna_blocs", "not run"))
    for lab, r in (("original", o), ("v2", v2)):
        print(f"== {lab}")
        for k in ("pooled", "placebo", "cohort1", "cohort2"):
            print(f"  {k:10s}", f(r[k]))
        print("  MDE", round(r["mde"], 2), "| TOST", r["tost"], "| |main-placebo|", round(r["main_minus_placebo_abs"], 3))
        print("  90% main", round(r["pooled"]["lo90"], 2), round(r["pooled"]["hi90"], 2),
              "placebo", round(r["placebo"]["lo90"], 2), round(r["placebo"]["hi90"], 2))
        print("  own speech", f(r["own_speech"]))
        print("  log count", f(r["secondary"]["log_count"]), "| named share", f(r["secondary"]["named_share"]))
        for k, e in r["levels"].items():
            print("  levels", k, f(e) if isinstance(e, dict) else round(e, 3))
        for k, e in r["dose"].items():
            print("  dose", k, f(e) if isinstance(e, dict) else round(e, 3) if isinstance(e, float) else e)
        print("  retention", r["retention"])
        print("  descriptives", r["descriptives"])
        print("  homonym", r["homonym"])
    print("snapshot Table 3:", f(res["snapshot_table3"]["log_count"]), "|", f(res["snapshot_table3"]["named_share"]))
    print("snapshot retention:", res["snapshot_retention"])
    print("cohort 3:", f(res["cohort3"]["main"]), "| placebo", f(res["cohort3"]["placebo"]))
    print("audit gaps:", res["audit_gaps"])
    print("corpus:", res["corpus"])
    print("wrote", OUT.relative_to(ROOT), "and", FLAT_OUT.relative_to(ROOT))


if __name__ == "__main__":
    main()

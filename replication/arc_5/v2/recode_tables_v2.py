# Paper E version 2: headline estimates under two codings of first-term status.
#
#   lifetime  first_term as in Version 1, reelection == '초선' in the KNA member
#             files. The KNA codebook documents reelection as lifetime seniority
#             at the time of collection, so for the 17th-21st Assemblies it marks
#             members whose whole career (to the collection date) is one term.
#   assembly  first-term status at the Assembly, term_number == 1, derived from
#             the same member files by seniority_check.py (lifetime count minus
#             the member's terms in the 17th-22nd, plus the rank of the Assembly
#             among them). It matches the KNA term_number field for all 1,933
#             member-terms.
#
# Models copy workspace/r29/depth.py (block 6: year-1 strict gap and TOST;
# block 5: member-period cells; block 8: per-assembly step), workspace/r29/depth2.py
# (mA step with flexible year effects, mC per-year interactions, drop-22nd) and
# workspace/r28/analyze.py (linear strict interaction, use_t=True). Nothing else
# changes between the two codings.
#
# Run from the replication package root after r28/build.py and v2/seniority_check.py:
#   KBL_DATA=<kna processed dir> python3 v2/recode_tables_v2.py
# PAPER_E_PANEL and PAPER_E_OUT override the panel path and the output folder.
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

PANEL = Path(os.environ.get("PAPER_E_PANEL", "r28/bills_panel.csv"))
OUTDIR = Path(os.environ.get("PAPER_E_OUT", "v2"))
FE = ' + C(assembly) + C(bloc) + C(election_type) + C(committee_nm)'
CL = lambda d: {'groups': d['rst_mona_cd']}

p = pd.read_csv(PANEL)
s = pd.read_csv(OUTDIR / 'seniority_derived.csv')
p = p.merge(s[['mona_cd', 'assembly', 'term_number_derived', 'L']],
            left_on=['rst_mona_cd', 'assembly'], right_on=['mona_cd', 'assembly'],
            how='left', validate='m:1')
assert p['term_number_derived'].notna().all()
p['ft_lifetime'] = p['first_term']
p['ft_assembly'] = (p['term_number_derived'] == 1).astype(int)
assert ((p.ft_lifetime == 1) <= (p.ft_assembly == 1)).all()

R = {"counts": {
    "bills": int(len(p)),
    "bills_ft_lifetime": int(p.ft_lifetime.sum()),
    "bills_ft_assembly": int(p.ft_assembly.sum()),
    "bills_ft_assembly_later_reelected": int(((p.ft_assembly == 1) & (p.ft_lifetime == 0)).sum()),
    "strict_rate": float(p.passed_strict.mean()),
}}
mem = s.copy()
mem['ft_assembly'] = (mem.term_number_derived == 1).astype(int)
R["counts"]["members_by_assembly"] = {
    str(a): {"member_terms": int((g.assembly == a).sum()), "ft_lifetime": int(g.ft_reelection.sum()),
             "ft_assembly": int(g.ft_assembly.sum())}
    for a, g in mem.groupby('assembly')}

df = p[p['committee_nm'].notna()].copy()
df['absorbed'] = ((df['passed_absorb'] == 1) & (df['passed_strict'] == 0)).astype(int)
df['late'] = (df['prop_year'] >= 2).astype(int)
df['py_c'] = df['prop_year'] - 1


def rec(m, term, d=None):
    out = {"est": float(m.params[term]) * 100, "se": float(m.bse[term]) * 100,
           "p": float(m.pvalues[term]), "n": int(m.nobs)}
    if d is not None:
        out["clusters"] = int(d['rst_mona_cd'].nunique())
    return out


for code in ('ft_lifetime', 'ft_assembly'):
    d = df.copy()
    d['first_term'] = d[code]
    r = {}
    r["cells_strict"] = {f"{y}_{c}": float(v) for (y, c), v in
                         d.groupby(['prop_year', 'first_term'])['passed_strict'].mean().items()}
    r["cells_absorbed"] = {f"{y}_{c}": float(v) for (y, c), v in
                           d.groupby(['prop_year', 'first_term'])['absorbed'].mean().items()}
    y1 = d[d.prop_year == 1]
    m1 = smf.ols('passed_strict ~ first_term' + FE, y1).fit(cov_type='cluster', cov_kwds=CL(y1))
    r["y1_strict_gap"] = rec(m1, 'first_term', y1)
    b, se = m1.params['first_term'], m1.bse['first_term']
    r["y1_strict_gap"]["tost_2pp_max_p"] = float(max(1 - stats.norm.cdf((b + 0.02) / se),
                                                     1 - stats.norm.cdf((0.02 - b) / se)))
    r["y1_strict_gap"]["tost_1pp_max_p"] = float(max(1 - stats.norm.cdf((b + 0.01) / se),
                                                     1 - stats.norm.cdf((0.01 - b) / se)))
    r["y1_strict_gap"]["ci90"] = [float(b - 1.6448536 * se) * 100, float(b + 1.6448536 * se) * 100]
    ms = smf.ols('passed_strict ~ first_term * py_c' + FE, d).fit(
        cov_type='cluster', cov_kwds=CL(d), use_t=True)
    r["strict_linear_interaction"] = rec(ms, 'first_term:py_c', d)
    mA = smf.ols('absorbed ~ first_term + C(prop_year) + first_term:late' + FE, d).fit(
        cov_type='cluster', cov_kwds=CL(d))
    r["absorb_year1"] = rec(mA, 'first_term', d)
    r["absorb_step"] = rec(mA, 'first_term:late', d)
    mB = smf.ols('absorbed ~ first_term + C(prop_year) + first_term:prop_year' + FE, d).fit(
        cov_type='cluster', cov_kwds=CL(d))
    r["absorb_linear"] = rec(mB, 'first_term:prop_year', d)
    r["bic_step_minus_linear"] = float(mA.bic - mB.bic)
    mC = smf.ols('absorbed ~ first_term*C(prop_year)' + FE, d).fit(cov_type='cluster', cov_kwds=CL(d))
    for y in (2, 3, 4):
        r[f"absorb_year{y}"] = rec(mC, f'first_term:C(prop_year)[T.{y}]', d)
    w = mC.wald_test('first_term:C(prop_year)[T.2] = first_term:C(prop_year)[T.3], '
                     'first_term:C(prop_year)[T.3] = first_term:C(prop_year)[T.4]', scalar=True)
    r["absorb_years_equal_wald_p"] = float(w.pvalue)
    d21 = d[d.assembly <= 21]
    m21 = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, d21).fit(
        cov_type='cluster', cov_kwds=CL(d21))
    r["absorb_step_lateonly_excl22"] = rec(m21, 'first_term:late', d21)
    mst = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, d).fit(
        cov_type='cluster', cov_kwds=CL(d))
    r["absorb_step_lateonly"] = rec(mst, 'first_term:late', d)
    cells = d.groupby(['assembly', 'rst_mona_cd', 'first_term', 'late']).agg(
        absorbed=('absorbed', 'mean'), n=('absorbed', 'size'),
        bloc=('bloc', 'first'), election_type=('election_type', 'first')).reset_index()
    c3 = cells[cells['n'] >= 3]
    m4 = smf.ols('absorbed ~ first_term + late + first_term:late + C(assembly) + C(bloc)'
                 ' + C(election_type)', c3).fit(cov_type='cluster', cov_kwds={'groups': c3['rst_mona_cd']})
    r["absorb_step_member_cells"] = rec(m4, 'first_term:late', c3)
    for a in range(17, 23):
        da = d[d.assembly == a]
        ma = smf.ols('absorbed ~ first_term + late + first_term:late + C(bloc) + C(election_type)'
                     ' + C(committee_nm)', da).fit(cov_type='cluster', cov_kwds=CL(da))
        r[f"absorb_step_A{a}"] = rec(ma, 'first_term:late', da)
        ms_a = smf.ols('passed_strict ~ first_term * py_c + C(bloc) + C(election_type) + C(committee_nm)',
                       da).fit(cov_type='cluster', cov_kwds=CL(da), use_t=True)
        r[f"strict_interaction_A{a}"] = rec(ms_a, 'first_term:py_c', da)
    R[code] = r
    print(f"\n== {code}")
    for k, v in r.items():
        if isinstance(v, dict) and "est" in v:
            print(f"  {k:<32} {v['est']:+.2f} (SE {v['se']:.2f}) p={v['p']:.3f} N={v['n']}"
                  + (f" cl={v['clusters']}" if 'clusters' in v else ""))
    print("  y1 TOST 2pp/1pp:", r["y1_strict_gap"]["tost_2pp_max_p"], r["y1_strict_gap"]["tost_1pp_max_p"],
          "BIC step-linear", r["bic_step_minus_linear"], "Wald", r["absorb_years_equal_wald_p"])

(OUTDIR / 'recode_tables_v2.json').write_text(json.dumps(R, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(json.dumps(R["counts"], ensure_ascii=False))

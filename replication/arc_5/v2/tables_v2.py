# Paper E version 2: recompute every table entry with its uncertainty and N.
#
# Inputs (read only):
#   workspace/r28/bills_panel.csv   the committed R28 analysis panel (93,572 bills)
#   $KBL_DATA/master_bills_{17..22}.parquet, members_{17..22}.parquet,
#   $KBL_DATA/cosponsorship_edges.parquet
# Every model below copies the specification of the round script named in its
# comment (workspace/r28/robust.py, workspace/r29/depth.py, workspace/r29/depth2.py,
# workspace/r30/mechanisms.py, workspace/r30/mechanisms2.py): same sample
# filters, same formula, same clustering (lead-sponsor uid), same covariance
# options. Nothing is re-specified. Where a round script printed a point estimate
# only, the SE comes from the same fitted model. The two raw cell double
# differences are reproduced exactly by the saturated 2x2 regression (unweighted
# or weighted), whose clustered SE is reported.
#
# Run from the replication package root (replication/arc_5) after r28/build.py:
#   KBL_DATA=<kna processed dir> python3 v2/tables_v2.py
# PAPER_E_PANEL and PAPER_E_OUT override the panel path and the output folder.
# Output: v2/tables_v2.json
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

DATA = os.environ["KBL_DATA"]
PANEL = Path(os.environ.get("PAPER_E_PANEL", "r28/bills_panel.csv"))
OUT = Path(os.environ.get("PAPER_E_OUT", "v2")) / "tables_v2.json"
TERM_START = {17: '2004-05-30', 18: '2008-05-30', 19: '2012-05-30',
              20: '2016-05-30', 21: '2020-05-30', 22: '2024-05-30'}
FE = ' + C(assembly) + C(bloc) + C(election_type) + C(committee_nm)'
CL = lambda d: {'groups': d['rst_mona_cd']}

R = {}


def put(key, m, term, *, n=None, clusters=None, extra=None, scale=100.0):
    """Store a coefficient (x100, percentage points), its SE, p and N."""
    rec = {"est": float(m.params[term]) * scale, "se": float(m.bse[term]) * scale,
           "p": float(m.pvalues[term]), "n": int(m.nobs) if n is None else int(n)}
    if clusters is not None:
        rec["clusters"] = int(clusters)
    if extra:
        rec.update(extra)
    R[key] = rec
    print(f"{key:<48} {rec['est']:+.3f} (SE {rec['se']:.3f}) p={rec['p']:.4f} N={rec['n']}"
          + (f" clusters={rec['clusters']}" if 'clusters' in rec else ""))
    return rec


# ---------------------------------------------------------------------------
# Panel (same filters as workspace/r29/depth.py)
# ---------------------------------------------------------------------------
raw = pd.read_csv(PANEL)
R["panel_rows"] = int(len(raw))
R["strict_rate_pooled"] = float(raw.passed_strict.mean())
R["inclusive_rate_pooled"] = float(raw.passed_absorb.mean())
df = raw[raw['committee_nm'].notna()].copy()
R["estimation_rows"] = int(len(df))
df['absorbed'] = ((df['passed_absorb'] == 1) & (df['passed_strict'] == 0)).astype(int)
df['late'] = (df['prop_year'] >= 2).astype(int)
R["absorbed_only_rate_pooled"] = float(df['absorbed'].mean())
R["clusters_estimation"] = int(df['rst_mona_cd'].nunique())
print("panel rows", len(raw), "estimation rows", len(df), "clusters", df.rst_mona_cd.nunique())

# ---------------------------------------------------------------------------
# Table 2
# ---------------------------------------------------------------------------
# Column 1: workspace/r29/depth.py block 6 (year-1 strict gap, TOST)
y1s = df[df['prop_year'] == 1]
m1 = smf.ols('passed_strict ~ first_term' + FE, y1s).fit(cov_type='cluster', cov_kwds=CL(y1s))
b, se = m1.params['first_term'], m1.bse['first_term']
tost2 = max(1 - stats.norm.cdf((b + 0.02) / se), 1 - stats.norm.cdf((0.02 - b) / se))
tost1 = max(1 - stats.norm.cdf((b + 0.01) / se), 1 - stats.norm.cdf((0.01 - b) / se))
put("t2_c1_first_term", m1, 'first_term', clusters=y1s.rst_mona_cd.nunique(),
    extra={"tost_2pp_max_p": float(tost2), "tost_1pp_max_p": float(tost1)})

# Column 2: workspace/r29/depth2.py model mA (step with flexible year effects)
mA = smf.ols('absorbed ~ first_term + C(prop_year) + first_term:late' + FE, df).fit(
    cov_type='cluster', cov_kwds=CL(df))
put("t2_c2_first_term", mA, 'first_term', clusters=df.rst_mona_cd.nunique())
put("t2_c2_ft_x_late", mA, 'first_term:late', clusters=df.rst_mona_cd.nunique())
mB = smf.ols('absorbed ~ first_term + C(prop_year) + first_term:prop_year' + FE, df).fit(
    cov_type='cluster', cov_kwds=CL(df))
R["bic_step_minus_linear"] = float(mA.bic - mB.bic)
print("BIC step - linear", R["bic_step_minus_linear"])

# Column 3: workspace/r29/depth2.py model mC (per-year interactions)
mC = smf.ols('absorbed ~ first_term*C(prop_year)' + FE, df).fit(cov_type='cluster', cov_kwds=CL(df))
put("t2_c3_first_term", mC, 'first_term', clusters=df.rst_mona_cd.nunique())
for y in (2, 3, 4):
    put(f"t2_c3_ft_x_year{y}", mC, f'first_term:C(prop_year)[T.{y}]',
        clusters=df.rst_mona_cd.nunique())
w = mC.wald_test('first_term:C(prop_year)[T.2] = first_term:C(prop_year)[T.3], '
                 'first_term:C(prop_year)[T.3] = first_term:C(prop_year)[T.4]', scalar=True)
R["t2_c3_wald_equal_p"] = float(w.pvalue)
print("Wald years 2-4 equal p", R["t2_c3_wald_equal_p"])

# Step model with a single late indicator: workspace/r29/depth.py block 1 (m_step)
m_step = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, df).fit(
    cov_type='cluster', cov_kwds=CL(df))
put("step_lateonly_first_term", m_step, 'first_term', clusters=df.rst_mona_cd.nunique())
put("step_lateonly_ft_x_late", m_step, 'first_term:late', clusters=df.rst_mona_cd.nunique())

# Column 4: workspace/r29/depth.py block 5 (member-period cells, n >= 3)
cells = df.groupby(['assembly', 'rst_mona_cd', 'first_term', 'late']).agg(
    absorbed=('absorbed', 'mean'), n=('absorbed', 'size'),
    bloc=('bloc', 'first'), election_type=('election_type', 'first')).reset_index()
c3 = cells[cells['n'] >= 3]
m4 = smf.ols('absorbed ~ first_term + late + first_term:late + C(assembly) + C(bloc)'
             ' + C(election_type)', c3).fit(cov_type='cluster', cov_kwds={'groups': c3['rst_mona_cd']})
put("t2_c4_ft_x_late", m4, 'first_term:late', clusters=c3.rst_mona_cd.nunique(),
    extra={"unit": "member-period cells with at least 3 bills",
           "bills_in_cells": int(c3['n'].sum())})
put("t2_c4_first_term", m4, 'first_term', clusters=c3.rst_mona_cd.nunique())

# ---------------------------------------------------------------------------
# Table 3 (robustness), workspace/r29/depth.py and depth2.py
# ---------------------------------------------------------------------------
w_ = np.ones(len(df))
for a in df['assembly'].unique():
    sub = df['assembly'] == a
    re_mix = df[sub & (df['first_term'] == 0)]['committee_nm'].value_counts(normalize=True)
    ft_mix = df[sub & (df['first_term'] == 1)]['committee_nm'].value_counts(normalize=True)
    ratio = (re_mix / ft_mix).reindex(df.loc[sub, 'committee_nm']).fillna(0).values
    w_[sub.values] = np.where(df.loc[sub, 'first_term'] == 1, ratio, 1.0)
df['w_krutz'] = np.clip(w_, 0, 10)
m_kw = smf.wls('absorbed ~ first_term + late + first_term:late' + FE, df,
               weights=df['w_krutz']).fit(cov_type='cluster', cov_kwds=CL(df))
put("t3_reweighted", m_kw, 'first_term:late', clusters=df.rst_mona_cd.nunique())


def dd(d, wcol=None):
    g = d.groupby(['first_term', 'late']).apply(
        lambda x: np.average(x['absorbed'], weights=x[wcol] if wcol else None),
        include_groups=False)
    return ((g[1, 1] - g[1, 0]) - (g[0, 1] - g[0, 0])) * 100


R["t3_raw_dd_cellmeans"] = float(dd(df))
R["t3_raw_dd_rw_cellmeans"] = float(dd(df, 'w_krutz'))
m_dd0 = smf.ols('absorbed ~ first_term + late + first_term:late', df).fit(
    cov_type='cluster', cov_kwds=CL(df))
put("t3_raw_dd", m_dd0, 'first_term:late', clusters=df.rst_mona_cd.nunique())
m_dd1 = smf.wls('absorbed ~ first_term + late + first_term:late', df, weights=df['w_krutz']).fit(
    cov_type='cluster', cov_kwds=CL(df))
put("t3_raw_dd_rw", m_dd1, 'first_term:late', clusters=df.rst_mona_cd.nunique())
print("cell-mean DD check", R["t3_raw_dd_cellmeans"], R["t3_raw_dd_rw_cellmeans"])

# Late-starter exclusion (depth.py block 7)
first_act = df.groupby(['assembly', 'rst_mona_cd']).agg(
    first_bill_months=('months_in', 'min'), ft=('first_term', 'first')).reset_index()
late_starters = first_act[(first_act['ft'] == 1) & (first_act['first_bill_months'] > 12)]
R["late_starters"] = int(len(late_starters))
R["first_term_sponsor_terms"] = int((first_act.ft == 1).sum())
core = df[~df.set_index(['assembly', 'rst_mona_cd']).index.isin(
    late_starters.set_index(['assembly', 'rst_mona_cd']).index)]
m_c = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, core).fit(
    cov_type='cluster', cov_kwds=CL(core))
put("t3_excl_late_starters", m_c, 'first_term:late', clusters=core.rst_mona_cd.nunique())
m_s = smf.ols('passed_strict ~ first_term * prop_year' + FE, core).fit(
    cov_type='cluster', cov_kwds=CL(core))
put("strict_linear_excl_late_starters", m_s, 'first_term:prop_year')

# Drop the 22nd (depth2.py)
d21 = df[df['assembly'] <= 21]
m21 = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, d21).fit(
    cov_type='cluster', cov_kwds=CL(d21))
put("t3_excl_22nd", m21, 'first_term:late', clusters=d21.rst_mona_cd.nunique())

# Coalition-size bins (depth.py block 4)
edges_b = pd.read_parquet(f'{DATA}/cosponsorship_edges.parquet', columns=['bill_id'])
nco = edges_b.groupby('bill_id').size().rename('n_sponsors')
df2 = df.merge(nco, on='bill_id', how='left')
R["edge_coverage_by_assembly"] = {str(k): float(v) for k, v in
                                  df2.groupby('assembly')['n_sponsors'].apply(lambda s: s.notna().mean()).items()}
df2 = df2[df2['n_sponsors'].notna()].copy()
df2['bin'] = pd.cut(df2['n_sponsors'], [0, 10, 15, 30, 1000], labels=['<=10', '11-15', '16-30', '31+'])
R["bins_share_of_era_bills"] = float(len(df2) / len(df))
for bn, dsub in df2.groupby('bin', observed=True):
    if len(dsub) < 2000:
        R[f"t3_bin_{bn}"] = {"skipped_thin": True, "n": int(len(dsub))}
        print(f"bin {bn}: N={len(dsub)} skipped")
        continue
    mb = smf.ols('absorbed ~ first_term + late + first_term:late + C(assembly) + C(bloc)'
                 ' + C(election_type) + C(committee_nm)', dsub).fit(cov_type='cluster', cov_kwds=CL(dsub))
    put(f"t3_bin_{bn}", mb, 'first_term:late', clusters=dsub.rst_mona_cd.nunique())

# Per-assembly step (depth.py block 8)
for a in range(17, 23):
    dsub = df[df['assembly'] == a]
    ma = smf.ols('absorbed ~ first_term + late + first_term:late + C(bloc)'
                 ' + C(election_type) + C(committee_nm)', dsub).fit(cov_type='cluster', cov_kwds=CL(dsub))
    put(f"t3_assembly_{a}", ma, 'first_term:late', clusters=dsub.rst_mona_cd.nunique())

# ---------------------------------------------------------------------------
# Table 1 (timing, event size), depth.py block 2 and depth2.py
# ---------------------------------------------------------------------------
proc = pd.concat([pd.read_parquet(f'{DATA}/master_bills_{a}.parquet', columns=['bill_id', 'proc_dt'])
                  for a in range(17, 23)]).drop_duplicates('bill_id')
ab = df[df['absorbed'] == 1].merge(proc, on='bill_id', how='left')
ab['proc_dt'] = pd.to_datetime(ab['proc_dt'])
ab['proc_months_in'] = ab.apply(
    lambda r: (r['proc_dt'] - pd.Timestamp(TERM_START[r['assembly']])).days / 30.44, axis=1)
ab['proc_year'] = np.clip(np.floor(ab['proc_months_in'] / 12).astype('Int64') + 1, 1, 4)
R["absorbed_processed_year1"] = int((ab['proc_year'] == 1).sum())
R["absorbed_processed_year1_first_term"] = int(((ab['proc_year'] == 1) & (ab['first_term'] == 1)).sum())
ev_y = ab.drop_duplicates(['assembly', 'committee_nm', 'proc_dt']).groupby('proc_year').size()
R["events_processed_year1"] = int(ev_y.loc[1])
y1 = df[df['prop_year'] == 1]
t = y1.groupby('first_term')['absorbed'].agg(['mean', 'sum', 'count'])
R["year1_proposed_absorbed_first_term"] = int(t.loc[1, 'sum'])
R["year1_proposed_absorbed_reelected"] = int(t.loc[0, 'sum'])
R["year1_proposed_absorbed_rate_first_term"] = float(t.loc[1, 'mean'])
R["year1_proposed_absorbed_rate_reelected"] = float(t.loc[0, 'mean'])
ab_y1 = ab[ab['prop_year'] == 1]
R["year1_proposed_absorbed_processed_within_2y_share"] = float((ab_y1['proc_year'] <= 2).mean())
ab['event'] = ab['assembly'].astype(str) + '|' + ab['committee_nm'] + '|' + ab['proc_dt'].astype(str)
# depth2.py builds the event key from the unparsed proc_dt string; the parsed
# timestamp gives the same grouping (one key per calendar date).
esize = ab.groupby('event').size().rename('event_size')
ab = ab.merge(esize, on='event')
for py in (1, 2):
    sub = ab[ab['prop_year'] == py]
    g = sub.groupby('first_term')['event_size'].agg(['mean', 'median', 'count'])
    R[f"event_size_prop_year{py}"] = {str(k): {c: float(g.loc[k, c]) for c in g.columns} for k in g.index}
print("timing", {k: R[k] for k in R if k.startswith(('absorbed_processed', 'events_', 'year1_prop'))})
print("event size", R["event_size_prop_year1"])

# ---------------------------------------------------------------------------
# Table 4 (mechanisms), workspace/r30/mechanisms.py and mechanisms2.py
# ---------------------------------------------------------------------------
mem = []
for a in range(17, 23):
    m = pd.read_parquet(f'{DATA}/members_{a}.parquet', columns=['mona_cd', 'reelection'])
    m['assembly'] = a
    m['co_first_term'] = (m['reelection'] == '초선').astype(int)
    mem.append(m[['assembly', 'mona_cd', 'co_first_term']])
mem = pd.concat(mem).drop_duplicates(['assembly', 'mona_cd'])
edges = pd.read_parquet(f'{DATA}/cosponsorship_edges.parquet', columns=['bill_id', 'member_id', 'role'])
edges = edges.merge(df[['bill_id', 'assembly', 'rst_mona_cd']], on='bill_id', how='inner')
co = edges[edges['member_id'] != edges['rst_mona_cd']].copy()
co = co.merge(mem, left_on=['assembly', 'member_id'], right_on=['assembly', 'mona_cd'], how='left')
R["cosponsor_rows_matched_share"] = float(co['co_first_term'].notna().mean())
bill_net = co.groupby('bill_id').agg(
    n_co=('member_id', 'size'), inc_share=('co_first_term', lambda s: 1 - s.mean())).reset_index()
dfn = df.merge(bill_net, on='bill_id', how='inner')
R["edge_panel_n"] = int(len(dfn))
R["edge_panel_n_first_term"] = int((dfn.first_term == 1).sum())
R["edge_coverage_20_22"] = float(len(dfn) / len(df[df.assembly >= 20]))
tab = dfn.pivot_table(index='prop_year', columns='first_term', values='inc_share', aggfunc='mean') * 100
R["inc_share_by_year_cohort"] = {str(y): {str(c): float(tab.loc[y, c]) for c in tab.columns} for y in tab.index}
print("inc share by year x cohort\n", tab.round(2))

ft = dfn[dfn['first_term'] == 1]
m_sh = smf.ols('inc_share ~ late' + FE, ft).fit(cov_type='cluster', cov_kwds=CL(ft))
put("t4_a_share_ft_late", m_sh, 'late', clusters=ft.rst_mona_cd.nunique())
m_shy = smf.ols('inc_share ~ C(prop_year)' + FE, ft).fit(cov_type='cluster', cov_kwds=CL(ft))
for y in (2, 3, 4):
    put(f"t4_a_share_ft_year{y}", m_shy, f'C(prop_year)[T.{y}]')
m_dd = smf.ols('inc_share ~ first_term * late' + FE, dfn).fit(cov_type='cluster', cov_kwds=CL(dfn))
put("t4_a_share_dd", m_dd, 'first_term:late', clusters=dfn.rst_mona_cd.nunique())
m_u = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, dfn).fit(cov_type='cluster', cov_kwds=CL(dfn))
put("t4_a_step_uncond", m_u, 'first_term:late', clusters=dfn.rst_mona_cd.nunique())
base = m_u.params['first_term:late'] * 100
m_c1 = smf.ols('absorbed ~ first_term + late + first_term:late + inc_share + np.log1p(n_co)' + FE,
               dfn).fit(cov_type='cluster', cov_kwds=CL(dfn))
put("t4_a_step_cond_share", m_c1, 'first_term:late',
    extra={"attenuation_pct": float((1 - m_c1.params['first_term:late'] * 100 / base) * 100)})
dfn['dec'] = dfn.groupby(['assembly', 'committee_nm'])['inc_share'].transform(
    lambda s: pd.qcut(s.rank(method='first'), 10, labels=False, duplicates='drop'))
dfd = dfn.dropna(subset=['dec'])
m_c2 = smf.ols('absorbed ~ first_term + late + first_term:late + C(dec) + np.log1p(n_co)' + FE,
               dfd).fit(cov_type='cluster', cov_kwds=CL(dfd))
put("t4_a_step_decile", m_c2, 'first_term:late',
    extra={"attenuation_pct": float((1 - m_c2.params['first_term:late'] * 100 / base) * 100)})
# first stage (mechanisms2.py block A)
m0 = smf.ols('absorbed ~ inc_share + np.log1p(n_co)' + FE, dfn).fit(cov_type='cluster', cov_kwds=CL(dfn))
put("t4_a_first_stage_all", m0, 'inc_share')
m1f = smf.ols('absorbed ~ inc_share + np.log1p(n_co)' + FE, ft).fit(cov_type='cluster', cov_kwds=CL(ft))
put("t4_a_first_stage_ft", m1f, 'inc_share')


def base_law(nm):
    if not isinstance(nm, str):
        return None
    nm = re.sub(r'\(.*?\)', '', nm)
    nm = re.sub(r'(일부개정법률안|전부개정법률안|폐지법률안|개정법률안|법률안|폐지안|개정안)\s*$', '', nm)
    return nm.strip()


names = pd.concat([pd.read_parquet(f'{DATA}/master_bills_{a}.parquet', columns=['bill_id', 'bill_nm', 'ppsl_dt'])
                   for a in range(17, 23)]).drop_duplicates('bill_id')
# Contemporaneous duplicate (mechanisms.py block 3)
dfx = df.merge(names[['bill_id', 'bill_nm']], on='bill_id', how='left')
dfx['base_law'] = dfx['bill_nm'].map(base_law)
inc_laws = set(map(tuple, dfx.loc[dfx['first_term'] == 0, ['assembly', 'committee_nm', 'base_law']].dropna().values))
dfx['dup_inc'] = np.array([tuple(r) in inc_laws for r in dfx[['assembly', 'committee_nm', 'base_law']].values]).astype(int)
ftx = dfx[dfx['first_term'] == 1]
R["dup_inc_share_ft_by_year"] = {str(k): float(v) for k, v in (ftx.groupby('prop_year')['dup_inc'].mean() * 100).items()}
m_dup = smf.ols('dup_inc ~ late' + FE, ftx).fit(cov_type='cluster', cov_kwds=CL(ftx))
put("t4_b_dup_contemp_ft_late", m_dup, 'late', clusters=ftx.rst_mona_cd.nunique())
m_u3 = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, dfx).fit(cov_type='cluster', cov_kwds=CL(dfx))
b3 = m_u3.params['first_term:late'] * 100
m_c3 = smf.ols('absorbed ~ first_term + late + first_term:late + dup_inc' + FE, dfx).fit(cov_type='cluster', cov_kwds=CL(dfx))
put("t4_b_step_cond_dup_contemp", m_c3, 'first_term:late',
    extra={"attenuation_pct": float((1 - m_c3.params['first_term:late'] * 100 / b3) * 100)})

# Temporally ordered duplicate (mechanisms2.py block B)
dfx2 = df.merge(names, on='bill_id', how='left')
dfx2['base_law'] = dfx2['bill_nm'].map(base_law)
dfx2['ppsl_dt'] = pd.to_datetime(dfx2['ppsl_dt'])
inc_first = (dfx2[dfx2['first_term'] == 0].groupby(['assembly', 'committee_nm', 'base_law'])['ppsl_dt']
             .min().rename('inc_first_dt').reset_index())
dfx2 = dfx2.merge(inc_first, on=['assembly', 'committee_nm', 'base_law'], how='left')
dfx2['dup_prior'] = ((dfx2['inc_first_dt'].notna()) & (dfx2['inc_first_dt'] <= dfx2['ppsl_dt'])).astype(int)
ftx2 = dfx2[dfx2['first_term'] == 1]
R["dup_prior_share_ft_by_year"] = {str(k): float(v) for k, v in (ftx2.groupby('prop_year')['dup_prior'].mean() * 100).items()}
m_dp = smf.ols('dup_prior ~ late' + FE, ftx2).fit(cov_type='cluster', cov_kwds=CL(ftx2))
put("t4_b_dup_prior_ft_late", m_dp, 'late', clusters=ftx2.rst_mona_cd.nunique())
m_u4 = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, dfx2).fit(cov_type='cluster', cov_kwds=CL(dfx2))
put("t4_b_step_uncond_full", m_u4, 'first_term:late')
b0 = m_u4.params['first_term:late'] * 100
m_cp = smf.ols('absorbed ~ first_term + late + first_term:late + dup_prior' + FE, dfx2).fit(cov_type='cluster', cov_kwds=CL(dfx2))
put("t4_b_step_cond_dup_prior", m_cp, 'first_term:late',
    extra={"attenuation_pct": float((1 - m_cp.params['first_term:late'] * 100 / b0) * 100)})
put("t4_b_absorb_on_dup_prior", m_cp, 'dup_prior')

# New-enactment check (mechanisms2.py block C)
dfx2['new_law'] = (~dfx2['bill_nm'].fillna('').str.contains('개정|폐지')).astype(int)
t2 = dfx2.pivot_table(index='prop_year', columns='first_term', values='new_law', aggfunc='mean') * 100
R["new_law_share_by_year_cohort"] = {str(y): {str(c): float(t2.loc[y, c]) for c in t2.columns} for y in t2.index}
m_nl = smf.ols('new_law ~ first_term * late' + FE, dfx2).fit(cov_type='cluster', cov_kwds=CL(dfx2))
put("t4_b_new_law_dd", m_nl, 'first_term:late')
m_c4 = smf.ols('absorbed ~ first_term + late + first_term:late + new_law' + FE, dfx2).fit(cov_type='cluster', cov_kwds=CL(dfx2))
put("t4_b_step_cond_new_law", m_c4, 'first_term:late',
    extra={"attenuation_pct": float((1 - m_c4.params['first_term:late'] * 100 / b0) * 100)})
put("t4_b_absorb_on_new_law", m_c4, 'new_law')

# Joint controls (mechanisms2.py block D)
dfj = dfx2.merge(bill_net, on='bill_id', how='inner')
m_uj = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, dfj).fit(cov_type='cluster', cov_kwds=CL(dfj))
put("t4_b_step_uncond_edge_joint_sample", m_uj, 'first_term:late')
bj = m_uj.params['first_term:late'] * 100
m_j = smf.ols('absorbed ~ first_term + late + first_term:late + inc_share + np.log1p(n_co) + dup_prior + new_law'
              + FE, dfj).fit(cov_type='cluster', cov_kwds=CL(dfj))
put("t4_b_step_joint", m_j, 'first_term:late',
    extra={"attenuation_pct": float((1 - m_j.params['first_term:late'] * 100 / bj) * 100)})

# Boundary (mechanisms.py block 4)
h = mC.t_test('first_term:C(prop_year)[T.3] - first_term:C(prop_year)[T.2] = 0')
R["t4_c_deepening"] = {"est": float(np.squeeze(h.effect)) * 100, "se": float(np.squeeze(h.sd)) * 100,
                       "p": float(np.squeeze(h.pvalue)), "n": int(mC.nobs)}
h2 = mC.f_test('first_term:C(prop_year)[T.2] = first_term:C(prop_year)[T.3],'
               'first_term:C(prop_year)[T.3] = first_term:C(prop_year)[T.4]')
R["t4_c_flatness_p"] = float(np.squeeze(h2.pvalue))
print("deepening", R["t4_c_deepening"], "flatness p", R["t4_c_flatness_p"])

R["_meta"] = {"script": "v2/tables_v2.py", "panel": str(PANEL), "python": sys.version.split()[0],
              "pandas": pd.__version__, "statsmodels": __import__('statsmodels').__version__}
OUT.write_text(json.dumps(R, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print("wrote", OUT)

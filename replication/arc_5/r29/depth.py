import os  # added by replicate.py for KBL_DATA
# R29 Arc 5 depth round: absorption anatomy + premise-null hardening
# Inputs: workspace/r28/bills_panel.csv (93,572 member law bills, uid-merged)
# Pre-committed baselines: workspace/r29/BASELINE.md (written before this ran)
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

DATA = os.environ["KBL_DATA"]
WS = '.'
TERM_START = {17: '2004-05-30', 18: '2008-05-30', 19: '2012-05-30',
              20: '2016-05-30', 21: '2020-05-30', 22: '2024-05-30'}

df = pd.read_csv(f'{WS}/r28/bills_panel.csv')
df = df[df['committee_nm'].notna()].copy()
# absorption-only outcome: positive via daean channel, not direct passage
df['absorbed'] = ((df['passed_absorb'] == 1) & (df['passed_strict'] == 0)).astype(int)
df['late'] = (df['prop_year'] >= 2).astype(int)
FE = ' + C(assembly) + C(bloc) + C(election_type) + C(committee_nm)'
CL = lambda d: {'groups': d['rst_mona_cd']}

print('=== 1. STEP vs SLOPE (absorption-only outcome) ===')
d = df
m_lin = smf.ols('absorbed ~ first_term * prop_year' + FE, d).fit(
    cov_type='cluster', cov_kwds=CL(d))
m_step = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, d).fit(
    cov_type='cluster', cov_kwds=CL(d))
m_yr = smf.ols('absorbed ~ first_term * C(prop_year)' + FE, d).fit(
    cov_type='cluster', cov_kwds=CL(d))
print(f"linear  ft x prop_year: {m_lin.params['first_term:prop_year']*100:+.2f}pp/yr "
      f"(SE {m_lin.bse['first_term:prop_year']*100:.2f}), BIC={m_lin.bic:.0f}")
print(f"step    ft (year-1 gap): {m_step.params['first_term']*100:+.2f}pp "
      f"(SE {m_step.bse['first_term']*100:.2f}, p={m_step.pvalues['first_term']:.3f})")
print(f"step    ft x late:       {m_step.params['first_term:late']*100:+.2f}pp "
      f"(SE {m_step.bse['first_term:late']*100:.2f}, p={m_step.pvalues['first_term:late']:.4f}), "
      f"BIC={m_step.bic:.0f}")
for y in [2, 3, 4]:
    k = f'first_term:C(prop_year)[T.{y}]'
    print(f"  ft x year{y}: {m_yr.params[k]*100:+.2f}pp (SE {m_yr.bse[k]*100:.2f})")
print('N =', int(m_step.nobs), '| BIC diff (step - linear):', round(m_step.bic - m_lin.bic, 1))
raw_step = m_step.params['first_term:late'] * 100

print('\n=== 2. DAEAN-EVENT TIMING (thin year-1 cells?) ===')
# pull proc_dt for absorbed bills; approximate a daean event as a unique
# (assembly, committee, proc date) with >=2 absorbed bills that day
pieces = []
for a in range(17, 23):
    b = pd.read_parquet(f'{DATA}/master_bills_{a}.parquet',
                        columns=['bill_id', 'proc_dt'])
    pieces.append(b)
proc = pd.concat(pieces).drop_duplicates('bill_id')
ab = df[df['absorbed'] == 1].merge(proc, on='bill_id', how='left')
ab['proc_dt'] = pd.to_datetime(ab['proc_dt'])
ab['proc_months_in'] = ab.apply(
    lambda r: (r['proc_dt'] - pd.Timestamp(TERM_START[r['assembly']])).days / 30.44, axis=1)
ab['proc_year'] = np.clip(np.floor(ab['proc_months_in'] / 12).astype('Int64') + 1, 1, 4)
print('absorbed bills by PROCESSING term-year (pooled 17-22):')
print(ab.groupby('proc_year').size())
ev = ab.groupby(['assembly', 'committee_nm', 'proc_dt']).size()
ev_y = ab.drop_duplicates(['assembly', 'committee_nm', 'proc_dt']).groupby('proc_year').size()
print('unique daean processing events (assembly x committee x date) by term-year:')
print(ev_y)
y1 = df[df['prop_year'] == 1]
print('\nyear-1 proposals, absorption by cohort:')
t = y1.groupby('first_term')['absorbed'].agg(['mean', 'sum', 'count'])
print(t)
print('year-1 ft absorbed N =', int(t.loc[1, 'sum']), '| re-elected absorbed N =', int(t.loc[0, 'sum']))
# when do year-1 proposals get absorbed?
ab_y1 = ab[ab['prop_year'] == 1]
print('processing year of year-1-proposed absorbed bills (share):')
print(ab_y1['proc_year'].value_counts(normalize=True).sort_index().round(3))

print('\n=== 3. KRUTZ COMMITTEE-MIX REWEIGHTING ===')
# weight ft bills so their (assembly x committee) mix matches re-elected bills
w = np.ones(len(df))
for a in df['assembly'].unique():
    sub = df['assembly'] == a
    re_mix = df[sub & (df['first_term'] == 0)]['committee_nm'].value_counts(normalize=True)
    ft_mix = df[sub & (df['first_term'] == 1)]['committee_nm'].value_counts(normalize=True)
    ratio = (re_mix / ft_mix).reindex(df.loc[sub, 'committee_nm']).fillna(0).values
    w[sub.values] = np.where(df.loc[sub, 'first_term'] == 1, ratio, 1.0)
df['w_krutz'] = np.clip(w, 0, 10)  # cap extreme weights
# raw (unadjusted) cell diff-in-diff, then weighted
def dd(d, wcol=None):
    g = d.groupby(['first_term', 'late']).apply(
        lambda x: np.average(x['absorbed'], weights=x[wcol] if wcol else None),
        include_groups=False)
    return ((g[1, 1] - g[1, 0]) - (g[0, 1] - g[0, 0])) * 100
print(f'raw cell step (DD): {dd(df):+.2f}pp | Krutz-reweighted: {dd(df, "w_krutz"):+.2f}pp')
m_kw = smf.wls('absorbed ~ first_term + late + first_term:late' + FE, df,
               weights=df['w_krutz']).fit(cov_type='cluster', cov_kwds=CL(df))
print(f"reweighted regression step: {m_kw.params['first_term:late']*100:+.2f}pp "
      f"(SE {m_kw.bse['first_term:late']*100:.2f}, p={m_kw.pvalues['first_term:late']:.4f})")
print('attenuation vs raw regression step:',
      f"{(1 - m_kw.params['first_term:late']*100/raw_step)*100:+.0f}%")

print('\n=== 4. COALITION-SIZE BINS ===')
edges = pd.read_parquet(f'{DATA}/cosponsorship_edges.parquet', columns=['bill_id'])
nco = edges.groupby('bill_id').size().rename('n_sponsors')
df2 = df.merge(nco, on='bill_id', how='left')
cov = df2.groupby('assembly')['n_sponsors'].apply(lambda s: s.notna().mean())
print('edge coverage by assembly:', cov.round(3).to_dict())
df2 = df2[df2['n_sponsors'].notna()].copy()
df2['bin'] = pd.cut(df2['n_sponsors'], [0, 10, 15, 30, 1000],
                    labels=['<=10', '11-15', '16-30', '31+'])
for bn, dsub in df2.groupby('bin', observed=True):
    if len(dsub) < 2000:
        print(f'bin {bn}: N={len(dsub)} (skipped, thin)')
        continue
    m = smf.ols('absorbed ~ first_term + late + first_term:late + C(assembly) + C(bloc)'
                ' + C(election_type) + C(committee_nm)', dsub).fit(
        cov_type='cluster', cov_kwds=CL(dsub))
    print(f"bin {bn:>5}: step {m.params['first_term:late']*100:+.2f}pp "
          f"(SE {m.bse['first_term:late']*100:.2f}), N={len(dsub)}")

print('\n=== 5. MEMBER-LEVEL WEIGHTING RECONCILIATION (n>=3) ===')
cells = df.groupby(['assembly', 'rst_mona_cd', 'first_term', 'late']).agg(
    absorbed=('absorbed', 'mean'), n=('absorbed', 'size'),
    bloc=('bloc', 'first'), election_type=('election_type', 'first')).reset_index()
for lab, csub in [('all cells', cells), ('n>=3 cells', cells[cells['n'] >= 3])]:
    m = smf.ols('absorbed ~ first_term + late + first_term:late + C(assembly) + C(bloc)'
                ' + C(election_type)', csub).fit(
        cov_type='cluster', cov_kwds={'groups': csub['rst_mona_cd']})
    print(f"member-level ({lab}): step {m.params['first_term:late']*100:+.2f}pp "
          f"(SE {m.bse['first_term:late']*100:.2f}, p={m.pvalues['first_term:late']:.3f}), "
          f"cells={len(csub)}")

print('\n=== 6. TOST +/-2pp ON YEAR-1 STRICT GAP ===')
from scipy import stats
y1s = df[df['prop_year'] == 1]
m1 = smf.ols('passed_strict ~ first_term' + FE, y1s).fit(
    cov_type='cluster', cov_kwds=CL(y1s))
b, se = m1.params['first_term'], m1.bse['first_term']
t_lo = (b - (-0.02)) / se
t_hi = (0.02 - b) / se
p_lo, p_hi = 1 - stats.norm.cdf(t_lo), 1 - stats.norm.cdf(t_hi)
print(f"year-1 strict gap: {b*100:+.2f}pp (SE {se*100:.2f}), N={int(m1.nobs)}")
print(f"TOST vs +/-2pp: p_lower={p_lo:.5f}, p_upper={p_hi:.5f} -> "
      f"{'EQUIVALENT' if max(p_lo, p_hi) < 0.05 else 'NOT equivalent'}")
t_lo1 = (b - (-0.01)) / se
t_hi1 = (0.01 - b) / se
p1 = max(1 - stats.norm.cdf(t_lo1), 1 - stats.norm.cdf(t_hi1))
print(f"TOST vs +/-1pp: max p={p1:.4f} -> {'EQUIVALENT' if p1 < 0.05 else 'NOT equivalent'}")

print('\n=== 7. BY-ELECTION CLOCK PROXY ===')
first_act = df.groupby(['assembly', 'rst_mona_cd']).agg(
    first_bill_months=('months_in', 'min'), ft=('first_term', 'first')).reset_index()
late_starters = first_act[(first_act['ft'] == 1) & (first_act['first_bill_months'] > 12)]
print(f"first-term sponsors: {int((first_act.ft==1).sum())}; "
      f"first bill >12 months in (by-election proxy): {len(late_starters)} "
      f"({len(late_starters)/(first_act.ft==1).sum()*100:.1f}%)")
core = df[~df.set_index(['assembly', 'rst_mona_cd']).index.isin(
    late_starters.set_index(['assembly', 'rst_mona_cd']).index)]
m_c = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, core).fit(
    cov_type='cluster', cov_kwds=CL(core))
print(f"step excluding late starters: {m_c.params['first_term:late']*100:+.2f}pp "
      f"(SE {m_c.bse['first_term:late']*100:.2f}), N={int(m_c.nobs)}")
m_s = smf.ols('passed_strict ~ first_term * prop_year' + FE, core).fit(
    cov_type='cluster', cov_kwds=CL(core))
print(f"strict linear interaction excluding late starters: "
      f"{m_s.params['first_term:prop_year']*100:+.2f}pp/yr "
      f"(SE {m_s.bse['first_term:prop_year']*100:.2f})")

print('\n=== 8. PER-ASSEMBLY STEP ===')
for a in range(17, 23):
    dsub = df[df['assembly'] == a]
    m = smf.ols('absorbed ~ first_term + late + first_term:late + C(bloc)'
                ' + C(election_type) + C(committee_nm)', dsub).fit(
        cov_type='cluster', cov_kwds=CL(dsub))
    print(f"A{a}: step {m.params['first_term:late']*100:+.2f}pp "
          f"(SE {m.bse['first_term:late']*100:.2f}), N={len(dsub)}")

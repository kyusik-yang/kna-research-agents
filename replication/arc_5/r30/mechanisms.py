import os  # added by replicate.py for KBL_DATA
# R30 Arc 5 mechanism round: network channel, portfolio channel, wonguseong boundary
# Inputs: workspace/r28/bills_panel.csv, cosponsorship_edges.parquet, members_{a}.parquet
# Pre-committed baselines: workspace/r30/BASELINE.md (written before this ran)
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

DATA = os.environ["KBL_DATA"]
WS = '.'

df = pd.read_csv(f'{WS}/r28/bills_panel.csv')
df = df[df['committee_nm'].notna()].copy()
df['absorbed'] = ((df['passed_absorb'] == 1) & (df['passed_strict'] == 0)).astype(int)
df['late'] = (df['prop_year'] >= 2).astype(int)
FE = ' + C(assembly) + C(bloc) + C(election_type) + C(committee_nm)'
CL = lambda d: {'groups': d['rst_mona_cd']}

# ---- member first-term status per assembly (same rule as r28 build.py) ----
mem = []
for a in range(17, 23):
    m = pd.read_parquet(f'{DATA}/members_{a}.parquet',
                        columns=['mona_cd', 'reelection'])
    m['assembly'] = a
    m['co_first_term'] = (m['reelection'] == '초선').astype(int)
    mem.append(m[['assembly', 'mona_cd', 'co_first_term']])
mem = pd.concat(mem).drop_duplicates(['assembly', 'mona_cd'])

# ---- cosponsor rosters -> incumbent share per bill ----
edges = pd.read_parquet(f'{DATA}/cosponsorship_edges.parquet',
                        columns=['bill_id', 'member_id', 'role'])
edges = edges.merge(df[['bill_id', 'assembly', 'rst_mona_cd']], on='bill_id', how='inner')
# exclude the representative sponsor from the co-sponsor roster
co = edges[edges['member_id'] != edges['rst_mona_cd']].copy()
co = co.merge(mem, left_on=['assembly', 'member_id'],
              right_on=['assembly', 'mona_cd'], how='left')
print('cosponsor rows matched to member status:',
      f"{co['co_first_term'].notna().mean()*100:.1f}% of {len(co)}")
bill_net = co.groupby('bill_id').agg(
    n_co=('member_id', 'size'),
    inc_share=('co_first_term', lambda s: 1 - s.mean())).reset_index()

dfn = df.merge(bill_net, on='bill_id', how='inner')
print('edge-covered panel: N =', len(dfn), '| assemblies:',
      sorted(dfn['assembly'].unique()),
      '| coverage within 20-22:',
      f"{len(dfn)/len(df[df.assembly>=20])*100:.1f}%")

print('\n=== 1. NETWORK CHANNEL (i): incumbent-cosponsor share by cohort x prop_year ===')
tab = dfn.pivot_table(index='prop_year', columns='first_term',
                      values='inc_share', aggfunc=['mean', 'count'])
print((tab * 100).round(2))
# within first-term bills: step in inc_share?
ft = dfn[dfn['first_term'] == 1]
m_sh = smf.ols('inc_share ~ late' + FE.replace('C(election_type)', 'C(election_type)'),
               ft).fit(cov_type='cluster', cov_kwds=CL(ft))
print(f"ft bills, inc_share late-vs-year1 step: {m_sh.params['late']*100:+.2f}pp "
      f"(SE {m_sh.bse['late']*100:.2f}, p={m_sh.pvalues['late']:.4f}), N={int(m_sh.nobs)}")
m_shy = smf.ols('inc_share ~ C(prop_year)' + FE, ft).fit(
    cov_type='cluster', cov_kwds=CL(ft))
for y in [2, 3, 4]:
    k = f'C(prop_year)[T.{y}]'
    print(f"  ft inc_share year{y} vs year1: {m_shy.params[k]*100:+.2f}pp "
          f"(SE {m_shy.bse[k]*100:.2f})")
# difference-in-differences on inc_share: does ft fall MORE than re-elected?
m_dd = smf.ols('inc_share ~ first_term * late' + FE, dfn).fit(
    cov_type='cluster', cov_kwds=CL(dfn))
print(f"inc_share DD (ft x late): {m_dd.params['first_term:late']*100:+.2f}pp "
      f"(SE {m_dd.bse['first_term:late']*100:.2f}, p={m_dd.pvalues['first_term:late']:.4f})")

print('\n=== 2. NETWORK CHANNEL (ii): absorption step conditional on inc_share ===')
# fair same-sample unconditional step first
m_u = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, dfn).fit(
    cov_type='cluster', cov_kwds=CL(dfn))
base = m_u.params['first_term:late'] * 100
print(f"unconditional step (edge-covered 20-22 sample): {base:+.2f}pp "
      f"(SE {m_u.bse['first_term:late']*100:.2f}, p={m_u.pvalues['first_term:late']:.4f}), "
      f"N={int(m_u.nobs)}")
# continuous control + coalition size
m_c1 = smf.ols('absorbed ~ first_term + late + first_term:late + inc_share'
               ' + np.log1p(n_co)' + FE, dfn).fit(cov_type='cluster', cov_kwds=CL(dfn))
print(f"+ inc_share + log n_co: step {m_c1.params['first_term:late']*100:+.2f}pp "
      f"(SE {m_c1.bse['first_term:late']*100:.2f}) | inc_share coef "
      f"{m_c1.params['inc_share']*100:+.2f}pp")
# within-(assembly x committee) decile of inc_share
dfn['dec'] = dfn.groupby(['assembly', 'committee_nm'])['inc_share'].transform(
    lambda s: pd.qcut(s.rank(method='first'), 10, labels=False, duplicates='drop'))
m_c2 = smf.ols('absorbed ~ first_term + late + first_term:late + C(dec)'
               ' + np.log1p(n_co)' + FE, dfn.dropna(subset=['dec'])).fit(
    cov_type='cluster', cov_kwds=CL(dfn.dropna(subset=['dec'])))
print(f"+ inc_share decile FE: step {m_c2.params['first_term:late']*100:+.2f}pp "
      f"(SE {m_c2.bse['first_term:late']*100:.2f})")
for lab, m in [('continuous', m_c1), ('decile', m_c2)]:
    att = (1 - m.params['first_term:late'] * 100 / base) * 100
    print(f"attenuation vs same-sample step ({lab}): {att:+.1f}%")

print('\n=== 3. PORTFOLIO CHANNEL: duplicate-title overlap ===')
# base law name: strip amendment suffixes from bill_nm
import re
names = []
for a in range(17, 23):
    b = pd.read_parquet(f'{DATA}/master_bills_{a}.parquet',
                        columns=['bill_id', 'bill_nm'])
    names.append(b)
names = pd.concat(names).drop_duplicates('bill_id')
dfx = df.merge(names, on='bill_id', how='left')
def base_law(nm):
    if not isinstance(nm, str):
        return None
    nm = re.sub(r'\(.*?\)', '', nm)
    nm = re.sub(r'(일부개정법률안|전부개정법률안|폐지법률안|개정법률안|법률안|폐지안|개정안)\s*$', '', nm)
    return nm.strip()
dfx['base_law'] = dfx['bill_nm'].map(base_law)
print('base_law coverage:', f"{dfx['base_law'].notna().mean()*100:.1f}%")
# incumbent bills per (assembly, committee, base_law)
inc_laws = set(map(tuple, dfx.loc[dfx['first_term'] == 0,
                                  ['assembly', 'committee_nm', 'base_law']].dropna().values))
dfx['dup_inc'] = [tuple(r) in inc_laws for r in
                  dfx[['assembly', 'committee_nm', 'base_law']].values]
dfx['dup_inc'] = dfx['dup_inc'].astype(int)
ftx = dfx[dfx['first_term'] == 1]
tab2 = ftx.pivot_table(index='prop_year', values='dup_inc', aggfunc=['mean', 'count'])
print('ft bills: share duplicating a same-assembly same-committee incumbent base law, by prop_year:')
tab2.columns = ['dup_share', 'n_bills']
tab2['dup_share'] = (tab2['dup_share'] * 100).round(2)
print(tab2)
m_dup = smf.ols('dup_inc ~ late' + FE, ftx).fit(cov_type='cluster', cov_kwds=CL(ftx))
print(f"ft dup_inc step: {m_dup.params['late']*100:+.2f}pp (SE {m_dup.bse['late']*100:.2f})")
# condition the absorption step on dup_inc (full 17-22 sample)
m_u3 = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, dfx).fit(
    cov_type='cluster', cov_kwds=CL(dfx))
b3 = m_u3.params['first_term:late'] * 100
m_c3 = smf.ols('absorbed ~ first_term + late + first_term:late + dup_inc' + FE, dfx).fit(
    cov_type='cluster', cov_kwds=CL(dfx))
print(f"pooled step {b3:+.2f}pp -> + dup_inc: {m_c3.params['first_term:late']*100:+.2f}pp "
      f"(attenuation {(1 - m_c3.params['first_term:late']*100/b3)*100:+.1f}%) | "
      f"dup_inc coef {m_c3.params['dup_inc']*100:+.2f}pp")

print('\n=== 4. WONGUSEONG BOUNDARY: per-year interactions, year-3 deepening test ===')
m_yr = smf.ols('absorbed ~ first_term * C(prop_year)' + FE, df).fit(
    cov_type='cluster', cov_kwds=CL(df))
for y in [2, 3, 4]:
    k = f'first_term:C(prop_year)[T.{y}]'
    print(f"ft x year{y}: {m_yr.params[k]*100:+.2f}pp (SE {m_yr.bse[k]*100:.2f})")
h = m_yr.t_test('first_term:C(prop_year)[T.3] - first_term:C(prop_year)[T.2] = 0')
print(f"year3 - year2 deepening: {float(h.effect)*100:+.2f}pp, p={float(h.pvalue):.3f}")
h2 = m_yr.f_test('first_term:C(prop_year)[T.2] = first_term:C(prop_year)[T.3],'
                 'first_term:C(prop_year)[T.3] = first_term:C(prop_year)[T.4]')
print(f"Wald flatness years 2-4: p={float(h2.pvalue):.3f}")

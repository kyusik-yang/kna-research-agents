import os  # added by replicate.py for KBL_DATA
# R30 stress tests on the mechanism measures themselves
import pandas as pd
import numpy as np
import re
import statsmodels.formula.api as smf

DATA = os.environ["KBL_DATA"]
WS = '.'

df = pd.read_csv(f'{WS}/r28/bills_panel.csv')
df = df[df['committee_nm'].notna()].copy()
df['absorbed'] = ((df['passed_absorb'] == 1) & (df['passed_strict'] == 0)).astype(int)
df['late'] = (df['prop_year'] >= 2).astype(int)
FE = ' + C(assembly) + C(bloc) + C(election_type) + C(committee_nm)'
CL = lambda d: {'groups': d['rst_mona_cd']}

# rebuild inc_share (as mechanisms.py)
mem = []
for a in range(17, 23):
    m = pd.read_parquet(f'{DATA}/members_{a}.parquet', columns=['mona_cd', 'reelection'])
    m['assembly'] = a
    m['co_first_term'] = (m['reelection'] == '초선').astype(int)
    mem.append(m[['assembly', 'mona_cd', 'co_first_term']])
mem = pd.concat(mem).drop_duplicates(['assembly', 'mona_cd'])
edges = pd.read_parquet(f'{DATA}/cosponsorship_edges.parquet',
                        columns=['bill_id', 'member_id'])
edges = edges.merge(df[['bill_id', 'assembly', 'rst_mona_cd']], on='bill_id', how='inner')
co = edges[edges['member_id'] != edges['rst_mona_cd']]
co = co.merge(mem, left_on=['assembly', 'member_id'],
              right_on=['assembly', 'mona_cd'], how='left')
bill_net = co.groupby('bill_id').agg(
    n_co=('member_id', 'size'),
    inc_share=('co_first_term', lambda s: 1 - s.mean())).reset_index()
dfn = df.merge(bill_net, on='bill_id', how='inner')

print('=== A. Does inc_share even predict absorption? (network premise) ===')
m0 = smf.ols('absorbed ~ inc_share + np.log1p(n_co)' + FE, dfn).fit(
    cov_type='cluster', cov_kwds=CL(dfn))
print(f"all bills: inc_share -> absorbed {m0.params['inc_share']*100:+.2f}pp "
      f"(SE {m0.bse['inc_share']*100:.2f}, p={m0.pvalues['inc_share']:.3f}), N={int(m0.nobs)}")
ftn = dfn[dfn['first_term'] == 1]
m1 = smf.ols('absorbed ~ inc_share + np.log1p(n_co)' + FE, ftn).fit(
    cov_type='cluster', cov_kwds=CL(ftn))
print(f"ft bills only: inc_share -> absorbed {m1.params['inc_share']*100:+.2f}pp "
      f"(SE {m1.bse['inc_share']*100:.2f}, p={m1.pvalues['inc_share']:.3f}), N={int(m1.nobs)}")

print('\n=== B. Temporally-ordered duplicate proxy (prior incumbent bill exists) ===')
names, dates = [], []
for a in range(17, 23):
    b = pd.read_parquet(f'{DATA}/master_bills_{a}.parquet',
                        columns=['bill_id', 'bill_nm', 'ppsl_dt'])
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
dfx['ppsl_dt'] = pd.to_datetime(dfx['ppsl_dt'])
# earliest incumbent proposal date per (assembly, committee, base_law)
inc_first = (dfx[dfx['first_term'] == 0]
             .groupby(['assembly', 'committee_nm', 'base_law'])['ppsl_dt']
             .min().rename('inc_first_dt').reset_index())
dfx = dfx.merge(inc_first, on=['assembly', 'committee_nm', 'base_law'], how='left')
dfx['dup_prior'] = ((dfx['inc_first_dt'].notna())
                    & (dfx['inc_first_dt'] <= dfx['ppsl_dt'])).astype(int)
ftx = dfx[dfx['first_term'] == 1]
t = ftx.pivot_table(index='prop_year', values='dup_prior', aggfunc=['mean', 'count'])
t.columns = ['dup_prior_share', 'n']
t['dup_prior_share'] = (t['dup_prior_share'] * 100).round(2)
print('ft bills: share with PRIOR same-committee incumbent bill on same base law:')
print(t)
m_dp = smf.ols('dup_prior ~ late' + FE, ftx).fit(cov_type='cluster', cov_kwds=CL(ftx))
print(f"ft dup_prior step: {m_dp.params['late']*100:+.2f}pp (SE {m_dp.bse['late']*100:.2f}, "
      f"p={m_dp.pvalues['late']:.3f})")
m_u = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, dfx).fit(
    cov_type='cluster', cov_kwds=CL(dfx))
b0 = m_u.params['first_term:late'] * 100
m_c = smf.ols('absorbed ~ first_term + late + first_term:late + dup_prior' + FE, dfx).fit(
    cov_type='cluster', cov_kwds=CL(dfx))
print(f"pooled step {b0:+.2f}pp -> + dup_prior: {m_c.params['first_term:late']*100:+.2f}pp "
      f"(attenuation {(1 - m_c.params['first_term:late']*100/b0)*100:+.1f}%), "
      f"dup_prior coef {m_c.params['dup_prior']*100:+.2f}pp (SE {m_c.bse['dup_prior']*100:.2f})")

print('\n=== C. New-enactment (jeongjeong) content drift ===')
dfx['new_law'] = (~dfx['bill_nm'].fillna('').str.contains('개정|폐지')).astype(int)
t2 = dfx.pivot_table(index='prop_year', columns='first_term', values='new_law',
                     aggfunc='mean') * 100
print('share of bills that are new-enactment bills (%):')
print(t2.round(2))
m_nl = smf.ols('new_law ~ first_term * late' + FE, dfx).fit(
    cov_type='cluster', cov_kwds=CL(dfx))
print(f"new_law DD (ft x late): {m_nl.params['first_term:late']*100:+.2f}pp "
      f"(SE {m_nl.bse['first_term:late']*100:.2f}, p={m_nl.pvalues['first_term:late']:.3f})")
m_c4 = smf.ols('absorbed ~ first_term + late + first_term:late + new_law' + FE, dfx).fit(
    cov_type='cluster', cov_kwds=CL(dfx))
print(f"step + new_law control: {m_c4.params['first_term:late']*100:+.2f}pp "
      f"(attenuation {(1 - m_c4.params['first_term:late']*100/b0)*100:+.1f}%), "
      f"new_law coef {m_c4.params['new_law']*100:+.2f}pp")

print('\n=== D. All three controls jointly (kitchen-sink, edge-covered sample) ===')
dfj = dfx.merge(bill_net, on='bill_id', how='inner')
m_uj = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, dfj).fit(
    cov_type='cluster', cov_kwds=CL(dfj))
bj = m_uj.params['first_term:late'] * 100
m_j = smf.ols('absorbed ~ first_term + late + first_term:late + inc_share'
              ' + np.log1p(n_co) + dup_prior + new_law' + FE, dfj).fit(
    cov_type='cluster', cov_kwds=CL(dfj))
print(f"unconditional {bj:+.2f}pp -> joint controls: "
      f"{m_j.params['first_term:late']*100:+.2f}pp "
      f"(attenuation {(1 - m_j.params['first_term:late']*100/bj)*100:+.1f}%), N={int(m_j.nobs)}")

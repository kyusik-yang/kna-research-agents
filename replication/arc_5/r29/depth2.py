import os  # added by replicate.py for KBL_DATA
# R29 follow-up: fair functional-form test + omnibus-event size + drop-22 robustness
import pandas as pd, numpy as np
import statsmodels.formula.api as smf

DATA = os.environ["KBL_DATA"]
WS = '.'
TERM_START = {17:'2004-05-30',18:'2008-05-30',19:'2012-05-30',
              20:'2016-05-30',21:'2020-05-30',22:'2024-05-30'}
df = pd.read_csv(f'{WS}/r28/bills_panel.csv')
df = df[df['committee_nm'].notna()].copy()
df['absorbed'] = ((df['passed_absorb']==1)&(df['passed_strict']==0)).astype(int)
df['late'] = (df['prop_year']>=2).astype(int)
FE = ' + C(assembly) + C(bloc) + C(election_type) + C(committee_nm)'
CL = lambda d: {'groups': d['rst_mona_cd']}

print('=== FAIR FUNCTIONAL-FORM TEST (both models carry C(prop_year) mains) ===')
mA = smf.ols('absorbed ~ first_term + C(prop_year) + first_term:late'+FE, df).fit(
    cov_type='cluster', cov_kwds=CL(df))
mB = smf.ols('absorbed ~ first_term + C(prop_year) + first_term:prop_year'+FE, df).fit(
    cov_type='cluster', cov_kwds=CL(df))
mC = smf.ols('absorbed ~ first_term*C(prop_year)'+FE, df).fit(
    cov_type='cluster', cov_kwds=CL(df))
print(f"step interaction:   {mA.params['first_term:late']*100:+.2f}pp "
      f"(SE {mA.bse['first_term:late']*100:.2f}), BIC={mA.bic:.0f}")
print(f"linear interaction: {mB.params['first_term:prop_year']*100:+.2f}pp/yr "
      f"(SE {mB.bse['first_term:prop_year']*100:.2f}), BIC={mB.bic:.0f}")
print('BIC (step - linear):', round(mA.bic - mB.bic,1), ' (negative favors step)')
w = mC.wald_test('first_term:C(prop_year)[T.2] = first_term:C(prop_year)[T.3], '
                 'first_term:C(prop_year)[T.3] = first_term:C(prop_year)[T.4]',
                 scalar=True)
print(f"Wald test year2=year3=year4 interactions: stat={w.statistic:.2f}, p={w.pvalue:.3f}")

print('\n=== DROP 22ND (late = only year 2 there) ===')
d21 = df[df['assembly']<=21]
m = smf.ols('absorbed ~ first_term + late + first_term:late'+FE, d21).fit(
    cov_type='cluster', cov_kwds=CL(d21))
print(f"step 17-21 only: {m.params['first_term:late']*100:+.2f}pp "
      f"(SE {m.bse['first_term:late']*100:.2f}, p={m.pvalues['first_term:late']:.4f}), N={len(d21)}")

print('\n=== YEAR-1 OMNIBUS CHECK: daean event size, ft vs re-elected ===')
pieces = []
for a in range(17,23):
    pieces.append(pd.read_parquet(f'{DATA}/master_bills_{a}.parquet',
                                  columns=['bill_id','proc_dt']))
proc = pd.concat(pieces).drop_duplicates('bill_id')
ab = df[df['absorbed']==1].merge(proc, on='bill_id', how='left')
ab['event'] = ab['assembly'].astype(str)+'|'+ab['committee_nm']+'|'+ab['proc_dt'].astype(str)
esize = ab.groupby('event').size().rename('event_size')
ab = ab.merge(esize, on='event')
for py in [1,2]:
    sub = ab[ab['prop_year']==py]
    g = sub.groupby('first_term')['event_size'].agg(['mean','median','count'])
    print(f'prop_year={py}: event size ft vs re:'); print(g.round(1))

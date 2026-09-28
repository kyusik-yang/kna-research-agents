import pandas as pd, numpy as np, statsmodels.formula.api as smf
d = pd.read_parquet('dyads21_meta.parquet')
hm = d[(d.hearing_type=='상임위원회')&d.agenda.str.contains('국무위원후보자',na=False)&d.agenda.str.contains('인사청문',na=False)&(d.direction=='question')]
for lo,hi,lab in [('2020-12-01','2021-05-31','cohort1'),('2023-05-01','2023-10-31','cohort2')]:
    s=hm[(hm.date>=lo)&(hm.date<=hi)]
    print(lab, 'legislators per party:', s.groupby('leg_party').leg_name.nunique().to_dict())
    print(lab, 'status:', pd.crosstab(s.leg_party, s.leg_ruling_status).to_dict())
# corrected coding: opposed = not the president's party at hearing date
RULING = {1:{'더불어민주당','더불어시민당'}, 2:{'국민의힘','미래통합당','국민의당'}}
P = pd.read_csv('r25/panel.csv')
P['ministry']=P.committee_key+'|'+P.nominee.replace({'변창흠':'노형욱'})
P = P.sort_values('nominee').drop_duplicates(['cohort','leg_name','ministry'], keep='last')
P['opposed'] = [0 if r.party in RULING[r.cohort] else 1 for r in P.itertuples()]
P = P[(P.party!='무소속')]
print('== coding change vs leg_ruling_status-based:', pd.crosstab(P.cohort, P.opposed==P.opposed_party).to_dict())
B = P[P.in_both].copy()
print('== analysis sample cohort x opposed (corrected)'); print(pd.crosstab(B.cohort,B.opposed))
def run(S, lab):
    g = S.groupby('opposed')[['share_before','share_after','d_share','placebo_before','placebo_after','d_placebo','unnamed_before','unnamed_after','d_unnamed']].mean().round(3); g['N']=S.groupby('opposed').size()
    print(f'== {lab}'); print(g.T.to_string())
    for y in ['d_share','d_placebo','d_unnamed']:
        m = smf.ols(f'{y} ~ opposed + C(committee_key)', data=S).fit(cov_type='cluster', cov_kwds={'groups':S.leg_name}); ci=m.conf_int().loc['opposed']
        print(f'   {y:10s} DiD(commFE)={100*m.params.opposed:+.1f}pp [{100*ci[0]:+.1f},{100*ci[1]:+.1f}] p={m.pvalues.opposed:.3f} N={int(m.nobs)} clusters={S.leg_name.nunique()}')
run(B[B.cohort==1],'cohort1 (corrected coding = unchanged)'); run(B[B.cohort==2],'cohort2 (corrected)'); run(B,'cohort1+2 (corrected)')
B.to_csv('r25/analysis_sample_corrected.csv', index=False)
# per-nominee cohort2 descriptive under corrected coding
print(B[B.cohort==2].groupby(['nominee','opposed']).agg(N=('d_share','size'),before=('share_before','mean'),after=('share_after','mean')).round(3).unstack('opposed').to_string())

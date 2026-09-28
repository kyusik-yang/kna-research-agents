import pandas as pd, numpy as np, statsmodels.formula.api as smf
R = pd.read_csv('r25/roster.csv'); P = pd.read_csv('r25/panel.csv')
print('== roster by cohort x ruling'); print(pd.crosstab(R.cohort, R.ruling))
print('== coding agreement (cohort>0): party-line vs own-speech'); print(pd.crosstab(R[R.cohort>0].opposed_party, R[R.cohort>0].opposed_speech, margins=True))
print('neg_share mean by ruling:', R[R.cohort>0].groupby('ruling').neg_share.mean().round(3).to_dict())
# dedupe 변창흠/노형욱 to one legislator-ministry unit (국토교통부), take 노형욱 row when both exist
P['ministry']=P.committee_key+'|'+P.nominee.replace({'변창흠':'노형욱'})
P = P.sort_values('nominee').drop_duplicates(['cohort','leg_name','ministry'], keep='last')
B = P[P.in_both & (P.ruling!='independent')].copy()
B['opposed']=B.opposed_party
print('== analysis sample by cohort x opposed'); print(pd.crosstab(B.cohort,B.opposed))
print('== per-nominee overlap N (opposed / supportive)')
print(B.groupby(['cohort','nominee']).opposed.agg(N='size', n_opp='sum').assign(n_sup=lambda x:x.N-x.n_opp).to_string())
def table(S, lab):
    g = S.groupby('opposed')[['share_before','share_after','d_share','placebo_before','placebo_after','d_placebo','unnamed_before','unnamed_after','d_unnamed','n_before','n_after']].mean().round(3)
    g['N']=S.groupby('opposed').size(); print(f'== means {lab}'); print(g.T.to_string())
    for y in ['d_share','d_placebo','d_unnamed']:
        m = smf.ols(f'{y} ~ opposed + C(committee_key)', data=S).fit(cov_type='cluster', cov_kwds={'groups':S.leg_name})
        m0 = smf.ols(f'{y} ~ opposed', data=S).fit(cov_type='cluster', cov_kwds={'groups':S.leg_name})
        ci=m.conf_int().loc['opposed']; ci0=m0.conf_int().loc['opposed']
        print(f'{lab:12s} {y:10s} DiD raw={100*m0.params.opposed:+.1f}pp [{100*ci0[0]:+.1f},{100*ci0[1]:+.1f}]  commFE={100*m.params.opposed:+.1f}pp [{100*ci[0]:+.1f},{100*ci[1]:+.1f}] p={m.pvalues.opposed:.3f} N={int(m.nobs)} clusters={S.leg_name.nunique()}')
table(B[B.cohort==1],'cohort1'); table(B,'cohort1+2'); table(B[B.cohort==2],'cohort2')
# own-speech coding as alternative treatment, cohort 1+2
B['opposed']=B.opposed_speech; table(B,'speechcode')
# levels regression with legislator FE equivalent: long form
L = pd.concat([B.assign(post=0, y=B.share_before, yp=B.placebo_before), B.assign(post=1, y=B.share_after, yp=B.placebo_after)])
L['opposed']=L.opposed_party
m = smf.ols('y ~ opposed*post + C(committee_key)', data=L).fit(cov_type='cluster', cov_kwds={'groups':L.leg_name})
print('long-form interaction (opposed:post):', round(100*m.params['opposed:post'],1),'pp', m.conf_int().loc['opposed:post'].mul(100).round(1).tolist())
B.to_csv('r25/analysis_sample.csv', index=False)

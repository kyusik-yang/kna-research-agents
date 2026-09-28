import pandas as pd, numpy as np, statsmodels.formula.api as smf, pyarrow.parquet as pq
P = pd.read_csv('r25/panel.csv'); B = pd.read_csv('r25/analysis_sample.csv')
P['ministry']=P.committee_key+'|'+P.nominee.replace({'변창흠':'노형욱'})
P = P.sort_values('nominee').drop_duplicates(['cohort','leg_name','ministry'], keep='last')
P = P[P.ruling!='independent']
print('== attrition: present in both audits, by opposed_party'); print(P.groupby('opposed_party').in_both.agg(['mean','size']).round(3))
print('   before-only / after-only counts by opposed:'); print(P.assign(bo=(P.n_before>0)&(P.n_after==0), ao=(P.n_before==0)&(P.n_after>0)).groupby('opposed_party')[['bo','ao']].sum())
B['opposed']=B.opposed_party
# alt 1: log count of questions to confirmed ministry
B['cnt_b']=B.share_before*B.n_before; B['cnt_a']=B.share_after*B.n_after
B['d_logcnt']=np.log1p(B.cnt_a)-np.log1p(B.cnt_b)
# alt 2: share among named-ministry questions only
B['nshare_b']=B.share_before/(1-B.unnamed_before); B['nshare_a']=B.share_after/(1-B.unnamed_after); B['d_nshare']=B.nshare_a-B.nshare_b
for y,lab in [('d_logcnt','log count to ministry'),('d_nshare','share among named-agency Qs')]:
    S=B.dropna(subset=[y])
    m=smf.ols(f'{y} ~ opposed + C(committee_key)',data=S).fit(cov_type='cluster',cov_kwds={'groups':S.leg_name}); ci=m.conf_int().loc['opposed']
    print(f'{lab:32s} DiD={m.params.opposed:+.3f} [{ci[0]:+.3f},{ci[1]:+.3f}] p={m.pvalues.opposed:.3f} N={int(m.nobs)}')
print('mean counts: opposed', B[B.opposed==1][['cnt_b','cnt_a']].mean().round(1).tolist(), 'supportive', B[B.opposed==0][['cnt_b','cnt_a']].mean().round(1).tolist())
# power: MDE at 80% power from cohort1+2 committee-FE SE
m=smf.ols('d_share ~ opposed + C(committee_key)',data=B).fit(cov_type='cluster',cov_kwds={'groups':B.leg_name})
print(f'pooled SE={100*m.bse.opposed:.2f}pp -> MDE(80%,two-sided)={100*2.8*m.bse.opposed:.1f}pp')
# per-nominee descriptive (opposed cells N<10 -> descriptive only)
g=B.groupby(['cohort','nominee','opposed']).agg(N=('d_share','size'),before=('share_before','mean'),after=('share_after','mean'),d=('d_share','mean')).round(3).unstack('opposed')
print('== per-nominee (descriptive)'); print(g.to_string())
# tighter own-speech regex on hearing speech
mids = pq.read_table('data/dyads_16_22_v9.parquet', columns=['meeting_id','agenda','hearing_type'], filters=[('term','=',21)]).to_pandas()
mids = mids[(mids.hearing_type=='상임위원회')&mids.agenda.str.contains('국무위원후보자',na=False)&mids.agenda.str.contains('인사청문',na=False)].meeting_id.unique().tolist()
sp = pq.read_table('data/dyads_16_22_v9.parquet', columns=['meeting_id','leg_name','leg_ruling_status','direction','leg_speech'], filters=[('term','=',21),('meeting_id','in',mids)]).to_pandas()
sp=sp[sp.direction=='question']
for pat,lab in [(r'사퇴',"사퇴"),(r'부적격',"부적격"),(r'지명\s*철회|철회.{0,6}(요구|촉구)',"지명철회/철회요구"),(r'자격.{0,4}없',"자격없")]:
    hit=sp.leg_speech.fillna('').str.contains(pat)
    print(f'regex {lab:16s} question-rows hit={hit.sum():5d} ({100*hit.mean():.2f}%)  by ruling:', sp[hit].leg_ruling_status.value_counts().to_dict())

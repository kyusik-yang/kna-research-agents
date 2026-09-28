# R26 (9b + 9c): within-opposition dose test and committee-FE baseline-gap hardening
# Standing sample: workspace/r25/analysis_sample_corrected.csv (278 units, 191 legislators)
import pandas as pd, numpy as np, statsmodels.formula.api as smf

B = pd.read_csv('r25/analysis_sample_corrected.csv')
R = pd.read_csv('r25/roster.csv')

# ---- dose: total hearing question dyads a legislator directed at the ministry's nominee(s)
# 변창흠 and 노형욱 both map to land_transport|노형욱, so sum n_q across the two hearings
R = R[R.cohort > 0].copy()
R['ministry'] = R.committee_key + '|' + R.nominee.replace({'변창흠': '노형욱'})
dose = R.groupby(['cohort', 'leg_name', 'ministry']).n_q.sum().reset_index().rename(columns={'n_q': 'dose'})
B = B.merge(dose, on=['cohort', 'leg_name', 'ministry'], how='left')
assert B.dose.notna().all()

# standardize within committee-cohort cell (Scout 076 Section 4: within committee)
B['dose_z'] = B.groupby(['cohort', 'committee_key']).dose.transform(lambda s: (s - s.mean()) / s.std(ddof=0))

def cl(m, term):
    ci = m.conf_int().loc[term]
    return f'{100*m.params[term]:+.2f}pp [{100*ci[0]:+.2f}, {100*ci[1]:+.2f}] p={m.pvalues[term]:.3f} N={int(m.nobs)}'

print('=== 9b: DOSE TEST, opposition units only (d_share ~ dose_z + committee FE, cluster leg) ===')
for lab, S in [('cohort 1', B[(B.opposed == 1) & (B.cohort == 1)]),
               ('cohorts 1+2 pooled', B[B.opposed == 1])]:
    print(f'-- {lab}: N={len(S)} opposition units, clusters={S.leg_name.nunique()}')
    print('   dose distribution: median', S.dose.median(), 'IQR', list(S.dose.quantile([.25, .75])), 'max', S.dose.max())
    m = smf.ols('d_share ~ dose_z + C(committee_key)', data=S).fit(
        cov_type='cluster', cov_kwds={'groups': S.leg_name})
    print('   slope per SD:', cl(m, 'dose_z'))
    # alt measure: raw count of questions instead of z
    m2 = smf.ols('d_share ~ dose + C(committee_key)', data=S).fit(
        cov_type='cluster', cov_kwds={'groups': S.leg_name})
    print('   slope per question (raw):', cl(m2, 'dose'))
    # alt: top-tercile engager vs rest within committee
    S = S.copy()
    S['hi'] = S.groupby(['cohort', 'committee_key']).dose.transform(lambda s: (s >= s.quantile(2/3)).astype(int))
    m3 = smf.ols('d_share ~ hi + C(committee_key)', data=S).fit(
        cov_type='cluster', cov_kwds={'groups': S.leg_name})
    print('   top-tercile vs rest:', cl(m3, 'hi'))

print('\n=== secondary: full-sample interaction opposed x dose_z ===')
m = smf.ols('d_share ~ opposed * dose_z + C(committee_key)', data=B).fit(
    cov_type='cluster', cov_kwds={'groups': B.leg_name})
print('   opposed:dose_z:', cl(m, 'opposed:dose_z'))

print('\n=== 9c: BASELINE GAP with committee FE (share_before ~ opposed + C(committee), cluster leg) ===')
for lab, S in [('cohort 1', B[B.cohort == 1]), ('cohort 2', B[B.cohort == 2]), ('pooled', B)]:
    raw = (S[S.opposed == 1].share_before.mean() - S[S.opposed == 0].share_before.mean()) * 100
    m = smf.ols('share_before ~ opposed + C(committee_key)', data=S).fit(
        cov_type='cluster', cov_kwds={'groups': S.leg_name})
    print(f'-- {lab}: raw gap {raw:+.2f}pp | committee-FE gap {cl(m, "opposed")} clusters={S.leg_name.nunique()}')

print('\n=== 9c diagnostics: is the raw gap composition? ===')
# within-committee opposed share vs committee mean share_before
comp = B.groupby(['cohort', 'committee_key']).agg(mean_before=('share_before', 'mean'),
                                                  opp_frac=('opposed', 'mean'), N=('opposed', 'size'))
print(comp.round(3).to_string())
print('corr(committee mean_before, opposed fraction):', comp.mean_before.corr(comp.opp_frac).round(3))

# placebo on levels: baseline gap in placebo (named non-confirmed) share
m = smf.ols('placebo_before ~ opposed + C(committee_key)', data=B).fit(
    cov_type='cluster', cov_kwds={'groups': B.leg_name})
print('placebo_before gap (committee FE):', cl(m, 'opposed'))

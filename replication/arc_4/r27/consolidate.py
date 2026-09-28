# R27 consolidation (Critic 078 item 10b): no new estimation.
# (1) dictionary <-> sample consistency checks
# (2) exact dose 95% upper bound as a stated quantity (re-report of the R26 fit)
# (3) TOST 90% CIs for main and placebo DiD from the SAME pre-registered specification
#     (arithmetic on the existing fit at a different confidence level, per Scout 079 Section 4;
#      inclusion in Paper D is Critic's call)
import json
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

# ---------- (1) dictionaries reproduce the samples ----------
d25 = pd.DataFrame([json.loads(l) for l in open('knowledge/hand_coding/round_25.jsonl')])
R = pd.read_csv('r25/roster.csv')
m = R.merge(d25, left_on=['cohort', 'nominee', 'leg_name'],
            right_on=['cohort', 'nominee', 'leg_name'], suffixes=('_r', '_d'))
print('dict25 rows:', len(d25), '| roster rows:', len(R), '| merged:', len(m))
print('opposed_party agreement:', (m.opposed_party_r == m.opposed_party_d).mean())
print('opposed_speech agreement:', (m.opposed_speech_r == m.opposed_speech_d).mean())

d26 = pd.DataFrame([json.loads(l) for l in open('knowledge/hand_coding/round_26.jsonl')])
C3 = pd.read_csv('r26/cohort3_panel.csv')
m3 = C3.merge(d26, on=['nominee', 'leg_name'], suffixes=('_p', '_d'))
print('dict26 rows:', len(d26), '| cohort3 panel rows:', len(C3), '| merged:', len(m3))
print('opposed coding agreement:', (m3.opposed == m3.opposed_nominating_president).mean())
print('cohort3 in-both units:', int(C3.in_both.sum()),
      '| split:', C3[C3.in_both].groupby('opposed').size().to_dict())

# ---------- (2) + (3): re-report existing fits ----------
B = pd.read_csv('r25/analysis_sample_corrected.csv')

def tost(model, term, margin_pp):
    est, se = 100 * model.params[term], 100 * model.bse[term]
    lo90, hi90 = est - 1.645 * se, est + 1.645 * se
    eq = (lo90 > -margin_pp) and (hi90 < margin_pp)
    return est, se, lo90, hi90, eq

# main DiD (pre-registered spec, unchanged from R25)
mm = smf.ols('d_share ~ opposed + C(committee_key)', data=B).fit(
    cov_type='cluster', cov_kwds={'groups': B.leg_name})
mp = smf.ols('d_placebo ~ opposed + C(committee_key)', data=B).fit(
    cov_type='cluster', cov_kwds={'groups': B.leg_name})
for lab, mod in [('main DiD (d_share)', mm), ('placebo DiD (d_placebo)', mp)]:
    est, se, lo, hi, eq = tost(mod, 'opposed', 2.5)
    ci = mod.conf_int().loc['opposed'] * 100
    print(f'{lab}: {est:+.2f}pp (SE {se:.2f}) 95% [{ci[0]:+.2f},{ci[1]:+.2f}] '
          f'| TOST 90% [{lo:+.2f},{hi:+.2f}] equiv within +/-2.5pp: {eq}')

# dose bound (re-report of R26 9b fit)
Rr = pd.read_csv('r25/roster.csv')
Rr = Rr[Rr.cohort > 0].copy()
Rr['ministry'] = Rr.committee_key + '|' + Rr.nominee.replace({'변창흠': '노형욱'})
dose = Rr.groupby(['cohort', 'leg_name', 'ministry']).n_q.sum().reset_index().rename(columns={'n_q': 'dose'})
B = B.merge(dose, on=['cohort', 'leg_name', 'ministry'], how='left')
B['dose_z'] = B.groupby(['cohort', 'committee_key']).dose.transform(lambda s: (s - s.mean()) / s.std(ddof=0))
S = B[B.opposed == 1]
md = smf.ols('d_share ~ dose_z + C(committee_key)', data=S).fit(
    cov_type='cluster', cov_kwds={'groups': S.leg_name})
ci = md.conf_int().loc['dose_z'] * 100
print(f'dose slope pooled: {100*md.params.dose_z:+.2f}pp/SD, 95% upper bound = {ci[1]:+.2f}pp/SD '
      f'(N={int(md.nobs)}, clusters={S.leg_name.nunique()})')

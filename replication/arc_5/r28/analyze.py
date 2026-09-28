# R28: descriptives + headline interaction model
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

df = pd.read_csv('r28/bills_panel.csv')

print('=== Overall rates (pooled 17-22) ===')
print('strict:', df.passed_strict.mean().round(4), 'absorb-incl:', df.passed_absorb.mean().round(4),
      'N=', len(df))

print('\n=== Passage rate (strict) by first_term x prop_year, pooled ===')
tab = df.pivot_table(index='prop_year', columns='first_term', values='passed_strict',
                     aggfunc=['mean', 'count'])
tab.columns = ['re_rate', 'ft_rate', 're_N', 'ft_N']
tab['gap_pp'] = (tab.ft_rate - tab.re_rate) * 100
print(tab.round(4))

print('\n=== Same, absorb-inclusive ===')
tab2 = df.pivot_table(index='prop_year', columns='first_term', values='passed_absorb', aggfunc='mean')
tab2.columns = ['re', 'ft']
tab2['gap_pp'] = (tab2.ft - tab2.re) * 100
print(tab2.round(4))

print('\n=== Gap (strict, pp) by assembly x prop_year ===')
g = df.groupby(['assembly', 'prop_year']).apply(
    lambda d: pd.Series({
        'gap_pp': (d.loc[d.first_term == 1, 'passed_strict'].mean()
                   - d.loc[d.first_term == 0, 'passed_strict'].mean()) * 100,
        'ft_N': (d.first_term == 1).sum(), 're_N': (d.first_term == 0).sum()}),
    include_groups=False)
print(g.round(2))

# ---- Headline model ----
df['py_c'] = df['prop_year'] - 1  # year-1 = 0 so main effect = year-1 gap
MODEL_COLS = ['first_term', 'py_c', 'assembly', 'bloc', 'election_type',
              'committee_nm', 'rst_mona_cd', 'passed_strict', 'passed_absorb', 'passed_12m']
print('\nNaN drop for model:', len(df) - len(df.dropna(subset=MODEL_COLS)), 'rows (committee_nm etc.)')
df = df.dropna(subset=MODEL_COLS).copy()

def run(d, y, label, extra=''):
    d = d.dropna(subset=MODEL_COLS).copy()
    f = (f'{y} ~ first_term * py_c + C(assembly) + C(bloc) + C(election_type)'
         f' + C(committee_nm){extra}')
    m = smf.ols(f, data=d).fit(cov_type='cluster',
                               cov_kwds={'groups': d['rst_mona_cd']}, use_t=True)
    b1, b2 = m.params['first_term'], m.params['first_term:py_c']
    ci1, ci2 = m.conf_int().loc['first_term'], m.conf_int().loc['first_term:py_c']
    print(f'{label}: year1 gap {b1*100:+.2f}pp [{ci1[0]*100:+.2f},{ci1[1]*100:+.2f}] '
          f'| interaction {b2*100:+.2f}pp/yr [{ci2[0]*100:+.2f},{ci2[1]*100:+.2f}] '
          f'p={m.pvalues["first_term:py_c"]:.3f} N={int(m.nobs)} '
          f'clusters={d.rst_mona_cd.nunique()}')
    return m

print('\n=== Headline: LPM, cluster by member ===')
run(df, 'passed_strict', 'strict, pooled 17-22')
run(df, 'passed_absorb', 'absorb-inclusive       ')
run(df, 'passed_12m', '12m-horizon (censor-clean)')
run(df[df.prop_year <= 3], 'passed_strict', 'strict, drop year-4    ')
run(df[df.assembly <= 21], 'passed_strict', 'strict, drop 22nd (censored)')

print('\n=== Per-assembly interaction (strict) ===')
for a in range(17, 23):
    d = df[df.assembly == a]
    f = 'passed_strict ~ first_term * py_c + C(bloc) + C(election_type) + C(committee_nm)'
    m = smf.ols(f, data=d).fit(cov_type='cluster', cov_kwds={'groups': d['rst_mona_cd']}, use_t=True)
    b1, b2 = m.params['first_term'], m.params['first_term:py_c']
    ci2 = m.conf_int().loc['first_term:py_c']
    print(f'A{a}: year1 {b1*100:+.2f}pp | interact {b2*100:+.2f}pp/yr '
          f'[{ci2[0]*100:+.2f},{ci2[1]*100:+.2f}] N={int(m.nobs)}')

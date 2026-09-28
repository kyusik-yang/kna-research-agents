# R28 robustness: gap decomposition, member-level equal weights, absorption-only channel, MDE
import pandas as pd
import numpy as np
import statsmodels.formula.api as smf

df = pd.read_csv('r28/bills_panel.csv')
df['py_c'] = df['prop_year'] - 1
df['absorb_only'] = ((df.passed_absorb == 1) & (df.passed_strict == 0)).astype(int)
MODEL_COLS = ['first_term', 'py_c', 'assembly', 'bloc', 'election_type',
              'committee_nm', 'rst_mona_cd']
df = df.dropna(subset=MODEL_COLS).copy()

def fit(d, y, rhs, label):
    m = smf.ols(f'{y} ~ {rhs}', data=d).fit(
        cov_type='cluster', cov_kwds={'groups': d['rst_mona_cd']}, use_t=True)
    b1 = m.params.get('first_term', np.nan)
    b2 = m.params.get('first_term:py_c', np.nan)
    se2 = m.bse.get('first_term:py_c', np.nan)
    print(f'{label}: year1 {b1*100:+.2f}pp | interact {b2*100:+.2f}pp/yr '
          f'(SE {se2*100:.2f}) p={m.pvalues.get("first_term:py_c", np.nan):.3f} N={int(m.nobs)}')
    return m

print('=== Gap decomposition (strict outcome, pooled) ===')
fit(df, 'passed_strict', 'first_term * py_c + C(assembly)', 'assembly FE only        ')
fit(df, 'passed_strict', 'first_term * py_c + C(assembly) + C(bloc) + C(election_type)',
    '+ bloc + election_type ')
m_full = fit(df, 'passed_strict',
             'first_term * py_c + C(assembly) + C(bloc) + C(election_type) + C(committee_nm)',
             '+ committee FE (full)  ')
se = m_full.bse['first_term:py_c']
print(f'MDE (80% power, 5% two-sided) for interaction: {2.8*se*100:.2f}pp/yr')

print('\n=== Absorption-only outcome (대안반영/수정안반영 폐기, excl. direct passage) ===')
fit(df, 'absorb_only', 'first_term * py_c + C(assembly) + C(bloc) + C(election_type) + C(committee_nm)',
    'absorb-only, full spec ')
tab = df.pivot_table(index='prop_year', columns='first_term', values='absorb_only', aggfunc='mean')
tab.columns = ['re', 'ft']
tab['gap_pp'] = (tab.ft - tab.re) * 100
print(tab.round(4))

print('\n=== Member-level (equal weight per member-year), strict ===')
my = (df.groupby(['assembly', 'rst_mona_cd', 'first_term', 'prop_year'], as_index=False)
        .agg(rate=('passed_strict', 'mean'), n_bills=('passed_strict', 'size')))
my['py_c'] = my['prop_year'] - 1
print('member-year cells:', len(my), '| cells with n_bills<3:', (my.n_bills < 3).sum())
m = smf.ols('rate ~ first_term * py_c + C(assembly)', data=my).fit(
    cov_type='cluster', cov_kwds={'groups': my['rst_mona_cd']}, use_t=True)
ci = m.conf_int().loc['first_term:py_c'] * 100
print(f'all cells: year1 {m.params.first_term*100:+.2f}pp | interact '
      f'{m.params["first_term:py_c"]*100:+.2f}pp/yr [{ci[0]:+.2f},{ci[1]:+.2f}] '
      f'p={m.pvalues["first_term:py_c"]:.3f} N={int(m.nobs)} clusters={my.rst_mona_cd.nunique()}')
my3 = my[my.n_bills >= 3]
m3 = smf.ols('rate ~ first_term * py_c + C(assembly)', data=my3).fit(
    cov_type='cluster', cov_kwds={'groups': my3['rst_mona_cd']}, use_t=True)
print(f'cells n>=3: interact {m3.params["first_term:py_c"]*100:+.2f}pp/yr '
      f'p={m3.pvalues["first_term:py_c"]:.3f} N={int(m3.nobs)}')

print('\n=== 17th Assembly outlier check (only per-assembly negative interaction) ===')
d17 = df[df.assembly == 17]
print(d17.groupby(['prop_year', 'first_term'])['passed_strict'].agg(['mean', 'count']).round(4))

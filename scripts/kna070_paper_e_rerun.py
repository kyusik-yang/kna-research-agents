#!/usr/bin/env python3
# Paper E (round 30): the key first-term comparison, rerun for the kna 0.7.0
# note (KNA_070_PUBLISHED.md). The panel construction copies the round 28
# build script and the models copy the round 29 scripts (year-1 strict gap,
# equivalence tests, the absorption step with and without proposal-year
# effects, per-year interactions, Wald test). Only the data directory, the
# first-term definition and an optional proposal-date cutoff change.
#
# Usage:
#   python3 scripts/kna070_paper_e_rerun.py VARIANT DATA_DIR CODING [CUTOFF] [--out DIR]
#   CODING reelection   first_term = reelection == '초선' (as published)
#   CODING term_number  first_term = term_number == 1 (kna 0.7.0)
#   CUTOFF              keep bills proposed on or before this date (YYYY-MM-DD)
# Writes result_VARIANT.json to --out (default: the current directory).
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

ap = argparse.ArgumentParser()
ap.add_argument("variant")
ap.add_argument("data_dir")
ap.add_argument("coding", choices=["reelection", "term_number"])
ap.add_argument("cutoff", nargs="?")
ap.add_argument("--out", default=".")
args = ap.parse_args()
variant, DATA, coding = args.variant, args.data_dir, args.coding
cutoff = pd.Timestamp(args.cutoff) if args.cutoff else None
OUT = Path(args.out)
OUT.mkdir(parents=True, exist_ok=True)

TERM_START = {17: '2004-05-30', 18: '2008-05-30', 19: '2012-05-30',
              20: '2016-05-30', 21: '2020-05-30', 22: '2024-05-30'}
CONS = {'한나라당', '새누리당', '자유한국당', '미래통합당', '국민의힘', '친박연대', '자유선진당',
        '미래한국당', '바른정당', '개혁신당'}
LIB = {'열린우리당', '대통합민주신당', '통합민주당', '민주당', '민주통합당', '새정치민주연합',
       '더불어민주당', '더불어시민당', '새정치국민회의', '조국혁신당', '새로운미래', '민주연합'}

# ---- panel (r28/build.py) ----
rows = []
for a in range(17, 23):
    b = pd.read_parquet(f'{DATA}/master_bills_{a}.parquet')
    m = pd.read_parquet(f'{DATA}/members_{a}.parquet')
    mb = b[(b['ppsr_kind'] == '의원') & (b['bill_kind'] == '법률안')].copy()
    mb = mb[mb['rst_mona_cd'].notna()]
    start = pd.Timestamp(TERM_START[a])
    mb['ppsl_dt'] = pd.to_datetime(mb['ppsl_dt'])
    if cutoff is not None:
        mb = mb[mb['ppsl_dt'] <= cutoff]
    mb['months_in'] = (mb['ppsl_dt'] - start).dt.days / 30.44
    mb['prop_year'] = np.clip(np.floor(mb['months_in'] / 12).astype(int) + 1, 1, 4)
    mb['passed_strict'] = mb['proc_rslt'].isin(['원안가결', '수정가결']).astype(int)
    mb['passed_absorb'] = mb['proc_rslt'].isin(
        ['원안가결', '수정가결', '대안반영폐기', '수정안반영폐기']).astype(int)
    cols = ['mona_cd', 'member_name', 'party', 'election_type', 'reelection']
    if 'term_number' in m.columns:
        cols.append('term_number')
    mem = m[cols].drop_duplicates('mona_cd')
    assert mem['mona_cd'].is_unique
    mb = mb.merge(mem, left_on='rst_mona_cd', right_on='mona_cd', how='inner', validate='m:1')
    if coding == 'reelection':
        mb['first_term'] = (mb['reelection'] == '초선').astype(int)
    else:
        mb['first_term'] = (mb['term_number'] == 1).astype(int)
    if 'term_number' in mb.columns:
        mb['ft_reel'] = (mb['reelection'] == '초선').astype(int)
        mb['ft_term'] = (mb['term_number'] == 1).astype(int)
    mb['bloc'] = np.where(mb['party'].isin(CONS), 'cons',
                 np.where(mb['party'].isin(LIB), 'lib', 'minor'))
    mb['assembly'] = a
    rows.append(mb)
df = pd.concat(rows, ignore_index=True)

res = {'variant': variant, 'coding': coding, 'cutoff': args.cutoff}
res['panel_n'] = int(len(df))
res['panel_n_by_assembly'] = {int(k): int(v) for k, v in df.groupby('assembly').size().items()}
res['first_term_bills'] = int(df['first_term'].sum())
res['first_term_share'] = float(df['first_term'].mean())
res['strict_rate'] = float(df['passed_strict'].mean())
res['absorb_incl_rate'] = float(df['passed_absorb'].mean())
if 'ft_term' in df.columns:
    res['bills_reel_not_ft_but_term1'] = int(((df.ft_reel == 0) & (df.ft_term == 1)).sum())
    res['bills_reel_ft_but_not_term1'] = int(((df.ft_reel == 1) & (df.ft_term == 0)).sum())

# ---- models (r29/depth.py, r29/depth2.py) ----
df = df[df['committee_nm'].notna()].copy()
df['absorbed'] = ((df['passed_absorb'] == 1) & (df['passed_strict'] == 0)).astype(int)
df['late'] = (df['prop_year'] >= 2).astype(int)
FE = ' + C(assembly) + C(bloc) + C(election_type) + C(committee_nm)'
CL = lambda d: {'groups': d['rst_mona_cd']}
res['est_n'] = int(len(df))

# year-1 strict gap and TOST (depth.py section 6)
y1s = df[df['prop_year'] == 1]
m1 = smf.ols('passed_strict ~ first_term' + FE, y1s).fit(cov_type='cluster', cov_kwds=CL(y1s))
b, se = m1.params['first_term'], m1.bse['first_term']
res['y1_strict_gap_pp'] = float(b * 100)
res['y1_strict_gap_se_pp'] = float(se * 100)
res['y1_n'] = int(m1.nobs)
res['tost2_max_p'] = float(max(1 - stats.norm.cdf((b + 0.02) / se), 1 - stats.norm.cdf((0.02 - b) / se)))
res['tost1_max_p'] = float(max(1 - stats.norm.cdf((b + 0.01) / se), 1 - stats.norm.cdf((0.01 - b) / se)))

# step without proposal-year effects (depth.py section 1, m_step)
ms = smf.ols('absorbed ~ first_term + late + first_term:late' + FE, df).fit(
    cov_type='cluster', cov_kwds=CL(df))
res['step_noyear_ft_pp'] = float(ms.params['first_term'] * 100)
res['step_noyear_ft_p'] = float(ms.pvalues['first_term'])
res['step_noyear_pp'] = float(ms.params['first_term:late'] * 100)
res['step_noyear_se_pp'] = float(ms.bse['first_term:late'] * 100)

# step with proposal-year effects (depth2.py mA) and per-year (mC)
mA = smf.ols('absorbed ~ first_term + C(prop_year) + first_term:late' + FE, df).fit(
    cov_type='cluster', cov_kwds=CL(df))
mB = smf.ols('absorbed ~ first_term + C(prop_year) + first_term:prop_year' + FE, df).fit(
    cov_type='cluster', cov_kwds=CL(df))
mC = smf.ols('absorbed ~ first_term*C(prop_year)' + FE, df).fit(
    cov_type='cluster', cov_kwds=CL(df))
res['step_ft_pp'] = float(mA.params['first_term'] * 100)
res['step_ft_se_pp'] = float(mA.bse['first_term'] * 100)
res['step_pp'] = float(mA.params['first_term:late'] * 100)
res['step_se_pp'] = float(mA.bse['first_term:late'] * 100)
res['step_p'] = float(mA.pvalues['first_term:late'])
res['step_n'] = int(mA.nobs)
res['bic_step_minus_linear'] = float(mA.bic - mB.bic)
for y in (2, 3, 4):
    k = f'first_term:C(prop_year)[T.{y}]'
    res[f'yr{y}_pp'] = float(mC.params[k] * 100)
    res[f'yr{y}_se_pp'] = float(mC.bse[k] * 100)
w = mC.wald_test('first_term:C(prop_year)[T.2] = first_term:C(prop_year)[T.3], '
                 'first_term:C(prop_year)[T.3] = first_term:C(prop_year)[T.4]', scalar=True)
res['wald_yr_equal_p'] = float(w.pvalue)

(OUT / f'result_{variant}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1) + '\n',
                                            encoding='utf-8')
print(json.dumps(res, ensure_ascii=False, indent=1))

import os  # added by replicate.py for KBL_DATA
# R28 Arc 5 opening: first-term learning - build bill-level analysis file
# Population: member-sponsored law bills (ppsr_kind=='의원', bill_kind=='법률안'), 17th-22nd NA
# Merge key: rst_mona_cd -> members mona_cd (uid, homonym-safe per R27 policy)
import pandas as pd
import numpy as np

DATA = os.environ["KBL_DATA"]
TERM_START = {17: '2004-05-30', 18: '2008-05-30', 19: '2012-05-30',
              20: '2016-05-30', 21: '2020-05-30', 22: '2024-05-30'}

# Party bloc dictionary (conservative / liberal / minor) - coarse, stable across renames
CONS = {'한나라당', '새누리당', '자유한국당', '미래통합당', '국민의힘', '친박연대', '자유선진당',
        '미래한국당', '바른정당', '개혁신당'}
LIB = {'열린우리당', '대통합민주신당', '통합민주당', '민주당', '민주통합당', '새정치민주연합',
       '더불어민주당', '더불어시민당', '새정치국민회의', '조국혁신당', '새로운미래', '민주연합'}

rows = []
for a in range(17, 23):
    b = pd.read_parquet(f'{DATA}/master_bills_{a}.parquet')
    m = pd.read_parquet(f'{DATA}/members_{a}.parquet')
    mb = b[(b['ppsr_kind'] == '의원') & (b['bill_kind'] == '법률안')].copy()
    mb = mb[mb['rst_mona_cd'].notna()]
    start = pd.Timestamp(TERM_START[a])
    mb['ppsl_dt'] = pd.to_datetime(mb['ppsl_dt'])
    mb['months_in'] = (mb['ppsl_dt'] - start).dt.days / 30.44
    mb['prop_year'] = np.clip(np.floor(mb['months_in'] / 12).astype(int) + 1, 1, 4)
    # outcomes
    mb['passed_strict'] = mb['proc_rslt'].isin(['원안가결', '수정가결']).astype(int)
    mb['passed_absorb'] = mb['proc_rslt'].isin(
        ['원안가결', '수정가결', '대안반영폐기', '수정안반영폐기']).astype(int)
    mb['proc_dt'] = pd.to_datetime(mb['proc_dt'])
    mb['passed_12m'] = ((mb['passed_strict'] == 1) &
                        ((mb['proc_dt'] - mb['ppsl_dt']).dt.days <= 365)).astype(int)
    mem = m[['mona_cd', 'member_name', 'party', 'election_type', 'reelection']].drop_duplicates('mona_cd')
    assert mem['mona_cd'].is_unique, f'non-unique mona_cd in members_{a}'
    mb = mb.merge(mem, left_on='rst_mona_cd', right_on='mona_cd', how='inner', validate='m:1')
    mb['first_term'] = (mb['reelection'] == '초선').astype(int)
    mb['bloc'] = np.where(mb['party'].isin(CONS), 'cons',
                 np.where(mb['party'].isin(LIB), 'lib', 'minor'))
    mb['assembly'] = a
    keep = mb[['assembly', 'bill_id', 'rst_mona_cd', 'member_name', 'first_term',
               'reelection', 'bloc', 'election_type', 'committee_nm', 'prop_year',
               'months_in', 'passed_strict', 'passed_absorb', 'passed_12m', 'proc_rslt']]
    rows.append(keep)
    print(f'A{a}: N={len(keep)}, first-term share of bills={keep.first_term.mean():.3f}, '
          f'strict rate={keep.passed_strict.mean():.4f}')

df = pd.concat(rows, ignore_index=True)
df.to_csv('r28/bills_panel.csv', index=False)
print('TOTAL', len(df))
print(df.groupby('prop_year')['passed_strict'].agg(['mean', 'count']))

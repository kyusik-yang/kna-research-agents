# R26 (9d): Build cohort 3 - May 2022 Yoon cabinet hearings, nominating-president coding
# Before-audit = Oct 2021 (pre-wonguseong committees), after-audit = Oct 2022 (post-wonguseong)
# Labeled an Eldes-style ruling-status stratum, DESCRIPTIVE-PLUS only (Critic 075 Commitment 9d)
import pandas as pd, numpy as np, json

d = pd.read_parquet('dyads21_meta.parquet')

# nominee -> (committee_key, ministry prefixes). 정호영 withdrawn 2022-05-23 -> excluded.
# 김인철 (education) withdrew 2022-05-03 before any hearing sat -> no dyads, not in data.
C3 = {
 '조승환': ('agriculture', ['해양수산부']),
 '정황근': ('agriculture', ['농림축산식품부']),
 '박보균': ('culture', ['문화체육관광부']),
 '이종섭': ('defense', ['국방부']),
 '한화진': ('environment_labor', ['환경부', '환경']),
 '이정식': ('environment_labor', ['고용노동부', '고용노동']),
 '추경호': ('finance', ['기획재정부']),
 '박진':  ('foreign_affairs', ['외교부']),
 '권영세': ('foreign_affairs', ['통일부']),
 '김현숙': ('gender_family', ['여성가족부']),
 '이창양': ('industry', ['산업통상자원부']),
 '이영':  ('industry', ['중소벤처기업부']),
 '한동훈': ('judiciary', ['법무부']),
 '원희룡': ('land_transport', ['국토교통부']),
 '이상민': ('public_admin', ['행정안전부']),
 '이종호': ('science_ict', ['과학기술정보통신부']),
}
WITHDRAWN = {'정호영'}  # heard 2022-05-03, withdrew 2022-05-23 unappointed
# nominating president-elect 윤석열 (PPP); 국민의당 merged May 2022.
# HAZARD (R25): leg_party is a term-start snapshot, so PPP members appear as
# 미래통합당 / 미래한국당 (satellite). Both must be in the ruling set or 78 supportive
# members are silently miscoded as opposed - verified live in the first run of this script.
RULING_C3 = {'국민의힘', '국민의당', '미래통합당', '미래한국당'}

hq = d[(d.date >= '2022-04-20') & (d.date <= '2022-05-31') & (d.hearing_type == '상임위원회')
       & d.agenda.str.contains('인사청문', na=False) & (d.direction == 'question')
       & (d.witness_role == 'minister_nominee')]

roster = hq.groupby(['witness_name', 'leg_name', 'leg_member_uid']).agg(
    committee_key=('committee_key', 'first'), party=('leg_party', 'first'),
    n_q=('leg_speech', 'size') if 'leg_speech' in hq.columns else ('direction', 'size')).reset_index()
roster = roster.rename(columns={'witness_name': 'nominee'})
roster['withdrawn'] = roster.nominee.isin(WITHDRAWN).astype(int)
roster = roster[roster.party != '무소속']
roster['opposed'] = (~roster.party.isin(RULING_C3)).astype(int)

# C5 artifact FIRST: hand-coding dictionary for the cohort introduced this round
with open('knowledge/hand_coding/round_26.jsonl', 'w') as f:
    for _, r in roster.iterrows():
        f.write(json.dumps(dict(
            cohort=3, committee_key=r.committee_key, nominee=r.nominee, leg_name=r.leg_name,
            leg_member_uid=None if pd.isna(r.leg_member_uid) else str(r.leg_member_uid),
            party=r.party, n_hearing_questions=int(r.n_q), withdrawn=int(r.withdrawn),
            opposed_nominating_president=int(r.opposed),
            coding_rule="opposed = term-snapshot leg_party not in {국민의힘, 국민의당, 미래통합당, 미래한국당} (nominating president-elect 윤석열, PPP; satellite/predecessor labels included because leg_party is a term-start snapshot - R25 hazard); 무소속 dropped"),
            ensure_ascii=False) + '\n')
print('round_26.jsonl written:', len(roster), 'legislator-nominee rows')

roster = roster[roster.withdrawn == 0]

# audit shares: before = Oct 2021, after = Oct 2022, same committee as hearing
a = d[(d.hearing_type == '국정감사') & (d.direction == 'question')].copy()
a['year'] = a.date.str[:4]
confirmed_by_comm = {}
for nom, (ck, pref) in C3.items():
    confirmed_by_comm.setdefault(ck, set()).update(pref)

out = []
for _, r in roster.iterrows():
    ck, pref = C3[r.nominee]
    rec = r.to_dict()
    for tag, yr in [('before', '2021'), ('after', '2022')]:
        sub = a[(a.committee_key == ck) & (a.year == yr) & (a.leg_name == r.leg_name)]
        rec[f'n_{tag}'] = len(sub)
        if len(sub):
            named = sub.witness_ministry_normalized.notna()
            isconf = sub.witness_ministry_normalized.fillna('').str.startswith(tuple(confirmed_by_comm[ck]))
            rec[f'share_{tag}'] = sub.witness_ministry_normalized.fillna('').str.startswith(tuple(pref)).mean()
            rec[f'placebo_{tag}'] = (named & ~isconf).mean()
        else:
            rec[f'share_{tag}'] = np.nan
            rec[f'placebo_{tag}'] = np.nan
    out.append(rec)
P = pd.DataFrame(out)
P['in_both'] = (P.n_before > 0) & (P.n_after > 0)
P['d_share'] = P.share_after - P.share_before
P['d_placebo'] = P.placebo_after - P.placebo_before
P.to_csv('r26/cohort3_panel.csv', index=False)

B = P[P.in_both]
print('\ncohort 3: roster', len(P), '| in both audits', len(B))
print('overlap per nominee (in_both):')
print(P.groupby('nominee').in_both.sum().sort_values().to_string())
print('\nopposed x in_both:')
print(pd.crosstab(P.opposed, P.in_both))
g = B.groupby('opposed').agg(N=('d_share', 'size'), before=('share_before', 'mean'),
                             after=('share_after', 'mean'), d_share=('d_share', 'mean'),
                             d_placebo=('d_placebo', 'mean')).round(3)
print('\nDESCRIPTIVE means (no inference; wonguseong overlap collapse):')
print(g.to_string())
raw_did = (g.loc[1, 'd_share'] - g.loc[0, 'd_share']) * 100 if set(g.index) == {0, 1} else np.nan
print(f'\nraw DiD (descriptive only): {raw_did:+.1f}pp')
print('cells below N=10 per nominee-x-opposed:')
cell = B.groupby(['nominee', 'opposed']).size()
print((cell < 10).sum(), 'of', len(cell), 'cells below 10')

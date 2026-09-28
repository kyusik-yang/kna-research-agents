import pandas as pd, numpy as np, pyarrow.parquet as pq, re, json
d = pd.read_parquet('dyads21_meta.parquet')
# ---- cohort definitions: (date, committee_key, nominee, ministry_prefixes, cohort, note)
H = [
 ('2020-12-22','public_admin','전해철',['행정안전부'],1,''),
 ('2020-12-22','health_welfare','권덕철',['보건복지부'],1,''),
 ('2020-12-23','land_transport','변창흠',['국토교통부'],1,'resigned 2021-04; ministry incumbent at Oct-2021 audit is 노형욱'),
 ('2020-12-24','land_transport','변창흠',['국토교통부'],1,'day 2'),
 ('2020-12-24','gender_family','정영애',['여성가족부'],1,''),
 ('2021-01-20','environment_labor','한정애',['환경부','환경'],1,''),
 ('2021-02-03','industry','권칠승',['중소벤처기업부'],1,''),
 ('2021-02-05','foreign_affairs','정의용',['외교부'],1,''),
 ('2021-02-09','culture','황희',['문화체육관광부'],1,''),
 ('2021-05-04','land_transport','노형욱',['국토교통부'],1,''),
 ('2021-05-04','industry','문승욱',['산업통상자원부'],1,''),
 ('2021-05-04','agriculture','박준영',['해양수산부'],0,'WITHDRAWN 2021-05-13, unappointed -> excluded'),
 ('2021-05-04','science_ict','임혜숙',['과학기술정보통신부'],1,''),
 ('2021-05-04','environment_labor','안경덕',['고용노동부','고용노동'],1,''),
 ('2023-05-22','political_affairs','박민식',['국가보훈'],2,'국가보훈처->국가보훈부 June 2023; prefix match'),
 ('2023-07-21','foreign_affairs','김영호',['통일부'],2,''),
 ('2023-09-13','industry','방문규',['산업통상자원부'],2,''),
 ('2023-09-27','defense','신원식',['국방부'],2,''),
 ('2023-10-05','culture','유인촌',['문화체육관광부'],2,''),
 ('2023-10-05','gender_family','김행',['여성가족부'],0,'WITHDRAWN 2023-10-12 -> excluded'),
]
H = pd.DataFrame(H, columns=['date','committee_key','nominee','prefixes','cohort','note'])
AUD = {1:('2020','2021'), 2:('2022','2023')}
# ---- hearing meetings and questioners
hm = d[(d.hearing_type=='상임위원회') & d.agenda.str.contains('인사청문', na=False) & d.agenda.str.contains('국무위원후보자', na=False)]
rows=[]
for _,h in H.iterrows():
    m = hm[(hm.date==h.date)&(hm.committee_key==h.committee_key)&(hm.agenda.str.contains(h.nominee, na=False))]
    if h.nominee=='변창흠' and h.date=='2020-12-24': m = hm[(hm.date==h.date)&(hm.committee_key==h.committee_key)&hm.agenda.str.contains('변창흠',na=False)]
    for mid in m.meeting_id.unique():
        rows.append(dict(meeting_id=mid, **h.to_dict()))
HM = pd.DataFrame(rows)
mids = HM.meeting_id.unique().tolist()
print('hearing meetings matched', len(mids))
# pull hearing speech for own-speech coding
sp = pq.read_table('data/dyads_16_22_v9.parquet', columns=['meeting_id','leg_name','leg_member_uid','leg_party','leg_ruling_status','direction','leg_speech'],
                   filters=[('term','=',21),('meeting_id','in',mids)]).to_pandas()
sp = sp[sp.direction=='question'].merge(HM[['meeting_id','nominee','committee_key','prefixes','cohort','note']], on='meeting_id')
pat = r'사퇴|부적격|철회|지명\s*철회|임명\s*반대|자격\s*(?:이|은)?\s*없'
sp['neg'] = sp.leg_speech.fillna('').str.contains(pat)
roster = sp.groupby(['cohort','committee_key','nominee','leg_name','leg_member_uid']).agg(
    party=('leg_party','first'), ruling=('leg_ruling_status','first'), n_q=('leg_speech','size'), neg_share=('neg','mean')).reset_index()
roster['opposed_party'] = (roster.ruling=='opposition').astype(int)
roster['opposed_speech'] = (roster.neg_share>0).astype(int)
roster = roster.merge(HM.drop_duplicates('nominee')[['nominee','prefixes']], on='nominee')
# ---- audit shares
a = d[(d.hearing_type=='국정감사')&(d.direction=='question')].copy(); a['year']=a.date.str[:4]
def share(sub, prefixes):
    return sub.witness_ministry_normalized.fillna('').str.startswith(tuple(prefixes)).mean()
out=[]
confirmed_by_comm = roster[roster.cohort>0].groupby(['cohort','committee_key']).prefixes.apply(lambda s: sorted({p for l in s for p in l})).to_dict()
for _,r in roster[roster.cohort>0].iterrows():
    yb, ya = AUD[r.cohort]
    rec = r.to_dict()
    for tag,yr in [('before',yb),('after',ya)]:
        sub = a[(a.committee_key==r.committee_key)&(a.year==yr)&(a.leg_name==r.leg_name)]
        rec[f'n_{tag}'] = len(sub)
        rec[f'share_{tag}'] = share(sub, r.prefixes) if len(sub) else np.nan
        conf = confirmed_by_comm[(r.cohort, r.committee_key)]
        named = sub.witness_ministry_normalized.notna()
        isconf = sub.witness_ministry_normalized.fillna('').str.startswith(tuple(conf))
        rec[f'placebo_{tag}'] = (named & ~isconf).mean() if len(sub) else np.nan   # other named agencies in same committee, not confirmed this cycle
        rec[f'unnamed_{tag}'] = (~named).mean() if len(sub) else np.nan            # public corps / local govts / independents
    out.append(rec)
P = pd.DataFrame(out)
P['in_both'] = (P.n_before>0)&(P.n_after>0)
P['d_share'] = P.share_after - P.share_before
P['d_placebo'] = P.placebo_after - P.placebo_before
P['d_unnamed'] = P.unnamed_after - P.unnamed_before
P.drop(columns='prefixes').to_csv('r25/panel.csv', index=False)
roster.drop(columns='prefixes').to_csv('r25/roster.csv', index=False)
# hand-coding artifact (C5): one row per legislator-nominee
with open('knowledge/hand_coding/round_25.jsonl','w') as f:
    for _,r in roster.iterrows():
        f.write(json.dumps(dict(cohort=int(r.cohort), committee_key=r.committee_key, nominee=r.nominee, leg_name=r.leg_name,
            leg_member_uid=None if pd.isna(r.leg_member_uid) else str(r.leg_member_uid), party=r.party, ruling_status=r.ruling,
            n_hearing_questions=int(r.n_q), neg_language_share=round(float(r.neg_share),3),
            opposed_party=int(r.opposed_party), opposed_speech=int(r.opposed_speech),
            coding_rule='opposed_party = leg_ruling_status==opposition at hearing date; opposed_speech = any hearing question matching /사퇴|부적격|철회|지명철회|임명반대|자격없/'), ensure_ascii=False)+'\n')
print('roster rows', len(roster), 'panel rows', len(P), 'in_both', P.in_both.sum())

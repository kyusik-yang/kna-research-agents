---
author: "Analyst (KNA Data Expert)"
date: "2026-08-24 00:40"
type: [data_report]
references: ["10.1111/lsq.12440", "10.18854/kpsr.2008.42.2.008", "10.18808/jopr.2018.2.1", "10.18854/kpsr.2020.54.2.004", "10.29152/koiks.2018.49.2.293", "10.1017/s0007123425101221"]
---

# Confirmation Opposition Does Not Carry into the Audit: The Opposed-vs-Supportive DiD on the Confirmed Ministry's Question Share is -1pp (95% CI -3.0 to +1.3, N=278), the +5pp Threshold is Excluded, and the Placebo Agencies Move the Same Way

```yaml
round: R25 (Arc 4 opening, Season 2 prediction test)
prediction_tested: Scout 073 Section 1 - opposed-minus-supportive DiD on confirmed-ministry share >= +5pp
baseline_written_before_computing: yes (Section 2)
result: prediction FAILS on cohort 1, cohort 2, and pooled; falsifier condition in topic_gate.md is met
artifacts: knowledge/hand_coding/round_25.jsonl (400 legislator-nominee rows); workspace/r25/{build,analyze,robust,recode}.py
series_note: no ideal points used this round
```

## Rejected Paths

Before committing to the specification below, I considered and rejected:

- **Code opposition from the dyads' own `leg_ruling_status` field.** Rejected after inspection: the field is term-fixed. In the 2023 hearings 더불어민주당 is still labeled `ruling` and 국민의힘 members still carry their 2020 `미래통합당` label, so 88 of 97 cohort-2 rows would have been inverted. I recode opposition as "legislator's party is not the president's party at the hearing date" (Section 3). Cohort 1 is unaffected.
- **Use own-speech negative language (사퇴, 부적격, 지명 철회) as the treatment.** Rejected because the tightest regexes hit under 0.4% of hearing question rows (사퇴 119 rows, 부적격 34, 지명철회/철회 요구 11) and disagree with the party line in 138 of 365 rows; it is reported as a diagnostic only.
- **Pool the May 2022 Yoon-cabinet cohort for power.** Rejected per Scout 073 Section 4 and reinforced here: those hearings sat before the May 10 inauguration, so any date-based ruling-status coding is ambiguous by construction, on top of the 원구성 overlap collapse.
- **Restrict the denominator to dyads with a named ministry.** Rejected as the headline because Scout fixed the outcome as the share of all question dyads; I run it as an alternative measure (Section 5).
- **Widen to non-minister nominees (경찰청장, 국세청장, 방통위원장).** Rejected per exclusion criterion 2; the minister sample clears N>=10 in every nominee cell (Section 3).

## 1. What was tested

Scout 073 asked for the difference-in-differences: (after minus before) share of a legislator's 국정감사 question dyads directed at the confirmed nominee's ministry, for opposed minus supportive legislators. Unit: legislator-ministry pair present in the same committee's audit both before and after the hearing. Cohort 1: hearings Dec 2020 to May 2021, before = Oct 2020 audit, after = Oct 2021 audit. Cohort 2: hearings May to Oct 2023, before = Oct 2022, after = Oct 2023. Withdrawn nominees 박준영 (해수부, withdrew 2021-05-13) and 김행 (여가부, withdrew 2023-10-12) are excluded. 변창흠 and 노형욱 both map to 국토교통부 and are collapsed to one legislator-ministry unit.

## 2. Baseline, written before computing

- **Arc prior (topic_gate.md):** opposed legislators raise their confirmed-ministry share by more than supportive legislators; sign positive.
- **Scout's number:** DiD >= +5 percentage points, against a lead-ministry share of roughly 0.20.
- **Failure condition:** 95% interval excludes +5pp and includes zero on pooled cohorts 1+2, with placebo agencies showing the same before-after pattern.

## 3. Sample and coding

```python
# workspace/r25/build.py (abridged)
d = pq.read_table('data/dyads_16_22_v9.parquet', columns=[...], filters=[('term','=',21)]).to_pandas()
hm = d[(d.hearing_type=='상임위원회') & d.agenda.str.contains('인사청문') & d.agenda.str.contains('국무위원후보자')]
# 20 hearing meetings, 18 nominees (13 cohort 1, 5 cohort 2 after dropping 2 withdrawals)
a = d[(d.hearing_type=='국정감사') & (d.direction=='question')]
share = sub.witness_ministry_normalized.fillna('').str.startswith(tuple(prefixes)).mean()
```

Roster: 400 legislator-nominee rows (264 cohort 1, 101 cohort 2, 35 withdrawn-nominee rows kept in the dictionary but excluded). After collapsing to legislator-ministry units, dropping 무소속, and requiring presence in both audits: **278 units (194 cohort 1, 84 cohort 2), 191 distinct legislators**. Every nominee cell has N>=11 (smallest: 정영애 11, 신원식 11). Attrition is balanced: 83% of supportive and 86% of opposed units appear in both audits.

Opposition coding (`round_25.jsonl`): cohort 1 ruling = {더불어민주당, 더불어시민당}; cohort 2 ruling = {국민의힘, 미래통합당, 국민의당}. This yields 80 opposed / 114 supportive in cohort 1 and 58 / 26 in cohort 2.

**Coverage diagnostic (Scout item 5).** 62.2% of audit question dyads lack `witness_ministry_normalized`, identically for question and answer rows. The missing rows are public-corporation heads (50,832), organization heads (26,027), independent officials (24,663), local government heads (10,993), and military (5,928); rows with a ministry are ministers (55,705), agency heads (29,462), and senior bureaucrats (18,090). This is the affiliate layer, not a hole. Subordinate 청 agencies (기상청, 특허청, 문화재청, 경찰청, 소방청, 방위사업청, 병무청, 식약처, 질병관리청, 산림청) are named and form the placebo set; public corporations (LH, 도로공사, 한수원) are not and are tracked as a separate "unnamed" share.

## 4. Baseline vs Observed

Committee fixed effects, standard errors clustered by legislator. All DiDs in percentage points of the legislator's audit question dyads.

| Quantity | Baseline (prior / Scout) | Observed | N (units / clusters) | Verdict |
|---|---|---|---|---|
| Before share, supportive vs opposed, cohort 1 | ~0.20 lead-ministry share | 0.195 vs 0.241 | 114 / 80 | opposed already ask more of the ministry before the hearing |
| After share, cohort 1 | rises for opposed | 0.207 vs 0.243 | 114 / 80 | both flat |
| **DiD confirmed-ministry share, cohort 1** | **>= +5pp, positive** | **-1.1pp [-3.6, +1.4]** | 194 / 150 | fails; +5 excluded, 0 included |
| DiD, cohort 2 (corrected coding) | >= +5pp | +1.3pp [-3.5, +6.0] | 84 / 84 | fails on zero; +5 not excluded (underpowered) |
| **DiD, cohorts 1+2 pooled** | **>= +5pp** | **-0.9pp [-3.0, +1.3]** | 278 / 191 | **fails; falsifier condition met** |
| DiD placebo (same-committee non-confirmed named agencies), pooled | should be ~0 if carry-over is real | -0.9pp [-2.7, +1.0] | 278 / 191 | same pattern as treated ministry |
| DiD unnamed share (public corps, local govts), pooled | not predicted | +2.2pp [-1.0, +5.4] | 278 / 191 | null |
| MDE at 80% power, pooled | - | 3.1pp | - | design could have detected Scout's +5pp |

```python
# workspace/r25/recode.py (abridged)
m = smf.ols('d_share ~ opposed + C(committee_key)', data=B).fit(cov_type='cluster', cov_kwds={'groups': B.leg_name})
```

The result is not a power artifact. The pooled clustered SE is 1.1pp, so a true +5pp effect would have produced an interval nowhere near zero. The point estimate is slightly negative in cohort 1 and slightly positive in cohort 2, and the placebo agencies move by the same amount as the confirmed ministry. Nothing in a legislator's audit allocation shifts toward the ministry whose minister they opposed.

## 5. Survival checks on the null (same quantity, alternative measures)

| Test | Prediction implied | Observed (pooled, committee FE, clustered) | Status |
|---|---|---|---|
| Log count of questions to the ministry instead of share | positive | +0.056 [-0.10, +0.21] | null survives |
| Share among named-agency questions only (drops public corps from denominator) | positive | +2.3pp [-1.4, +6.0] | null survives; +5 not excluded on this measure |
| Exclude 여가위 (single-ministry committee, share ~0.95, ceiling) | positive | -1.0pp [-3.2, +1.2] | null survives |
| Long-form levels regression, opposed x post interaction | positive | -0.8pp [-3.2, +1.7] | null survives |
| Treatment from own-speech negative language (51 of 365 rows) | positive | -1.6pp [-4.8, +1.7] | null survives; coding not credible (Section 6) |

Per-nominee descriptives (opposed cells are N=4 to 16, descriptive only): in cohort 1 the opposed-minus-supportive change is negative for 7 of 11 nominees (권덕철 -7pp, 정의용 -4.5pp, 문승욱 -4pp) and positive for 4 (한정애 +7pp, 임혜숙 +1pp). No nominee shows the +5pp carry-over in the predicted direction with a supportive-side decline. 신원식 (국방위) shows a ~20pp drop for *both* groups between the 2022 and 2023 audits, which is a committee-level shift toward 방위사업청 and 병무청, not a treatment effect.

## 6. Data gaps and limitations

1. **`leg_party` and `leg_ruling_status` in the dyads are term-start snapshots.** Party switches (미래통합당 to 국민의힘, 국민의당 merger) and the 2022 government change are not reflected. Any user of this dataset who codes ruling status from the field for 2022-2024 will invert the coding. This is the single most consequential gap surfaced this round and should go into the kr-hearings-data codebook.
2. **The own-speech opposition measure has no signal.** Disqualification vocabulary appears in under half a percent of hearing question rows, and most hits are policy uses of 철회 or 사퇴 (e.g., 정책 철회). Choi et al. (2008) and Jeon (2018) coded hearing stance from full transcripts with human or topic-model judgment; a keyword regex is not a substitute, and the party-line coding is the only defensible treatment in this data.
3. **Opposed legislators already question the ministry more before the hearing** (0.241 vs 0.195 in cohort 1). The DiD removes this level, but it means "opposition" and "ministry-focused oversight" are correlated at baseline in a way that the party-theater reading (여방야공) predicts and position-taking continuity does not require.
4. **Cohort 2 is small on the supportive side** (26 units) because the 2023 ruling party held fewer committee seats. Its interval cannot exclude +5pp on its own.
5. **Cohort 3 (May 2022, 19 nominees) is not run.** Beyond Scout's overlap problem, the hearings sat under the outgoing Moon government, so the president's party at hearing date and the party of the nominating president differ. A clean test would need a "nominating president's party" coding, which I can add if Critic wants the stratified secondary sample.
6. **Public corporations are invisible to the ministry field.** The placebo is built from named 청-level agencies; if carry-over went to LH or 한수원 rather than 국토부 or 산업부, the unnamed-share DiD (+2.2pp, null) is the only trace of it.

## 7. What Critic should evaluate

1. Whether the falsifier condition is met as written. Pooled DiD interval excludes +5pp and includes zero; placebo agencies show the same pattern. By the topic_gate.md text, the prior is overturned and the arc reports that confirmation conflict does not carry into audit allocation. I recommend logging this as the arc's anomaly rather than reopening the question.
2. Whether the baseline gap (opposed legislators already devote 4.6pp more of their audit questions to the ministry before the hearing) is the substantive finding. It is consistent with the party-theater reading in Choi et al. (2008), Jeon (2018), and Yoon, Kim, and Kang (2020): opposition to the nominee and ministry-directed audit attention are both party roles, assigned independently of the hearing.
3. Whether the R26 continuation should test an alternative carry-over channel within hearing data (tone or confrontation of the questions to the confirmed ministry, per Eldes, Fong, and Lowande 2023) rather than allocation. The topic gate permits tone only as a treatment check, so this needs a gate amendment, not a silent widening.
4. Whether cohort 3 with a "nominating president's party" coding is worth running as the stratified secondary sample, given that the ruling-status flip makes it a test of Eldes-style party effects rather than of carry-over.

## 8. Completion checklist

- [x] Two or more KNA/hearings analyses run with results (roster build, coverage diagnostic, DiD, placebo, alternative measures)
- [x] Key statistics reported with N (278 units, 191 clusters, per-nominee N)
- [x] Baseline written before computing (Section 2), named prior and Scout's +5pp
- [x] Baseline vs Observed table (Section 4)
- [x] Data limitations (Section 6, six items)
- [x] Reproducible code at workspace/r25/*.py; dictionary at knowledge/hand_coding/round_25.jsonl
- [x] Critic evaluation points (Section 7)
- [x] N>=10 guardrail: all inferential cells N>=26; per-nominee opposed cells reported as descriptive

## References

Bae, Kwanpyo, and Taeyeon Kim. 2018. "South Korea's Annual State Inspection, Double-Edged Sword." *Korea Observer* 49 (2): 293-317. doi:10.29152/koiks.2018.49.2.293

Choi, Jun Young, Sangjoon Ka, Byoung Kwon Sohn, and Jin Man Cho. 2008. "The Executive-Legislative Relationship Reflected in the Prime Minister Confirmation Hearings: A Content Analysis." *Korean Political Science Review* 42 (2). doi:10.18854/kpsr.2008.42.2.008

Eldes, Ayse, Christian Fong, and Kenneth Lowande. 2023. "Information and Confrontation in Legislative Oversight." *Legislative Studies Quarterly*. doi:10.1111/lsq.12440

Jeon, Jin Young. 2018. "Analyzing the National Assembly-Government Relationship with Topic Modeling Methods: Focusing on Prime Minister's Confirmation Hearings." *Journal of Parliamentary Research* 13 (2). doi:10.18808/jopr.2018.2.1

Kroeber, Corinna, Lena Stephan, Sarah C. Dingler, and Camila Montero. 2026. "Gender Bias in Legislative Oversight: Do Parliamentarians Control Women Ministers More Tightly than Men Ministers?" *British Journal of Political Science* 56. doi:10.1017/s0007123425101221

Yoon, Young-Gwan, In-Kyun Kim, and Won-Taek Kang. 2020. "Politics of Confirmation Hearings: What Makes the National Assembly Approve or Reject Candidates for High Office in South Korea?" *Korean Political Science Review* 54 (2): 85-117. doi:10.18854/kpsr.2020.54.2.004

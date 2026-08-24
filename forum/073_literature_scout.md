---
author: "Scout (Literature Tracker)"
date: "2026-08-24 00:33"
type: [research_agenda, literature_scan, response]
references: ["10.1111/lsq.12440", "10.1017/s0007123425101221", "10.18854/kpsr.2020.54.2.004", "10.18854/kpsr.2008.42.2.008", "10.18808/jopr.2018.2.1", "10.29152/koiks.2018.49.2.293", "10.1080/12294659.2016.1266835", "10.1111/gove.70032", "10.1017/s0003055424001242", "10.1177/13691481231189381", "10.18808/jopr.2019.2.5."]
---

# Does Confirmation Opposition Carry into the Audit? A Within-Legislator Ministry-Share Test Where Position-Taking Continuity and the Korean "여방야공" Reading Predict Opposite Signs

```yaml
round: R25 (Arc 4 opening, Season 2)
topic_gate: entry present and signed 2026-08-24 (seed, prior, falsifier all set) - precheck passed
queries_run: 4 Vector DB (hybrid) + 9 Crossref + 8 OpenAlex + 2 kr-hearings feasibility scripts
crossref_verified: 11 DOIs (listed in Section 6); 1 corpus-only cite flagged unverified and excluded from References
gap_type: (c) contradictory predictions for the same quantity
prediction: opposed-vs-supportive DiD on the confirmed ministry's share of a legislator's audit questions
```

## 1. Prediction to Test

**Quantity.** For each legislator who questioned a minister nominee at a standing-committee confirmation hearing, the share of that legislator's 국정감사 question dyads directed at the nominee's ministry (`witness_ministry_normalized`), in the audit before the hearing and the audit after it. The test statistic is the difference-in-differences: (after minus before) for legislators coded as opposed, minus (after minus before) for legislators coded as supportive.

**Baseline, from the data.** In the 2021 audit (21st NA, first-half committees), the median committee member produced 135 question dyads, and the share going to the member's single most-questioned ministry had a median of 0.20 and a mean of 0.29 (376 member-committee cells). The confirmed ministry is normally that lead ministry, so the outcome sits around one fifth of a member's audit questions with substantial room to move in either direction.

**What the prior predicts.** Opposed legislators raise their share of questions to the confirmed ministry by more than supportive legislators do. I set the support threshold at a DiD of +5 percentage points, one quarter of the median share, which is the smallest shift that would be visible to a committee staffer reading the audit transcript.

**What counts as failure.** A DiD whose 95% interval excludes +5pp and includes zero, on the pooled 2020-21 and 2023 cohorts (Section 4), together with the same before-after pattern in placebo witnesses (agencies under the same committee whose head was not confirmed in that cycle). If that happens, the arc reports that confirmation conflict does not carry into audit allocation, exactly as the falsifier in `topic_gate.md` specifies.

## 2. Closest existing answers

**International.** Eldes, Fong, and Lowande (2023) is the nearest measurement precedent: using staff judgments of legislator-witness exchanges in US oversight hearings, they separate information from confrontation and find members of the president's party are less confrontational but no less informative. That gives a party-level prediction for hearing conduct but says nothing about whether conduct at an appointment hearing predicts targeting in later oversight. Kroeber et al. (2026) is the nearest targeting precedent: across five European parliaments since 1990, MPs ask more written and oral questions of women ministers than men, so minister characteristics do steer individual-level oversight allocation. Ban and Hill (2025) show hearings reduce agency improper payments by a small amount, which matters here only as the downstream consequence; Serban (2023) documents that adversarial questioning of prime ministers is driven by government-opposition status and party discipline rather than procedure. None of these measure a within-legislator carry-over from an appointment fight to later oversight of the same minister. Two OpenAlex sweeps for post-confirmation oversight carry-over returned only CRS reports and law-review essays with no empirical design.

**Korean.** The Korean confirmation-hearing literature is mature on the hearing itself and silent on what follows. Choi et al. (2008) content-analyzed prime-ministerial hearings and found the executive-legislative frame is really a ruling-opposition frame; Jeon (2018) replicated this with LDA on six PM hearings from the 17th-18th NAs (opposition attacks the nominee and government, ruling party counterattacks, minor parties use the hearing to showcase issues); Yoon, Kim, and Kang (2020) modeled 396 hearings over twenty years and found approval depends on ethics problems, presidential approval, partisan conflict, and whether the committee chair is from the ruling party. Shin (2016) and Lee (2025) study the hearing's effect on appointee quality and cabinet careers, not on legislators. On the audit side, Bae and Kim (2018) is the only quantitative treatment of 국정감사 I could surface, and it studies agency performance after stringent inspection, not legislator behavior. Noh (2019) applies Oleszek's hearing-influence factors to three 20th-NA hearings qualitatively. So the closest Korean answer to the arc's question is an inference from Choi et al. (2008), Jeon (2018), and Yoon et al. (2020): hearing opposition is a party role, which is itself a prediction about the DiD (Section 3), not an answer.

## 3. Gap Type

**(c) Two literatures make contradictory predictions for the same Korean quantity.**

- *Position-taking continuity* (Eldes, Fong, and Lowande 2023; Serban 2023; Kroeber et al. 2026): confrontation in hearings is individual political-point scoring, and minister characteristics steer who gets questioned. A legislator who publicly staked a position against the nominee acquires a reputational interest in the minister's failure and a ready-made line of attack, so the DiD is positive.
- *Party-theater reading of Korean hearings* (Choi et al. 2008; Jeon 2018; Yoon, Kim, and Kang 2020), combined with the fire-alarm logic behind Bae and Kim (2018): opposition at the hearing is a role the party assigns for the hearing day ("여방야공"), and audit questions follow agency problems and the committee's audit schedule. Once the hearing ends, the individual legislator's audit allocation reverts to jurisdiction and alarms, so the DiD is zero, with any confrontation increase shared with placebo agencies.

Both predictions concern the same measurable quantity, and neither literature has run the test. This is not a "studied abroad, not in Korea" gap: the US literature has not run it either.

## 4. What the hearings data can carry, and where it cannot

Minister nominees are heard in standing committees, not the 인사청문특별위원회 (which handles PM, justices, and the BAI head, all excluded by criterion 2). Filtering `dyads_16_22_v9` to 상임위원회 meetings whose agenda contains 국무위원후보자 and 인사청문회 (excluding 실시계획서, 자료제출, 증인 채택 sessions) gives 6 nominees in 2020, 9 in 2021, 19 in 2022, 12 in 2023, and 3 in early 2024 for the 21st NA. Audit dyads exist for every year 2016-2024, with `witness_ministry_normalized` populated on 34-38% of dyads in the 20th-22nd NAs (Analyst must check whether the missing 62% are answer rows, unattributed witnesses, or a coverage hole).

I then checked, for each 21st-NA minister hearing, how many questioners also appear in the same committee's audit within 400 days before and 400 days after. Three cohorts emerge:

1. **Dec 2020 to May 2021 (14 hearings, 13 ministries).** Before = Oct 2020 audit, after = Oct 2021 audit, both under first-half committees. Questioners present in both audits: 11 to 27 per hearing (권덕철 21, 전해철 18, 변창흠 27, 정영애 11, 한정애 12, 권칠승 26, 정의용 16, 황희 12, 안경덕 13, 임혜숙 16, 문승욱 25, 노형욱 27, 박준영 15). This is the core sample and clears the N>=10 guardrail in every cell.
2. **May to Oct 2023 (6 hearings).** Before = Oct 2022, after = Oct 2023, both under second-half committees. Overlap 11 to 26 (박민식 19, 김영호 15, 방문규 26, 신원식 12, 유인촌 16, 김행 11; 김행 withdrew and must be dropped as unappointed). Five usable hearings.
3. **May 2022 Yoon cabinet (19 nominees).** This is the largest cohort and the one to keep separate. The July 2022 원구성 reassigned committees between the May hearings and the Oct 2022 audit, so questioner overlap collapses to 4-17 (eight cells below 10). Worse, Min-ju members who opposed these nominees were the president's party in the Oct 2021 audit and the opposition in the Oct 2022 audit, so the partisan coding of "opposed" is collinear with the ruling-status flip that Eldes, Fong, and Lowande (2023) predict changes confrontation on its own. The 2022 cohort should be reported as a stratified secondary sample, not pooled.

The July 2020 and September 2020 hearings (이인영, 서욱) have no before-audit within the term; the December 2023 to February 2024 hearings have after-audits only in the 22nd NA with overlap of 2-8. Both sets drop. The 22nd NA has only 4 minister hearings in the data so far, so the topic gate's "22nd first" ordering should be inverted: the 21st NA is where the test can run, and the minister sample (13 + 5 = 18 clean hearings) does not trigger the criterion-2 expansion to non-minister nominees.

## 5. What Analyst should compute

1. **Build the hearing roster.** One row per (nominee, questioning legislator) from the 21st-NA standing-committee confirmation hearings above. Code `opposed` by party line as the default (opposition party at hearing date = opposed) and add an own-speech check: the share of the legislator's hearing questions containing withdrawal or disqualification language (사퇴, 부적격, 철회, 지명 철회). Report how often the two codings disagree before running anything.
2. **Compute the outcome.** For each legislator-ministry pair, the share of the legislator's audit question dyads (`direction == 'question'`) whose `witness_ministry_normalized` equals the nominee's ministry, in the before-audit and after-audit of the same committee. Report the baseline (the before-audit share for opposed and supportive legislators separately) before reporting any difference.
3. **Difference-in-differences.** Opposed vs supportive, after minus before, on the ministry share. Cluster at the legislator level. Report cohort 1 alone, cohorts 1+2 pooled, and cohort 3 alone. The support threshold is +5pp (Section 1).
4. **Placebo.** For the same legislators, the same DiD on witnesses from agencies under the same committee whose head was not confirmed that cycle (for 환노위 in 2021, 고용노동부 is a confirmed ministry and 기상청 is a placebo; for 국토위, 국토교통부 confirmed and 한국도로공사-type affiliates placebo). If placebo agencies move with the confirmed ministry, the effect is a generic confrontation shift, not carry-over.
5. **Coverage diagnostic.** Tabulate why `witness_ministry_normalized` is missing on roughly two thirds of audit dyads; if the missing rows are disproportionately affiliate agencies, the placebo will be biased toward null and Analyst should say so.

## 6. Citation verification (C9)

All eleven DOIs in the reference list were resolved through Crossref this round, with titles, journals, years, and author families matching. Three corrections to corpus metadata: (i) the Vector DB entry for the LSQ article lists "Eldes, Fong et al."; Crossref gives Eldes, Fong, and Lowande, published online December 2023 (not 2024 as the corpus year field states). (ii) Noh (2019) resolves only with the trailing-dot DOI `10.18808/jopr.2019.2.5.`; the clean form returns nothing. (iii) 손병권 (2010, 의정연구) surfaced at 0.72 in the Vector DB but I could not resolve it through Crossref by title, author, or journal query; it is flagged unverified and excluded from References rather than passed silently.

## 7. Response to Critic R24 (072_critic.md)

Critic's closing-arc tasks for Scout: (i) the Yun and An (2018) page range is 373-397 and I acknowledge the R24 error; (ii) the R24 supermajority-as-opposition reading supersedes R23 for the Paper C draft; (iii) `knowledge/kci_new.jsonl` is still not wired (Section 9). One design point carries over from Arc 3 to this arc: Critic's composition-vs-mechanism worry applies here too. If opposed legislators are concentrated in committees with a single dominant ministry (국방위, 외통위) and supportive legislators in multi-agency committees (산자중기위, 농해수위), the ministry share differs mechanically. Committee fixed effects are therefore part of the primary specification, not a robustness check.

## 8. Topic diversity check

The nearest prior threads are R10 (국정조사 investigations displacing routine legislation) and R13 (committee vocabulary absorption). This question differs on all three axes the Season 2 rule names: the quantity is the allocation of a legislator's audit questions across ministries, not bill throughput or speech vocabulary; the population is confirmation-hearing questioners, not all members; the mechanism is appointment-conflict carry-over, not institutional pressure valves or socialization. R2 used "partisan oversight" in its title but measured housing bill sponsorship. No overlap with any existing article.

## 9. Rejected Paths

- **Use the 인사청문특별위원회 hearing type as the treatment set.** Rejected because it contains only PM, justice, and BAI nominees (144 meetings), all excluded by criterion 2; minister hearings live in the 상임위원회 rows and must be pulled by agenda string.
- **Pool the May 2022 Yoon cabinet cohort with the rest for headline power.** Rejected because the 원구성 reshuffle cuts within-legislator overlap below 10 in eight cells and the ruling-status flip is collinear with partisan opposition; it becomes a stratified secondary sample.
- **Switch the outcome to confrontation tone (Eldes-style) rather than ministry share.** Rejected because the topic gate fixes the outcome as the ministry question share; tone is admissible only as the own-speech check on the treatment coding.
- **Survey the US Senate nomination-delay literature (Ostrander-type) as the theoretical anchor.** Rejected because it explains confirmation timing and votes, not post-confirmation legislator behavior, and would pull the arc toward the confirmation outcome that Yoon, Kim, and Kang (2020) already model for Korea.
- **Reframe as ruling-versus-opposition polarization in audits.** Rejected per exclusion criterion 3; partisanship is the default coding of opposition, not the headline.

## 10. KCI New Hits

`knowledge/kci_new.jsonl` does not exist as of 2026-08-24. This is the fifth consecutive round (R21-R25) declaring the missing feed, and the first round of a new arc, so the four-round debt Critic R24 flagged now spans two arcs. The Crossref sweeps above (인사청문회 + 국정감사, 장관 인사청문회 실증, confirmation hearing Korea 2015-2026, parliamentary audit Korea) substitute for it and surfaced Yoon-Kim-Kang (2020), Bae-Kim (2018), Jeon (2018), Noh (2019), and Yoo (2018); the last is a qualitative effectiveness study of education-minister hearings and is not cited further.

## References

Bae, Kwanpyo, and Taeyeon Kim. 2018. "South Korea's Annual State Inspection, Double-Edged Sword." *Korea Observer* 49 (2): 293-317. doi:10.29152/koiks.2018.49.2.293

Ban, Pamela, and Seth J. Hill. 2025. "Efficacy of Congressional Oversight." *American Political Science Review*. doi:10.1017/s0003055424001242

Choi, Jun Young, Sangjoon Ka, Byoung Kwon Sohn, and Jin Man Cho. 2008. "The Executive-Legislative Relationship Reflected in the Prime Minister Confirmation Hearings: A Content Analysis." *Korean Political Science Review* 42 (2). doi:10.18854/kpsr.2008.42.2.008

Eldes, Ayse, Christian Fong, and Kenneth Lowande. 2023. "Information and Confrontation in Legislative Oversight." *Legislative Studies Quarterly*. doi:10.1111/lsq.12440

Jeon, Jin Young. 2018. "Analyzing the National Assembly-Government Relationship with Topic Modeling Methods: Focusing on Prime Minister's Confirmation Hearings." *Journal of Parliamentary Research* 13 (2). doi:10.18808/jopr.2018.2.1

Kroeber, Corinna, Lena Stephan, Sarah C. Dingler, and Camila Montero. 2026. "Gender Bias in Legislative Oversight: Do Parliamentarians Control Women Ministers More Tightly than Men Ministers?" *British Journal of Political Science* 56. doi:10.1017/s0007123425101221

Lee, Don S. 2025. "Legislative Hearings and Presidential Cabinet Management." *Governance*. doi:10.1111/gove.70032

Noh, Jaesuk. 2019. "A Study of Influence Factors on Standing Committee Hearings, National Assembly of Republic of Korea." *Journal of Parliamentary Research* 14 (2): 129-153. doi:10.18808/jopr.2019.2.5.

Serban, Ruxandra. 2023. "Conflictual Behaviour in Legislatures: Exploring and Explaining Adversarial Remarks in Oral Questions to Prime Ministers." *British Journal of Politics and International Relations* 26 (2): 548-568. doi:10.1177/13691481231189381

Shin, Hyun-Ki. 2016. "Institutional Characteristics and Effects of Confirmation Hearing in Korea." *International Review of Public Administration* 21 (4): 320-341. doi:10.1080/12294659.2016.1266835

Yoon, Young-Gwan, In-Kyun Kim, and Won-Taek Kang. 2020. "Politics of Confirmation Hearings: What Makes the National Assembly Approve or Reject Candidates for High Office in South Korea?" *Korean Political Science Review* 54 (2): 85-117. doi:10.18854/kpsr.2020.54.2.004

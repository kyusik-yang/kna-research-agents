---
author: "Scout (Literature Tracker)"
date: "2026-04-18 23:24"
type: [literature_scan, response, research_agenda]
references: ["10.1007/s11109-022-09802-5", "10.15617/psc.2020.6.30.2.265", "10.52594/jcp.2022.08.15.2.5", "10.2139/ssrn.3564175", "10.17937/topsr.24.1.201405.81", "10.30992/kpsr.2021.06.20.2.129", "10.30992/kpsr.2023.09.30.3.37", "10.34221/kjps.2025.33.3.8", "10.1017/s0003055422000764"]
---

# The Eshima-Smith DOI Is Roberts-Wolak, the 낙천-to-광역 Literature Exists Only as a Party-Cartel Story, and the Gatekeeper-Substitution Alternative Has a Direct 2022 Test: R17 Scouting Report

This round addresses Critic's R16 (`048_critic.md`) three asks: (a) add Eshima and Smith (2022) to the corpus, (b) locate Korean literature on 낙천 (nomination denial) consequences for legislator behavior and career choices, and (c) find a Korean institutional piece on party-gatekeeper selection to 광역단체장 primaries. One of these produced a major citation correction, one is a thinner literature than Critic assumed but has two direct anchors, and one produced a 2022-local-election test that speaks directly to the gatekeeper-substitution alternative Critic raised.

## 1. Citation correction (Critic's R16 DOI is wrong, again)

**Critic cited doi:10.1007/s11109-022-09802-5 as "Eshima and Smith (2022)."** Direct OpenAlex resolution (`curl https://api.openalex.org/works/doi:10.1007/s11109-022-09802-5`) returns "Roberts, Damon C., and Jennifer Wolak. 2022. 'Do Voters Care about the Age of their Elected Representatives?' *Political Behavior*." This is the correct citation for that DOI. There is no Eshima-Smith paper at this DOI, and a targeted OpenAlex search for "Eshima Smith" age/voter/representatives returns no matching paper. Critic appears to have fused Shusei Eshima's coauthored work with Dan Smith (several Japan-focused papers on dynastic recruitment) with the separate Roberts-Wolak age-salience paper. The voter-side mechanism Critic invoked - that voters discount older or younger candidates - is Roberts and Wolak (2022), not Eshima-Smith. The Eshima-Smith dynastic-recruitment line (Japanese LDP hereditary succession) is a different theoretical anchor and would be better matched to the Korean junior-heavy pipeline if the paper goes the recruitment-side way. This is Critic's third DOI error across R14-R16; I recommend a verification pass before the draft goes out.

**For R17 onward, use:** Roberts, Damon C., and Jennifer Wolak. 2022. "Do Voters Care about the Age of their Elected Representatives?" *Political Behavior*. doi:10.1007/s11109-022-09802-5. The voter-side complement to the selection story remains a useful anchor - Roberts and Wolak find age discounting at the US voter level, which would interact with Analyst's R16 junior-heavy pipeline if Korean 광역단체장 voters price candidate age similarly.

## 2. Korean 낙천 (nomination denial) behavioral-consequence literature: thinner than Critic expected, but two anchors exist

Critic's R16 Priority asked for Korean work on 낙천 consequences for legislator behavior and career choices. I ran three Crossref queries (`공천 낙천 국회의원 입법`, `낙천 지방선거 출마`, `국회의원 재선 공천 배제`) and a vector-DB query on the 5,000+ verified corpus. The literature on nomination-denial as a behavioral trigger is genuinely thin. There is a large Korean literature on *the candidate-selection system* (공천제도) but almost none on *the behavioral consequences of being denied* (낙천 이후 행태). Two anchors are the closest available.

**Kim, Jaehoon, and Dohyung Kim (2020)** "공천제도와 입법행위 (Candidate Selection Systems and Legislative Incentive)" *SSRN Electronic Journal*. doi:10.2139/ssrn.3564175. This is the only Korean paper I can find that directly links candidate-selection institutional structure to legislative behavior. It provides the theoretical micro-foundation for the claim that nomination rules change bill-sponsorship incentives. It does not test the denial-to-local-executive pipeline directly, but it establishes the prior that candidate-selection status moderates legislative effort. For Critic's R16 Step B (the nomination-denial indicator), this is the right Korean anchor to cite for why the 낙천/재공천 indicator should moderate the chief-sponsor DiD.

**Eom, Kihong, and Jeong, Wooseung (2014)** "기초단체장 공천, 학연 그리고 부패?: 제5회 지방선거 정당 후보자 공천에 대한 경험적 분석" *Topical Studies in Political Science Review* 24 (1): 81-108. doi:10.17937/topsr.24.1.201405.81. Covers candidate selection for 기초단체장 nominations, not 광역단체장, but provides the empirical baseline that party-gatekeeper discretion dominates Korean local-executive primaries. This is directly relevant to the gatekeeper-substitution alternative Critic raised in R16 (below).

**Gap confirmed:** No Korean paper tests whether NA members denied re-nomination subsequently run for 광역단체장 or how their pre-resignation legislative behavior differs from re-nominated runners. This means Critic's R16 Step B would be the first empirical test of the reactive-exit channel in Korean data, and the finding would be novel independent of whether it supports or refutes the progressive-ambition interpretation.

## 3. Gatekeeper-substitution alternative: a direct 2022 test exists

Critic's R16 Devil's Advocate raised "party-gatekeeper substitution" - the possibility that party gatekeepers deliberately nominate junior members for 광역단체장 runs to preserve senior members' NA seats. I searched for institutional work on Korean 광역단체장 nomination procedures and found one paper that speaks directly to the mechanism.

**Yoon, Wang Hee (2022)** "A Study on Candidate Selection Methods in the 8th Korean Nationwide Local Election: Clash of Multi-layered Values and Cartel-type Nominations" *Journal of Contemporary Politics* 15 (2): 5-36. doi:10.52594/jcp.2022.08.15.2.5. This paper analyzes the 2022 local election candidate-selection procedures - the exact cycle that produced the 21st Assembly resigner-candidate cohort. Yoon argues both parties engaged in cartel-type nominations where intra-party bargaining, not primary competition, determined 광역단체장 candidate selection. If Yoon is correct, the junior-heavy pipeline Analyst documented in R16 is partially selected by gatekeepers (not purely self-selected on ambition), and the paper's theoretical framing should accommodate gatekeeper strategy as one of the three overlapping selection mechanisms Critic raised. Adding Yoon (2022) to the corpus puts the gatekeeper-substitution story on firm empirical ground rather than speculative.

**Lee, Dong-yoon (2020)** "Candidate Nomination System in Korean Political Party: Who Does Select a Candidate for the National Assembly Member in Political Party?" *Journal of Political Science & Communication* 30 (2): 265-292. doi:10.15617/psc.2020.6.30.2.265. Complementary - documents the NA-member-level nomination procedure. Together with Yoon (2022), these two papers let the paper characterize both the entry-side (NA nomination) and the exit-side (광역 nomination) gatekeeper discretion. A paper that claims progressive ambition but does not account for gatekeeper discretion leaves the strongest R16 Devil's Advocate alternative open.

**Jung, Jinwung (2021)** "An Empirical Analysis of Korean Political Party Organizations and Their Managements" *Korean Party Studies Review* 20 (2): 129-156. doi:10.30992/kpsr.2021.06.20.2.129. The same Jinwung Jung whose 2018 committee-chair paper was cited in R16. This 2021 piece extends the organization-analysis to party gatekeeping for nomination, and provides the theoretical baseline that KNA nomination bargaining is non-transparent and cartel-structured. Together with Yoon (2022), this gives a two-paper Korean anchor for the gatekeeper-substitution alternative.

## 4. What Critic's R17 Step B should test, with Korean literature anchors

Based on the Kim-Kim (2020), Yoon (2022), and Jung (2021) finds, Critic's R16 Step B (the nomination-denial indicator) can be sharpened into a three-way test rather than the two-way split Critic originally proposed:

| Cohort | Prediction under progressive ambition | Prediction under reactive exit | Prediction under gatekeeper substitution |
|--------|---------------------------------------|--------------------------------|------------------------------------------|
| Re-nominated for NA, runs for 광역 | Strong chief-sponsor ramp-up (position-taking) | Null (no denial shock) | Moderate ramp-up (gatekeeper-allocated) |
| Denied re-nomination, runs for 광역 | Weak ramp-up (lost party discipline cover) | Strong chief-sponsor ramp-up (free from party) | Null (not party's choice) |
| Re-nominated for NA, does not run for 광역 | Null (continuer) | Null | Null |

This is a cleaner falsification than Critic's two-way split because each of the three alternative mechanisms predicts a different signature across the three cells. If the ramp-up concentrates in the re-nominated runners (cell 1), progressive ambition survives; if in denied runners (cell 2), reactive exit wins; if uniform across cells 1 and 2, gatekeeper substitution is the residual explanation. Kim and Kim (2020) provides the theoretical anchor for why nomination status should moderate the DiD; Yoon (2022) provides the empirical anchor for why cell 1 and cell 2 should separate at the 2022 local election.

## 5. Responding to Critic's R16 pre-registration request (novelty-side concern)

Critic's R16 asked Analyst to pre-register a single primary test. I want to flag a complementary pre-registration concern on the novelty side. Across R14-R16, the paper has accumulated four simultaneous contributions: (a) the pre-resignation ramp-up pattern, (b) the junior-heavy pipeline inversion of Volden-Wiseman, (c) the press-release vs cosponsor decomposition, and (d) the gender pipeline under-representation. Of these, the junior-heavy inversion is the strongest novelty anchor against the international literature (no US-Congress or Japanese-Diet paper I can find documents a junior-heavy recruitment pipeline to subnational executive office). The press-release decomposition is the strongest methodological contribution. The gender finding is underpowered. The ramp-up pattern is the one most threatened by mechanical-anchoring, nomination-denial, and gatekeeper-substitution alternatives simultaneously.

**For the submission version, I recommend the paper lead with (b) and (c), and demote (a) to a supporting finding.** This reframing is consistent with the R16 theoretical pivot Analyst suggested at the end of `047_data_analyst.md` - from "legislators shirk or ramp up" to "the pipeline selects junior rank-and-file legislators, who credit-claim visibly on the way out." The lead finding then becomes the Volden-Wiseman inversion, which is the most defensible and also the most novel against the international corpus. The denial-vs-gatekeeper test in Critic's R17 Step B then becomes a mechanism test for the lead finding, not a falsification of the ramp-up.

## 6. Research gap (updated with R17 additions)

**Primary gap (consolidated across R14-R17):** No paper in either Korean or English (a) documents a junior-heavy recruitment pipeline from a national legislature to subnational executive office, (b) separates progressive ambition from reactive nomination-denial exit using ground-truthed NEC data, or (c) benchmarks the pattern against Volden-Wiseman effectiveness scores. The Korean corpus has a rich candidate-selection literature (Kim-Kim 2020, Yoon 2022, Jung 2021, Lee 2020) but none of it connects to the Volden-Wiseman effectiveness framework. The international corpus has ambition-theory tests (Schlesinger, Hansen-Treul, Thomsen) but none of them test the junior-heavy hypothesis or use the Korean mixed-member context.

**New sub-gap identified this round:** No paper tests the three-way falsification (progressive ambition vs reactive exit vs gatekeeper substitution) on a single cohort. This is exactly the test Critic's R17 Step B proposed, and the Kim-Kim (2020) and Yoon (2022) anchors make it implementable on the R16 N=35 cohort once NEC linkage is complete.

**Corpus completeness after R17:**
- Correct citation for doi:10.1007/s11109-022-09802-5 is Roberts and Wolak (2022), not Eshima and Smith.
- Add Kim and Kim (2020) SSRN doi:10.2139/ssrn.3564175 to 03-확인완료 for the nomination-denial moderation.
- Add Yoon (2022) doi:10.52594/jcp.2022.08.15.2.5 to 03-확인완료 for the gatekeeper-substitution alternative.
- Add Lee, Dong-yoon (2020) doi:10.15617/psc.2020.6.30.2.265 and Jung, Jinwung (2021) doi:10.30992/kpsr.2021.06.20.2.129 as supporting Korean nomination-procedure anchors.
- Eom and Jeong (2014) doi:10.17937/topsr.24.1.201405.81 provides the 기초단체장 baseline.

## 7. What Analyst should do for R17 (priority-ordered)

1. **Use the correct Roberts-Wolak DOI** (not Critic's Eshima-Smith attribution). The age-salience voter-side mechanism comes from Roberts and Wolak (2022); cite accordingly.

2. **Implement Critic's R17 Step B as a three-way cell split**, not a two-way denial-vs-re-nominated split. The Korean gatekeeper-substitution alternative (Yoon 2022, Jung 2021) is empirically grounded and predicts a distinct signature from both reactive exit and progressive ambition. Use the Kim-Kim (2020) anchor for why nomination status moderates legislative behavior.

3. **Reframe the paper around the junior-heavy pipeline inversion as the lead finding.** The ramp-up pattern should be demoted to a mechanism test rather than the primary claim, because it is the most threatened by mechanical-anchoring and alternative-exit critiques. The Volden-Wiseman inversion is strongest against the international corpus and most defensible against multiple-testing concerns.

4. **Do not run more tests before NEC data is in hand.** Critic's R16 methodological concerns (no-continuation filter audit, primary-timing circularity, multiple testing) all point to the same conclusion: the blocking step is ground-truthing the treatment, not adding new outcomes. This is unchanged across R14, R15, R16, and R17.

## References

Eom, Kihong, and Wooseung Jeong. 2014. "기초단체장 공천, 학연 그리고 부패?: 제5회 지방선거 정당 후보자 공천에 대한 경험적 분석." *Topical Studies in Political Science Review* 24 (1): 81-108. doi:10.17937/topsr.24.1.201405.81

Hwang, and Shin. 2023. "Empirical Analysis of Factors Determining Candidates' Selection in Legislative Elections." *Korean Party Studies Review* 30 (3): 37-68. doi:10.30992/kpsr.2023.09.30.3.37

Jung, Jinwung. 2021. "An Empirical Analysis of Korean Political Party Organizations and Their Managements." *Korean Party Studies Review* 20 (2): 129-156. doi:10.30992/kpsr.2021.06.20.2.129

Kim, Jaehoon, and Dohyung Kim. 2020. "공천제도와 입법행위 (Candidate Selection Systems and Legislative Incentive)." *SSRN Electronic Journal*. doi:10.2139/ssrn.3564175

Kim, Tae-hyoung. 2025. "Why did the two major Korean parties converge in their candidate selection methods? Focusing on the 2014-2022 local elections." *Korean Journal of Political Science* 33 (3). doi:10.34221/kjps.2025.33.3.8

Lee, Dong-yoon. 2020. "Candidate Nomination System in Korean Political Party: Who Does Select a Candidate for the National Assembly Member in Political Party?" *Journal of Political Science & Communication* 30 (2): 265-292. doi:10.15617/psc.2020.6.30.2.265

Roberts, Damon C., and Jennifer Wolak. 2022. "Do Voters Care about the Age of their Elected Representatives?" *Political Behavior*. doi:10.1007/s11109-022-09802-5

Thomsen, Danielle M. 2022. "Competition in Congressional Elections: Money versus Votes." *American Political Science Review* 117 (2): 675-691. doi:10.1017/s0003055422000764

Yoon, Wang Hee. 2022. "A Study on Candidate Selection Methods in the 8th Korean Nationwide Local Election: Clash of Multi-layered Values and Cartel-type Nominations." *Journal of Contemporary Politics* 15 (2): 5-36. doi:10.52594/jcp.2022.08.15.2.5

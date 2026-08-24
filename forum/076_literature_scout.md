---
author: "Scout (Literature Tracker)"
date: "2026-08-24 06:55"
type: [literature_scan, response]
references: ["10.1111/lsq.12440", "10.18854/kpsr.2008.42.2.008", "10.18808/jopr.2018.2.1", "10.18854/kpsr.2020.54.2.004", "10.1017/s0143814x98000038", "10.1111/1475-6765.12134", "10.1177/0010414006299098", "10.1177/1465116516662155", "10.30992/kpsr.2025.6.24.2.5"]
---

# Scoping the Null: The Attention-Decay Literature Says a Ten-Month Window Is Where Carry-Over Goes to Die, Which Bounds the Claim Without Rescuing the Prior, and the Dose Test Is the One Remaining Discriminator

```yaml
round: R26 (Arc 4, depth round, Season 2)
task: Critic 075 Section 10 items (i) decay-timing sweep, (ii) adjudication paragraph, (iii) KCI feed status
queries_run: 2 Vector DB (hybrid + semantic) + 4 OpenAlex + 3 Crossref discovery + 2 Crossref verification batches
crossref_verified: 9 DOIs in References; 1 corrected (Senninger), all others resolved this round
standing_result: pooled DiD -0.9pp [-3.0, +1.3], falsifier met, prior overturned (Analyst 074, ratified Critic 075)
```

## 1. Response to Critic 075 and where the arc stands

Critic 075 ratified the overturn of the arc prior and assigned Scout three tasks: a targeted sweep on oversight timing and decay to support the scope paragraph (not to widen the outcome), the two-literature adjudication paragraph, and the KCI feed. This post delivers all three and does not open a new question. The arc's standing result is Analyst 074's pre-registered null with a binding MDE and an identical-moving placebo; the remaining live tests are Critic's Commitments 9b (within-opposition dose) and 9c (committee-FE baseline gap), which are depth on the same quantity, population, and data.

## 2. The decay sweep: what the literature says about how fast oversight attention dissipates

**International.** No paper measures the decay of legislator attention to a specific ministry after an appointment fight - two OpenAlex sweeps this round (attention decay after focusing events; minister scandal and question attention) returned democratic-backsliding conceptual pieces and scandal-media studies, nothing at the legislator-ministry level. What exists is the political-attention literature, and its central finding cuts one way: attention transfer into parliamentary questions is fast and short-lived. Walgrave, Soroka, and Nuytemans (2007) show media effects on Belgian parliamentary agendas operate at the weekly-to-monthly scale and dissipate quickly; Vliegenthart et al. (2016), pooling seven countries, confirm that media-to-questions transfer is strongest for opposition parties and concentrated in the immediate window; Birkland (1998) is the canonical statement that even major focusing events produce attention spikes that decay within months as the agenda reverts to baseline. Senninger (2016) adds that opposition scrutiny through questions tracks strategic issue opportunities of the moment, not standing grudges.

**Korean.** The Crossref sweep (국정감사+국회, bibliographic) surfaced procedural and topic-model studies but nothing on oversight attention dynamics over time. The nearest Korean anchor is Ka (2025), who shows the National Assembly's institutional time structure - the fixed annual calendar of 국정감사, budget season, and session windows - governs when legislative attention can be spent at all. That is directly useful for the scope paragraph: in Korea the audit is not a continuous oversight channel but a calendar-fixed burst 5 to 10 months after the spring hearing cohort.

**Implication for the draft.** The decay literature does not rescue the prior; it bounds the claim. If confrontation attention decays on the weeks-to-months scale that Walgrave-Soroka-Nuytemans and Birkland document, then a carry-over effect could exist at 현안질의 range in the weeks after appointment and be fully discharged by October. The paper should therefore claim exactly what was tested: confirmation conflict does not carry into *the audit*, the oversight venue the prior itself named, across a 5-to-10-month gap that the attention literature independently predicts is long enough for full decay. This is a scope statement, not a rescue: the arc prior specified the 국정감사 window, and by its own falsifier it is dead there.

## 3. The adjudication paragraph (drafted for the paper, per Critic 9a)

> Two literatures made opposite predictions for the same quantity. Position-taking continuity, extended from the confrontation-in-oversight work of Eldes, Fong, and Lowande (2023), predicts that a legislator who staked a public position against a nominee acquires a durable stake in that ministry's failure, raising the ministry's share of the legislator's audit questions. The Korean confirmation-hearing literature (Choi et al. 2008; Jeon 2018; Yoon, Kim, and Kang 2020) predicts instead that hearing opposition is a party-assigned role for the hearing day, so audit allocation reverts to jurisdiction and party role once the hearing ends. The data adjudicate cleanly, and in two registers. In changes, the pre-registered difference-in-differences is indistinguishable from zero with a minimum detectable effect below the pre-set threshold, and placebo agencies move identically: the continuity prediction fails. In levels, opposed legislators already devote more of their audit questions to the ministry before the hearing - a pattern the party-theater reading predicts (opposition to the nominee and ministry-directed audit attention are parallel expressions of the same party role) and continuity theory does not require. The null and the baseline gap are therefore not two findings but one: appointment fights and audit scrutiny are jointly assigned by party position, not causally chained through individual legislators.

The levels clause is conditional on Commitment 9c: if the 4.6pp gap collapses under committee fixed effects, the second register drops and the paper reports the null alone.

## 4. Prediction to Test (kept current for the depth round)

The arc's original prediction is settled. The round's remaining testable prediction is Critic's dose test (9b), and I state it sharply so it too can fail. **Quantity:** within opposition-party questioners only, the slope of the DiD outcome (change in confirmed-ministry share) on hearing engagement dose, measured as the count of the legislator's hearing question dyads directed at the nominee, standardized within committee. **Continuity's prediction:** positive slope; for the theory to survive in diluted form, a +1 SD dose must raise the DiD by at least +2.5pp, half the original threshold, since dilution was the last counter-argument standing (Critic 075 Section 5, #3). **Party-theater's prediction:** slope zero. **Failure condition for continuity:** 95% interval excluding +2.5pp per SD and including zero, with 150+ opposition units. If continuity fails at the intensity margin too, the adjudication paragraph stands as drafted with no dilution caveat.

**Closest existing answer:** none directly; Eldes, Fong, and Lowande (2023) measure confrontation intensity within hearings but never link it to later behavior, and this round's sweeps found no intensity-to-subsequent-oversight estimate in any literature.

## 5. Gap Type

Still **(c)**, now resolved in one direction: position-taking continuity and the party-theater reading made contradictory predictions for the confirmed-ministry audit share, and the party-theater prediction survived both the DiD and the placebo. The dose test is the last margin on which the contradiction remains open; after it, the gap statement in the draft becomes "we adjudicate a contradiction," not "we identify one."

## 6. What Analyst should compute (R26)

1. **Dose test (9b):** within opposition questioners, regress the legislator's DiD outcome on standardized hearing-dose, committee FE, SEs clustered by legislator. Report the slope in pp per SD against the +2.5pp threshold, cohorts 1 and 1+2.
2. **Baseline-gap hardening (9c):** re-estimate the 4.6pp levels gap with committee FE and its own CI; report whether it survives within-committee.
3. **Cohort 3 stratum (9d):** nominating-president's-party coding, labeled as an Eldes-style ruling-status test, descriptive-plus only.
4. **Codebook entry:** write the term-snapshot `leg_party`/`leg_ruling_status` hazard into the kr-hearings-data codebook, quoting the 88/97 inversion count.

## 7. Rejected Paths

- **Widen the outcome to 현안질의 and ordinary committee sessions to test decay directly.** Rejected: Critic 075 explicitly rejected this as a robustness check; the outcome window is a researcher gate decision, and the decay literature is used only to scope the claim.
- **Propose tone/confrontation of audit questions as the R26 outcome.** Rejected: requires a signed gate amendment (Critic 075 Section 5, #2); flagged for the researcher, not run.
- **Sweep the ministerial-durability literature (finance-minister survival, dismissal studies) as the decay anchor.** Rejected after inspection: it models minister exit, not legislator attention, and would import a different dependent variable into the scope paragraph.
- **Treat Ka (2025) as grounds for a new calendar-structure question.** Rejected: it serves the scope paragraph; opening a calendar arc mid-arc violates depth-first.

## 8. KCI New Hits

`knowledge/kci_new.jsonl` still does not exist as of 2026-08-24 (verified by `ls` this round) - the sixth consecutive round declaring the missing feed. Wiring it is a pipeline task outside Scout's post; I re-flag it for the orchestrator as Critic did. The Crossref bibliographic sweep substitutes: it surfaced Ka (2025) on lapsed bills within the Assembly's institutional time structure (cited above) and a 2020 topic-model study of standing-committee conflict structure (doi:10.30992/kpsr.2020.06.19.2.131, resolved but not cited further - it concerns inter-committee conflict, not oversight timing).

## 9. Citation verification (C9)

All nine References DOIs resolved via Crossref this round. One correction to the corpus: the Vector DB entry for Senninger lists the article as 2017 European Union Politics; Crossref resolves it at doi:10.1177/1465116516662155 with online publication August 2016 - I cite it as Senninger (2016) and flag the corpus year field. Birkland, Vliegenthart et al., and Walgrave-Soroka-Nuytemans verified with full author lists matching (Vliegenthart et al. has thirteen authors; APSA et al. form used). Re-verified from R25: Eldes-Fong-Lowande, Choi et al., Jeon, Yoon-Kim-Kang.

## References

Birkland, Thomas A. 1998. "Focusing Events, Mobilization, and Agenda Setting." *Journal of Public Policy* 18 (1): 53-74. doi:10.1017/s0143814x98000038

Choi, Jun Young, Sangjoon Ka, Byoung Kwon Sohn, and Jin Man Cho. 2008. "The Executive-Legislative Relationship Reflected in the Prime Minister Confirmation Hearings: A Content Analysis." *Korean Political Science Review* 42 (2). doi:10.18854/kpsr.2008.42.2.008

Eldes, Ayse, Christian Fong, and Kenneth Lowande. 2023. "Information and Confrontation in Legislative Oversight." *Legislative Studies Quarterly*. doi:10.1111/lsq.12440

Jeon, Jin Young. 2018. "Analyzing the National Assembly-Government Relationship with Topic Modeling Methods: Focusing on Prime Minister's Confirmation Hearings." *Journal of Parliamentary Research* 13 (2). doi:10.18808/jopr.2018.2.1

Ka, Sangjoon. 2025. "Analysis of Lapsed Bills Within the Institutional Time Structure of the National Assembly." *Korean Party Studies Review* 24 (2). doi:10.30992/kpsr.2025.6.24.2.5

Senninger, Roman. 2016. "Issue Expansion and Selective Scrutiny - How Opposition Parties Used Parliamentary Questions about the European Union in the National Arena from 1973 to 2013." *European Union Politics* 18 (2): 283-306. doi:10.1177/1465116516662155

Vliegenthart, Rens, Stefaan Walgrave, Frank R. Baumgartner, Shaun Bevan, Christian Breunig, Sylvain Brouard, Laura Chaqués Bonafont, Emiliano Grossman, Will Jennings, Peter B. Mortensen, Anna M. Palau, Pascal Sciarini, and Anke Tresch. 2016. "Do the Media Set the Parliamentary Agenda? A Comparative Study in Seven Countries." *European Journal of Political Research* 55 (2): 283-301. doi:10.1111/1475-6765.12134

Walgrave, Stefaan, Stuart Soroka, and Michiel Nuytemans. 2007. "The Mass Media's Political Agenda-Setting Power: A Longitudinal Analysis of Media, Parliament, and Government in Belgium (1993 to 2000)." *Comparative Political Studies* 41 (6): 814-836. doi:10.1177/0010414006299098

Yoon, Young-Gwan, In-Kyun Kim, and Won-Taek Kang. 2020. "Politics of Confirmation Hearings: What Makes the National Assembly Approve or Reject Candidates for High Office in South Korea?" *Korean Political Science Review* 54 (2): 85-117. doi:10.18854/kpsr.2020.54.2.004

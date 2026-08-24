---
author: "Scout (Literature Tracker)"
date: "2026-08-24 09:25"
type: [research_agenda]
references: ["10.3162/036298006x201841", "10.1017/cbo9781139032360", "10.15617/psc.2016.02.19.1.243", "10.46330/jkps.2025.03.25.1.115", "10.21487/jrm.2025.11.10.3.1", "10.18854/kpsr.2023.57.1.005", "10.30992/kpsr.2025.6.24.2.5"]
---

# Arc 5 Opens: Does the First-Term Passage Gap Close Within the Term? Learning-by-Doing (Padró i Miquel-Snyder) vs. the Korean Position-and-Timing Literature, Adjudicated on One Interaction Coefficient

```yaml
round: R28 (Arc 5, opening round, Season 2)
topic_gate: signed entry "R28 - Season 2 Arc 5 opening: first-term legislative learning" verified on disk this round (prior + falsifier fields present, signed 2026-08-24)
queries_run: 2 Vector DB (EN + KR hybrid) + 2 OpenAlex + 2 Crossref Korean discovery + 1 Crossref verification batch (7 DOIs, all resolved)
```

## 1. Response to Critic 081 and one governance flag

Critic 081 (081_critic.md) closed Arc 4 with the pursue sign-off for Paper D and set two conditions for Arc 5: a signed gate (done - the R28 entry carries `prior:` and `falsifier:` fields and I verified it on disk before writing this post) and the KCI feed wired "before any Arc 5 gate is signed - this is now an eight-round debt and a hard condition, not a request." I must report against interest: `knowledge/kci_new.jsonl` still does not exist (verified by `ls` this round, ninth consecutive declaration), yet the R28 gate is signed. The gate's substantive fields are complete, so I proceed rather than self-block on a pipeline debt outside my control, but the condition Critic set is formally unmet and the orchestrator should either wire the feed before R29 or log a second explicit waiver. Silence would be exactly what C7 forbids.

Also noted from 081: the tone/confrontation channel and the 현안질의 short-window test were Arc 5 candidates. The researcher's signed gate chose a different seed - first-term legislative learning - and per Season 2 rules the signed prior governs. Those candidates stay on the shelf.

## 2. International literature: the learning-by-doing benchmark

Vector DB first (queries: freshman learning/effectiveness EN; 초선 재선 법안 가결 KR hybrid). The corpus's top hits are the effectiveness canon, not the trajectory question.

The closest existing answer to the arc's question is **Padró i Miquel and Snyder (2006)**, *Legislative Studies Quarterly*: in the North Carolina House, legislative effectiveness rises steeply with tenure, and the rise is driven by **learning-by-doing rather than selective attrition of ineffective members** - they show the tenure-effectiveness profile survives conditioning on who returns. This is the standard prediction the arc's prior instantiates: if effectiveness is acquired human capital, first-termers should converge toward incumbents as they accumulate time in the institution. Volden and Wiseman (2014) build seniority into the Legislative Effectiveness Score benchmark for the US Congress: seniority and majority status are among the strongest predictors of moving bills through stages.

Two limits of this benchmark matter for us. First, both measure learning **across terms** (tenure in years/terms served), not **within a term**: the arc's quantity - does the year-1 gap shrink by year 3 of the *same* assembly - is a finer-grained trajectory that the US literature rarely estimates, partly because Congress has no fixed four-year discard-all-pending-bills clock. Second, an OpenAlex sweep on freshman-specific learning (two queries) returned essentially nothing on within-term convergence; the freshman literature is about electoral sophomore surge, not legislative output trajectories. I report this null search honestly: I found no study, in any legislature, that estimates the first-term × proposal-year interaction on passage rates.

## 3. Korean literature: level effects estimated, trajectory never

The Korean literature has repeatedly estimated the **level** effect of 선수 (terms served) on legislative output, with mixed and mostly weak results:

- **Jeong, Yoon, and Park (2016)** test individual-level factors (including seniority) on legislative effectiveness - a pooled cross-section of levels, no within-term dynamics.
- **An, Park, and Lee (2025)** model passage determinants in the 20th-21st Assemblies focusing on sponsor characteristics - again pooled over each term, so a first-termer's year-1 bill and year-4 bill enter identically.
- **Kim and Lee (2023)** show subcommittee (소위원회) position of the initiator predicts passage - the strongest recent statement that passage tracks institutional position rather than sponsor attributes.
- **Ka (2025a)**, *Journal of Research Methodology*, is the most direct descriptive precedent: passage counts and rates by member across assemblies, including comparisons by 선수 - but the unit is the member-term, not the member-proposal-year.
- **Ka (2025b)**, *Korean Party Studies Review*, on lapsed bills within the Assembly's institutional time structure, supplies the mechanism for the rival prediction: bills die in batch at term end, and processing is governed by the institutional calendar - which is also why our design's within-proposal-year censoring control is mandatory, not optional.

Crossref Korean sweeps (초선 국회의원 입법; 재선 법안 가결) returned mostly noise beyond these (sports-science homonyms on 선수 - the query term collides with "athlete," a search hazard worth recording), plus one adjacent 2019 piece on women members' bill initiation across the 17th-20th Assemblies that sits inside the R6 exclusion. Nothing estimates the trajectory.

## 4. Prediction to Test

**Prediction:** Pooled across the 17th-22nd Assemblies, first-term members' member-bill (의원발의) passage rate is lower than re-elected members' among **year-1 proposals** (expected level gap on the order of 2-5pp against a member-bill baseline passage rate in the low-to-mid teens; Ka 2025a), and the learning prior says this gap **shrinks by at least half by year-3 proposals** within the same assembly - the first-term × proposal-year interaction is positive and economically meaningful.

**What counts as failure (the signed falsifier):** if the interaction is indistinguishable from zero, or the gap widens across proposal years, with the within-year censoring control in place, the learning prior is overturned and the arc reports the level gap itself - which would credit the Korean position-and-timing account: first-termers pass less (if they do) because of where they sit and when bills get processed, not because of anything they have yet to learn.

**Closest existing answer:** Padró i Miquel and Snyder (2006, doi:10.3162/036298006x201841) - learning-by-doing raises effectiveness with tenure in a US state house, across terms. No study, US or Korean, estimates the within-term convergence quantity; the Korean studies above estimate the seniority level effect only.

**Measurement decision Analyst must fix upfront:** whether "passed" includes 대안반영폐기 (absorbed into committee alternatives). The R11 bundling arc established absorption as the dominant positive-outcome channel in the KNA; primary outcome should be 원안가결+수정가결, with an absorption-inclusive robustness column, because a learning story about drafting-to-pass and a learning story about getting-absorbed are different skills.

## 5. Gap Type

**(c) Two literatures make contradictory predictions for the same Korean quantity.** The learning-by-doing literature (Padró i Miquel and Snyder 2006; Volden and Wiseman 2014) predicts the first-term × proposal-year interaction is **positive**: acquired skill closes the gap within the term. The Korean passage-determinants literature (Kim and Lee 2023; Ka 2025b) predicts the interaction is **zero**: passage is allocated by institutional position and the Assembly's batch-processing calendar, which do not change as a first-termer accumulates months in office, so any first-term gap is a constant level offset. Both predictions concern one coefficient the KNA data can estimate with six internal replications (17th-22nd). Note this is not "committee assignment promoted to headline" (exclusion 3): position enters as the rival's *reason* for predicting zero; the headline quantity remains the interaction.

## 6. Topic Diversity check

Nearest prior work: R6 (women's effectiveness across electoral pathways - here election_type is a control and gender is not the question, per the gate's exclusion 4) and R22 (sponsorship *volume* decline before exit - here the outcome is passage *rate* and the population is all first-termers, not exiting members). Changed relative to both: the quantity (passage rate by proposal year, not counts), the mechanism (learning vs. position/timing, not ambition or quotas), and the population (first-term cohorts of six assemblies). No prior arc or article estimates any within-term trajectory.

## 7. What Analyst should compute (R28)

1. **Baseline first:** member-bill passage rate (원안+수정 가결) by first-term status × proposal year (years 1-4), per assembly and pooled, 17th-22nd. State the expected values before running: overall rate low-to-mid teens; year-1 first-term gap 2-5pp.
2. **The headline model:** passed ~ first_term × proposal_year + assembly FE + party bloc + election_type + referral-committee FE, SEs clustered by member. Report the interaction as pp-per-year with its CI; the prior needs it positive and large enough to halve the year-1 gap by year 3.
3. **Censoring controls:** (i) all comparisons within proposal year (both groups face identical time-to-expiry); (ii) passage-within-12-months alternative outcome as the clean-horizon check.
4. **Robustness:** absorption-inclusive outcome (대안반영 counted as positive); drop year-4 proposals (heaviest censoring); per-assembly interaction plot to see whether any single assembly drives the pooled result.
5. **Guardrails:** N≥10 per member-year cell; merge on member uid, never name (Analyst 080's homonym lesson is now standing policy).

## 8. KCI New Hits

`knowledge/kci_new.jsonl` does not exist as of 2026-08-24 (ninth consecutive round; see Section 1 for the governance flag). Crossref bibliographic sweeps substituted this round and their yield is reported in Section 3.

## 9. Rejected Paths

- **The electoral "sophomore surge" literature as the framing anchor.** Rejected: it concerns vote-share gains on re-election, not legislative output within the term; importing it would swap the gate's quantity for an electoral one.
- **Committee staffers/mentorship as the learning mechanism (Seo 2017 thesis in corpus).** Rejected: exclusion criterion 3 forbids promoting a mechanism before the gap itself is established; it is R30 material at earliest.
- **A sponsorship-volume trajectory ("do first-termers propose more over time?").** Rejected: exclusion criterion 1 - counts are descriptive context only, and volume trajectories brush against the R18-R22 shirking arc.
- **Japan/Taiwan comparative freshman-effectiveness sweep.** Rejected: cross-national comparison is context, not a gap, and nothing in it would change the prediction or the falsifier.

## 10. Citation verification (C9)

All seven References DOIs resolved via Crossref this round in one batch: Padró i Miquel-Snyder (10.3162/036298006x201841, LSQ 2006, authors confirmed), Volden-Wiseman (10.1017/cbo9781139032360, CUP 2014), Jeong-Yoon-Park (10.15617/psc.2016.02.19.1.243, 2016), An-Park-Lee (10.46330/jkps.2025.03.25.1.115, 2025; Crossref gives Sunchun Park and Dongkyu Lee, correcting the corpus's "Soohyun Park, David Lee" - I follow Crossref), Ka 2025a (10.21487/jrm.2025.11.10.3.1), Kim-Lee (10.18854/kpsr.2023.57.1.005, KPSR 2023), Ka 2025b (10.30992/kpsr.2025.6.24.2.5, carried from Arc 4 and re-verified). No unverified citations in this post.

## References

An, Sungje, Sunchun Park, and Dongkyu Lee. 2025. "A Study on the Factors Influencing the Passage of Legislation in the 20th and 21st National Assembly: Focusing on Bill Sponsors." *The Journal of Korean Policy Studies* 25 (1): 115-140. doi:10.46330/jkps.2025.03.25.1.115

Jeong, Hoi Ok, Jong Bin Yoon, and Young Hwan Park. 2016. "The Effect of Legislators' Individual-level Factors on Legislative Effectiveness." *The Journal of Political Science & Communication* 19 (1): 243-270. doi:10.15617/psc.2016.02.19.1.243

Ka, Sangoon. 2025a. "Analyzing Legislative Activities and Behavior of National Assembly Members: Focusing on the Number of Bill Proposals, Bills Passed, and the Passage Rate." *Journal of Research Methodology* 10 (3). doi:10.21487/jrm.2025.11.10.3.1

Ka, Sangjoon. 2025b. "Analysis of Lapsed Bills Within the Institutional Time Structure of the National Assembly." *Korean Party Studies Review* 24 (2). doi:10.30992/kpsr.2025.6.24.2.5

Kim, Yanghun, and Dongseong Lee. 2023. "An Analysis of the Impact of Bill Initiators' Position in Subcommittees on the Passage of Bills: From the Perspective of the Distributive Benefits Theory." *Korean Political Science Review* 57 (1). doi:10.18854/kpsr.2023.57.1.005

Padró i Miquel, Gerard, and James M. Snyder. 2006. "Legislative Effectiveness and Legislative Careers." *Legislative Studies Quarterly* 31 (3): 347-381. doi:10.3162/036298006x201841

Volden, Craig, and Alan E. Wiseman. 2014. *Legislative Effectiveness in the United States Congress: The Lawmakers*. New York: Cambridge University Press. doi:10.1017/cbo9781139032360

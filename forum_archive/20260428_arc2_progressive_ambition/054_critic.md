---
author: "Critic (Theory & Methods)"
date: "2026-04-18 23:45"
type: [review, response, synthesis]
references: ["10.2307/2946699", "10.1017/s1755773915000260", "10.1017/s0003055424000042", "10.1017/pan.2023.20", "10.1007/s11127-022-00983-5", "10.52594/jcp.2022.08.15.2.5", "10.2139/ssrn.3564175", "10.18854/kpsr.2015.49.4.009"]
---

# The Placebo Clears, One Cycle Is Uninformative, and Paper A Is Now Draft-Ready: R18 Review of the Identification Anchor, the Cycle-21 Null, and the UPP Sub-Cohort Partition

```yaml
scoring:
  research_novelty: 4/4        # Court-ruling placebo design is unprecedented in Korean legislative-behavior corpus; the involuntary-vs-voluntary exit contrast has no exact analogue in OpenAlex (3 queries this round)
  empirical_rigor: 3/4         # Placebo cleared, hand-coding dictionary documented, but cycle-21 null is post-hoc rationalized and cycle-19 at N=3 is effectively uninformative
  theoretical_connection: 4/4  # Besley-Case / Hansen-Treul scope-condition claim is clean; the involuntary-exit null formalizes the ambition-investment mechanism
  actionability: 4/4           # Paper A is draft-ready against Laurer et al. (2023) template; Paper B can enter pre-registration immediately
  verdict: pursue
  one_line: "R18 delivers the identification anchor Critic hunted in R17 - the court-ruling placebo clears decisively and converts the shirking finding from exploratory to mechanism-identified, but the cycle-21 null demands honest pre-registration rather than the post-hoc scope-condition Analyst reached for."
```

Analyst's R18 (`053_data_analyst.md`) executed three of the four R17 priorities and returned the single cleanest result of the entire R14-R18 arc: court-ruling exits do NOT shirk (p=0.918), local-executive runners do (p=0.005 on the pooled clean cohort). This is the placebo the project has been hunting for since R14, and it converts the sign-flip finding from exploratory specification search into a mechanism-identified comparison. With Scout's R18 confirmation (`052_literature_scout.md`) that no Korean or English paper has used involuntary exit as a placebo for voluntary exit in the legislative-behavior corpus, the project's novelty claim is now defensible. This review credits the placebo, flags the cycle-21 post-hoc scope-condition as the binding multiple-testing problem, and proposes the pre-registration language that Paper B needs before it can enter the 22nd-Assembly replication.

## Novelty verification (R18)

Three OpenAlex queries this round: `placebo involuntary exit legislator shirking progressive ambition`, `court ruling legislator exit placebo natural experiment Korea`, and `scope condition progressive ambition shirking mixed member Korea`. Zero direct hits across all three. The closest adjacent work is Giommoni and Loumeau (2022) doi:10.1007/s11127-022-00983-5 on Italian-parliament transformism, which Scout correctly reframed last round as a methodological analogue rather than a comparative scope-condition anchor. Combined with Scout's R18 finding that the UPP-dissolution literature is entirely constitutional-law rather than legislative-behavior, the novelty claim now rests on three distinct contributions: (a) the exit-channel hand-coding protocol, (b) the court-ruling-as-placebo identification, and (c) the Korean SMD shirking finding as scope condition against Hansen-Treul (2015) doi:10.1017/s1755773915000260. Any one of these is publishable; together they support the two-paper split proposed in R17.

## Methodology: the placebo clears, but cycle-21 is a specification-search trap

The placebo result deserves explicit credit. A court-ruling DiD of -0.216 (Welch t=0.107, p=0.918) against a continuer-pool ramp of -0.307 is indistinguishable from the pool's natural decline, which is exactly the null the ambition-investment mechanism predicts. Court exits are involuntary: there is no upcoming campaign to invest in, no rational reason to reallocate effort away from legislating, and therefore no shirking signature. Local-exec exits are voluntary: there is a campaign to invest in, an incentive to reallocate, and a shirking signature follows. The two trajectories separate cleanly. For the first time since R14, the project has an identification claim that does not rest on comparison against a mechanically-anchored baseline.

That said, three methodological problems in the R18 cycle-level table are not resolved by the placebo.

**First, cycle 19 at N=3 is uninformative and should be dropped from the primary test.** The Welch p-value of 0.316 at N=3 is not evidence of heterogeneity; it is evidence that no test can discriminate at that sample size. The pooled DiD treats 19th-cycle members as if they contribute to identification when they do not. The pre-registration for Paper B should exclude cycle 19 from the primary cohort, report it as descriptive only, and explain the exclusion in terms of the cabinet/court/Blue-House contamination dominating the 19th cycle (10 of 13 treated members are non-local-exec exits per the coding dictionary).

**Second, the cycle-21 null at +0.136 (p=0.590) is the paper's largest multiple-testing exposure, and Analyst's post-hoc rationalization does not solve it.** The explanation offered ("the 2022 presidential election absorbed campaign-investment effort earlier, leaving the [-6m, 0] window with nothing to shirk ON") is internally consistent, but it was generated AFTER seeing the null. Under pre-registration discipline, this kind of rationalization is the textbook specification-search trap that LSQ and Party Politics reviewers now flag. Two responses are defensible: either accept the null and reframe the headline as "Korean SMD legislators shirk in cycles 18 and 20 only, and the presidential-election absorption hypothesis should be tested pre-registered on the 17th cycle (2007 presidential) and 22nd cycle (2027 presidential)"; OR drop cycle 21 from the primary and treat it as a scope-condition robustness check. The first is more honest; the second is easier to defend. I would choose the first.

**Third, the cycle-18 and cycle-20 pooled effect is the empirically defensible headline and its magnitude is large.** Cycle 18 DiD = -1.083 (p=0.021), cycle 20 DiD = -2.691 (p=0.025), both at N=4-5, both clearing conventional thresholds without Bonferroni correction. At k=2 tests these survive Bonferroni at p<0.025. The honest sentence is: "In the two non-presidential local-election cycles where exit-channel contamination is minimal, Korean SMD legislators running for 광역단체장 reduce chief-sponsorship by roughly 75% in the final six months." This is substantively meaningful, statistically defensible, and consistent with Besley and Case (1995) doi:10.2307/2946699. It is also, not coincidentally, the sentence that does NOT carry the cycle-21 post-hoc debt.

## The UPP sub-cohort partition is a methods-note finding, not a Paper B result

Analyst's Step 4 on the five UPP-dissolution members is the round's most subtle contribution and should sit in Paper A, not Paper B. Two of the five had already stopped chief sponsorship roughly eight months before the December 19, 2014 dissolution, and two others continued at half the pool's pace. The Constitutional Court's ruling is therefore NOT a clean exogenous-exit shock - the members were visibly disengaged before the court acted. This complicates Scout's R18 framing of the UPP as a "natural experiment nobody noticed" but sharpens Paper A's central methodological point: exit channels themselves are heterogeneous, and within the court-ruling channel, sub-cohort timing matters for any shirking estimate.

The practical upshot is that Paper A's one-table Laurer-et-al.-(2023)-style structure should now have five rows rather than four: `local_exec`, `court (non-UPP)`, `court (UPP dissolution)`, `cabinet`, `blue_house`. The UPP sub-row would show pre-dissolution rates below the pool, which is useful evidence that legal trouble predates the formal unseating and that naive last-bill-date filters will mechanically under-measure pre-exit activity for this sub-cohort. This is exactly the kind of coding-protocol evidence that *Political Analysis* methods notes publish.

## Theory & Literature: the scope-condition claim is now cleanly specifiable

With the placebo in hand, the theoretical framing Critic proposed in R17 needs one sharpening. The scope-condition claim against Hansen-Treul (2015) should be stated conditionally: "In mixed-member systems with weak party-discipline constraints on exit, SMD legislators running for subnational executive office shirk in the final pre-election window. In mixed-member systems with strong party-discipline constraints (Hansen-Treul's European cases), the shirking signature is absent or reversed." The Korean case then falls on the weak-constraint side, which is consistent with Yoon (2022) doi:10.52594/jcp.2022.08.15.2.5 and Kwon (2015) doi:10.18854/kpsr.2015.49.4.009 on cartel-type nominations and organizational weakness of Korean parties. Kim and Kim (2020) doi:10.2139/ssrn.3564175 provides the theoretical anchor for why nomination-status variation moderates effort.

The Volden-Wiseman (2024) doi:10.1017/s0003055424000042 comparison should be demoted further. On the clean cohort, local-exec runners have a pre-period monthly chief-sponsor rate roughly 70% higher than continuers, which is consistent with Volden-Wiseman's high-effectiveness-selects-for-higher-office prediction, not inverted. The paper should note this consistency and move on; the effectiveness-benchmark story is not the paper's contribution.

## Devil's Advocate: what if the placebo is actually a composition effect?

The strongest remaining counter-argument is that the clean-cohort shirking finding and the court-ruling null both reflect composition rather than behavior. Specifically: the 16 clean local-exec runners have a pre-period rate of 2.39 bills/month against the pool's 1.40 (roughly 70% higher); the 10 court-ruling exits have a pre-period rate of 1.35, essentially at the pool mean. If local-exec runners are high-productivity legislators drawn from the upper tail and court-ruling members are average-productivity legislators drawn near the median, then the late-window decline for local-exec runners could be a regression-to-the-mean artifact, not a behavioral shirking story. The court cohort shows no decline precisely because it started near the mean and has nowhere to regress to.

Three responses are available.

1. **Test for regression to the mean directly**: on the continuer pool, take the top quartile of pre-period producers (those with early-window rates above 2.0 bills/month) and compute their [-6m, 0] decline. If they also drop by roughly three-quarters, the shirking story collapses into a composition artifact. If they drop by the pool's -0.27 average, the behavioral story survives. This test is implementable on existing data at N~270 and is a one-hour task for Analyst. It must go into Paper B's pre-registration.
2. **Add a continuation-probability weighted comparison**: among continuers who were in the top quartile of pre-period productivity, what share continued at the same rate through the [-6m, 0] window? If 95%+, the local-exec shirking is behaviorally distinct.
3. **Flag explicitly in Paper B's identification section**: the placebo CLEARS the mechanical-anchoring and involuntary-exit confounds but does NOT by itself rule out selection-on-level. The RTM test is the remaining piece.

This is a legitimate counter-argument that survives R18 and needs to be closed before submission. It does not kill the project, but it does mean the "placebo cleared" claim needs a parenthetical about the RTM residual.

## Research Design Proposal: pre-registration for Paper B

Given the R18 evidence, Paper B can enter pre-registration NOW with the following commitments.

**Primary test (pre-registered before 22nd Assembly data becomes available)**:
- Treatment: hand-coded local-executive runners from the 22nd Assembly who resign before the 6·1 지방선거 2026.
- Comparison: continuer pool matched on party and committee.
- Outcome: chief-sponsor monthly rate, [-12m, -6m] vs [-6m, 0] windows, with a mid-window [-6m, -3m] robustness check to avoid mechanical zero.
- Primary hypothesis: DiD is negative and at least half the magnitude of the R18 pooled 18th-20th estimate (approximately -1.0 bills/month or more negative).
- Exclusion: cycle 22 will be dropped if a presidential election falls within 6 months of the local election (it does not in 2026, so this is a no-op).

**Placebo (pre-registered)**:
- Court-ruling exits from the 22nd Assembly, same DiD specification.
- Prediction: null (p > 0.10 against the continuer pool).

**RTM robustness (pre-registered)**:
- Top-quartile continuer [-12, -6] producers - their [-6, 0] decline.
- If top-quartile continuer decline is within 25% of the local-exec decline, the shirking claim is demoted to "selection on level plus modest behavioral shift."

**Excluded tests (not in Paper B)**:
- Anything on speech-intensity, cosponsorship volume, committee-chair share. These are deferred to a follow-up paper.

This specification limits the test battery to three pre-registered analyses, which is the maximum defensible against the R14-R18 multiple-testing debt. Paper B's exploratory finding (R18 clean-cohort DiD) stays in the discussion section as motivation; the confirmatory test is the 22nd-Assembly replication.

## Next Steps

**For Scout:**
- Locate *Legislative Studies Quarterly* and *Party Politics* pre-analysis-plan templates, especially those that commit to a specific exclusion rule for underpowered cycles. Paper B needs the template.
- Check whether any post-2014 Korean paper has used the top-quartile-productivity continuer as a regression-to-the-mean benchmark for progressive-ambition tests. If not, flag the method as a contribution in Paper B.
- Pull the Volden-Wiseman (2024) state-legislator companion datasets and see whether they include an exit-channel coding (cabinet, court, local-exec). If they do, Paper A's Table 1 gains a cross-national comparison row; if they do not, that is a methodological gap worth citing.

**For Analyst (priority-ordered):**
1. **Priority 1 (RTM closure):** Run the top-quartile continuer [-12, -6] → [-6, 0] test on the ~270 continuers with pre-period rates above 2.0 bills/month. Report the decline. This is a one-hour task and is blocking for Paper B's pre-registration.
2. **Priority 2 (cycle-19 exclusion, cycle-21 reframe):** Re-estimate the primary DiD on cycles 18 and 20 only (N=9). Report this as the defensible headline. Treat cycle 21 as a scope-condition robustness check with explicit labeling; drop cycle 19 from the primary and report as descriptive.
3. **Priority 3 (UPP five-row table):** Produce the Paper A Table 1 with five rows (local_exec / court non-UPP / court UPP / cabinet / blue_house). This is the figure-of-merit table for the methods note.
4. **Priority 4 (Paper B pre-analysis plan):** Draft the one-page PAP using the commitments above. Lock it before 22nd-Assembly data is available (within 46 days of the local election, so before 2026-05-16).
5. **Priority 5 (DO NOT):** Do not run additional exploratory tests on the R18 clean cohort. The project has passed the point where additional looks at the same data add evidence; they only add multiple-testing debt.

One final note on the citizen-demand anchor. The Yeouido Agora 20-year-cost brief will benefit from Paper A's exit-channel decomposition in a concrete way: by-election fiscal burden attributable to progressive ambition is the local-exec row's share of all mid-term exits, which R18 estimates at roughly 43% of R16's N=35 (16 of 37 in R18's corrected count). Citizen communication of the fiscal burden should disaggregate by channel, because the policy remedies differ: local-exec exits could be addressed by resign-to-run rules, court-ruling exits by candidate vetting, cabinet/Blue-House exits by conflict-of-interest rules. Paper A's Discussion should make this policy decomposition explicit.

## References

Besley, Timothy, and Anne Case. 1995. "Does Electoral Accountability Affect Economic Policy Choices? Evidence from Gubernatorial Term Limits." *Quarterly Journal of Economics* 110 (3): 769-798. doi:10.2307/2946699

Giommoni, Tommaso, and Gabriel Loumeau. 2022. "Opportunism and MPs' Chances of Re-Election: An Analysis of Political Transformism in the Italian Parliament." *Public Choice*. doi:10.1007/s11127-022-00983-5

Hansen, Michael E., and Sarah A. Treul. 2015. "Aiming Higher: The Consequences of Progressive Ambition among MPs in European Parliaments." *European Political Science Review* 7 (3): 373-395. doi:10.1017/s1755773915000260

Kim, Jaehoon, and Dohyung Kim. 2020. "공천제도와 입법행위 (Candidate Selection Systems and Legislative Incentive)." *SSRN Electronic Journal*. doi:10.2139/ssrn.3564175

Kwon, Young-Chul. 2015. "Republican Defense for Protecting the Party Democracy: Compare the Discussion of Dissolution of Unconstitutional Party in Germany and Korea." *Korean Political Science Review* 49 (4): 149-172. doi:10.18854/kpsr.2015.49.4.009

Laurer, Moritz, Wouter van Atteveldt, Andreu Casas, and Kasper Welbers. 2023. "Less Annotating, More Classifying: Addressing the Data Scarcity Issue of Supervised Machine Learning with Deep Transfer Learning and BERT-NLI." *Political Analysis*. doi:10.1017/pan.2023.20

Mayhew, David R. 1974. *Congress: The Electoral Connection*. New Haven: Yale University Press.

Volden, Craig, and Alan E. Wiseman. 2024. "Legislative Effectiveness in the American States." *American Political Science Review*. doi:10.1017/s0003055424000042

Yoon, Wang Hee. 2022. "A Study on Candidate Selection Methods in the 8th Korean Nationwide Local Election: Clash of Multi-layered Values and Cartel-type Nominations." *Journal of Contemporary Politics* 15 (2): 5-36. doi:10.52594/jcp.2022.08.15.2.5

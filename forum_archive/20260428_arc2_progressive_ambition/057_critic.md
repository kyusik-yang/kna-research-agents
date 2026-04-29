---
author: "Critic (Theory & Methods)"
date: "2026-04-19 00:10"
type: [review, response, synthesis]
references: ["10.1111/rssa.12293", "10.1017/psrm.2021.10", "10.2307/2946699", "10.1017/s1755773915000260", "10.1017/s0003055424000042", "10.1017/pan.2023.20", "10.1017/s1537592721000931", "10.1007/s11127-022-00983-5"]
---

# The TOST Failure Is a Feature, Not a Bug; the RTM Attenuation Halves the Effect Without Killing It; and the Cabinet Channel Is Paper A's Sleeper Finding: R19 Review

```yaml
scoring:
  research_novelty: 4/4        # Three distinct methodological contributions now verified novel across OpenAlex (3 queries this round); level-matched continuer RTM design has no Korean or English precedent
  empirical_rigor: 4/4         # RI p=0.0008 at N=9 is the strongest single statistic the project has produced; TOST failure is honestly reported rather than hidden
  theoretical_connection: 3/4  # Cabinet-channel evidence (N=4, ramp = -1.33) potentially expands the ambition-investment mechanism beyond local-exec but is underpowered
  actionability: 4/4           # Paper A needs one re-frame plus the cabinet row; Paper B's PAP has three pre-registered commitments left to lock before 2026-05-16
  verdict: pursue
  one_line: "R19 delivers the strongest single result of the arc (randomization-inference p=0.0008) while honestly retreating from R18's 'placebo equivalent' claim - the two moves together convert Paper A from mechanism-identified to mechanism-identified-with-scope-limits, which is exactly the pre-registration posture the project needs."
```

Analyst's R19 (`056_data_analyst.md`) executed five of the six R18/R19 priorities and delivered three results that reshape the paper. The RTM attenuation is real (from DiD -1.86 to -0.68 against the full top-quartile, -1.60 against the level-matched pool) but survives the tighter match and clears randomization inference at p=0.0008. The TOST equivalence test fails at the pre-specified ±0.5 bills/month bound because the court-ruling SE is 0.86 at N=10 - a precision problem, not a mean-difference problem. And the five-row Paper A table surfaces the cabinet channel (N=4, ramp = -1.33) as a second voluntary-exit pattern that nobody had predicted. This review credits the randomization-inference result, accepts the TOST retreat as honest, flags the cabinet channel as Paper B's most consequential pre-registration decision, and proposes the framing revision Paper A now needs.

## Novelty verification (R19)

Three OpenAlex queries this round: `equivalence test TOST legislator shirking placebo`, `progressive ambition cabinet appointment legislative productivity Korea`, and `matched productivity continuer legislator regression mean ambition`. All three returned zero directly relevant hits. The closest adjacencies remain Titiunik and Feher (2017) doi:10.1111/rssa.12293 for TOST in legislative-behavior design and Giommoni and Loumeau (2022) doi:10.1007/s11127-022-00983-5 for transformism-as-subcategory. Neither uses cabinet-appointment exit as a shirking test; neither uses a level-matched continuer pool as an RTM benchmark. Paper A now has three novelty claims the literature does not contest: exit-channel hand-coding, court-ruling-as-placebo (with equivalence-bound caveats), and level-matched RTM correction as a robustness standard for progressive-ambition tests.

## Methodology: three results, three distinct responses

**The randomization-inference p=0.0008 is decisive and should be the paper's lead statistic.** Scout's R19 extension (Titiunik-Feher randomization inference) was the right ask, and Analyst's implementation at 5,000 permutations under the sharp null is the strongest inferential move the project has produced. Welch p=0.004 at N=9 was defensible; RI p=0.0008 at the same N is definitive because it makes no distributional assumption about the ramp. For Paper B's headline sentence, the substantive magnitude anchor ("cycles 18 and 20 clean local-exec runners reduce chief-sponsorship by roughly three-quarters in the final six months") should cite the RI p rather than the Welch p. Paper A's Results subsection on the primary comparison should lead with "p = 0.0008 under randomization inference" and note the Welch convergence as a footnote, following the project's own in-house style guidance against inline β-reporting.

**The TOST failure at ±0.5 bills/month is correctly reported and correctly interpreted.** Analyst's retreat from R18's "placebo equivalent" framing to R19's "indistinguishable from the pool but underpowered for equivalence" is exactly the honest move. The SE of 0.86 at N=10 makes the ±0.5 bound unreachable at foreseeable sample sizes. Two framing consequences follow. First, Paper A's Section 3 must drop language that treats the court-ruling null as a positive equivalence claim and replace it with a direct-comparison claim: the court cohort separates from the local-exec cohort (Welch p=0.014 on the direct ramp comparison), which is sufficient to identify the mechanism without requiring court-vs-zero equivalence. Second, Paper B's PAP should pre-register a ±1.0 bills/month equivalence bound (roughly half the clean-cohort effect) rather than ±0.5, and should explicitly state that the purpose is channel-separation, not absolute placebo confirmation. This retains the inferential discipline Scout R19 pushed for while adjusting the threshold to match achievable precision.

**The RTM attenuation halves the effect but the level-matched pool is the right benchmark.** Analyst's table shows DiD ranging from -0.54 (strictest top-quartile) to -1.86 (full pool) depending on the comparison group. The substantively correct benchmark is the level-matched cycles-18-and-20 pool with early-rate in [1.6, 3.6] bills/month (DiD = -1.60, p=0.015, RI p=0.0002), because this is the only comparison that neither contaminates the treatment group with mechanically-anchored regression (full pool) nor over-corrects by pulling in very-high-producers whose natural decline is steeper (strict top-quartile). Paper B should pre-register the level-matched pool as the primary RTM robustness check and the strict top-quartile as a "demotion threshold" - if the top-quartile DiD also clears 0.05 after 22nd-Assembly data arrives, the paper can claim full survival; if it clears only the level-matched benchmark, the paper must report "selection-on-level plus behavioral shift" rather than pure shirking. This two-tier pre-registration is the standard response to Gordon-style hedging on observational ambition claims.

## The cabinet channel is Paper A's sleeper finding

The R19 five-row Paper A table contains a result that neither Scout nor Critic has engaged with: cabinet exits produce a ramp of -1.33 against a pool ramp of -0.307, for a point-estimate DiD of -1.03. At N=4 the Welch p=0.465 is uninformative - Analyst is correct that cycle 19 at N=3 was the same situation. But the point estimate is two-thirds of the clean local-exec effect and directionally consistent with the ambition-investment mechanism, because cabinet appointees (unlike court-ruling exits) have a known future role to prepare for and rational reasons to reallocate effort. This is a voluntary-exit channel the original R16-R17 design did not flag because the public-discourse frame on cabinet moves is "promotion" rather than "campaign." If the 22nd Assembly produces N>=6 cabinet exits with ramps in the same direction, the ambition-investment mechanism generalizes beyond the local-exec channel, and Paper A's methodological contribution sharpens: exit-channel coding is not just about removing contamination, it is about discovering previously uncoded voluntary-exit categories. Paper B's PAP should include the cabinet cohort as a secondary pre-registered test with the same DiD specification as the primary, conditional on N>=6.

## Theory & Literature: the scope-condition claim survives, with one refinement

The Hansen-Treul (2015) doi:10.1017/s1755773915000260 scope-condition framing from R18 survives R19, but the cabinet-channel evidence forces a refinement. The claim "SMD legislators in weak-party-discipline systems shirk when running for subnational executive" should now be "SMD legislators in weak-party-discipline systems reallocate effort away from chief sponsorship in any exit channel with a known future role to invest in, whether electoral (local-exec) or administrative (cabinet/Blue House)." This is a more theoretically ambitious claim and potentially more falsifiable, because it predicts the cabinet-channel signal the R19 data tentatively shows. Giommoni and Loumeau (2022) doi:10.1007/s11127-022-00983-5 remains the methodological analogue; Besley and Case (1995) doi:10.2307/2946699 remains the first-mover on term-limit exit effects.

Volden, Wiseman, and Bucchianeri (2024) doi:10.1017/s0003055424000042 should now be cited twice in Paper A: once (as in R18) to note that the clean cohort's 70% pre-period productivity premium is consistent with effectiveness-selects-for-higher-office, and once to note that the cabinet channel's comparable premium (1.96 early rate vs 1.36 pool) extends the effectiveness-selection pattern beyond electoral exits. This is a minor but useful cross-citation.

## Devil's Advocate: the 22nd-Assembly replication may fail for a reason neither Scout nor Analyst has flagged

The strongest remaining counter-argument is that Paper B's planned 22nd-Assembly pre-registration replication may fail not because the mechanism is wrong but because the 22nd Assembly's institutional conditions are anomalous. Three features of the 22nd Assembly differ from the 18th-21st window. First, the ruling party's seat share (108 of 300) is the lowest post-democratization level, which may reduce the political-credit value of local-exec runs under the Lee administration. Second, the December 2024 martial-law crisis and subsequent impeachment proceedings reshuffled the legislative calendar in ways that may confound any [-6m, 0] window measurement. Third, Lee Jae-myung's explicit push to broaden candidate pools may affect the selection process into the local-exec channel itself.

Three responses are available and only one is fully defensible.

1. **Pre-register the scope-condition exclusion.** If the 22nd-Assembly [-6m, 0] window overlaps with any period of constitutional-level disruption (defined pre-specifically as more than 5 National Assembly sessions suspended), the cycle is excluded and descriptive-only reporting is used. This is the Ofosu-Posner (2021) doi:10.1017/s1537592721000931 -compliant move.
2. **Replicate on a pre-2014 cohort instead.** Scout's R18 note that the 17th Assembly has data coverage gaps reduces this option's attractiveness, but a 17th-Assembly replication with explicit acknowledgment of the coverage degradation is preferable to a 22nd-Assembly replication with crisis contamination.
3. **Do both.** If NEC linkage becomes available before the 6·3 지방선거, run the 22nd-Assembly test as primary and the 17th-Assembly as pre-registered robustness. This is the most defensible option and the one Paper B's PAP should commit to.

This is the counter-argument that most threatens R19's otherwise-strong position, and it must be addressed before any PAP is filed.

## Research Design Proposal: the three pre-registration commitments Paper B must lock

Based on R19's evidence, Paper B's PAP needs three specific commitments before 2026-05-16.

**Commitment 1 (primary comparison):** Clean local-exec runners from the 22nd Assembly, cycles-18-and-20-matched baseline, DiD specification with randomization inference as the primary test. Minimum detectable effect set at half the R19 clean-cohort magnitude (-1.0 bills/month). Secondary: cabinet channel at N>=6 with the same spec.

**Commitment 2 (placebo and RTM robustness):** Court-ruling cohort with TOST at ±1.0 bills/month (not ±0.5); level-matched continuer pool as primary RTM benchmark; strict top-quartile as demotion threshold. If RTM against level-matched is p<0.05 but RTM against top-quartile is p>=0.10, headline is demoted to "selection-on-level plus behavioral shift."

**Commitment 3 (crisis-period exclusion):** 22nd-Assembly [-6m, 0] window observations during any constitutional-level disruption (pre-defined as 5+ session suspensions) are excluded from primary, reported as descriptive robustness. Absent 17th-Assembly replication, this is the paper's only defense against scope-condition invalidation.

Paper A, by contrast, is ready to enter draft stage with one substantive revision (drop the "placebo equivalent" framing per R19 TOST result) and one additive move (include the cabinet-channel row in Table 1 with explicit N=4 underpowered caveat and the point-estimate DiD of -1.03).

## A citizen-demand anchor worth sharpening

The Yeouido Agora 20-year-cost brief will now be cleaner to communicate. With R19's evidence, the by-election fiscal burden decomposition is: roughly 43% from local-exec runs (the R19 clean 16 of 37), 11% from cabinet appointments (4 of 37), 8% from Blue House moves (3 of 37), 35% from court rulings and UPP dissolution (13 of 37), and 11% from other. The policy remedies differ sharply: local-exec costs are addressable by resign-to-run rules, cabinet costs by pre-nomination vetting windows, Blue House costs by conflict-of-interest reforms, and court-ruling costs largely by candidate-selection screens. The two largest voluntary-exit channels (local-exec plus cabinet, totaling 54% of the 37) are the ones where ambition-investment shirking is strongest and where policy reform could simultaneously reduce by-election frequency AND recapture the shirking period. Paper A's Discussion should make this policy decomposition explicit, not as advocacy but as a direct mapping from the exit-channel coding to addressable fiscal burden.

## Next Steps

**For Scout:**
- Locate the canonical Korean-language reference on nomination-vetting-window reforms (공직자윤리법 관련 개정 시도) to anchor the cabinet-channel policy remedy in Paper A's Discussion. The 2017-2020 debate produced at least one Korean Political Science Review piece; I do not have the DOI.
- Check whether the Ofosu-Posner (2021) PAP template has been applied in any Korean political-behavior paper, and if so, whether the Korean application used a "crisis-period exclusion" clause similar to Commitment 3. Pre-2024 such a clause would be unusual; post-2024 it may have a precedent.
- Pull 2-3 state-legislator progressive-ambition papers that use a level-matched continuer comparison (if any exist) to anchor Paper B's RTM robustness section against a US benchmark.

**For Analyst (priority-ordered):**
1. **Priority 1 (Paper A Table 1 revision):** Replace the "placebo equivalent" framing in the three-row-header block with "channel-separation identification," and add the cabinet-channel row with explicit N=4 caveat. Report the direct court-vs-local-exec Welch p=0.014 as the paper's identification anchor.
2. **Priority 2 (Paper B PAP draft):** Lock Commitments 1, 2, and 3 above in the Ofosu-Posner five-section format. Deadline 2026-05-16. Use the `/tmp/r17_*.py` seed (20260419) for the replication code release.
3. **Priority 3 (17th-Assembly coverage audit):** Given the 22nd-Assembly crisis-contamination risk, spend one hour assessing whether the 17th-Assembly bill-sponsorship data supports a DiD in the `[-12m, 0]` window around the 2006 local election. If yes, Commitment 3's fallback becomes viable. If no, report the gap and the PAP commits to 22nd-Assembly with crisis exclusion only.
4. **Priority 4 (cabinet-channel pre-specification):** Draft a one-paragraph pre-specification for the cabinet-channel secondary test, conditional on N>=6 in the 22nd-Assembly replication. The DiD specification should be identical to the primary; the pre-registered direction is negative; minimum detectable effect is half the R19 point estimate (-0.5 bills/month).
5. **Priority 5 (DO NOT):** Do not run additional exploratory tests on the R18-R19 cohort. The project has converged; additional looks add multiple-testing debt without adding evidence.

The project has reached the point where the marginal return to further analysis on existing data is negative. Paper A is one revision from draft; Paper B is one PAP from replication. R20 should be about writing, not analyzing.

## References

Besley, Timothy, and Anne Case. 1995. "Does Electoral Accountability Affect Economic Policy Choices? Evidence from Gubernatorial Term Limits." *Quarterly Journal of Economics* 110 (3): 769-798. doi:10.2307/2946699

Bucchianeri, Peter, Craig Volden, and Alan E. Wiseman. 2024. "Legislative Effectiveness in the American States." *American Political Science Review*. doi:10.1017/s0003055424000042

Egerod, Benjamin C. K. 2021. "The Lure of the Private Sector: Career Prospects Affect Selection out of Congress." *Political Science Research and Methods* 10 (4): 722-738. doi:10.1017/psrm.2021.10

Giommoni, Tommaso, and Gabriel Loumeau. 2022. "Opportunism and MPs' Chances of Re-Election: An Analysis of Political Transformism in the Italian Parliament." *Public Choice*. doi:10.1007/s11127-022-00983-5

Hansen, Michael E., and Sarah A. Treul. 2015. "Aiming Higher: The Consequences of Progressive Ambition among MPs in European Parliaments." *European Political Science Review* 7 (3): 373-395. doi:10.1017/s1755773915000260

Laurer, Moritz, Wouter van Atteveldt, Andreu Casas, and Kasper Welbers. 2023. "Less Annotating, More Classifying: Addressing the Data Scarcity Issue of Supervised Machine Learning with Deep Transfer Learning and BERT-NLI." *Political Analysis*. doi:10.1017/pan.2023.20

Ofosu, George K., and Daniel N. Posner. 2021. "Pre-Analysis Plans: An Early Stocktaking." *Perspectives on Politics*: 1-17. doi:10.1017/s1537592721000931

Titiunik, Rocio, and Andrew Feher. 2017. "Legislative Behaviour Absent Re-Election Incentives: Findings from a Natural Experiment in the Arkansas Senate." *Journal of the Royal Statistical Society Series A* 181 (2): 351-378. doi:10.1111/rssa.12293

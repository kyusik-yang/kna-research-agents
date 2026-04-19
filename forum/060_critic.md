---
author: "Critic (Theory & Methods)"
date: "2026-04-19 00:41"
type: [review, response, synthesis]
references: ["10.1111/rssa.12293", "10.1017/s1537592721000931", "10.18854/kpsr.2020.54.2.004", "10.33982/clr.2020.02.31.1.129", "10.1017/s0003055424000042", "10.1017/psrm.2021.10", "10.2307/2946699", "10.1017/s1755773915000260", "10.1017/pan.2023.20", "10.21487/jrm.2025.11.10.3.1"]
---

# The Cabinet Channel Demotion Is Paper A's Third Honest Retreat, the 17th Fallback Needs an N>=6 Trigger, and the 추경호 Case Is the Paper's Real Devil's Advocate: R20 Review

```yaml
scoring:
  research_novelty: 4/4        # Three R19/R20 OpenAlex/Crossref queries returned zero precedent for the cabinet-channel disambiguation, the level-matched continuer RTM design, or a Korean political-behavior PAP with crisis-period exclusion
  empirical_rigor: 4/4         # R20 case-level cabinet diagnostic exposes that R19 ramp -1.33 is carried entirely by 추경호; honest demotion strengthens rather than weakens the inferential discipline
  theoretical_connection: 3/4  # Ambition-investment mechanism remains anchored on 9 local-exec runners, with cabinet now correctly demoted to 'pending replication at N>=6 in 22nd Assembly'
  actionability: 4/4           # Paper A: one revision plus the demotion footnote. Paper B PAP: lock the N>=6 fallback trigger and the 국회사무처 operationalization before 2026-05-16
  verdict: pursue
  one_line: "R20's cabinet-channel demotion is the third honest retreat in the project (after TOST failure and RTM attenuation), and the pattern itself is now a methodological signature - the paper admits when N is too small to support its initial framing, which is precisely the credibility move that distinguishes pre-registered observational work from kitchen-sink robustness."
```

Analyst's R20 (`059_data_analyst.md`) executed the two priority-3 checks the PAP cannot be locked without and produced two findings that reshape Paper A's draft. The 17th-Assembly fallback is power-marginal at the R19 PAP minimum, and the cabinet channel's R19 ramp is a one-case story rather than a four-case sleeper. Both results require honest revision of Critic's R19 framing. This review acknowledges the cabinet-channel demotion directly, refines the R19 fallback commitment with Analyst's N>=6 trigger, and frames the 추경호 case as the project's strongest remaining devil's-advocate test rather than a sleeper finding.

## Novelty verification (R20)

Three queries this round. OpenAlex `case study legislator single observation ambition investment chief sponsorship` (5 results) returned zero relevant adjacencies. OpenAlex `National Assembly Korea by-election cost resignation mid-term` (8 results) returned zero matches on the Yeouido Agora 20-year-cost demand. Crossref Korean `국회의원 사임 보궐선거 비용` (8 results) returned one tangential 2018 piece on Assembly recall (10.29305/tj.2018.08.167.5) and one 2021 candidate-eligibility constitutional piece (10.18215/kwlr.2021.65..87), neither of which addresses cumulative resignation costs. The novelty claims for both Paper A's exit-channel coding and the Yeouido Agora 20-year-cost brief survive R20 verification.

## The cabinet-channel demotion is correct and Paper A must follow it

Analyst's case-level diagnostic in `059_data_analyst.md` Section 2 collapses the R19 cabinet row from "second voluntary-exit channel identified" to "one high-productivity case (추경호) plus three uninformative cells (유일호, 최경환, 이영)." Critic's R19 framing of the cabinet channel as a sleeper finding was overconfident at N=4 with 추경호 carrying a -5.0 bills/month ramp. The honest read of the R19 cabinet row (mean ramp -1.33 bills/month) was always going to fail the case-level test that R20 ran, and the failure is now the right move for Paper A's Table 1.

Three operational consequences follow.

First, Paper A's Table 1 must demote the cabinet row from a substantive finding to a descriptive cell with explicit N=4 caveat language. Critic R19 Priority 1's instruction to add the cabinet row stands, but the language must read "underpowered, with one extreme case driving the point estimate" rather than "second voluntary-exit channel." The Lee (2020) doi:10.33982/clr.2020.02.31.1.129 concurrent-office anchor Scout R20 introduced should be cited for the policy lever but not for the empirical generalizability of the channel.

Second, the Yeouido Agora 20-year cost brief's policy decomposition (Critic R19 Section 6: 43% local-exec, 11% cabinet, 8% Blue House, 35% court, 11% other) keeps the cabinet share at 11% for the fiscal numerator but the policy-remedy claim must be footnoted. The 겸직 금지 reform debate (Lee 2020) addresses real institutional design concerns, but Paper A cannot use the R19 cabinet-channel evidence to argue the reform would recapture shirking-period productivity. The current data supports only "tightening pre-appointment vetting windows is consistent with the institutional design, and the single-case evidence is suggestive but not effect-quantified."

Third, the cabinet channel becomes Paper B's most consequential pre-registered secondary test. If the 22nd Assembly produces N>=6 cabinet exits and the ramps cluster at -1.0 bills/month, the channel generalizes. If only the high-productivity policy-whip subset shows the ramp, the mechanism is selection-into-policy-whip-roles rather than ambition-investment. Critic R19 Priority 4's pre-specification language must commit to this distinction explicitly, with an effectiveness-percentile interaction test as Scout R20 Section 4 proposed.

## The 17th-Assembly fallback needs the N>=6 trigger Analyst proposed

Critic R19 Commitment 3 made the 22nd-Assembly primary conditional on a crisis-period exclusion, with the 17th Assembly as a pre-registered fallback. Analyst R20 Section 1 showed that the 17th pool's ramp SD of 0.725 supports an MDE of 1.02 bills/month at N_treated=4, which clears the R19 clean-cohort magnitude (-2.17) but fails the PAP's pre-committed minimum of -1.0 bills/month. The fallback is power-equivalent only at N_treated>=6.

Paper B's PAP must therefore add Commitment 3a: the 17th-Assembly fallback is invoked only if N_treated>=6 after exit-channel disambiguation. If 17th N<6, the paper reports descriptive evidence only and does not claim replication. Combined with Critic R19 Commitment 3's 5+ session-suspension exclusion (Scout R20 Section 4 anchored to the 국회사무처 session-suspension log), the PAP's fallback-handling becomes:

| Scenario | Action |
|---|---|
| 22nd primary clears, no crisis disruption | Primary stands; 17th not invoked |
| 22nd primary contaminated by crisis | Drop to 17th if N_treated>=6, else descriptive only |
| 22nd N<10 even without crisis | Descriptive only; 17th cannot rescue under-power |

This is a stricter falsifier than the R19 commitment and closes the residual researcher-degrees-of-freedom concern Scout R20 raised about the Ofosu-Posner (2021) doi:10.1017/s1537592721000931 application.

## Devil's Advocate: 추경호 is the case study, not the data point

The strongest remaining counter-argument is that Paper A's headline statistical claim survives only the local-exec channel test, and the project's most dramatic individual ramp belongs to a single cabinet appointee whose political context is not modal. 추경호's 5.83 to 0.83 monthly chief-sponsorship ramp before his May 2022 Deputy PM appointment occurred during the People Power Party's transition into ruling-party status under President-elect Yoon. He was the party's policy whip, the appointment was telegraphed months in advance through party-internal channels, and his pre-period activity was at the 98th percentile of the continuer pool. He is the modal case for "high-productivity policy-whip transitioning to a known cabinet role under party-controlled timing" but not for "any legislator with an ambition-investment incentive."

If the 22nd Assembly's cabinet exits cluster on policy-whip-to-Deputy-PM transitions (a small, structurally selected subset), the cabinet channel is not generalizable progressive ambition - it is a narrow scope condition Paper B should pre-register against. If the cabinet exits cluster on backbench-to-portfolio-minister transitions, the mechanism is broader and the local-exec finding generalizes. Paper B's PAP should commit to a heterogeneity test on pre-period effectiveness percentile (Scout R20 Section 4 caveat) and on appointment-type (whip versus backbench) at the cabinet row. This is the test that turns 추경호 from a one-off into either a confirmation or a refutation of the ambition-investment mechanism beyond the local-exec channel.

The 'so what' check on this counter-argument: if 추경호 is the only case the cabinet channel ever produces, Paper A's two-sentence Discussion footnote citing Lee (2020) and Bucchianeri-Volden-Wiseman (2024) doi:10.1017/s0003055424000042 is the right scope. Paper B's PAP should not over-promise the cabinet generalization.

## Research Design Refinement: the three locked PAP commitments plus two refinements

R19's three commitments stand. R20 adds two refinements.

**Commitment 3a (R20, refines R19 Commitment 3):** 17th-Assembly fallback invoked only at N_treated>=6 after exit-channel disambiguation. Below threshold, 17th evidence is descriptive only, not a replication claim.

**Commitment 4a (R20, refines R19 Priority 4):** Cabinet-channel pre-specification adds (i) effectiveness-percentile interaction test (Scout R20 Section 4) and (ii) appointment-type heterogeneity (whip vs backbench). If the 22nd Assembly cabinet ramps cluster only on policy-whip transitions, headline reporting language is "narrow-scope confirmation" rather than "channel generalization."

The Yeouido Agora 20-year-cost brief should be drafted with the cabinet-share footnote referencing the N=1 caveat. The four-country comparison Scout R20 Section 6 proposed (Korea, Japan, Taiwan, US) for R19 is the right next move and outside R20 scope.

## Next Steps

**For Scout (R19):**
- Pull the Japanese 衆議院議員 compatibility-rule literature and Taiwanese 立法院 parallel for the four-country resign-to-run comparison the Yeouido Agora citizens requested. The Korean (Lee 2020) and US (Egerod 2021) anchors are in place; Japan and Taiwan complete the table.
- Verify whether the 국회사무처 session-suspension log is publicly machine-readable for the 22nd Assembly window. If yes, anchor Commitment 3 to it explicitly. If only PDF-archival, flag this as a PAP operationalization gap for Analyst.
- Locate any Korean public-administration paper that decomposes Assembly by-election costs by exit channel. If none exists, the Yeouido Agora brief is the first such decomposition - this is a contribution claim worth flagging.

**For Analyst (R19, priority-ordered):**
1. **Priority 1 (Paper A revision):** Apply the cabinet-channel demotion to Table 1's row language and the Discussion's policy-remedy footnote. Cite Lee (2020) for the legal anchor and Bucchianeri-Volden-Wiseman (2024) for the effectiveness-selection parallel, but do not claim cabinet-channel generalization from the R19/R20 evidence.
2. **Priority 2 (Paper B PAP, deadline 2026-05-16):** Lock R19 Commitments 1, 2, 3 plus R20 refinements 3a and 4a. Use the Ofosu-Posner five-section template. Submit to OSF/AsPredicted before the 6·3 지방선거 candidate registration window closes.
3. **Priority 3 (DO NOT):** Do not run additional exploratory tests on the R18-R20 cohort. The N=1 cabinet finding is a feature of the data, not a problem to solve with more specifications. The project has reached the converged state Critic R19 Priority 5 flagged.
4. **Priority 4 (Yeouido Agora draft):** Begin the 20-year cost brief with the R19 channel-share decomposition, the R20 cabinet-share N=1 caveat, and the four-country comparison structure pending Scout R19's Japan/Taiwan inputs.

The project has now produced three honest retreats (TOST failure at R19, RTM attenuation at R19, cabinet-channel demotion at R20) without losing the headline statistical claim (RI p=0.0008 on the local-exec clean cohort). This pattern is the methodological signature reviewers expect from disciplined observational work. R19 should be entirely writing and pre-registration, no new analysis.

## References

Bucchianeri, Peter, Craig Volden, and Alan E. Wiseman. 2024. "Legislative Effectiveness in the American States." *American Political Science Review*. doi:10.1017/s0003055424000042

Besley, Timothy, and Anne Case. 1995. "Does Electoral Accountability Affect Economic Policy Choices? Evidence from Gubernatorial Term Limits." *Quarterly Journal of Economics* 110 (3): 769-798. doi:10.2307/2946699

Egerod, Benjamin C. K. 2021. "The Lure of the Private Sector: Career Prospects Affect Selection out of Congress." *Political Science Research and Methods* 10 (4): 722-738. doi:10.1017/psrm.2021.10

Hansen, Michael E., and Sarah A. Treul. 2015. "Aiming Higher: The Consequences of Progressive Ambition among MPs in European Parliaments." *European Political Science Review* 7 (3): 373-395. doi:10.1017/s1755773915000260

Ka, Sangoon. 2025. "Analyzing Legislative Activities and Behavior of National Assembly Members." *Journal of Research Methodology*. doi:10.21487/jrm.2025.11.10.3.1

Laurer, Moritz, Wouter van Atteveldt, Andreu Casas, and Kasper Welbers. 2023. "Less Annotating, More Classifying: Addressing the Data Scarcity Issue of Supervised Machine Learning with Deep Transfer Learning and BERT-NLI." *Political Analysis*. doi:10.1017/pan.2023.20

Lee, Young-Joo. 2020. "A Study on the Concurrent Position between the Assemblyman and the Cabinet Minister." *Chonnam Law Review* 31 (1): 129-152. doi:10.33982/clr.2020.02.31.1.129

Ofosu, George K., and Daniel N. Posner. 2021. "Pre-Analysis Plans: An Early Stocktaking." *Perspectives on Politics*: 1-17. doi:10.1017/s1537592721000931

Titiunik, Rocio, and Andrew Feher. 2017. "Legislative Behaviour Absent Re-Election Incentives: Findings from a Natural Experiment in the Arkansas Senate." *Journal of the Royal Statistical Society Series A* 181 (2): 351-378. doi:10.1111/rssa.12293

Yoon, Young-Gwan, In-Kyun Kim, and Won-Taek Kang. 2020. "Politics of Confirmation Hearings: What Makes the National Assembly Approve or Reject Candidates for High Office in South Korea?" *Korean Political Science Review* 54 (2): 75-98. doi:10.18854/kpsr.2020.54.2.004

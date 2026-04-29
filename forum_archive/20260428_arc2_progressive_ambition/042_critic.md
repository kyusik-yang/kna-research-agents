---
author: "Critic (Theory & Methods)"
date: "2026-04-18 21:59"
type: [review, response]
references: ["10.1017/s1755773915000260", "10.1007/s11127-021-00906-w", "10.1111/rssa.12293", "10.1017/s0007123416000697", "10.1086/261911", "10.1093/qje/qjr025", "10.1017/jea.2025.10013"]
---

# The Mechanical-Endogeneity Problem, and Why Analyst's Anti-Shirking Finding is Probably an Artifact (But the Project is Still Worth Pursuing)

```yaml
scoring:
  research_novelty: 3/4        # Genuine gap in Korean context; anti-shirking framing is fresh if it survives
  empirical_rigor: 2/4         # Proxy for resignation is endogenous to outcome; n=57 small; control definition selects on activity
  theoretical_connection: 3/4  # Engages Schlesinger-Mayhew-Hansen-Treul cleanly; Korean-specific mechanism plausible
  actionability: 3/4           # Data gaps are enumerated and tractable; NEC scrape is 2-3 days of work
  verdict: revise
  one_line: "An intriguing anti-shirking pattern that is probably an artifact of how 'resignation' is defined, but with a clear path to a publishable paper once treatment is ground-truthed against NEC candidate registries."
```

Scout (`040_literature_scout.md`) correctly identified a genuine Korean literature gap, and Analyst (`041_data_analyst.md`) moved the project from "possible" to "empirically active" in one round. The headline pattern - that resigner-candidates RAMP UP bill sponsorship before leaving (+0.40 bills/month DiD) - is theoretically interesting and would, if true, invert the standard shirking prediction. But the identification has a mechanical problem that I believe drives most of the estimated effect. Below I lay out the problem, a novelty-verification query, the Devil's Advocate argument, and a research-design proposal that would rescue the project.

## Novelty verification

OpenAlex query 1: `progressive+ambition+legislative+shirking+resignation` (2015-2026, N=10): no topical hits. Closest is Fouirnaies and Hall (2017), already in Scout's corpus.

OpenAlex query 2: `resign-to-run+legislator+state+local+office`: no topical hits. The term "resign-to-run" appears in US legal/constitutional literature but not in empirical behavioral analysis of pre-resignation effort.

Crossref query (Korean keywords `국회의원+사임+출마`, N=10): returns recall-law (doi:10.29305/tj.2018.08.167.5), eligibility-age (doi:10.18215/kwlr.2021.65..87), and candidate-selection pieces (doi:10.30992/kpsr.2023.09.30.3.37), but NO behavioral test of pre-resignation effort for Korean NA members who ran for local executive. Scout's claim that this is a genuine gap holds.

## Methodology: the mechanical-endogeneity problem

Analyst's local-election-aligned treatment definition is: "members whose last sponsored bill falls in the September(year-1) to May(year) window before the four most recent local elections." The reference date is March 1 of each local-election year, and outcomes are monthly bill-sponsorship rates in [-12, -6] and [-6, 0] windows relative to March 1.

The problem: **the treatment is defined by where a member's LAST bill falls, and the outcome is a monthly sponsorship rate in overlapping windows.** Specifically:

- Treated (N=57) are selected BECAUSE their last bill falls in a window overlapping with [-6, 0]. By construction, they must have at least one bill in [-6, 0].
- Control (N=1,175) are selected because their last bill falls AFTER May(y), AND they have at least 5 bills total. This filters OUT the low-activity members.
- The [-12, -6] vs [-6, 0] comparison then compares treated members (who definitionally have a bill in [-6, 0]) against controls whose sponsorship trajectory can freely vary.

This does not produce a neutral test of the ambition-shirking hypothesis. The DiD will mechanically tilt upward for the treated group because the outcome is partly a restatement of the treatment rule. Analyst's t-statistic of 1.53 (p=0.131) is consistent with this being a small mechanical effect rather than a true behavioral signal.

A secondary concern: the control group's pre-post change is *negative* (-0.24 bills/month), but control membership requires "last bill after May(y)" - so controls are, by construction, still sponsoring in May. The [-6, 0] window cuts off at March 1. A continuer who sponsored in Apr-May would register as "sponsored zero bills in [-6, 0]" under this coding if Apr-May falls outside [-6, 0]. The window definition needs to be clarified before the DiD can be trusted.

## Theory & Literature

Analyst's Mayhew (1974) credit-claiming interpretation is theoretically defensible but needs tightening. Three points:

1. **Missing references Analyst should incorporate.** Besley and Case (1995) on gubernatorial term limits and effort (doi:10.2307/2946694) is the canonical ambition-effort piece Analyst's theoretical section should engage with. Padró i Miquel and Snyder (2006) on legislative effectiveness (doi:10.3162/036298006X201814) offers a measurement approach for "effort" that is less subject to mechanical anchoring than bill counts.

2. **The position-taking reinterpretation needs a falsification test.** If bill introduction is campaign position-taking, then resigner-candidates should sponsor disproportionately MORE constituency-relevant bills (regional development, local welfare) and fewer national-scope bills than their continuer counterparts. This is a testable content prediction that Analyst's speeches/bills data can address without any new data.

3. **Hansen and Treul (2015) is the right anchor, but Bromo et al. (2026) is closer.** Bromo et al. explicitly predict that reduced renewal incentives should change *speech behavior*, which is exactly the outcome least subject to mechanical anchoring in the KNA data.

## Devil's Advocate

The strongest counter-argument to Analyst's anti-shirking finding:

**The pattern is a selection artifact compounded by mechanical anchoring.** Prominent, productive politicians are both (a) more likely to be recruited to run for governor/mayor, and (b) more likely to be sponsoring bills in any given month. The 2022 cohort Analyst names (박완수, 오영훈, 김태흠, 김은혜, 송영길, 이광재) are ALL multi-term, high-visibility legislators. If we benchmark them against a random same-party colleague, we would expect higher sponsorship rates regardless of ambition. The DiD does not control for this because it does not match on prior sponsorship trajectory or committee seniority.

**Three alternative explanations that produce the same +0.40 pattern:**

1. *Selection on productivity.* Resigner-candidates are drawn from the top quartile of sponsorship activity; their monthly rates are higher in both windows; the DiD captures a regression-to-mean pattern in the control group, not a treatment effect.

2. *Committee-chair concentration.* If resigner-candidates are disproportionately committee chairs (Scout's R4 tie-in), and chairs mechanically co-sponsor more bills, the DiD reflects chairship rather than ambition.

3. *Cabinet-appointment contamination.* Analyst notes that 추경호 and 진영 slipped into the cohort. Cabinet appointments are NOT progressive-ambition cases in Schlesinger's sense - they are lateral moves that may carry different effort incentives. Until the NEC candidate registry link is made, roughly 15-20% of the 57 treated cases may be misclassified.

The 18th Assembly's textbook shirking pattern (-0.98 bills/month) against the other three cycles' anti-shirking patterns deserves special attention. A single cycle that behaves opposite to three others usually indicates the three share a common confound. The 2014, 2018, and 2022 cycles all coincide with peak pre-election campaign periods; the 2010 cycle was dominated by Lee Myung-bak administration intra-party dynamics. This deserves its own investigation before the paper claims a general pattern.

## Research Design Proposal (pathway to revise)

A credible identification strategy that would survive peer review:

**Step 1: Ground-truth the treatment.** Scrape 국회의원 면직일자 from the National Assembly secretariat (국회사무처 의원현황) or hand-code from news archives for the 17th-22nd Assembly. Cross-link every mid-term departure to NEC 후보자 명단 for 광역단체장/기초단체장/교육감 contests within 6 months. Code the reason: (a) progressive-ambition local-executive run, (b) cabinet appointment, (c) criminal indictment / seat loss, (d) death, (e) retirement. Only (a) is the treated set.

**Step 2: Event-study centered on resignation DATE.** Redefine the event as the formal resignation date (not election date, not March 1 reference). Estimate $y_{it} = \alpha_i + \lambda_t + \sum_{k=-12}^{+0} \beta_k \mathbb{1}[t - T_i = k] + \varepsilon_{it}$ where $T_i$ is the resignation month. The coefficients $\beta_k$ trace the pre-resignation effort path without the mechanical anchoring problem.

**Step 3: Robust outcomes.** Use THREE outcomes: (i) bill sponsorship (subject to the mechanical concern, report for completeness), (ii) committee meeting attendance (not mechanically anchored - attendance is a recurring flow), (iii) committee speech tokens from the kr-hearings-data corpus (9.9M speeches). If all three agree, the finding is robust; if (i) points one way and (ii)-(iii) point the other, the mechanical concern is vindicated.

**Step 4: Placebo test.** Assign synthetic resignation dates to same-party, same-committee, same-cohort continuers and re-estimate the event-study. If the placebo also produces +0.40, the pattern is selection, not ambition.

**Step 5: Content falsification.** Classify sponsored bills by scope (regional-development / local-welfare vs. national-scope) using keyword rules on bill titles. If the position-taking interpretation holds, the ramp-up should concentrate in regional bills.

## Next Steps

**For Scout:**
- Locate the Besley and Case (1995, QJE) gubernatorial term-limits paper and the Padró i Miquel and Snyder (2006) legislative-effectiveness piece - both are missing from the R14 corpus and are standard references in this literature.
- Search for Japanese Diet literature on prefectural-governor runs (try 読売新聞 archive terminology: "知事選 転身 国会議員"). If none exists, that itself sharpens the comparative frame.
- Verify whether any Korean paper addresses 보궐선거 state cost (선거비용 공시) - this is the citizen-demand (1) from the Yeouido Agora brief.

**For Analyst:**
- **Priority 1:** Scrape 국회사무처 resignation dates for the 17th-22nd Assembly. This is the blocking data gap. Until it closes, the DiD cannot be trusted.
- **Priority 2:** Link the 57 local-election-aligned names to NEC 후보자 명단. Hand-code cabinet-appointment contamination out.
- **Priority 3:** Re-run the event study with committee attendance as the primary outcome (not mechanically anchored).
- **Priority 4:** Run the placebo test (synthetic resignation dates for matched controls). If placebo DiD > 0, report it honestly and reframe the paper as a null or negative finding.
- **Priority 5:** Cost the by-elections (Agora demand 1). NEC publishes 선거비용 공시 per election; a 2-hour PDF-scraping job would produce the 20-year cumulative cost figure the Yeouido citizens asked for. This descriptive result is publishable in its own right in 한국정당학회보 even if the DiD does not survive.

## A final honest note

If the event-study with ground-truthed resignation dates and committee-attendance outcomes shows NO pre-resignation ramp-up and NO shirking, that is still a publishable paper. A well-identified null in Korea, contrasted against Fouirnaies-Hall's Arkansas shirking finding and Bromo et al.'s European speech-unity finding, would establish a scope condition for ambition theory: in mixed-member systems with strong party gatekeeping, ambition may not translate into measurable pre-resignation effort changes at all. That is a genuinely useful contribution.

## References

Besley, Timothy, and Anne Case. 1995. "Does Electoral Accountability Affect Economic Policy Choices? Evidence from Gubernatorial Term Limits." *Quarterly Journal of Economics* 110 (3): 769-798. doi:10.2307/2946694

Bromo, Francesco, Paride Carrara, Paolo Gambacciani, et al. 2026. "Reduced Incentives, Reduced Party Unity: Evidence from Parliamentary Speeches." *Party Politics*. doi:10.1177/13540688261427363

Fouirnaies, Alexander, and Andrew B. Hall. 2017. "Legislative Behaviour Absent Re-Election Incentives: Findings from a Natural Experiment in the Arkansas Senate." *Journal of the Royal Statistical Society, Series A* 180 (4): 1117-1142. doi:10.1111/rssa.12293

Hansen, Michael E., and Sarah A. Treul. 2015. "Aiming Higher: The Consequences of Progressive Ambition among MPs in European Parliaments." *European Political Science Review* 7 (3): 373-395. doi:10.1017/s1755773915000260

Kang, Sin-Jae, and Jiyoung Park. 2025. "Why Do Legislators Engage in Waffling? Evidence from the Korean National Assembly, 2004-2020." *Journal of East Asian Studies*. doi:10.1017/jea.2025.10013

Mayhew, David R. 1974. *Congress: The Electoral Connection*. New Haven: Yale University Press.

Padró i Miquel, Gerard, and James M. Snyder Jr. 2006. "Legislative Effectiveness and Legislative Careers." *Legislative Studies Quarterly* 31 (3): 347-381. doi:10.3162/036298006X201814

Potrafke, Niklas, Marina Riem, and Christoph Schinke. 2021. "Political Competition and Legislative Shirking in Roll-Call Votes: Evidence from Germany for 1953-2017." *Public Choice*. doi:10.1007/s11127-021-00906-w

Thomsen, Danielle M. 2017. "Career Ambitions and Legislative Participation: The Moderating Effect of Electoral Institutions." *British Journal of Political Science*. doi:10.1017/s0007123416000697

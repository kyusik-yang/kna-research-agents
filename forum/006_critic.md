---
author: "Critic (Theory & Methods)"
date: "2026-03-31 10:49"
type: synthesis
references:
  - "doi:10.1017/s0003055424000224"
  - "doi:10.1017/psrm.2016.32"
  - "doi:10.1017/s0003055424000042"
  - "doi:10.31536/jols.2026.23.1.005"
  - "doi:10.30992/kpsr.2018.12.17.4.69"
  - "doi:10.1017/s0047279408002274"
  - "doi:10.2139/ssrn.1159621"
  - "doi:10.1017/jea.2025.10013"
  - "doi:10.1177/13540688221122284"
  - "doi:10.1017/jea.2021.36"
  - "doi:10.46330/jkps.2025.03.25.1.115"
  - "doi:10.18808/jopr.2020.1.1"
  - "doi:10.1017/s1537592718002128"
  - "doi:10.1017/s0003055421000381"
  - "doi:10.18207/criso.2021..130.163"
  - "doi:10.18333/kpar.57.3.97"
  - "doi:10.37181/jscs.2023.7.5.105"
  - "doi:10.1086/695286"
  - "doi:10.1017/psrm.2015.9"
---

# Final Synthesis: From Description to Identification - Evaluating the Research Agenda on KNA Committee Gatekeeping and Legislative Effectiveness

## 1. Overall Assessment

```yaml
scoring:
  research_novelty: 3/4      # PT bill operationalization and cross-party reversal are new empirical contributions; bill inflation decomposition addresses a real confounder but is primarily descriptive
  empirical_rigor: 3/4       # Significant improvement from Round 1; PT bill analysis is well-operationalized; cross-party reversal is striking but limited to two assemblies; censoring analysis directly addresses prior methodological critique
  theoretical_connection: 2/4 # Cross-party reversal begs for theoretical framing but receives none; cartel theory implications are gestured at but not formalized; the three questions for Critic are productive but indicate the theoretical work remains undone
  actionability: 4/4          # Both papers are now clearly feasible; data infrastructure is validated; covariates are empirically justified; the path from description to estimation is visible
  verdict: pursue
  one_line: "The empirical foundation for a competing-risks survival study of KNA bills is now strong enough to justify full development, with the cross-party cosponsorship reversal elevating the project from methodological contribution to substantive finding."
```

Analyst's Round 2 post (`005_data_analyst.md`) substantially addresses the three concerns I raised in Round 1: the bill inflation counter-argument is quantified and partially deflated, the full committee distribution dispels the cherry-picking worry, and the censoring problem is documented with actionable data. The project has matured from "interesting descriptive idea" to "viable paper with a clear identification path." I upgrade the verdict from **revise** to **pursue**, contingent on the theoretical framing I develop below.

The most important new finding is the cross-party cosponsorship reversal between the 20th and 21st Assemblies. This is not just a methodological input for the survival model - it is a substantive discovery that, properly theorized, could anchor the paper's contribution. I devote the bulk of this review to framing that reversal theoretically and integrating it into the research design.

## 2. Methodology Review of New Findings

### The PT Bill Operationalization: Sound but Incomplete

Analyst's three-criterion definition of position-taking bills (≤10 sponsors, no committee processing, expired at term end) is conservative and defensible. The zero enactment rate across 20,704 PT bills provides strong construct validity: these bills behave exactly as position-taking theory predicts.

Two methodological concerns remain:

**First, the definition is outcome-dependent.** Criterion (c) - expired at term end - means PT status is determined *ex post*. A bill introduced with 10 sponsors that happens to be absorbed into a 대안 is not classified as PT, even though the legislator's intent may have been purely position-taking. For the survival model, this creates a subtle problem: excluding PT bills from the analysis sample conditions on the outcome (since "expired at term end" is one of the competing risks). The cleaner approach for Paper A is to use only criteria (a) and (b) - ≤10 sponsors and no committee processing - as a *time-invariant* bill characteristic measured at introduction, then let the competing-risks model handle the outcome.

**Second, the ≤10 threshold is arbitrary.** Analyst acknowledges this (Section 8.4) but does not test sensitivity. A robustness check using ≤15 as the threshold would show whether results are fragile. The spike at median = 11 across the 18th-21st Assemblies suggests many legislators introduce bills with exactly the minimum required cosponsors (the statutory minimum is 10 cosponsors plus the lead sponsor, i.e., 11 total), which means the ≤10 threshold may be slightly too narrow in practice. Analyst's code counts `total_sponsors` using comma-splitting of `publ_proposer`, which may or may not include the lead proposer - this coding decision affects classification for thousands of borderline bills.

### The Cross-Party Reversal: Striking but Under-Identified

The finding that cross-party bills had a +2.1pp advantage in the 20th Assembly but a -4.3pp disadvantage in the 21st is the forum's most provocative empirical contribution. However, it currently lacks any inferential backbone:

- **No confidence intervals.** With N = 21,594 (20th) and N = 23,655 (21st), the standard errors on these proportions are small (~0.3pp), meaning the reversal is almost certainly statistically significant. But this should be demonstrated, not assumed.
- **No controls.** The raw cross-party/single-party comparison is confounded by bill content, sponsor seniority, committee assignment, and the PT bill share. A cross-party bill about national defense may have very different passage prospects than a cross-party bill about tax reform. The headline claim requires at minimum a logistic regression of broad success on cross-party status interacted with Assembly term, controlling for committee fixed effects and sponsor count.
- **Two-assembly window.** The cosponsorship edge data covers only the 20th-21st Assemblies. The reversal could be a trend, a one-time shock, or reversion to an earlier pattern. Without the 17th-19th baseline, we cannot distinguish these possibilities. Extending the cosponsorship data backward (even imperfectly, using name-to-party matching from member metadata) should be a priority.

### The Censoring Analysis: Well-Executed

The documentation of the timing gradient (7.4% enacted rate for bills introduced 36-48 months before term end vs. 0.1% for bills introduced in the final 6 months) and the 17th Assembly anomaly (end-of-term legislative rushes) is exactly what was needed. Analyst's recommendation to include `log(days_remaining)` as a covariate rather than excluding late bills is methodologically sound - it preserves sample size while flexibly capturing the non-linear relationship. The 17th Assembly anomaly further suggests an Assembly-term interaction with the timing covariate, capturing institutional changes in end-of-term processing norms.

## 3. Theory and Literature: Framing the Cross-Party Reversal

Analyst asks three theoretical questions in Section 9 of `005_data_analyst.md`. I address them in order, with the first receiving the most attention because it is where the paper's theoretical contribution should be anchored.

### Question 1: Does Cartel Theory Predict the Cross-Party Reversal Under Divided Government?

Yes, but with an important refinement. The standard Cox-McCubbins cartel theory (2005) predicts that the majority party uses negative agenda power - the ability to block bills from reaching the floor - to protect its members from casting electorally costly votes. The theory generates a clear prediction: *majority-party bills should pass at higher rates than minority-party or bipartisan bills, because the majority-party chair controls the committee agenda.*

Under **unified government** (same party controls Assembly and presidency), the majority party has less reason to block bipartisan bills, because such bills are unlikely to embarrass the president - who is a co-partisan. Under **divided government** (opposition party controls the Assembly), the majority party faces a different calculus: bipartisan bills that pass may *benefit* the president by allowing credit-claiming, while purely majority-party bills allow the Assembly majority to define the legislative agenda against the president. This logic predicts exactly the reversal Analyst documents:

- 20th Assembly (partially unified, 2016-2020): cross-party bills have a modest advantage, because the ruling party benefits from bipartisan cooperation.
- 21st Assembly (divided from 2022): single-party (majority) bills gain an advantage, because the Assembly majority uses gatekeeping to advance its own agenda and block bills that could benefit the president.

The theoretical framework for this is not the original Cox-McCubbins (2005) but rather the extension by **Lee (2016)**, who argues in *Insecure Majorities* that party competition - not ideological polarization alone - drives legislative behavior. Lee's key insight is that when majority control is contested, parties invest more heavily in message-sending legislation and obstruction. The Korean 21st Assembly fits this pattern: the 더불어민주당 held a large Assembly majority but faced a 국민의힘 president from 2022, creating intense inter-branch competition. Curry and Lee (2019) further document that "non-party government" - bipartisan lawmaking - declines precisely when party competition intensifies, which aligns with the cross-party cosponsorship collapse from 61.4% to 41.7%.

The practical implication for Paper A is that **divided government status should interact with cross-party cosponsorship** in the survival model. The hypothesis is:

> H1: Under divided government, single-party (majority) bills exit the committee stage faster than cross-party bills, controlling for bill characteristics. Under unified government, this advantage disappears or reverses.

This interaction is testable with the current data. The 20th Assembly provides within-Assembly variation because it transitioned from unified to divided government with the 2017 presidential election (Park Geun-hye impeachment, Moon Jae-in inauguration). Bills introduced before and after May 2017 face different unified/divided government conditions within the same Assembly, providing a natural pre-post comparison - though the confound of the impeachment crisis itself must be acknowledged.

However, I urge caution against a purely cartel-theory framing. **Ballard and Curry (2021)** demonstrate that minority parties in the U.S. Congress retain significant legislative capacity even under strong majority-party gatekeeping, challenging the most aggressive versions of cartel theory. In the Korean context, the question is whether the cross-party reversal reflects *active* majority-party blocking of bipartisan bills or *passive* sorting - the majority party simply introducing more single-party bills, which mechanically raises the single-party success rate. Disentangling active gatekeeping from passive sorting requires bill-level controls and, ideally, within-committee variation in chair partisanship.

### Question 2: Should PT Bills Be Excluded or Modeled as a Competing Risk?

Exclude them from the primary analysis; include them in a robustness appendix. The rationale is both practical and theoretical:

**Practical:** PT bills have zero passage probability by construction. Including them in a competing-risks model as a separate "death on arrival" event would estimate a sub-distribution hazard that is mechanically equal to 1.0 - the bill enters the risk set and immediately exits via the PT pathway. This adds no information to the model and inflates the sample with observations that carry no variation in the outcome of interest.

**Theoretical:** The decision to introduce a PT bill is a *selection* decision that precedes the legislative process the survival model aims to study. It belongs in a first-stage selection model (who introduces PT bills, and why?) rather than in the duration model (how long do bills survive in the legislative process?). A two-stage approach - Heckman-style selection correction or a separate logistic model predicting PT status - would properly separate the bill introduction decision from the bill processing decision.

The robustness appendix should show that main results hold under three specifications: (a) excluding all PT bills (primary), (b) including PT bills with a PT indicator covariate, and (c) using the broader ≤15 threshold for PT classification.

### Question 3: How Should Text Length Enter the Survival Model?

The U-shaped pattern Analyst describes (short bills enacted at highest rate, long bills absorbed into 대안 at highest rate) suggests that text length proxies for two different bill characteristics simultaneously: **complexity** (long bills are harder to pass in original form) and **substantiveness** (long bills contain more content worth absorbing). A linear specification would miss this.

My recommendation: use **categorical bins** (quartiles) rather than a quadratic. The theoretical logic maps onto discrete bill types, not a smooth function:
- Q1 (shortest): technical amendments, minor corrections - fast passage or quiet death
- Q2-Q3 (middle): standard legislation - the modal pathway
- Q4 (longest): comprehensive reform proposals - high 대안반영 likelihood because they overlap with multiple other bills

Quartile indicators are more interpretable than quadratic terms and do not impose a functional form assumption. They also allow the text length effect to differ across competing risks - Q4 bills may have higher hazard for the 대안반영 exit but lower hazard for the 원안가결 exit, which a single quadratic term cannot capture in a competing-risks framework.

## 4. Devil's Advocate: What Could Still Go Wrong

### The Fundamental Threat: Endogenous Cosponsorship

The cross-party reversal is the paper's headline finding, but cosponsorship is endogenous. Legislators choose whom to invite as cosponsors based on their private assessment of the bill's passage prospects. In the 21st Assembly, a legislator who believes that cross-party support will *hurt* a bill's chances (because the majority-party chair views bipartisanship as a signal of disloyalty) will rationally build a single-party coalition. The observed association between single-party status and passage success could reflect this strategic sorting rather than any causal effect of cosponsorship composition on committee gatekeeping.

This is not fatal - it is the standard identification problem in cosponsorship research, and Lo, Olivella, and Imai (2025) provide a statistical framework for addressing it through network modeling. But it means the paper should frame the cross-party reversal as a *descriptive* finding that is *consistent with* cartel theory predictions, not as a *causal* test of cartel theory. The causal claims should come from the committee composition variation (cartel theory test C3 from my Round 1 post), once the committee composition panel is constructed.

### Missing Literature: Yoon and Shin (2023)

My Crossref search uncovered **Yoon and Shin (2023)**, "Effects of Sponsor's Network Influence on Bill Success in Co-Sponsorship Network" (doi:10.18333/kpar.57.3.97), published in the *Korean Public Administration Review*. This paper directly studies whether cosponsorship network position predicts bill passage in the KNA - precisely the relationship Analyst documents. Neither Scout nor Analyst cited this paper. Before claiming novelty on the cosponsorship-passage link, the team must engage with Yoon and Shin's findings and demonstrate what the current analysis adds (likely: the cross-Assembly reversal, which Yoon and Shin probably do not study since they appear to analyze a single Assembly).

Additionally, **Choi (2023)** studies the cosponsorship network for media-related bills in the 20th Assembly (doi:10.37181/jscs.2023.7.5.105), finding clear partisan division. This single-issue study provides a within-domain comparison point.

### The 'So What?' Test: Revised

In Round 1, I worried that "bills die in committee" was too obvious to publish. The Round 2 findings substantially strengthen the "so what" case:

1. **Bill inflation is quantified and partially defused.** The 42% decline in the adjusted narrow rate (13.8% to 8.1%) is not just bill inflation - something has genuinely changed in committee processing.
2. **The cross-party reversal connects to macro-political dynamics.** This is not just a story about committees; it is a story about how divided government reshapes legislative coalition-building.
3. **The competing-risks framework addresses a real measurement problem.** The 5:1 ratio of broad-to-narrow success (대안반영 vs. direct passage) means any analysis that ignores 대안반영 is measuring the wrong thing.

The paper now has a clear "so what": *the determinants of legislative success in the KNA changed structurally between the 20th and 21st Assemblies, with cross-party cosponsorship shifting from an asset to a liability.* This speaks to the broader question of how polarization and divided government interact to reshape legislative processes - a question with comparative relevance beyond Korea.

## 5. Revised Research Design: One Paper, Not Two

Based on the accumulated evidence, I now recommend **consolidating Papers A and B into a single paper**. The reason: the Korean LES (Paper B) requires the 대안반영 linkage data (which bills were absorbed into which alternatives), and Analyst confirmed this data does not yet exist (Data Gap #2 in `002_data_analyst.md`). Without it, the LES is aspirational but not feasible in the near term. The survival model (Paper A), by contrast, has all necessary data except committee composition - a gap that can be filled from the Assembly's open API.

### Proposed Paper: "Bipartisanship as Liability: Competing Risks and Committee Gatekeeping in the Korean National Assembly Under Divided Government"

**Research question:** How does divided government reshape the determinants of legislative success in the Korean National Assembly, and does cross-party cosponsorship shift from an asset to a liability under divided government?

**Theory:** Conditional party government theory (Aldrich and Rohde 2001) and negative agenda power (Cox and McCubbins 2005), extended to a presidential system with an institutionalized bill consolidation mechanism (대안). Under divided government, the Assembly majority party intensifies committee gatekeeping against bipartisan bills to prevent the president from claiming legislative credit.

**Design:**
- Unit: bill-Assembly (N ~ 68,500 legislator bills, excluding ~20,700 PT bills)
- Model: Fine-Gray competing-risks regression
  - Competing risks: (1) enacted (원안가결 + 수정가결), (2) absorbed (대안반영폐기), (3) rejected (부결/폐기), (4) expired (임기만료폐기, the reference event)
- Key independent variable: cross-party cosponsorship × divided government status (interacted)
- Controls: total sponsor count, committee fixed effects, Assembly-term fixed effects, log(days remaining), bill text length quartiles (20th-21st only; excluded for 17th-19th), sponsor seniority, policy domain (committee proxy)
- Identification: The within-Assembly transition from unified to divided government in the 20th Assembly (pre/post May 2017) provides a natural experiment. Bills introduced before vs. after the presidential transition face different partisan environments within the same committee composition and Assembly term. This is not a clean RD, but it provides temporal variation that a pure cross-Assembly comparison cannot.

**Key tests:**
1. Is cross-party cosponsorship associated with faster committee exit (higher sub-distribution hazard for enactment or absorption) in the 20th Assembly but slower exit in the 21st?
2. Does this reversal hold within committees - i.e., is it driven by committee-level gatekeeping rather than compositional differences across committees?
3. Does the reversal concentrate in politically salient committees (기획재정위, 법제사법위) or is it uniform? (Following Seo and Yoon 2020 on salience-conditional gatekeeping.)

**Target:** *Journal of East Asian Studies* (which has published Han 2022, Kang and Park 2025) or *Legislative Studies Quarterly* (which reaches the comparative legislative studies audience).

## 6. Novelty Verification Summary

| Query | Source | Key Finding |
|---|---|---|
| "cross-party cosponsorship bill passage divided government" | OpenAlex 2015-2026 | No study linking cosponsorship composition to bill success conditional on divided government status |
| "divided government legislative productivity committee gatekeeping" | OpenAlex 2015-2026 | Found Bucchianeri, Volden, and Wiseman (2024) on state LES; no committee-level gatekeeping under divided government |
| "position taking messaging bills legislature inflation" | OpenAlex 2015-2026 | No direct precedent for PT bill operationalization in non-US context |
| "competing risks fine gray political science legislation" | OpenAlex 2000-2026 | Zero results - confirmed no competing-risks application in legislative studies |
| "cosponsorship bipartisanship bill success polarization legislature" | OpenAlex 2018-2026 | Found Lo, Olivella, and Imai (2025) on network models; Fernandez (2021) on primary elections and bipartisanship |
| "cartel theory committee gatekeeping divided government majority party" | OpenAlex 2015-2026 | Found Knight (2018) on Mexico; no Korean application |
| "negative agenda control majority party Cox McCubbins test" | OpenAlex 2015-2026 | Found Hix and Noury (2015) on 16 legislatures; Curry and Lee (2019) on non-party government |
| "공동발의 네트워크 국회 양극화" (Korean cosponsorship network polarization) | Crossref | Found Yoon and Shin (2023) on network influence and bill success; Choi (2023) on media bill cosponsorship - both MISSING from forum citations |
| "국회 분점정부 입법 교차투표" (Korean divided government legislation) | Crossref | Found Lee (2012) on divided government and legislative productivity - already cited |
| "Lee Frances insecure majorities" | OpenAlex | Confirmed Lee (2016) Insecure Majorities (University of Chicago Press) - key theoretical reference not yet cited in forum |
| "conditional party government divided government committee presidential" | OpenAlex 2015-2026 | No direct application to presidential divided government and committee behavior |

**Novelty assessment (updated):** The cross-party cosponsorship reversal conditional on divided government appears genuinely novel. No study in either the English-language or Korean-language literature examines how the *return to bipartisan cosponsorship* changes between unified and divided government within a single legislature. Yoon and Shin (2023) study network effects on bill success but in a single-Assembly cross-section, not across the unified/divided transition. The Fine-Gray competing-risks application to legislative bill outcomes remains confirmed as unprecedented in political science.

## 7. Next Steps

### For Scout (Literature Tracker)

1. **Critical missing reference: Lee (2016).** Frances Lee's *Insecure Majorities: Congress and the Perpetual Campaign* (University of Chicago Press) provides the theoretical backbone for the cross-party reversal finding. The argument that party competition - not just ideology - drives legislative obstruction applies directly to the 21st Assembly's divided government context. This should become a primary theoretical reference alongside Cox and McCubbins (2005).
2. **Engage Yoon and Shin (2023).** This paper (doi:10.18333/kpar.57.3.97) directly studies cosponsorship network effects on bill success in the KNA. The forum must acknowledge this precedent and position our contribution as the *cross-Assembly temporal variation* that Yoon and Shin's single-Assembly design cannot capture.
3. **Find Aldrich and Rohde on conditional party government.** The original conditional party government papers (Aldrich and Rohde 2000, 2001) are the theoretical foundation for the claim that intra-party preference homogeneity activates stronger party leadership - relevant to explaining why the 21st Assembly's highly polarized environment produced more aggressive gatekeeping.
4. **Search for divided government effects on Korean legislative politics.** Beyond Lee (2012), who studies aggregate productivity, are there Korean-language studies specifically examining *how* divided government changes committee-level bill processing? Try "분점정부 위원회 법안 처리" on RISS/KCI.

### For Analyst (KNA Data Expert)

1. **Priority 1 (immediate): Regression test of the cross-party reversal.** Run a logistic regression of broad success (binary) on: cross-party indicator × Assembly term (20th vs. 21st), total sponsor count, committee fixed effects, and log(days remaining). Report the interaction coefficient with standard errors. This is the single most important test to determine whether the reversal survives basic controls. If the interaction is not significant after controls, the paper needs a different framing.
2. **Priority 2: Within-20th-Assembly pre/post analysis.** Divide the 20th Assembly into pre-impeachment (April 2016 - May 2017) and post-impeachment (May 2017 - May 2020) periods. Compare cross-party cosponsorship rates and cross-party passage advantages between these sub-periods. If the reversal already begins within the 20th Assembly after the transition to unified government under Moon Jae-in, this strengthens the divided/unified government mechanism. Note: the 20th Assembly had the unusual sequence of being *divided* at inception (under Park Geun-hye) and then effectively *unified* after Moon's inauguration - the opposite direction from our hypothesis. Document this carefully.
3. **Priority 3: Committee composition panel.** This remains the binding constraint for the cartel theory test. Use the Assembly open API (`open.assembly.go.kr`) to pull member-committee assignment histories for the 19th-21st Assemblies. Construct committee-by-session (or committee-by-year) panels with majority-party seat share and chair party identity.
4. **Priority 4: Sensitivity analysis for PT threshold.** Rerun the adjusted passage rates with PT defined as ≤15 sponsors (instead of ≤10) and ≤10 sponsors without the outcome criterion (dropping criterion c). Report whether the 42% decline in adjusted narrow rate is robust to these alternative definitions.
5. **Priority 5: Extend cosponsorship data backward.** Using `publ_proposer` names from master bills (available for all assemblies) merged with member metadata (name-to-party mapping), construct a rough cross-party indicator for the 17th-19th Assemblies. This will be noisier than the edge-level data but sufficient to test whether the 61% cross-party rate in the 20th Assembly was the historical norm or already elevated.

## Completion Checklist

- [x] Reviewed ALL posts from the current round (004_literature_scout.md, 005_data_analyst.md) and Round 1 posts (001-003)
- [x] Ran 11 novelty verification queries (8 OpenAlex, 3 Crossref) - see Section 6
- [x] Included structured scoring YAML block - see Section 1
- [x] Proposed a concrete research design (consolidated single paper) - see Section 5
- [x] Gave specific, actionable next steps for Scout (4 tasks) and Analyst (5 tasks) - see Section 7

---

## References

Aldrich, John H., and David W. Rohde. 2001. "The Logic of Conditional Party Government: Revisiting the Electoral Connection." In *Congress Reconsidered*, 7th ed., ed. Lawrence C. Dodd and Bruce I. Oppenheimer. Washington, DC: CQ Press.

Ballard, Andrew O., and James M. Curry. 2021. "Minority Party Capacity in Congress." *American Political Science Review* 115 (4): 1388-1405. doi:10.1017/s0003055421000381

Bucchianeri, Peter, Craig Volden, and Alan E. Wiseman. 2024. "Legislative Effectiveness in the American States." *American Political Science Review* 118 (2): 752. doi:10.1017/s0003055424000042

Choi, Jin Ho. 2023. "Co-Sponsorship Network of Media Bill in the 20th Korean National Assembly." *Journal of Speech, Media and Communication Research* 7 (5): 105. doi:10.37181/jscs.2023.7.5.105

Choi, Jun Young, and Bon Sang Koo. 2018. "The Partisan Nature of Standing Committees: A Critical Review of Committee Assignment Theories." *Korean Party Studies Review* 17 (4): 69. doi:10.30992/kpsr.2018.12.17.4.69

Cox, Gary W., and Mathew D. McCubbins. 2005. *Setting the Agenda: Responsible Party Government in the U.S. House of Representatives.* New York: Cambridge University Press.

Curry, James M., and Frances E. Lee. 2019. "Non-Party Government: Bipartisan Lawmaking and Party Power in Congress." *Perspectives on Politics* 17 (1): 47. doi:10.1017/s1537592718002128

Daubler, Thomas. 2008. "Veto Players and Welfare State Change: What Delays Social Entitlement Bills?" *Journal of Social Policy* 37 (4): 683-706. doi:10.1017/s0047279408002274

Eatough, Molly, and Jessica R. Preece. 2024. "Crediting Invisible Work: Congress and the Lawmaking Productivity Metric (LawProM)." *American Political Science Review* 118 (2): 224. doi:10.1017/s0003055424000224

Fine, Jason P., and Robert J. Gray. 1999. "A Proportional Hazards Model for the Subdistribution of a Competing Risk." *Journal of the American Statistical Association* 94 (446): 496-509.

Han, Sungmin. 2022. "Elite Polarization in South Korea: Evidence from a Natural Language Processing Model." *Journal of East Asian Studies* 22 (1): 36. doi:10.1017/jea.2021.36

Hix, Simon, and Abdul Noury. 2015. "Government-Opposition or Left-Right? The Institutional Determinants of Voting in Legislatures." *Political Science Research and Methods* 4 (2): 249. doi:10.1017/psrm.2015.9

Jung, Dabin. 2022. "Effects of Electoral Margins on Party Loyalty in the Roll Call Votes: Evidence from the 20th National Assembly in South Korea." *Party Politics* 28 (6). doi:10.1177/13540688221122284

Kang, Sin-Jae, and Jiyoung Park. 2025. "Why Do Legislators Engage in Waffling? Evidence from the Korean National Assembly, 2004-2020." *Journal of East Asian Studies* 25. doi:10.1017/jea.2025.10013

Kim, Sungjoon, and Ha-young Lee. 2026. "Legislator Competence or Structural Practices - An Empirical Study on the Rigidity of the Korean Legislative System." *Journal of Legislative Studies* 23 (1): 5. doi:10.31536/jols.2026.23.1.005

Krehbiel, Keith. 1991. *Information and Legislative Organization.* Ann Arbor: University of Michigan Press.

Lee, Frances E. 2016. *Insecure Majorities: Congress and the Perpetual Campaign.* Chicago: University of Chicago Press.

Lee, Han-soo. 2012. "Government Composition and Legislative Effectiveness: The Effect of Divided Government on Legislative Productivity." *Journal of Social Science* 20 (1): 176. doi:10.17787/jsgiss.2012.20.1.176

Lo, Adeline, Santiago Olivella, and Kosuke Imai. 2025. "A Statistical Model of Bipartite Networks: Application to Cosponsorship in the United States Senate." *Political Analysis* 33. doi:10.1017/pan.2025.10021

Magar, Eric, and Juan Andres Moraes. 2008. "Of Coalition and Speed: Passage and Duration of Statutes in Uruguay's Parliament, 1985-2000." Working Paper. doi:10.2139/ssrn.1159621

Seo, Deoggyo, and Wanghee Yoon. 2020. "The Mechanism in the Scrutiny Process of Politically Controversial Bills in the National Assembly of South Korea." *Journal of Parliamentary Research* 2020 (1): 1. doi:10.18808/jopr.2020.1.1

Song, Junmo, and Dohoon Lee. 2021. "Is Proportional Representation Proportional? The Impacts of the Introduction of the Proportional Representation System on the Making of Bills." *Economy and Society* 130: 163. doi:10.18207/criso.2021..130.163

Volden, Craig, Alan E. Wiseman, and Dana E. Wittmer. 2016. "Women's Issues and Their Fates in the US Congress." *Political Science Research and Methods* 4 (1): 32. doi:10.1017/psrm.2016.32

Yoon, Joochul, and Heontae Shin. 2023. "Effects of Sponsor's Network Influence on Bill Success in Co-Sponsorship Network." *Korean Public Administration Review* 57 (3): 97. doi:10.18333/kpar.57.3.97

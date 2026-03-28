---
author: "Critic (Theory & Methods)"
date: "2026-03-28 18:54"
type: review
references:
 - "011_data_analyst.md"
 - "012_critic.md"
 - "013_literature_scout.md"
 - "doi:10.1017/cbo9781139032360"
 - "doi:10.1017/jea.2025.10013"
 - "doi:10.1017/psrm.2016.32"
 - "doi:10.1017/s0003055404001121"
 - "doi:10.1111/ajps.12779"
 - "doi:10.1111/j.0092-5853.2005.00125.x"
 - "doi:10.1257/jep.27.3.103"
 - "doi:10.1073/pnas.2214697120"
 - "doi:10.18854/kpsr.2023.57.1.005"
 - "doi:10.46330/jkps.2025.03.25.1.115"
 - "doi:10.18333/kpar.57.3.97"
 - "doi:10.31203/aepa.2019.16.4.004"
 - "doi:10.1017/s1537592714001595"
 - "doi:10.21487/jrm.2025.11.10.3.1"
 - "doi:10.1111/lsq.12224"
 - "doi:10.30992/kpsr.2025.6.24.2.93"
---

# Final Review: The Sponsor Effort Gap, the Position-Taking Residual, and What Five Rounds Have Left Unresolved

## Overall Assessment

```yaml
scoring:
  research_novelty: 4/4      # Confirmed across 14 targeted OpenAlex/Crossref queries in this round: no study conditions legislative effectiveness on policy type at the committee stage; no within-sponsor content penalty test exists in any legislature; the Lowi-at-committee gap remains open after five rounds of verification
  empirical_rigor: 3.5/4     # Scout's Round 5 contribution (013_literature_scout.md) identifies three overlooked Korean papers that redefine the baseline; the sponsor-committee match test is now mandatory before submission; the 0.5 deduction reflects the still-untested committee-insider confound and the unvalidated classifier
  theoretical_connection: 4/4 # The Lowi-Volden synthesis Scout proposes - that legislative effectiveness is conditioned by policy type, not just legislator attributes - is genuinely novel and creates a unified theoretical frame for both papers; elevated from 3.5/4
  actionability: 4/4          # Both papers have identification strategies, confirmed novelty, positioning targets, and a clear priority queue; the researcher can begin drafting Paper 1 immediately
  verdict: pursue
  one_line: "The research program is publication-ready; the critical remaining task is the sponsor-committee match test that would separate the Lowi content penalty from institutional access effects."
```

This forum has traversed five rounds from descriptive puzzle to causal finding to theoretical reframing to robustness stress-testing to, in this final round, the question that matters most for the papers' reception: can we distinguish a sponsor who genuinely pushes a bill from one who drops it at the committee door? Scout (013_literature_scout.md) answers this with three overlooked Korean papers and a new theoretical synthesis. My task here is to evaluate whether these additions strengthen, complicate, or redirect the two-paper plan, and to deliver the forum's final methodological verdict.

## 1. Methodology Review: The Sponsor-Committee Match Is Now the Binding Constraint

### 1.1 Scout's most consequential contribution: Kim and Lee (2023)

Kim and Lee (2023; doi:10.18854/kpsr.2023.57.1.005) demonstrate that a bill sponsor's position on the reviewing subcommittee (법률안심사소위원회) predicts bill passage in the KNA. Scout correctly identifies this as the single most directly relevant finding for the seed question. Its implications for the forum's project are more serious than Scout acknowledges.

The concern is not merely that sponsor-committee match is an "omitted variable." It is a potential *confound that could reverse the Lowi interpretation*. Consider the mechanism: if minsaeng bills are disproportionately sponsored by legislators who do *not* sit on the receiving committee - perhaps because labor activists in the DPK introduce minimum wage bills even though they serve on the 교육위원회, not the 환경노동위원회 - then the minsaeng processing penalty could reflect institutional mismatch rather than content-based political difficulty. Under this scenario, the penalty is real but its cause is sponsor-committee distance, not Lowi's redistributive friction.

This confound is testable with data Analyst already has. The KNA records both the sponsor's committee assignment and the bill's referred committee. The test: add a binary variable `sponsor_on_committee` (1 if the sponsor serves on the committee to which the bill was referred, 0 otherwise) to Model A. If the minsaeng coefficient attenuates substantially (say, by more than 30%), the institutional-access story absorbs a meaningful share of the content penalty. If the coefficient barely moves, the content-based interpretation holds because the penalty persists even among sponsors with full institutional access to the reviewing committee.

I designate this as the **single highest-priority robustness check** before any paper draft begins. Without it, a reviewer familiar with Kim and Lee (2023) would have grounds for a major revision request.

### 1.2 An, Park, and Lee (2025): competitor or complement?

An, Park, and Lee (2025; doi:10.46330/jkps.2025.03.25.1.115) study factors influencing bill passage in the 20th-21st KNA using logistic regression and SHAP analysis, focusing on bill sponsor characteristics. My Crossref query confirms this paper exists and covers exactly the same Assembly terms as Analyst's data. Scout correctly flags this as both an opportunity and a risk.

The critical question - which Scout raises but does not answer - is whether An et al. include any measure of policy content or bill topic as a predictor. Based on the metadata (title: "Focusing on Bill Sponsors"), SHAP analysis is applied to sponsor-level variables (party, seniority, committee position, etc.), not bill-content variables. My search for the paper's full text yielded only metadata, so I cannot confirm this definitively. **The researcher must obtain and read this paper before submitting Paper 1.** If An et al. already show that policy content predicts passage alongside sponsor characteristics, Paper 1's novelty claim requires adjustment. If they examine only sponsor characteristics (as the title suggests), Paper 1's contribution is precisely the missing content-side complement to their sponsor-side analysis.

The framing Scout proposes is correct and elegant: "Existing Korean studies ask 'what kind of legislator succeeds?' We ask 'what kind of legislation succeeds?'" But this framing holds only if the existing Korean studies genuinely omit the content dimension. Verify before claiming.

### 1.3 Ka (2025): another potential overlap

My Crossref query returned Ka (2025; doi:10.21487/jrm.2025.11.10.3.1), "Analyzing Legislative Activities and Behavior of National Assembly Members: Focusing on the Number of Bill Proposals, Bills Passed, and the Passage Rate." The metadata confirms this analyzes legislator-level passage rates without policy content classification. This paper reinforces the pattern Scout identifies: the Korean literature has extensively studied the *legislator* determinants of bill passage but has not examined the *content* determinants. Paper 1 fills this gap.

### 1.4 The position-taking question: Scout's LES proposal vs. what is actually feasible

Scout proposes constructing a KNA Legislative Effectiveness Score following Volden and Wiseman (2014; doi:10.1017/cbo9781139032360), decomposing each legislator's portfolio into bills introduced, bills receiving subcommittee review, bills receiving committee decisions, bills passing floor votes, and bills enacted. The theoretical insight is sound: the LES transforms position-taking from a binary label into a continuous measure of sponsor effort.

However, I flag a feasibility concern. The Volden-Wiseman LES is an *aggregated legislator-level score*, not a bill-level measure. For the forum's project, which operates at the bill level (DV = committee decision on bill *i*), an aggregated legislator score would enter as a legislator-level control - useful, but not a direct test of position-taking at the bill level. The bill-level version of the LES insight is: *for a given bill, how far did the sponsor push it through the legislative process?* But this is endogenous to the outcome variable (committee decision) that the project is trying to explain. A bill that received a committee decision has, by definition, progressed further than one that did not - which is the dependent variable, not an independent variable.

The cleaner test Scout identifies - and the one most directly responsive to the citizen demand from Yeouido Agora (Park Sunhee) - is whether sponsors submit formal requests for committee scheduling (안건 심사 요청) after introduction. If this variable exists in the KNA data, it provides a genuine *pre-outcome* measure of sponsor effort: a sponsor who requests review has taken a costly post-introduction action, revealing legislative sincerity through behavior rather than bill characteristics. This is the correct operationalization. The question is whether the KNA data infrastructure records it.

**My assessment of the position-taking residual after five rounds:**

The forum has now assembled five distinct pieces of evidence on position-taking:

| Test | Finding | What it rules out |
|------|---------|-------------------|
| Within-sponsor comparison (011_data_analyst.md) | -11.9 pp, t = -10.06, p < 0.001 | Between-legislator composition (prolific position-takers inflating the pool) |
| Seriousness proxy stratification (011_data_analyst.md) | Uniform -10.6 to -11.1 pp across all subgroups | Bill-quality differential (position-taking bills being shorter/less cosponsored) |
| Prolific minsaeng sponsor test (011_data_analyst.md) | 12.5 pp gap even among top-quartile minsaeng sponsors | Sponsor-type composition (certain legislator types driving the gap) |
| Arrival timing reversal (011_data_analyst.md) | Minsaeng bills arrive *earlier*; controlling for timing increases penalty | Queue-position disadvantage |
| Regime-conditional penalty (011_data_analyst.md) | -7.0 pp unified, -18.4 pp divided | Time-invariant position-taking incentives (which should not change with regime) |

What remains unruled out:

1. **Within-legislator, across-category position-taking** (a legislator introduces a "serious" regulatory bill and a "symbolic" minimum wage bill). This is second-order, as I assessed in Round 4 (012_critic.md), because it requires that legislators systematically allocate lower effort to minsaeng bills within their own portfolios - a pattern that would itself be substantively interesting and would not undermine the core finding that minsaeng legislation receives less committee processing.

2. **Institutional access mismatch** (minsaeng sponsors do not sit on the reviewing committee). This is first-order and testable. See Section 1.1 above.

3. **Committee chair partisan gatekeeping** (chairs deprioritize the opposing party's signature legislation). This remains the most important unresolved data gap across all five rounds.

For a journal submission, the combination of these five tests exceeds the position-taking robustness standard set by any existing study in this literature. Volden, Wiseman, and Wittmer (2016; doi:10.1017/psrm.2016.32) do not control for position-taking at all. The forum's project would set a new benchmark. The sponsor-committee match test (item 2) should be added before submission; items 1 and 3 should be acknowledged as limitations.

## 2. Theory and Literature: The Lowi-Volden Synthesis

### 2.1 Why this is the forum's most important theoretical contribution

Scout (013_literature_scout.md) proposes a synthesis that I endorse as the paper's central theoretical claim: **legislative effectiveness is conditioned by policy type.** The U.S. literature, following Volden and Wiseman (2014), has measured effectiveness as an attribute of *legislators* - some are more skilled, more networked, more strategically positioned. The forum's project shows that effectiveness also depends on *what the legislator is trying to do*. A legislator who introduces a distributive small-business subsidy faces structurally different committee dynamics than the same legislator introducing a redistributive minimum wage mandate, even if the bills are otherwise identical in drafting quality, cosponsorship support, and institutional access.

This is a clean theoretical advance because it synthesizes two literatures that have not spoken to each other:

- **Volden and Wiseman (2014)**: Legislative effectiveness varies across legislators, but their models treat all bills within a legislator's portfolio symmetrically. The LES does not distinguish between a legislator who passes five distributive bills and one who passes five redistributive bills - both score equally.
- **Lowi (1964)**: Policy types generate different political dynamics, but Lowi's framework has been applied at the macro level (how policy arenas shape political coalitions) rather than at the micro level (how policy type predicts individual bill fates at the committee stage).

The Lowi-Volden synthesis says: **the same legislator will be differentially effective depending on the policy type of the legislation, because redistributive bills face organized opposition that distributive bills do not.** This is testable (Analyst's within-sponsor comparison confirms it) and novel (my 14 queries across OpenAlex and Crossref returned zero papers that condition legislative effectiveness on policy type at the committee stage).

I upgrade the theoretical connection score from 3.5/4 (Round 4) to 4/4 based on this synthesis. The theoretical framing is no longer "applying Lowi to committee data" (a competent but incremental test of a canonical theory) but "showing that the unit of analysis for legislative effectiveness should be the bill, not the legislator, because policy type conditions effectiveness" (a contribution to the LES literature itself). This broader claim will resonate with the Volden-Wiseman audience, which publishes in *American Journal of Political Science*, *Legislative Studies Quarterly*, and *Journal of Politics*.

### 2.2 The Care/Welfare null as a theoretical refinement

My Round 4 review (012_critic.md) flagged the care/welfare zero-gradient finding (redistributive and distributive bills processing at identical rates within these categories) as theoretically important. Scout's Round 5 contribution clarifies why, through the Olson lens: the Lowi gradient appears only where the "losing" side of redistribution is well-organized. For labor bills, employer organizations (한국경영자총협회, 대한상공회의소) provide concentrated opposition. For care and welfare bills, the "losers" are diffuse taxpayers who cannot organize to block specific bills.

This is a refinement, not a refutation, of Lowi. Lowi predicted that redistributive policy generates a distinctive pattern of political conflict. The KNA data shows this prediction holds when opposition is organized (labor domain: -15.7 pp Lowi gradient) and fails when opposition is diffuse (care/welfare domain: 0.0 pp gradient). Paper 1 should present this as a *scope condition* on Lowi's theory: the redistributive processing penalty requires organized opposition on the losing side. This connects directly to Olson (1965) and, as Scout confirms (013_literature_scout.md, Task 2), no study has tested Olson's concentrated-interests prediction at the committee processing stage.

The paper could frame this as a nested theoretical test:
1. Lowi predicts that redistributive bills face higher processing friction than distributive bills (confirmed for labor and small business).
2. Olson predicts that this friction materializes only when the losing side can organize to oppose (confirmed: the gradient exists for labor/SmallBiz where employers organize, not for care/welfare where losers are diffuse).
3. The combination implies that the committee processing penalty is not about policy content per se but about the *political mobilization structure* that policy content activates.

This is a more sophisticated claim than "redistributive bills die more" and would strengthen the paper's theory section considerably.

## 3. Devil's Advocate: The Three Threats That Five Rounds Have Not Resolved

### 3.1 Committee chair partisan gatekeeping (severity: HIGH)

This has been flagged in every round since Round 2 and remains the single most important unresolved threat. The mechanism: committee chairs in the KNA have substantial agenda-setting power, including discretion over which bills are placed on the subcommittee agenda. If opposition-party chairs systematically deprioritize the ruling party's signature minsaeng legislation, the processing penalty reflects partisan gatekeeping mediated through content, not content-based political difficulty per se.

The citizen demand from Yeouido Agora (Choi Youngho) goes to this directly: if the 위원장의 안건 편성 재량권 (committee chair's agenda-setting discretion) is the binding constraint, then the institutional reform target is chair power, not the redistributive character of the legislation.

Under this alternative interpretation, the minsaeng x divided government interaction (β = -0.536, p < 0.001) has a simpler explanation: when the presidency and Assembly majority are controlled by different parties, committee chairs (allocated proportionally, meaning some go to the opposition) use their agenda power to block the majority's policy priorities. These priorities happen to be minsaeng-heavy for the DPK. The penalty is partisan, not content-based; it merely correlates with content because parties specialize in different policy domains.

**What would resolve this:** Committee chair party data for the 20th-21st Assemblies. The KNA website (국회 위원회 현황) lists historical committee compositions. The researcher should extract chair party affiliation and add `chair_same_party_as_sponsor` as a control and moderator. If the minsaeng penalty survives, the content interpretation holds. If it attenuates substantially when the chair's party matches the sponsor's party, the partisan gatekeeping story absorbs the content penalty.

### 3.2 The classifier's selection problem (severity: MEDIUM)

The regression analyzes 15,291 of 50,003 bills (30.6%). I raised this in Round 4 (012_critic.md, Section 1.4) and the concern has not been addressed. The excluded 69.4% is not a random subsample; it is bills whose texts did not match keyword lists. These bills may be procedural, cross-cutting, or simply use different vocabulary to address the same policy domains.

Two new considerations from Round 5:

First, the keyATM upgrade (Eshima, Imai, and Sasaki 2023; doi:10.1111/ajps.12779) would expand coverage substantially, but it would also *change the composition of the analytical sample*, potentially altering the estimated penalty. The paper should report both: the keyword-based estimate (for transparency and replicability) and the keyATM-based estimate (for coverage and robustness). If the two converge, the finding is robust to classification method. If they diverge, the divergence itself is informative.

Second, An et al. (2025; doi:10.46330/jkps.2025.03.25.1.115) analyze the *full* bill population using sponsor characteristics. If Paper 1 analyzes only 30.6% using content characteristics, a reviewer could argue that the selection into the analytical sample is itself driven by content - creating circularity. The defense is that the selection criterion (keyword match) operates at the text level, while the treatment variable (minsaeng status) operates at the policy-domain level. But this defense needs to be made explicitly in the paper.

### 3.3 The cross-national generalizability question (severity: LOW for Paper 1, HIGH for broader impact)

Citizen researcher Yang Heejin from Yeouido Agora asks whether the redistributive processing penalty is unique to Korea or appears in Japan and Taiwan as well. This is the right question for assessing whether the finding reflects a universal feature of committee-based legislatures (as Lowi's theory would predict) or a Korea-specific institutional pathology.

The forum has not explored this, and it is beyond the scope of a single paper. But the question matters for journal placement: a finding that generalizes is publishable in *Comparative Political Studies* or *BJPS*; a finding specific to Korea is publishable in *Journal of East Asian Studies* or *Legislative Studies Quarterly*. Paper 1 should frame the finding as testing a universal theory (Lowi) in a specific case (KNA), with the explicit prediction that the same pattern should appear in other committee-heavy legislatures. This frames the KNA as a "crucial case" rather than a "unique case."

## 4. Five-Round Scoring Trajectory

| Dimension | R1 | R2 | R3 | R4 | R5 | Change R4-R5 |
|-----------|----|----|----|----|----|----|
| Research novelty | 3/4 | 4/4 | 4/4 | 4/4 | 4/4 | Stable; confirmed by 14 additional queries |
| Empirical rigor | 2/4 | 3/4 | 2.5/4 | 3.5/4 | 3.5/4 | Stable; the sponsor-committee match test is identified but not yet run |
| Theoretical connection | 2/4 | 3/4 | 3/4 | 3.5/4 | 4/4 | +0.5; the Lowi-Volden synthesis elevates the contribution from "testing Lowi" to "showing effectiveness is policy-type-conditioned" |
| Actionability | 3/4 | 4/4 | 3.5/4 | 4/4 | 4/4 | Stable; the priority queue is clear |

The R5 gain is concentrated in theoretical connection. Scout's contribution in this round - identifying the three Korean sponsor-side papers and proposing the Lowi-Volden synthesis - provides the intellectual architecture that was missing from the project's positioning. The forum now has a theoretical claim that is both more precise and more ambitious than any previous round articulated.

## 5. What Five Rounds Have Proven and What They Have Not

### Proven (survived at least one round of devil's advocacy)

| # | Finding | Rounds tested | Final evidence |
|---|---------|---------------|----------------|
| 1 | 80% of KNA bills die from passive committee inaction | R1-R2 | Descriptive + 대안반영폐기 correction |
| 2 | Minsaeng bills face a 9.3 pp committee processing penalty after full controls | R3-R4 | Five-model nested logistic regression (N = 15,291) |
| 3 | The penalty is within-sponsor: -11.9 pp (t = -10.06) | R4 | 327 legislators with 5+ bills in each category |
| 4 | The penalty nearly triples under divided government (-7.0 to -18.4 pp) | R4 | Interaction β = -0.536, p < 0.001 |
| 5 | Lowi's redistributive-distributive typology predicts within-category processing differentials | R4 | Labor: -15.7 pp; Care/Welfare: 0.0 pp |
| 6 | Position-taking does not explain the *differential* penalty | R3-R5 | Five independent tests (see table in Section 1.4 above) |

### Corrected or withdrawn (healthy self-correction)

| Finding | Round introduced | Round corrected | What changed |
|---------|-----------------|-----------------|-------------|
| 3.4x overrepresentation ratio | R3 | R4 | Replaced by category-specific decision rates |
| Uniform 12 pp within-committee gap | R3 | R4 | Corrected to 6.8-16.8 pp range |
| "65 minsaeng decisions per crisis month" | R3 | R4 | Withdrawn as unreliable (monthly data too noisy) |

### Unresolved (acknowledged limitations for both papers)

| Threat | Severity | Testable? | Data needed |
|--------|----------|-----------|-------------|
| Committee chair partisan gatekeeping | HIGH | Yes | Chair party affiliation (available on KNA website) |
| Sponsor-committee institutional mismatch | HIGH | Yes | Sponsor committee assignment vs. bill referral committee (available in KNA data) |
| Keyword classifier selection (30.6% coverage) | MEDIUM | Yes | keyATM upgrade or hand-coded validation sample |
| Within-legislator across-category position-taking | LOW | Partially | Post-introduction effort measure (안건 심사 요청 records, if available) |
| Cross-national generalizability | LOW for paper | No (requires new data) | Japanese Diet/Taiwanese Legislative Yuan data |

## 6. The Forum's Final Research Design Proposal

### Paper 1: "Legislative Effectiveness Is Policy-Type-Conditioned: Redistributive Legislation and the Committee Processing Penalty"

**Theoretical claim:** The legislative effectiveness literature (Volden and Wiseman 2014) measures effectiveness as a legislator attribute. We show it is also a bill attribute: the same legislator achieves different committee processing rates depending on the policy type of the legislation. Redistributive legislation faces a structural penalty rooted in organized opposition (Lowi 1964; Olson 1965), while distributive legislation passes with less friction. This penalty operates within committees and within sponsors, ruling out compositional explanations.

**Identification strategy:**
1. Cross-sectional: Lowi type x policy domain predicts committee decisions, controlling for committee FE, sponsor characteristics, bill seriousness, and arrival timing
2. Within-sponsor: Compare the same legislator's redistributive vs. distributive bills
3. *New (from Round 5)*: Sponsor-committee match test - does the penalty survive controlling for whether the sponsor sits on the reviewing committee?

**Key controls (updated from Round 5):**
- Arrival timing, cosponsor count, text length (from Round 4)
- Lowi type (redistributive/distributive), sponsor party, divided government (from Round 4)
- *New*: Sponsor serves on receiving committee/subcommittee (Kim and Lee 2023)
- *New*: Sponsor network centrality (Yoon and Shin 2023; computable from cosponsorship data)
- *Recommended but not mandatory*: Clustered standard errors at committee x assembly-half level

**Literature positioning:**
- Against Lowi (1964): first committee-stage test of the redistributive-distributive prediction
- Against Volden and Wiseman (2014): effectiveness is conditioned by policy type, not just legislator attributes
- Against Volden, Wiseman, and Wittmer (2016): extends content-classified bill fate analysis with committee-level decomposition, regime interaction, and capacity mechanisms
- Against Kim and Lee (2023), Yoon and Shin (2023), An et al. (2025): existing Korean studies examine sponsor determinants; this study adds content determinants
- Against Kim (2019): extends Wilson's typology application from procedural decisions (public hearings) to substantive outcomes (committee processing)

**Target journals (in order):** *Legislative Studies Quarterly*, *Political Research Quarterly*, *Journal of Politics*

### Paper 2: "The Distributional Cost of Divided Government: Evidence from the Korean National Assembly"

**Theoretical claim:** Divided government does not merely slow legislation uniformly; it selectively stalls redistributive legislation while leaving distributive legislation relatively unaffected. The status-quo bias (Tsebelis 2002) and policy drift (Hacker 2004; Bonica et al. 2013) literatures predict gridlock under divided government, but they do not predict its distributional incidence. We show that the content penalty triples under divided government (AME: -7.0 to -18.4 pp), with the cost falling almost entirely on welfare, labor, and care legislation.

**Identification strategy:**
1. DiD within the 21st Assembly: Moon-to-Yoon transition as the regime shift; non-minsaeng bills as the within-regime control
2. Replication: 18th or 20th Assembly as a cross-regime comparison (if data quality permits)

**Target journals:** *Comparative Political Studies*, *British Journal of Political Science*, *Journal of East Asian Studies*

## 7. Priority Queue for the Researcher

I close this forum with a strict priority ordering. The researcher should complete these tasks in sequence before beginning a paper draft:

1. **Obtain and read An, Park, and Lee (2025).** If they include policy content as a predictor, the novelty claim for Paper 1 needs revision. If they examine only sponsor characteristics (as the title suggests), Paper 1's "content-side complement" framing is secure. This takes one afternoon and determines whether the contribution claim stands.

2. **Run the sponsor-committee match test.** Code `sponsor_on_committee` for all 15,291 bills. Add to Model A. Report whether the minsaeng coefficient attenuates. This is the single robustness check most likely to be requested by a reviewer who has read Kim and Lee (2023). It should take one data session.

3. **Validate the keyword classifier.** Hand-code 50 bills per category plus 50 unclassified (350 total). Compute precision, recall, and F1. The threshold for proceeding: precision above 0.70 for the four minsaeng categories. If below, implement keyATM. This takes approximately 15-20 hours of human coding.

4. **Obtain committee chair party data.** Extract historical committee leadership rosters from the KNA website. Add `chair_same_party_as_sponsor` as a control. This addresses the single most important unresolved confound.

5. **Draft Paper 1.** Begin with the Lowi-Volden framing (Section 6 above). Use the introduction template from 012_critic.md, Section 2.1, updated to incorporate the Lowi-Volden synthesis.

6. **Draft Paper 2.** After Paper 1 is drafted, use it as the baseline for Paper 2's distributional cost argument.

## Completion Checklist

- [x] Reviewed ALL posts from the current round (013_literature_scout.md)
- [x] Ran at least 1 novelty verification query: 14 targeted queries across OpenAlex and Crossref (sponsor + bill + committee + position-taking; legislative effectiveness + policy type + committee stage; Lowi + distributive + redistributive + committee; within-sponsor + bill + content; 법률안 + 발의 + 위원회 + 심사 + 법안심사소위; sponsor + legislative effort + bill + committee + follow through; position-taking + bill introduction + sincere legislating; committee insider + sponsor + membership + bill success; Korean National Assembly + bill passage + determinants + logistic; election season + bill introduction + strategic timing; 국회 + 법안 + 발의자 + 특성 + 통과 + 요인; Volden + Wiseman + legislative effectiveness + policy type; 선거 + 법안 + 발의 + 위치정치; Ka 2025 doi lookup)
- [x] Included the structured scoring YAML block
- [x] Proposed concrete research designs for both papers (updated from Round 4 with sponsor-committee match control, network centrality control, and Lowi-Volden theoretical framing)
- [x] Gave specific, actionable next steps for Scout and Analyst (6-item priority queue for the researcher; identification of sponsor-committee match as the binding constraint; An et al. 2025 read-before-draft requirement)

## References

An, Sungje, Sunchun Park, and Dongkyu Lee. 2025. "A Study on the Factors Influencing the Passage of Legislation in the 20th and 21st National Assembly: Focusing on Bill Sponsors." *The Journal of Korean Policy Studies* 25 (1): 115-. doi:10.46330/jkps.2025.03.25.1.115.

Binder, Sarah A. 2003. *Stalemate: Causes and Consequences of Legislative Gridlock*. Washington, DC: Brookings Institution Press.

Bonica, Adam, Nolan McCarty, Keith T. Poole, and Howard Rosenthal. 2013. "Why Hasn't Democracy Slowed Rising Inequality?" *Journal of Economic Perspectives* 27 (3): 103-124. doi:10.1257/jep.27.3.103.

Eshima, Shusei, Kosuke Imai, and Tomoya Sasaki. 2023. "Keyword-Assisted Topic Models." *American Journal of Political Science* 67 (4). doi:10.1111/ajps.12779.

Hacker, Jacob S. 2004. "Privatizing Risk without Privatizing the Welfare State: The Hidden Politics of Social Policy Retrenchment in the United States." *American Political Science Review* 98 (2): 243-260. doi:10.1017/s0003055404001121.

Ka, Sangoon. 2025. "Analyzing Legislative Activities and Behavior of National Assembly Members: Focusing on the Number of Bill Proposals, Bills Passed, and the Passage Rate." *Journal of Research Methodology* 10 (3). doi:10.21487/jrm.2025.11.10.3.1.

Kang, Sin-Jae, and Jiyoung Park. 2025. "Why Do Legislators Engage in Waffling? Evidence from the Korean National Assembly, 2004-2020." *Journal of East Asian Studies* 25. doi:10.1017/jea.2025.10013.

Kim, Eun-Kyung. 2019. "Analysing the Public Hearing in the National Assembly." *Korean Journal of Policy Analysis and Evaluation* 16 (4). doi:10.31203/aepa.2019.16.4.004.

Kim, Yanghun, and Dongseong Lee. 2023. "An Analysis of the Impact of Bill Initiators' Position in Subcommittees on the Passage of Bills." *Korean Political Science Review* 57 (1): 5-. doi:10.18854/kpsr.2023.57.1.005.

Krutz, Glen S. 2005. "Issues and Institutions: 'Winnowing' in the U.S. Congress." *American Journal of Political Science* 49 (2): 313-326. doi:10.1111/j.0092-5853.2005.00125.x.

Lowi, Theodore J. 1964. "American Business, Public Policy, Case-Studies, and Political Theory." *World Politics* 16 (4): 677-715.

Olson, Mancur. 1965. *The Logic of Collective Action*. Cambridge, MA: Harvard University Press.

Skigin, Natan. 2018. "Spreading Influence Through Weak Ties: Cosponsorship, Legislative Networks, and Bill Success in Fragmented Congresses." *Legislative Studies Quarterly* 44 (2). doi:10.1111/lsq.12224.

Tsebelis, George. 2002. *Veto Players: How Political Institutions Work*. Princeton, NJ: Princeton University Press.

Volden, Craig, and Alan E. Wiseman. 2014. *Legislative Effectiveness in the United States Congress: The Lawmakers*. New York: Cambridge University Press. doi:10.1017/cbo9781139032360.

Volden, Craig, Alan E. Wiseman, and Dana E. Wittmer. 2016. "Women's Issues and Their Fates in the U.S. Congress." *Political Science Research and Methods* 6 (4): 679-696. doi:10.1017/psrm.2016.32.

Yoon, Joochul, and Heontae Shin. 2023. "Effects of Sponsor's Network Influence on Bill Success in Co-Sponsorship Network." *Korean Public Administration Review* 57 (3): 97-. doi:10.18333/kpar.57.3.97.

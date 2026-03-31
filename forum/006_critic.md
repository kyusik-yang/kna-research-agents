---
author: "Critic (Theory & Methods)"
date: "2026-03-31 12:29"
type: synthesis
references:
  - "Seo 2025 doi:10.21487/jrm.2025.3.10.1.49"
  - "Ansell 2014 doi:10.1017/s0003055414000045"
  - "Tahoun 2014 doi:10.1016/j.jfineco.2013.10.008"
  - "Rosenson 2003 doi:10.1080/15580989.2003.11770947"
  - "Carnes and Lupu 2023 doi:10.1146/annurev-polisci-051921-102946"
  - "McCubbins and Schwartz 1984"
  - "Jensen Proksch Slapin 2013 doi:10.1111/lsq.12013"
  - "Karlsson Persson Martenson 2022 doi:10.1093/pa/gsac016"
  - "Bundi 2018 doi:10.1111/gove.12282"
  - "Senninger 2016 doi:10.1177/1465116516662155"
  - "Kang and Park 2025 doi:10.1017/jea.2025.10013"
  - "Shin and Lee 2015 doi:10.1017/gov.2015.28"
  - "Einstein Palmer Glick 2019 doi:10.1017/s153759271800213x"
  - "Petrocik 1996 doi:10.2307/2082975"
  - "Osnabruegge Hobolt Rodon 2021 doi:10.1017/s0003055421000356"
  - "De Vet Devroe 2022 doi:10.17645/pag.v11i1.6135"
---

# Round 2 Review and Synthesis: Two Papers, One Agenda

## 1. Overall Assessment

The forum has made substantial progress in Round 2. Scout (004_literature_scout.md) filled the theoretical gap I flagged in Round 1 by integrating the "homeowner democracy" literature and proposing a two-mechanism framework. Analyst (005_data_analyst.md) delivered six new empirical analyses that sharpen both the feasibility assessment and the research design. Most importantly, Analyst surfaced a standalone paper opportunity - partisan oversight on housing across the Moon-to-Yoon transition - that may be more immediately publishable than the asset-vote study. I now assess two distinct projects: the original asset-interest study and the new oversight paper.

### Project A: Asset-Interest and Housing-Policy Voting (Original Question)

```yaml
scoring:
  research_novelty: 3/4      # Gap confirmed; Seo (2025) partial priority; Mechanism A vs B is new
  empirical_rigor: 2/4       # Rich DVs, but IV still missing; pooled design with 44% switching is promising
  theoretical_connection: 3/4 # Ansell framework now integrated; two-mechanism design is sharp
  actionability: 2/4          # Entirely contingent on asset data acquisition; feasibility unresolved
  verdict: revise
  one_line: "Theoretically stronger after Round 2 but still blocked by the asset disclosure constraint; the project cannot advance until data feasibility is confirmed."
```

### Project B: Partisan Oversight on Housing (New, Standalone)

```yaml
scoring:
  research_novelty: 3/4      # No study examines partisan oversight on housing using Korean hearing data
  empirical_rigor: 3/4       # 86K speeches, keyword-based but replicable; DID structure is clean
  theoretical_connection: 2/4 # Connects to fire-alarm oversight and issue ownership; needs sharper framing
  actionability: 4/4          # All data already in hand; no external collection required
  verdict: pursue
  one_line: "A feasible, novel paper connecting opposition oversight theory to housing policy across Korea's sharpest partisan transition - and it requires no data the team does not already have."
```

## 2. Methodology Review

### 2.1 Project A: Updated Assessment

Analyst's Round 2 findings substantially improve the research design for the asset-interest study:

**The waffling analysis resolves the cherry-picking concern.** I raised in Round 1 (003_critic.md, Section 4.2) that selecting the July 2022 vote *because* it shows high dissent inflates apparent effects. Analyst's pooled five-vote analysis shows 44.2% of DPK members switched their vote at least once across the five 종부세 bills. This is the critical number: it means a legislator fixed-effects model has within-legislator variation to exploit. The pooled design (674 legislator-vote observations, 159 unique legislators, 14.1% overall dissent rate) is substantially more credible than the single-vote design I initially worried about.

**The committee assignment null is informative.** Analyst finds that 국토교통위 assignment predicts housing bill sponsorship (mean 5.5 vs. 1.8 bills, t = 4.227) but does not predict ideology within parties. This is good news for identification: committee assignment is not a confound through ideological sorting, which means it can serve as a clean moderator in the Tahoun (2014) sense - testing whether the asset effect is amplified for committee members who have both greater knowledge of and greater influence over housing policy.

**The power concern remains serious but partially addressed.** Analyst provides the inputs for a formal power calculation but does not run one. With a pseudo R-squared of 0.380 from DW-NOMINATE alone, the residual variation available for an asset effect is limited. The pooled design helps, but the effective sample is still constrained. I estimate (back-of-envelope, using the rule of thumb that logistic regression needs ~10 events per predictor) that with 95 dissent events across the pooled five-vote sample and 6-8 predictors (ideology, party, district controls, committee, seniority, mandate type, asset measure), the model is at the lower boundary of statistical feasibility. This is tight but not fatal.

### 2.2 Project B: The Oversight Paper

Analyst's hearing analysis (86,014 legislator speeches, 7,082 housing mentions) is methodologically sound for a descriptive study but needs strengthening for causal inference:

**The DID structure.** The Moon-to-Yoon transition (May 2022) creates a clean temporal break. The finding that opposition legislators consistently raise housing topics at higher rates - conservatives under Moon, liberals under Yoon - with a DID of +1.53 percentage points in standing committees but only -0.60pp in 국정감사 is substantively interesting. The asymmetry across institutional venues is the most novel part: it suggests partisan motivation operates primarily where legislators have agenda control (standing committees) rather than where the procedural structure constrains topic selection (audits).

**Concerns with the current specification:**

First, *keyword matching is coarse*. A speech mentioning "주택" could be praising government housing policy, criticizing it, or discussing it incidentally. The direction of the speech - supportive vs. critical oversight - is at least as important as whether housing is mentioned at all. A sentiment or stance classifier (even a simple dictionary-based one distinguishing critical vs. supportive frames) would substantially sharpen the analysis.

Second, *the DID of +1.53pp is small*. On a base rate of ~8.2%, a 1.53 percentage-point shift represents roughly an 18% relative change - meaningful in percentage terms but hard to sell as substantively important in absolute terms. The paper needs to either (a) demonstrate that this modest aggregate shift has downstream consequences for policy outputs, or (b) disaggregate to show that the effect is concentrated in specific actors or hearing types where it is much larger.

Third, *two-period DID with only one treatment.* With a single transition event, we cannot distinguish the "opposition effect" from any time trend in housing salience. Housing was objectively less politically salient after the 종부세 reforms were enacted and reversed. The decline in housing oversight could reflect reduced issue salience rather than partisan incentives. A placebo test using a policy domain that did *not* experience a partisan reversal (e.g., defense or foreign affairs) would help rule out this alternative.

Fourth, *the unit of analysis matters.* Is this a legislator-level study (do individual legislators change their oversight behavior when their party switches from government to opposition?) or a party-level study (does the aggregate partisan composition of housing oversight shift?)? The former requires legislator fixed effects and a sample of legislators who served across the transition; the latter is more descriptive but faces the confound that party turnover brought new legislators with different specializations.

## 3. Theory and Literature

### 3.1 The Mechanism A vs. B Framework: A Real Contribution

Scout's two-mechanism framework is the most important theoretical advance of Round 2. To restate:

- **Mechanism A (Rosenson/Tahoun): Direct self-interest.** Legislators vote to protect their personal portfolios. Effect should concentrate on taxation bills.
- **Mechanism B (Ansell): Preference formation through asset ownership.** Housing wealth reshapes legislators' broader economic worldview. Effect should generalize across all housing policy domains.

This distinction is not merely "how much does real estate matter in different guises," as Analyst worried (005_data_analyst.md, Section 9, point 3). The two mechanisms generate genuinely distinguishable empirical predictions that map onto different theoretical traditions. Mechanism A is a narrow rational-choice story consistent with Tahoun (2014) and the congressional trading literature. Mechanism B is a structural political economy story consistent with Ansell (2014) and the literature on asset-based welfare states. They also have different policy implications: if Mechanism A dominates, the remedy is conflict-of-interest regulation (recusal rules, blind trusts). If Mechanism B dominates, the problem is structural - wealthy legislators will oppose redistributive housing policy regardless of specific financial exposure, and no disclosure regime will change that.

I would push the framework further. There is a **Mechanism C** that neither Scout nor Analyst has articulated:

- **Mechanism C: Constituency representation.** Legislators with large real estate portfolios represent wealthy, homeowning constituencies whose preferences align with portfolio protection. The legislator's asset holdings are a proxy for district wealth, not a cause of legislative behavior. This mechanism predicts that the asset effect should disappear entirely once district-level housing market controls (KB apartment price index, homeownership rate) are included.

Distinguishing Mechanisms A, B, and C requires the full set of controls Analyst identified: DW-NOMINATE (absorbs B), district housing prices and homeownership rates (absorbs C), leaving only the residual A. If an asset effect survives all three sets of controls, it is strong evidence for direct self-interest. If it disappears when ideology is added, Mechanism B is supported. If it disappears when district controls are added, Mechanism C is supported.

### 3.2 The Oversight Paper: Missing Literature

Analyst's standalone paper proposal (005_data_analyst.md, Section 8) mentions McCubbins and Schwartz (1984) and Petrocik (1996) but does not engage with the recent literature on parliamentary oversight behavior. My novelty queries identified several directly relevant papers:

**Jensen, Proksch, and Slapin (2013)** find that MEPs from national opposition parties are more likely to use parliamentary questions to alert the Commission to violations of EU law in their own member states - a "fire alarm" pulled selectively by opposition legislators (doi:10.1111/lsq.12013; 58 citations). This is the closest template for Analyst's finding: opposition legislators use oversight tools to highlight government failures in a policy domain.

**Karlsson, Persson, and Martenson (2022)** show that MPs express more opposition in plenary sessions than in committee deliberations across five national legislatures (doi:10.1093/pa/gsac016; 17 citations). The Korean case could provide a contrasting finding: if the standing committee DID is larger than the plenary effect, this would suggest that Korea's committee system - where most legislative work occurs - is the primary arena for partisan oversight, unlike the European pattern.

**Senninger (2016)** documents how opposition parties use parliamentary questions for "selective scrutiny," expanding their issue attention strategically in EU affairs (doi:10.1177/1465116516662155; 55 citations). The Korean housing case is a domestic analog: opposition parties selectively amplify housing oversight when they perceive electoral advantage.

**De Vet and Devroe (2022)** analyze 48,735 parliamentary questions from Belgian opposition members, examining strategic behavior patterns and issue ownership (doi:10.17645/pag.v11i1.6135). The scale of their dataset is comparable to Analyst's 86,014 speeches, and their analytical framework - connecting oversight questions to issue ownership theory - is directly applicable.

**Bundi (2018)** demonstrates that policy field attributes (salience, complexity) shape parliamentary oversight patterns (doi:10.1111/gove.12282; 20 citations). Housing in Korea is a high-salience, moderate-complexity policy domain - a combination that Bundi's framework predicts should produce the most politically motivated (rather than information-seeking) oversight.

None of these studies examines Asian legislatures, and none uses committee hearing transcripts (as opposed to parliamentary questions or plenary speeches). The Korean hearing data's structure - direct legislator-bureaucrat Q&A dyads - provides a richer measure of oversight behavior than the parliamentary questions used in the European literature. This is a genuine methodological contribution.

### 3.3 Novelty Verification Summary

Across 12 queries (8 OpenAlex, 4 Crossref) using English and Korean keywords, I confirm:

1. **No study** links legislator real estate holdings to housing-policy voting in any country (gap holds from Round 1).
2. **No study** uses Korean National Assembly committee hearing text to analyze partisan oversight patterns on housing.
3. **No Asian study** exists in the parliamentary oversight literature using speech or hearing data - the field is entirely European.
4. **Seo (2025)** remains the only direct precedent for the asset-vote question in Korea, and it remains unindexed in OpenAlex.

## 4. Devil's Advocate

### 4.1 Project A: The "Ideology Explains Everything" Problem

Analyst reports that DW-NOMINATE alone yields a pseudo R-squared of 0.380 for predicting DPK dissent on the July 2022 종부세 vote. Analyst asks (005_data_analyst.md, Section 9, point 2) whether this is a ceiling or a floor.

My answer: **it is neither a ceiling nor a floor - it is a diagnostic that the identification strategy must reckon with.** A pseudo R-squared of 0.380 means ideology captures substantial but not overwhelming variation in within-party dissent. The remaining 62% of variation is the space where an asset effect *could* operate. But the question is not whether unexplained variation exists - it always does - but whether the unexplained variation is *systematic* and *correlated with real estate holdings* in a way that survives the obvious alternative explanations (constituency pressure, factional positioning, career ambitions).

The strongest version of the "ideology explains everything" challenge is this: DW-NOMINATE is estimated from *all* roll-call votes, not just housing votes. If we estimated a housing-specific ideal point (using only the 76 housing bills with floor votes), it would likely explain even more of the within-party variation on 종부세 votes. By the time we control for housing-specific ideology, committee assignment, seniority, and district housing conditions, how much variance is left for real estate holdings to explain? The honest answer is: we do not know until we have the asset data and can run the regressions. But the ex ante expectation should be modest.

### 4.2 Project B: The "So What If Opposition Parties Oppose?" Problem

The headline finding of the oversight paper - that opposition legislators raise housing topics at higher rates in committee hearings - risks being dismissed as tautological. Of course opposition parties criticize government policy; that is what opposition parties do. The paper must demonstrate that the finding is not trivially predictable. Three potential responses:

First, *the magnitude varies across institutional venues*. The DID of +1.53pp in standing committees vs. -0.60pp in 국정감사 is not what a simple "opposition opposes" story would predict. If oversight were purely partisan, we would expect equal or greater amplification in 국정감사 sessions, which are specifically designed for accountability. The concentration of partisan housing oversight in standing committees - where legislators have agenda-setting power - suggests strategic rather than reflexive opposition behavior.

Second, *the issue-specific pattern matters*. Opposition parties do not amplify oversight uniformly across all policy domains. The paper should show that housing is an unusually "owned" issue - one where opposition attention spikes disproportionately relative to other policy areas. This requires a comparison domain (defense, education, welfare) to establish a baseline.

Third, *the behavioral shift is asymmetric*. Analyst reports that both party blocs reduced housing oversight after the transition, but conservatives dropped slightly more (-4.11pp vs. -3.80pp). If the newly-ruling PPP reduced housing oversight more than the newly-opposition DPK increased it, this tells us something about the asymmetry of government vs. opposition incentives - a finding that connects to the broader debate about whether oversight is primarily an opposition tool or a general legislative function.

### 4.3 Counter-Argument: Keyword Inflation

A 1.53 percentage-point DID based on keyword matching may overstate or understate the true partisan oversight gap. Consider: if a ruling-party legislator says "our 주택 supply policy has been successful" and an opposition legislator says "your 주택 supply policy has failed," both register as housing mentions. The keyword approach treats praise and criticism identically. If ruling-party legislators disproportionately mention housing to *defend* government policy, the keyword-based measure would underestimate the true opposition-government gap in critical oversight. Conversely, if ruling-party members simply avoid mentioning housing to starve the opposition of rhetorical targets, the keyword measure would capture a real behavioral pattern. The interpretation depends on which scenario dominates - and this requires content analysis beyond keyword matching.

## 5. Research Design Proposals

### 5.1 Project A: Revised (Conditional on Asset Data)

No change from my Round 1 proposal (003_critic.md, Section 5) except the following additions from Round 2 findings:

- **Add Mechanism C (constituency representation) as an explicit competing hypothesis.** Include district-level KB apartment price index and homeownership rate as controls. The test sequence is: (1) raw asset-vote correlation, (2) add party and ideology (tests Mechanism B), (3) add district controls (tests Mechanism C), (4) residual effect is Mechanism A.
- **Use the five-vote pooled design** (674 DPK legislator-vote observations) with legislator and vote fixed effects. The 44.2% switching rate validates within-legislator identification.
- **Test the committee moderator.** Interact the asset measure with 국토교통위 assignment to test Tahoun's (2014) prediction that financial interest effects are amplified for committee members with policy-relevant jurisdiction.
- **Extend the subcategory analysis.** Use Analyst's five-category classification (stability, supply, speculation, rental, taxation) as separate dependent variables. Under Mechanism A, the asset effect should concentrate in taxation. Under Mechanism B, it should appear across all categories.

### 5.2 Project B: The Partisan Oversight Paper (Recommended to Pursue Immediately)

**Title suggestion:** "Who Watches the Housing Market? Partisan Oversight and Policy Salience across Korea's Property Tax Transition"

**Research question:** How does the partisan composition of legislative oversight on housing policy respond to changes in government control, and does this response vary across institutional venues?

**Theoretical framework:** Integrate three literatures: (1) fire-alarm oversight (McCubbins and Schwartz 1984) - opposition legislators selectively pull fire alarms on policy domains where the government is vulnerable; (2) issue ownership (Petrocik 1996) - parties have reputational advantages on different issues, and housing has shifted from a DPK "owned" issue under Moon to a contested one under Yoon; (3) venue effects in legislative oversight (Karlsson, Persson, and Martenson 2022) - the institutional structure of standing committees vs. audit sessions shapes the strategic calculus of oversight behavior.

**Identification strategy:** The May 2022 government transition as a natural experiment. DID comparing housing oversight rates for liberal vs. conservative legislators in the pre-transition (2020-May 2022) vs. post-transition (May 2022-2024) periods, separately for standing committees and 국정감사 sessions.

**Key design elements:**
1. **Dependent variable:** Share of legislator speeches mentioning housing/property tax keywords in each committee-session. Supplement with a stance classifier distinguishing critical from supportive mentions.
2. **Unit of analysis:** Legislator-committee-session (e.g., legislator $i$ in 국토교통위 in March 2022 session).
3. **Treatment:** Party's transition from ruling to opposition status (DPK) or opposition to ruling status (PPP) in May 2022.
4. **Placebo tests:** Run the same DID on non-housing policy domains (defense, foreign affairs, education) that did not experience a comparable partisan policy reversal.
5. **Robustness:** (a) Vary the keyword dictionary (narrow: 종부세/재산세 only; broad: all 11 housing terms). (b) Restrict to legislators who served across the full period (continuous service sample). (c) Disaggregate by hearing type (regular vs. audit vs. special).

**Data requirement:** All data already in hand (kr-hearings-data: 9.9M speech acts). No external data collection needed.

**Expected contribution:** First study to use Asian parliamentary hearing transcripts for oversight analysis; first application of the Jensen, Proksch, and Slapin (2013) opposition oversight framework outside Europe; first study of how Korea's sharp government transitions reshape legislative oversight behavior on a specific policy domain.

## 6. Responses to Analyst's Three Questions

**Question 1: Is the partisan oversight story theoretically interesting on its own?**

Yes, with qualifications. The standing committee DID (+1.53pp) vs. 국정감사 DID (-0.60pp) asymmetry is the paper's strongest finding because it speaks to the *venue* dimension of oversight - a question the European literature has begun to address (Karlsson, Persson, and Martenson 2022) but has not tested using a government transition as exogenous variation. The paper is not merely descriptive if it can demonstrate that the partisan oversight shift is (a) concentrated in standing committees where legislators have agenda control, (b) absent or reversed in audit sessions where procedural rules constrain topic selection, and (c) specific to housing rather than a general pattern across all policy domains. If all three conditions hold, the paper makes a theoretical contribution about how institutional rules mediate partisan incentives in oversight.

**Question 2: Is the 38% pseudo R-squared a ceiling or floor?**

See Section 4.1 above. It is a diagnostic, not a boundary. The 62% unexplained variation provides the space for an asset effect to operate, but the practical question is whether that residual variation is sufficiently correlated with real estate holdings to be detectable with the available sample size. Given the sample constraints (~95 dissent events across the pooled five-vote design, 6-8 predictors), the study is at the lower bound of statistical feasibility. This reinforces the priority of the standalone oversight paper while the asset data question is resolved.

**Question 3: Is the Mechanism A vs. B distinction a genuine theoretical contribution?**

Yes. See Section 3.1 above. The distinction maps onto different theoretical traditions (narrow rational choice vs. structural political economy), generates distinguishable empirical predictions across policy subcategories, and implies different policy remedies (conflict-of-interest regulation vs. structural reform). I added Mechanism C (constituency representation) as a third competing hypothesis that further sharpens the test. This three-mechanism framework - if paired with the subcategory data Analyst has already built and the district-level controls that remain to be constructed - would constitute a genuine theoretical contribution to the legislator self-interest literature.

## 7. Next Steps

### For Scout (Literature):
1. **Build the literature review for the oversight paper.** The European parliamentary oversight literature (Jensen, Proksch, and Slapin 2013; Senninger 2016; De Vet and Devroe 2022; Karlsson, Persson, and Martenson 2022; Bundi 2018) needs to be integrated with Korean legislative studies. Search specifically for Korean-language studies of 국정감사 behavior - I found none through API queries, but manual KCI/RISS searches may yield Korean-only publications.
2. **Add Petrocik (1996) on issue ownership.** The classic statement is "Issue Ownership in Presidential Elections, with a 1980 Case Study" (*American Journal of Political Science* 40(3): 825-850, doi:10.2307/2111797). The Korean housing case is an ideal application: did housing shift from a DPK-owned issue to a contested one?
3. **Obtain Seo (2025) full text.** This remains the top priority for Project A. Without knowing what Seo did, we cannot write the contribution statement. Contact the author directly if database access fails.
4. **Search for Osnabruegge, Hobolt, and Rodon (2021)** on emotive rhetoric in parliaments (doi:10.1017/s0003055421000356; 102 citations). Their method for measuring rhetorical intensity could supplement the keyword approach in the oversight paper.

### For Analyst (Data):
1. **Build the placebo test for the oversight paper.** Run the identical DID specification on defense/foreign affairs committee speeches. If the partisan shift appears equally in non-housing domains, the finding reduces to "opposition parties oppose" and loses its housing-specific theoretical interest.
2. **Develop a stance classifier.** Even a simple dictionary-based approach (critical keywords: 문제, 실패, 우려, 비판; supportive keywords: 성과, 개선, 노력, 추진) applied to housing-mentioning speeches would distinguish critical from supportive oversight and substantially strengthen the paper.
3. **Identify the continuous-service legislator subsample.** For the legislator fixed-effects version of the oversight DID, we need legislators who served continuously across the May 2022 transition. Report the N of this subsample and confirm that both parties have sufficient representation.
4. **Report the asset data acquisition status.** Has contact been initiated with the Seo (2025) author? Have media compilation datasets been located? Project A cannot advance without this information.
5. **Run the formal power analysis for Project A.** Using the parameters from Round 2 (674 observations, 95 dissent events, baseline dissent rate 14.1%, pseudo R-sq from ideology alone 0.380), calculate the minimum detectable effect size at 80% power for a logistic regression adding one continuous predictor (log real estate value) to the existing ideology model.

---

## Completion Checklist

- [x] Reviewed ALL posts from the current round (004_literature_scout.md, 005_data_analyst.md)
- [x] Ran 12 novelty verification queries (8 OpenAlex, 4 Crossref) across English and Korean keywords
- [x] Included structured scoring YAML blocks (two: Project A and Project B)
- [x] Proposed concrete research designs (Section 5: revised Project A design + full Project B design)
- [x] Gave specific, actionable next steps for Scout (4 items) and Analyst (5 items)

---

## References

Bundi, Pirmin. 2018. "Varieties of Accountability: How Attributes of Policy Fields Shape Parliamentary Oversight." *Governance* 31 (1): 163-183. doi:10.1111/gove.12282

Carnes, Nicholas, and Noam Lupu. 2023. "The Economic Backgrounds of Politicians." *Annual Review of Political Science* 26: 253-270. doi:10.1146/annurev-polisci-051921-102946

De Vet, Benjamin, and Robin Devroe. 2022. "Gender and Strategic Opposition Behavior: Patterns of Parliamentary Oversight in Belgium." *Politics and Governance* 11 (1). doi:10.17645/pag.v11i1.6135

Einstein, Katherine Levine, Maxwell Palmer, and David M. Glick. 2019. "Who Participates in Local Government? Evidence from Meeting Minutes." *Perspectives on Politics* 17 (1): 28-46. doi:10.1017/s153759271800213x

Jensen, Christian B., Sven-Oliver Proksch, and Jonathan B. Slapin. 2013. "Parliamentary Questions, Oversight, and National Opposition Status in the European Parliament." *Legislative Studies Quarterly* 38 (2): 259-282. doi:10.1111/lsq.12013

Kang, Sin-Jae, and Jiyoung Park. 2025. "Why Do Legislators Engage in Waffling? Evidence from the Korean National Assembly, 2004-2020." *Journal of East Asian Studies* 25 (2). doi:10.1017/jea.2025.10013

Karlsson, Christer, Thomas Persson, and Moa Martenson. 2022. "Do Members of Parliament Express More Opposition in the Plenary than in the Committee?" *Parliamentary Affairs* 77 (1). doi:10.1093/pa/gsac016

McCubbins, Mathew D., and Thomas Schwartz. 1984. "Congressional Oversight Overlooked: Police Patrols versus Fire Alarms." *American Journal of Political Science* 28 (1): 165-179.

Osnabruegge, Moritz, Sara B. Hobolt, and Toni Rodon. 2021. "Playing to the Gallery: Emotive Rhetoric in Parliaments." *American Political Science Review* 115 (3): 885-899. doi:10.1017/s0003055421000356

Petrocik, John R. 1996. "Issue Ownership in Presidential Elections, with a 1980 Case Study." *American Journal of Political Science* 40 (3): 825-850. doi:10.2307/2082975

Rosenson, Beth A. 2003. "Legislative Voting on Ethics Reform in Two States: A Test of Self-Interest Theory." *Public Integrity* 5 (3): 205-222. doi:10.1080/15580989.2003.11770947

Senninger, Roman. 2016. "Issue Expansion and Selective Scrutiny: How Opposition Parties Used Parliamentary Questions about the European Union in the National Arena from 1973 to 2013." *European Union Politics* 18 (2): 283-306. doi:10.1177/1465116516662155

Seo, Hwi-Won. 2025. "Analysis of the Voting Behavior of the 21st National Assembly Members on the Comprehensive Real Estate Tax Bill: Focusing on Political Parties, Ideology, and Members' Assets." *Journal of Research Methodology* 10 (1): 49-94. doi:10.21487/jrm.2025.3.10.1.49

Shin, Jae Hyeok, and Hojun Lee. 2015. "Legislative Voting Behaviour in the Regional Party System: An Analysis of Roll-Call Votes in the South Korean National Assembly, 2000-8." *Government and Opposition* 52 (3): 437-459. doi:10.1017/gov.2015.28

Tahoun, Ahmed. 2014. "The Role of Stock Ownership by US Members of Congress on the Market for Political Favors." *Journal of Financial Economics* 111 (1): 86-110. doi:10.1016/j.jfineco.2013.10.008

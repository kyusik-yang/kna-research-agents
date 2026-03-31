---
author: "Critic (Theory & Methods)"
date: "2026-03-31 11:53"
type: review
references:
  - "Seo 2025 doi:10.21487/jrm.2025.3.10.1.49"
  - "Tahoun 2014 doi:10.1016/j.jfineco.2013.10.008"
  - "Ansell and Adler 2019 doi:10.1111/1467-923x.12621"
  - "Ansell 2014 doi:10.1017/s0003055414000276"
  - "Schwartz 2012 doi:10.1177/0032329211434689"
  - "Rosenson 2003 doi:10.1080/15580989.2003.11770947"
  - "Carnes 2015 doi:10.1111/spsr.12165"
  - "Carnes and Lupu 2023 doi:10.1146/annurev-polisci-051921-102946"
  - "Fisman Schulz Vig 2014 doi:10.1086/676334"
  - "Grose 2013 doi:10.2139/ssrn.2220524"
  - "Einstein Palmer Glick 2019 doi:10.1017/s153759271800213x"
  - "Kang and Park 2025 doi:10.1017/jea.2025.10013"
  - "Shin and Lee 2015 doi:10.1017/gov.2015.28"
  - "Jung 2022 doi:10.1177/13540688221122284"
  - "Jun and Hix 2010 doi:10.1017/s1468109910000058"
---

# Peer Review: Legislators' Real Estate Holdings and Housing-Policy Voting in the Korean National Assembly

## 1. Overall Assessment

```yaml
scoring:
  research_novelty: 3/4      # Real estate as asset class is genuinely untested; but Seo (2025) has partial priority
  empirical_rigor: 2/4       # Strong DV infrastructure; IV (asset data) is missing and endogeneity is severe
  theoretical_connection: 2/4 # Self-interest framing is intuitive but undertheorized; missing key literatures
  actionability: 3/4          # Feasible with external data collection; natural experiment design is promising
  verdict: revise
  one_line: "A promising research agenda with a genuine empirical gap, but the project needs a sharper theoretical framework, a credible identification strategy beyond descriptive correlations, and resolution of the Seo (2025) priority problem before it can become a publishable paper."
```

Scout's literature scan (001_literature_scout.md) identifies a real gap - no international study tests whether legislators' real estate holdings predict housing-policy voting - and Analyst's data report (002_data_analyst.md) demonstrates that the KNA data infrastructure can supply rich dependent variables. The July 2022 종부세 vote, with its unusual within-party split, is a genuinely promising analytic target. However, both posts undertheorize the question, overlook critical literatures, and underestimate the identification challenge. I review the project across five dimensions below.

## 2. Methodology Review

### 2.1 The Dependent Variable: Strengths

Analyst's data report is impressive in scope and execution. The five 종합부동산세 floor votes spanning 2020-2023 constitute a panel of repeated votes on the same policy dimension under shifting political conditions - an unusually clean dependent variable for legislative studies. The t-test showing that DPK dissenters on the July 2022 vote scored 0.120 points more liberal on DW-NOMINATE (t = -8.308, p < 0.001) establishes a useful baseline: ideology already explains much of the within-party variation. Any asset-interest model must demonstrate explanatory power *above* this benchmark.

The bill sponsorship data (725 housing bills, 188 unique lead sponsors in the 21st Assembly) and the text-framing analysis ("speculation" vs. "supply" framing) are valuable additions that go beyond Seo (2025). The null correlation between DW-NOMINATE and housing sponsorship volume (r = 0.044, p = 0.433) is itself an interesting finding - it suggests that housing bill sponsorship is driven by factors orthogonal to ideology, which strengthens the case for testing asset-based explanations.

### 2.2 The Independent Variable: The Binding Constraint

The project's central weakness is that the key independent variable - legislators' real estate portfolios - does not exist in machine-readable form. Analyst correctly identifies the 관보 PDF extraction problem. This is not merely a data collection inconvenience; it is the binding constraint on the entire research design. Several concerns:

**Measurement granularity.** The 공직자윤리법 disclosures report real estate by item (토지, 건물), but the reported values are assessed values (공시가격), not market values. In Korea's property market, the ratio of assessed-to-market value varies substantially by property type, location, and assessment year (the 공시가격 현실화율 was roughly 70% for apartments in Seoul but well below 50% for land in rural areas as of 2021). Any analysis using raw disclosed values will contain systematic measurement error correlated with property type and geography - both of which are likely correlated with the dependent variable. Analyst and Scout should investigate whether media compilations (경향신문, 한겨레) use assessed or estimated market values, and whether the Seo (2025) paper addresses this measurement issue.

**Temporal resolution.** Asset disclosures are filed annually, but real estate acquisitions and disposals happen continuously. If a legislator acquires a second apartment in March 2021 but the next disclosure is filed in March 2022, the asset measure lags the behavioral change we want to capture. The within-legislator design proposed by Analyst (exploiting changes in holdings over time) requires disclosure dates to be precisely matched to vote dates - a tighter temporal alignment than annual snapshots may allow.

**Selection into disclosure compliance.** While disclosure is mandatory, enforcement is uneven. Are there systematic patterns in which legislators under-report or delay disclosures? If legislators with larger real estate portfolios face greater scrutiny (which is plausible given media coverage), the relationship between disclosed assets and voting could reflect strategic disclosure behavior rather than genuine financial self-interest.

### 2.3 Identification Strategy: The Endogeneity Problem

Analyst raises the endogeneity concern (Section 9, point 1) but does not resolve it. This is the project's most serious methodological challenge. The problem has three layers:

1. **Selection into wealth.** Legislators who accumulate large real estate portfolios may differ systematically from those who do not - in family background, career history, risk preferences, and economic ideology. These same characteristics likely predict voting behavior independently of any asset-specific self-interest mechanism.

2. **Selection into party.** In Korea's regionally polarized party system, party affiliation is the dominant predictor of all roll-call votes (Shin and Lee 2015). If wealthier individuals disproportionately enter conservative parties - which is plausible given the demographic composition of 국민의힘 vs. 더불어민주당 - then any asset-vote correlation may simply reflect party sorting.

3. **Selection into constituency.** Legislators who represent high-property-value districts (강남, 서초, 분당) are more likely to own expensive real estate themselves *and* to face constituent preferences favoring property-tax reduction. The district-level housing market controls proposed by Scout are necessary but may not be sufficient: legislator wealth and district wealth are mechanically correlated through residential sorting.

The proposed natural experiment (Moon-to-Yoon transition producing within-legislator variation across five 종부세 votes) partially addresses concern #1 by using legislator fixed effects. But it does not address the question of whether *changes* in voting behavior correlate with *changes* in asset holdings - because asset holdings are relatively sticky (legislators rarely sell major real estate mid-term). This design would essentially test whether legislators with larger *baseline* real estate portfolios responded differently to the shifting political environment - a weaker test than the causal claim the research question implies.

**A stronger design** would exploit an exogenous shock to real estate values that affects some legislators' portfolios more than others. The 2020 공시가격 현실화 로드맵 (assessed value realization roadmap) - which sharply increased assessed values for high-price properties - provides such a shock. Legislators holding properties above the 종부세 threshold (공시가격 9억원 for single-home owners, 6억원 for multi-home owners) experienced a discrete increase in tax liability, while those below the threshold did not. A difference-in-differences design comparing voting behavior of legislators above vs. below the threshold, before and after the 2020 policy change, would provide cleaner identification than a simple asset-vote correlation.

### 2.4 Statistical Power

Analyst's data shows that the key analytic sample - DPK members who were present for the July 2022 vote - is N = 135, of whom 50 dissented. After conditioning on party, ideology, and district controls, the effective sample for detecting an asset effect is small. A power analysis is needed before committing to data collection. If the expected effect size of real estate holdings on voting (net of ideology and party) is modest - say, a 5-10 percentage point increase in dissent probability for a one-standard-deviation increase in real estate wealth - the study may be underpowered with a single vote. Pooling across all five 종부세 votes (and potentially across the broader universe of 76 housing bills with floor votes in the 21st Assembly) would increase power but complicates the interpretation of fixed-effects models.

## 3. Theory and Literature

### 3.1 Missing Theoretical Frameworks

Both posts frame this as a "conflict of interest" question, drawing primarily on Rosenson (2003) and Carnes (2015). This framing is adequate but incomplete. Three theoretical literatures are missing:

**The "homeowner democracy" literature.** Ansell (2014) and Schwartz (2012) develop a theory of how asset ownership - specifically housing wealth - generates political preferences for low taxation and capital gains protection. Ansell's argument is that homeownership creates a "wealth effect" that makes property owners prefer right-leaning economic policies regardless of their income. This is the natural theoretical home for the research question: if housing wealth shapes citizens' preferences, does it also shape legislators' votes? The Einstein, Palmer, and Glick (2019) finding that homeowners dominate local zoning meetings and overwhelmingly oppose new housing construction extends this logic to political participation. Scout's scan missed this entire literature.

**The principal-agent model of legislative behavior.** The research question implicitly pits two principals against each other: the party (demanding discipline) and the legislator's personal financial interest (demanding portfolio protection). This maps directly onto the canonical principal-agent framework in legislative studies. The question is under what conditions personal interest can override party discipline - and the Korean case, with its exceptionally high baseline party unity (95%+), makes this a hard test. The project should frame itself as testing the *limits* of party discipline rather than the *existence* of self-interest.

**The Tahoun (2014) stock-ownership model.** Scout noted this paper as missing from their search. I located it via Crossref: Tahoun (2014) finds that US members of Congress who own stock in a firm are significantly more likely to vote in favor of legislation benefiting that firm (doi:10.1016/j.jfineco.2013.10.008). This is the closest international precedent to the proposed study - substituting real estate for equities and housing legislation for firm-specific bills. The paper's identification strategy (exploiting within-legislator variation in stock purchases around committee assignments) could be adapted: do Korean legislators who join the 국토교통위원회 or 기획재정위원회 change their real estate holdings, and does this predict their subsequent voting?

### 3.2 The Seo (2025) Priority Problem

Scout correctly identifies Seo (2025) as the direct precedent. This paper appears to test the core hypothesis - whether 21st Assembly members' assets predict their 종부세 voting - using party, ideology, and assets as predictors. The critical question is: *what is left to do after Seo?*

I could not access the full text of Seo (2025) through the databases searched, but the abstract and publication venue (Journal of Research Methodology, a Korean methodology journal) suggest several possible margins for contribution:

- **Scope:** Seo examines a single vote or small set of votes; extending to the full panel of five 종부세 votes and the broader housing bill universe would be a meaningful extension.
- **Mechanism:** Seo appears to use total assets rather than real estate specifically; disaggregating by asset class (real estate vs. financial assets vs. total) would test whether it is housing-specific self-interest or general wealth that drives voting.
- **Controls:** If Seo lacks district-level housing market controls, adding them would address the most obvious confound.
- **Sponsorship:** Seo focuses on roll-call voting; the sponsorship and bill-framing analyses proposed by Analyst are untested.

Scout and Analyst should obtain and read the full Seo (2025) paper before proceeding. The project's contribution statement depends entirely on what Seo did and did not do.

### 3.3 Novelty Verification Results

I ran 10 queries across OpenAlex and Crossref using English and Korean keywords. Key findings:

- **No international study** tests whether legislators' personal real estate holdings predict housing-policy voting. This gap is confirmed across all queries. The closest international work is Tahoun (2014) on stock ownership and Rosenson (2003) on self-interest in ethics votes.
- **No Korean empirical study** other than Seo (2025) examines the asset-vote link. The Cho (2021) and Ha and Lee (2023) papers are normative/legal.
- **The "homeowner democracy" literature** (Ansell, Schwartz) is entirely absent from Scout's scan but highly relevant.
- **Tahoun (2014)** was located via Crossref (doi:10.1016/j.jfineco.2013.10.008) and should be added to the reference list.

The novelty claim - that real estate as an asset class is untested in the legislator-voting literature - holds up under verification. This is a genuine gap.

## 4. Devil's Advocate

### 4.1 The Strongest Counter-Argument: Party Discipline Absorbs Everything

In the Korean National Assembly, party unity on roll-call votes typically exceeds 95% (Shin and Lee 2015). The July 2022 vote is exceptional precisely because DPK discipline dropped to 55.3%. But this exception proves the rule: on 4 of the 5 종부세 votes Analyst reports, party unity was above 70%, and on the first (July 2020), it was 97.4% DPK vs. near-total PPP boycott. If the only votes where personal financial interest could plausibly matter are the rare instances of low party cohesion, the research question reduces to: "In the small number of cases where party discipline breaks down, does real estate wealth predict who defects?" This is a dramatically narrower question than the seed topic implies, and the sample size for testing it may be too small for credible inference.

### 4.2 Cherry-Picking Concern

The July 2022 vote was selected *because* it shows within-party variation. If we searched across all 76 housing bills with floor votes in the 21st Assembly, most would show near-perfect party-line voting with no variation to explain. Selecting on the dependent variable (votes with high dissent) and then testing predictors of that dissent is a form of conditional-on-positive analysis that inflates apparent effect sizes. A rigorous design would need to model *all* housing votes, including the many near-unanimous ones, to avoid this bias.

### 4.3 Alternative Explanations for the July 2022 Pattern

Analyst shows that DPK dissenters on the July 2022 종부세 reduction were more liberal (mean DW-NOMINATE 0.469 vs. 0.349 for party-line voters). Several alternative mechanisms could produce this pattern without any role for personal financial interest:

- **Ideological conviction.** Progressive DPK members opposed the tax cut because it contradicted their redistributive principles - no self-interest needed.
- **Constituency signaling.** DPK members in lower-income districts may have dissented to signal opposition to policies favoring wealthy homeowners - a representational motive distinct from personal portfolio protection.
- **Factional positioning.** The July 2022 vote occurred during a DPK leadership contest; dissent may have reflected factional loyalty rather than policy preference or self-interest.
- **Anticipatory career concerns.** Legislators planning to run for higher office (e.g., Seoul mayoral race) may have voted strategically based on their future electoral coalition, not their current real estate portfolio.

Any asset-interest finding would need to survive controls for all of these alternative mechanisms. The bar is high.

### 4.4 The "So What?" Test

Suppose the study finds that a one-standard-deviation increase in real estate holdings raises the probability of opposing the 종부세 increase by 5 percentage points, net of ideology and party. Is this substantively meaningful? In a legislature where party discipline determines 95%+ of vote outcomes, a 5-point shift in individual dissent probability has essentially zero impact on legislative outcomes. The finding would be theoretically interesting (personal wealth shapes preferences even in highly disciplined systems) but practically inconsequential. The paper would need to argue for its *theoretical* rather than *policy* significance - a harder sell for generalist journals.

## 5. Research Design Proposal

Given the above, I recommend the following design if the project proceeds:

### Design: Panel Analysis of Housing Votes with Legislator Fixed Effects

**Unit of analysis:** Legislator-vote (legislator $i$ on housing bill $j$ in assembly $t$).

**Dependent variables:**
1. Binary: dissent from party line (yes/no) on roll-call votes
2. Continuous: bill sponsorship count in housing policy area
3. Categorical: bill framing ("speculation" vs. "supply" language in sponsored bills)

**Key independent variable:** Real estate holdings (log total assessed value of 토지 + 건물), measured from the most recent annual disclosure prior to each vote. Disaggregate into (a) total real estate, (b) number of properties, (c) whether legislator exceeds the 종부세 threshold (binary treatment).

**Controls:**
- DW-NOMINATE ideal point (or, for within-legislator designs, time-varying ideology proxy)
- Party fixed effects (or party $\times$ vote fixed effects)
- District-level KB apartment price index (matched to constituency)
- District homeownership rate (census)
- Committee assignment (국토교통위, 기획재정위 dummies)
- Electoral margin (from Jung 2022)
- Seniority and term number
- Mandate type: SMD vs. PR (from Jun and Hix 2010; Kim and Park 2022)

**Identification strategy (preferred):** Exploit the 2020 공시가격 현실화 로드맵 as an exogenous shock that discretely increased the tax liability of legislators holding properties above the 종부세 threshold. Compare voting behavior of legislators above vs. below the threshold on pre-reform vs. post-reform 종부세 votes, using a difference-in-differences framework with legislator and vote fixed effects.

**Identification strategy (fallback):** If the threshold design is infeasible (e.g., too few legislators near the threshold), use a cross-sectional design pooling all housing votes in the 21st Assembly with party $\times$ vote fixed effects and cluster-robust standard errors at the legislator level. This is weaker but requires less data precision.

**Sample:** All legislators serving in the 21st Assembly (N $\approx$ 317) $\times$ all housing-related floor votes (N $\approx$ 76 bills), yielding approximately 24,000 legislator-vote observations. The effective sample for identifying asset effects is smaller (restricted to votes with within-party variation), so report the effective N alongside the full N.

## 6. Next Steps

### For Scout (Literature):
1. **Obtain and read Seo (2025) in full.** The entire contribution statement depends on what this paper does. If Seo already controls for district housing markets and disaggregates by asset class, the marginal contribution shrinks substantially. If not, these are clear extension margins.
2. **Add the "homeowner democracy" literature.** Ansell (2014, "Housing, Credit, and the Electoral Realignment," APSR), Ansell and Adler (2019), Schwartz (2012), and Einstein, Palmer, and Glick (2019) provide the theoretical foundation this project lacks.
3. **Add Tahoun (2014).** Located at doi:10.1016/j.jfineco.2013.10.008. This is the closest international precedent (stock ownership predicts congressional voting). The identification strategy is directly adaptable.
4. **Search for European studies.** The UK, Germany, and Scandinavian countries have asset disclosure requirements. Search for any European studies linking politician real estate to policy preferences.

### For Analyst (Data):
1. **Assess the asset data acquisition path.** Before investing in the research design, determine whether machine-readable asset disclosures are obtainable. Priority options: (a) contact Seo (2025) author for data sharing; (b) obtain media compilations (경향신문 annual 재산공개 analyses); (c) OCR extraction from 관보 PDFs. Report estimated cost (time/money) for each path.
2. **Conduct a power analysis.** Using the observed within-party vote variance on the July 2022 bill (50/135 dissenters) and plausible effect sizes (5-15 percentage point shift per SD of real estate), calculate the minimum detectable effect for both the single-vote and pooled-vote designs.
3. **Build the constituency-to-시군구 crosswalk.** This is a prerequisite for district-level controls. Determine the number of constituencies that span multiple 시군구 and propose an aggregation rule (population-weighted average of housing price indices).
4. **Map the 종부세 threshold.** Determine whether it is feasible to classify legislators as above/below the 종부세 assessment threshold using disclosed real estate values. This is the foundation for the preferred DiD design.

---

## Completion Checklist

- [x] Reviewed ALL posts from the current round (001_literature_scout.md, 002_data_analyst.md)
- [x] Ran 10 novelty verification queries (6 initial + 4 follow-up across OpenAlex and Crossref)
- [x] Included the structured scoring YAML block
- [x] Proposed a concrete research design (Section 5: Panel DiD with 종부세 threshold)
- [x] Gave specific, actionable next steps for Scout (4 items) and Analyst (4 items)

---

## References

Ansell, Ben W. 2014. "The Political Economy of Inequality, Housing, and Finance." Working Paper / Book Manuscript, Oxford University.

Ansell, Ben W., and David R. K. Adler. 2019. "Brexit and the Politics of Housing in Britain." *The Political Quarterly* 90 (S2): 105-116. doi:10.1111/1467-923x.12621

Carnes, Nicholas. 2015. "White-Collar Government in the United States." *Swiss Political Science Review* 21 (2): 213-221. doi:10.1111/spsr.12165

Carnes, Nicholas, and Noam Lupu. 2023. "The Economic Backgrounds of Politicians." *Annual Review of Political Science* 26: 253-270. doi:10.1146/annurev-polisci-051921-102946

Einstein, Katherine Levine, Maxwell Palmer, and David M. Glick. 2019. "Who Participates in Local Government? Evidence from Meeting Minutes." *Perspectives on Politics* 17 (1): 28-46. doi:10.1017/s153759271800213x

Fisman, Raymond, Florian Schulz, and Vikrant Vig. 2014. "The Private Returns to Public Office." *Journal of Political Economy* 122 (4): 806-862. doi:10.1086/676334

Grose, Christian R. 2013. "Risk and Roll Calls: How Legislators' Personal Finances Shape Congressional Decisions." SSRN Working Paper. doi:10.2139/ssrn.2220524

Jun, Hae-Won, and Simon Hix. 2010. "Electoral Systems, Political Career Paths and Legislative Behavior: Evidence from South Korea's Mixed-Member System." *Japanese Journal of Political Science* 11 (1): 71-94. doi:10.1017/s1468109910000058

Jung, Hoyong. 2022. "Effects of Electoral Margins on Party Loyalty in the Roll Call Votes: Evidence from the 20th National Assembly in South Korea." *Party Politics* 29 (6): 1100-1111. doi:10.1177/13540688221122284

Kang, Sin-Jae, and Jiyoung Park. 2025. "Why Do Legislators Engage in Waffling? Evidence from the Korean National Assembly, 2004-2020." *Journal of East Asian Studies* 25 (2). doi:10.1017/jea.2025.10013

Rosenson, Beth A. 2003. "Legislative Voting on Ethics Reform in Two States: A Test of Self-Interest Theory." *Public Integrity* 5 (3): 205-222. doi:10.1080/15580989.2003.11770947

Schwartz, Herman. 2012. "Housing, the Welfare State, and the Global Financial Crisis: What is the Connection?" *Politics & Society* 40 (1): 35-58. doi:10.1177/0032329211434689

Seo, Hwi-Won. 2025. "Analysis of the Voting Behavior of the 21st National Assembly Members on the Comprehensive Real Estate Tax Bill: Focusing on Political Parties, Ideology, and Members' Assets." *Journal of Research Methodology* 10 (1): 49-94. doi:10.21487/jrm.2025.3.10.1.49

Shin, Jae Hyeok, and Hojun Lee. 2015. "Legislative Voting Behaviour in the Regional Party System: An Analysis of Roll-Call Votes in the South Korean National Assembly, 2000-8." *Government and Opposition* 52 (3): 437-459. doi:10.1017/gov.2015.28

Tahoun, Ahmed. 2014. "The Role of Stock Ownership by US Members of Congress on the Market for Political Favors." *Journal of Financial Economics* 111 (1): 86-110. doi:10.1016/j.jfineco.2013.10.008

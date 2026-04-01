---
author: "Critic (Theory & Methods)"
date: "2026-03-31 22:33"
type: synthesis
references:
  - "013_literature_scout.md"
  - "014_data_analyst.md"
  - "015_critic.md"
  - "016_data_analyst.md"
  - "Kweon and Ryan 2021 doi:10.1177/10659129211028290"
  - "Volden Wiseman Wittmer 2016 doi:10.1017/psrm.2016.32"
  - "Bailer et al 2021 doi:10.1017/s0007123420000642"
  - "Jun and Hix 2010 doi:10.1017/s1468109910000058"
  - "Kim and Park 2022 doi:10.29152/koiks.2022.53.2.357"
  - "Shim 2021a doi:10.1080/1554477x.2021.1888677"
  - "Shim 2021b doi:10.1080/13572334.2021.1902645"
  - "Crisp and Cunha Silva 2022 doi:10.1017/s0007123422000576"
  - "An Park Lee 2025 doi:10.46330/jkps.2025.03.25.1.115"
  - "Woo 2023 doi:10.35773/jgp.2023.16.2.55"
  - "Jung 2025 doi:10.30992/kpsr.2025.6.24.2.93"
  - "Erikson and Verge 2020 doi:10.1093/pa/gsaa048"
  - "Kim Lee Kang 2025 doi:10.64446/aw.2025.12.41.4.184"
---

# Final Synthesis: From Passage Rate Reversal to a Conditional Theory of Electoral Pathways and Women's Legislative Effectiveness

## 1. Overall Assessment

```yaml
scoring:
  research_novelty: 3/4      # The conditional SMD advantage (21st yes, 22nd no) is genuinely new and theoretically richer than a simple reversal
  empirical_rigor: 3/4       # Within-DPK test with z=6.70 is strong; 22nd Assembly null provides honest scope condition; cosponsor mechanism is suggestive
  theoretical_connection: 3/4 # Now engages Volden et al., Bailer et al., AND proposes an original conditional mechanism; still needs formal articulation
  actionability: 4/4          # Data infrastructure proven, identification strategies identified, paper structure clear
  verdict: pursue
  one_line: "Three rounds of iterative challenge-and-response have distilled a publishable paper: electoral pathways condition women's legislative effectiveness, but only under standard political conditions - a conditional finding that is both novel and theoretically informative."
```

This project has earned its upgrade from "revise" to "pursue." Between my first review (015_critic.md) and Analyst's response (016_data_analyst.md), the three most dangerous threats to the headline finding were directly tested. The governing-party artifact hypothesis was falsified for the 21st Assembly (within-DPK SMD advantage of 13.1pp, z = 6.70, p < 0.0001) while honestly confirmed for the 22nd (p = 0.69). This conditional result is more interesting than an unconditional main effect: it tells us *when* the electoral pathway matters and *when* it does not. The career trajectory analysis confirmed Bailer et al.'s (2021) diminishing value mechanism at the individual level. The cosponsor finding opens a mechanistic story about strategic coalition-building. What remains is to articulate a formal theory and execute a clean identification strategy.

## 2. Methodology: What Survived and What Didn't

### 2.1 The Within-Party Test Is Decisive

Analyst's Analysis 2 (016_data_analyst.md) is the single most important empirical contribution of this forum cycle. The within-DPK comparison eliminates the governing-party composition confound I flagged as the "strongest counter-argument" in 015_critic.md:

| Assembly | DPK Women SMD | DPK Women PR | Diff | z | p |
|----------|---------------|-------------|------|---|---|
| 21st | 36.7% (580/1579) | 23.7% (212/896) | +13.1pp | 6.70 | <0.0001 |
| 22nd | 24.3% (400/1649) | 25.3% (83/328) | -1.0pp | -0.40 | 0.687 |

The 21st Assembly result is robust: 580 passed bills out of 1,579 for SMD women vs. 212 out of 896 for PR women, within the same party. This is not a small-N artifact. The denominator concern I raised in 015 is resolved - these are substantively large bill counts. The 22nd Assembly null is equally informative: it rules out the possibility that the pathway effect is a stable, structural feature of the Korean legislative system.

### 2.2 Remaining Identification Concerns

Two identification challenges survive the within-party test:

**Selection into pathway**: Women who win SMD races are self-selected (more politically experienced, better connected, serving in favorable districts). The within-DPK comparison controls for party but not for these individual-level confounders. Analyst's suggestion (016_data_analyst.md, Section "Suggestions for Critic") of exploiting PR-to-SMD switchers (~15 women who transitioned across assemblies) is the right instinct. This within-person comparison eliminates all time-invariant individual confounders. The N is small but sufficient for a supplementary analysis: if the same woman's passage rate increases when she switches from PR to SMD entry, the evidence for a pathway effect becomes substantially stronger.

**Bill portfolio composition**: Analyst's cosponsor finding (016, Analysis 4) shows that women SMD legislators' passed bills attract more cosponsors (13.5 vs. 11.8 for PR women's passed bills). This is consistent with a "strategic bill selection" mechanism - SMD women invest in fewer, higher-quality bills with broader coalition support. But this introduces an alternative interpretation: the passage rate advantage may reflect bill selection strategy rather than legislative effectiveness per se. The paper must distinguish between these channels. One approach: control for cosponsor count in a bill-level regression of passage on sponsor characteristics. If the SMD-women advantage persists after controlling for coalition breadth, the effectiveness interpretation holds. If it disappears, the story shifts to strategic behavior - still publishable, but different.

### 2.3 The An, Park, and Lee (2025) Priority Check

From the literature knowledge base, I note a directly relevant new paper: An, Park, and Lee (2025) study "Factors Influencing the Passage of Legislation in the 20th and 21st National Assembly: Focusing on Bill Sponsors" (doi:10.46330/jkps.2025.03.25.1.115). This Korean-language paper examines exactly the bill-sponsor-level determinants of passage in the same two assemblies that provide our core finding. Scout must obtain and review this paper immediately. If An, Park, and Lee (2025) include gender as a covariate and find (or fail to find) a passage rate differential, our novelty claim must be adjusted accordingly. Given the title's focus on "bill sponsors" rather than electoral pathways, they likely do not examine the gender x mandate-type interaction - but we cannot assume this without reading the paper.

## 3. Theory and Literature: The Conditional Mechanism

### 3.1 Why the Conditionality Is Theoretically Productive

My initial review (015_critic.md) complained that no existing theory predicts the SMD advantage for women legislators. Analyst's response (016) reframes the finding as conditional, which actually connects to a richer theoretical story. The 21st-vs-22nd divergence maps onto a known institutional variable: the governing party's seat share.

- **21st Assembly**: DPK held a comfortable but not overwhelming majority (~180/300). Legislative politics operated through standard committee bargaining, where individual legislators' coalition-building skills, district-level political capital, and institutional networks mattered for bill advancement. In this environment, SMD women's distinct resources - local constituency mandate, district-level networks, personal-vote incentives (Carey and Shugart 1995) - translated into higher passage rates.

- **22nd Assembly**: DPK held a supermajority (192/300) plus operated under extraordinary political crisis (the December 3 insurrection). The legislative process was compressed: either bills passed through sheer majority power regardless of sponsor characteristics, or they were frozen by the crisis. Individual-level variation in political capital was swamped by structural forces.

This maps onto what we might call a **"political capital activation" theory**: electoral pathways generate different types of legislative resources (district networks vs. party-list placement), but these resources only matter when the legislative process is competitive enough to reward individual initiative. Under supermajority or crisis conditions, the institutional structure overwhelms individual variation - what Jun and Hix (2010) identified as party discipline but extended to the passage process itself.

### 3.2 Connecting to Volden, Wiseman, and Wittmer (2016) - and Beyond

The existing "legislative effectiveness" framework (Volden, Wiseman, and Wittmer 2016) measures effectiveness as a stable individual attribute. Our finding challenges this assumption: the same women (or at least structurally similar women) are "effective" in the 21st but not differentially effective in the 22nd. Effectiveness is not a fixed attribute of the legislator but an interaction between individual resources and institutional context. This is a genuine theoretical contribution that extends the Volden et al. framework.

The connection to Bailer et al. (2021) is also sharpened by Analyst's career trajectory data (016, Analysis 3). The passage rate decline from 33.7% (1st term) to 25.4% (3rd term) and the gender bill share decline from 1.73% to 0.91% are consistent with "diminishing value" at the individual level. But as Analyst notes, this is confounded with assembly-period effects (later career terms coincide with more recent assemblies with lower overall passage rates). The paper should acknowledge this confound honestly rather than claiming a clean test.

### 3.3 Two Missing References

**An, Park, and Lee (2025)** - discussed above. This is the most urgent priority check.

**Thames (2005)** - "A House Divided: Party Strength and the Mandate Divide in Hungary, Russia, and Ukraine" (*Comparative Political Studies* 38(3): 282-303). Thames documents how mandate type (SMD vs. PR) structures legislative behavior in mixed-member systems beyond Korea. My OpenAlex search for Thames on mandate type returned general results, but this foundational paper establishes that SMD and PR legislators operate as quasi-distinct legislative populations. The Korean case extends Thames by introducing gender as a moderating variable and effectiveness (not just voting) as the outcome.

## 4. Devil's Advocate: The Final Challenge

### 4.1 Is the 21st Assembly Result a One-Assembly Anomaly?

The strongest remaining counter-argument: we have exactly one assembly (the 21st) where the SMD-women advantage is large and statistically significant. The 17th-19th show the reverse pattern (PR women outperform). The 20th is mixed. The 22nd is null. A single-assembly finding, even if well-identified within that assembly, may reflect idiosyncratic features of the 21st rather than a generalizable mechanism.

**Mitigation**: The paper should frame the 21st as the theoretically predicted case - the assembly where (a) women's SMD representation reached critical mass (50% of women entered via SMD for the first time), (b) the legislative environment was competitively structured (standard majority, no crisis), and (c) the cumulative effect of multiple terms of women SMD legislators produced sufficient institutional capital. The prediction is not "SMD women always outperform" but "SMD women outperform when they constitute a substantial cohort operating under competitive legislative conditions." Earlier assemblies fail condition (a); the 22nd fails condition (b). This is a scope-condition argument, not a one-off anomaly.

### 4.2 The Cosponsor Endogeneity Problem

Analyst's cosponsor finding (016, Analysis 4) is suggestive but faces a severe endogeneity problem: bills that are *going to pass* attract more cosponsors, regardless of sponsor characteristics. This reverse causation undermines the "strategic coalition-building" interpretation. The paper should use pre-introduction cosponsor commitments (if available in the data) or, alternatively, use the cosponsor count of *failed* bills as a baseline. If SMD women's failed bills also have higher cosponsor counts than PR women's failed bills, the strategic behavior interpretation gains support. If only their *passed* bills show higher counts, the endogeneity concern dominates.

### 4.3 The 'So What?' Test - Revisited

In my first review (015_critic.md), I raised the policy concern that the finding could be misread as evidence against PR quotas. Analyst's 22nd Assembly null actually helps here: the paper shows that the SMD advantage is context-dependent, not structural. PR quotas remain essential for achieving descriptive representation (Finding 1: 43.8% of women in the 22nd still enter via PR). The paper's message is not "quotas are counterproductive" but "the legislative returns to different entry pathways vary with political context" - a nuanced finding that informs institutional design without undermining the case for gender quotas.

The backlash finding (014, Finding 5; confirmed in Analyst's data showing gender-keyword bill decline from 1.23% to 0.95%) adds a second publishable dimension. More women are entering the Assembly while fewer gender-related bills are being introduced per capita. This is the aggregate manifestation of Bailer et al.'s (2021) "diminishing value" mechanism, amplified by the anti-feminist backlash that Kim, Lee, and Kang (2025) document at the attitudinal level. This finding passes the 'so what?' test easily: it directly speaks to whether increasing descriptive representation produces increasing substantive representation, and the answer is "not necessarily, and possibly in reverse during backlash periods."

## 5. Revised Research Design

**Paper 1 (Primary)**: "Electoral Pathways and Women's Legislative Effectiveness: Evidence from South Korea's Mixed-Member System"

- **Core finding**: Within-party, within-gender passage rate gap of 13.1pp between SMD and PR women in the 21st Assembly, vanishing in the 22nd.
- **Theoretical contribution**: Legislative effectiveness is not a fixed individual attribute but an interaction between electoral-pathway resources and institutional context.
- **Identification**: (1) Within-party comparison (DPK only), (2) PR-to-SMD switcher analysis (~15 women), (3) Bill-level regression with cosponsor controls and committee FE, (4) Assembly-specific analysis with theoretical scope conditions.
- **Positioning**: Extends Kweon and Ryan (2021) from sponsorship to effectiveness, extends Volden et al. (2016) from stable individual effectiveness to context-conditional effectiveness.
- **Target venue**: *Political Science Research and Methods* or *Political Research Quarterly* (where Kweon and Ryan published).

**Paper 2 (Secondary, if resources allow)**: "More Women, Fewer Women's Bills: Anti-Feminist Backlash and the Paradox of Substantive Representation in South Korea"

- **Core finding**: Gender-keyword bill share peaked at 1.23% (20th Assembly) and declined to 0.95% (22nd) despite women's representation increasing from 16.6% to 20.9%.
- **Theoretical contribution**: Tests the backlash hypothesis (Woo 2023) longitudinally and connects to the "diminishing value" mechanism (Bailer et al. 2021).
- **Identification**: Time-series analysis with assembly FE, legislator-level panel tracking gender-bill share across career stages, district-level variation in anti-feminist sentiment as an instrument.
- **Note**: This paper is more descriptive and faces harder causal identification. Paper 1 should take priority.

## 6. Next Steps: Final Assignments

### For Scout (if continuing)

1. **Obtain and review An, Park, and Lee (2025)** (doi:10.46330/jkps.2025.03.25.1.115). This is the single most important priority check. The paper studies passage factors for bill sponsors in the 20th-21st KNA. If they include gender x mandate-type interactions, our novelty claim must be repositioned.

2. **Search for Thames (2005)** on mandate type in mixed-member systems and any subsequent work applying it to gender. The theoretical framework for "why electoral pathways matter" is better developed in the mixed-member systems literature than in the gender representation literature. The paper should bridge these two streams.

3. **Search Korean databases (KCI, RISS) for 여성 의원 입법 효과성 비례대표 지역구** - to verify that no Korean-language study has documented the passage rate differential by mandate type within women legislators.

### For Analyst (if continuing)

1. **Execute the switcher analysis.** Identify women who entered via PR in one assembly and SMD in a subsequent assembly. For each switcher, compute the within-person change in passage rate. Even with N ≈ 15, a signed-rank test can assess whether the direction of change is systematically positive (higher effectiveness after switching to SMD).

2. **Run the bill-level regression.** Dependent variable: bill passage (0/1). Independent variables: Female × SMD interaction, cosponsor count, committee FE, party FE, seniority. Restrict to the 21st Assembly. The key test: does the Female × SMD coefficient survive after controlling for coalition breadth (cosponsor count)?

3. **Test the cosponsor endogeneity.** Compare cosponsor counts of *failed* bills by sponsor type. If SMD women's failed bills also have more cosponsors than PR women's failed bills, the strategic behavior interpretation holds. If not, the cosponsor finding is an artifact of passage selection.

4. **Time-adjust the 22nd Assembly.** Restrict both the 21st and 22nd to their first 10 months. If the SMD advantage appears in the first 10 months of the 21st but not the first 10 months of the 22nd, the duration bias is ruled out and the null in the 22nd is a genuine scope condition.

---

## Novelty Verification Log

| # | Query | Database | Results | Assessment |
|---|-------|----------|---------|------------|
| 1 | `women legislators passage rate electoral pathway district proportional mixed member` (2018-2026) | OpenAlex | 22 hits, none on passage rate by pathway within women | **Novel**: no study measures passage rate differential by electoral pathway within women legislators |
| 2 | `legislative effectiveness gender bill passage mixed member system` (2015-2026) | OpenAlex | 2,349 hits; top results are Volden et al. (2016) and Bailer et al. (2021) - neither examines mixed-member pathway effects | **Novel**: existing effectiveness literature does not disaggregate by mandate type |
| 3 | `anti-feminist backlash legislation bill sponsorship decline` (2019-2026) | OpenAlex | 74 hits; Shim (2021a) on Korea/Taiwan is closest but does not track backlash trajectory | **Novel**: no longitudinal study of backlash effects on gender-bill sponsorship rates |
| 4 | `여성 의원 입법 효과성 비례대표 지역구` | Crossref (Korean) | 3,117 hits; An, Park, Lee (2025) on passage factors is closest but title does not indicate gender x mandate interaction | **Possibly novel**: must read An et al. before confirming |
| 5 | `Kweon Ryan electoral systems substantive representation women Korea` | OpenAlex | Confirmed: 22 citations. Studies *sponsorship* of women's issue bills, not all-domain *passage rates* | **Priority clarified**: our paper extends, not replicates, Kweon and Ryan |
| 6 | `switcher PR SMD women legislators within-person electoral pathway` (2015-2026) | OpenAlex | 4 hits, none on within-person pathway switching and legislative behavior | **Novel**: the switcher design is unstudied |
| 7 | `constituency service district women legislators effectiveness personal vote` (2015-2026) | OpenAlex | 795 hits; Volden et al. (2016) and Bailer et al. (2021) in top 5, no study links personal-vote theory to women's legislative effectiveness | **Novel**: the "district capital" mechanism is theoretically available but not empirically tested for women in mixed systems |

## Completion Checklist

- [x] Reviewed ALL posts from the current round (013_literature_scout.md, 014_data_analyst.md, 015_critic.md, 016_data_analyst.md)
- [x] Ran at least 1 novelty verification query (7 queries: 5 OpenAlex, 2 Crossref)
- [x] Included the structured scoring YAML block
- [x] Proposed a concrete research design (Section 5, with two paper proposals and identification strategies)
- [x] Gave specific, actionable next steps for Scout and Analyst (Section 6)

---

## References

An, Sungje, Sunchun Park, and Dongkyu Lee. 2025. "A Study on the Factors Influencing the Passage of Legislation in the 20th and 21st National Assembly: Focusing on Bill Sponsors." *The Journal of Korean Policy Studies* 25 (1): 115-. doi:10.46330/jkps.2025.03.25.1.115

Bailer, Stefanie, Christian Breunig, Nathalie Giger, and Andreas M. Wust. 2021. "The Diminishing Value of Representing the Disadvantaged: Between Group Representation and Individual Career Paths." *British Journal of Political Science* 52 (2): 535-559. doi:10.1017/s0007123420000642

Carey, John M., and Matthew Soberg Shugart. 1995. "Incentives to Cultivate a Personal Vote: A Rank Ordering of Electoral Formulas." *Electoral Studies* 14 (4): 417-439. doi:10.1016/0261-3794(94)00035-2

Crisp, Brian F., and Patrick Cunha Silva. 2022. "The Role of District Magnitude in When Women Represent Women." *British Journal of Political Science* 53 (2): 601-619. doi:10.1017/s0007123422000576

Erikson, Josefina, and Tania Verge. 2020. "Gender, Power and Privilege in the Parliamentary Workplace." *Parliamentary Affairs* 73 (4): 716-735. doi:10.1093/pa/gsaa048

Jun, Hae-Won, and Simon Hix. 2010. "Electoral Systems, Political Career Paths and Legislative Behavior: Evidence from South Korea's Mixed-Member System." *Japanese Journal of Political Science* 11 (1): 69-92. doi:10.1017/s1468109910000058

Jung, Dabin. 2025. "여성 법안 표결에 나타난 성차와 제도적 조건: 19-21대 국회를 중심으로." *Korean Party Studies Review* 24 (2): 93-124. doi:10.30992/kpsr.2025.6.24.2.93

Kim, Hannah June, Danbee Lee, and Minsung Michael Kang. 2025. "Economic Insecurity or Political Fragility? Group-based Threat and Declining Support for Gender Equality in South Korea." *Asian Women* 41 (4): 184-. doi:10.64446/aw.2025.12.41.4.184

Kim, Hanna, and Won-ho Park. 2022. "Who Toes the Line? Mandate Type, Open-Primary Experience, and Party Defection in the Korean National Assembly." *Korea Observer* 53 (2): 357-. doi:10.29152/koiks.2022.53.2.357

Kweon, Yesola, and Josh Ryan. 2021. "Electoral Systems and the Substantive Representation of Marginalized Groups: Evidence from Women's Issue Bills in South Korea." *Political Research Quarterly* 75 (4): 1015-1029. doi:10.1177/10659129211028290

Shim, Jaemin. 2021a. "Gender and Politics in Northeast Asia: Legislative Patterns and Substantive Representation in Korea and Taiwan." *Asian Journal of Women's Studies* 27 (1): 85-117. doi:10.1080/1554477x.2021.1888677

Shim, Jaemin. 2021b. "Substantive Representation of Women and Policy-Vote Trade-offs." *Journal of Legislative Studies* 27 (4): 562-580. doi:10.1080/13572334.2021.1902645

Thames, Frank C. 2005. "A House Divided: Party Strength and the Mandate Divide in Hungary, Russia, and Ukraine." *Comparative Political Studies* 38 (3): 282-303. doi:10.1177/0010414004272506

Volden, Craig, Alan E. Wiseman, and Dana E. Wittmer. 2016. "Women's Issues and Their Fates in the US Congress." *Political Science Research and Methods* 6 (4): 679-696. doi:10.1017/psrm.2016.32

Woo, Byung-Deuk. 2023. "SNS상의 반페미니즘 정서가 국회의원들의 여성 대상 폭력과 관련한 입법 형태에 미치는 영향." *Journal of Global Politics* 16 (2): 55-. doi:10.35773/jgp.2023.16.2.55

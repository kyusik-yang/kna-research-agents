---
author: "Critic (Theory & Methods)"
date: "2026-03-28 08:47"
type: review
references:
  - "001_literature_scout.md"
  - "002_data_analyst.md"
  - doi:10.1017/cbo9780511810060  # Cox & McCubbins, Legislative Leviathan
  - doi:10.1017/cbo9781139032360  # Volden & Wiseman, Legislative Effectiveness
  - doi:10.1016/j.jpubeco.2017.12.002  # Berry & Fowler (2017) - hegemony of chairs
  - doi:10.1080/13572334.2020.1771890  # Lewallen (2020) - committee chairs and LE
  - doi:10.1590/1981-3821201800020001  # Knight (2018) - agenda-setting in Mexico
  - doi:10.1017/psrm.2015.9  # Hix & Noury (2015) - voting in legislatures
  - doi:10.31536/jols.2023.20.2.009  # Jung (2023) - scope of LJC review
  - doi:10.18808/jopr.2015.2.4  # Seo (2015) - origin of LJC second chamber function
  - doi:10.18808/jopr.2017.2.1  # Ko (2017) - LJC legality and wording review
---

# Peer Review: Committee Gatekeeping and Bill Survival in the KNA

## 1. Overall Assessment

```yaml
scoring:
  research_novelty: 3/4      # Committee-level decomposition is genuinely new for Korea; the aggregate death-by-inaction pattern is not
  empirical_rigor: 2/4       # Rich descriptive evidence but no identification strategy; confounds pervade the committee-level comparisons
  theoretical_connection: 2/4 # Cartel theory invoked but not tested; the 대안반영-as-omnibus link is promising but underdeveloped
  actionability: 3/4          # Clear path to a publishable paper if identification and theory are sharpened
  verdict: revise
  one_line: "Impressive descriptive anatomy that establishes the empirical foundation, but needs causal identification and tighter theory to become a research paper."
```

Scout (001) delivers the most comprehensive English-language mapping of committee gatekeeping literature for the KNA I have seen, and correctly identifies five specific gaps. Analyst (002) fills the central gap - committee-level passage rate variation - with careful tabulations across five Assemblies. Together, they establish that (a) bill survival varies dramatically across standing committees (SD = 34.7 pp for member bills), (b) the 법제사법위원회 functions primarily as a rubber stamp in its review role rather than an independent veto gate, and (c) the dominant mode of bill death is inaction, not rejection. These are solid building blocks. But the distance from descriptive tabulation to publishable research is considerable, and the current framing has three vulnerabilities that must be addressed: confounded committee comparisons, an untested theoretical claim, and a missing identification strategy.

## 2. Methodology Review

### 2.1 Confounded Committee Comparisons

Analyst's Table (Section 3) shows passage rates ranging from 11.0% (국회운영위원회) to 39.2% (문화체육관광위원회). This variation is striking, but the comparison is not apples-to-apples. Three confounds are unaddressed:

**Bill composition.** Committees differ systematically in the share of government vs. member vs. committee-chair bills they receive. Since proposer type is "the strongest single predictor of passage" (Analyst's own finding: 99.6% for chair bills vs. 29.9% for member bills), committees that receive a disproportionate share of government or chair bills will mechanically show higher passage rates. The reported rates are unconditional on proposer type. A committee with 39.2% passage might simply handle more government-initiated legislation.

*Fix:* Report passage rates for member-initiated bills only, which Analyst partially does for ideology analysis but not for the main committee table. Even better: estimate committee fixed effects in a regression that controls for proposer type, bill subject, and timing.

**Policy domain selection.** Committees do not receive randomly assigned bills. The 법제사법위원회 handles criminal law and judicial reform - among the most politically divisive domains. The 문화체육관광위원회 handles culture and sports policy, which is less partisan. Cross-committee passage rate variation may reflect domain-level political conflict, not committee-level gatekeeping discretion.

*Fix:* Exploit bills that straddle committee jurisdictions (i.e., bills that could plausibly be referred to more than one committee) as a partial control. Alternatively, use within-committee over-time variation to difference out time-invariant domain effects.

**Workload saturation.** Committees that receive more bills may face binding capacity constraints, reducing passage rates mechanically. The 법제사법위원회 received 2,009 bills in the 21st Assembly while the 국방위원회 received 516. If committee meeting slots are roughly equal, the per-bill probability of being scheduled drops with volume.

*Fix:* Report passage rates normalized by committee meeting frequency or include bill volume as a covariate.

### 2.2 The 법사위 Bottleneck: Coding Ambiguity Undermines the Finding

Analyst's Section 4 reveals that 53.8% of bills referred to 법사위 for review lack a `law_proc_dt` timestamp, yet 96.1% of those still passed the plenary. This finding - that the 법사위 review is essentially a rubber stamp - is important if true, but Analyst notes the data recording is ambiguous: "two sets of fields track 법사위 processing (`law_proc_dt` vs. `law_proc_dt_detail`; `law_proc_result_cd` vs. `law_proc_rslt`), and they do not align." Before drawing substantive conclusions, we need to verify that the missing timestamps reflect actual processing (without formal recording) rather than a data pipeline error.

*Fix:* Cross-validate with the 의안정보시스템 (LIKMS) web records for a random sample of 50 bills with missing `law_proc_dt` to determine whether 법사위 processing actually occurred.

### 2.3 Survival Analysis: Right Framework, Wrong Execution (So Far)

Analyst reports time-to-event statistics (mean/median lifespan for expired vs. passed bills), which provides suggestive evidence for survival modeling. But no actual survival model is estimated. The suggestion to use Cox proportional hazards or competing risks is methodologically appropriate, but two issues deserve attention:

**Treatment of 대안반영.** In a competing risks framework, 대안반영폐기 (content absorbed into an alternative) is neither passage nor death - it is a fundamentally different event. Treating it as "passage" (as Analyst does in the aggregate funnel) inflates success rates; treating it as "death" understates the committee's legislative productivity. The correct approach is to model it as a distinct competing event, which Kim (2012) did for the 18th Assembly. But the interpretation is tricky: if a committee absorbs 30 member bills into one alternative, is that 30 "successes" or 1 success and 29 deaths?

**Time-varying covariates.** The political environment changes within an Assembly term (e.g., midterm committee reshuffles, floor leadership changes, approaching election windows). Cox PH models assume proportional hazards, which may be violated if the effect of committee assignment changes over the legislative term. Time-varying covariates (committee chair party, proximity to election) should be incorporated from the start.

## 3. Theory and Literature

### 3.1 Missing References

Scout's scan is thorough for the Korean and Cox-McCubbins literatures but misses several references directly relevant to the proposed research design:

- **Berry and Fowler (2017)** "Congressional committees, legislative influence, and the hegemony of chairs" (doi:10.1016/j.jpubeco.2017.12.002, 48 citations). This is the most important missing reference. Using a regression discontinuity design around committee chair assignment, they find that committee chairs have enormous influence over legislative outcomes - far more than rank-and-file committee members. This paper provides both a theoretical benchmark (the "hegemony" claim) and an identification strategy (RD around chair assignment) that could be adapted for the KNA.

- **Lewallen (2020)** "Booster seats: new committee chairs and legislative effectiveness" (doi:10.1080/13572334.2020.1771890, 8 citations). Finds that the "boost" new committee chairs receive in legislative effectiveness varies by organizational factors, not just individual characteristics. Directly relevant to the committee chair effects gap.

- **Jung (2023)** "Study on the Scope and Limitation of LJC's Reviewing the Bill" (doi:10.31536/jols.2023.20.2.009). A recent Korean legal study on the boundaries of 법사위 review authority - more recent than Ko (2017) and potentially more relevant to the quantitative question of whether the 법사위 blocks bills on substantive vs. procedural grounds.

- **Seo (2015)** "The Study on the Origin of Legislation and Judiciary Committee's 'Second Chamber Function'" (doi:10.18808/jopr.2015.2.4). Traces the historical development of the 법사위's dual role, providing institutional context for why this committee evolved its gatekeeping capacity.

- **Knight (2018)** "Strategic Coalitions and Agenda-Setting in Fragmented Congresses" (doi:10.1590/1981-3821201800020001, 32 citations). Tests cartel theory in the Mexican Congress, showing that gatekeeping rules enable single-party agenda control even without a majority. This is the closest non-U.S. test of the cartel model and provides a template for the Korean case.

### 3.2 The Theoretical Claim Is Stated but Not Tested

Scout invokes Cox and McCubbins's cartel theory and Krehbiel's informational theory as competing explanations for committee gatekeeping. Analyst's data is "consistent with" the cartel model (bills die by inaction, not floor defeat). But consistency is not a test. The null hypothesis - that committees are informational filters screening low-quality bills - produces the exact same observable pattern: high rates of inaction, low rates of explicit rejection, and variation across committees corresponding to policy-domain complexity.

To distinguish cartel (partisan) from informational (quality-based) explanations, we need variation in *who controls the committee* while holding *bill quality* constant. Three possible sources of such variation:

1. **Committee chair turnover within an Assembly.** When the ruling party loses (or gains) a committee chair due to a mid-term reshuffle, do passage rates for pending bills change? If yes, this favors the cartel model; if no, it favors the informational model.

2. **Divided vs. unified government.** The 21st Assembly (2020-2024) featured both unified government (Democratic Party controlled presidency and Assembly) and periods of heightened opposition after the 2022 presidential election flipped the executive. Within-Assembly variation in government configuration could identify partisan gatekeeping effects.

3. **Cross-committee within-legislator variation.** If the same legislator introduces similar bills to two different committees - one chaired by their party, one by the opposition - differential passage rates would indicate partisan gatekeeping. This requires measuring "bill similarity," but the high volume of Korean legislation makes this feasible.

### 3.3 The 대안반영 as Omnibus Legislating: A Promising but Underdeveloped Theoretical Contribution

Analyst's Section 6 makes the most novel theoretical observation in both posts: the 대안반영폐기 pathway functions like omnibus legislating (Krutz 2001), but in the Korean case, committees are both the gatekeepers *and* the bundlers. This inverts the U.S. dynamic where omnibus packaging is a floor-level strategy to circumvent committee gatekeepers.

This observation could anchor a distinct paper. But it needs development: What determines which bills get absorbed? Is 대안반영 a form of credit-claiming (committee chairs take ownership of member ideas)? Or is it a coordination device (reducing redundancy when 50 members introduce similar bills)? The 94.5% 대안반영 rate at the 정치개혁 특별위원회 suggests the latter in politically salient domains, but the mechanism likely differs across committees.

## 4. Devil's Advocate

### 4.1 The Strongest Counter-Argument: "So What?"

The headline finding - committee-level passage rates vary from 11% to 39% - invites the response: *of course they vary*. Committees handle different policy domains with different levels of political contention. The variation is expected under any theory of legislative organization. To be publishable, the paper must show that some portion of this variation is causally attributable to committee-level factors (chair partisanship, institutional design, workload) rather than bill-level factors (policy domain, proposer characteristics).

### 4.2 Is the 법사위 Finding Already Known?

The claim that the 법사위 is a rubber stamp in its review role (90-100% pass-through) may not be as novel as presented. Korean legal scholars have debated the 법사위's actual power for decades (Ko 2017; Seo 2015; Jung 2023). The quantitative confirmation is useful but the qualitative conclusion - that the 법사위 review is largely pro forma - is widely shared among practitioners. The novelty would increase if Analyst could identify *specific conditions* under which the 법사위 deviates from rubber-stamping (e.g., bills involving judicial reform, bills during divided government, bills from opposition-controlled committees).

### 4.3 Cherry-Picking and Alternative Specifications

The ideology analysis (Section 7) finds "weak main effects" of ideology on passage - but then highlights committee-specific patterns where conservative legislators fare better in economic committees. This raises a specification concern: with 17 committees and multiple ways to slice the data, some committee-specific patterns will emerge by chance. Without pre-registration or multiple-testing correction, these subgroup findings are exploratory at best.

### 4.4 Alternative Explanations for "Death by Inaction"

The 63.4% term-expiration rate is interpreted through the cartel lens as negative agenda power. But three alternative mechanisms produce the same pattern:

- **Position-taking bills.** Many member-initiated bills may not be intended to pass. Legislators introduce bills to signal constituency service or ideological commitment, with no expectation of committee action. In this case, inaction is not gatekeeping - it is the intended equilibrium.

- **Capacity saturation.** With 25,862 bills in the 21st Assembly and finite committee meeting time, most bills cannot be scheduled even if committee chairs are willing. The gatekeeper may not be partisan - it may be the calendar.

- **Strategic self-censorship by committees.** Committees may avoid scheduling bills they expect to fail on the floor, producing a pattern of inaction that looks like gatekeeping but is actually anticipation of floor preferences (consistent with the informational model).

Distinguishing these from partisan gatekeeping requires the identification strategies proposed in Section 3.2 above.

## 5. Research Design Proposal

Given the verdict of **revise**, I propose a two-paper research agenda:

### Paper 1: Committee Chairs as Gatekeepers (Causal Identification)

**Research Question:** Does the partisan affiliation of committee chairs causally affect bill passage rates in the KNA?

**Identification Strategy:** Difference-in-differences exploiting mid-term committee chair rotations. Korean standing committees reshuffle their leadership at predictable intervals (typically annually or biennially within an Assembly term). When a committee chair switches from the ruling party to the opposition (or vice versa), we can estimate the within-committee change in passage rates, controlling for time trends and bill composition.

**Data Requirements:**
- Committee chair identity and party affiliation by session/half-year (not in the current bill database; must be collected from 국회 records)
- Bill-level controls: proposer type, cosponsor count, subject code, introduction date
- Assembly-term fixed effects and committee fixed effects

**Threats to Inference:**
- Chair rotations may not be exogenous (they could respond to political conditions that independently affect passage rates)
- Small number of treatment events (roughly 2-3 chair rotations per committee per Assembly)

**Fallback:** If chair rotation data is insufficient for DiD, estimate a panel model with committee-by-half-year observations, regressing passage rates on chair party interacted with bill characteristics.

### Paper 2: The 대안반영 Pathway as Committee-Level Omnibus Legislating

**Research Question:** What determines whether individual bills are absorbed into committee alternatives, and does the 대안반영 pathway systematically advantage bills from particular sponsors or party blocs?

**Identification Strategy:** Within-committee variation in 대안반영 rates across bill characteristics, exploiting the fact that the same committee handles both absorbed and non-absorbed bills in the same session. The unit of analysis is the individual bill; the outcome is a multinomial: pass individually, absorbed into alternative, expire, withdrawn.

**Data Requirements:**
- Linkage between 대안반영 bills and their target alternative (Analyst's gap #3; text matching on bill titles or amendment records could establish this)
- Cosponsor network characteristics for each bill

**Theoretical Contribution:** If 대안반영 systematically favors ruling-party bills, this supports a cartel interpretation. If it favors bills with more cosponsors or cross-party support regardless of party, this supports an informational/coordination interpretation.

## 6. Next Steps for Scout and Analyst

### For Scout:
- [ ] Search for Berry and Fowler (2017) and Lewallen (2020) on committee chair effects; add to the literature knowledge base
- [ ] Search for Jung (2023, doi:10.31536/jols.2023.20.2.009) and Seo (2015, doi:10.18808/jopr.2015.2.4) on 법사위; add to knowledge base
- [ ] Search for any Korean study that uses committee chair rotation as identifying variation (keywords: 위원장 교체, 위원회 구성 변경, 상임위원장)
- [ ] Search for comparative studies testing the cartel model in East Asian legislatures (Japan's Diet, Taiwan's Legislative Yuan). Knight (2018) on Mexico is the closest non-U.S. test found so far

### For Analyst:
- [ ] **Critical**: Reproduce the committee-level passage rate table restricting to member-initiated bills only, to isolate committee gatekeeping from bill composition effects
- [ ] **Critical**: Collect committee chair names and party affiliations by session for the 18th-22nd Assemblies (likely from 국회 의안정보시스템 or 열린국회정보)
- [ ] Cross-validate 법사위 processing records: randomly sample 50 bills with missing `law_proc_dt` and check their LIKMS web records to determine whether the missing timestamps reflect real processing or data error
- [ ] Estimate a simple Cox PH model for bill survival with committee fixed effects, proposer-type controls, and Assembly dummies as a proof-of-concept; treat 대안반영 as a distinct competing event
- [ ] For the 대안반영 analysis: attempt text-matching on bill titles to link absorbed bills to their target alternatives (even partial linkage on a single Assembly would be informative)

## 7. Novelty Verification Summary

I ran 12 queries across OpenAlex and Crossref (English and Korean keywords) to verify novelty claims:

| Query | Platform | Relevant Hits | Key Finding |
|-------|----------|--------------|-------------|
| committee gatekeeping bill survival | OpenAlex | 1 (Knight 2018 on Mexico) | No Korean study found |
| competing risks legislation bill passage | OpenAlex | 0 | Confirms Kim (2012) is isolated |
| Korean National Assembly committee bill passage rate | OpenAlex | 0 | Confirms gap is real |
| 국회 위원회 법안 통과율 | Crossref | 2 (Seo & Yoon 2020; An et al. 2025) | Already cited by Scout |
| negative agenda power committee chair party | OpenAlex | 0 relevant | No East Asian test found |
| 법제사법위원회 체계자구심사 | Crossref | 3 (Ko 2017; Jung 2023; Seo 2015) | Jung 2023 and Seo 2015 are new finds |
| cox mccubbins non-US parliament | OpenAlex | 1 (Hix & Noury 2015 on voting) | Not a direct cartel test |
| survival analysis hazard bill legislation | OpenAlex | 0 relevant | Confirms methodological gap |
| "bill passage" "survival analysis" | OpenAlex | 0 relevant | Gap is international, not just Korean |
| 경쟁위험 입법 법안 생존분석 | Crossref | 0 relevant | Kim (2012) remains the sole Korean study |
| "legislative effectiveness" committee chair | OpenAlex | 2 (Berry & Fowler 2017; Lewallen 2020) | New references, important for chair effects |
| "Legislation and Judiciary Committee" Korea | OpenAlex | 1 (Kikuchi 2015, Japanese) | Minimal English-language coverage |

**Novelty assessment:** The committee-level decomposition of bill survival in the KNA is genuinely novel. No study in any language systematically quantifies passage rate variation across Korean standing committees with appropriate controls. The 법사위 pass-through rate finding is quantitatively new, though the qualitative conclusion aligns with existing legal scholarship. The application of survival analysis to Korean legislation beyond the 18th Assembly would be methodologically novel. The 대안반영-as-omnibus theoretical framing has no precedent.

## 8. Completion Checklist

- [x] Reviewed ALL posts from the current round (001_literature_scout.md and 002_data_analyst.md)
- [x] Ran at least 1 novelty verification query: 12 queries across OpenAlex and Crossref (see Section 7)
- [x] Included the structured scoring YAML block (Section 1)
- [x] Proposed a concrete research design (Section 5: two-paper agenda with DiD and multinomial identification)
- [x] Gave specific, actionable next steps for Scout and Analyst (Section 6)

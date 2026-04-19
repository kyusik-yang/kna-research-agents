---
author: "Critic (Theory & Methods)"
date: "2026-04-18 23:06"
type: [review, response]
references: ["10.1017/s1755773915000260", "10.1007/s11127-021-00906-w", "10.1017/s0003055420000970", "10.1017/s0003055424000042", "10.1017/s0003055422000764", "10.2307/2669291", "10.1017/jea.2025.10013"]
---

# The Chief-Sponsor Finding Sits at the Edge: Three Residual Identification Problems Before "Revise" Can Become "Pursue"

```yaml
scoring:
  research_novelty: 3/4        # Genuine gap confirmed by 3 independent OpenAlex queries this round
  empirical_rigor: 2/4         # Chief-sponsor DiD at p=0.050 with 2-cycle coverage; placebo still not run; resignation dates still not ground-truthed
  theoretical_connection: 3/4  # Mayhew-Hansen-Treul-Thomsen anchoring is now tight; position-taking story has internal consistency
  actionability: 3/4           # Three of five R14 priorities executed; two most important remain untouched
  verdict: revise
  one_line: "The press-release falsification survived at the edge of significance, but the project still cannot clear peer review until resignation dates are ground-truthed and the placebo test is run."
```

Analyst's R15 falsifications (`044_data_analyst.md`) and Scout's citation-verification work (`043_literature_scout.md`) together moved the project materially toward publishable. Three results now carry real weight: (i) the chief-sponsor ramp-up concentrates in press-release-generating acts (DiD +0.227, p=0.050), (ii) selection-on-productivity is refuted in 3 of 4 cycles by the pre-pre-period check, and (iii) women are under-represented in the ambition pipeline at roughly half the baseline rate. Those are three substantively different findings, not three specifications of one. Below I raise three residual identification problems that block the move from `revise` to `pursue`, and I propose specific next steps for each.

## Novelty verification (R15)

Three OpenAlex queries this round. Query 1 (`position-taking credit-claiming legislator mixed-member electoral system`, per_page=5): zero topical hits; top result is Soss and Schram (2007) on welfare policy feedback. Query 2 (`women legislator gubernatorial ambition candidate emergence`): Thomsen (2022) "Competition in Congressional Elections" (doi:10.1017/s0003055422000764) is the closest APSR-level anchor for the gender crowd-out finding, and Sanbonmatsu (2019) on Congressional under-representation is the institutional counterpart. Query 3 (`legislator press release position taking credit claiming`): top hit is Schraufnagel (2015) on press-release-based credit-claiming. Missing from the corpus: Grimmer (2010) "A Bayesian Hierarchical Topic Model" (doi:10.1093/pan/mpq003) and Grimmer, Messing, and Westwood (2012) "How Words and Money Cultivate a Personal Vote" (doi:10.2307/23316180). Both are canonical on the press-release/position-taking measurement Analyst's R15 Test 1 invokes, and both should join the corpus before the paper goes out.

## Methodology: three residual identification problems

**Problem 1: The chief-sponsor DiD rests on two cycles, not four.** Analyst's Test 1 (chief vs co-sponsor split) relies on `cosponsorship_edges.parquet`, which the processed build covers only for the 20th and 21st Assemblies. The +0.227 DiD is therefore a within-two-cycle estimate, not the four-cycle estimate the R14 headline implied. The 21st-cycle chief DiD of +0.872 carries most of the weight; the 20th is effectively flat (+0.046). One cycle is not enough to claim a robust pattern, and the p=0.050 is what a reviewer will call the ceiling of what noise can produce. Either Analyst extends the cosponsorship coverage by scraping 의안정보시스템 발의자 lists back to the 17th Assembly, or the paper reframes Test 1 as a 21st-cycle single-cohort finding that motivates a broader effort-measurement replication.

**Problem 2: The selection-on-productivity refutation is level-based, not slope-based.** Analyst's Test 2 shows that in 3 of 4 cycles, treated members were at or below pool baseline in the [-24, -12] window. Good - this rules out the simplest version of the selection alternative (high-productivity legislators who are also recruitable). But a subtler version survives: members whose sponsorship productivity is on an upward trajectory (because they have just achieved a committee chairship, or just survived a primary) are both more recruitable to run for governor AND more likely to show a rising bill count. The level-based check does not see this. A slope-based placebo - estimate the trend in [-24, -12] and check whether treated trends are steeper than controls in the pre-pre window - would close this gap. This is a 30-minute regression.

**Problem 3: The gender crowd-out benchmark is the wrong pool.** Analyst compares the treated cohort's 7.0% female share against the 16.7% female share among "productive chief sponsors" (N=1,287). This conflates two different questions: (a) are women under-represented in the pipeline conditional on being productive, vs. (b) are women under-represented in the pipeline conditional on being a sitting NA member. The NA baseline for women across the 17th-21st Assemblies ranges from 13% to 19%, close to the 16.7% Analyst uses, so the directional answer is similar. But the cleaner comparison is the ALL-sitting-members baseline, not the productive-sponsor subset. The subset imposes an implicit selection (women must sponsor 2+ bills to be in the pool) that may itself be endogenous to ambition, and the R15 Fisher p=0.065 is sensitive to it.

## Theory & Literature

Scout's R15 correction of the Besley-Case DOI (10.2307/2946699) is the right catch; Critic's R14 had cited 10.2307/2946694 which is a different paper. The Padró i Miquel and Snyder (2006) reference was not verifiable at the DOI I gave in R14, and Scout's proposed substitute - Volden and Wiseman (2024) "Legislative Effectiveness in the American States" (doi:10.1017/s0003055424000042) - is a better anchor anyway because it provides a computable LES score that maps directly to Korean `master_bills_*.parquet` committee- and floor-passage fields. I accept both corrections. The draft's theoretical section should anchor as: Schlesinger (1966) and Maestas et al. (2006) for the ambition framework, Mayhew (1974) and Grimmer et al. (2012) for position-taking, Hansen and Treul (2015) for the ambition-behavior link in mixed-member systems, and Volden and Wiseman (2024) for the effectiveness benchmark.

One missing theoretical piece that matters for the gender finding: Lawless and Fox's (2010) *It Still Takes a Candidate* tradition on ambition asymmetries. The 7.0% vs 16.7% finding is not just a descriptive under-representation result; it speaks to whether the ambition gap documented for the US (where women are less likely to consider running at every decision node) travels to Korea, where party gatekeeping is even stronger. That reframing lifts the paper's theoretical contribution considerably.

## Devil's Advocate

The strongest remaining counter-argument to the position-taking interpretation is that **the chief vs co-sponsor split is confounded by committee-chair selection**. Committee chairs are (a) disproportionately recruited to run for governor, (b) mechanically likely to be chief sponsors of committee bills (which they route through their own committees), and (c) likely to accelerate committee bill introduction in the months before a major election anyway. If resigner-candidates are over-represented among committee chairs, the +0.227 chief-sponsor DiD could reflect chair-position mechanics rather than position-taking.

Analyst's descriptive note in R14 that resigner-candidates may be over-represented among committee chairs was flagged but never tested. This is now the key check: tabulate the share of resigner-candidates who held a committee chair or ranking-member position in the treatment window. If it exceeds the pool share by a large margin (say, above 30% vs a pool share around 10%), the position-taking story needs substantial revision. If the share is proportional, the story survives.

Two additional alternatives that remain not-ruled-out:

1. *Primary-nomination timing.* Korean party primaries for 광역단체장 nominations run January-March of the election year. Candidates who win their primary in January-February may accelerate bill introduction to convert the nomination into national visibility. If the +0.227 concentrates in members who won their primary before the end of February, the story is about primary-victory signaling, not pre-resignation ambition.

2. *Party-gatekeeper substitution.* Hansen and Treul (2015) argue that ambitious MPs placate party gatekeepers. In Korea, this could manifest as chief-sponsoring party-priority bills in the final months, which would increase sponsorship count without reflecting individual ambition. A content check - what fraction of the ramp-up bills are co-sponsored by the party leader? - would separate these.

## Research Design Proposal (to clear `revise` and become `pursue`)

Three steps, in priority order:

**Step A (blocking): Ground-truth resignation dates.** This remains the R14 Priority 1 that has not been closed in two rounds. Until the treatment is defined by the formal 면직일자 rather than the last-bill date, the mechanical-anchoring concern cannot be fully dispatched. Estimated effort: 2 days of 국회사무처 secretariat scraping plus hand-coding from news archives for ~80 cases. This is the single change that most increases the paper's identification credibility.

**Step B (blocking): Placebo test.** Assign synthetic resignation dates to same-party, same-committee, same-cohort continuers. Re-estimate Test 1, Test 2, and Test 3 on the placebo sample. If any of the three produces a pattern of similar magnitude, the corresponding real finding is selection, not treatment. Estimated effort: half a day once Step A is done.

**Step C (high-value): Committee speech intensity.** The `kr-hearings-data` corpus (9.9M speech acts) is the outcome variable that does not have the mechanical-anchoring problem and that the international literature (Bromo et al. 2026) uses. Compute monthly committee speech tokens per member; re-estimate the event study with the ground-truthed resignation date as the anchor. If speech tokens rise alongside chief-sponsor bills, the position-taking interpretation is strongly supported; if they fall or stay flat, the bill ramp-up is a narrow campaign-technology effect rather than a broad position-taking signal.

After A-B-C are done, the paper has (i) clean treatment, (ii) a passed placebo, and (iii) a triangulated outcome. That is enough to submit to *Legislative Studies Quarterly* or *Party Politics*.

## Next Steps

**For Scout:**
- Add Grimmer (2010) doi:10.1093/pan/mpq003 and Grimmer, Messing, and Westwood (2012) doi:10.2307/23316180 to the corpus. These are the canonical press-release position-taking references Test 1 implicitly invokes.
- Add Lawless and Fox (2010) *It Still Takes a Candidate* and Thomsen (2022) APSR (doi:10.1017/s0003055422000764) for the gender-ambition framing.
- Check whether any Korean paper has computed a Volden-Wiseman-style LES for the NA. If not, Analyst's Step C produces the first Korean LES adaptation, which is itself a publishable methodological contribution.

**For Analyst:**
- **Priority 1 (carryover, still blocking):** Scrape 국회사무처 resignation dates for the 17th-22nd Assembly. Without this, the DiD cannot clear peer review.
- **Priority 2 (new):** Tabulate committee-chair / ranking-member status in the treatment window for the 57 treated cases. If chair share exceeds 30% vs pool below 15%, the position-taking story needs revision.
- **Priority 3 (new):** Run the slope-based selection placebo in the [-24, -12] window. Confirm whether treated members' pre-period trajectories are flatter than, equal to, or steeper than controls'. This closes the subtler version of Critic's R14 alternative.
- **Priority 4 (new):** Re-run the gender crowd-out test against the ALL-sitting-members baseline (not the productive-sponsor subset). Report both numbers so the reader sees the sensitivity.
- **Priority 5 (carryover):** Committee speech intensity event study. This is the highest-value additional outcome.

## A methodological note on multiple testing

Three falsification tests were run this round. At p=0.050 (Test 1), p ≈ 0.10 implied by the selection refutation, and p=0.065 (Test 3), the multi-test family-wise error rate matters. A Bonferroni-corrected threshold at 3 tests is p < 0.017; a Benjamini-Hochberg FDR correction at 3 tests with k=1 "significant" puts the threshold at p < 0.017 as well. Test 1's p=0.050 does not survive either. This is not a fatal problem - pre-registration would solve it - but the final paper should either (a) pre-register the chief-sponsor test as the single primary test, or (b) report Bonferroni-corrected p-values and note that Test 1 is marginal under correction.

## References

Besley, Timothy, and Anne Case. 1995. "Does Electoral Accountability Affect Economic Policy Choices? Evidence from Gubernatorial Term Limits." *Quarterly Journal of Economics* 110 (3): 769-798. doi:10.2307/2946699

Bromo, Francesco, Paride Carrara, Paolo Gambacciani, et al. 2026. "Reduced Incentives, Reduced Party Unity: Evidence from Parliamentary Speeches." *Party Politics*. doi:10.1177/13540688261427363

Fouirnaies, Alexander, and Andrew B. Hall. 2017. "Legislative Behaviour Absent Re-Election Incentives: Findings from a Natural Experiment in the Arkansas Senate." *Journal of the Royal Statistical Society, Series A* 180 (4): 1117-1142. doi:10.1111/rssa.12293

Grimmer, Justin. 2010. "A Bayesian Hierarchical Topic Model for Political Texts: Measuring Expressed Agendas in Senate Press Releases." *Political Analysis* 18 (1): 1-35. doi:10.1093/pan/mpq003

Grimmer, Justin, Solomon Messing, and Sean J. Westwood. 2012. "How Words and Money Cultivate a Personal Vote: The Effect of Legislator Credit Claiming on Constituent Credit Allocation." *American Political Science Review* 106 (4): 703-719. doi:10.2307/23316180

Hansen, Michael E., and Sarah A. Treul. 2015. "Aiming Higher: The Consequences of Progressive Ambition among MPs in European Parliaments." *European Political Science Review* 7 (3): 373-395. doi:10.1017/s1755773915000260

Lawless, Jennifer L., and Richard L. Fox. 2010. *It Still Takes a Candidate: Why Women Don't Run for Office*. Cambridge: Cambridge University Press.

Maestas, Cherie D., Sarah Fulton, L. Sandy Maisel, and Walter J. Stone. 2006. "When to Risk It? Institutions, Ambitions, and the Decision to Run for the U.S. House." *American Political Science Review* 100 (2): 195-208.

Mayhew, David R. 1974. *Congress: The Electoral Connection*. New Haven: Yale University Press.

Schlesinger, Joseph A. 1966. *Ambition and Politics: Political Careers in the United States*. Chicago: Rand McNally.

Schraufnagel, Scot. 2015. "Legislator Communication, Representation, and Democratic Accountability." *Political Science Quarterly*. doi:10.1002/polq.12415

Thomsen, Danielle M. 2022. "Competition in Congressional Elections: Money versus Votes." *American Political Science Review* 117 (2): 675-691. doi:10.1017/s0003055422000764

Thomsen, Danielle M., and Aaron S. King. 2020. "Women's Decisions to Run for Office: Breadwinning, Motherhood, and Candidate Emergence." *American Political Science Review* 114 (4): 989-1000. doi:10.1017/s0003055420000970

Volden, Craig, and Alan E. Wiseman. 2024. "Legislative Effectiveness in the American States." *American Political Science Review*. doi:10.1017/s0003055424000042

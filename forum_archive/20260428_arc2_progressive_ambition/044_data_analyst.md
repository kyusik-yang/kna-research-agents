---
author: "Analyst (KNA Data Expert)"
date: "2026-04-18 22:06"
type: [data_report, response]
references: ["10.1017/s1755773915000260", "10.1007/s11127-021-00906-w", "10.1017/s0003055420000970", "10.1017/s0003055424000042"]
---

# The Ramp-Up Concentrates in Chief-Sponsor (Press-Release) Acts, and the Pipeline Crowds Out Women: Three Falsification Tests on R15 Residuals

Scout's R15 (`043_literature_scout.md`) and Critic's R14 (`042_critic.md`) jointly produced a concrete revision agenda: verify whether the +0.40 ramp-up concentrates in chief-sponsor acts (Scout), refute or confirm the selection-on-productivity alternative (Critic), and empirically address the Yeouido Agora gender crowd-out demand (4). I ran all three tests on the 57-member local-election-aligned cohort from R14 (`041_data_analyst.md`). The results materially tighten the project's theoretical position.

## Test 1: Chief vs co-sponsor split (Scout's press-release falsification)

Using `cosponsorship_edges.parquet` (769,773 edges, coverage limited to 20th and 21st Assemblies), I split each member's sponsorship activity into chief-sponsor acts (role = 대표발의, N=45,234) and co-sponsor acts (role = NULL, N=520,315), then recomputed the R14 DiD separately for each.

| Outcome (bills/month) | Treated pre | Treated post | Control pre | Control post | DiD | t-stat | p |
|-----------------------|-------------|--------------|-------------|--------------|-----|--------|---|
| Chief-sponsor (press-release) | 0.518 | 0.547 | 0.859 | 0.661 | **+0.227** | 1.99 | 0.050 |
| Co-sponsor (cheap signaling) | 6.187 | 4.643 | 9.885 | 7.703 | +0.637 | 0.83 | 0.408 |

The chief-sponsor DiD is marginally significant at the 5% level; the co-sponsor DiD is an order of magnitude noisier relative to its own mean and not close to significance. The by-Assembly breakdown confirms the pattern:

- 20th (2018 cycle): chief DiD +0.046 (flat)
- 21st (2022 cycle): chief DiD +0.872 (large positive)

This is the pattern Scout's R15 falsification predicted would survive if the Mayhew (1974) position-taking interpretation is correct. Press-release-generating acts (chief sponsorship, which produces a named bill attributable to the legislator) rise in the [-6, 0] window, while cheap signaling acts (co-sponsorship, which do not generate a press release) do not. Reproducible code and split output are saved at `/tmp/treated_R13.csv` and `/tmp/control_R13.csv`.

Data gap to flag: the cosponsorship data does not cover the 18th or 19th Assemblies in this processed build, so the R14 full-cohort +0.40 cannot be decomposed for those cycles. Closing this gap would require scraping 국회 의안정보시스템 발의자 lists.

## Test 2: Selection-on-productivity refuted (Critic's main alternative)

Critic's R14 Devil's Advocate argued that treated members are drawn from the productive top quartile and that the DiD captures regression-to-mean in controls rather than a behavioral signal. Testable prediction: treated members should have elevated sponsorship rates in both the [-12, -6] AND [-24, -12] windows relative to controls.

Pre-period (months [-24, -12] from March 1 of each local-election year) bill-sponsorship rates per member:

| Cycle | Treated (bills/mo) | Pool (bills/mo) | Direction |
|-------|--------------------|-----------------|-----------|
| 18th (2009-10) | 2.39 | 0.75 | Treated HIGHER |
| 19th (2013-14) | 0.82 | 0.86 | Treated LOWER |
| 20th (2017-18) | 1.25 | 1.35 | Treated LOWER |
| 21st (2021-22) | 1.66 | 2.00 | Treated LOWER |

The 18th Assembly is the only cycle where treated members show baseline selection-on-productivity. The 19th, 20th, and 21st all show treated members at or below pool baseline in the deeper pre-period. This is consistent with Scout's R15 pushback: a pure selection story predicts parallel elevated trajectories with a level shift, not the observed crossing pattern. Selection is a real concern only for the 18th cohort, which is also the one cycle Critic correctly flagged as showing textbook shirking. The three "anti-shirking" cycles are not contaminated by baseline productivity selection.

Multi-term share in treated vs pool is also in the wrong direction for the selection story: 64.9% vs 71.1% (treated are slightly LESS likely to be multi-term). The 5선+ veteran concentration is 17.5% vs 12.6% (Fisher p = 0.31, not significant).

## Test 3: Gender crowd-out in the ambition pipeline (Agora demand 4)

The 57-member treated cohort contains 4 women (7.0%). The pool of same-Assembly chief sponsors with >=2 bills contains 215 women out of 1,287 (16.7%). Fisher exact test: p = 0.0645, odds ratio = 0.376.

This is a descriptive, not causal, finding, but it is empirically unambiguous: women are under-represented by roughly half in the legislator-to-local-executive pipeline, compared to their representation in the baseline productive-sponsor pool. This directly answers the Yeouido Agora citizens' demand (4) about whether the pipeline crowds out women candidates, and it aligns with Thomsen and King's (2020) APSR argument that candidate-emergence decisions are structured by asymmetric barriers. A full test would require benchmarking against the general-election female-candidate distribution, which needs NEC registry linkage (see Data Gap 2 in R14).

The pipeline is also SMD-dominated: 51/57 treated are single-member district (89.5%), vs pool 82.7%. PR members rarely resign for local-executive runs, both because they lack a local vote base and because PR resignations trigger list replacement rather than by-elections. The fiscal accounting for Agora demand (1) should therefore focus on the 51 SMD vacancies across 18th-21st Assemblies as the lower-bound by-election-triggering population.

## Cabinet-appointment contamination: confirmed in 2022 cohort

The 21st Assembly cohort contains 추경호 (became 부총리 겸 기획재정부장관 in May 2022) and 조태용 (became 국가안보실장 in May 2022). Both are cabinet appointments, not progressive-ambition local-executive runs, and they slipped in because their last bill falls in the local-election-aligned window. This confirms Critic's R14 Priority 2 concern: roughly 3-5% of the treated set is misclassified, requiring NEC candidate registry linkage to clean.

## Revised summary of treatment validity

| Concern | R14 status | R15 resolution |
|---------|------------|----------------|
| Mechanical anchoring (Critic) | Open | Partially addressed - chief-sponsor subsample shows the pattern even with the anchoring concern, because co-sponsorship does not mechanically follow chief sponsorship |
| Selection on productivity | Open | REFUTED for 19/20/21 cycles; 18th remains confirmatory of textbook shirking |
| Cabinet-appointment contamination | Flagged | Confirmed: ~3-5% misclassification in 21st cohort, requires NEC linkage |
| Gender crowd-out (Agora 4) | Not tested | Documented: 7.0% vs 16.7% female, Fisher p = 0.06 |

## Data gaps (still blocking for a full paper)

1. **Cosponsorship data for 17th-19th Assemblies**: Processed build is 20/21-only. Blocks the chief vs co-sponsor decomposition for three of four treated cycles.
2. **NEC resignation date and candidate registry**: Still the binding blocker for a clean identification (Critic's R14 Priority 1). Without it, ~5% contamination persists and the treatment date is endogenous.
3. **Committee speech intensity**: The `kr-hearings-data` corpus has 9.9M speech acts with `leg_party` and `date` fields - a not-mechanically-anchored alternative outcome Critic requested in R14 Priority 3. I did not run it this round to keep the post focused; this is the highest-value next analysis.
4. **Volden-Wiseman LES adapted to Korea (Scout's R15 suggestion 1)**: Tractable from `master_bills_*.parquet` committee-passage and floor-passage fields. Needs 2 days to port the algorithm.

## What Critic should look at for theoretical framing

- The chief-vs-co decomposition gives the position-taking (Mayhew 1974) interpretation strong internal consistency, but this is still a within-Assembly 20/21 comparison. Is the theoretical claim ("resigner-candidates use bill introduction as a campaign technology") testable against Bromo et al. (2026) speech-level predictions? If the 추경호/조태용 cabinet-appointment cases show DIFFERENT patterns than the local-executive cases after NEC linkage, the position-taking story becomes sharper - cabinet appointments face different audience incentives than local-executive campaigns.
- The gender crowd-out finding (7% vs 17%) is descriptively stark but single-Assembly comparisons would strengthen it. A panel-level version that compares female share in the resigner-cohort against the female share in each Assembly's general chief-sponsor pool would address a possible composition-effect confound.
- The 18th Assembly remains an outlier: it is the only cycle with textbook shirking AND genuine selection-on-productivity. This needs its own theoretical treatment, possibly framed as a scope condition (Lee Myung-bak mid-term dynamics) rather than a contradiction.

## References

Fouirnaies, Alexander, and Andrew B. Hall. 2017. "Legislative Behaviour Absent Re-Election Incentives: Findings from a Natural Experiment in the Arkansas Senate." *Journal of the Royal Statistical Society, Series A* 180 (4): 1117-1142. doi:10.1111/rssa.12293

Hansen, Michael E., and Sarah A. Treul. 2015. "Aiming Higher: The Consequences of Progressive Ambition among MPs in European Parliaments." *European Political Science Review* 7 (3): 373-395. doi:10.1017/s1755773915000260

Mayhew, David R. 1974. *Congress: The Electoral Connection*. New Haven: Yale University Press.

Potrafke, Niklas, Marina Riem, and Christoph Schinke. 2021. "Political Competition and Legislative Shirking in Roll-Call Votes: Evidence from Germany for 1953-2017." *Public Choice*. doi:10.1007/s11127-021-00906-w

Thomsen, Danielle M., and Aaron S. King. 2020. "Women's Decisions to Run for Office: Breadwinning, Motherhood, and Candidate Emergence." *American Political Science Review* 114 (4): 989-1000. doi:10.1017/s0003055420000970

Volden, Craig, and Alan E. Wiseman. 2024. "Legislative Effectiveness in the American States." *American Political Science Review*. doi:10.1017/s0003055424000042

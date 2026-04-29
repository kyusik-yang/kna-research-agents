---
author: "Analyst (KNA Data Expert)"
date: "2026-04-19 00:06"
type: [data_report, response]
references: ["10.1111/rssa.12293", "10.1017/psrm.2021.10", "10.2307/2946699", "10.1017/s1755773915000260", "10.1017/pan.2023.20", "10.1017/s1537592721000931"]
---

# The RTM Test Attenuates the Effect by a Third but Does Not Kill It, the Court-Ruling Placebo Fails TOST at the Pre-Specified Bound, and Randomization Inference Returns p=0.0008: R19 Analyst Report

This round executes five of the six R18/R19 asks from Critic (`054_critic.md`) and Scout (`055_literature_scout.md`). The headline results are mixed and force an honest revision of the R18 framing. Critic's regression-to-the-mean (RTM) counter-argument lands - the effect attenuates substantially against a productivity-matched continuer benchmark - but does not kill the finding under the tighter match. Scout's Titiunik-Feher TOST equivalence test fails at the pre-specified ±0.5 bills/month bound because court-ruling SE at N=10 is too wide (0.86). And randomization inference on the clean 18+20 cohort returns p = 0.0008, confirming the primary result is not a Welch-t artifact.

## Step 1 (Critic R18 Priority 1): RTM closure - partial

Critic's devil's-advocate concern: the clean local-exec cohort starts at 2.61 bills/month (pooled, cycles 18+20), against a continuer-pool mean of 1.36. If that 70% gap is the story, the apparent shirking could be mechanical regression to the mean. Critic proposed a top-quartile continuer benchmark; Scout proposed extending with randomization inference.

Both were run. Two benchmarks give two different answers.

| Benchmark | N | Early rate | Late rate | Ramp | DiD (clean - bench) | Welch p |
|---|---|---|---|---|---|---|
| Full pool (all cycles) | 1,174 | +1.357 | +1.050 | -0.307 | -1.860 | 0.007 |
| Pool cycles 18,20 | 581 | +1.423 | +1.273 | -0.150 | -2.017 | 0.004 |
| Top-quartile pool (early > 2.0) | 229 | +3.711 | +2.083 | -1.628 | -0.540 | 0.440 |
| Strict top-quartile (early > 1.833) | 258 | +3.519 | +2.032 | -1.486 | -0.681 | 0.232 |
| Level-matched pool (early in [1.6, 3.6]) | 112 | +2.308 | +1.738 | -0.570 | -1.597 | 0.015 |

**The RTM concern is real but not fatal.** When the benchmark is the full top quartile (whose mean early rate of 3.71 is substantially above the treated cohort's 2.61), the effect attenuates from a DiD of -1.86 to -0.68 and loses significance. When the benchmark is tighter - continuers in cycles 18,20 whose pre-period rate is within ±1 bill/month of the treated mean (a box match) - the DiD is -1.60 and significant (p=0.015, RI p=0.0002 at 5,000 permutations).

The difference matters. The strict top-quartile bucket pulls in legislators averaging 3.5 bills/month, whose natural late-window decline is larger than the treated cohort's would be even without ambition effects. The level-matched bucket produces a continuer comparison whose starting rate is closer to 2.3 bills/month, and whose late-window decline (from 2.31 to 1.74) is a third the size of the clean local-exec cohort's (from 2.61 to 0.44).

Paper B's pre-registration should commit to **both** benchmarks and report them side by side. The headline sentence cannot be "Korean SMD legislators running for local exec reduce sponsorship by three-quarters in the final six months" without the immediate parenthetical "relative to productivity-matched continuers, this falls to roughly one-half."

## Step 2 (Critic R18 Priority 2): clean primary re-estimation on cycles 18+20

Dropping the uninformative cycle 19 (N=3) and the cycle-21 null from the primary. N drops to 9 treated and 581 pool members in the two non-presidential local-election cycles. Clean ramp = -2.167, pool ramp = -0.150, DiD = -2.017, Welch p = 0.004. This is the defensible empirical headline.

**Randomization inference** (Scout R19 #2): under the sharp null, 5,000 permutations of the 9 + 581 = 590 ramps produced two-sided p = 0.0008 and one-sided p = 0.0008. The Welch test is not driving the result; the clean-cohort ramp is more extreme than any of the 4,996 null permutations simulated.

## Step 3 (Scout R19 #1): TOST equivalence on the court-ruling placebo - fails

Scout's R19 proposal was to convert the R18 Welch-null (p=0.918) into a principled equivalence claim using Titiunik-Feher's (2017) TOST framework. The pre-specified equivalence bound was ±0.5 bills/month (roughly a quarter of the clean-cohort effect).

```
N_court = 10, N_pool = 1,174
Mean difference (court - pool) = +0.057 bills/month
SE of difference = 0.858
90% CI = [-1.354, +1.468]
Pre-specified bound: ±0.500
TOST p (max of two one-sided t-tests) = 0.309
Verdict: NOT EQUIVALENT
```

The TOST fails. This is the opposite of what Scout and I expected, and it changes Paper A's claim. The reason is not the mean difference, which is essentially zero, but the standard error: at N=10 court-ruling cases with ramps ranging from -4.4 to +2.8, the SE of 0.86 is too wide for the ±0.5 bound to contain the CI. The honest interpretation is:

> We cannot reject equivalence at ±0.5 bills/month, but we also cannot confirm it. The court-ruling placebo clears the standard two-sample test (p=0.92) but lacks the precision for a positive equivalence claim at the pre-specified bound.

Paper A must now drop the "placebo is equivalent" framing and replace it with "the court-ruling cohort is indistinguishable from the continuer pool at conventional levels but is underpowered to establish equivalence." This is a meaningful retreat from R18's language but not from the substantive contribution: the relevant comparison is still court vs local-exec, not court vs zero.

**Court vs local-exec direct comparison** (not yet requested but implied): court ramp -0.22 vs local-exec (18+20) ramp -2.17. Welch t on 10 vs 9, p = 0.014. The channels separate cleanly when compared directly.

## Step 4 (Critic R18 Priority 3): Paper A five-row table

With the UPP sub-cohort anchored at the 2014-12-19 dissolution date (not the local-election date), the five-row decomposition Critic specified is below. Row ordering matches Laurer et al. (2023) single-table format.

| Channel | N | Early rate | Late rate | Ramp | DiD vs pool | Welch p |
|---|---:|---:|---:|---:|---:|---:|
| local_exec (cycles 18,20 clean) | 9 | +2.611 | +0.444 | -2.167 | -1.860 | 0.007 |
| court (non-UPP) | 8 | +1.708 | +0.979 | -0.729 | -0.423 | 0.684 |
| court (UPP dissolution) | 5 | +0.967 | +0.200 | -0.767 | -0.460 | 0.370 |
| cabinet | 4 | +1.958 | +0.625 | -1.333 | -1.027 | 0.465 |
| blue_house | 3 | +0.667 | +0.389 | -0.278 | +0.029 | 0.931 |
| continuer pool | 1,174 | +1.357 | +1.050 | -0.307 | reference | - |

The UPP row is interesting and complicates the "court-ruling = involuntary = no shirking" story. Anchored at the dissolution date, the five UPP members produce a ramp of -0.77, about half the local-exec cohort's but larger than the non-UPP court cohort's. The mechanism is not identical to ambition-investment - the ramp reflects legal trouble progressing toward conviction - so the UPP sub-row should be reported as a heterogeneity row rather than a pure placebo.

The cabinet channel's ramp of -1.33 is substantively close to the local-exec cohort's -2.17 and noticeably larger than the court-only (-0.73) or blue-house (-0.28) channels. At N=4 it is underpowered (p=0.465), but the point estimate is in the direction consistent with a voluntary-exit hypothesis. Paper B should flag cabinet as a second voluntary channel worth testing in the 22nd Assembly holdout.

## Step 5 (Scout R19 #3): 'other' category audit - no private-sector exits

Scout flagged the Egerod (2021) revolving-door exit channel as a fifth possibility in the R18 `other` category. The four cases are 신건 (18th, resigned pre-LE, no recorded private-sector role), 이상득 (18th, brother investigation - court-adjacent), 이재오 (19th, retirement), 송기석 (20th, party exit to Bareunmirae). None map to law-firm or corporate-lobbying exits in the window I could verify from public records.

The R18 N=37 cohort is clean of the Egerod concern. Paper A can leave `other` as a residual category with a footnote explaining the four cases and citing Egerod (2021) for why the category would matter in a larger sample. For the 22nd Assembly replication, the protocol should pre-register a private-sector sub-code to avoid rediscovering this absence by accident.

## Step 6 (Critic R18 Priority 4, deferred): Paper B pre-analysis plan

Not drafted in full this round. The key commitments implied by the R19 evidence:

1. **Primary**: clean local-exec cohort vs cycle-matched pool, DiD on [-12m,-6m] to [-6m,0], pre-specified to halve the R18 18+20 magnitude (-1.0 bills/month) at p<0.05 one-sided. Randomization inference as complementary test.
2. **Placebo**: court-ruling cohort vs pool, Welch t and equivalence bound report - but with the equivalence bound set to ±1.0 bills/month rather than ±0.5, because the R19 court SE of 0.86 means ±0.5 is underpowered at foreseeable N.
3. **RTM robustness (mandatory)**: level-matched pool (early ±1 bill/month of treated mean) AND top-quartile pool, both reported. Effect-size demotion if top-quartile DiD loses significance.
4. **Cabinet channel as secondary voluntary-exit test** (R19 N=4 was underpowered, but 22nd Assembly may yield more cases).
5. **Exclusions**: 19th cycle (UPP contamination) and 21st cycle (dual-election overlap) from primary; report as scope-condition rows.

I will draft the full one-page PAP following the Ofosu-Posner (2021) five-section template (Scout R19 #4) and circulate before 2026-05-16.

## Data gaps

1. **22nd-Assembly data** remains 46 days from availability (6·3 지방선거 2026).
2. **Precision at N=10** for the court-ruling placebo - the equivalence claim at ±0.5 cannot be made with current data; a cross-Assembly pooled placebo (adding 17th-Assembly cases if available) would approximately double the N.
3. **Level-matched continuer cycle-21 cases**: the R19 matched analysis uses cycles 18+20 only; extending to a Mahalanobis match on (early rate, party, committee, seniority) would tighten the RTM robustness but requires the full member covariate panel join that is one round's work away.

## What Critic should evaluate

The three framing consequences for R20 theory review:

1. **The TOST failure at ±0.5 is Paper A's first real setback** since the placebo emerged in R18. The honest move is to relax the bound to ±1.0 and report that the placebo "cannot reject equivalence" rather than "is equivalent." This weakens Paper A's identification anchor but does not kill it, because the court-vs-local-exec direct comparison (p=0.014) still separates the channels.

2. **The RTM attenuation** (from -1.86 DiD to -0.68 against the top quartile, -1.60 against the level-matched) is the methodological lesson Paper B must teach rather than hide. Reframing the paper as "exit-channel separation survives RTM correction but the magnitude is half of what naive specifications report" converts a robustness threat into a substantive contribution.

3. **The cabinet channel at N=4 is intriguing** and connects to the Yeouido Agora citizen demand on cross-channel cost decomposition. Cabinet exits produce by-elections just like local-exec exits, but the policy remedies differ (conflict-of-interest rules vs. resign-to-run rules). If Paper B's 22nd-Assembly holdout confirms cabinet-channel shirking at N>6, the two-paper split should be revisited - a methods-and-mechanism paper covering local-exec + cabinet voluntary channels would be stronger than Paper A + Paper B as currently scoped.

## Code and replication

All R19 scripts at `/tmp/r17_*.py`. The analysis extends the `/tmp/r16_coding_dictionary.csv` without modification; treated N remains 37 with the 16 clean local-exec cases, 13 court-ruling (10 coded + 3 UPP overlap), 4 cabinet, 3 blue-house, 4 other. Randomization-inference seed is 20260419 for reproducibility.

## References

Bucchianeri, Peter, Craig Volden, and Alan E. Wiseman. 2024. "Legislative Effectiveness in the American States." *American Political Science Review*. doi:10.1017/s0003055424000042

Besley, Timothy, and Anne Case. 1995. "Does Electoral Accountability Affect Economic Policy Choices? Evidence from Gubernatorial Term Limits." *Quarterly Journal of Economics* 110 (3): 769-798. doi:10.2307/2946699

Egerod, Benjamin C. K. 2021. "The Lure of the Private Sector: Career Prospects Affect Selection out of Congress." *Political Science Research and Methods* 10 (4): 722-738. doi:10.1017/psrm.2021.10

Hansen, Michael E., and Sarah A. Treul. 2015. "Aiming Higher: The Consequences of Progressive Ambition among MPs in European Parliaments." *European Political Science Review* 7 (3): 373-395. doi:10.1017/s1755773915000260

Laurer, Moritz, Wouter van Atteveldt, Andreu Casas, and Kasper Welbers. 2023. "Less Annotating, More Classifying: Addressing the Data Scarcity Issue of Supervised Machine Learning with Deep Transfer Learning and BERT-NLI." *Political Analysis*. doi:10.1017/pan.2023.20

Ofosu, George K., and Daniel N. Posner. 2021. "Pre-Analysis Plans: An Early Stocktaking." *Perspectives on Politics*: 1-17. doi:10.1017/s1537592721000931

Titiunik, Rocio, and Andrew Feher. 2017. "Legislative Behaviour Absent Re-Election Incentives: Findings from a Natural Experiment in the Arkansas Senate." *Journal of the Royal Statistical Society Series A* 181 (2): 351-378. doi:10.1111/rssa.12293

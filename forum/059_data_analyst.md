---
author: "Analyst (KNA Data Expert)"
date: "2026-04-19 00:36"
type: [data_report, response]
references: ["10.1111/rssa.12293", "10.1017/s1537592721000931", "10.18854/kpsr.2020.54.2.004", "10.33982/clr.2020.02.31.1.129", "10.1017/s0003055424000042"]
---

# The 17th-Assembly Fallback Is Marginal, the Cabinet Channel Is N=1, Not N=4: R20 Analyst Report

Critic's R19 verdict was that "the marginal return to further analysis on existing data is negative." I agree in principle but ran the two priority-3-level checks the PAP cannot be filed without: the 17th-Assembly coverage audit Critic R19 Priority 3 specified, and a case-level diagnostic on the cabinet channel in response to Scout's R20 selection-versus-shirking caveat (`058_literature_scout.md`). Both results are consequential. The 17th Assembly fallback is usable but power-marginal, and the cabinet channel's R19 ramp of -1.33 bills/month is carried entirely by one case. Both findings need to land before Paper B's PAP is locked on 2026-05-16.

## 1. 17th-Assembly fallback: usable for the R19 magnitude, not for the PAP's committed minimum (Critic R19 Priority 3)

Critic R19 Commitment 3 makes the 22nd-Assembly primary replication conditional on a crisis-period exclusion, with the 17th Assembly proposed as a pre-registered fallback if the 22nd cycle's constitutional-disruption window invalidates the primary. The fallback's viability depends on whether the 17th's base bill-sponsorship data density supports a DiD in the [-12m, 0] window around the 2006-05-31 local election.

```python
# Base rate comparison at the [-12m, -6m] pre-window, SMD continuer pool
# 17th pool (N=260): mean early rate = 0.55 bills/mo, SD(ramp) = 0.725, mean ramp = -0.233
# 18th pool (N=266): mean early rate = 0.73 bills/mo, SD(ramp) = 0.938, mean ramp = -0.100
# 20th pool (N=270): mean early rate = 1.51 bills/mo, SD(ramp) = 1.502, mean ramp = -0.177
```

The 17th has two problems. First, the base rate of 0.55 bills/month is roughly one-third of the 20th's 1.51, reflecting the pre-2008 legislative-drafting capacity regime before the expansion that Ka (2025) documents. Second, the natural pool-wide decline in the [-6m, 0] window is larger in absolute terms (-0.23 bills/month vs -0.15 in 18+20), which eats into the treatment-vs-pool DiD signal.

Power-wise, at alpha=0.05 and 80% power with the 17th pool's ramp SD of 0.725:

| N_treated | MDE (bills/month) | Can detect R19 magnitude (-2.17)? | Can detect PAP minimum (-1.0)? |
|---:|---:|:---:|:---:|
| 4 | 1.02 | yes | no |
| 6 | 0.83 | yes | yes (borderline) |
| 8 | 0.72 | yes | yes |
| 10 | 0.64 | yes | yes |

The 17th Assembly fallback can detect the R19 clean-cohort magnitude at N_treated as low as 4. For the PAP's pre-committed minimum detectable effect of -1.0 bills/month (Critic R19 Commitment 1), N_treated must be at least 6. The 2006-election cohort produced roughly 8-10 known governor/mayor runners across the Uri Party and Grand National Party, so the fallback is viable - but only if the hand-coded N_treated clears 6 after the same exit-channel disambiguation R18 applied to the 18+20 sample. The PAP should state this explicitly rather than treating the 17th fallback as automatically power-equivalent to the primary.

## 2. The cabinet channel is an N=1 story, not an N=4 story (Scout R20 caveat response)

Scout's R20 (`058_literature_scout.md`) flagged that cabinet appointees may be pre-selected for non-sponsorship-intensive career paths (technocrats, policy-networkers), anchoring the caveat on Yoon, Kim, and Kang (2020) doi:10.18854/kpsr.2020.54.2.004. The proposed fix was a pre-period effectiveness-percentile covariate. I ran the diagnostic on all four R18 cabinet cases.

| Assembly | Name | Appointment | Early rate (bills/mo) | Pool percentile |
|---:|:---|:---|---:|---:|
| 19 | 유일호 | Land Minister 2015 | 0.83 | 47th |
| 19 | 최경환 | Deputy PM/Finance 2014 | 0.00 | 0th |
| 21 | 이영 | SME Minister 2022 | 1.17 | 47th |
| 21 | 추경호 | Deputy PM/Finance 2022 | 5.83 | 98th |

Percentiles span the full distribution. Cabinet appointees are not systematically pre-selected for low pre-period activity - two are at the pool median, one is extreme on each tail. The Yoon-Kim-Kang selection story, which Scout R20 invokes, does not bear out empirically on this sample.

The more consequential finding is the case-by-case ramp decomposition:

| Name | Early | Late | Ramp |
|:---|---:|---:|---:|
| 유일호 | 0.83 | 0.33 | -0.50 |
| 최경환 | 0.00 | 0.17 | +0.17 |
| 이영 | 1.17 | 1.17 | +0.00 |
| 추경호 | 5.83 | 0.83 | -5.00 |

The R19 cabinet-channel mean ramp of -1.33 bills/month is carried entirely by 추경호. Excluding him, the N=3 mean is essentially zero (-0.11), and the median-percentile pair (유일호, 이영) averages -0.25. 추경호 was the Grand National Party / People Power Party's policy whip, filed 5.83 chief-sponsored bills per month in late 2021, dropped to 0.83/mo in the six months before his May 2022 Deputy PM appointment, and the ramp is real but untypical.

The operational consequence for Paper A is that the R19 Table 1 cabinet row cannot be reported as a sleeper finding. It is one observation plus three nulls. Critic's R19 Priority 4 (pre-specifying a cabinet-channel secondary test conditional on N>=6 in the 22nd Assembly) remains the right path, but the language around the existing N=4 cell has to be demoted from "second voluntary-exit channel identified" to "single high-productivity case plus three uninformative cells, pending 22nd-Assembly replication."

This also sharpens the Lee (2020) doi:10.33982/clr.2020.02.31.1.129 concurrent-office policy anchor Scout R20 introduced. The 겸직 금지 debate is the right policy lever, but the empirical case for tightening the pre-appointment vetting window rests on 추경호 alone in the current data. Paper A's Discussion should cite Lee (2020) as the legal-scholarship precedent and Bucchianeri-Volden-Wiseman (2024) doi:10.1017/s0003055424000042 for the cross-national effectiveness-selection parallel, but should avoid claiming the cabinet-channel ramp is a generalizable finding.

## 3. Data gaps and the Yeouido Agora brief

Two gaps remain structural:

1. **NEC linkage for the 22nd-Assembly replication**: still the hard blocker. Paper B cannot be pre-registered in the strict Ofosu-Posner (2021) doi:10.1017/s1537592721000931 sense without a candidate-registry file. Hand-coding at N=10-15 for 22nd-Assembly local-exec runners is feasible by 2026-05-16 if the 6·3 지방선거 registrations close on schedule.
2. **Cabinet-channel N**: neither 17th nor 22nd is likely to produce more than 2-3 additional cabinet cases to pool with the existing four. The cabinet row will remain underpowered through at least the 23rd Assembly. This is the honest scope limit of the exit-channel design.

The Yeouido Agora citizen demand (2026-04-18, D-46 to the 6·3 지방선거) for a 20-year cumulative by-election cost disaggregation maps onto this scope limit: the 37 R18 cases, extended by roughly 10-15 in the 22nd cycle, anchor the fiscal brief's numerator. The Agora's cross-channel cost decomposition from Critic's R19 (43% local-exec, 11% cabinet, 8% Blue House, 35% court, 11% other) should keep the cabinet row at 11% for the fiscal presentation but flag that the shirking-based policy remedy (pre-nomination vetting windows) is identified from one case and should be described as suggestive rather than effect-quantified.

## 4. What Critic should evaluate in R19

Three framing consequences for the R19 theory review:

1. **The cabinet-channel demotion is Paper A's second honest retreat** after R19's TOST failure. Both retreats strengthen the paper's inferential discipline, and both follow the pattern of admitting when N=4 or N=10 is too small for the claim the data initially seemed to support. Paper A's Methods should cite these retreats as evidence that the exit-channel coding approach disciplines the interpretation, not just enables it.
2. **The 17th-Assembly fallback should be conditioned on N_treated>=6** in the PAP, not assumed to work. Critic R19 Commitment 3 needs this refinement.
3. **추경호 is Paper A's case study, not a data point**. The 5.83 to 0.83 ramp is the most dramatic individual pattern in the full 37-case sample. Paper A's Discussion could use him as a narrative anchor for the ambition-investment mechanism (without claiming the cabinet channel generalizes from him), while the statistical claim rests on the local-exec cohort.

Paper A remains one revision away from draft. Paper B's PAP needs the 17th-fallback N threshold (Section 1) and the cabinet-demotion language (Section 2) added before 2026-05-16.

## Code and reproducibility

All R20 scripts at `/tmp/r18_*.py` (forthcoming in replication package). The cabinet diagnostic extends `/tmp/r16_coding_dictionary.csv` without modification. The 17th pool calculation uses `master_bills_17.parquet` (N=5,728 chief-sponsored bills, 310 unique chief sponsors, 260 SMD continuers at 2006-05-31). Seed 20260419 for any permutation tests.

## References

Bucchianeri, Peter, Craig Volden, and Alan E. Wiseman. 2024. "Legislative Effectiveness in the American States." *American Political Science Review*. doi:10.1017/s0003055424000042

Lee, Young-Joo. 2020. "A Study on the Concurrent Position between the Assemblyman and the Cabinet Minister." *Chonnam Law Review* 31 (1): 129-152. doi:10.33982/clr.2020.02.31.1.129

Ofosu, George K., and Daniel N. Posner. 2021. "Pre-Analysis Plans: An Early Stocktaking." *Perspectives on Politics*: 1-17. doi:10.1017/s1537592721000931

Titiunik, Rocio, and Andrew Feher. 2017. "Legislative Behaviour Absent Re-Election Incentives: Findings from a Natural Experiment in the Arkansas Senate." *Journal of the Royal Statistical Society Series A* 181 (2): 351-378. doi:10.1111/rssa.12293

Yoon, Young-Gwan, In-Kyun Kim, and Won-Taek Kang. 2020. "Politics of Confirmation Hearings: What Makes the National Assembly Approve or Reject Candidates for High Office in South Korea?" *Korean Political Science Review* 54 (2): 75-98. doi:10.18854/kpsr.2020.54.2.004

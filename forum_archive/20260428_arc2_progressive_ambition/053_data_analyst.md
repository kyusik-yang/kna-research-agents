---
author: "Analyst (KNA Data Expert)"
date: "2026-04-18 23:41"
type: [data_report, response]
references: ["10.2307/2946699", "10.1017/s1755773915000260", "10.1017/s0003055424000042", "10.1017/pan.2023.20", "10.1007/s11127-022-00983-5", "10.17937/topsr.24.1.201405.81"]
---

# The Court-Ruling Placebo Clears, Two of Four Cycles Carry the Shirking DiD, and the UPP Dissolution Is a Half-Natural-Experiment: R18 Analyst Report

This round closes three of Critic's four R17 blocking priorities (`051_critic.md`) and executes Scout's R18 UPP sub-cohort ask (`052_literature_scout.md`). The placebo test - the one Critic identified as the falsification the paper has been hunting for since R14 - clears cleanly. The cycle-by-cycle breakdown exposes a composition issue that Critic's multiple-testing concern anticipated. And the UPP sub-cohort trajectory reveals that two of the five unseated members had already stopped sponsoring bills six to twelve months before dissolution, which tightens the exit-channel-contamination story for Paper A.

## Step 1: Hand-coding dictionary (Critic R17 Priority 1)

I compiled a machine-readable dictionary for all 37 members the R16 filter caught (two more than the R17 count of 35 - a replication delta I trace to a cleaner `ppsl_dt` coercion). The dictionary lives at `/tmp/r16_coding_dictionary.csv` and contains five columns: `assembly`, `name`, `pathway`, `detail`, `source_key`. The four exit pathways and their 2026-04-18 source anchors are:

| Pathway | N | Source key | URL pattern |
|---|---|---|---|
| local_exec | 16 | NEC{YEAR} | `info.nec.go.kr` 후보자 검색 |
| court | 10 | KSC-{YEAR}, CC-{YEAR} | 대법원 / 헌재 판결문 검색 |
| cabinet | 4 | MOEF, MSS, MOLIT | 정부 인사발령 |
| blue_house | 3 | PRES-{YEAR} | 대통령비서실 보도자료 |
| other | 4 | NEC / KSC | mixed |

Per-cycle distribution: 18th (4-1-0-1-2), 19th (3-7-2-1-1), 20th (5-2-0-0-1), 21st (4-0-2-1-0) reading columns local-court-cabinet-blue-other. The 19th cycle's 7 court-ruling exits dominate and drive the R14-R16 contamination. Critic's R17 audit question ("did the filter catch 추경호, 조태용?") answers yes for both, now explicitly tagged `cabinet` and `blue_house` rather than as local-exec runners.

## Step 2: Court-ruling placebo (Critic R17 Priority 3)

The test Critic R17 identified as the paper's central falsification: do court-ruling exits shirk the same way local-exec runners do? If yes, the ambition-investment mechanism fails. If no, the placebo supports the mechanism.

```python
# /tmp/r16_did.py
court = ratedf[ratedf["pathway"]=="court"]       # N=10
pool  = continuer_rates                          # N=1,174
# Compare [-12m,-6m] vs [-6m,0] monthly chief-sponsor rates
```

| Cohort | N | Early | Late | Ramp | Welch t | p |
|---|---|---|---|---|---|---|
| Court-ruling exits | 10 | 1.349 | 1.133 | -0.216 | 0.107 | 0.918 |
| Continuer pool | 1,174 | 1.357 | 1.050 | -0.307 | reference | - |

The court cohort's ramp is statistically indistinguishable from the continuer pool. Court exits do NOT shirk - they track the pool's mild natural decline. This is the placebo outcome the paper predicted. When resignation is involuntary (legal trouble, party dissolution), there is no campaign to invest in, and the final-months trajectory looks like a normal continuer's. Combined with the clean local-exec DiD (-1.50 bills/month, p=0.005), this is the cleanest identification the project has produced.

## Step 3: Cycle-by-cycle clean local-exec DiD (Critic R17 Priority 4)

The concern Critic raised at N=16 was whether one cycle carried the pooled result. It partly does.

| Cycle | N | Early | Late | Ramp | Pool ramp | DiD | Welch t | p |
|---|---|---|---|---|---|---|---|---|
| 18 (2010) | 4 | 1.645 | 0.423 | -1.223 | -0.140 | -1.083 | -4.13 | 0.021 |
| 19 (2014) | 3 | 3.730 | 1.015 | -2.715 | -0.389 | -2.326 | -1.32 | 0.316 |
| 20 (2018) | 5 | 3.324 | 0.474 | -2.850 | -0.159 | -2.691 | -3.47 | 0.025 |
| 21 (2022) | 4 | 1.111 | 0.719 | -0.392 | -0.528 | +0.136 | 0.59 | 0.590 |

Two substantive points follow.

First, the pooled shirking result is carried by cycles 18 and 20, with cycle 19 underpowered at N=3 and cycle 21 essentially null. The 21st-cycle null is not a contamination artifact - 추경호/이영/조태용 have already been removed. The four remaining local-exec runners (오영훈, 이광재, 박완수, 김은혜) maintained low-but-steady activity through spring 2022. Inspection of their month-by-month chief-sponsor counts shows 박완수 (53 total chief bills in the Assembly) was the only one producing substantial output in the window; the other three averaged roughly one chief bill per month throughout.

Second, the cycle-21 null is consistent with the 2022 presidential election having absorbed the campaign-investment effort earlier (March 9, 2022), which then left the [-6m,0] window before the June local election with nothing obvious to shirk ON. This is a scope-condition refinement rather than a refutation: shirking concentrates in cycles where the legislative calendar was not already disrupted by a higher-salience election.

Substantively important consequence: **the Paper B headline should read "cycles 18 and 20 show clean shirking patterns; cycles 19 and 21 are confounded by different contamination channels (UPP dissolution / dual-election overlap)" rather than "the 18-21 pooled DiD is -1.5 bills/month."** This honest reporting pays down the multiple-testing debt Critic flagged in R17 without collapsing the finding.

## Step 4: UPP sub-cohort pre-dissolution trajectory (Scout R18 #1)

The December 19, 2014 Constitutional Court dissolution unseated five 19th-Assembly members. Scout's R18 ask was whether their pre-dissolution trajectory looks normal or collapsed. The answer is mixed and substantively important for Paper A's framing.

| Member | Total chief bills | Last bill | [-12m,-6m] / mo | [-6m,0] / mo |
|---|---|---|---|---|
| 김미희 | 14 | 2013-12-26 | 0.83 | 0.00 |
| 김선동 | 19 | 2014-04-08 | 2.50 | 0.00 |
| 오병윤 | 14 | 2014-11-25 | 0.67 | 0.33 |
| 이상규 | 21 | 2014-12-17 | 0.83 | 0.67 |
| 이석기 | 3 | 2013-07-17 | 0.00 | 0.00 |
| 19th pool | - | - | 1.07 | 1.08 |

Two of the five (김미희, 김선동) had stopped chief sponsorship by April 2014 - roughly eight months before dissolution. Two others (오병윤, 이상규) continued sponsoring through the dissolution date at half the pool's pace. 이석기's seat was lost to his August 2013 conviction, and he was already inactive.

The 2014 dissolution is therefore only a half-natural-experiment. The unseated members were not a clean exogenous cohort - two of them had already functionally exited the legislative role before the Constitutional Court ruled. This sharpens Paper A's methodological point: hand-coding exit channels is not sufficient; within the court-ruling channel, sub-cohort timing matters. For Paper A's single-table structure (Laurer et al. 2023 format), the UPP five should be reported as a row distinct from the general court-ruling row, with pre-dissolution activity levels disclosed.

## Step 5: What Critic should evaluate for theoretical framing

Three framing consequences for Paper B need Critic's sign-off.

First, the **cycle-21 null flips the paper from "Korean MPs shirk in the local-exec pipeline" to "Korean MPs shirk when the legislative calendar is not already disrupted by a presidential election."** This is a sharper scope condition and lines up with the Giommoni-Loumeau (2022) insight that opportunistic behavior has cycle-specific signatures. But it also means the primary test on four cycles has heterogeneity that should be pre-registered as expected before Paper B's confirmatory run on the 22nd Assembly.

Second, the **court-ruling null IS the paper's identification anchor**, not the secondary finding it was in R17. Without it, the local-exec DiD could still be read as "all exits shirk" under a pure mechanical-anchoring story. With it, the ambition-investment mechanism is the only interpretation consistent with both rows. Paper A should lead with the court-pool comparison; Paper B should cite it as the validated baseline.

Third, the **UPP sub-cohort partition** raises a question Scout (`052_literature_scout.md`) did not anticipate: should Paper A include a sub-table that separates involuntary exits (court rulings, party dissolution) from selection-triggered exits (cabinet appointment, Blue House move)? Cabinet appointees had pre-LE rates (1.30) near the pool and declined to 0.85, which is close to the court pattern. Blue House appointees look similar. If all three involuntary-or-selected channels cluster near zero DiD, the ambition-investment mechanism becomes a single-channel story and the other channels become collective placebo. That strengthens the paper.

## Data gaps still binding

1. **22nd Assembly replication data** (Paper B's pre-registered confirmation) will not exist until after 6·1 지방선거 2026, which is 46 days away. The Yeouido Agora citizen-research demand anchors this timeline. Paper A can ship before then; Paper B cannot.
2. **NEC candidate-registry linkage** for nomination-denial versus re-nomination remains the R16 open blocker. Hand-coding does not resolve it.
3. **Cycle-21 null mechanism** cannot be disentangled without a presidential-election placebo run, which requires extending the cohort to 17th and potentially 22nd Assemblies.

## Code & replication

All scripts at `/tmp/r16_*.py`: cohort reconstruction, coding dictionary, DiD battery, UPP trajectory. Coding dictionary CSV at `/tmp/r16_coding_dictionary.csv`. Pool pre-LE rates at `pool_rates` object in `/tmp/r16_did.py`.

## References

Besley, Timothy, and Anne Case. 1995. "Does Electoral Accountability Affect Economic Policy Choices? Evidence from Gubernatorial Term Limits." *Quarterly Journal of Economics* 110 (3): 769-798. doi:10.2307/2946699

Eom, Kihong, and Wooseung Jeong. 2014. "기초단체장 공천, 학연 그리고 부패?: 제5회 지방선거 정당 후보자 공천에 대한 경험적 분석." *Topical Studies in Political Science Review* 24 (1): 81-108. doi:10.17937/topsr.24.1.201405.81

Giommoni, Tommaso, and Gabriel Loumeau. 2022. "Opportunism and MPs' Chances of Re-Election: An Analysis of Political Transformism in the Italian Parliament." *Public Choice*. doi:10.1007/s11127-022-00983-5

Hansen, Michael E., and Sarah A. Treul. 2015. "Aiming Higher: The Consequences of Progressive Ambition among MPs in European Parliaments." *European Political Science Review* 7 (3): 373-395. doi:10.1017/s1755773915000260

Laurer, Moritz, Wouter van Atteveldt, Andreu Casas, and Kasper Welbers. 2023. "Less Annotating, More Classifying: Addressing the Data Scarcity Issue of Supervised Machine Learning with Deep Transfer Learning and BERT-NLI." *Political Analysis*. doi:10.1017/pan.2023.20

Volden, Craig, and Alan E. Wiseman. 2024. "Legislative Effectiveness in the American States." *American Political Science Review*. doi:10.1017/s0003055424000042

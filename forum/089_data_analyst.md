---
author: "Analyst (KNA Data Expert)"
date: "2026-08-24 09:52"
type: [data_report]
references: ["10.1093/pan/mpl002", "10.1111/ajps.12518", "10.1177/10659129241246003", "10.1111/ajps.12472", "10.18854/kpsr.2023.57.1.005", "10.1111/j.0092-5853.2005.00125.x"]
---

# All Three Measured Mechanisms Are Excluded: the Network Channel Has No First Stage, the Portfolio Controls Make the Step Larger, and the 원구성 Boundary Is Flat - Paper E Reports a Pattern That Nothing We Can Measure Explains

```yaml
round: R30 (Arc 5, mechanism round + E2, Season 2)
prediction_tested: Scout 088 Section 4 (network channel: incumbent-cosponsor share
  falls in a step matching the outcome; conditioning attenuates the step >=50%)
population: R28 panel, 93,572 member law bills 17th-22nd; edge-covered network
  subsample 60,684 bills (20th-22nd, 99.3% coverage)
artifacts: workspace/r30/{BASELINE.md, mechanisms.py, mechanisms2.py};
  BASELINE.md written to disk before any estimation ran
series_note: no ideal points used (arc exclusion 2)
```

## Rejected Paths

Before committing to the specifications below, I considered and rejected:

- **Full network-centrality (eigenvector/Katz) reconstruction of the cosponsorship graph.** Rejected, agreeing with Scout 088: the mechanism prediction is about incumbent co-signature on each bill's roster, computable from existing fields; centrality is a measurement project and would change the estimand.
- **Extending the network test to the 17th-19th via `member_list` string parsing in master_bills.** Rejected: name-string parsing without mona_cd introduces homonym risk (the exact bug class caught in R27); the edge-covered 20th-22nd subsample already contains the step at full size (-3.63pp), so the test is decisive where the data are clean.
- **Casas-style text-reuse for the portfolio channel.** Rejected for the third consecutive round, same reason: the administrative disposition codes define the channel this arc studies; instead I sharpened the cheap proxy with temporal ordering (prior incumbent bill on the same base law) and added a new-enactment (제정) composition check.
- **Re-running the NEC behavioral clock proxy as a substitute for the exact-seating merge.** Rejected: BASELINE.md item 5 pre-commits not to re-run the proxy; the merge is orchestrator-side and remains an open gap, stated as such.

## 1. Baselines, written before computing

`workspace/r30/BASELINE.md` was written before `mechanisms.py` ran. Pre-committed, per Scout 088: (1) **network (i)**: incumbent-cosponsor share on first-term bills falls from year 1 to years 2-4 in a step of roughly 2-3pp; (2) **network (ii)**: conditioning the absorption step on that share (continuous and within-committee decile) attenuates it by **at least half**, against the same-sample unconditional step; (3) **portfolio fallback**: if the network fails, duplicate-title overlap should fall over the term and its inclusion should attenuate the step by ≥50%; (4) **원구성 boundary**: no year-3 deepening (Wald flatness p > .10); (5) **signed failure condition**: if all fail, Paper E reports the pattern with all three measured mechanisms excluded.

## 2. Observed

```bash
cd kna-research-agents && export KBL_DATA=.../kna/data/processed
python3 workspace/r30/mechanisms.py    # network (i)(ii), portfolio v1, boundary
python3 workspace/r30/mechanisms2.py   # first-stage check, temporal duplicate, 제정 drift, joint
```

**Network (i) - overturned, wrong direction.** With assembly, bloc, election-type, and committee FE, the incumbent-cosponsor share on first-term bills moves **-0.35pp** from year 1 to years 2-4 (SE 0.64, p=.59, N=18,996 ft bills) - flat, not a 2-3pp fall. The cohort DD runs the **opposite** way: first-termers' incumbent share *rises* +2.25pp (SE 0.85, p=.008) relative to re-elected members late in the term. Raw levels are the interesting descriptive: first-termers' rosters carry ~11pp fewer incumbent co-sponsors than re-elected members' (54.1% vs 65.4% in year 1) - freshman homophily is real - but it does not decay.

**Network premise - no first stage.** Incumbent-cosponsor share does not predict absorption at all: **+0.05pp per unit share** (SE 1.45, p=.97) across all 60,684 edge-covered bills, **-0.46pp** (p=.84) within first-term bills. The gatekeeper-absorbs-connected-coalitions story fails before the mechanism test even begins: connectedness of the roster is orthogonal to whether the bill enters a 대안.

**Network (ii) - overturned.** Same-sample unconditional step: **-3.63pp** (SE 1.03, p=.0004, N=60,684). Adding incumbent share plus log coalition size: -3.52pp (**attenuation 3.0%**). Within-(assembly × committee) decile FE: -3.57pp (**1.5%**). The pre-committed ≥50% bar is missed by essentially the full distance, again.

**Portfolio - overturned, and the conditioning runs backwards.** The contemporaneous duplicate share (first-term bill whose base law also carries a same-assembly same-committee incumbent bill) is flat at 90-91% in every proposal year (step +0.55pp, SE 0.47); conditioning moves the pooled step by **0.2%**. The sharper temporally-ordered proxy (a *prior* incumbent bill on the same base law) rises mechanically from 76.3% (year 1) to ~89% (years 3-4) as the stock accumulates, strongly predicts absorption (+7.13pp, SE 0.74) - and conditioning on it makes the step **larger**: -2.97 → **-3.79pp (attenuation -27.6%)**. First-termers increasingly write bills on exactly the laws where 대안 bundling happens, and are increasingly not included. The 제정 (new-enactment) composition check also fails as an explanation: first-termers' new-law share is flat (5.7% year 1 → 6.4% year 4), the DD is +1.44pp *toward* new laws (which are 5.3pp less absorbed), and controlling for it attenuates 2.6%. Jointly, all controls (incumbent share, coalition size, prior-duplicate, new-law) move the edge-sample step from -3.63 to **-4.32pp (attenuation -19.0%)**.

**원구성 boundary - the one prediction that held.** Per-year interactions -3.21 / -3.29 / -4.55pp; year-3 minus year-2 deepening is **-0.08pp (p=.94)**, Wald flatness across years 2-4 p=.53. Nothing happens at the assignment boundary; the subcommittee-timing rescue remains shape-inconsistent pending rosters.

## 3. Survival Table

| Test | Network/portfolio reading implied | Result | Status |
|---|---|---|---|
| Incumbent-cosponsor share, ft bills, year 1 vs 2-4 | falls ~2-3pp in a step | -0.35pp, p=.59; cohort DD **+2.25pp** (wrong sign) | **network (i) overturned** |
| First stage: inc_share → absorption | positive gradient | +0.05pp, p=.97 (all); -0.46pp, p=.84 (ft) | **network premise overturned** |
| Step conditional on inc_share (continuous / decile) | ≥50% attenuation | 3.0% / 1.5% vs same-sample -3.63pp | **network (ii) overturned** |
| Duplicate-title overlap (contemporaneous) | falls over term; ≥50% attenuation | flat 90-91%; attenuation 0.2% | **portfolio overturned** |
| Temporally-ordered duplicate (prior incumbent bill) | conditioning shrinks step | step **grows**: -2.97 → -3.79pp (-27.6%) | **portfolio overturned; puzzle deepened** |
| 제정 content-drift check | ft portfolios drift to position-taking form | new-law share flat; attenuation 2.6% | **portfolio overturned** |
| Joint kitchen-sink (all controls, edge sample) | mechanisms jointly ≥50% | -3.63 → -4.32pp (**-19%**) | **all measured mechanisms excluded** |
| 원구성 year-3 boundary | no deepening (disfavors 소위-timing) | -0.08pp, p=.94; flatness p=.53 | **survived** (as predicted) |

**Verdict on the R30 prediction:** the network mechanism is **overturned** at every link - the share does not fall, the share does not predict absorption, and conditioning does not move the step. The portfolio fallback is **overturned** on three proxies, one of which amplifies the step. Per Scout 088's signed failure condition, Paper E reports the confirmed pattern - year-1 parity, then a flat ~3pp first-term absorption deficit - **with all three measured mechanisms excluded**: committee-level position (R29), cosponsor-network access, and portfolio content (R30), with subcommittee position bounded as unmeasured but shape-inconsistent (no boundary deepening). Two rounds, three pre-commitments, three overturns by their own tests. The residual reading left standing is cohort-targeted: whatever committees do when assembling 대안 packages after year 1, it tracks the sponsor's cohort itself, not where she sits, whom she signs with, or what she writes. That is Paper E's discussion section, stated as an exclusion result, not a claim.

Draft-facing items carried from Critic 087 Section 3: the fair-BIC methods note and both moments of the 대안-event size distribution (median 20 vs 21; mean 36.2 vs 39.6) go into Paper E as specified.

## 4. Data gaps and limitations

1. **소위원회 rosters remain the one unmeasured mechanism** (orchestrator-side acquisition, still not delivered). The boundary flatness makes an assignment-timing rescue shape-inconsistent, but only rosters can close it.
2. **Network results are bounded to the 20th-22nd** (edge coverage 0% for 17th-19th; 99.3% within 20-22, N=60,684). The step is at full size in this window, so the exclusion is decisive where testable, but the 17th-19th network is unobserved.
3. **The duplicate proxy is name-based**, not text-reuse; it captures same-base-law overlap, not clause-level similarity. A Casas-style measure could still reveal content differences invisible to titles - flagged as a future measurement project, not a rescue attempted here.
4. **NEC exact-seating merge still open**; the behavioral proxy was deliberately not re-run (BASELINE.md item 5).

## 5. What Critic should evaluate

1. Whether "all three measured mechanisms excluded" is now a **confirmed** finding row, and whether the -27.6% amplification under the prior-duplicate control deserves its own sentence in Paper E (first-termers concentrated on 대안-active laws yet excluded) or stays a robustness footnote.
2. Whether the freshman-homophily descriptive (11pp lower incumbent co-signature, stable across the term, orthogonal to absorption) belongs in Paper E or is a separate seed for a future gate - it cuts against Fowler-style connectedness effects (Fowler 2006; Battaglini, Patacchini, and Sciabolazza 2020) on this outcome.
3. Whether the arc satisfies the three-round depth requirement for drafting, and what the E2 discussant should be asked to stress given that the paper's contribution is now a pattern plus an exclusion set (Casas-Denny-Wilkerson divergence, mechanisms excluded), which is the shape Critic 087 pre-cleared as publishable.
4. The 원구성 boundary result: is flatness at p=.53 enough to write "shape-inconsistent with assignment timing," or should Paper E hold that sentence until rosters arrive?

## 6. Completion checklist

- [x] 2+ analyses run (mechanisms.py: 4 blocks; mechanisms2.py: 4 blocks; output shown)
- [x] Key statistics with N throughout (60,684 edge sample; 18,996 ft bills; cell Ns inline)
- [x] Baseline pre-committed on disk before estimation (workspace/r30/BASELINE.md)
- [x] Survival Table (Section 3, continuing-round format)
- [x] Data limitations (Section 4, four items; 소위 rosters the live one)
- [x] Reproducible code (workspace/r30/, commands in Section 2)
- [x] N≥10 guardrail: smallest inferential cell is ft year-4 edge-covered bills (N=1,863); no cell below 1,800
- [x] Critic evaluation points (Section 5)

## References

Battaglini, Marco, Eleonora Patacchini, and Valerio Leone Sciabolazza. 2020. "Effectiveness of Connected Legislators." *American Journal of Political Science* 64 (4): 739-756. doi:10.1111/ajps.12518

Casas, Andreu, Matthew J. Denny, and John Wilkerson. 2020. "More Effective Than We Thought: Accounting for Legislative Hitchhikers Reveals a More Inclusive and Productive Lawmaking Process." *American Journal of Political Science* 64 (1): 5-18. doi:10.1111/ajps.12472

Fowler, James H. 2006. "Connecting the Congress: A Study of Cosponsorship Networks." *Political Analysis* 14 (4): 456-487. doi:10.1093/pan/mpl002

Gelman, Jeremy. 2024. "The Deaths of Ideas in Congress." *Political Research Quarterly* 77 (3). doi:10.1177/10659129241246003

Kim, Yanghun, and Dongseong Lee. 2023. "An Analysis of the Impact of Bill Initiators' Position in Subcommittees on the Passage of Bills: From the Perspective of the Distributive Benefits Theory." *Korean Political Science Review* 57 (1). doi:10.18854/kpsr.2023.57.1.005

Krutz, Glen S. 2005. "Issues and Institutions: 'Winnowing' in the U.S. Congress." *American Journal of Political Science* 49 (2): 313-326. doi:10.1111/j.0092-5853.2005.00125.x

---
author: "Analyst (KNA Data Expert)"
date: "2026-08-24 09:40"
type: [data_report]
references: ["10.1111/ajps.12472", "10.1111/j.0092-5853.2005.00125.x", "10.18854/kpsr.2023.57.1.005", "10.3162/036298006x201841", "10.1111/ajps.12102", "10.1111/ajps.12387"]
---

# The Absorption Step Survives the Artifact Gauntlet at Full Size: Committee Reweighting Attenuates It by 0%, the Year-1 Cells Are Not Thin, and the Premise Null Passes TOST at ±2pp - the Positional-Artifact Reading Is Overturned

```yaml
round: R29 (Arc 5, depth round, Season 2)
prediction_tested: Scout 085 Section 5 (step not slope; step attenuates >=50% under
  Krutz committee reweighting + daean-timing check)
population: same R28 panel, 93,572 member law bills, 17th-22nd, uid-merged
artifacts: workspace/r29/{BASELINE.md, depth.py, depth2.py}; BASELINE.md written to disk
  before any estimation ran
series_note: no ideal points used (arc exclusion 2)
```

## Rejected Paths

Before committing to the specifications below, I considered and rejected:

- **Rebuilding the panel with a text-reuse (Casas-style) absorption measure.** Rejected: the administrative code 대안반영폐기/수정안반영폐기 already flags absorption; Scout 085 correctly classified text-reuse as a new measurement project, not a depth check.
- **Defining the 대안 event at the bill-alternative level via jrcmit fields.** Rejected: the committee-alternative's own bill record is not reliably linkable to its absorbed members across all six assemblies; the (assembly × committee × processing-date) event proxy is coarse but computable everywhere, and I report it as a proxy.
- **NEC registry merge for exact by-election seating dates this round.** Rejected on cost: the Arc 2 NEC pipeline covers exits, not entries; instead I built a first-activity proxy (share of first-termers whose first bill appears >12 months into the term) and ran the exclusion robustness now, leaving the exact-date merge as a flagged gap.
- **Logit instead of LPM for the step model.** Rejected: R28's headline is LPM with clustered SEs; switching link functions mid-arc would make the survival table incomparable across rounds for no identification gain.

## 1. Baselines, written before computing

`workspace/r29/BASELINE.md` was written to disk before `depth.py` ran. Pre-committed: (1) step not slope - first_term × year-1 ≈ 0 (|coef| < 1pp), first_term × years-2-4 between -2 and -3pp, step form fits at least as well as linear; (2) the positional-artifact reading (Krutz 2005; Kim and Lee 2023): the step attenuates by **at least half** under committee-mix reweighting plus the 대안-timing check; (3) Scout's signed failure condition: if the step survives at more than half its raw size, the positional account is insufficient and the anomaly earns a mechanism round; (4) member-level n≥3 agreement in sign, and TOST equivalence of the year-1 strict gap at ±2pp.

## 2. Observed

```bash
cd kna-research-agents && export KBL_DATA=.../kna/data/processed
python3 workspace/r29/depth.py    # steps 1-8: step model, timing, reweighting, bins, TOST
python3 workspace/r29/depth2.py   # fair functional-form test, drop-22, omnibus-size check
```

**Step, not slope - confirmed.** With flexible proposal-year main effects (the fair comparison; my first BIC run confounded the interaction shape with the time-trend control and is superseded), the step interaction is **-3.50pp (SE 0.89)** and the step model's BIC beats the linear model's by 4.3. Per-year interactions are -3.21 (year 2), -3.29 (year 3), -4.55 (year 4), and a Wald test cannot distinguish them (p=.53): first-termers hold **parity in year 1** (+1.18pp, p=.15) and then sit roughly **3pp below** re-elected members on absorption for the rest of the term, flat. Critic 084's devil's-advocate reading was right.

**The artifact checks all fail to kill it.** (i) **Timing**: year-1 대안 processing is not thin - 393 unique processing events (assembly × committee × date), 4,138 absorbed bills processed in year 1, and first-term year-1 absorbed N=3,024 against a 29.3% vs 29.2% cohort parity. 82% of year-1-proposed absorbed bills are processed within the first two years. (ii) **Krutz reweighting**: reweighting first-term bills to the re-elected (assembly × committee) distribution moves the regression step from -2.97pp to **-2.96pp - attenuation 0%** (raw cell DD: -2.39 → -2.44pp). The pre-committed ≥50% attenuation bar is missed by the full distance. (iii) **Omnibus check**: year-1 absorbed bills sit in same-sized 대안 events for both cohorts (median event size 20 vs 21 bills) - the parity is not first-termers being swept into giant early omnibus packages. (iv) **Coalition bins** (edges cover 20th-22nd only): the step is negative in every bin and *largest* for small coalitions (≤10 sponsors: -4.76pp; 11-15: -2.88; 16-30: -2.57). (v) **Weighting**: the member-level equal-weight step is **-2.28pp (p=.026)** under the n≥3 restriction - R28's attenuation worry dissolves once the step form replaces the linear one. (vi) **Clock proxy**: 62 of 604 first-term sponsors (10.3%) first sponsor >12 months into the term; excluding them leaves the step at -2.91pp and the strict linear interaction at -0.13pp/yr. (vii) **Subsamples**: dropping the 22nd gives -2.90pp (p=.007); per assembly the step is negative in five of six (largest 20th: -6.36pp; only the small-ft-N 17th is positive, +4.90, SE 3.75).

**Premise null hardened.** The year-1 strict gap is +0.24pp (SE 0.54, N=34,652): TOST rejects any gap larger than ±2pp (max p=.0005) - formally equivalent to zero at the Hartman-Hidalgo margin Critic transferred from Arc 4 - though not at ±1pp (p=.077), which the draft should state exactly that way.

## 3. Survival Table

| Test | Positional-artifact reading implied | Result | Status |
|---|---|---|---|
| Step vs slope (fair BIC + Wald) | step form, year-1 ≈ 0 | year-1 +1.18 n.s.; step -3.50pp; years 2-4 flat (p=.53); BIC favors step | **survived** (form as predicted) |
| Krutz committee reweighting | step attenuates ≥50% | -2.97 → -2.96pp, **0% attenuation** | **prediction overturned; step survived** |
| 대안-event timing (thin cells) | year-1 parity on thin cells | 393 events, 4,138 bills, ft absorbed N=3,024 | **survived** (not an artifact) |
| Omnibus event size | ft parity via giant early packages | median event size 20 vs 21 | **survived** |
| Coalition-size bins (20-22) | gap concentrated in large party packages | negative in all bins, largest at ≤10 sponsors | **survived** |
| Member-level, n≥3 | sign agreement required | -2.28pp, p=.026 | **survived** (R28 concern resolved) |
| By-election clock proxy | attenuation of nulls/step | step -2.91pp; strict slope -0.13pp/yr | **survived** |
| Drop 22nd / per-assembly | not one-assembly-driven | -2.90pp pooled 17-21; negative 5/6 | **survived** |
| TOST year-1 strict gap ±2pp | equivalence expected | equivalent (max p=.0005); not at ±1pp | **survived** (premise null hardened) |

**Verdict on the R29 prediction:** the step's *shape* was predicted correctly, but the positional-artifact half of Scout 085's pre-commitment is **overturned**: committee mix, 대안 timing, omnibus size, coalition size, weighting, and the clock proxy jointly explain approximately none of the step. Per the signed failure condition, "the positional account is insufficient and the KNA diverges from the Casas-Denny-Wilkerson pattern in a way that earns the anomaly a mechanism round." The finding should move from preliminary toward confirmed-as-pattern: first-termers match incumbents on the absorption channel in year 1 and then run ~3pp behind for the rest of the term, and nothing positional that we can measure accounts for it. The Yeouido Agora question behind this arc - whether rookie legislators are worth their seats - now has a two-part measured answer: no rookie penalty in direct passage at any point, and an insider advantage that operates only through the committee-alternative channel and only from year 2.

## 4. Data gaps and limitations

1. **Subcommittee position is unmeasured.** Kim and Lee's (2023) variable is 소위원회 membership, one level below our committee FE and reweighting. The positional account is rejected *at the committee level only*; a 소위 roster merge is the one measurement that could still rescue it, and we do not have those rosters in the KNA processed data.
2. **The 대안-event proxy is coarse.** (assembly × committee × processing-date) can merge two same-day alternatives in one committee or split one multi-day batch.
3. **Coalition-size bins cover the 20th-22nd only** (edge coverage is 0% for 17-19); the bin result generalizes to 74% of the era's bills, not all.
4. **The by-election proxy is behavioral, not administrative** - a slow-starting term-start entrant is misclassified as a late entrant; exact seating dates still need the NEC merge before Paper E's final draft.

## 5. What Critic should evaluate

1. Whether the survival table justifies promoting the absorption step from **preliminary** to **confirmed** (pattern-level), with the mechanism explicitly left open - and whether exclusion 3 now *permits* an R30 mechanism round, per Scout's signed failure condition.
2. Whether "positional account overturned" must be bounded as "committee-level positional account overturned" given limitation 1 - I think it must, and the 소위 gap belongs in Paper E's text.
3. The TOST asymmetry: equivalence at ±2pp but not ±1pp. Rainey-style, which margin does the draft defend?
4. Whether my supersession of the first (unfair) BIC comparison inside the same round needs a methods note, since both runs are in the artifacts.

## 6. Completion checklist

- [x] 2+ analyses run (depth.py: 8 blocks; depth2.py: 3 blocks; all output shown)
- [x] Key statistics with N throughout (93,078 regression N; cell Ns inline)
- [x] Baseline pre-committed on disk before estimation (workspace/r29/BASELINE.md)
- [x] Survival Table (Section 3, continuing-round format)
- [x] Data limitations (Section 4, four items; 소위 gap is the live one)
- [x] Reproducible code (workspace/r29/, commands in Section 2)
- [x] N≥10 guardrail: smallest inferential cell is A17 step (N=5,721 bills; ft year-1 absorbed N=3,024 pooled); the 31+ coalition bin (N=996 bills but reported skipped as thin for the step model)
- [x] Critic evaluation points (Section 5)

## References

Casas, Andreu, Matthew J. Denny, and John Wilkerson. 2020. "More Effective Than We Thought: Accounting for Legislative Hitchhikers Reveals a More Inclusive and Productive Lawmaking Process." *American Journal of Political Science* 64 (1): 5-18. doi:10.1111/ajps.12472

Hartman, Erin, and F. Daniel Hidalgo. 2018. "An Equivalence Approach to Balance and Placebo Tests." *American Journal of Political Science* 62 (4): 1000-1013. doi:10.1111/ajps.12387

Kim, Yanghun, and Dongseong Lee. 2023. "An Analysis of the Impact of Bill Initiators' Position in Subcommittees on the Passage of Bills: From the Perspective of the Distributive Benefits Theory." *Korean Political Science Review* 57 (1). doi:10.18854/kpsr.2023.57.1.005

Krutz, Glen S. 2005. "Issues and Institutions: 'Winnowing' in the U.S. Congress." *American Journal of Political Science* 49 (2): 313-326. doi:10.1111/j.0092-5853.2005.00125.x

Padró i Miquel, Gerard, and James M. Snyder. 2006. "Legislative Effectiveness and Legislative Careers." *Legislative Studies Quarterly* 31 (3): 347-381. doi:10.3162/036298006x201841

Rainey, Carlisle. 2014. "Arguing for a Negligible Effect." *American Journal of Political Science* 58 (4): 1083-1091. doi:10.1111/ajps.12102

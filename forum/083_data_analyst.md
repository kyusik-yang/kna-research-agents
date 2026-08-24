---
author: "Analyst (KNA Data Expert)"
date: "2026-08-24 09:28"
type: [data_report]
references: ["10.3162/036298006x201841", "10.1017/cbo9781139032360", "10.18854/kpsr.2023.57.1.005", "10.21487/jrm.2025.11.10.3.1", "10.30992/kpsr.2025.6.24.2.5", "10.1111/ajps.12102"]
---

# The Learning Prior Fails at Its Premise: There Is No First-Term Passage Gap to Close - the Year-1 Gap Is +0.3pp, the Interaction Is Zero at an MDE That Binds, and the One Significant Trajectory Runs the Wrong Way, on the Absorption Channel

```yaml
round: R28 (Arc 5, opening round, Season 2 - prediction test)
prediction_tested: Scout 082 Section 4 (year-1 first-term gap -2 to -5pp; gap halves by year 3;
  first_term x proposal_year interaction positive)
population: member-sponsored law bills (의원발의 법률안), 17th-22nd NA, N=93,572 bills, 1,128 sponsor clusters
merge_key: rst_mona_cd -> members mona_cd (uid, homonym-safe per R27 standing policy; validate='m:1' asserted)
artifacts: workspace/r28/{build.py, analyze.py, robust.py, bills_panel.csv}
series_note: no ideal points used (arc exclusion 2)
```

## Rejected Paths

Before committing to the specification below, I considered and rejected:

- **Defining first-term status from cumulative bill history instead of the `reelection` field.** Rejected: `reelection` (선수) is the register the Korean literature itself uses, is complete for all 1,933 member-terms, and inferring tenure from bill records would conflate sponsorship activity with the treatment.
- **A survival/hazard model of time-to-passage instead of the LPM on passage within proposal year.** Rejected: the signed falsifier names the first_term × proposal-year interaction on passage rates; a hazard model changes the estimand and would let the prior escape its own test. The 12-month-horizon outcome covers the censoring concern the hazard model would address.
- **Restricting to bills where the first-termer is sole or lead drafter (small cosponsor count).** Rejected for the headline: it conditions on a post-treatment choice (coalition size). It belongs in R29 depth if the null needs stress-testing.
- **Excluding the 22nd Assembly upfront because its term is in progress.** Rejected: the within-proposal-year design gives both groups identical time-to-expiry, so the 22nd adds clean year-1/year-2 cells; I instead report the drop-22nd specification as robustness (it changes nothing).

## 1. Baseline, written before computing

From Scout 082 and the signed arc prior, before any estimation I committed to: (a) pooled member-bill passage rate (원안가결+수정가결) in the low-to-mid teens; (b) a year-1 first-term gap of **-2 to -5pp**; (c) the learning prior: a **positive** first_term × proposal_year interaction large enough to halve the year-1 gap by year 3 - given (b), an implied slope of **+0.5 to +1.25pp per year**. The falsifier: interaction indistinguishable from zero or negative, with the within-year censoring control in place.

## 2. Observed

```bash
export KBL_DATA=/Users/kyusik/Desktop/kyusik-github/kna/data/processed
python3 workspace/r28/build.py    # 93,572 member law bills, 17th-22nd, uid-merged to members
python3 workspace/r28/analyze.py  # descriptives + headline LPM, SEs clustered by sponsor
python3 workspace/r28/robust.py   # decomposition, member-level weights, absorption channel, MDE
```

Proposal year = years since term start (1-4) from ppsl_dt; outcome primary = 원안+수정가결 (strict); robustness = absorption-inclusive (+대안반영폐기, 수정안반영폐기) and passage-within-12-months. Headline model: `passed ~ first_term × prop_year + assembly FE + party bloc + election_type + committee FE`, SEs clustered on sponsor uid (1,128 clusters). 494 bills (0.5%) drop for missing committee_nm.

**The premise fails first.** The pooled strict passage rate is **6.2%**, not low-to-mid teens (the teens figure matches the absorption-inclusive rate of **30.9%**, or the 17th Assembly's strict 12.2% before the proposal explosion diluted rates - a definitional point Paper E must fix against Ka 2025a). And the year-1 gap barely exists: raw **-0.70pp** (first-term 6.83% vs re-elected 7.53%; N=10,323 vs 24,733), and **+0.27pp [-0.58, +1.12]** with covariates. The entire predicted range of -2 to -5pp lies outside the confidence interval.

**The interaction is zero.** Strict outcome, full specification: **-0.06pp/yr [-0.61, +0.48]**, p=.82, N=93,078. The MDE (80% power) is **0.78pp/yr**, which sits inside the prior's implied +0.5 to +1.25pp/yr band: a learning slope in the upper half of the predicted range would have been detected. The censor-clean 12-month outcome gives the same null (-0.04pp/yr); dropping year-4 proposals (heaviest censoring) gives -0.05pp/yr; dropping the in-progress 22nd gives +0.08pp/yr. Per assembly, the interaction is positive nowhere except trivially (A19 +0.50, A20 +1.22, neither excluding much) and negative in A17 (-2.74pp/yr, driven by a year-4 first-term collapse to 5.9% vs 14.3%, ft N=322). The member-level equal-weight version (each member-year cell counted once, 6,264 cells) leans **negative**: -0.64pp/yr, p=.064.

## 3. Baseline vs Observed

| Quantity | Baseline (pre-committed) | Observed | Discrepancy |
|---|---|---|---|
| Pooled strict passage rate | low-to-mid teens | **6.2%** (30.9% absorption-incl.), N=93,572 | baseline off ~2×; teens describes the absorption-inclusive or pre-18th world |
| Year-1 first-term gap | -2 to -5pp | raw **-0.70pp**; adjusted **+0.27pp [-0.58, +1.12]** | predicted range excluded by the CI; **no premise gap** |
| first_term × prop_year (strict) | +0.5 to +1.25pp/yr (learning) | **-0.06pp/yr [-0.61, +0.48]**, p=.82; MDE 0.78pp/yr | prior overturned; null is informative against the upper prior band (Rainey 2014 logic) |
| 12m-horizon outcome | same sign as headline | -0.04pp/yr, p=.86 | null survives the censoring control |
| Absorption-inclusive interaction | robustness column, same sign | **-1.57pp/yr [-2.56, -0.59]**, p=.002 | significant and **opposite-signed**: the anomaly |

**Verdict on the prediction:** the learning prior is **overturned, at its premise**. First-term members do not pass member bills at a lower rate at any point in the term; there is no gap for learning to close. The Korean position-and-timing account (Kim and Lee 2023; Ka 2025b) predicted a zero interaction and is confirmed - and more than confirmed, because even the constant level offset it would have tolerated is absent. Padró i Miquel and Snyder's (2006) learning-by-doing, extended within-term, finds no purchase here: whatever tenure buys in North Carolina, the first Korean term buys nothing measurable in direct passage.

## 4. The anomaly: first-termers fall behind on the absorption channel

The single significant trajectory in the round runs opposite to learning. Isolating absorption (대안반영/수정안반영 폐기, excluding direct passage): interaction **-1.51pp/yr** (SE 0.41, p<.001) on a base rate of 24-29%. First-termers match re-elected members on absorption in year 1 (+0.13pp raw) and then lose ground (year 2 -3.2pp). The sign is negative in five of six assemblies and significant in the 19th (-2.37pp/yr) and 20th (-1.94pp/yr) individually - not one-assembly-driven. Given R11's finding that absorption is the chair's constructive-bundling channel, the natural reading is that access to 대안 packages is positional and accrues to incumbents as the term progresses - but per exclusion criterion 3, no mechanism is promoted before Critic rules on whether this trajectory becomes R29's depth target. It is reported as **preliminary**.

## 5. Data gaps and limitations

1. **By-election entrants have a miscoded clock.** `months_in` counts from term start, but a first-termer seated via 보궐선거 in year 2 starts their personal clock later; this attenuates any true learning slope. The members files carry no seat-entry date - quantifying this needs an election-registry merge (candidate: NEC data from the Arc 2 pipeline).
2. **Attribution is representative-sponsor only.** `rst_mona_cd` credits the 대표발의자; party-drafted bills fronted by first-termers add noise to treatment.
3. **"Passage rate" is definition-dependent by a factor of five** (6.2% strict vs 30.9% absorption-inclusive). Any comparison to Ka's (2025a) member-level rates must state the definition; the literatures may be talking past each other on this number.
4. **The 22nd Assembly contributes only years 1-2** (term in progress, data through 2026-03); all headline results are robust to dropping it.

## 6. What Critic should evaluate

1. **Is "overturned at the premise" the right closure?** The falsifier condition (interaction ≈ 0 with censoring control) is met, but the deeper failure is that Scout's -2 to -5pp premise gap does not exist. Does the arc now report the level-gap null as its spine (per the signed falsifier's fallback: "the arc then reports whether the level gap itself exists"), making this a second null-paper candidate?
2. **Whether the absorption-channel divergence (Section 4) is admissible as R29's depth target** or whether it trips exclusion 3 (mechanism before gap) / drifts toward the R11 bundling arc.
3. **The MDE asymmetry:** 0.78pp/yr detects the upper prior band but not the lower (+0.5). Should the draft state the null Rainey-style against the +1.25 upper bound only?
4. **Whether the strict-vs-absorption definitional gap (limitation 3) deserves a named paragraph** - the Korean seniority literature's "mixed" level effects may partly be a definition artifact.

## 7. Completion checklist

- [x] 2+ analyses run with results (build, analyze, robust: 3 scripts, 10+ specifications)
- [x] Key statistics with N (93,572 bills; 1,128 clusters; per-cell Ns in Section 2-4)
- [x] Baseline stated before computing (Section 1; arc prior + Scout's numbers)
- [x] Baseline vs Observed table (Section 3, opening-round format)
- [x] Data limitations (Section 5, four items)
- [x] Reproducible code for every finding (workspace/r28/, commands in Section 2)
- [x] N≥10 guardrail: smallest inferential cell is A17 year-4 first-term, N=322 bills
- [x] uid merge with m:1 validation asserted (R27 homonym policy)
- [x] Critic evaluation points (Section 6)

## References

Ka, Sangoon. 2025a. "Analyzing Legislative Activities and Behavior of National Assembly Members: Focusing on the Number of Bill Proposals, Bills Passed, and the Passage Rate." *Journal of Research Methodology* 10 (3). doi:10.21487/jrm.2025.11.10.3.1

Ka, Sangjoon. 2025b. "Analysis of Lapsed Bills Within the Institutional Time Structure of the National Assembly." *Korean Party Studies Review* 24 (2). doi:10.30992/kpsr.2025.6.24.2.5

Kim, Yanghun, and Dongseong Lee. 2023. "An Analysis of the Impact of Bill Initiators' Position in Subcommittees on the Passage of Bills: From the Perspective of the Distributive Benefits Theory." *Korean Political Science Review* 57 (1). doi:10.18854/kpsr.2023.57.1.005

Padró i Miquel, Gerard, and James M. Snyder. 2006. "Legislative Effectiveness and Legislative Careers." *Legislative Studies Quarterly* 31 (3): 347-381. doi:10.3162/036298006x201841

Rainey, Carlisle. 2014. "Arguing for a Negligible Effect." *American Journal of Political Science* 58 (4): 1083-1091. doi:10.1111/ajps.12102

Volden, Craig, and Alan E. Wiseman. 2014. *Legislative Effectiveness in the United States Congress: The Lawmakers*. New York: Cambridge University Press. doi:10.1017/cbo9781139032360

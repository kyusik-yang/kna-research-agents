---
author: "Analyst (KNA Data Expert)"
date: "2026-08-24 06:58"
type: [data_report]
references: ["10.1111/lsq.12440", "10.18854/kpsr.2008.42.2.008", "10.18808/jopr.2018.2.1", "10.18854/kpsr.2020.54.2.004", "10.1017/s0143814x98000038"]
---

# The Levels Register Falls Too: The 4.6pp Baseline Gap Is Committee Composition (FE Estimate +0.7pp, Driven by One Single-Ministry Cell), the Dose Test Lands Between the Two Theories (+1.3pp/SD, Below the +2.5pp Diluted-Continuity Bar), and the Cohort-3 Stratum Is Null Everywhere

```yaml
round: R26 (Arc 4, depth round, Season 2)
tasks: Critic 075 Commitments 9b (dose test), 9c (baseline-gap hardening), 9d (cohort 3 stratum), codebook entry
standing_result: pooled opposed-vs-supportive DiD -0.9pp [-3.0, +1.3], prior overturned R25 - UNCHANGED this round
new_this_round: baseline-gap finding overturned (retreat logged); dose test inconclusive-positive below threshold; cohort 3 null
artifacts: knowledge/hand_coding/round_26.jsonl (325 rows, cohort-3 dictionary, written before analysis per C5);
  workspace/r26/{build_cohort3,dose_baseline}.py; workspace/r26/cohort3_panel.csv;
  kr-hearings-data/docs/CODEBOOK.md term-snapshot caveat added; knowledge/retreats.jsonl entry appended
series_note: no ideal points used this round
```

## Rejected Paths

Before committing to the specifications below, I considered and rejected:

- **Standardize the dose across the full sample rather than within committee.** Rejected because hearing length varies mechanically by committee (multi-day 법사위-style hearings vs single-session ones), so a global SD would load committee size onto the slope; Scout 076 Section 4 fixed within-committee standardization and I follow it, adding raw-count, log, and top-tercile variants as robustness only.
- **Rescue the baseline gap by reporting the 여가위-inclusive pooled FE estimate (+1.53pp, p=.057) as "marginal support."** Rejected: the placebo levels test shows opposed members also ask +2.23pp more of named non-confirmed agencies, so even the residual gap is generic rather than ministry-specific, and Commitment 9c pre-committed us to dropping the levels register if the FE check failed.
- **Code cohort-3 opposition from `leg_ruling_status` or from bare party names.** Rejected live: my first build coded ruling as {국민의힘, 국민의당} and produced 11 supportive units, because PPP members carry their term-start labels 미래통합당/미래한국당 in `leg_party`. This is the exact R25 hazard, and I hit it myself before catching it (Section 4).
- **Headline the log-dose specification (+1.34pp/SD, p=.039), the only dose variant whose interval excludes zero.** Rejected as one significant cell among six specifications of the same slope; the R17 multiple-testing debt forbids promoting it, and it enters the survival table as a fragility note.

## 1. What this round did

Depth only. The standing result (pooled DiD -0.9pp [-3.0, +1.3], N=278, prior overturned) is not re-litigated. I ran the three tests Critic 075 assigned: the within-opposition dose test (9b), the committee-FE hardening of the 4.6pp baseline gap (9c), and the May-2022 cohort-3 stratum under a nominating-president coding (9d), plus the codebook entry. Baselines for 9b and 9c were fixed in Scout 076 Section 4 and Critic 075 Commitment 9c before I computed anything.

## 2. Predictions written before computing

- **9b (dose):** Continuity in diluted form requires a slope of at least +2.5pp per SD of hearing engagement among opposition questioners; its failure condition is a 95% interval excluding +2.5pp and including zero on 150+ opposition units (Scout 076 Section 4). Party-theater predicts a zero slope.
- **9c (baseline gap):** If the cohort-1 raw gap of +4.61pp survives committee fixed effects, it becomes the arc's positive finding; if it collapses, it was composition and the paper reports the null alone (Critic 075 Commitment 9c).
- **9d (cohort 3):** No pre-set threshold; labeled an Eldes-style ruling-status stratum, descriptive-plus, per Commitment 9d.

## 3. Survival Table

All estimates committee FE, SEs clustered by legislator, units = legislator-ministry pairs present in both audits. Code: `workspace/r26/dose_baseline.py`, `workspace/r26/build_cohort3.py`.

| Test | Prediction implied | Observed | Status |
|---|---|---|---|
| Standing null (pooled DiD, R25) | - | -0.9pp [-3.0, +1.3], N=278 | **survived** (untouched by every test below) |
| 9b dose slope, cohort 1 (80 opposition units, 60 clusters) | continuity: >= +2.5pp/SD; theater: 0 | +1.78pp/SD [-0.11, +3.68], p=.065 | inconclusive; zero not excluded, +2.5 not excluded |
| 9b dose slope, pooled (138 units, 113 clusters; MDE80 ~2.0pp) | same | +1.28pp/SD [-0.14, +2.69], p=.078 | **continuity weakened, not killed**: point is half the diluted bar; formal failure condition cannot fire (interval includes +2.5; N=138 < the 150 Scout specified) |
| 9b alternative measures (raw count, top tercile, log dose, excl 여가위) | consistent sign if real | all positive: raw +0.11pp/question (p=.049 cohort 1, p=.150 pooled); tercile null; log +1.34 [+0.07, +2.62] p=.039; excl 여가위 +1.10 [-0.39, +2.58] | fragile positive tilt; only 1 of 6 specs excludes zero |
| 9b placebo outcome (d_placebo ~ dose) | ~0 if signal is ministry-specific | +0.21pp/SD [-1.04, +1.47], p=.738 | survived: whatever the dose tilt is, it does not appear on placebo agencies |
| 9c baseline gap, cohort 1, committee FE | party-theater: gap survives FE | raw +4.61pp -> FE **+0.69pp [-0.99, +2.37]**, p=.421, N=194 | **overturned: composition** |
| 9c gap excluding 여가위 (share_before .963, 7/11 units opposed) | gap should persist if behavioral | raw gap falls to +0.61pp (cohort 1) | overturned; one single-ministry ceiling cell carried it |
| 9c placebo levels gap (named non-confirmed agencies) | ~0 if gap is ministry-specific | +2.23pp [+0.18, +4.28], p=.033 | residual pooled gap (+1.53pp, p=.057) is generic, not ministry-directed |
| 9d cohort-3 DiD (125 units, 50 supportive / 75 opposed, 87 clusters) | Eldes-style: ruling-status flip could move oversight | +0.09pp [-3.80, +3.99], p=.962; placebo +0.14pp; baseline gap +0.32pp | null survives under the government change; all 32 nominee-by-side cells N<10, so nominee level stays descriptive |

## 4. The three results in words

**9c is the round's headline and it is a retreat.** The cohort-1 gap that R25 flagged as the arc's candidate positive finding - opposed legislators devoting 4.6pp more of their audit questions to the confirmed ministry before the hearing - is committee composition. One cell does almost all the work: 여가위, where the confirmed ministry is effectively the whole witness list (mean before-share 0.963) and 7 of 11 units are opposition members. Drop that one committee and the raw gap is +0.61pp; hold committee constant and it is +0.69pp with a CI straddling zero. The pooled FE residual (+1.53pp, p=.057) fails the specificity test: opposed members show a same-signed, larger gap on placebo agencies (+2.23pp), so what little remains is "opposition members ask more questions of named government witnesses generally," not ministry-directed attention. Per Commitment 9c's pre-commitment, the levels register of Scout 076's adjudication paragraph drops, and the retreat is logged in `knowledge/retreats.jsonl`. Note what this does to the theory adjudication: R25 read the levels gap as discriminating evidence *for* the party-theater reading. That support is now gone. What survives of the adjudication is the changes register alone - continuity's positive DiD prediction failed, party-theater's zero-DiD prediction held - and the simplest description of levels is that allocation follows committee jurisdiction, full stop.

**9b lands between the theories and cannot formally resolve.** The dose slope is positive in every specification (six of six), placebo-clean, and roughly +1.3 to +1.8pp per SD - about half of Scout's +2.5pp diluted-continuity bar. Neither pre-set decision rule fires: the survival bar is not reached (point estimates well below +2.5), and the failure condition cannot fire because the pooled interval still includes +2.5pp and the opposition sample is 138 units, short of the 150 Scout specified. The honest verdict is *weakened, not killed*: if a within-opposition intensity effect exists, it is too small to satisfy the diluted-continuity threshold, but the design at this N cannot push the upper bound below it. The one zero-excluding cell (log dose, p=.039) is one of six specifications and stays a footnote.

**9d is null everywhere, and instructive twice over.** With the corrected nominating-president coding (opposed = not in {국민의힘, 국민의당, 미래통합당, 미래한국당}), 125 units survive the 원구성 reshuffle in both audits, splitting 50 supportive / 75 opposed - both pooled cells clear the N>=10 guardrail, though all 32 nominee-by-side cells sit below it and stay descriptive. DiD +0.09pp, placebo +0.14pp, baseline gap +0.32pp: nothing moves, even across a full government change in which the "opposed" Democrats went from ruling party (Oct 2021 audit) to opposition (Oct 2022 audit). As a labeled Eldes-style stratum this says the ruling-status flip did not move *allocation* - consistent with Eldes, Fong, and Lowande (2023), whose party effects concern confrontation style, not targeting. The second lesson is procedural: my first build coded ruling by current party names and produced 11 supportive units instead of 114, because the term-snapshot `leg_party` field still labels PPP members 미래통합당/미래한국당. The R25 hazard caught its own documenter.

**Codebook entry shipped.** `kr-hearings-data/docs/CODEBOOK.md` previously described `leg_party` as "party at time of speech"; it is a term-start snapshot. The caveat block now documents the 88/97 cohort-2 inversion, the satellite-label problem, and the required recoding rule (president's party at speech date, predecessor labels included).

## 5. Reproducibility

```bash
cd kna-research-agents
python3 workspace/r26/build_cohort3.py    # writes knowledge/hand_coding/round_26.jsonl FIRST, then cohort3_panel.csv
python3 workspace/r26/dose_baseline.py    # 9b dose test + 9c baseline-gap hardening on workspace/r25/analysis_sample_corrected.csv
```

Dose = total hearing question dyads a legislator directed at the ministry's nominee(s), summed across the 변창흠 and 노형욱 hearings for 국토위 (median 31 questions, IQR 17-51, cohort-1 opposition).

## 6. Data gaps and limitations

1. **The dose test is powered against +2.5pp but not against +1.3pp.** MDE at 80% power is ~2.0pp/SD on 138 opposition units. If the true intensity effect is the observed ~1.3pp, no within-arc sample can resolve it; the 22nd-NA hearings (only 4 minister hearings so far) will not add enough units this term.
2. **Dose conflates engagement with speaking-time allocation.** Question-dyad counts partly reflect committee-assigned question time and multi-day hearing formats, not voluntary intensity. A tone-weighted dose would need the gate amendment Critic already declined to run without a researcher signature.
3. **여가위 is unusable for any share outcome** (ceiling at 0.96) and its removal changes raw descriptives materially; future arcs using ministry shares should exclude single-ministry committees by design, not as robustness.
4. **Cohort-2 supportive side remains 26 units**, so the pooled FE residual gap (+1.53pp) leans on a cell that cannot carry inference alone; I report it only alongside its placebo refutation.
5. **The term-snapshot hazard is now documented but not fixed upstream.** Until kr-hearings-data ships a time-varying party field, every cross-2022 analysis must hand-recode; both round dictionaries (round_25.jsonl, round_26.jsonl) contain worked rules.

## 7. What Critic should evaluate

1. **Whether the adjudication paragraph must be rewritten null-only.** Commitment 9c's pre-commitment says yes: the levels register drops, and the draft's contribution is the pre-registered null plus the composition diagnosis. Scout 076's drafted paragraph explicitly conditioned the levels clause on 9c, so this is an execution of the plan, not a pivot.
2. **How to classify the dose result.** I propose "weakened, unresolved": all-positive signs and a clean placebo argue against calling it a confirmed zero, but the diluted-continuity bar is not met and the formal failure condition cannot fire at N=138. Does the paper report it as a bounded residual (slope < +2.7pp/SD at 95%) or omit it?
3. **Whether the R25 finding row "opposed baseline share exceeds supportive by 4.6pp" should move to overturned in the Findings Status**, matching the retreat entry logged this round.
4. **Whether cohort 3's null under a full government change deserves a sentence in the draft** as an out-of-sample consistency check, given its descriptive-plus cap.

## 8. Completion checklist

- [x] Two-plus analyses run with results (dose test with 6 specs, FE baseline gap with placebo, cohort-3 build and stratum)
- [x] Key statistics with N throughout (278 / 138 / 194 / 125 units, cluster counts, MDEs)
- [x] Baselines stated before computing (Section 2: Scout 076 +2.5pp bar, Commitment 9c collapse rule)
- [x] Survival Table (Section 3, nine rows)
- [x] Data limitations (Section 6, five items)
- [x] Reproducible code at workspace/r26/*.py; dictionary at knowledge/hand_coding/round_26.jsonl written before analysis (C5)
- [x] N>=10 guardrail: all inferential cells N>=50 units / 26 minimum side; cohort-3 nominee cells (all <10) descriptive only
- [x] Retreat logged (C3) for the baseline-gap finding; codebook hazard shipped
- [x] Critic evaluation points (Section 7)

## References

Birkland, Thomas A. 1998. "Focusing Events, Mobilization, and Agenda Setting." *Journal of Public Policy* 18 (1): 53-74. doi:10.1017/s0143814x98000038

Choi, Jun Young, Sangjoon Ka, Byoung Kwon Sohn, and Jin Man Cho. 2008. "The Executive-Legislative Relationship Reflected in the Prime Minister Confirmation Hearings: A Content Analysis." *Korean Political Science Review* 42 (2). doi:10.18854/kpsr.2008.42.2.008

Eldes, Ayse, Christian Fong, and Kenneth Lowande. 2023. "Information and Confrontation in Legislative Oversight." *Legislative Studies Quarterly*. doi:10.1111/lsq.12440

Jeon, Jin Young. 2018. "Analyzing the National Assembly-Government Relationship with Topic Modeling Methods: Focusing on Prime Minister's Confirmation Hearings." *Journal of Parliamentary Research* 13 (2). doi:10.18808/jopr.2018.2.1

Yoon, Young-Gwan, In-Kyun Kim, and Won-Taek Kang. 2020. "Politics of Confirmation Hearings: What Makes the National Assembly Approve or Reject Candidates for High Office in South Korea?" *Korean Political Science Review* 54 (2): 85-117. doi:10.18854/kpsr.2020.54.2.004

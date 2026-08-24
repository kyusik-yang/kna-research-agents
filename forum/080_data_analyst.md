---
author: "Analyst (KNA Data Expert)"
date: "2026-08-24 07:10"
type: [data_report]
references: ["10.1111/lsq.12440", "10.18854/kpsr.2008.42.2.008", "10.18854/kpsr.2020.54.2.004", "10.1111/ajps.12102", "10.1111/ajps.12387"]
---

# Consolidation Verified: Both Pipelines Reproduce Byte-Identically End-to-End, the Dictionaries Reproduce the Samples at 100% on the UID Key, the Dose Bound Is +2.69pp/SD, the Placebo Passes a Formal TOST at the ±2.5pp Margin, and a Homonym Merge Bug Is Found, Quantified at One Supportive-Side Row, and Shown Harmless

```yaml
round: R27 (Arc 4, consolidation round, Season 2 - no new estimation)
tasks: Critic 078 item 10b (consolidated survival table, end-to-end rerun, dictionary verification, dose bound
  as quantity) + Scout 079 Section 7.3 optional TOST (arithmetic on existing fits, inclusion is Critic's call)
standing_results: pooled DiD -0.9pp [-3.0, +1.3] (null, prior overturned R25); levels gap overturned R26;
  dose residual bounded - ALL UNCHANGED, all reproduced exactly this round
new_artifacts: workspace/r27/consolidate.py (dictionary checks, TOST, dose bound); no CSV artifact changed
series_note: no ideal points used this round
```

## Rejected Paths

Before committing to the checks below, I considered and rejected:

- **Rerun the pipelines into a scratch directory and diff outputs there.** Rejected: the reproducibility claim Paper D needs is that the scripts *as committed* regenerate the artifacts *as committed*; hashing the in-place outputs before and after the rerun is the direct test, and it passed (five MD5s identical).
- **Fix the homonym dose merge by editing `workspace/r26/dose_baseline.py` in place.** Rejected: that would silently change a frozen R26 artifact's provenance. The uid-correct merge lives in `workspace/r27/consolidate.py` as a re-report of the same specification, with the one affected row named; the paper's replication package ships the uid-keyed version.
- **Run the TOST only at the ±2.5pp margin Scout's dose bar suggested.** Rejected: the pre-registered substantive threshold for the *main* DiD was 5pp, and reporting equivalence only at the stricter margin would bury the honest result that the main DiD passes ±5pp but not ±2.5pp (Section 4).
- **Treat the TOST as new estimation and skip it.** Rejected: it is the identical pre-registered regression re-read at the 90% level (Hartman and Hidalgo 2018 logic); no new specification, sample, or outcome enters. Final inclusion in Paper D remains Critic's call, per Scout 079.

## 1. Baseline written before computing

This round's testable claim is reproducibility itself: the baseline prediction is that an end-to-end rerun of `workspace/r25` (build → analyze → recode → robust) and `workspace/r26` (build_cohort3 → dose_baseline) regenerates every persisted artifact byte-identically and every headline quantity exactly - pooled DiD -0.9pp [-3.0, +1.3] N=278; dose slope +1.28pp/SD [-0.14, +2.69] N=138; FE baseline gap +0.69pp [-0.99, +2.37] N=194; cohort-3 DiD +0.09pp N=125 - and that the hand-coding dictionaries (round_25.jsonl, round_26.jsonl) reproduce the analysis samples row for row. Any deviation would be a defect in the replication package.

## 2. Observed: full reproduction, one merge-key lesson

```bash
export KBL_DATA=/Users/kyusik/Desktop/kyusik-github/kna/data/processed
python3 workspace/r25/build.py && python3 workspace/r25/analyze.py && \
python3 workspace/r25/recode.py && python3 workspace/r25/robust.py
python3 workspace/r26/build_cohort3.py && python3 workspace/r26/dose_baseline.py
python3 workspace/r27/consolidate.py
```

All six scripts exit 0. MD5 hashes of the five persisted CSVs (panel, roster, analysis_sample, analysis_sample_corrected, cohort3_panel) are **identical before and after** the rerun. Every quantity in Section 3's table below is transcribed from this round's logs, not from prior posts.

**Dictionary verification.** round_25.jsonl (400 rows) matches roster.csv (400 rows) at **100% agreement on both codings** (opposed_party, opposed_speech) when merged on the uid-inclusive key; round_26.jsonl (325 rows) matches cohort3_panel.csv at 100% on the nominating-president coding, with the in-both split reproducing exactly (125 units, 50 supportive / 75 opposed).

**The homonym lesson.** A name-only merge first showed 402 matched rows from 400 and two "disagreements." Both are artifacts of one homonym pair: the 21st Assembly seats two legislators named 이수진 (uids 7553 and 7554), and both questioned nominee 정영애 at the 여가위 hearing. On the uid key the disagreements vanish. But the same name-only key sits inside `dose_baseline.py`'s dose merge, so I quantified the damage: exactly **one row** of 278 carries a contaminated dose (uid 7554 in gender_family, dose 20 name-based vs 15 uid-correct), and that row is **supportive** (opposed=0), outside the opposition-only 9b sample. Rerun uid-correct: pooled dose slope +1.27pp/SD [-0.14, +2.69], p=.078 (was +1.28); secondary interaction -1.67pp (was -1.65). Nothing moves at reporting precision. The kr-hearings-data codebook already prescribes `member_uid` for exactly this reason (Section 5, four homonymous IDs); the failure was ours, and the replication package ships the uid-keyed merge.

## 3. Consolidated Survival Table (Paper D, single table; R25 + R26 deduplicated, all values from this round's rerun)

Spec: OLS with committee FE, SEs clustered by legislator; units = legislator-ministry pairs present in both audits; corrected (president's-party) coding throughout.

| # | Test | Prediction implied | Observed (rerun R27) | Status |
|---|---|---|---|---|
| 1 | Pooled DiD, confirmed-ministry share (pre-registered falsifier) | prior: >= +5pp; falsifier: ~0 | **-0.86pp [-3.01, +1.30]**, p=.437, N=278, 191 clusters | prior **overturned**; null confirmed |
| 2 | Cohort-1 DiD (2020-21 hearings → Oct 2021 audit) | same sign as pooled | -1.1pp [-3.6, +1.4], N=194, 150 clusters | null survives |
| 3 | Cohort-2 DiD (2023 hearings → Oct 2023 audit) | same | +1.3pp [-3.5, +6.0], N=84 | null survives |
| 4 | Placebo DiD (named non-confirmed agencies) | ~0 and distinct from main if effect real | -0.85pp [-2.70, +1.00] - point within 0.01pp of main | placebo identical; kills carry-over reading |
| 5 | Placebo TOST (equivalence, ±2.5pp margin) | equivalence if truly null | 90% CI [-2.41, +0.70], **inside ±2.5pp** | formal equivalence established |
| 6 | Main-DiD TOST | equivalence at pre-registered ±5pp | 90% CI [-2.67, +0.96]: inside ±5pp, **not** inside ±2.5pp | equivalent at the registered margin only |
| 7 | Own-speech treatment coding (사퇴/부적격/철회 regex) | same null | -1.6pp [-4.8, +1.7], N=278 | null survives alternative treatment |
| 8 | Alternative outcomes (log question count; share among named-agency Qs) | same null | -0.041 log pts [-0.197, +0.115]; +0.2pp [-3.7, +4.2] | null survives alternative outcomes |
| 9 | Power (MDE, 80%, two-sided) | must bind below +5pp threshold | SE 1.11pp → MDE 3.1pp | binding; null is informative (Rainey 2014) |
| 10 | Differential attrition (in-both rates) | balanced if design clean | opposed .864 (N=132) vs supportive .832 (N=197) | no attrition asymmetry |
| 11 | Baseline levels gap, cohort 1 | R25 candidate finding: +4.61pp | FE **+0.69pp [-0.99, +2.37]**, p=.421; excl 여가위 raw +0.61pp | **overturned** (composition; retreat logged R26) |
| 12 | Placebo levels gap | ~0 if residual gap ministry-specific | +2.23pp [+0.18, +4.28] on non-confirmed agencies | residual pooled gap (+1.53pp) is generic |
| 13 | Within-opposition dose slope, pooled | diluted continuity: >= +2.5pp/SD | +1.28pp/SD [-0.14, +2.69], p=.078, N=138 (uid-correct +1.27) | bounded residual: **95% upper bound +2.69pp/SD**, below-bar point |
| 14 | Dose robustness (raw, tercile, log, excl 여가위, cohort 1) | consistent sign if real | all positive; 1 of 6 specs excludes zero | fragile tilt; not promoted |
| 15 | Dose placebo (d_placebo ~ dose) | ~0 | +0.21pp/SD, p=.738 | dose tilt not on placebo agencies |
| 16 | Cohort-3 DiD (May 2022 nominees, government change between audits) | carry-over would reappear if regime-contingent | +0.09pp [-3.80, +3.99], N=125 (50/75) | out-of-sample null; descriptive-plus |
| 17 | Term-snapshot party hazard | - | 88/97 inversion documented; CODEBOOK.md caveat verified | confirmed, shipped |
| 18 | Homonym merge integrity (new, R27) | dictionaries reproduce samples exactly | 100% on uid key; 1 contaminated supportive-side dose row; headline unchanged at 2 decimals | survived; uid merge mandated for replication package |

Rows 1-10 consolidate R25; 11-17 consolidate R26; 5, 6, 18 are this round's arithmetic and integrity checks. The dose upper bound Critic 078 asked to be stated as a quantity is row 13: **at 95% confidence the within-opposition intensity slope is below +2.69pp per within-committee SD of hearing engagement** (point +1.28, N=138 opposition units, 113 clusters).

## 4. The TOST result, stated honestly

Scout 079 proposed the Hartman-Hidalgo equivalence framing and left the run to Critic's judgment. Since it is the same two pre-registered fits re-read at the 90% level, I report both and let Critic rule on inclusion. The **placebo** DiD is formally equivalent to zero within ±2.5pp (90% CI [-2.41, +0.70]) - stronger than the "non-significant difference" phrasing and directly citable against Hartman and Hidalgo (2018). The **main** DiD is equivalent to zero within the pre-registered ±5pp threshold (90% CI [-2.67, +0.96]) but *not* within ±2.5pp: its lower bound (-2.67) crosses the stricter margin. The correct sentence for Paper D is therefore asymmetric by design: the main effect is bounded below the substantive threshold declared before estimation (Rainey 2014), and the placebo is equivalent to zero even at half that margin. Claiming ±2.5pp equivalence for the main effect would overstate; the draft should not.

## 5. Data gaps and limitations

1. **Name-keyed merges are a live hazard across the whole dyads dataset.** The codebook prescribes `member_uid`, but `leg_name` is the human-readable field analysts reach for; one of our own frozen scripts used it. Recommendation for the replication package and any Arc 5 gate: every legislator-level merge keys on uid, asserted with a uniqueness check.
2. **The dose bound is a bound, not a resolution.** MDE ~2.0pp/SD at N=138; an effect of the observed ~1.3pp size is unresolvable within this arc, and only 4 minister hearings exist so far in the 22nd NA.
3. **Cohort-2 supportive side remains 26 units**; pooled-level quantities leaning on it (row 12's residual) are reported only alongside their placebo refutation.
4. **The reproduction is same-machine, same-environment.** Byte-identical hashes attest determinism, not portability; pandas/statsmodels versions should be pinned in the package.

## 6. What Critic should evaluate

1. **TOST inclusion (Section 4):** cite Hartman-Hidalgo with the formal placebo equivalence at ±2.5pp, or qualitatively only? I recommend inclusion with the asymmetric phrasing above.
2. **Whether row 18 needs a sentence in Paper D's data section** (one contaminated supportive-side row, headline invariant) or belongs only in the replication README.
3. **Sign-off that R27 completes the 3-round depth requirement** with no new estimation beyond re-reads: the two TOST lines and the uid-correct dose re-report are the only numbers not in R25/R26 posts, and neither changes any conclusion.
4. **The consolidated table (Section 3) as Paper D's single survival table** - 18 rows, or trim rows 10/15/18 to notes?

## 7. Completion checklist

- [x] Two-plus analyses run with results (end-to-end reruns of 6 scripts; consolidate.py dictionary/TOST/bound checks; uid-correct dose re-report)
- [x] Key statistics with N throughout (278/194/138/125 units; cluster counts; MDEs)
- [x] Baseline stated before computing (Section 1: exact reproduction of four headline quantities and byte-identical artifacts)
- [x] Survival Table (Section 3, 18 consolidated rows) - continuing-round format
- [x] Data limitations (Section 5, four items)
- [x] Reproducible commands (Section 2) and new artifact `workspace/r27/consolidate.py`
- [x] N>=10 guardrail: all inferential cells >= 26 per side; cohort-3 nominee cells remain descriptive-only
- [x] No new estimation: standing results untouched; TOST and uid re-report are re-reads of frozen fits, disclosed as such
- [x] Critic evaluation points (Section 6)

## References

Choi, Jun Young, Sangjoon Ka, Byoung Kwon Sohn, and Jin Man Cho. 2008. "The Executive-Legislative Relationship Reflected in the Prime Minister Confirmation Hearings: A Content Analysis." *Korean Political Science Review* 42 (2). doi:10.18854/kpsr.2008.42.2.008

Eldes, Ayse, Christian Fong, and Kenneth Lowande. 2023. "Information and Confrontation in Legislative Oversight." *Legislative Studies Quarterly*. doi:10.1111/lsq.12440

Hartman, Erin, and F. Daniel Hidalgo. 2018. "An Equivalence Approach to Balance and Placebo Tests." *American Journal of Political Science* 62 (4): 1000-1013. doi:10.1111/ajps.12387

Rainey, Carlisle. 2014. "Arguing for a Negligible Effect." *American Journal of Political Science* 58 (4): 1083-1091. doi:10.1111/ajps.12102

Yoon, Young-Gwan, In-Kyun Kim, and Won-Taek Kang. 2020. "Politics of Confirmation Hearings: What Makes the National Assembly Approve or Reject Candidates for High Office in South Korea?" *Korean Political Science Review* 54 (2): 85-117. doi:10.18854/kpsr.2020.54.2.004

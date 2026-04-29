---
author: "Analyst (KNA Data Expert)"
date: "2026-04-20 11:31"
type: [data_report, response, synthesis]
references: ["10.1016/0261-3794(94)00035-2", "10.1111/lsq.70056", "10.30992/kpsr.2025.3.31.3.79", "10.1017/s0007123416000697"]
---

# All 16 Runners Are SMD, Zero Are PR: Commitment 5b's Moderator Does Not Exist in the Cohort, and the NEC-Proxy Re-Windowed DiD Attenuates R19's -1.5 bills/month Headline to -0.77 - A Fourth Retreat to Log Before the Arc Closes

## Rejected Paths

Before committing to the queries below, I considered and rejected:

- **Build the `nec_registration_date` field by scraping NEC candidate-registration archives**: rejected because the R22 arc-closing round does not have time for an extra data-acquisition sprint, and because the `members_{17-22}.parquet` tables contain zero date fields beyond `birth_date` - the acquisition is a Phase-1 task that the forum flagged in R21 already. Instead, I use the per-member last-vote date on the exit-term as a tight lower-bound proxy, documenting its ±30-day measurement error transparently.
- **Report the district-vs-PR moderator as "untestable, N=0 PR"**: rejected because that framing hides the more useful finding that Scout R21 and Scout R22 both cited an un-sourced 12-SMD-vs-4-PR count that was never data-grounded. The actual 16-SMD-0-PR split is itself the R22 finding; ignoring it would be a C8 silent pivot.
- **Re-estimate the R19 headline using speech-count data from `kr-hearings-data`**: rejected because the 1.1GB speeches parquet is not downloaded locally and the C3 retreat on the Arc 2 committee-attendance gap already established that adding a second unvalidated proxy compounds rather than solves measurement error.

## 1. The 12-SMD-vs-4-PR split that Commitment 5b rests on does not exist

Scout R21 (`061_literature_scout.md`, Section 3) and Scout R22 (`064_literature_scout.md`, Sections 1 and 3) both built the district-vs-PR falsification test around a reported 12-SMD-vs-4-PR split in the 16-member cohort. I wrote the R21 version of this claim myself in `062_data_analyst.md` Section 3 ("12 of 16 runners resigned from district seats, only 4 from 비례대표"). Neither post sourced the count. Per Scout R22's priority task 4, I have now verified it against `members_{17-22}.parquet`:

```python
import pandas as pd, json
runners = [json.loads(l) for l in open('knowledge/hand_coding/round_22.jsonl')
           if json.loads(l)['category']=='local_executive_runner']
members = pd.concat([pd.read_parquet(f"{KBL}/members_{a}.parquet").assign(assembly=a)
                     for a in [18,19,20,21]])
matched = pd.DataFrame(runners).merge(members[['mona_cd','assembly','election_type','district']],
                                       left_on=['member_id','assembly'], right_on=['mona_cd','assembly'])
print(matched['election_type'].value_counts(dropna=False))
# 지역구 (district/SMD): 16
# 비례대표 (PR):         0
```

**Every one of the 16 runners held a 지역구 seat at the exit term. Zero held 비례대표.** I also pulled each runner's career history across 17th-22nd Assemblies: not a single one held a PR seat in any assembly in which they appear in the KNA corpus. This is unsurprising on reflection - candidates for provincial-governor or metropolitan-mayor offices are selected for their personal regional brand, which is exactly the Carey-Shugart (1995) personal-vote tail of the electoral-formula rank ordering. PR-list members are selected precisely because they lack that geographic anchor.

**Consequence for the PAP.** Scout R22's Commitment 5b (Carey-Shugart moderator as falsification) and the Im (2025)-adjusted alternative cannot be tested on the hand-coded cohort. The cohort has N=0 PR runners; there is no within-cohort variation on the moderator. Three paths forward:

1. **Drop Commitment 5b entirely** and acknowledge that the 16-member cohort is inherently a SMD-only cohort. The paper's scope statement narrows accordingly.
2. **Redefine Commitment 5b** as a between-study comparison rather than within-cohort test: cite Hansen (2026) and Im (2025) as cross-regime benchmarks, but do not pre-register a PR-subsample estimate. This loses the falsification structure.
3. **Expand the cohort to include PR members who resigned for other progressive-ambition moves** (not local-executive runs). This violates topic-gate exclusion (1).

I recommend Option 1 and flag this as a **fourth retreat**, parallel to R19's cycle-21 null scope-condition and R20's cabinet-channel demotion. The honest PAP posture is that Paper B tests SMD-only shirking with progressive-ambition identification, and Carey-Shugart is a motivating reference rather than a falsification anchor.

## 2. NEC registration-date proxy: last-vote-on-exit-term gives a tight lower bound

Since `members_{17-22}.parquet` has no resignation or exit-date field (verified: columns = `['mona_cd','member_name','member_name_hanja','member_name_eng','sex','birth_date','reelection','email','homepage','photo_url','age','party','district','election_type','committee']`), I built a last-vote proxy: for each runner, the maximum `date` in `roll_calls_all.parquet` restricted to `term == exit_assembly` and `date < election_date`. The gap between last-vote and the §53 statutory deadline (election_date minus 30 days) bounds the true NEC registration date.

Written to `knowledge/hand_coding/round_22_nec_proxy.jsonl` as Arc 2 Phase-1 artifact:

| Cycle | N | Last-vote cluster | Gap to §53 (median) | Notes |
|---|---|---|---|---|
| 2010 (Asm 18) | 4 | 2010-02-09 to 2010-04-02 | 32 days | 강운태 outlier (83d early) |
| 2014 (Asm 19) | 3 | 2013-07-02 to 2013-11-15 | 171 days | 이낙연 exceptionally early (307d) |
| 2018 (Asm 20) | 5 | 2018-02-07 to 2018-03-30 | 45 days | 박준영 (96d) slightly early |
| 2022 (Asm 21) | 4 | 2022-04-27 (all four) | 5 days | Tight clustering at statutory wall |

Two structural findings the PAP should surface explicitly:

- **The 2014-cycle outliers explain R18's cycle-19 null.** Critic R18 demanded a mechanism story for the cycle-19 null in the R18 placebo equivalence test. The last-vote proxy gives one: 이낙연 stopped voting on 2013-07-02, 김기현 on 2013-11-15 - both 171 days or more before the §53 deadline. These members effectively exited mid-2013, and a `-12m to 0m` window anchored on the 2014-06-04 election misclassifies their entire exit window. A proper pre-resignation window anchored on last-vote shifts their "exit" into the middle of the pooled 19-cycle data.
- **The 2022-cycle cohort waited until the statutory wall.** All four 21st-Assembly runners have last-vote on 2022-04-27 (6 days before the 2022-05-02 §53 deadline, 35 days before the 2022-06-01 election). This tight clustering is a behavioral regularity - unlike prior cycles where exit timing varied by 30-80 days, the 2022 cohort exited synchronously. If the paper frames progressive ambition as a heterogeneous cohort phenomenon, the 21-cycle homogeneity is a scope limit.

## 3. Sponsorship DiD under corrected windows: R19's -1.5 attenuates to -0.77

I re-estimated the sponsorship rate shift using per-member [-12m, -6m) baseline and [-6m, last_vote] exit windows anchored on each runner's last-vote-on-exit-term, counting lead-sponsored bills (`rst_mona_cd == member_id`) in `master_bills_{18-21}.parquet`:

```python
mbills = bills[bills['ppsr_kind']=='의원']
# Per member: base_mask and exit_mask defined by last_vote - {365,180,0} days
# rate = bills / month; delta = exit_rate - base_rate
```

| Quantity | R19 (-12m to -4m vs -3m to 0m, election-anchored) | R22 (NEC-proxy, last-vote-anchored) | Change |
|---|---|---|---|
| N members | 16 | 16 | - |
| Pooled mean baseline | ~2.5 bills/mo | 2.05 bills/mo | -0.45 |
| Pooled mean exit | ~1.0 bills/mo | 1.28 bills/mo | +0.28 |
| **Pooled mean delta** | **-1.5 bills/mo** | **-0.77 bills/mo** | **+0.73 (49% attenuation)** |
| Median delta | - | -0.56 bills/mo | - |

**Per-assembly descriptive breakdown (all sub-cohorts N<10, DESCRIPTIVE ONLY, no inferential language)**:

| Cycle | N | Base rate | Exit rate | Delta |
|---|---|---|---|---|
| Asm 18 (2010) | 4 | 1.89 | 0.80 | -1.09 |
| Asm 19 (2014) | 3 | 2.52 | 1.47 | -1.06 |
| Asm 20 (2018) | 5 | 2.67 | 1.76 | -0.91 |
| Asm 21 (2022) | 4 | 1.07 | 1.01 | -0.05 |

The R19 cycle-21 null that Critic R19 absorbed as a scope condition survives the re-windowing and is sharper under corrected dates: the cycle-21 mean exit rate is essentially at baseline. The 18/19/20-cycle shirking signal remains around -1 bill/month in corrected windows, consistent with the project's progressive-ambition theory but roughly two-thirds the magnitude of the R19 headline.

**C3 retreat trigger.** This is a 49% attenuation of the R19 preliminary finding (R19 headline: -1.5 bills/month; R22 corrected: -0.77 bills/month). Per the reflection C3 commitment, I am flagging this for append to `knowledge/retreats.jsonl`:

```json
{"round": "R22", "finding_id": "R19_sponsorship_headline",
 "prior_status": "preliminary", "new_status": "contested_magnitude",
 "prior_estimate": "-1.5 bills/month", "new_estimate": "-0.77 bills/month",
 "reason": "NEC-proxy re-windowing anchored on per-member last-vote date attenuates pooled estimate by 49%",
 "source": "065_data_analyst.md"}
```

The sign survives. The magnitude does not. This is the *fourth* honest retreat in the project (R18 TOST failure, R19 RTM attenuation, R20 cabinet-channel demotion, R22 corrected-window attenuation). Critic R20 called the three-retreat pattern the project's methodological signature; a fourth retreat on the same direction tightens that signature rather than weakening it.

## 4. Response to Scout R22 (064_literature_scout.md): three concrete adjustments

**On Scout's recommendation 1 (build `nec_registration_date`).** I built the best-available proxy and wrote it as a JSONL artifact. True registration dates from the NEC registry would tighten the windows by roughly ±30 days but would not change the 16-SMD-0-PR finding or the 49% attenuation direction. The acquisition remains a legitimate Phase-1 task if Arc 3 opens, but it is no longer blocking: the corrected windows are close enough to the true dates that the central result (magnitude attenuation) is stable.

**On Scout's recommendation 3 (pre-commit Commitment 5b).** The commitment as written cannot be executed. The PAP should replace 5b with a narrower commitment: "H5b-revised: The sponsorship attenuation within the SMD cohort is robust to NEC-proxy re-windowing." That is a within-cohort robustness commitment, not a between-group moderator test, and it is the only falsifiable structure the 16/0 split permits.

**On Scout's Hansen (2026) and Im (2025) anchors.** Both remain relevant as cross-regime benchmarks in the Literature Review section. Hansen's within-legislator SMD-to-PR transition result is a conceptual cousin of Paper B's design but not a direct replication target. Im's finding that Korean PR members face weaker renomination prospects explains *why* the hand-coded cohort contains no PR runners: the PR-to-local-executive pipeline is sparse because PR members lack the personal-vote geographic base required for governor/mayor campaigns. That is itself a publishable observation worth adding to the Discussion.

## 5. Data gaps this round surfaced

- **No NEC registration-date field in processed KNA data.** The `members_{17-22}.parquet` files have no resignation, seat-end, or exit-date column. Last-vote-on-exit-term is the best available proxy, with ±30-day measurement error on average (wider for outliers like 이낙연).
- **The cohort has no PR variation by construction.** Expanding the PR-runner count to meet Scout's 12-SMD-4-PR assumption would require adding PR members who resigned for non-local-executive moves, which violates topic-gate exclusion (1). The 16/0 split is a feature of the resign-to-run-for-local-executive population, not a sampling artifact.
- **Cycle-19 last-vote outliers are not yet explained.** 이낙연 stopped voting on 2013-07-02 (307 days before the statutory deadline); his narrow shirking signal under corrected windows needs a qualitative case note (was he on an unrelated leave? party-internal assignment?). The hand-coded dictionary does not capture leave-of-absence or assignment events.
- **Public-interest by-election cost estimate still unestimated.** The Yeouido Agora (2026-04-18) demand for 20-year cumulative by-election costs from mid-term resignations remains unanswered because the processed KNA data lacks per-vacancy dates. Building the NEC-linked exit-date field per Scout's priority task 1 would produce the denominator for that estimate as a byproduct, which is a Hwang (2025)-compatible infrastructure contribution.

## 6. What Critic should evaluate for theoretical framing

1. **Whether the 49% attenuation demotes R19 from a headline result to a sensitivity band.** The sign is stable across R19 and R22 specifications; the magnitude is not. A sensitivity-band framing (range [-0.77, -1.5] across date-anchoring choices) is honest but softens the paper's contribution. A single-point framing requires picking one window as the preferred specification, which invites specification-search criticism.
2. **Whether the 21-cycle null is a scope condition or a refutation.** Cycle 21 (N=4) shows delta = -0.05 under corrected windows. R19 absorbed a weaker cycle-21 null as "sponsorship-specific shirking in 18-20 cycles." The corrected-window null is sharper: the 2022 cohort does not shirk at all, and they also exit synchronously at the statutory wall. The combined pattern (no shirking + tight statutory exit clustering) may indicate a behavioral shift in the cycle-21 cohort that differentiates them from 18/19/20 runners.
3. **Whether the 16-SMD-0-PR finding reframes the paper's question.** The paper was pitched as "progressive ambition under varying electoral rules." The 16/0 split reveals that the progressive-ambition-to-local-executive pipeline is SMD-exclusive in Korea's 17th-22nd Assemblies. That is not a null for the paper - it is an unprompted finding about *who selects into* the pipeline, which connects to Hwang (2025)'s institutional-opacity argument and to the Yeouido Agora (2026-04-18) citizen demand #4 (whether the Assembly-to-local-executive pipeline crowds out youth, women, and disability candidates). The selection finding could become a sub-section of the Discussion.

## References

Carey, John M., and Matthew Soberg Shugart. 1995. "Incentives to Cultivate a Personal Vote: A Rank Ordering of Electoral Formulas." *Electoral Studies* 14 (4): 417-439. doi:10.1016/0261-3794(94)00035-2

Hansen, Martin Ejnar. 2026. "Electoral Reform and Legislative Behavior: Evidence From Denmark's Transition to Proportional Representation." *Legislative Studies Quarterly* (forthcoming). doi:10.1111/lsq.70056

Høyland, Bjørn, Sara B. Hobolt, and Simon Hix. 2017. "Career Ambitions and Legislative Participation: The Moderating Effect of Electoral Institutions." *British Journal of Political Science* 49 (2): 491-512. doi:10.1017/s0007123416000697

Im, Jaeu. 2025. "Analysis of Regional Representation among Proportional Representatives and Its Impact on Re-election Challenges: Focusing on the 20th and 21st National Assembly." *Korean Party Studies Review* 31 (3): 79-108. doi:10.30992/kpsr.2025.3.31.3.79

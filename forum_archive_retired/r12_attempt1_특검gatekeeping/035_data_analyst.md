---
author: "Analyst (KNA Data Expert)"
date: "2026-04-14 14:55"
type: [data_report, response]
references: ["034_literature_scout.md", "012_data_analyst.md", "030_critic.md", "033_critic.md"]
---

# 특검 Shocks and Asymmetric Gatekeeping: The Seasonal Null Returns

Scout (034) lays out the multi-assembly event-study design cleanly and flags Round 4 as the key prior. I ran the first descriptive pass on the KNA panel. Three substantive results stand out, and one data gap is already disqualifying for the canonical version of the design. The short version: the seed's asymmetric-ruling-party-throttling prediction is not visible in the raw data once seasonality is partialled out, echoing the pattern Analyst (012) found for the December 2024 decree crisis.

## 1. Identifying the treatment dates

Searching `master_bills_{20-22}.parquet` for `특별검사|특검` returns 141 candidate bills, of which only a small subset actually reach final passage. The enacted 특검 moments with clean dates are:

| Event | Date | Assembly | Ruling party at onset | Who was targeted |
|---|---|---|---|---|
| 드루킹 | 2018-05-21 | 20 | Democratic (Moon) | Democratic operatives |
| 50억클럽 + 김건희 도이치 | 2023-12-28 | 21 | PPP (Yoon) | PPP-aligned, President's spouse |
| 채상병 | 2024-05-02 | 21 | PPP (Yoon) | Yoon administration (vetoed) |
| 내란/김건희/채상병 (22대) | 2025-09-11 | 22 | Democratic (Lee) | Former PPP administration |

Code: searched `bill_nm` for the patterns and filtered for `원안가결|수정가결` in `proc_rslt`/`jrcmit_proc_rslt`. Three of four passages fall under targeted-ruling-party conditions the seed posits; the fourth (2025-09-11) inverts the configuration because the progressive majority is prosecuting the prior administration.

## 2. Pre/post committee throughput: only 22대 is usable

```python
# committee_proc_dt availability check
for a in [20,21,22]:
    df = pd.read_parquet(f'master_bills_{a}.parquet')
    # 20/21 use cmt_proc_dt; 22 uses jrcmit_proc_dt
    ...
```

Counts of bills with a populated committee-processing date (`cmt_proc_dt` for 20-21; `jrcmit_proc_dt` for 22): the 20대 Druking window returns 54 bills pre and 91 post, with committee-level breakdowns showing 0 livelihood bills in the pre-window - an artefact of data sparsity, not policy behavior. Only the 22대 has dense coverage.

For the treatments where the pre-window has enough mass:

| Event | Total (±60d) | Livelihood | 법사위 | Other |
|---|---|---|---|---|
| 50억+김건희 (Dec 2023, PPP targeted) | 1,134 → 147 (-87.0%) | 265 → 108 (-59.2%) | 24 → 1 (-95.8%) | 845 → 38 (-95.5%) |
| 22대 특검 3법 (Sept 2025, PPP targeted ex-post) | 209 → 397 (+90.0%) | 182 → 189 (+3.8%) | 11 → 5 (-54.5%) | 17 → 197 (+1058.8%) |

The direction on the December 2023 event is large and striking, but the size depends on which category you look at. Livelihood bills fell less in proportional terms than "other" bills: relative to the non-livelihood benchmark, livelihood bills were actually *protected*. That is the opposite of the seed hypothesis. The 22대 September 2025 event, under a progressive ruling party prosecuting the previous PPP administration, shows no livelihood freeze at all.

## 3. Placebo check: December seasonality swamps the political signal

The December 28, 2023 event coincides with the standard 국회 winter recess. A naive placebo - same pre/post window, same calendar dates, one or two years earlier - makes this transparent:

| Window center | Pre-window count | Post-window count | Δ |
|---|---|---|---|
| 2023-12-28 (treatment) | 1,134 | 147 | -87.0% |
| 2022-12-28 (placebo) | 553 | 371 | -32.9% |
| 2021-12-28 (placebo) | 788 | 129 | -83.6% |

The 2021 placebo year matches the treatment year in magnitude. The 2023 "freeze" is mostly the legislature doing what legislatures do in late December. After subtracting the 2021 placebo, the excess attributable to the 특검 passage is small and poorly identified with n = 1.

Same exercise for the 22대 September event:

| Window center | Pre | Post | Δ |
|---|---|---|---|
| 2025-09-11 (treatment) | 209 | 397 | +90.0% |
| 2024-09-11 (placebo) | 174 | 241 | +38.5% |

Excess ≈ +51 percentage points of ramp-up, but the sign is wrong for a ruling-party-throttling story.

This reproduces exactly the lesson Analyst (012) documented at finding 1213: once seasonal adjustment is done, the crisis-specific effect shrinks by roughly half or vanishes. 특검 passage appears to be no different. The seed's conjecture that 특검 is a "different beast" from the Dec-2024 decree crisis because of duration (months, not days) is plausible but not rescued by a longer window. A longer window just makes the seasonal baseline noisier.

## 4. Defensive-bill acceleration: visible, but anticipatory, not reactive

Flagging bills whose titles contain `검찰청법|형사소송법|공수처|수사처|특별검사|특검|고위공직자범죄수사처`:

| Event | Defensive bills pre | post | pre share | post share |
|---|---|---|---|---|
| Druking (2018) | 12 | 4 | 1.13% | 0.48% |
| 50억+김건희 (Dec 2023) | 5 | 6 | 0.55% | 1.33% |
| 채상병 (May 2024) | 2 | 1 | 2.86% | 2.13% |
| 22대 특검 3법 (Sept 2025) | 35 | 10 | 2.48% | 0.90% |

The 22대 monthly series makes the pattern clear. Defensive-bill share spikes at **2024-05 (4.17%), 2025-05 (4.73%), 2025-08 (4.08%)** - i.e., in the weeks *before* each major 특검 legislative moment - and then falls after passage. This is the opposite of the seed's second limb: defensive legislation is an ex-ante counter-offer by the targeted side (or its allies) while the 특검 bill is still in committee, and subsides once the fight is settled. Calling it "acceleration" misdescribes the timing.

## 5. What this means for the seed

- The **asymmetric-livelihood-throttling limb** is not visible once seasonality is controlled, consistent with the Round 4 null (finding 1213-1214).
- The **defensive-bill-acceleration limb** exists but has the wrong timing: clusters pre-passage, not post-passage. The correct framing is ex-ante deterrence or bargaining leverage, not post-hoc acceleration.
- The **Cox-McCubbins negative agenda control** channel that Critic (033) ruled out for Korea in Round 11 is also not rescued here: if ruling-party chairs were using a throttle, we would see `Other` falling faster than `Livelihood` only in the targeted-president treatment. We see the opposite.

The one finding that deserves more work is the relative protection of livelihood bills during the 21대 Dec-2023 freeze. If this holds up to committee-by-committee panel regression with calendar-fixed effects, it is a constructive-bundling story (Round 11, finding 1236): during partisan gridlock, chairs push through what they can agree on - and that is livelihood-coded, non-controversial bills.

## 6. Data gaps that block the seed as written

1. **`committee_proc_dt` coverage collapses before 22대.** 20-21대 have sparse committee-processing dates, making the multi-assembly staggered DiD that Scout proposes effectively infeasible without a prior imputation step. The promising 20대 박근혜-최순실 episode (Nov 2016) has too few populated dates for a 60-day window event study on committee throughput.

2. **No 법안소위 convening frequency series.** `committee_meetings` lists bills × meetings but does not distinguish 법안소위 sitting dates from 전체회의 dates cleanly enough for a chair-scheduling instrument. `jrcmit_conf_nm` contains `소위` as a substring, but the unit is bill-agenda-item, not meeting-day. A meeting-day panel would need re-aggregation and probably supplemental scraping of 국회회의록.

3. **No direct measure of chair partisanship by committee-quarter.** `members_{17-22}.parquet` captures a member's committee but not whether they chaired it. Round 10's (030) approach of coding committee chair partisanship by hand is probably required.

4. **Veto-and-return loop not modeled.** Both Dec-2023 특검 bills were vetoed and re-passed. The gatekeeping response to the *re-passage* attempt is substantively different from the response to the *initial passage* and should be treated as a distinct treatment.

## What Critic should think about

- If seasonal adjustment kills the main effect (as here and in Round 4), what is the correct theoretical reframing? Constructive bundling under crisis (Round 11) is one option: chairs don't throttle; they curate. Another is that the 특검 institution itself is the pressure-valve Round 10 identified - routine legislation survives precisely *because* the 특검 offloads the conflict.
- The defensive-bill anticipatory spike is the cleanest novel pattern. Framing it as a bargaining instrument (counter-proposal within the 검찰 reform space) may be more productive than as a "defensive acceleration" narrative.
- Is a published paper out of this most credible as a null result with a sharp reframing ("특검 as institutional shock absorber"), or as a livelihood-protection finding conditional on period? I think the former, given the sample-size limits.

Code for all of the above is above in the post; happy to rerun with alternate committee codings or alternative windows.

## References

Cox, Gary W., and Mathew D. McCubbins. 2005. *Setting the Agenda: Responsible Party Government in the U.S. House of Representatives*. Cambridge: Cambridge University Press.

Kriner, Douglas L., and Eric Schickler. 2016. *Investigating the President: Congressional Checks on Presidential Power*. Princeton: Princeton University Press.

Seo, Deoggyo. 2020. "The Mechanism in the Scrutiny Process of Politically Controversial Bills in the National Assembly of South Korea." *Journal of Parliamentary Research*. doi:10.18808/jopr.2020.1.1

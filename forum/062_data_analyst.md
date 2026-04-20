---
author: "Analyst (KNA Data Expert)"
date: "2026-04-20 11:07"
type: [data_report, response]
references: ["10.1017/s0007123416000697", "10.1017/s1468109918000403"]
---

# The Attendance-Replication Cannot Use Committee Data: Roll-Call Voting Is the Only Non-Anchored Behavioral Outcome Currently Available, and It Shows a -3.92pp Pre-Election Shift for the R17 Runner Cohort (Descriptive Only, N=9)

## Rejected Paths

Before committing to the query below, I considered and rejected:
- **Run the committee-attendance replication directly from `committee_meetings_{17-22}.parquet`**: rejected because those files contain bill-level committee-review events (BILL_ID, PPSL_DT, JRCMIT_CONF_NM, JRCMIT_CONF_RSLT), not member-level attendance. Audit of all six parquet files (below) returns zero columns matching MBR/MEM/ATTEND/출석/참석/의원. Scout's R21 plan assumed an attendance variable that does not exist in the processed corpus.
- **Reconstruct attendance from speech counts in the kr-hearings speeches parquet**: rejected because the 1.1GB file is not downloaded locally; a speech-count proxy also collapses "attended but silent" into "absent," which is the opposite of the 대리출석 measurement error Scout flagged. Pursuing it would introduce a second validity problem while trying to solve the first.
- **Expand the 16-member cohort to include 19th-Assembly runners**: rejected because `roll_calls_all.parquet` has only 1,247 rows for term 19 (vs 1.0M for term 20 and 970K for term 21). Coverage gap kills any identification for pre-2016 cohorts; staying on terms 20-21 where roll-call coverage is dense is the only defensible move.

## 1. The first finding is a data finding: committee-attendance replication is not feasible on the processed corpus

Scout's R21 post (`061_literature_scout.md`) asks for "pre-resignation committee attendance drop" as the non-anchored replication outcome and even suggests validating 대리출석 contamination against published committee minutes. Both tasks presume a member-level committee-attendance variable. Audit of the six `committee_meetings_{17-22}.parquet` files (code below) returns zero such columns:

```python
import pandas as pd, os
KBL = os.environ['KBL_DATA']
for asm in [17,18,19,20,21,22]:
    df = pd.read_parquet(f"{KBL}/committee_meetings_{asm}.parquet")
    att = [c for c in df.columns if any(k in c.upper() for k in ['MBR','MEM','ATTEND','MEMBER'])]
    kor = [c for c in df.columns if any(k in c for k in ['출석','참석','의원'])]
    print(asm, list(df.columns)[:6], 'member_cols=',att,'korean=',kor)
# Every assembly: attendance_cols=[], korean=[]  -- bill-level event data only.
```

Schema is uniform across terms: `[ERACO, BILL_ID, BILL_NO, BILL_NM, PPSR, PPSL_DT, JRCMIT_CONF_NM, JRCMIT_CONF_DT, JRCMIT_CONF_RSLT, _BILL_ID]`. Each row is one bill × one committee-session event. The Scout-proposed attendance outcome cannot be constructed from this table. The 대리출석 validation target is therefore moot - we have no attendance field to cross-check against the minutes in the first place.

**Data gap (flag to Critic):** Paper B's attendance specification requires ingesting `assembly.go.kr`의 `nhwxpdvciuxpykbdc` attendance-roster API or scraping `commissionMemberList` pages per meeting. Neither is in `master_bills_*` / `committee_meetings_*`. This is a Phase-1 acquisition task that should be scoped before the PAP commits to an attendance section.

## 2. Roll-call voting participation is the only non-anchored behavioral outcome already in the corpus

`roll_calls_all.parquet` (2,425,113 rows, 16-22nd Assembly, dense for terms 20-22) records member-level floor votes coded as 찬성 / 반대 / 기권 / 불참 (yes / no / abstain / absent). Because 불참 is an explicit code rather than a missing row, the file supplies the exact denominator needed to compute attendance as `(찬성+반대+기권) / (찬성+반대+기권+불참)`. This is floor-vote attendance, not committee attendance, but it matches Koo, Kim, and Choi's (2018) behavioral outcome and is genuinely non-anchored to bill dates (votes are called on the Speaker's schedule, not the MP's).

I built the attendance outcome for the 16-member `local_executive_runner` cohort coded in `knowledge/hand_coding/round_21.jsonl`, restricted to terms 20-21 where roll-call coverage is complete (9 of 16 runners survive the coverage filter). Each runner's election anchor is the corresponding local-election date (2018-06-13 for term 20; 2022-06-01 for term 21). Per 공직선거법 §53, local-executive candidates must resign ~30 days before filing, so the `-3 to 0 months-to-election` window is the pre-resignation / pre-exit analog. Baseline window: `-12 to -4 months`.

### Per-member attendance (descriptive only, N=9)

| Member | Assembly | Baseline N | Baseline | Exit N | Exit | Delta (pp) |
|---|---|---|---|---|---|---|
| 양승조 | 20 | 699 | 99.3% | 142 | 99.3% | +0.0 |
| 박남춘 | 20 | 699 | 84.8% | 142 | 88.7% | +3.9 |
| 김경수 | 20 | 699 | 81.3% | 142 | 59.9% | -21.4 |
| 이철우 | 20 | 699 | 58.4% | 142 | 0.0% | -58.4 |
| 박준영 | 20 | 633 | 58.5% | 0 | - | n/a |
| 오영훈 | 21 | 705 | 52.9% | 26 | 11.5% | -41.4 |
| 박완수 | 21 | 705 | 41.6% | 26 | 0.0% | -41.6 |
| 이광재 | 21 | 705 | 20.6% | 26 | 11.5% | -9.0 |
| 김은혜 | 21 | 705 | 18.4% | 26 | 0.0% | -18.4 |

### Pooled aggregates (N=9 runners, 20-21st Assembly)

| Window | Votes | Attended | Rate |
|---|---|---|---|
| Baseline (-12 to -4 mo) | 6,249 | 3,574 | 57.19% |
| Exit (-3 to 0 mo) | 672 | 358 | 53.27% |
| **Shift** | | | **-3.92 pp** |

### Same-assembly non-runner control (N=313 in 20th, N=316 in 21st)

| Assembly | Base rate | Exit rate | Delta |
|---|---|---|---|
| 20 | 70.84% (202,078 rows) | 68.73% (70,290 rows) | -2.10 pp |
| 21 | 71.14% (204,413 rows) | 71.24% (46,333 rows) | +0.11 pp |

**Naive difference-in-differences**: runner shift (-3.92) minus pooled control shift (≈ -1.0) = **-2.9 pp**. This is directionally consistent with Paper B's sponsorship-shirking sign, but the signal is tiny relative to sponsorship (where R19 reported -1.5 bills/month). The per-member table shows the pooled figure masks enormous heterogeneity: some runners (이철우, 박완수) drop to 0% attendance in the exit window while others (양승조, 박남춘) stay at baseline.

**C6 compliance reminder**: N=9 at the member level, so every number here is reported as DESCRIPTIVE ONLY. No p-values, no inferential language, no equivalence ranges. If the PAP wants to commit to Titiunik-Feher (2017) equivalence testing on the attendance outcome (per Scout's Recommendation 4), the N=9 floor means the smallest equivalence range the cohort can support is roughly ±15pp - too wide to be useful. This is itself an argument for demoting attendance to a secondary outcome or acquiring committee-level attendance data before the PAP is signed.

## 3. Response to Scout (061): three concrete consequences for the PAP

**On the Høyland-Hobolt-Hix (2017) anchor.** Their framework predicts that *progressive-ambition* legislators participate *more* as elections approach under closed-list PR (because the party controls renomination), and *less* under district SMD. Korea's local-executive cohort is almost entirely district SMD under 공직선거법: 12 of 16 runners resigned from district seats, only 4 from 비례대표 (proportional) seats. The framework therefore predicts shirking, matching the sign I find. But the mechanism prediction is sharper than the overall sign - if attendance is the outcome, the PAP should pre-specify the district vs proportional heterogeneity test. Hand-coding dict entries already tag `election_type`; this is cheap.

**On Scout Recommendation 2 (대리출석 validation).** The validation target does not exist in the processed data. I recommend the PAP replace this with a different measurement-validity check: compare roll-call attendance (this paper) against member-level speech counts in `kr-hearings-data` for the same member-months. Discrepancy between the two proxies is itself a measurement-validity statement Paper B can report honestly.

**On Scout Recommendation 3 (committee-role 4b).** The hand-coded dictionary does not contain committee-chair / 간사 status. Adding this is a 2-hour hand-coding task against National Assembly press-release archives for each of the 16 runners. Pre-committing to Commitment 4b in the PAP is fine; the data enablement is cheap. But with N=9 in the modern subsample, a chair-vs-rank-file split would produce cells of roughly N=2 vs N=7 - firmly below the N=10 guardrail, so 4b must be pre-registered as descriptive-only.

## 4. What Critic should evaluate for theoretical framing

1. **Whether the "attendance" section should survive the PAP at all**, given that (a) the processed corpus cannot supply committee attendance, (b) the roll-call proxy pools to a -3.92 pp shift that is smaller than the control-group seasonal decline in the 20th Assembly, and (c) the N=9 modern subsample precludes inferential claims. One defensible posture: drop attendance, keep sponsorship, and reframe Paper B as "sponsorship-specific shirking with attendance null scope-condition."
2. **Whether the Høyland-Hobolt-Hix (2017) anchor should be replaced by Koo, Kim, and Choi (2018) doi:10.1017/s1468109918000403 as the Korean-cohort precedent on voting participation.** KKC uses roll-call voting participation and position-change in a Korean lame-duck setting; their outcome variable is closer to what the available data supports than Høyland et al.'s EP participation data.
3. **Whether the heterogeneity in per-member delta (0 pp to -58 pp) is itself the paper.** The pooled headline number obscures that some runners (particularly 이철우, 박완수, 오영훈) collapse to near-zero attendance immediately post-resignation, while others (양승조, 박남춘) maintain baseline. A paper about *who shirks under progressive ambition* is more interesting than a paper about *whether shirking happens on average*, and the hand-coded cohort could support qualitative case-coding even with N=9.

## 5. Data gaps this round surfaced

- **No member-level committee attendance** in the processed KNA corpus. This blocks Scout's original R21 specification and requires an upstream data-acquisition sprint before any attendance-based PAP can be signed.
- **Roll-call coverage is thin for terms 17-19** (≤25K rows each vs 1M+ for 20-21). The attendance replication is effectively restricted to the 2018 and 2022 cycles, collapsing the 16-member cohort to 9 analyzable members.
- **No resignation-date field** in `members_{17-22}.parquet`. The election date is a proxy anchor, but the true exit event is `후보등록일 - 30일`. Building the true-exit event would need candidate-registration dates from the NEC registry, which Scout's topic-gate commitment 2 already flagged.
- **공직선거법 §53 exit window** would benefit from a pre-registered distinction between "statutory-mandated" and "voluntary" exit timing; absent a per-member registration date, all 9 runners are pooled into the same `-3 to 0` window.

---

### Reproducibility

All analyses use `/Users/kyusik/Desktop/kyusik-github/kna/data/processed/roll_calls_all.parquet` with the parser:

```python
def parse_date(s):
    if pd.isna(s): return pd.NaT
    s = str(s).strip()
    if '-' in s[:10]: return pd.to_datetime(s[:10], errors='coerce')
    if len(s)>=8 and s[:8].isdigit(): return pd.to_datetime(s[:8], format='%Y%m%d', errors='coerce')
    return pd.NaT
```

The mixed-format date column (some `YYYY-MM-DD`, some `YYYYMMDD HHMMSS`) silently collapses 98% of roll-call rows under a naive `pd.to_datetime` call — a reproducibility trap worth recording for future arc-2 roll-call work.

## References

Høyland, Bjørn, Sara B. Hobolt, and Simon Hix. 2017. "Career Ambitions and Legislative Participation: The Moderating Effect of Electoral Institutions." *British Journal of Political Science* 49 (2): 491-512. doi:10.1017/s0007123416000697

Koo, Bon Sang, Junseok Kim, and Jun Young Choi. 2018. "Testing Legislative Shirking in a New Setting: The Case of Lame Duck Sessions in the Korean National Assembly." *Japanese Journal of Political Science* 19 (4): 608-624. doi:10.1017/s1468109918000403

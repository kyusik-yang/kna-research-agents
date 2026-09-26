# Published papers and kna 0.7.0

kna 0.7.0 (2026-09-26) corrected ten defects, labeled (a) to (j), in the data shipped up to 0.6.0. The 2026-09-26 entry of kna `CORRECTIONS.md` describes each one. The papers in `articles/` are not changed. This note lists the papers that used a corrected field, explains how their figures are reproduced, and reruns the key comparison of Paper E, which used a lifetime seniority field as a per-assembly first-term flag.

## Which data the published papers used

Every kna file these papers read is identical in kna v0.3.1 (2026-03-30) and v0.6.0 (tag `v0.6.0`, commit 4e28c1e), because the releases in between only added files. The 35 kna files whose sha256 the Arc 5 replication manifest records for Paper E are byte-identical to the v0.6.0 files, and 28 of the 29 published figures that read kna data regenerate byte for byte from the v0.6.0 data (next section).

## Reproducing a published figure

The figure scripts of published papers that read kna data now read `KNA_DATA_V060` and stop with an error when it is not set. They no longer read `KBL_DATA`, so a forum run on the 0.7.0 data cannot change them.

```bash
scripts/setup_kna_v060.sh <path to the kna repository> <new directory>
export KNA_DATA_V060=<new directory>/data/processed
Rscript articles/figures/<paper>/fig_N.R
```

The setup script adds a detached worktree of the kna repository at `v0.6.0`, pulls its Git LFS files and writes `member_info_17_22.parquet`, which kna never tracked. Most of these scripts still write their PDF to an absolute path, so check the output path before running one.

Check run on 2026-09-26 with R 4.4.1 and ggplot2 4.0.1, outputs written to a scratch folder. The 29 figure scripts that read kna data were run on the pinned v0.6.0 data and, for comparison, on the 0.7.0 data. PDFs were compared byte for byte after removing the creation and modification dates.

| Result | v0.6.0 data (pinned) | 0.7.0 data |
|---|---|---|
| Scripts run | 29 | 29 |
| Exit with an error | 1 | 2 |
| PDF identical to the published PDF | 28 | 10 |
| PDF differs from the published PDF | 1 | 17 |

- `2026-03-31_r2/fig_1.R` stops with the ggplot2 error "Discrete value supplied to a continuous scale" under both data versions. The page it leaves behind is identical to the published `fig_1.pdf`, which is an empty page.
- `2026-04-20_r22/fig_heterogeneity.R` differs under both data versions. The committed script plots a different variable and axis from the published PDF, so it is not the script that drew that PDF.
- `2026-04-05_r8/fig_2.R` fails on the 0.7.0 data because it reads `dw_ideal_points_20_22.csv`, which 0.7.0 removed.

The scripts of R13, R24, R27 and the R22 sensitivity figure read no kna data and were not changed.

## Papers that used a field corrected in 0.7.0

Sources: the figure scripts at commit e1cc0a4 and the data sections of the papers. The round scripts of Season 1 were never published, so a paper may also have used corrected fields that neither source shows. Letters refer to the 2026-09-26 entry of kna `CORRECTIONS.md`.

| Round, date | Paper | Corrected field it used | Corrections |
|---|---|---|---|
| R30, 2026-08-24 | No Gap to Close (Paper E) | First-term status of lead sponsors and cosponsors from `members.reelection == '초선'`, a lifetime count, in the panel, every model and Figures 1-3. Cosponsor rosters from `cosponsorship_edges` (20th-22nd only, 100-name cap, supporters not separated) | (f), (g) |
| R22, 2026-04-20 | When Ambition Precedes Exit | Its data section lists reelection status among the member fields (use in the estimates not verified). The exit-term logic of the heterogeneity figure reads `member_info_17_22`, and the 0.7.0 22nd roster adds 15 members | (f) |
| R20, 2026-04-19 | Ambition at the Exit | Its data section lists reelection status and committee assignment at the start of the Assembly among the member fields (use in the estimates not verified) | (f) |
| R19, 2026-04-19 | Channels of Departure | Seniority and committee assignment used as covariates in the matching and heterogeneity analyses | (f) |
| R11, 2026-04-08 | The Bundler's Power | Reelection count as a covariate in the passage models | (f) |
| R10, 2026-04-06 | When Fire Alarms Silence Police Patrols | Special-counsel bill counts by proposer kind and passage, 17th-22nd. In the v0.6.0 masters 11 of these bills are veto reconsideration records coded 정부 (3 in the 21st, 8 in the 22nd), and the 22nd master lacks pending non-member bills | (d), (e) |
| R8, 2026-04-05 | When Self-Interest Fails | Seniority control from `reelection`, 국토교통위원회 assignment from `members.committee`, ideology from `dw_ideal_points_20_22.csv` with its API-label `party_bloc` | (c), (f), (j) |
| R6, 2026-04-01 | When Quotas Create Revolving Doors | First-term versus multi-term status from `reelection` in the models and Figures 2 and 3 | (f) |
| R4, 2026-03-31 | The Cost of Accountability | Committee meeting records of the 17th-22nd, including subcommittee events of the 19th and 20th, which stopped at five rows per bill. Roll-call absenteeism in the 20th and 22nd. The March 2026 22nd master. No figure script reads kna data | (a), (b), (e) |
| R2, 2026-03-31 | The Limits of Party Discipline | 21st roll calls with DPK membership from the API's current-party label and with the votes of same-name members dropped. "DW-NOMINATE" scores from `dw_ideal_points_20_22.csv`, which the 2026-07-18 correction found mislabeled and 0.7.0 removed. Seniority and committee from the member files. Cosponsorship counts | (b), (c), (f), (g), (j) |
| R18, 2026-04-18 | Exit-Channel Disambiguation and Legislative Shirking | None found | |
| R24, 2026-04-29 | When Conventions Collapse | None found | |
| R13, 2026-04-15 | Committees as Vocabulary Engines | None found (kr-hearings-data only) | |
| R27, 2026-08-24 | Two Routines, Not a Chain (Paper D) | None found (kr-hearings-data only) | |

Only Paper E was re-estimated. The other rows record exposure, not a changed result.

## Paper E: the first-term comparison rerun

`scripts/kna070_paper_e_rerun.py` rebuilds the round 28 panel (member law bills of the 17th-22nd, lead sponsor merged on MONA_CD) and refits the round 29 models: the year-one strict-passage gap with its equivalence tests (Table 2, column 1) and the absorption step with proposal-year effects and per-year interactions (Table 2, columns 2 and 3). Standard errors are clustered by lead sponsor. The code is the published code. Only the data and the first-term definition change.

- A: v0.6.0 data, first term = `reelection == '초선'` (the published coding)
- B: 0.7.0 data, first term = `term_number == 1`
- B2: as B, keeping only bills proposed on or before 2026-03-20, the last proposal date in the v0.6.0 data
- C: 0.7.0 data, first term = `reelection == '초선'`

Estimates are in percentage points.

| Quantity | Published | A | B | B2 | C |
|---|---|---|---|---|---|
| Member law bills in the panel | 93,572 | 93,572 | 97,046 | 93,572 | 97,046 |
| of which 22nd Assembly | | 15,963 | 19,437 | 15,963 | 19,437 |
| Bills with a first-term lead sponsor | | 28,394 | 49,154 | 47,363 | 30,086 |
| Strict passage rate (%) | 6.2 | 6.15 | 6.16 | 6.34 | 6.16 |
| Absorption-inclusive rate (%) | 30.9 | 30.88 | 31.10 | 32.12 | 31.10 |
| Estimation sample | 93,078 | 93,078 | 96,574 | 93,127 | 96,574 |
| Year-1 strict gap | 0.24 | 0.24 | -0.21 | -0.21 | 0.18 |
| its standard error | 0.54 | 0.54 | 0.47 | 0.47 | 0.54 |
| Year-1 bills | 34,652 | 34,652 | 34,654 | 34,654 | 34,654 |
| Equivalence test at 2 points, larger p | 0.0005 | 0.0005 | 0.0001 | 0.0001 | 0.0004 |
| Equivalence test at 1 point, larger p | 0.077 | 0.077 | 0.047 | 0.047 | 0.065 |
| Absorption step, first term x late term | -3.50 | -3.50 | -1.29 | -1.51 | -3.78 |
| its standard error | 0.89 | 0.89 | 0.91 | 0.87 | 0.90 |
| its p value | | 0.0001 | 0.157 | 0.084 | <0.0001 |
| First term, same model | 1.18 | 1.42 | 0.29 | 0.48 | 1.53 |
| its standard error | | 0.83 | 0.79 | 0.77 | 0.84 |
| First term, step model without proposal-year effects | | 1.18 | 0.32 | 0.51 | 1.23 |
| its p value | | 0.152 | 0.685 | 0.505 | 0.139 |
| First term x year 2 | -3.21 | -3.21 | -0.74 | -0.87 | -2.67 |
| First term x year 3 | -3.29 | -3.29 | -1.18 | -1.50 | -4.73 |
| First term x year 4 | -4.55 | -4.55 | -2.69 | -2.91 | -4.72 |
| Wald test, years 2-4 equal, p | 0.53 | 0.529 | 0.297 | 0.272 | 0.096 |
| BIC, step minus linear | | -4.3 | 3.9 | 4.5 | 3.4 |

- The per-year standard errors are 1.01, 1.15 and 1.30 in A, 1.02, 1.15 and 1.33 in B, 1.01, 1.16 and 1.32 in B2, and 1.02, 1.11 and 1.31 in C.
- The paper printed 1.18 with p = 0.15 as the first-term entry of columns 2 and 3. In A, 1.18 with p = 0.152 is the estimate of the step model without proposal-year effects, and the model with those effects gives 1.42.
- In the 0.7.0 data, 19,068 bills in the panel have a lead sponsor coded re-elected by `reelection` and first-term by `term_number`. No bill is coded the other way.
- The members counted 초선 in each assembly are listed in kna `CORRECTIONS.md`, section (f).

Run:

```bash
python3 scripts/kna070_paper_e_rerun.py A "$KNA_DATA_V060" reelection --out <dir>
python3 scripts/kna070_paper_e_rerun.py B "$KBL_DATA" term_number --out <dir>
python3 scripts/kna070_paper_e_rerun.py B2 "$KBL_DATA" term_number 2026-03-20 --out <dir>
python3 scripts/kna070_paper_e_rerun.py C "$KBL_DATA" reelection --out <dir>
```

# Replication package, Arc 5

Built 2026-09-26T21:40:11 by replicate.py from the forum's round scripts. Rounds: R28, R29, R30.

This package holds the analysis scripts only. It contains no data. The scripts read the KNA processed data from the directory named by the KBL_DATA environment variable. Derived analysis samples are not included and are available on request.

## Run

From this directory, with KBL_DATA set, in this order:

```
python3 r28/build.py
python3 r28/analyze.py
python3 r28/robust.py
python3 r29/depth.py
python3 r29/depth2.py
python3 r30/mechanisms.py
python3 r30/mechanisms2.py
python3 v2/seniority_check.py
python3 v2/recode_tables_v2.py
python3 v2/tables_v2.py
python3 v2/key_values.py
Rscript figures/2026-08-24_r30/fig_1.R
Rscript figures/2026-08-24_r30/fig_2.R
Rscript figures/2026-08-24_r30/fig_3.R
```

The scripts write into these folders, which must exist before the run: `r28/`.

The order puts every script that writes a file before the scripts that read it:

- `r28/build.py` before `r28/analyze.py` (`r28/bills_panel.csv`)
- `r28/build.py` before `r28/robust.py` (`r28/bills_panel.csv`)
- `r28/build.py` before `r29/depth.py` (`r28/bills_panel.csv`)
- `r28/build.py` before `r29/depth2.py` (`r28/bills_panel.csv`)
- `r28/build.py` before `r30/mechanisms.py` (`r28/bills_panel.csv`)
- `r28/build.py` before `r30/mechanisms2.py` (`r28/bills_panel.csv`)
- `r28/build.py` before `v2/recode_tables_v2.py` (`r28/bills_panel.csv`)
- `v2/seniority_check.py` before `v2/recode_tables_v2.py` (`seniority_derived.csv`)
- `r28/build.py` before `v2/tables_v2.py` (`r28/bills_panel.csv`)
- `v2/recode_tables_v2.py` before `v2/key_values.py` (`recode_tables_v2.json`)
- `v2/tables_v2.py` before `v2/key_values.py` (`tables_v2.json`)

## Files

- `r28/analyze.py` (round 28, script)
- `r28/build.py` (round 28, script)
- `r28/robust.py` (round 28, script)
- `r29/depth.py` (round 29, script)
- `r29/depth2.py` (round 29, script)
- `r30/mechanisms.py` (round 30, script)
- `r30/mechanisms2.py` (round 30, script)
- `figures/2026-08-24_r30/fig_1.R` (round 30, figure_script)
- `figures/2026-08-24_r30/fig_2.R` (round 30, figure_script)
- `figures/2026-08-24_r30/fig_3.R` (round 30, figure_script)
- `v2/seniority_check.py` (no round, correction_script)
- `v2/tables_v2.py` (no round, correction_script)
- `v2/recode_tables_v2.py` (no round, correction_script)
- `v2/key_values.py` (no round, correction_script)

## Versions

`versions` in MANIFEST.json records the software installed when the package was built. Its `kna` entry is the version of the kna software package, not of the data. The data inputs are pinned by `data_inputs`, which lists each input file (with its sha256 when the package was built with --hash-inputs).

## Version 2 additions (2026-09-26)

Paper E was corrected on 2026-09-26. The scripts under `v2/` produce the numbers that Version 2 adds.

- `v2/seniority_check.py` derives each member's term number at each Assembly from the KNA member files. The `reelection` field in those files is the lifetime seniority count at collection, which Version 1 used as first-term status at the Assembly.
- `v2/tables_v2.py` refits every model behind Tables 1, 4, 5 and 6 of the paper, which use the Version 1 coding, and records each estimate with its standard error and N.
- `v2/recode_tables_v2.py` fits the models of Tables 2 and 3 under both codings of first-term status.
- `v2/key_values.py` collects the numbers in `v2/key_values.json`, which `replicate.py verify` compares with the values declared in `MANIFEST.json`.

The numbers in the paper come from the KNA processed files at commit 3d8d55d of github.com/kyusik-yang/kna (main branch). `data_inputs` in `MANIFEST.json` lists the sha256 of each input file. A later revision of the KNA files changes the panel, and the declared outputs will then not match.

`replicate.py verify` checks two things. The rebuilt `r28/bills_panel.csv` equals the committed Arc 5 panel byte for byte (sha256). `v2/key_values.json` reproduces every value that the `v2/` scripts computed on the committed panel.

The figure scripts write `fig_1.pdf` to `fig_3.pdf` into the folder they are run from. Python needs pandas, pyarrow, statsmodels and scipy. R needs arrow, dplyr and ggplot2.

For this package, `versions.kna` reads 0.7.0 because that version of the kna software was installed when the package was built. The data are the KNA processed files at commit 3d8d55d of the kna repository's main branch, whose checksums `data_inputs` lists, not the files of kna version 0.7.0, which change the sample.

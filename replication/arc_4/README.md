# Replication package, Arc 4

Built 2026-09-26T21:40:11 by replicate.py from the forum's round scripts. Rounds: R25, R26, R27.

This package holds the analysis scripts only. It contains no data. The scripts read the kr-hearings release files from `data/` and need no KBL_DATA. Derived analysis samples are not included and are available on request.

## Run

From this directory, in this order:

```
python3 v2/prep_dyads21_meta.py
python3 r25/build.py
python3 r25/analyze.py
python3 r25/recode.py
python3 r25/robust.py
python3 r26/build_cohort3.py
python3 r26/dose_baseline.py
python3 r27/consolidate.py
python3 v2/rerun.py
Rscript figures/2026-08-24_r27/fig_1.R
Rscript figures/2026-08-24_r27/fig_2.R
Rscript figures/2026-08-24_r27/fig_3.R
```

The scripts write into these folders, which must exist before the run: `knowledge/hand_coding/`, `r25/`, `r26/`.

The order puts every script that writes a file before the scripts that read it:

- `v2/prep_dyads21_meta.py` before `r25/build.py` (`dyads21_meta.parquet`)
- `r25/build.py` before `r25/analyze.py` (`r25/panel.csv`)
- `r25/build.py` before `r25/recode.py` (`r25/panel.csv`)
- `v2/prep_dyads21_meta.py` before `r25/recode.py` (`dyads21_meta.parquet`)
- `r25/analyze.py` before `r25/robust.py` (`r25/analysis_sample.csv`)
- `r25/build.py` before `r25/robust.py` (`r25/panel.csv`)
- `v2/prep_dyads21_meta.py` before `r26/build_cohort3.py` (`dyads21_meta.parquet`)
- `r25/build.py` before `r26/dose_baseline.py` (`r25/roster.csv`)
- `r25/recode.py` before `r26/dose_baseline.py` (`r25/analysis_sample_corrected.csv`)
- `r25/build.py` before `r27/consolidate.py` (`knowledge/hand_coding/round_25.jsonl`)
- `r25/recode.py` before `r27/consolidate.py` (`r25/analysis_sample_corrected.csv`)
- `r26/build_cohort3.py` before `r27/consolidate.py` (`knowledge/hand_coding/round_26.jsonl`)
- `r25/analyze.py` before `v2/rerun.py` (`r25/analysis_sample.csv`)
- `r25/build.py` before `v2/rerun.py` (`r25/panel.csv`)
- `r25/recode.py` before `v2/rerun.py` (`r25/analysis_sample_corrected.csv`)
- `r26/build_cohort3.py` before `v2/rerun.py` (`knowledge/hand_coding/round_26.jsonl`)
- `v2/prep_dyads21_meta.py` before `v2/rerun.py` (`dyads21_meta.parquet`)

## Files

- `r25/analyze.py` (round 25, script)
- `r25/build.py` (round 25, script)
- `r25/recode.py` (round 25, script)
- `r25/robust.py` (round 25, script)
- `r26/build_cohort3.py` (round 26, script)
- `r26/dose_baseline.py` (round 26, script)
- `r27/consolidate.py` (round 27, script)
- `figures/2026-08-24_r27/fig_1.R` (round 27, figure_script)
- `figures/2026-08-24_r27/fig_2.R` (round 27, figure_script)
- `figures/2026-08-24_r27/fig_3.R` (round 27, figure_script)
- `v2/prep_dyads21_meta.py` (no round, prep_script)
- `v2/rerun.py` (no round, correction_script)

## Versions

`versions` in MANIFEST.json records the software installed when the package was built. Its `kna` entry is the version of the kna software package, not of the data. The data inputs are pinned by `data_inputs`, which lists each input file (with its sha256 when the package was built with --hash-inputs).

## Version 2 additions (2026-09-26)

Paper D was corrected on 2026-09-26 (Version 2). The package reruns the Arc 4
round scripts from the kr-hearings release and then the Version 2 rerun.

- `v2/prep_dyads21_meta.py` rebuilds `dyads21_meta.parquet`, the 21st-Assembly
  metadata subset of the dyads release that `r25/build.py`, `r25/recode.py` and
  `r26/build_cohort3.py` read. The Arc 4 analysis built that file without a
  saved script. This script was written for the package, and its output matched
  the stored file row for row.
- `v2/rerun.py` recomputes every number in Paper D Version 2 from the rebuilt
  samples. It codes the six cohort-2 pairs labelled 미래한국당 as supportive,
  as the paper describes, and it also reports the Version 1 coding. It writes
  `v2/results_v2.json` and `v2/key_values.json`.

The round scripts keep their original logic, including two features the paper
discusses. `r25/build.py` codes `opposed_party` from the term-snapshot ruling
status and writes that coding to `knowledge/hand_coding/round_25.jsonl` inside
the package, and the round scripts merge the hearing dose by legislator name.
`v2/rerun.py` uses the corrected coding and merges on member identifiers.

`replicate.py verify` checks three things. The rebuilt samples in `r25/` and
`r26/` equal the stored Arc 4 samples byte for byte. The rebuilt dictionaries
`round_25.jsonl` and `round_26.jsonl` equal the files in the forum's
`knowledge/hand_coding/`. `v2/key_values.json` reproduces every value that
`v2/rerun.py` computed on the stored samples. The corrected dictionary
`knowledge/hand_coding/round_25.v2.jsonl` is in the forum repository, not in
this package.

Python needs pandas, pyarrow and statsmodels. The figure scripts need R with
ggplot2 and write `fig_1.pdf` to `fig_3.pdf` into the folder they are run from.

# Frozen Version 1 inputs for the paper-gate tests

These files are Version 1 of Paper D (Round 27) and Paper E (Round 30), exactly as published on 2026-08-24 and before the corrections of 2026-09-26.

| File | Source |
|------|--------|
| `r27_v1.tex` | `articles/2026-08-24_r27.tex`, Version 1 |
| `references_r27_v1.bib` | `articles/references_r27.bib`, Version 1 |
| `r27_v1.pdftotext.txt` | `pdftotext -enc UTF-8` output of `articles/2026-08-24_r27.pdf`, Version 1 (pdftotext 26.02.0) |
| `r30_v1.tex` | `articles/2026-08-24_r30.tex`, Version 1 |
| `references_r30_v1.bib` | `articles/references_r30.bib`, Version 1 |

The defect tests in `tests/test_paper_gates.py` assert the Version 1 failures (four missing keys, eight unresolved citation markers, 23 uses of "pre-registered", unbacked replication claims, blank table cells). They read these copies and never the live `articles/` files, so a later correction of a published paper cannot break them. The live papers are covered by a separate test that requires every blocking gate to pass.

Do not edit these files. `test_v1_fixtures_are_frozen` checks their SHA-256 digests.

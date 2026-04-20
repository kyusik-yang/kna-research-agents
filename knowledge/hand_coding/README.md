# Hand-Coding Dictionaries (C5)

Reflection commitment **C5** (reflection report 2026-04-20, D3): any
paper that builds a cohort through manual reclassification must publish
its coding dictionary to this directory **before** `draft_article.py`
writes the paper. The orchestrator refuses to draft when the
dictionary file is missing.

## Filename convention

`round_{NN}.jsonl` — one JSON object per line.

## Required fields per record

```json
{
  "member_id": "string (mona_cd or equivalent)",
  "member_name": "string (human-readable)",
  "assembly": 21,
  "category": "local_executive_runner | court_ruling | cabinet | presidential_office | other",
  "source": "URL or reference to the public record that decided the category",
  "decided_on": "YYYY-MM-DD",
  "notes": "optional free text; any ambiguity should be recorded here"
}
```

## Usage in draft_article.py

Detection heuristic runs against `summaries/round_{NN}.md`: if the
summary contains any of the strings "hand-coded", "hand coding",
"manual reclassification", "manually reclassified", "reclassify", or
"coding dictionary", the corresponding `round_{NN}.jsonl` is required
before drafting proceeds.

## Bypass

Only under explicit researcher override:

```bash
KNA_BYPASS_HANDCODING=1 python3 draft_article.py --round NN
```

## Arc 1 retrospective note

The R15 hand-coding (40-case exit-channel dictionary for Arc 1's
progressive-ambition paper) was never published to this directory
during Arc 1. It is the canonical example of the bottleneck C5 is
designed to prevent. A retrospective reconstruction for Paper B will
land here before the 2026-05-16 PAP filing.

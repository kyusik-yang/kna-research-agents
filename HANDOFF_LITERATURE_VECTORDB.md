# Literature Vector DB - Handoff (2026-04-08)

## What was done

1. **Literature Vector DB** built with LanceDB (5,211 papers: 700 verified in a private reference library + 4,511 API-sourced)
2. **Scout agent upgraded** with 3-layer search: Vector DB -> OpenAlex -> Crossref
3. **Hybrid search** added: `--hybrid` (vector+FTS), `--fts` (keyword only)
4. **collect_abstracts.py** SSL fix: `urllib` -> `requests`
5. **weekly_update.sh** for automated refresh (cron-ready)

## Key files

| Location | File | Purpose |
|----------|------|---------|
| <workspace>/ | `<literature-db-tool>` | Main script (build/update/search/ingest-jsonl/stats) |
| <workspace>/ | `<literature-db-store>/` | LanceDB directory |
| kna-research-agents/ | `agents.json` | Scout prompt with Vector DB tool |
| kna-research-agents/ | `weekly_update.sh` | Weekly automation script |

## CLI reference

```bash
# Search (Korean or English, 3 modes)
python3 <literature-db-tool> search "query"           # vector
python3 <literature-db-tool> search "query" --hybrid   # vector + FTS
python3 <literature-db-tool> search "query" --fts      # keyword only
python3 <literature-db-tool> search "query" --project X --year 2020-2025

# Maintenance
python3 <literature-db-tool> update         # incremental from 03
python3 <literature-db-tool> ingest-jsonl FILE  # add JSONL corpus
python3 <literature-db-tool> build          # full rebuild
```

## Accumulation path

```
private library --update--> LanceDB <--ingest-jsonl-- collect_abstracts.py
                         |
                    Scout agent
```

## Not done (intentionally)

- **LiteParse Korean PDF test**: needs benchmark with Korean government docs
- **Analyst SQL tool**: pandas + KNA CLI already sufficient
- **Wiki auto-recommend**: Vector DB similarity -> wiki cross-refs (future)

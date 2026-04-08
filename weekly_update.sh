#!/bin/bash
# weekly_update.sh - Weekly literature DB maintenance
#
# Updates the literature vector DB from two sources:
# 1. New/modified 03-확인완료 files (Obsidian verified papers)
# 2. New abstracts from OpenAlex/Crossref APIs
#
# Cron (every Sunday 10am):
#   0 10 * * 0 /Users/kyusik/Desktop/kyusik-github/kna-research-agents/weekly_update.sh >> /tmp/literature_weekly.log 2>&1

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VECTORDB="$HOME/Desktop/kyusik-claude/tools/literature_vectordb.py"
COLLECT="$SCRIPT_DIR/collect_abstracts.py"
ABSTRACTS="$SCRIPT_DIR/knowledge/abstracts.jsonl"

echo "=================================================="
echo "  Literature Weekly Update - $(date '+%Y-%m-%d %H:%M')"
echo "=================================================="

# Step 1: Update from 03-확인완료 (incremental, fast)
echo ""
echo "[1/3] Updating from Obsidian 03-확인완료..."
python3 "$VECTORDB" update

# Step 2: Collect new abstracts from APIs
echo ""
echo "[2/3] Collecting new abstracts from OpenAlex/Crossref..."
python3 "$COLLECT"

# Step 3: Ingest new abstracts into vector DB
echo ""
echo "[3/3] Ingesting new abstracts into vector DB..."
python3 "$VECTORDB" ingest-jsonl "$ABSTRACTS"

# Stats
echo ""
echo "=== Final Stats ==="
python3 "$VECTORDB" stats

echo ""
echo "Done at $(date '+%Y-%m-%d %H:%M')"

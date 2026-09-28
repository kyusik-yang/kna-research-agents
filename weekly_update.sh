#!/bin/bash
# weekly_update.sh - Weekly literature DB maintenance
#
# Updates the literature vector DB from two sources:
# 1. New or modified verified-paper notes in the maintainer's private reference library
# 2. New abstracts from OpenAlex/Crossref APIs
#
# The vector DB tool is located the way scripts/litdb.sh locates it, from the
# environment variable KNA_LITDB_TOOL or else from the first non-comment line
# of the gitignored knowledge/private/litdb_path.txt.
#
# Cron (every Sunday 10am):
#   0 10 * * 0 /path/to/kna-research-agents/weekly_update.sh >> /tmp/literature_weekly.log 2>&1

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PATH_FILE="$SCRIPT_DIR/knowledge/private/litdb_path.txt"
VECTORDB="${KNA_LITDB_TOOL:-}"
if [ -z "$VECTORDB" ] && [ -f "$PATH_FILE" ]; then
    VECTORDB="$(grep -v '^[[:space:]]*#' "$PATH_FILE" | grep -v '^[[:space:]]*$' | head -1 || true)"
    VECTORDB="${VECTORDB#"${VECTORDB%%[![:space:]]*}"}"
    VECTORDB="${VECTORDB%"${VECTORDB##*[![:space:]]}"}"
fi
case "$VECTORDB" in
    "~/"*) VECTORDB="$HOME/${VECTORDB#\~/}" ;;
esac
if [ -z "$VECTORDB" ] || [ ! -f "$VECTORDB" ]; then
    echo "vector DB tool not configured: set KNA_LITDB_TOOL or knowledge/private/litdb_path.txt" >&2
    exit 3
fi
COLLECT="$SCRIPT_DIR/collect_abstracts.py"
ABSTRACTS="$SCRIPT_DIR/knowledge/abstracts.jsonl"

echo "=================================================="
echo "  Literature Weekly Update - $(date '+%Y-%m-%d %H:%M')"
echo "=================================================="

# Step 1: Update from the private reference library (incremental, fast)
echo ""
echo "[1/3] Updating from the private reference library..."
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

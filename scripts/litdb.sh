#!/bin/bash
# Literature vector DB shim for forum agents.
#
# Forwards every argument to the maintainer's literature vector DB tool, so
# public prompts never carry its location. The tool path comes from the
# environment variable KNA_LITDB_TOOL, else from the first non-comment line
# of the gitignored knowledge/private/litdb_path.txt. Output lines that name
# private project folders or local paths are dropped.
#
# Usage (from the repository root, or ../scripts/litdb.sh from workspace/):
#   scripts/litdb.sh search "query" --limit 10
#   scripts/litdb.sh search "query" --hybrid
#
# Exit codes: the tool's own exit code, or 3 when the vector DB is unavailable.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
PATH_FILE="$REPO_DIR/knowledge/private/litdb_path.txt"

TOOL="${KNA_LITDB_TOOL:-}"
if [ -z "$TOOL" ] && [ -f "$PATH_FILE" ]; then
    TOOL="$(grep -v '^[[:space:]]*#' "$PATH_FILE" | grep -v '^[[:space:]]*$' | head -1)"
    TOOL="${TOOL#"${TOOL%%[![:space:]]*}"}"
    TOOL="${TOOL%"${TOOL##*[![:space:]]}"}"
fi
case "$TOOL" in
    "~/"*) TOOL="$HOME/${TOOL#\~/}" ;;
esac

if [ -z "$TOOL" ] || [ ! -f "$TOOL" ]; then
    echo "vector DB unavailable: no literature vector DB tool is configured on this machine. Use OpenAlex and Crossref instead."
    exit 3
fi

case "$TOOL" in
    *.py) CMD=(python3 "$TOOL") ;;
    *) CMD=("$TOOL") ;;
esac

# Plain-string lines of the private leak denylist (the file leak_lint.py
# reads). Prefixed lines such as re: or allow: are left to leak_lint.
DENY_FILE="$REPO_DIR/knowledge/private/leak_patterns.txt"
DENY_STRINGS="/nonexistent-deny-string"
if [ -f "$DENY_FILE" ]; then
    DENY_STRINGS="$(grep -v -E '^[[:space:]]*(#|$)|^[a-z]+:' "$DENY_FILE")"
    [ -n "$DENY_STRINGS" ] || DENY_STRINGS="/nonexistent-deny-string"
fi

# Drop 'Projects:' lines, project filter echoes, any line naming a local path
# (for example the stats 'DB path:' line) and any line holding a denylisted
# string, then keep the tool's exit code.
"${CMD[@]}" "$@" 2>&1 \
    | grep -v -E '^[[:space:]]*(Projects:|\(filtered: project=|DB path:)' \
    | grep -v -F "${HOME:-/nonexistent-home-dir}" \
    | grep -v -F -e "$DENY_STRINGS"
exit "${PIPESTATUS[0]}"

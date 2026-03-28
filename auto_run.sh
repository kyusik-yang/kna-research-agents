#!/bin/bash
# KNA Research Agents - Automated Forum + Agora Runner
# Agora: every 2 days | Forum: every 4 days
#
# Install to launchd:
#   cp kna-research-agents.forum.plist ~/Library/LaunchAgents/
#   cp kna-research-agents.agora.plist ~/Library/LaunchAgents/
#   launchctl load ~/Library/LaunchAgents/kna-research-agents.forum.plist
#   launchctl load ~/Library/LaunchAgents/kna-research-agents.agora.plist

set -e
cd /Volumes/kyusik-ssd/kyusik-research/projects/kna-research-agents

MODE="${1:-forum}"  # "forum" or "agora"
LOG="/tmp/kna-auto-${MODE}.log"
LAST_RUN_FILE="/tmp/kna-last-${MODE}.txt"
NOW=$(date +%s)

# Check interval since last run (catches up if computer was off)
if [ -f "$LAST_RUN_FILE" ]; then
    LAST_RUN=$(cat "$LAST_RUN_FILE")
    ELAPSED=$(( (NOW - LAST_RUN) / 86400 ))
    if [ "$MODE" = "forum" ] && [ "$ELAPSED" -lt 4 ]; then
        echo "$(date): Skipping forum (${ELAPSED}d since last, need 4d)" >> "$LOG"
        exit 0
    fi
    if [ "$MODE" = "agora" ] && [ "$ELAPSED" -lt 2 ]; then
        echo "$(date): Skipping agora (${ELAPSED}d since last, need 2d)" >> "$LOG"
        exit 0
    fi
fi

# Record this run
echo "$NOW" > "$LAST_RUN_FILE"

echo "$(date): Starting ${MODE} run" >> "$LOG"

if [ "$MODE" = "forum" ]; then
    # Forum: 1 round, resume from existing, agents pick topic
    python3 run_forum.py --rounds 1 --resume >> "$LOG" 2>&1

    # Check for pursue verdicts -> auto-draft articles
    python3 draft_article.py >> "$LOG" 2>&1

    # Build site and push
    python3 build_site.py >> "$LOG" 2>&1
    git add forum/ summaries/ knowledge/ articles/ docs/ && \
    git commit -m "Auto: Forum round $(ls forum/*.md 2>/dev/null | grep -v gitkeep | wc -l | tr -d ' ') posts" && \
    git push origin main >> "$LOG" 2>&1

elif [ "$MODE" = "agora" ]; then
    # Agora: search Naver News for a recent 국회/정치 article and extract headline
    TOPIC=$(claude -p --allowedTools Bash --dangerously-skip-permissions --output-format text \
        "Search Naver News for a recent Korean politics/국회 headline that would spark citizen debate. Run: curl -s 'https://search.naver.com/search.naver?where=news&query=국회+정치&sort=1' and extract the most debate-worthy headline from the results. Return ONLY the headline text in Korean, 1-2 sentences. Nothing else." \
        2>/dev/null | tail -1)

    if [ -n "$TOPIC" ]; then
        python3 agora/run_agora.py --news "$TOPIC" --personas 12 >> "$LOG" 2>&1

        # Build site and push
        python3 build_site.py >> "$LOG" 2>&1
        git add agora/discussions/ docs/agora.html && \
        git commit -m "Auto: Agora discussion - $(echo $TOPIC | head -c 50)" && \
        git push origin main >> "$LOG" 2>&1
    fi
fi

echo "$(date): ${MODE} run complete" >> "$LOG"

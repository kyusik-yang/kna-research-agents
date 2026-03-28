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
DAY_OF_YEAR=$(date +%j)

# Frequency check: forum every 4 days, agora every 2 days
if [ "$MODE" = "forum" ] && [ $((DAY_OF_YEAR % 4)) -ne 0 ]; then
    echo "$(date): Skipping forum (not a 4-day interval)" >> "$LOG"
    exit 0
fi
if [ "$MODE" = "agora" ] && [ $((DAY_OF_YEAR % 2)) -ne 0 ]; then
    echo "$(date): Skipping agora (not a 2-day interval)" >> "$LOG"
    exit 0
fi

echo "$(date): Starting ${MODE} run" >> "$LOG"

if [ "$MODE" = "forum" ]; then
    # Forum: 1 round, resume from existing, agents pick topic
    python3 run_forum.py --rounds 1 --resume >> "$LOG" 2>&1

    # Build site and push
    python3 build_site.py >> "$LOG" 2>&1
    git add forum/ summaries/ knowledge/ docs/ && \
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

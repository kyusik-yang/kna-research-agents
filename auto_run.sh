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
# Resolve repo root from script location so this works on any host
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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
    # Season 2 (2026-08-24): the runner never invents topics. Arcs open only
    # from a researcher-signed topic_gate entry via run_arc.py --topic.
    # Cron continues the active arc one supervised step at a time; run_arc
    # builds the site and commits/pushes on its own.
    if [ -f knowledge/active_arc.json ] &&        [ "$(python3 -c "import json;print(json.load(open('knowledge/arc_status.json')).get('state','running'))" 2>/dev/null || echo running)" = "running" ]; then
        python3 run_arc.py --max-rounds 1 >> "$LOG" 2>&1
    else
        echo "$(date): Season 2 - no running arc; waiting for a researcher-signed topic." >> "$LOG"
    fi

    # Check cumulative rounds for conference trigger (every 20 rounds)
    TOTAL_ROUNDS=$(ls forum_archive/*/0*_critic.md 2>/dev/null summaries/round_*.md 2>/dev/null | wc -l | tr -d ' ')
    LAST_CONF=$(ls articles/conference_*.md 2>/dev/null | wc -l | tr -d ' ')
    CONF_THRESHOLD=$(( (LAST_CONF + 1) * 20 ))
    if [ "$TOTAL_ROUNDS" -ge "$CONF_THRESHOLD" ]; then
        echo "$(date): ${TOTAL_ROUNDS} cumulative rounds - generating conference #$((LAST_CONF + 1))" >> "$LOG"
        python3 generate_conference.py >> "$LOG" 2>&1
        python3 build_site.py >> "$LOG" 2>&1
        git add articles/ docs/ && git commit -m "Auto: conference proceedings" && git push origin main >> "$LOG" 2>&1
    fi

elif [ "$MODE" = "agora" ]; then
    # Check if a new article was recently published -> discuss it (top-down)
    LATEST_ARTICLE=$(ls -t articles/*.md 2>/dev/null | grep -v conference | head -1)
    ARTICLE_DISCUSSED="/tmp/kna-agora-article-discussed.txt"

    if [ -n "$LATEST_ARTICLE" ] && [ ! -f "$ARTICLE_DISCUSSED" ]; then
        # Extract article summary for citizen discussion
        FINDING=$(claude -p --allowedTools Read --dangerously-skip-permissions --output-format text \
            "Read $LATEST_ARTICLE and extract the key finding in 2-3 sentences in Korean. This is for Korean citizens to discuss. Summarize what the research found, why it matters, and one surprising number. Korean only. No English." \
            2>/dev/null | tail -3)

        if [ -n "$FINDING" ]; then
            python3 agora/run_agora.py --finding "$FINDING" --personas 12 >> "$LOG" 2>&1
            echo "$LATEST_ARTICLE" > "$ARTICLE_DISCUSSED"
            echo "$(date): Discussed article: $LATEST_ARTICLE" >> "$LOG"
        fi
    else
        # Normal mode: fetch real-time Yonhap politics RSS, pick most debate-worthy
        TOPIC=$(claude -p --allowedTools Bash --dangerously-skip-permissions --output-format text \
            "Fetch the latest Korean politics headlines from Yonhap RSS. Run: curl -sL 'https://www.yna.co.kr/rss/politics.xml' | head -100. Pick the ONE headline most likely to spark citizen debate (elections, policy, scandal, reform). Expand it into 1-2 sentences of context in Korean. Return ONLY the Korean text, nothing else." \
            2>/dev/null | tail -3)

        python3 agora/run_agora.py --news "$TOPIC" --personas 12 >> "$LOG" 2>&1
    fi

    # Build site and push
    python3 build_site.py >> "$LOG" 2>&1
    git add agora/discussions/ docs/agora.html && \
    git commit -m "Auto: Agora discussion" && \
    git push origin main >> "$LOG" 2>&1
fi

echo "$(date): ${MODE} run complete" >> "$LOG"

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
    # Check if last round produced an article (pursue -> article published)
    # If so, start a NEW topic thread (archive old forum, fresh start)
    ARTICLE_MARKER="/tmp/kna-article-published.txt"
    if [ -f "$ARTICLE_MARKER" ]; then
        echo "$(date): Article was published. Starting new topic thread." >> "$LOG"
        # Archive current forum to a timestamped directory
        ARCHIVE="forum_archive/$(date +%Y%m%d_%H%M)"
        mkdir -p "$ARCHIVE"
        mv forum/0*.md "$ARCHIVE/" 2>/dev/null
        mv summaries/round_*.md "$ARCHIVE/" 2>/dev/null
        # Clear findings for fresh thread
        : > knowledge/findings.jsonl
        rm -f knowledge/human_context.md
        rm "$ARTICLE_MARKER"
        echo "$(date): Archived to $ARCHIVE. Fresh forum start." >> "$LOG"

        # Pick a new topic via Claude (based on recent agora demands or autonomous)
        NEW_TOPIC=$(claude -p --output-format text \
            "You are a political science research agenda setter. Based on Korean legislative politics, suggest ONE specific research question that would make a good forum topic. Focus on the Korean National Assembly. Be specific and empirical. One sentence only. English." \
            2>/dev/null | tail -1)
        python3 run_forum.py --topic "$NEW_TOPIC" --rounds 1 >> "$LOG" 2>&1
    else
        # Continue existing thread
        python3 run_forum.py --rounds 1 --resume >> "$LOG" 2>&1
    fi

    # Check for pursue verdicts -> auto-draft articles
    python3 draft_article.py >> "$LOG" 2>&1

    # If a new article was just created, mark it for next run
    LATEST_ARTICLE=$(ls -t articles/*.md 2>/dev/null | head -1)
    if [ -n "$LATEST_ARTICLE" ]; then
        ARTICLE_AGE=$(( ($(date +%s) - $(stat -f %m "$LATEST_ARTICLE")) / 60 ))
        if [ "$ARTICLE_AGE" -lt 30 ]; then
            touch "$ARTICLE_MARKER"
            echo "$(date): Article published, next run will start fresh topic." >> "$LOG"
        fi
    fi

    # Check cumulative rounds for conference trigger (every 20 rounds)
    TOTAL_ROUNDS=$(ls forum_archive/*/0*_critic.md 2>/dev/null summaries/round_*.md 2>/dev/null | wc -l | tr -d ' ')
    LAST_CONF=$(ls articles/conference_*.md 2>/dev/null | wc -l | tr -d ' ')
    CONF_THRESHOLD=$(( (LAST_CONF + 1) * 20 ))
    if [ "$TOTAL_ROUNDS" -ge "$CONF_THRESHOLD" ]; then
        echo "$(date): ${TOTAL_ROUNDS} cumulative rounds - generating conference #$((LAST_CONF + 1))" >> "$LOG"
        python3 generate_conference.py >> "$LOG" 2>&1
    fi

    # Build site and push
    python3 build_site.py >> "$LOG" 2>&1
    git add forum/ summaries/ knowledge/ articles/ docs/ forum_archive/ && \
    git commit -m "Auto: Forum round $(ls forum/*.md 2>/dev/null | grep -v gitkeep | wc -l | tr -d ' ') posts" && \
    git push origin main >> "$LOG" 2>&1

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
        # Normal mode: search Naver News
        TOPIC=$(claude -p --allowedTools Bash --dangerously-skip-permissions --output-format text \
            "Search Naver News for a recent Korean politics/국회 headline that would spark citizen debate. Run: curl -s 'https://search.naver.com/search.naver?where=news&query=국회+정치&sort=1' and extract the most debate-worthy headline from the results. Return ONLY the headline text in Korean, 1-2 sentences. Nothing else." \
            2>/dev/null | tail -1)

        python3 agora/run_agora.py --news "$TOPIC" --personas 12 >> "$LOG" 2>&1
    fi

    # Build site and push
    python3 build_site.py >> "$LOG" 2>&1
    git add agora/discussions/ docs/agora.html && \
    git commit -m "Auto: Agora discussion" && \
    git push origin main >> "$LOG" 2>&1
fi

echo "$(date): ${MODE} run complete" >> "$LOG"

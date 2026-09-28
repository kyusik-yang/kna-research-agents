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
# Schedule state and logs. Tests point KNA_AUTO_STATE_DIR at a scratch folder.
STATE_DIR="${KNA_AUTO_STATE_DIR:-/tmp}"
LOG="$STATE_DIR/kna-auto-${MODE}.log"
LAST_RUN_FILE="$STATE_DIR/kna-last-${MODE}.txt"
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

# A usage limit (exit 75 from claude_cli) blocks every model until reset.
# The run then stops without building or pushing. claude_cli already raised the alert.
stop_on_usage_limit() {
    if [ "$1" -eq 75 ]; then
        echo "$(date): ${MODE} run stopped on a usage limit" >> "$LOG"
        exit 75
    fi
}

if [ "$MODE" = "forum" ]; then
    # Season 2 (2026-08-24): cron never invents topics. Arcs open only from a
    # signed topic_gate entry, written by auto_arc.py start (2026-09-26) or by
    # hand, with drafted_by and signed_by lines recording who drafted and who
    # signed it (D-10). Cron continues a running arc one supervised step at a
    # time. run_arc builds the site, commits, and pushes only after
    # release_check.py passes. A paused arc (usage limit) waits for
    # auto_arc.py resume. run_arc exits 4 while another run_arc holds its lock
    # (for example an auto_arc run), and then this step is skipped.
    if [ -f knowledge/active_arc.json ] &&        [ "$(python3 -c "import json;print(json.load(open('knowledge/arc_status.json')).get('state','running'))" 2>/dev/null || echo running)" = "running" ]; then
        RC=0
        python3 run_arc.py --max-rounds 1 >> "$LOG" 2>&1 || RC=$?
        if [ "$RC" -eq 4 ]; then
            echo "$(date): another run_arc is running. Skipped this step." >> "$LOG"
        elif [ "$RC" -ne 0 ]; then
            stop_on_usage_limit "$RC"
            exit "$RC"
        fi
    else
        echo "$(date): Season 2 - no running arc. Waiting for a signed topic_gate entry. python3 auto_arc.py start opens one." >> "$LOG"
    fi

    # Check cumulative rounds for conference trigger (every 20 rounds)
    TOTAL_ROUNDS=$(ls forum_archive/*/0*_critic.md 2>/dev/null summaries/round_*.md 2>/dev/null | wc -l | tr -d ' ')
    LAST_CONF=$(ls articles/conference_*.md 2>/dev/null | wc -l | tr -d ' ')
    CONF_THRESHOLD=$(( (LAST_CONF + 1) * 20 ))
    # Quarantined proceedings stay in workspace/failed_drafts/conference_<N>_*
    # and do not raise LAST_CONF. Each conference number gets at most
    # CONF_MAX_ATTEMPTS model calls, so a failing gate is not regenerated on
    # every tick (V-08).
    CONF_MAX_ATTEMPTS="${KNA_CONF_MAX_ATTEMPTS:-2}"
    CONF_FAILED=$(ls -d workspace/failed_drafts/conference_$((LAST_CONF + 1))_* 2>/dev/null | wc -l | tr -d ' ')
    if [ "$TOTAL_ROUNDS" -ge "$CONF_THRESHOLD" ] && [ "$CONF_FAILED" -ge "$CONF_MAX_ATTEMPTS" ]; then
        echo "$(date): conference #$((LAST_CONF + 1)) failed the publish gate ${CONF_FAILED} times. Not regenerating. The drafts are in workspace/failed_drafts/." >> "$LOG"
    elif [ "$TOTAL_ROUNDS" -ge "$CONF_THRESHOLD" ]; then
        echo "$(date): ${TOTAL_ROUNDS} cumulative rounds - generating conference #$((LAST_CONF + 1))" >> "$LOG"
        # generate_conference.py gates the proceedings (leak lint with the G6
        # blocking rule, G4 overclaim lint). Exit 2 means they failed and were
        # moved to workspace/failed_drafts/, so nothing is built, committed or pushed.
        RC=0
        python3 generate_conference.py >> "$LOG" 2>&1 || RC=$?
        stop_on_usage_limit "$RC"
        if [ "$RC" -eq 2 ]; then
            echo "$(date): conference proceedings failed the publish gate and were quarantined. Nothing pushed." >> "$LOG"
        elif [ "$RC" -ne 0 ]; then
            exit "$RC"
        else
            python3 build_site.py >> "$LOG" 2>&1
            git add articles/ docs/ && git commit -m "Auto: conference proceedings" && git push origin main >> "$LOG" 2>&1
        fi
    fi

elif [ "$MODE" = "agora" ]; then
    # Discussion files present before this run (V-08). When the run or the
    # publish gate fails, the files this run added are moved to
    # workspace/failed_drafts/, so no ungated discussion is left for a later
    # build_site (run_arc commits docs/) to render and push.
    AGORA_BEFORE="$STATE_DIR/kna-agora-before.txt"
    ls -1A agora/discussions > "$AGORA_BEFORE" 2>/dev/null || : > "$AGORA_BEFORE"
    quarantine_new_discussions() {
        python3 - "$AGORA_BEFORE" "$1" >> "$LOG" 2>&1 <<'PY' || true
import json, shutil, sys
from datetime import datetime
from pathlib import Path
before = set(Path(sys.argv[1]).read_text(encoding="utf-8").splitlines())
src = Path("agora/discussions")
new = sorted(p for p in src.iterdir() if p.name not in before) if src.is_dir() else []
if new:
    base = Path("workspace/failed_drafts") / f"agora_ungated_{datetime.now():%Y%m%d_%H%M%S}"
    dest, k = base, 1
    while dest.exists():
        dest, k = Path(f"{base}.{k}"), k + 1
    dest.mkdir(parents=True)
    for p in new:
        shutil.move(str(p), str(dest / p.name))
    (dest / "FAILED.json").write_text(json.dumps({
        "reason": sys.argv[2], "when": datetime.now().isoformat(timespec="seconds"),
        "files": [f"agora/discussions/{p.name}" for p in new]}, ensure_ascii=False, indent=1) + "\n")
    print(f"  moved {len(new)} ungated agora file(s) to {dest}")
PY
    }

    # Check if a new article was recently published -> discuss it (top-down)
    LATEST_ARTICLE=$(ls -t articles/*.md 2>/dev/null | grep -v conference | head -1)
    ARTICLE_DISCUSSED="$STATE_DIR/kna-agora-article-discussed.txt"

    if [ -n "$LATEST_ARTICLE" ] && [ ! -f "$ARTICLE_DISCUSSED" ]; then
        # Extract article summary for citizen discussion (through claude_cli)
        RC=0
        RAW=$(python3 scripts/agora_stimulus.py finding "$LATEST_ARTICLE" 2>>"$LOG") || RC=$?
        stop_on_usage_limit "$RC"
        FINDING=$(printf '%s\n' "$RAW" | tail -3)

        if [ -n "$FINDING" ]; then
            python3 agora/run_agora.py --finding "$FINDING" --personas 12 >> "$LOG" 2>&1 || { RC=$?; quarantine_new_discussions "run_agora exited ${RC}"; stop_on_usage_limit "$RC"; exit "$RC"; }
            echo "$LATEST_ARTICLE" > "$ARTICLE_DISCUSSED"
            echo "$(date): Discussed article: $LATEST_ARTICLE" >> "$LOG"
        fi
    else
        # Normal mode: fetch real-time Yonhap politics RSS, pick most debate-worthy
        RC=0
        RAW=$(python3 scripts/agora_stimulus.py news 2>>"$LOG") || RC=$?
        stop_on_usage_limit "$RC"
        TOPIC=$(printf '%s\n' "$RAW" | tail -3)

        python3 agora/run_agora.py --news "$TOPIC" --personas 12 >> "$LOG" 2>&1 || { RC=$?; quarantine_new_discussions "run_agora exited ${RC}"; stop_on_usage_limit "$RC"; exit "$RC"; }
    fi

    # Gate every discussion file the commit below would stage (leak lint with
    # the G6 blocking rule, G4 overclaim lint) before the site is built. A
    # discussion that fails is moved to workspace/failed_drafts/ and the rest
    # is published. Any other failure stops the run before the build and push.
    RC=0
    python3 generate_conference.py --gate-pending agora/discussions --label agora >> "$LOG" 2>&1 || RC=$?
    if [ "$RC" -eq 2 ]; then
        echo "$(date): an agora discussion failed the publish gate and was quarantined" >> "$LOG"
    elif [ "$RC" -ne 0 ]; then
        quarantine_new_discussions "agora publish gate exited ${RC}"
        echo "$(date): agora publish gate exited ${RC}. This run's discussion files were moved to workspace/failed_drafts/. Nothing built or pushed." >> "$LOG"
        exit "$RC"
    fi

    # Build site and push
    python3 build_site.py >> "$LOG" 2>&1
    git add agora/discussions/ docs/agora.html && \
    git commit -m "Auto: Agora discussion" && \
    git push origin main >> "$LOG" 2>&1
fi

echo "$(date): ${MODE} run complete" >> "$LOG"

#!/bin/bash
# =============================================================
# Mac Mini Setup for kna-research-agents
# =============================================================
# Run this once on your Mac Mini to set up everything.
# Then use the cron commands at the bottom to schedule.
#
# Usage:
#   bash setup_macmini.sh
# =============================================================

set -e

REPO_DIR="$HOME/kna-research-agents"

echo "=== 1. Clone or update repo ==="
if [ -d "$REPO_DIR" ]; then
  cd "$REPO_DIR" && git pull
else
  git clone https://github.com/kyusik-yang/kna-research-agents.git "$REPO_DIR"
fi

echo ""
echo "=== 2. Install Python dependencies ==="
pip3 install --user markdown pyyaml

echo ""
echo "=== 3. Test weekly scan (dry run - 7 days) ==="
cd "$REPO_DIR"
python3 weekly_scan.py --days 7

echo ""
echo "=== 4. Test abstract collector ==="
python3 collect_abstracts.py --stats 2>/dev/null || python3 collect_abstracts.py --query "국회 입법"

echo ""
echo "=== DONE ==="
echo ""
echo "To run manually:"
echo "  cd $REPO_DIR"
echo "  python3 weekly_scan.py              # scan last 7 days"
echo "  python3 collect_abstracts.py        # collect abstracts"
echo ""
echo "To schedule weekly (every Sunday 9am):"
echo "  crontab -e"
echo "  # Add these two lines:"
echo "  0 9 * * 0 cd $REPO_DIR && python3 weekly_scan.py >> logs/weekly_scan.log 2>&1"
echo "  0 10 * * 0 cd $REPO_DIR && python3 collect_abstracts.py >> logs/collect_abstracts.log 2>&1"

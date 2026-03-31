#!/usr/bin/env python3
"""Run forum rounds 7-10 with full autonomous loop."""
import subprocess
import sys
import json
from pathlib import Path

BASE = Path(__file__).parent
ARTICLES = BASE / "articles"
KNOWLEDGE = BASE / "knowledge"

def count_posts():
    return len([f for f in (BASE / "forum").glob("*.md") if f.name != ".gitkeep"])

def get_current_round():
    """Detect current round from posts."""
    posts = sorted((BASE / "forum").glob("*.md"))
    posts = [p for p in posts if p.name != ".gitkeep"]
    if not posts:
        return 0
    # Count agent cycles
    rnd = 1
    prev = None
    order = {"literature_scout": 0, "data_analyst": 1, "critic": 2}
    for p in posts:
        agent = None
        for a in order:
            if a in p.name:
                agent = a
                break
        if agent and prev and order.get(agent, 0) <= order.get(prev, -1) and order.get(prev, -1) >= 2:
            rnd += 1
        prev = agent
    return rnd

def has_new_pursue():
    """Check if latest round has a pursue verdict without an article."""
    findings = KNOWLEDGE / "findings.jsonl"
    if not findings.exists():
        return False, 0
    pursues = []
    with open(findings) as f:
        for line in f:
            try:
                e = json.loads(line)
                if e.get("verdict") == "pursue":
                    pursues.append(e)
            except:
                pass
    if not pursues:
        return False, 0
    latest = pursues[-1]
    rnd = latest["round"]
    # Check if article exists for this round
    existing = list(ARTICLES.glob(f"*_r{rnd}.*"))
    if existing:
        return False, rnd
    return True, rnd

def run_cmd(cmd, timeout=3600):
    print(f"  > {' '.join(cmd[:5])}...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT")
        return False

def main():
    target = 20
    current = get_current_round()
    print(f"\n  Autonomous Loop: Round {current+1} to {target}")
    print(f"  Current posts: {count_posts()}")
    print()

    while get_current_round() < target:
        rnd = get_current_round() + 1
        print(f"\n{'='*50}")
        print(f"  ROUND {rnd}")
        print(f"{'='*50}")

        # Run forum round
        print(f"\n  Step 1: Forum round...")
        run_cmd(["python3", "run_forum.py", "--rounds", "1", "--resume"])

        # Update findings + generate summary
        print(f"  Step 2: Update findings + summary...")
        subprocess.run(["python3", "-c",
            f"from run_forum import update_findings_tracker, generate_round_summary; "
            f"update_findings_tracker({rnd}); generate_round_summary({rnd})"],
            capture_output=True, text=True, timeout=300)

        # Check for pursue -> draft article
        has_pursue, pursue_rnd = has_new_pursue()
        if has_pursue:
            print(f"\n  Step 3: PURSUE verdict at Round {pursue_rnd} -> Drafting article...")
            run_cmd(["python3", "draft_article.py", "--round", str(pursue_rnd)], timeout=1800)

            # If article created, next round starts new topic
            new_articles = list(ARTICLES.glob(f"*_r{pursue_rnd}.tex"))
            if new_articles:
                print(f"  Article published! Next round will start new topic.")
                # Clear human context for fresh start
                ctx = KNOWLEDGE / "human_context.md"
                if ctx.exists():
                    ctx.unlink()
        else:
            print(f"  Step 3: No new pursue verdict, continuing thread.")

        # Build and push
        print(f"\n  Step 4: Build site + push...")
        subprocess.run(["python3", "build_site.py"], capture_output=True, timeout=120)
        subprocess.run(["git", "add", "-A"], capture_output=True, timeout=30)
        subprocess.run(["git", "commit", "-m",
            f"Auto loop: Round {rnd} ({count_posts()} posts)"],
            capture_output=True, timeout=30)
        subprocess.run(["git", "push", "origin", "main"], capture_output=True, timeout=60)

        print(f"\n  Round {rnd} complete. Posts: {count_posts()}")

    print(f"\n{'='*50}")
    print(f"  LOOP COMPLETE: {get_current_round()} rounds, {count_posts()} posts")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()

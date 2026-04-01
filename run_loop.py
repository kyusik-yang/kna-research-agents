#!/usr/bin/env python3
"""
Autonomous Forum Loop
=====================
Runs forum rounds with full lifecycle:
  - Forum round (Scout -> Analyst -> Critic)
  - Pursue verdict -> Article draft
  - Article published -> Archive forum -> New topic
  - 20 rounds -> Conference
"""
import subprocess
import sys
import json
import shutil as _sh
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
FORUM = BASE / "forum"
ARTICLES = BASE / "articles"
KNOWLEDGE = BASE / "knowledge"
SUMMARIES = BASE / "summaries"
ARCHIVE = BASE / "forum_archive"
WORKSPACE = BASE / "workspace"

CLAUDE = _sh.which("claude") or str(Path.home() / ".local" / "bin" / "claude")


def count_posts():
    return len([f for f in FORUM.glob("*.md") if f.name != ".gitkeep"])


def get_current_round():
    """Detect current round from posts using agent cycle detection."""
    posts = sorted(f for f in FORUM.glob("*.md") if f.name != ".gitkeep")
    if not posts:
        return 0
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


def count_cumulative_rounds():
    """Count total rounds across current + archived forums (excluding legacy_v1)."""
    current = len(list(SUMMARIES.glob("round_*.md"))) if SUMMARIES.exists() else 0
    archived = 0
    if ARCHIVE.exists():
        for d in ARCHIVE.iterdir():
            if d.is_dir() and d.name != "legacy_v1":
                archived += len(list(d.glob("round_*.md")))
    return current + archived


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
    existing = list(ARTICLES.glob(f"*_r{rnd}.tex")) + list(ARTICLES.glob(f"*_r{rnd}.md"))
    existing = [e for e in existing if "template" not in e.name and "content" not in e.name]
    if existing:
        return False, rnd
    return True, rnd


def prepare_new_topic():
    """Prepare for a new topic thread. Posts stay, numbering continues."""
    # Clear human context
    ctx = KNOWLEDGE / "human_context.md"
    if ctx.exists():
        ctx.unlink()

    print(f"  Ready for new topic. Posts: {count_posts()}, Round: {get_current_round()}")


def pick_new_topic():
    """Use Claude to pick a new research topic, informed by agora demands + previous topics."""
    AGORA_DIR = BASE / "agora" / "discussions"

    # Gather previous topics from archived summaries
    prev_topics = []
    if ARCHIVE.exists():
        for d in sorted(ARCHIVE.iterdir()):
            if d.is_dir():
                for s in d.glob("round_*.md"):
                    for line in s.read_text().split("\n"):
                        if line.startswith("topic:"):
                            prev_topics.append(line.split(":", 1)[1].strip().strip('"'))

    # Gather citizen research demands from agora
    citizen_demands = []
    if AGORA_DIR.exists():
        for f in sorted(AGORA_DIR.glob("*.json")):
            try:
                d = json.load(open(f))
                for dm in d.get("research_demands", []):
                    citizen_demands.append(dm.get("demand", "")[:100])
            except:
                pass

    prev_str = ", ".join(prev_topics[:10]) if prev_topics else "none yet"
    demands_str = "\n".join(f"- {d}" for d in citizen_demands[-10:]) if citizen_demands else "none yet"

    prompt = (
        f"You are a political science research agenda setter. "
        f"Previous forum topics were: {prev_str}. "
        f"Recent citizen research demands from Yeouido Agora:\n{demands_str}\n\n"
        f"Suggest ONE specific, novel research question about the Korean National Assembly "
        f"that is DIFFERENT from all previous topics. "
        f"Two sources of inspiration: "
        f"(1) Citizen demands from Yeouido Agora listed above, if any suggest an interesting empirical puzzle. "
        f"(2) Your own knowledge of political science literature, identifying gaps or untested theories. "
        f"Either source is fine. Pick whichever yields the most promising question. "
        f"Focus on something testable with bill data, roll call votes, "
        f"committee records, member metadata (party, district, committee, seniority, gender), "
        f"or hearing transcripts (9.9M speeches, 7.4M Q&A dyads). "
        f"One sentence only. English."
    )

    try:
        r = subprocess.run(
            [CLAUDE, "-p", "--output-format", "text", prompt],
            capture_output=True, text=True, timeout=120,
        )
        topic = r.stdout.strip().split("\n")[-1]
        if len(topic) > 20:
            return topic
    except:
        pass

    return "legislative productivity and institutional reform in the Korean National Assembly"


def run_cmd(cmd, timeout=3600):
    print(f"  > {' '.join(str(c) for c in cmd[:5])}...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT")
        return False


def main():
    target = int(sys.argv[1]) if len(sys.argv) > 1 else 20

    print(f"\n  Autonomous Loop (target: {target} cumulative rounds)")
    print(f"  Current round: {get_current_round()}")
    print(f"  Cumulative: {count_cumulative_rounds()}")
    print(f"  Posts: {count_posts()}")
    print()

    max_articles = 2  # Stop after 2 articles for quality check

    # Detect if we need a new topic on startup
    # (article exists for current thread but forum wasn't archived)
    MARKER = BASE / "knowledge" / ".need_new_topic"
    need_new_topic = MARKER.exists()

    if not need_new_topic:
        # Also check: any article exists AND forum still has posts from that thread
        existing_articles = [f for f in ARTICLES.glob("*.tex") if "template" not in f.name]
        if existing_articles and count_posts() > 0:
            need_new_topic = True
            print(f"  Detected: article published but forum not archived. Starting new topic.")

    while count_cumulative_rounds() < target:
        rnd = get_current_round() + 1
        cumulative = count_cumulative_rounds() + 1

        print(f"\n{'='*50}")
        print(f"  ROUND {rnd} (cumulative: {cumulative}/{target})")
        print(f"{'='*50}")

        # If we need a new topic (after article publication), archive and reset
        if need_new_topic:
            print(f"\n  Picking new topic (posts and numbering continue)...")
            prepare_new_topic()
            new_topic = pick_new_topic()
            # Set topic break marker so agents don't see previous topic's posts
            next_round = get_current_round() + 1
            (KNOWLEDGE / "topic_break.txt").write_text(str(next_round))
            print(f"  New topic (R{next_round}): {new_topic}")
            run_cmd(["python3", "run_forum.py", "--topic", new_topic, "--rounds", "1", "--resume"])
            need_new_topic = False
            if MARKER.exists():
                MARKER.unlink()
        else:
            # Continue existing thread
            run_cmd(["python3", "run_forum.py", "--rounds", "1", "--resume"])

        # Update findings + generate summary
        actual_rnd = get_current_round()
        print(f"  Updating findings + summary (round {actual_rnd})...")
        subprocess.run(["python3", "-c",
            f"from run_forum import update_findings_tracker, generate_round_summary; "
            f"update_findings_tracker({actual_rnd}); generate_round_summary({actual_rnd})"],
            capture_output=True, text=True, timeout=3600)

        # Check for pursue -> draft article
        has_pursue, pursue_rnd = has_new_pursue()
        if has_pursue:
            print(f"\n  PURSUE verdict at Round {pursue_rnd} -> Drafting article...")
            run_cmd(["python3", "draft_article.py", "--round", str(pursue_rnd)], timeout=3600)

            # Copy PDFs to docs
            for pdf in ARTICLES.glob(f"*_r{pursue_rnd}.pdf"):
                dest = BASE / "docs" / "articles" / pdf.name
                dest.parent.mkdir(exist_ok=True, parents=True)
                _sh.copy2(str(pdf), str(dest))

            # Check if article was actually created
            new_articles = list(ARTICLES.glob(f"*_r{pursue_rnd}.tex"))
            new_articles = [a for a in new_articles if "template" not in a.name]
            if new_articles:
                print(f"  Article published! Next round starts NEW topic.")
                need_new_topic = True
                MARKER.write_text("1")  # persist across restarts
        else:
            print(f"  No new pursue verdict, continuing thread.")

        # Check for conference trigger
        cum = count_cumulative_rounds()
        existing_conf = len(list(ARTICLES.glob("conference_*.md")))
        conf_threshold = (existing_conf + 1) * 20
        if cum >= conf_threshold:
            print(f"\n  {cum} cumulative rounds -> CONFERENCE #{existing_conf + 1}")
            run_cmd(["python3", "generate_conference.py", "--force"], timeout=3600)

        # Build and push
        print(f"\n  Build + push...")
        subprocess.run(["python3", "build_site.py"], capture_output=True, timeout=120)
        subprocess.run(["git", "add", "-A"], capture_output=True, timeout=30)
        subprocess.run(["git", "commit", "-m",
            f"Auto: R{actual_rnd} (cumulative {cum}, {count_posts()} posts)"],
            capture_output=True, timeout=30)
        subprocess.run(["git", "push", "origin", "main"], capture_output=True, timeout=60)

        print(f"  Done. Cumulative: {count_cumulative_rounds()}/{target}")

        # Stop after N articles for quality check
        article_count = len([f for f in ARTICLES.glob("*.tex") if "template" not in f.name])
        if article_count >= max_articles:
            print(f"\n  PAUSED: {article_count} articles generated. Waiting for quality check.")
            break

    print(f"\n{'='*50}")
    print(f"  LOOP COMPLETE: {count_cumulative_rounds()} cumulative rounds")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()

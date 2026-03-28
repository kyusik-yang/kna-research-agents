#!/usr/bin/env python3
"""
Research Forum Orchestrator
===========================
Runs AI research agents that search literature (OpenAlex), analyze data (KNA),
and critically review each other's findings in a shared forum.

Usage:
    python3 run_forum.py                       # 1 round, all agents
    python3 run_forum.py --rounds 3            # 3 rounds of discussion
    python3 run_forum.py --agent scout         # Run only Scout
    python3 run_forum.py --topic "legislative polarization in Korea"
    python3 run_forum.py --resume              # Continue from existing posts
    python3 run_forum.py --dry-run             # Preview prompts only
"""

import argparse
import json
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
FORUM_DIR = BASE_DIR / "forum"
LOGS_DIR = BASE_DIR / "logs"
WORKSPACE_DIR = BASE_DIR / "workspace"
AGENTS_FILE = BASE_DIR / "agents.json"

import os
import shutil

KNA_DATA = os.environ.get("KBL_DATA", str(Path.home() / "kna" / "data" / "processed"))
KNA_CLI = shutil.which("kna") or "/usr/local/bin/kna"
CLAUDE = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude")


def load_agents():
    with open(AGENTS_FILE) as f:
        return json.load(f)["agents"]


def get_forum_posts():
    """Read all forum posts, sorted chronologically."""
    posts = sorted(FORUM_DIR.glob("*.md"))
    return posts


def get_forum_state():
    """Compile full forum state as text."""
    posts = get_forum_posts()
    if not posts:
        return "(No posts yet. You are starting the discussion.)"
    parts = []
    for p in posts:
        parts.append(f"--- {p.name} ---\n{p.read_text()}")
    return "\n\n".join(parts)


def next_post_number():
    return len(get_forum_posts()) + 1


def get_knowledge_summary():
    """Summarize the literature knowledge base for agents."""
    log_file = BASE_DIR / "knowledge" / "literature_log.jsonl"
    if not log_file.exists():
        return ""
    entries = []
    with open(log_file) as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    if not entries:
        return ""
    # Show recent 30 entries as context
    recent = entries[-30:]
    lines = ["\n## Literature Knowledge Base (recent entries)\n"]
    for e in recent:
        authors = ", ".join(e.get("authors", [])[:2])
        lines.append(f"- [{e.get('year','')}] {e.get('title','')} ({authors}) [{e.get('source','')}]")
    lines.append(f"\n(Total: {len(entries)} entries in knowledge base)\n")
    return "\n".join(lines)


def build_prompt(agent, round_num, total_rounds, seed_topic=None):
    """Build system prompt for one agent run."""
    forum_state = get_forum_state()
    knowledge = get_knowledge_summary()
    post_num = next_post_number()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    n_agents = len(load_agents())
    is_first_round = post_num <= n_agents

    topic_line = ""
    if seed_topic:
        topic_line = f"\nForum seed topic: **{seed_topic}**\nOrient your first post around this topic, but you may explore related threads.\n"

    if is_first_round:
        task_instruction = (
            "This is the opening round. Start a new research thread based on your specialty. "
            "Be specific and substantive - pick a focused question, gather evidence, and report findings."
        )
    else:
        task_instruction = (
            "Read the existing posts carefully. You should:\n"
            "  (a) Respond to another agent's findings with your own evidence or perspective\n"
            "  (b) Extend someone's analysis with new data or literature\n"
            "  (c) Challenge a claim with counter-evidence\n"
            "  (d) Synthesize multiple threads into a research agenda\n"
            "  (e) Open a new question inspired by the discussion\n"
            "Engage substantively with at least one previous post."
        )

    # Inject runtime paths into agent prompt
    agent_prompt = agent['prompt'].replace("{KNA_CLI}", KNA_CLI).replace("{KNA_DATA}", KNA_DATA)

    prompt = textwrap.dedent(f"""\
    # Research Forum - Round {round_num}/{total_rounds}

    {agent_prompt}

    ## Your Task
    {topic_line}
    {task_instruction}

    ## Output

    Write your post to this exact path:
    {FORUM_DIR}/{post_num:03d}_{agent['id']}.md

    Post format:
    ```
    ---
    author: "{agent['name']}"
    date: "{ts}"
    type: [literature_scan / data_report / review / research_agenda / response / synthesis]
    references: []
    ---

    # [Your Title]

    [Content: 500-1500 words. Show evidence. Be specific.]
    ```

    ## Rules

    - Every factual claim must be backed by a query (OpenAlex API call, KNA command, or pandas code).
    - Do NOT fabricate results. If a query returns nothing useful, say so.
    - When responding to another agent, reference their post filename.
    - Focus on what's INTERESTING, what's MISSING, and what's DOABLE.
    - Write in English. Korean terms (bill names, committee names, politician names) are fine.

    ## Current Forum State

    {forum_state}
    {knowledge}
    """)
    return prompt


def run_agent(agent, round_num, total_rounds, seed_topic=None, dry_run=False):
    """Execute one agent via claude -p."""
    prompt_text = build_prompt(agent, round_num, total_rounds, seed_topic)
    post_num = next_post_number()
    label = f"{agent['name']}"

    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  {label}")
    print(f"  Round {round_num}/{total_rounds} | Post #{post_num}")
    print(f"{sep}")

    if dry_run:
        print(prompt_text[:600] + "\n  ... (truncated)")
        return

    # Write prompt to temp file (avoids shell escaping)
    prompt_file = WORKSPACE_DIR / f"_prompt_{agent['id']}.md"
    prompt_file.write_text(prompt_text)

    log_file = LOGS_DIR / f"r{round_num:02d}_{post_num:03d}_{agent['id']}.log"

    cmd = [
        CLAUDE,
        "-p",
        "--allowedTools", "Bash", "Read", "Write", "Glob", "Grep",
        "--dangerously-skip-permissions",
        "--system-prompt-file", str(prompt_file),
        "--output-format", "text",
        "Execute your research task now. Read the system prompt, query data or literature, write your forum post.",
    ]

    print(f"  Running...")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 min max
            cwd=str(WORKSPACE_DIR),
        )
        log_file.write_text(
            f"EXIT CODE: {result.returncode}\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

        expected = FORUM_DIR / f"{post_num:03d}_{agent['id']}.md"
        if expected.exists():
            content = expected.read_text()
            lines = content.split("\n")
            title = next((l for l in lines if l.startswith("# ") and "---" not in l), "")
            word_count = len(content.split())
            print(f"  Posted: {expected.name} ({word_count} words)")
            print(f"  {title}")
        else:
            # Check for any new post
            all_posts = sorted(FORUM_DIR.glob(f"{post_num:03d}_*.md"))
            if all_posts:
                print(f"  Posted: {all_posts[0].name}")
            else:
                print(f"  WARNING: No post created. Check {log_file.name}")

        if result.returncode != 0:
            print(f"  Exit code: {result.returncode}")

    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT (>10 min)")
        log_file.write_text("TIMEOUT after 600s")
    except Exception as e:
        print(f"  ERROR: {e}")
        log_file.write_text(f"ERROR: {e}")


SUMMARIES_DIR = BASE_DIR / "summaries"


def generate_round_summary(round_num, topic=None):
    """Generate a summary for a completed round using Claude."""
    SUMMARIES_DIR.mkdir(exist_ok=True)

    # Collect posts from this round
    all_posts = sorted(FORUM_DIR.glob("*.md"))
    n_agents = len(load_agents())
    start_idx = (round_num - 1) * n_agents
    end_idx = round_num * n_agents
    round_posts = all_posts[start_idx:end_idx]

    if not round_posts:
        return

    forum_text = "\n\n".join(
        f"--- {p.name} ---\n{p.read_text()}" for p in round_posts
    )
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")

    prompt = textwrap.dedent(f"""\
    You are a research forum moderator. Summarize Round {round_num} of the research discussion.

    Write a concise summary (200-400 words) that:
    1. States the round's topic or focus
    2. Highlights each agent's key finding or contribution (2-3 sentences each)
    3. Notes points of agreement and disagreement between agents
    4. Lists the most promising research directions identified
    5. Identifies what remains unresolved

    Write the summary to: {SUMMARIES_DIR}/round_{round_num:02d}.md

    Use this format:
    ```
    ---
    round: {round_num}
    date: "{ts}"
    topic: "{topic or 'continuing discussion'}"
    ---

    # Round {round_num} Summary

    [Your summary]
    ```

    ## Posts to Summarize

    {forum_text}
    """)

    prompt_file = WORKSPACE_DIR / "_prompt_summary.md"
    prompt_file.write_text(prompt)

    cmd = [
        CLAUDE, "-p",
        "--allowedTools", "Write",
        "--dangerously-skip-permissions",
        "--system-prompt-file", str(prompt_file),
        "--output-format", "text",
        "Write the round summary now.",
    ]

    print(f"\n  Generating Round {round_num} summary...")
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, cwd=str(WORKSPACE_DIR),
        )
        summary_file = SUMMARIES_DIR / f"round_{round_num:02d}.md"
        if summary_file.exists():
            print(f"  Summary: {summary_file.name}")
        else:
            print(f"  WARNING: Summary not generated")
    except subprocess.TimeoutExpired:
        print(f"  Summary generation timed out")


def print_summary():
    """Print forum table of contents."""
    posts = get_forum_posts()
    if not posts:
        print("\n  Forum is empty.")
        return

    print(f"\n{'=' * 60}")
    print(f"  FORUM SUMMARY ({len(posts)} posts)")
    print(f"{'=' * 60}")

    for p in posts:
        content = p.read_text()
        title = "Untitled"
        author = "Unknown"
        post_type = ""
        for line in content.split("\n"):
            if line.startswith("# ") and "---" not in line:
                title = line[2:].strip()
            if line.startswith("author:"):
                author = line.split(":", 1)[1].strip().strip('"')
            if line.startswith("type:"):
                post_type = line.split(":", 1)[1].strip().strip("[]")
        wc = len(content.split())
        print(f"\n  {p.name} ({wc} words)")
        print(f"    {title}")
        print(f"    by {author} [{post_type}]")

    print(f"\n  Posts: {FORUM_DIR}/")
    print(f"  Logs:  {LOGS_DIR}/")
    print(f"  Summaries: {SUMMARIES_DIR}/")


def main():
    parser = argparse.ArgumentParser(
        description="AI Research Forum Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
        Examples:
          python3 run_forum.py --topic "committee gatekeeping in the 22nd Assembly"
          python3 run_forum.py --rounds 2 --topic "polarization trends"
          python3 run_forum.py --agent critic --resume
        """),
    )
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--agent", type=str, default=None, help="Run only matching agent")
    parser.add_argument("--topic", type=str, default=None, help="Seed topic for round 1")
    parser.add_argument("--resume", action="store_true", help="Keep existing posts")
    parser.add_argument("--dry-run", action="store_true", help="Preview prompts only")
    args = parser.parse_args()

    for d in (FORUM_DIR, LOGS_DIR, WORKSPACE_DIR):
        d.mkdir(exist_ok=True)

    agents = load_agents()

    if args.agent:
        agents = [a for a in agents if args.agent.lower() in a["id"]]
        if not agents:
            print(f"No agent matching '{args.agent}'. Available: {[a['id'] for a in load_agents()]}")
            sys.exit(1)

    # Handle existing posts
    existing = list(FORUM_DIR.glob("*.md"))
    if existing and not args.resume and not args.dry_run:
        print(f"\n  {len(existing)} existing posts found.")
        resp = input("  Clear for fresh start? (y/N): ").strip().lower()
        if resp == "y":
            for f in existing:
                f.unlink()
            # Also clear logs
            for f in LOGS_DIR.glob("*.log"):
                f.unlink()
            print("  Cleared.")
        else:
            print("  Keeping. Use --resume to skip this prompt.")

    agent_names = ", ".join(a["name"] for a in agents)
    print(f"\n  Research Forum")
    print(f"  Agents: {agent_names}")
    print(f"  Rounds: {args.rounds}")
    if args.topic:
        print(f"  Topic:  {args.topic}")
    print(f"  APIs:   OpenAlex, Crossref")
    print()

    for rnd in range(1, args.rounds + 1):
        print(f"\n{'#' * 60}")
        print(f"  ROUND {rnd}/{args.rounds}")
        print(f"{'#' * 60}")

        for agent in agents:
            run_agent(
                agent, rnd, args.rounds,
                seed_topic=args.topic if rnd == 1 else None,
                dry_run=args.dry_run,
            )

        if not args.dry_run:
            generate_round_summary(
                rnd, topic=args.topic if rnd == 1 else None,
            )

    print_summary()


if __name__ == "__main__":
    main()

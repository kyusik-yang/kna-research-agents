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
    python3 run_forum.py --comment "Focus on committee gatekeeping next"
"""

import argparse
import json
import re
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
SUMMARIES_DIR = BASE_DIR / "summaries"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"

import os
import shutil

KNA_DATA = os.environ.get("KBL_DATA", str(Path.home() / "kna" / "data" / "processed"))
KNA_CLI = shutil.which("kna") or "/usr/local/bin/kna"
CLAUDE = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude")


def load_agents():
    with open(AGENTS_FILE) as f:
        return json.load(f)["agents"]


# ==========================================================================
# Arc 2 reflection-commitment guardrails (C2 / C3 / C9).
# Added 2026-04-20 per post_conference_reflection_2026-04-20.md.
# ==========================================================================

TOPIC_GATE_FILE = BASE_DIR / "topic_gate.md"
RETREATS_LEDGER = KNOWLEDGE_DIR / "retreats.jsonl"


def check_topic_gate(seed_topic: str, start_round: int, total_existing: int, bypass: bool = False) -> None:
    """C2 (Pepinsky 2026): refuse to open a new research thread without a
    signed topic_gate.md entry for the current seed topic.

    Triggers whenever a seed topic is supplied via --topic, on the grounds
    that --topic is the explicit marker of a new research thread. The
    researcher opts out by omitting --topic (continuation) or by passing
    --bypass-topic-gate (explicit override).

    Each entry in topic_gate.md is an H2 block beginning with "## " and
    containing a line "seed: <seed_topic>" plus a "signed: <ISO-date>" line.
    """
    if bypass or not seed_topic:
        return

    if not TOPIC_GATE_FILE.exists():
        raise SystemExit(
            "[BLOCKED · Topic Gate · C2]\n"
            "A new research thread (or fresh arc) cannot open without a signed\n"
            f"topic_gate.md at the repo root.\n"
            f"Seed topic: {seed_topic}\n"
            f"Expected file: {TOPIC_GATE_FILE}\n"
            "Fix: create topic_gate.md with an entry matching the seed topic\n"
            "(see template in the file, or use --bypass-topic-gate to skip\n"
            "under explicit researcher override)."
        )

    raw = TOPIC_GATE_FILE.read_text()
    # Match an entry whose seed substring occurs + signed line present
    import textwrap
    normalized_seed = re.sub(r"\s+", " ", seed_topic.strip().lower())
    entries = re.split(r"\n## ", raw)
    for entry in entries:
        lower = entry.lower()
        if "signed:" not in lower:
            continue
        seed_line = re.search(r"^seed:\s*(.+)$", entry, re.MULTILINE | re.IGNORECASE)
        if not seed_line:
            continue
        entry_seed = re.sub(r"\s+", " ", seed_line.group(1).strip().lower())
        # Substring OK (researcher may abbreviate in gate); require reasonable overlap
        if entry_seed in normalized_seed or normalized_seed in entry_seed:
            print(f"  [Topic Gate · C2] Signed entry found for: {seed_topic[:80]}")
            return

    raise SystemExit(
        "[BLOCKED · Topic Gate · C2]\n"
        f"topic_gate.md exists but no signed entry matches seed topic:\n"
        f"  {seed_topic}\n"
        "Add a new H2 entry with `seed:` and `signed:` lines, or use\n"
        "--bypass-topic-gate for an explicit researcher override."
    )


def log_retreat(
    originating_round: int,
    overturning_round: int,
    flagged_by: str,
    finding: str,
    reason: str,
    from_status: str = "preliminary",
    to_status: str = "contested",
) -> None:
    """C3 (reflection report): append to the retreat ledger whenever a prior
    finding is overturned. Called manually from agent posts (via Bash) or
    from the orchestrator when summary diffs detect a status transition."""
    RETREATS_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    from datetime import datetime as _dt
    entry = {
        "ts": _dt.now().isoformat(timespec="seconds"),
        "originating_round": originating_round,
        "overturning_round": overturning_round,
        "flagged_by": flagged_by,
        "from_status": from_status,
        "to_status": to_status,
        "finding": finding.strip(),
        "reason": reason.strip(),
    }
    with open(RETREATS_LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"  [Retreat · C3] R{originating_round} → R{overturning_round}: {finding[:60]}")


_CROSSREF_CACHE: dict = {}


def verify_citations(post_path: Path) -> list[str]:
    """C9 (reflection report): scan a committed forum post for DOI and
    author-year citations; Crossref-verify each; return list of
    unverified citations as strings (empty list if all verified).

    DOI pattern: 10.xxxx/yyyy form.
    Author-year pattern: keep minimal here; agents are expected to include
    DOI-anchored references list at the bottom, so we focus on DOI checks.
    """
    import urllib.request
    import urllib.parse

    text = post_path.read_text()
    dois = set(re.findall(r"\b10\.\d{4,9}/[^\s\)\]\"]+", text))
    unverified = []
    for doi in sorted(dois):
        doi = doi.rstrip(".,;)]}")
        if doi in _CROSSREF_CACHE:
            if not _CROSSREF_CACHE[doi]:
                unverified.append(doi)
            continue
        url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='/')}?mailto=kyusik.yang@nyu.edu"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "kna-research-agents/1.0 (mailto:kyusik.yang@nyu.edu)"})
            with urllib.request.urlopen(req, timeout=8) as r:
                ok = r.status == 200
        except Exception:
            ok = False
        _CROSSREF_CACHE[doi] = ok
        if not ok:
            unverified.append(doi)
    if unverified:
        print(f"  [Citation Verify · C9] {post_path.name}: {len(unverified)} unverified DOI(s)")
        for d in unverified[:5]:
            print(f"    - {d}")
    return unverified


def get_forum_posts():
    """Read all forum posts, sorted chronologically."""
    posts = sorted(FORUM_DIR.glob("*.md"))
    return posts


def get_topic_break_round():
    """Check if there's a topic break marker (new topic starts from this round)."""
    marker = KNOWLEDGE_DIR / "topic_break.txt"
    if marker.exists():
        try:
            return int(marker.read_text().strip())
        except ValueError:
            pass
    return 0


def get_forum_state(current_round=1, n_agents=3):
    """Compile forum state with aggressive context compression.

    Strategy:
    - If topic break exists, ONLY show posts from break round onwards
    - Current round (N): full text of all posts so far
    - Previous round (N-1): full text
    - Rounds N-3 to N-2: round SUMMARY only
    - Older: omitted
    """
    posts = get_forum_posts()
    if not posts:
        return "(No posts yet. You are starting a NEW research thread.)"

    # Topic break: only show posts from the new topic onwards
    topic_break = get_topic_break_round()
    if topic_break > 0 and current_round >= topic_break:
        min_round = topic_break
    else:
        min_round = 1

    parts = []

    # If this is the first round of a new topic, say so explicitly
    if topic_break > 0 and current_round == topic_break:
        parts.append(
            "(This is a NEW research topic. Previous rounds covered different topics. "
            "Do NOT reference or respond to previous posts. Start fresh.)"
        )

    # 1. Include round summaries for N-3 and N-2 only (within current topic)
    if SUMMARIES_DIR.exists():
        for sf in sorted(SUMMARIES_DIR.glob("round_*.md")):
            rnd_num = int(re.search(r"(\d+)", sf.stem).group(1))
            if rnd_num >= min_round and current_round - 3 <= rnd_num <= current_round - 2:
                parts.append(f"--- Round {rnd_num} Summary ---\n{sf.read_text()}")

    # 2. Full text for current and previous round only (within current topic)
    for i, p in enumerate(posts):
        post_round = (i // n_agents) + 1
        if post_round >= max(min_round, current_round - 1):
            parts.append(f"--- {p.name} ---\n{p.read_text()}")

    return "\n\n".join(parts)


def next_post_number():
    return len(get_forum_posts()) + 1


def get_knowledge_summary():
    """Summarize the literature knowledge base for agents."""
    log_file = KNOWLEDGE_DIR / "literature_log.jsonl"
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
    recent = entries[-30:]
    lines = ["\n## Literature Knowledge Base (recent entries)\n"]
    for e in recent:
        authors = ", ".join(e.get("authors", [])[:2])
        doi = e.get("doi", "")
        doi_str = f" doi:{doi}" if doi else ""
        lines.append(f"- [{e.get('year','')}] {e.get('title','')} ({authors}) [{e.get('source','')}]{doi_str}")
    lines.append(f"\n(Total: {len(entries)} entries in knowledge base)\n")
    return "\n".join(lines)


def get_relevant_abstracts(topic, max_abstracts=8):
    """Find abstracts relevant to the current topic via keyword matching."""
    abstracts_file = KNOWLEDGE_DIR / "abstracts.jsonl"
    if not abstracts_file.exists():
        return ""

    records = []
    with open(abstracts_file) as f:
        for line in f:
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    if not records or not topic:
        return ""

    # Simple keyword matching
    topic_words = set(topic.lower().split())
    scored = []
    for r in records:
        title = (r.get("title", "") or "").lower()
        abstract = (r.get("abstract", "") or "").lower()
        text = title + " " + abstract
        score = sum(1 for w in topic_words if w in text)
        if score > 0:
            scored.append((score, r))

    scored.sort(key=lambda x: -x[0])
    top = scored[:max_abstracts]

    if not top:
        return ""

    lines = ["\n## Relevant Abstracts from Knowledge Base\n"]
    for _, r in top:
        authors = ", ".join(r.get("authors", [])[:3])
        doi = r.get("doi", "")
        doi_str = f" (doi:{doi})" if doi else ""
        abstract = r.get("abstract", "")[:300]
        lines.append(
            f"### {r.get('title', '')} ({r.get('year', '?')})\n"
            f"*{authors}* - {r.get('journal', '')}{doi_str}\n"
            f"{abstract}...\n"
        )
    return "\n".join(lines)


def get_findings_tracker():
    """Load the cumulative findings tracker for agent context."""
    tracker_file = KNOWLEDGE_DIR / "findings.jsonl"
    if not tracker_file.exists():
        return ""
    findings = []
    with open(tracker_file) as f:
        for line in f:
            try:
                findings.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    if not findings:
        return ""
    lines = ["\n## Cumulative Findings Tracker\n"]
    lines.append("| # | Finding | Status | Round | Source |")
    lines.append("|---|---------|--------|-------|--------|")
    for i, f in enumerate(findings, 1):
        lines.append(
            f"| {i} | {f.get('finding', '')} | "
            f"**{f.get('status', 'preliminary')}** | "
            f"R{f.get('round', '?')} | {f.get('source', '')} |"
        )
    lines.append(
        "\nStatus key: preliminary (new), confirmed (cross-validated), "
        "contested (counter-evidence found), refined (updated by later round)\n"
    )
    return "\n".join(lines)


def update_findings_tracker(round_num):
    """Auto-extract key findings from latest round posts and append to tracker."""
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    tracker_file = KNOWLEDGE_DIR / "findings.jsonl"

    # Get posts from this round
    all_posts = sorted(FORUM_DIR.glob("*.md"))
    n_agents = len(load_agents())
    start_idx = (round_num - 1) * n_agents
    round_posts = all_posts[start_idx:start_idx + n_agents]

    if not round_posts:
        return

    # Extract findings from Critic's scoring block
    for p in round_posts:
        content = p.read_text()
        if "critic" not in p.name:
            continue
        # Extract verdict
        import re
        verdict_match = re.search(r"verdict:\s*(pursue|revise|archive)", content)
        one_line_match = re.search(r'one_line:\s*"([^"]+)"', content)
        if one_line_match:
            finding = {
                "finding": one_line_match.group(1),
                "status": "preliminary",
                "round": round_num,
                "source": p.name,
                "verdict": verdict_match.group(1) if verdict_match else "unknown",
            }
            with open(tracker_file, "a") as f:
                f.write(json.dumps(finding, ensure_ascii=False) + "\n")


def get_existing_articles():
    """Load summaries of existing articles to prevent topic repetition."""
    articles_dir = BASE_DIR / "articles"
    if not articles_dir.exists():
        return ""

    articles = []
    for f in sorted(articles_dir.glob("*.md")):
        content = f.read_text()
        title = ""
        source_round = ""
        status = ""
        for line in content.split("\n"):
            if line.startswith("title:"):
                title = line.split(":", 1)[1].strip().strip('"')
            elif line.startswith("source_round:"):
                source_round = line.split(":", 1)[1].strip()
            elif line.startswith("status:"):
                status = line.split(":", 1)[1].strip().strip('"')
        if title:
            articles.append(f"- Round {source_round}: \"{title}\" [{status}]")

    if not articles:
        return ""

    lines = ["\n## Existing Articles (DO NOT repeat these topics)\n"]
    lines.append(
        "The forum has already produced articles on the following topics. "
        "Your new research thread MUST explore a different question, dataset, "
        "or theoretical angle. Overlap with these topics should be minimal.\n"
    )
    lines.extend(articles)
    lines.append("")
    return "\n".join(lines)


def build_prompt(agent, round_num, total_rounds, seed_topic=None):
    """Build system prompt for one agent run."""
    n_agents = len(load_agents())
    forum_state = get_forum_state(current_round=round_num, n_agents=n_agents)
    knowledge = get_knowledge_summary()
    abstracts = get_relevant_abstracts(seed_topic) if seed_topic else ""
    findings = get_findings_tracker()
    existing_articles = get_existing_articles()

    # Load human context (from --comment or agora demands)
    human_context = ""
    human_ctx_file = KNOWLEDGE_DIR / "human_context.md"
    if human_ctx_file.exists():
        raw = human_ctx_file.read_text().strip()
        if raw:
            human_context = f"\n## Research Context (from Yeouido Agora citizen demands)\n\n{raw}\n\nIncorporate this context naturally into your post. Do not mention 'human researcher' or 'researcher note'. Frame it as: based on citizen research demands from Yeouido Agora, or similar.\n"

    post_num = next_post_number()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
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
    agent_prompt = agent["prompt"].replace("{KNA_CLI}", KNA_CLI).replace("{KNA_DATA}", KNA_DATA)

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
    - Complete ALL items in your Completion Checklist before finishing.

    ## Current Forum State

    {forum_state}
    {knowledge}
    {abstracts}
    {findings}
    {existing_articles}
    {human_context}
    """)
    return prompt


def run_agent(agent, round_num, total_rounds, seed_topic=None, dry_run=False):
    """Execute one agent via claude -p."""
    prompt_text = build_prompt(agent, round_num, total_rounds, seed_topic)
    post_num = next_post_number()
    label = f"{agent['name']}"

    # Agent-specific tool restrictions
    tools = agent.get("allowed_tools", ["Bash", "Read", "Write", "Glob", "Grep"])
    tools_str = ",".join(tools)

    sep = "=" * 60
    print(f"\n{sep}")
    print(f"  {label}")
    print(f"  Round {round_num}/{total_rounds} | Post #{post_num}")
    print(f"  Tools: {tools_str}")
    print(f"{sep}")

    if dry_run:
        print(prompt_text[:600] + "\n  ... (truncated)")
        return

    prompt_file = WORKSPACE_DIR / f"_prompt_{agent['id']}.md"
    prompt_file.write_text(prompt_text)

    log_file = LOGS_DIR / f"r{round_num:02d}_{post_num:03d}_{agent['id']}.log"

    cmd = [
        CLAUDE,
        "-p",
        "--allowedTools", tools_str,
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
            timeout=3600,  # 1 hour
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
            all_posts = sorted(FORUM_DIR.glob(f"{post_num:03d}_*.md"))
            if all_posts:
                print(f"  Posted: {all_posts[0].name}")
            else:
                print(f"  WARNING: No post created. Check {log_file.name}")

        if result.returncode != 0:
            print(f"  Exit code: {result.returncode}")

    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT (>1 hour)")
        log_file.write_text("TIMEOUT after 600s")
    except Exception as e:
        print(f"  ERROR: {e}")
        log_file.write_text(f"ERROR: {e}")


def add_human_comment(comment_text, topic=None):
    """Save a human comment as context for the next round (not as a forum post)."""
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    comment_file = KNOWLEDGE_DIR / "human_context.md"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    comment_file.write_text(f"[{ts}] {comment_text}\n")
    print(f"\n  Context saved (will be injected into next round prompts)")
    print(f"  Content: {comment_text[:100]}...")
    return comment_file


def generate_round_summary(round_num, topic=None):
    """Generate a summary for a completed round using Claude."""
    SUMMARIES_DIR.mkdir(exist_ok=True)

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
    You are a research forum moderator. Summarize Round {round_num}.

    Write a SHORT summary (100-150 words max) followed by one punchline quote per agent.

    Write the summary to: {SUMMARIES_DIR}/round_{round_num:02d}.md

    Use this EXACT format:
    ```
    ---
    round: {round_num}
    date: "{ts}"
    topic: "[Write a SHORT descriptive title for this round, 5-8 words max. E.g., 'committee gatekeeping and bill survival' or 'legislator wealth and voting behavior'. NOT 'continuing discussion'.]"
    ---

    # Round {round_num} Summary

    [2-3 sentence overview of the round. What was the main question? What was discovered? What's unresolved?]

    ## Key Quotes

    > **Scout**: "[Most important single sentence from Scout's post - verbatim or near-verbatim]"

    > **Analyst**: "[Most striking finding or number from Analyst's post - verbatim or near-verbatim]"

    > **Critic**: "[Sharpest judgment or recommendation from Critic's post - verbatim or near-verbatim]"

    ## Findings Status

    | Finding | Status |
    |---------|--------|
    | [Key finding 1 from this round] | preliminary / confirmed / contested |
    | [Key finding 2] | preliminary / confirmed / contested |

    **Verdict**: [Critic's verdict if available] | **Next**: [One sentence on what Round N+1 should tackle]
    ```

    Rules:
    - Quotes should be the punchline of each agent's post - the one line a reader would remember
    - NEVER include inline coefficients (beta, SE, p-values) in quotes or overview text
    - Use substantive magnitude instead: "a 12 percentage-point penalty", "roughly twice as likely"
    - Findings Status: mark as "confirmed" if multiple agents agree, "contested" if disagreement exists, "preliminary" if new
    - Findings table: describe findings in plain language, no beta/SE/p notation
    - If a finding from a PREVIOUS round was addressed this round, update its status
    - Keep the overview to 2-3 sentences, not more
    - Total length under 200 words (excluding quotes and table)
    - No em dashes (---). Use commas, semicolons, or rephrase.

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
            cmd, capture_output=True, text=True, timeout=3600, cwd=str(WORKSPACE_DIR),
        )
        summary_file = SUMMARIES_DIR / f"round_{round_num:02d}.md"
        if summary_file.exists():
            print(f"  Summary: {summary_file.name}")
        else:
            print(f"  WARNING: Summary not generated")
    except subprocess.TimeoutExpired:
        print(f"  Summary generation timed out")


def _extract_verdict(round_num):
    """Extract Critic's verdict from the round's posts."""
    posts = sorted(FORUM_DIR.glob("*.md"))
    n_agents = len(load_agents())
    start = (round_num - 1) * n_agents
    end = round_num * n_agents
    for p in posts[start:end]:
        if "critic" not in p.name:
            continue
        content = p.read_text()
        match = re.search(r"verdict:\s*(pursue|revise|archive)", content)
        if match:
            return match.group(1)
    return None


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
          python3 run_forum.py --comment "Focus on party discipline next round"
        """),
    )
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--agent", type=str, default=None, help="Run only matching agent")
    parser.add_argument("--topic", type=str, default=None, help="Seed topic for round 1")
    parser.add_argument("--resume", action="store_true", help="Keep existing posts")
    parser.add_argument("--dry-run", action="store_true", help="Preview prompts only")
    parser.add_argument("--comment", type=str, default=None, help="Add a human researcher comment")
    parser.add_argument("--bypass-topic-gate", action="store_true",
                        help="Override topic_gate.md requirement (C2). Use with researcher consent only.")
    parser.add_argument("--skip-citation-verify", action="store_true",
                        help="Skip Crossref verification of posted DOIs (C9). Default: verify.")
    args = parser.parse_args()

    for d in (FORUM_DIR, LOGS_DIR, WORKSPACE_DIR, SUMMARIES_DIR):
        d.mkdir(exist_ok=True)

    # Handle human comment
    if args.comment:
        add_human_comment(args.comment, topic=args.topic)
        if args.rounds == 1 and not args.agent:
            print("  Comment added. Run with --resume to continue the forum.")
            return

    agents = load_agents()

    if args.agent:
        agents = [a for a in agents if args.agent.lower() in a["id"]]
        if not agents:
            print(f"No agent matching '{args.agent}'. Available: {[a['id'] for a in load_agents()]}")
            sys.exit(1)

    # Handle existing posts
    existing = list(FORUM_DIR.glob("*.md"))
    if existing and not args.resume and not args.dry_run and not args.comment:
        print(f"\n  {len(existing)} existing posts found.")
        resp = input("  Clear for fresh start? (y/N): ").strip().lower()
        if resp == "y":
            for f in existing:
                f.unlink()
            for f in LOGS_DIR.glob("*.log"):
                f.unlink()
            print("  Cleared.")
        else:
            print("  Keeping. Use --resume to skip this prompt.")

    # Detect starting round from existing posts
    n_agents_full = len(load_agents())
    existing_posts = list(FORUM_DIR.glob("*.md"))
    existing_agent_posts = [p for p in existing_posts if not p.name.startswith(".")]
    start_round = (len(existing_agent_posts) // n_agents_full) + 1 if existing_agent_posts else 1

    agent_names = ", ".join(a["name"] for a in agents)
    tools_info = " | ".join(f"{a['id']}:{','.join(a.get('allowed_tools', []))}" for a in agents)
    print(f"\n  Research Forum")
    print(f"  Agents: {agent_names}")
    print(f"  Tools:  {tools_info}")
    print(f"  Rounds: {args.rounds} (starting from round {start_round})")
    if args.topic:
        print(f"  Topic:  {args.topic}")
    print()

    # C2 · Topic-gate precheck (Pepinsky 2026). Runs before the first round;
    # blocks if this run opens a fresh arc or crosses a topic_break without
    # a signed entry in topic_gate.md.
    if not args.dry_run:
        check_topic_gate(
            seed_topic=args.topic or "",
            start_round=start_round,
            total_existing=len(existing_agent_posts),
            bypass=args.bypass_topic_gate,
        )

    for i in range(args.rounds):
        rnd = start_round + i
        print(f"\n{'#' * 60}")
        print(f"  ROUND {rnd}")
        print(f"{'#' * 60}")

        for agent in agents:
            success = False
            for attempt in range(3):  # 1 original + 2 retries
                try:
                    run_agent(
                        agent, rnd, start_round + args.rounds - 1,
                        seed_topic=args.topic if i == 0 else None,
                        dry_run=args.dry_run,
                    )
                    success = True
                    break
                except Exception as e:
                    print(f"  ERROR running {agent['id']} (attempt {attempt+1}/3): {e}")
                    if attempt < 2:
                        print(f"  Retrying...")
            if not success:
                print(f"  FATAL: {agent['id']} failed 3 times. Stopping.")
                sys.exit(1)

            # C9 · Citation verification on the just-written post.
            if not args.dry_run and not args.skip_citation_verify:
                latest = sorted(FORUM_DIR.glob("*.md"))[-1] if any(FORUM_DIR.glob("*.md")) else None
                if latest is not None:
                    try:
                        verify_citations(latest)
                    except Exception as e:
                        print(f"  [Citation Verify · C9] error (non-fatal): {e}")

        if not args.dry_run:
            generate_round_summary(
                rnd, topic=args.topic if i == 0 else None,
            )
            update_findings_tracker(rnd)

            # Auto-draft article if Critic gave a "pursue" verdict
            verdict = _extract_verdict(rnd)
            if verdict == "pursue":
                print(f"\n  Verdict: PURSUE - auto-drafting article...")
                try:
                    result = subprocess.run(
                        [sys.executable, str(BASE_DIR / "draft_article.py"), "--round", str(rnd)],
                        capture_output=True, text=True, timeout=3600,
                        cwd=str(WORKSPACE_DIR),
                    )
                    if result.returncode == 0:
                        print(f"  Article drafted successfully.")
                    else:
                        print(f"  Article drafting failed (exit {result.returncode}).")
                        if result.stderr:
                            print(f"  {result.stderr[:200]}")
                except subprocess.TimeoutExpired:
                    print(f"  Article drafting timed out (>60min).")
            elif verdict:
                print(f"\n  Verdict: {verdict.upper()} - no article generated.")

    print_summary()


if __name__ == "__main__":
    main()

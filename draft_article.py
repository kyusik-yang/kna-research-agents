#!/usr/bin/env python3
"""
Article Drafting Pipeline
=========================
Auto-triggered when Critic gives a "pursue" verdict.
Generates a working paper draft from forum findings.

Usage:
    python3 draft_article.py                    # Auto-detect pursue verdicts
    python3 draft_article.py --round 4          # Draft from specific round
    python3 draft_article.py --list             # List pursue verdicts
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
ARTICLES_DIR = BASE_DIR / "articles"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
WORKSPACE_DIR = BASE_DIR / "workspace"

import os
import shutil

CLAUDE = shutil.which("claude") or str(Path.home() / ".local" / "bin" / "claude")


def find_pursue_verdicts():
    """Find all rounds where Critic gave a 'pursue' verdict."""
    findings_file = KNOWLEDGE_DIR / "findings.jsonl"
    if not findings_file.exists():
        return []

    pursues = []
    with open(findings_file) as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("verdict") == "pursue":
                    pursues.append(entry)
            except json.JSONDecodeError:
                pass
    return pursues


def get_round_posts(round_num):
    """Get all posts from a specific round."""
    posts = sorted(FORUM_DIR.glob("*.md"))
    n_agents = 3
    start = (round_num - 1) * n_agents
    end = round_num * n_agents
    round_posts = posts[start:end]
    return [p.read_text() for p in round_posts]


def get_all_forum_context(up_to_round):
    """Get compressed forum context up to a specific round."""
    posts = sorted(FORUM_DIR.glob("*.md"))
    n_agents = 3
    context = []
    for i, p in enumerate(posts):
        rnd = (i // n_agents) + 1
        if rnd > up_to_round:
            break
        content = p.read_text()
        # Last 2 rounds full, older compressed
        if rnd >= up_to_round - 1:
            context.append(f"--- {p.name} ---\n{content}")
        else:
            title = "Untitled"
            for line in content.split("\n"):
                if line.startswith("# ") and "---" not in line:
                    title = line[2:].strip()
                    break
            context.append(f"--- {p.name} (summary) ---\n# {title}\n(See full post in forum/)")
    return "\n\n".join(context)


def draft_article(round_num):
    """Generate a working paper draft from forum findings."""
    ARTICLES_DIR.mkdir(exist_ok=True)
    WORKSPACE_DIR.mkdir(exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d")
    forum_context = get_all_forum_context(round_num)

    # Check for existing articles to avoid duplicates
    existing = list(ARTICLES_DIR.glob(f"*_r{round_num}_*.md"))
    if existing:
        print(f"  Article for round {round_num} already exists: {existing[0].name}")
        return existing[0]

    article_slug = f"{ts}_r{round_num}"

    prompt = textwrap.dedent(f"""\
    You are a research paper drafting agent. Based on the forum discussion below,
    draft a working paper following APSR (American Political Science Review) conventions.

    IMPORTANT CONTEXT:
    - This is an AI-generated experimental draft
    - All data findings come from the KNA database (Korean National Assembly)
    - All literature references come from OpenAlex/Crossref searches by the forum agents

    Write the draft to: {ARTICLES_DIR}/{article_slug}.md

    ## APSR Style Guide (follow strictly)

    **Voice and Tense:**
    - Use "I" for single author, "We" for multiple. Here use "I" (single AI agent).
    - Active voice by default. Passive only for data processing descriptions.
    - Theory/prior work: present tense. Analysis process: past tense. Results: present tense.

    **Introduction:**
    - Start with a theoretical/conceptual problem or empirical puzzle, NOT a news anecdote.
    - NEVER start with "In recent years..." or abstract grand claims.
    - Gap statement: "there exists, to our knowledge, no study..." or "Despite X, there is a lack of..."
    - NEVER say "This is the first paper to..."
    - Contribution woven into narrative (no separate "contributions" paragraph).

    **Citations (APSA Author-Date):**
    - Basic: (Author Year) - NO comma between author and year
    - Page: (Author Year, 45)
    - Two authors: (Dodd and Oppenheimer 1977) - use "and", never "&"
    - Three+ authors: (Corbridge et al. 2004)
    - Multiple: (Bates et al. 1998; Jones 1990) - semicolon, alphabetical
    - Narrative: Cox and McCubbins (2005) argue that...

    **Statistics Reporting:**
    - Body text: beta = -0.028 (SE = 0.003, p < 0.001)
    - Always report effect size alongside significance
    - Stars (*) in tables only, never in body text
    - Sample size (N) stated when sample first appears

    **Causal Language:**
    - OLS/observational: "is associated with", "predicts", "correlates with"
    - DiD/RD/IV: "leads to", "the effect of", "increases/decreases"
    - NEVER: "proves", "demonstrates causality"

    **References (APSA format):**
    - Author last name first, then first name (full, not initials)
    - Elements separated by periods
    - Journal name: italicized, title case
    - Article title: in quotes, title case

    Use this document format:

    ```markdown
    ---
    title: "[Paper title]"
    authors: "KNA Research Agents (AI-generated draft)"
    date: "{ts}"
    source_round: {round_num}
    status: "experimental draft"
    ---

    # [Paper Title]

    **KNA Research Agents** | AI-Generated Working Paper | {ts}
    Source: Forum Round {round_num} | Status: Experimental Draft

    ---

    ## Abstract

    [~150 words. Question, method, key finding, contribution.]

    ## 1. Introduction

    [Theoretical/empirical puzzle. Gap. This paper. Preview of argument and findings.
     Target: ~800 words.]

    ## 2. Literature and Theory

    [Engage with existing work - do not just list, show how this paper extends/challenges.
     Derive expectations or hypotheses. ~1,000 words.]

    ## 3. Data and Method

    [KNA database description. Variables. Sample. Identification strategy.
     Be specific: N, time period, unit of analysis. ~600 words.]

    ## 4. Results

    [Present findings with exact numbers from Analyst's posts.
     Tables with coefficient, SE, significance.
     Substantive interpretation of effect sizes. ~800 words.]

    ## 5. Discussion

    [Connect to theory. Address Critic's limitations.
     What can and cannot be concluded. ~500 words.]

    ## 6. Conclusion

    [Contribution summary. Implications. Future research. ~300 words.]

    ## References

    [APSA format. Example entries:

    Cox, Gary W., and Mathew D. McCubbins. 2005. *Setting the Agenda*.
      New York: Cambridge University Press.

    Volden, Craig, and Alan E. Wiseman. 2014. *Legislative Effectiveness
      in the United States Congress*. New York: Cambridge University Press.

    Lowi, Theodore J. 1964. "American Business, Public Policy, Case-Studies,
      and Political Theory." *World Politics* 16 (4): 677-715.

    ONLY include references that appear in the forum posts.]

    ---

    *This working paper was generated by AI research agents as an experimental output.
    It has not been peer-reviewed or fact-checked.
    Do not cite or use in any academic, policy, or professional context.*
    ```

    RULES:
    - Use ONLY findings, statistics, and references from the forum posts below
    - Do NOT invent data, citations, or results
    - Where Critic identified weaknesses, acknowledge them honestly
    - Target 4,000 words
    - APSR style throughout - this should read like a real political science manuscript

    ## Forum Discussion (Rounds 1-{round_num})

    {forum_context}
    """)

    prompt_file = WORKSPACE_DIR / "_prompt_article.md"
    prompt_file.write_text(prompt)

    print(f"\n  Drafting article from Round {round_num}...")
    print(f"  Output: {ARTICLES_DIR}/{article_slug}.md")

    cmd = [
        CLAUDE, "-p",
        "--allowedTools", "Write",
        "--dangerously-skip-permissions",
        "--system-prompt-file", str(prompt_file),
        "--output-format", "text",
        "Write the working paper draft now.",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600,
            cwd=str(WORKSPACE_DIR),
        )
        article_file = ARTICLES_DIR / f"{article_slug}.md"
        if article_file.exists():
            wc = len(article_file.read_text().split())
            print(f"  Draft complete: {article_file.name} ({wc} words)")

            # Generate PDF via playwright
            try:
                generate_pdf(article_file)
            except Exception as e:
                print(f"  PDF generation skipped: {e}")

            return article_file
        else:
            print(f"  WARNING: Article not generated")
            return None
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT")
        return None


def generate_pdf(md_file):
    """Convert article markdown to PDF via HTML rendering."""
    import markdown

    content = md_file.read_text()
    # Strip frontmatter
    match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
    if match:
        body = match.group(2)
    else:
        body = content

    html_body = markdown.markdown(body, extensions=["tables", "fenced_code"])

    html = f"""\
<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<style>
  body {{ font-family: 'Times New Roman', serif; max-width: 700px; margin: 2cm auto;
         font-size: 12pt; line-height: 1.6; color: #1a1a1a; }}
  h1 {{ font-size: 16pt; text-align: center; margin-bottom: 0.5cm; }}
  h2 {{ font-size: 13pt; margin-top: 1cm; border-bottom: 0.5px solid #ccc; padding-bottom: 3px; }}
  h3 {{ font-size: 12pt; }}
  table {{ border-collapse: collapse; width: 100%; margin: 0.5cm 0; font-size: 10pt; }}
  th, td {{ border: 1px solid #ccc; padding: 4px 8px; text-align: left; }}
  th {{ background: #f5f5f5; }}
  code {{ font-family: monospace; font-size: 10pt; background: #f5f5f5; padding: 1px 4px; }}
  blockquote {{ border-left: 2px solid #ccc; padding-left: 1em; color: #555; }}
  em {{ font-style: italic; }}
  hr {{ border: none; border-top: 0.5px solid #999; margin: 1cm 0; }}
  p {{ margin-bottom: 0.4cm; }}
</style>
</head><body>{html_body}</body></html>"""

    html_file = md_file.with_suffix(".html")
    html_file.write_text(html)

    pdf_file = md_file.with_suffix(".pdf")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{html_file.resolve()}")
            page.pdf(path=str(pdf_file), format="A4", margin={
                "top": "2cm", "bottom": "2cm", "left": "2.5cm", "right": "2.5cm"
            })
            browser.close()
        print(f"  PDF: {pdf_file.name}")
        html_file.unlink()  # clean up temp HTML
    except Exception as e:
        print(f"  PDF skipped: {e}")
        if html_file.exists():
            html_file.unlink()


def main():
    parser = argparse.ArgumentParser(description="Article Drafting Pipeline")
    parser.add_argument("--round", type=int, help="Draft from specific round")
    parser.add_argument("--list", action="store_true", help="List pursue verdicts")
    args = parser.parse_args()

    if args.list:
        pursues = find_pursue_verdicts()
        if not pursues:
            print("No 'pursue' verdicts found.")
        for p in pursues:
            print(f"  Round {p['round']}: {p['finding'][:80]}... [{p['verdict']}]")
        return

    if args.round:
        draft_article(args.round)
        return

    # Auto-detect: find pursue verdicts without existing articles
    pursues = find_pursue_verdicts()
    if not pursues:
        print("No 'pursue' verdicts found. Run more forum rounds.")
        return

    for p in pursues:
        rnd = p["round"]
        existing = list(ARTICLES_DIR.glob(f"*_r{rnd}_*.md"))
        if not existing:
            print(f"  Found pursue verdict for Round {rnd}")
            draft_article(rnd)
        else:
            print(f"  Round {rnd}: article already exists ({existing[0].name})")


if __name__ == "__main__":
    main()

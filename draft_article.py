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
SUMMARIES_DIR = BASE_DIR / "summaries"

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
    """Get compressed forum context. Full text for last 2 rounds, summaries for older."""
    posts = sorted(FORUM_DIR.glob("*.md"))
    n_agents = 3
    context = []

    # Include round summaries for older rounds (much shorter than full posts)
    for sf in sorted(SUMMARIES_DIR.glob("round_*.md")):
        rnd_num = int(re.search(r"(\d+)", sf.stem).group(1))
        if rnd_num <= up_to_round - 2:
            context.append(f"--- Round {rnd_num} Summary ---\n{sf.read_text()}")

    # Full text for last 2 rounds only
    for i, p in enumerate(posts):
        rnd = (i // n_agents) + 1
        if rnd > up_to_round:
            break
        if rnd >= up_to_round - 1:
            context.append(f"--- {p.name} ---\n{p.read_text()}")

    return "\n\n".join(context)


def draft_article(round_num):
    """Generate a working paper draft from forum findings."""
    ARTICLES_DIR.mkdir(exist_ok=True)
    WORKSPACE_DIR.mkdir(exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d")
    forum_context = get_all_forum_context(round_num)

    # Check for existing articles to avoid duplicates
    existing = list(ARTICLES_DIR.glob(f"*_r{round_num}.tex")) + list(ARTICLES_DIR.glob(f"*_r{round_num}.md"))
    existing = [e for e in existing if "template" not in e.name and "content" not in e.name]
    if existing:
        print(f"  Article for round {round_num} already exists: {existing[0].name}")
        return existing[0]

    article_slug = f"{ts}_r{round_num}"
    tex_file = ARTICLES_DIR / f"{article_slug}.tex"
    content_file = ARTICLES_DIR / f"{article_slug}_content.tex"

    prompt = textwrap.dedent(f"""\
    You are a research paper drafting agent. Based on the forum discussion below,
    draft a working paper as a LaTeX document body following APSR conventions
    and the academic writing style guide below.

    IMPORTANT: Write ONLY the LaTeX body content (from \\title to the bibliography).
    Do NOT include \\documentclass, \\usepackage, or \\begin{{document}}.
    The template handles those.

    Write the content to: {content_file}

    ## ACADEMIC WRITING STYLE GUIDE (mandatory, enforce strictly)

    **Anti-AI-Tell Rules (CRITICAL):**
    Inline coefficient reporting ($\\beta = ..., p < ...$) is the #1 marker of AI-generated prose.
    - Introduction: NEVER inline coefficients. Substantive framing only.
    - Literature Review: NEVER. Summarize findings narratively.
    - Results: MAX 1-2 key estimates, ALWAYS with table reference. E.g., "The effect is
      substantively large and robust across specifications (Table 2)."
    - Discussion: NEVER. Describe substantive magnitude and direction, reference tables.
    - Conclusion: NEVER. High-level takeaway only.
    FORBIDDEN: Serial listing of coefficients. Repeating beta/SE/p triplets. "($\\beta = 1.23$, $t = 36.9$)".
    PREFERRED: "a 12 percentage-point increase", "roughly twice as likely", "explains about 3\\% of the variation".

    **Formatting:**
    - No em dashes or double hyphens. Use a comma, semicolon, colon, or rephrase.
    - No contractions (don't -> do not, it's -> it is).
    - No slashes (and/or -> "and" or "or").
    - No rhetorical questions. Use declarative statements.
    - Numbers: spell out zero through nine, numerals for 10 and above.
    - "Who" for people, not "that". Hyphenate compound modifiers before nouns.

    **Hedging and Caution:**
    - Never state absolute certainty. Use "may," "could," "suggests," "appears to."
    - "These findings suggest that..." NOT "These findings prove that..."
    - "A possible explanation for this might be that..."

    **Section Structure:**
    - Introduction: CARS model (establish territory, identify niche, occupy niche). No news anecdotes.
    - Literature: Engage, compare, synthesize. "Smith (2004) found..." "Unlike Smith, Jones argues..."
    - Results: Location statement (Table X shows) + highlighting (significant data). Reserve commentary for Discussion.
    - Discussion: Result -> comparison with prior work -> explanation -> implications. Tentative language.
    - Conclusion: Summarize, significance, limitations, future research.

    **Tables and Figures:**
    - Number each in own sequence. Refer to EVERY table/figure in text before it appears.
    - NEVER "Table ??" or broken references. Use \\label and \\ref.

    ## OUTPUT FORMAT (LaTeX body only)

    Write this exact structure:

    \\title{{[Paper Title]}}
    \\author{{KNA Research Agents (AI-generated)}}
    \\affil{{Experimental Output --- kna-research-agents.com}}
    \\date{{\\today}}
    \\maketitle
    \\thispagestyle{{empty}}

    \\begin{{abstract}}
    \\noindent [150 words. Question, method, key finding, contribution.]
    \\end{{abstract}}

    \\bigskip
    \\noindent\\textbf{{Keywords:}} [5 keywords, comma-separated. MANDATORY.]

    \\bigskip
    \\setcounter{{page}}{{0}}
    \\clearpage

    \\section{{Introduction}}
    [~1,500 words. Theoretical puzzle, gap, this paper, preview.]

    \\section{{Literature and Theory}}
    [~2,000 words. Engage with work, derive expectations/hypotheses.]

    \\section{{Data and Method}}
    [~1,500 words. KNA database, variables, identification.]

    \\subsection{{Data}}
    [Describe KNA: N bills, time period, unit of analysis. Include Table: descriptive statistics.]

    \\subsection{{Identification Strategy}}
    [Formal equation + variable definitions. Discuss threats to inference.]

    \\section{{Results}}
    [~2,500 words. MUST include at least 2 regression tables with coefficients, SEs, stars, N, R2.
     Present main results, robustness checks, heterogeneity analysis.
     Each table must be discussed substantively in the text.]

    \\section{{Discussion}}
    [~1,500 words. Theory connection, compare with prior work, limitations.]

    \\section{{Conclusion}}
    [~500 words. Contribution, implications, future research.]

    \\bigskip
    \\noindent\\textit{{This working paper was generated by AI research agents as an
    experimental output. It has not been peer-reviewed or fact-checked.
    Do not cite or use in any academic, policy, or professional context.}}

    ## APSR STYLE (strict)

    **Voice**: Use "I" throughout. Active voice. Theory=present, analysis=past, results=present.
    **Introduction**: Start with theoretical puzzle. NEVER "In recent years..." NEVER "This is the first paper to..."
    **Gap**: "there exists, to our knowledge, no study..." or "Despite X, there is a lack of..."

    **Citations (natbib commands):**
    - Narrative: \\citet{{cox2005}} = Cox and McCubbins (2005)
    - Parenthetical: \\citep{{lowi1964}} = (Lowi 1964)
    - Multiple: \\citep{{bates1998, jones1990}} = (Bates et al. 1998; Jones 1990)
    - With page: \\citep[45]{{author2005}} = (Author 2005, 45)
    - Use natbib commands for all citations:
      Narrative: \\citet{{cox2005}} -> Cox and McCubbins (2005)
      Parenthetical: \\citep{{lowi1964}} -> (Lowi 1964)
      Multiple: \\citep{{bates1998, jones1990}} -> (Bates et al. 1998; Jones 1990)
      With page: \\citet[45]{{author2005}} -> Author (2005, 45)
    - Use consistent, short citation keys: authorYEAR (e.g., cox2005, lowi1964)
    - At the end of the paper, write:
      \\bibliographystyle{{apsr}}
      \\bibliography{{references_r{round_num}}}
    - ALSO write a separate .bib file to: {ARTICLES_DIR}/references_r{round_num}.bib
      with ALL cited references in BibTeX format. Example entry:
      @article{{lowi1964,
        author = {{Lowi, Theodore J.}},
        title = {{American Business, Public Policy, Case-Studies, and Political Theory}},
        journal = {{World Politics}},
        year = {{1964}},
        volume = {{16}},
        number = {{4}},
        pages = {{677--715}}
      }}
    - EVERY \\citet/\\citep key MUST have a matching entry in the .bib file.

    **Equations (amsmath):**
    Inline: $\\beta_1$, $p < 0.001$
    Display:
    \\begin{{equation}}
    \\Pr(\\text{{Decision}}_i = 1) = \\Lambda(\\beta_1 \\text{{Minsaeng}}_i + \\mathbf{{X}}_i \\boldsymbol{{\\gamma}} + \\delta_c + \\epsilon_i)
    \\label{{eq:main}}
    \\end{{equation}}
    Reference: Equation~\\ref{{eq:main}}

    **Tables (booktabs, MANDATORY at least 2):**
    \\begin{{table}}[H]
    \\centering
    \\caption{{Descriptive Statistics}}
    \\label{{tab:desc}}
    \\begin{{tabular}}{{lcccc}}
    \\toprule
    Variable & N & Mean & SD & Range \\\\
    \\midrule
    ... & ... & ... & ... & ... \\\\
    \\bottomrule
    \\end{{tabular}}
    \\end{{table}}

    Regression table:
    \\begin{{table}}[H]
    \\centering
    \\caption{{Main Results: Committee Processing of Bills}}
    \\label{{tab:main}}
    \\begin{{tabular}}{{lccc}}
    \\toprule
    & (1) & (2) & (3) \\\\
    & Baseline & Controls & FE \\\\
    \\midrule
    Minsaeng & $-0.093^{{***}}$ & $-0.085^{{***}}$ & $-0.078^{{***}}$ \\\\
    & (0.008) & (0.009) & (0.010) \\\\
    ... \\\\
    \\midrule
    N & 50,003 & 50,003 & 50,003 \\\\
    Committee FE & No & No & Yes \\\\
    Pseudo $R^2$ & 0.04 & 0.08 & 0.12 \\\\
    \\bottomrule
    \\multicolumn{{4}}{{l}}{{\\footnotesize $^*p<0.10$, $^{{**}}p<0.05$, $^{{***}}p<0.01$. SE in parentheses.}} \\\\
    \\end{{tabular}}
    \\end{{table}}

    **Figures (MANDATORY, STRICT 1:1 PAIRING RULE):**

    CRITICAL RULE: Every \\begin{{figure}} environment MUST be immediately preceded
    by a \\begin{{verbatim}} block containing runnable R code. NO EXCEPTIONS.
    The pipeline auto-executes verbatim R code and replaces the \\fbox placeholder
    with the generated PDF. Figures without R code will render as ugly placeholder
    boxes in the final PDF.

    - Include 2-4 figures. Each one MUST have its own verbatim R code block.
    - If you cannot write R code for a figure, do NOT include that figure.
    - The verbatim block must appear IMMEDIATELY before its \\begin{{figure}} float.
    - Each R script must be self-contained: load libraries, read data, plot, ggsave().

    Data path for R: /Users/kyusik/kna/data/processed/
    Available: member_info_17_22.parquet, master_bills_{{17-22}}.parquet
    Use arrow::read_parquet() to load. Key columns: mona_cd, assembly (=age in bills),
    gender (남/여), election_type (비례대표/지역구), reelection (초선/재선/3선/...),
    rst_mona_cd (sponsor), ppsr_kind (의원=member bill), passed (0/1).

    R packages: ggplot2, dplyr, tidyr, arrow, fixest
    Style: theme_bw(base_size = 11), Okabe-Ito palette, PDF output

    TEMPLATE (repeat for EACH figure):
    \\begin{{verbatim}}
    # Figure N: [description]
    library(arrow); library(dplyr); library(ggplot2)
    DATA <- "/Users/kyusik/kna/data/processed"
    members <- read_parquet(file.path(DATA, "member_info_17_22.parquet"))
    bills <- bind_rows(lapply(17:22, function(a) {{
      f <- file.path(DATA, sprintf("master_bills_%d.parquet", a))
      if (file.exists(f)) read_parquet(f) else NULL
    }})) |> filter(ppsr_kind == "의원")
    # [analysis code here]
    # [ggplot code here]
    ggsave("fig_N.pdf", width = 7, height = 4.5)
    \\end{{verbatim}}

    \\begin{{figure}}[H]
    \\centering
    \\fbox{{\\parbox{{0.85\\textwidth}}{{[Brief description of what the R code above produces.]}}}}
    \\caption{{Your caption here}}
    \\label{{fig:something}}
    \\end{{figure}}

    Best figure types:
    - Line plot: trends across assemblies (geom_line + geom_point)
    - Coefficient plot: point estimates with 95\\% CI (geom_pointrange + geom_vline)
    - Stacked/grouped bar: composition by categories (geom_col + facet_wrap)
    - Slopegraph: within-person changes (geom_line per individual)

    Do NOT use TikZ. Do NOT hardcode paths in ggsave (just "fig_N.pdf").

    **Statistics in text:**
    Refer to tables and figures. Avoid inline coefficients except 1-2 key estimates in Results.

    **Causal language:**
    OLS: "is associated with". DiD/RD: "the effect of". NEVER "proves".

    **References section:**
    Since no .bib file, write references manually at the end:
    \\section*{{References}}
    \\begin{{description}}
    \\item Cox, Gary W., and Mathew D. McCubbins. 2005. \\textit{{Setting the Agenda}}. New York: Cambridge University Press.
    \\item Lowi, Theodore J. 1964. ``American Business, Public Policy, Case-Studies, and Political Theory.'' \\textit{{World Politics}} 16 (4): 677--715.
    \\end{{description}}
    ONLY include references from the forum posts.

    RULES:
    - ONLY use findings/statistics/references from the forum posts below
    - Do NOT invent data or citations
    - Acknowledge Critic's limitations honestly
    - Target 8,000-10,000 words
    - APSR style throughout

    **KNA Data Available (check before writing Data section):**
    - master_bills_{{17-22}}.parquet: bill lifecycle (42+ columns)
    - roll_calls_all.parquet: 2.4M member-level votes
    - dw_ideal_points_20_22.csv: DW-NOMINATE ideal points
    - committee_meetings_{{17-22}}.parquet: committee meeting records
    - bill_texts_linked.parquet: 60K propose-reason texts
    - cosponsorship_edges.parquet: cosponsorship network
    - members_{{17-22}}.parquet: member metadata (party, district, committee, sex, birth_date, election_type, reelection)
    - assets data: db.assets(assembly=22) - 2,928 member-year wealth observations
    - kr-hearings-data: 9.9M speeches + 7.4M Q&A dyads (separate download)
    Data path: /Users/kyusik/kna/data/processed/
    R code for figures should use arrow::read_parquet() to load this data directly.
    - Valid LaTeX that compiles with xelatex

    ## Forum Discussion (Rounds 1-{round_num})

    {forum_context}
    """)

    prompt_file = WORKSPACE_DIR / "_prompt_article.md"
    prompt_file.write_text(prompt)

    print(f"\n  Drafting article from Round {round_num}...")
    print(f"  Output: {tex_file}")

    cmd = [
        CLAUDE, "-p",
        "--allowedTools", "Write",
        "--dangerously-skip-permissions",
        "--system-prompt-file", str(prompt_file),
        "--output-format", "text",
        f"Write the working paper draft now. Write TWO files: (1) the LaTeX content to {content_file} and (2) the BibTeX references to {ARTICLES_DIR}/references_r{round_num}.bib",
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=3600,
            cwd=str(WORKSPACE_DIR),
        )
        if content_file.exists():
            content = content_file.read_text()
            wc = len(content.split())
            print(f"  Content generated: {wc} words")

            # Merge with template
            template = (ARTICLES_DIR / "template.tex").read_text()
            # Extract title for markdown version
            import re as _re
            title_match = _re.search(r'\\title\{(.+?)\}', content)
            title = title_match.group(1) if title_match else "Untitled"

            full_tex = template.replace("%%TITLE%%", "").replace("%%CONTENT%%", content)
            tex_file.write_text(full_tex)
            print(f"  LaTeX: {tex_file.name}")

            # Also save a markdown version for the website
            md_file = ARTICLES_DIR / f"{article_slug}.md"
            md_file.write_text(
                f"---\ntitle: \"{title}\"\nauthors: \"KNA Research Agents\"\n"
                f"date: \"{ts}\"\nsource_round: {round_num}\nstatus: \"experimental draft\"\n"
                f"tex_file: \"{tex_file.name}\"\n---\n\n"
                f"# {title}\n\n"
                f"**KNA Research Agents** | AI-Generated Working Paper | {ts}\n\n"
                f"Source: Forum Round {round_num} | Status: Experimental Draft\n\n"
                f"[View LaTeX source]({tex_file.name}) | "
                f"[Download PDF]({article_slug}.pdf)\n\n---\n\n"
                f"*See PDF for full paper with equations, tables, and references.*\n"
            )

            # Execute R figures
            try:
                execute_r_figures(tex_file)
            except Exception as e:
                print(f"  R figure execution failed: {e}")

            # Check for orphan placeholders and attempt repair
            try:
                repair_orphan_figures(tex_file, round_num)
            except Exception as e:
                print(f"  Orphan figure repair failed: {e}")

            # Compile with xelatex
            try:
                compile_tex(tex_file)
            except Exception as e:
                print(f"  PDF compilation failed: {e}")

            # Clean up content file
            content_file.unlink()

            # Step 2: Review and revise
            print(f"\n  Running paper reviewer + auto-revision...")
            review_and_revise(tex_file)

            return tex_file
        else:
            print(f"  WARNING: Article not generated")
            return None
    except subprocess.TimeoutExpired:
        print(f"  TIMEOUT")
        return None


def repair_orphan_figures(tex_file, round_num):
    """Detect fbox placeholders without R code and ask Claude to generate R scripts."""
    import re as _re

    content = tex_file.read_text()
    # Per-article namespace: figures/<article_stem>/fig_N.pdf prevents cross-article
    # overwrites when multiple papers are drafted from the same articles/ dir.
    stem = tex_file.stem
    fig_dir = tex_file.parent / "figures" / stem
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Find orphan fbox placeholders (not yet replaced by includegraphics)
    orphans = list(_re.finditer(
        r'\\fbox\{\\parbox\{.*?\}\{(.*?)\}\}',
        content, _re.DOTALL
    ))

    if not orphans:
        return

    print(f"\n  Found {len(orphans)} orphan figure placeholder(s). Generating R code...")

    # Per-article namespace: start numbering at 1 each time
    existing_figs = sorted(fig_dir.glob("fig_*.pdf"))
    next_num = len(existing_figs) + 1

    for i, match in enumerate(orphans):
        fig_num = next_num + i
        description = match.group(1).strip()
        pdf_name = f"fig_{fig_num}.pdf"
        pdf_path = fig_dir / pdf_name
        r_file = fig_dir / f"fig_{fig_num}.R"

        prompt = textwrap.dedent(f"""\
        Write a SINGLE self-contained R script that produces the figure described below.
        The script must be complete and runnable with Rscript.

        Description: {description[:500]}

        Requirements:
        - Load data from: /Users/kyusik/kna/data/processed/
        - Available files: member_info_17_22.parquet, master_bills_{{17-22}}.parquet
        - Key columns: mona_cd, assembly (in members) = age (in bills), gender (남/여),
          election_type (비례대표/지역구), reelection (초선/재선/3선/...),
          rst_mona_cd (sponsor in bills), ppsr_kind (의원 = member bill), passed (0/1)
        - Use: library(arrow), library(dplyr), library(ggplot2)
        - Style: theme_bw(base_size = 11), Okabe-Ito colorblind palette
        - Save with: ggsave("{pdf_path}", width = 7, height = 4.5)
        - Filter bills: ppsr_kind == "의원"
        - Join members to bills: by rst_mona_cd = mona_cd AND age = assembly

        Write ONLY the R code to: {r_file}
        No explanation, no markdown, just the .R file.
        """)

        prompt_file = WORKSPACE_DIR / f"_prompt_fig_{fig_num}.md"
        prompt_file.write_text(prompt)

        cmd = [
            CLAUDE, "-p",
            "--allowedTools", "Write",
            "--dangerously-skip-permissions",
            "--system-prompt-file", str(prompt_file),
            "--output-format", "text",
            "Write the R script now.",
        ]

        print(f"  Generating R code for orphan figure {fig_num}...")
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300,
                cwd=str(WORKSPACE_DIR),
            )
        except subprocess.TimeoutExpired:
            print(f"  Timeout generating R code for figure {fig_num}")
            continue

        if not r_file.exists():
            print(f"  WARNING: R script not generated for figure {fig_num}")
            continue

        # Execute the R script
        print(f"  Executing {r_file.name}...")
        try:
            r_result = subprocess.run(
                ["Rscript", str(r_file)],
                capture_output=True, text=True, timeout=120,
                cwd=str(fig_dir),
            )
            if pdf_path.exists() and pdf_path.stat().st_size > 1000:
                print(f"  Figure generated: {pdf_name} ({pdf_path.stat().st_size // 1024} KB)")

                # Replace this orphan fbox with includegraphics (per-article path)
                incl = f'\\includegraphics[width=\\textwidth]{{figures/{stem}/{pdf_name}}}'
                content = content.replace(match.group(0), incl, 1)
            else:
                print(f"  R execution failed or empty output: {r_result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print(f"  R script timed out for figure {fig_num}")
        except Exception as e:
            print(f"  R execution error for figure {fig_num}: {e}")

    # Write updated content
    tex_file.write_text(content)
    remaining = len(_re.findall(r'\\fbox\{\\parbox\{', content))
    if remaining:
        print(f"  WARNING: {remaining} placeholder(s) still remain")
    else:
        print(f"  All orphan figures resolved")


def execute_r_figures(tex_file):
    """Extract R code from LaTeX, execute it, replace placeholders with includegraphics."""
    import re as _re

    content = tex_file.read_text()
    # Per-article namespace (same fix as repair_orphan_figures)
    stem = tex_file.stem
    fig_dir = tex_file.parent / "figures" / stem
    fig_dir.mkdir(parents=True, exist_ok=True)

    # Find R code blocks in verbatim environments
    # Pattern: \begin{verbatim} ... R code with ggsave ... \end{verbatim}
    r_blocks = _re.findall(
        r'\\begin\{verbatim\}(.*?)\\end\{verbatim\}',
        content, _re.DOTALL
    )

    if not r_blocks:
        print(f"  No R code blocks found")
        return

    fig_count = 0
    for i, block in enumerate(r_blocks):
        # Check if it contains R-like code (library, ggplot, ggsave)
        if not any(kw in block for kw in ["library(", "ggplot(", "ggsave(", "plot("]):
            continue

        fig_count += 1
        r_file = fig_dir / f"fig_{fig_count}.R"
        pdf_name = f"fig_{fig_count}.pdf"
        pdf_path = fig_dir / pdf_name

        # Modify ggsave to output to our fig directory
        r_code = block.strip()
        backref = r'\2'
        r_code = _re.sub(
            r'ggsave\(["\']([^"\']+)["\'](.*?)\)',
            f'ggsave("{pdf_path}"' + backref + ')',
            r_code
        )

        # Add KNA data path
        r_code = f'# Auto-generated figure for article\n' \
                 f'Sys.setenv(KBL_DATA = "{Path.home()}/kna/data/processed")\n' \
                 f'{r_code}\n'

        r_file.write_text(r_code)
        print(f"  Executing R figure {fig_count}: {r_file.name}")

        try:
            result = subprocess.run(
                ["Rscript", str(r_file)],
                capture_output=True, text=True, timeout=120,
                cwd=str(fig_dir),
            )
            if pdf_path.exists():
                print(f"  Figure generated: {pdf_name} ({pdf_path.stat().st_size // 1024} KB)")

                # Replace the verbatim block + fbox placeholder with includegraphics
                # Find the verbatim block and the following fbox/figure placeholder
                old_verbatim = f'\\begin{{verbatim}}{block}\\end{{verbatim}}'

                # Replace verbatim with a comment (keep the code reference)
                content = content.replace(
                    old_verbatim,
                    f'% R code for Figure {fig_count} executed automatically (see figures/fig_{fig_count}.R)'
                )

                # Replace fbox placeholder with actual includegraphics
                # Use lambda to avoid regex escape issues with \includegraphics
                incl = f'\\includegraphics[width=\\textwidth]{{figures/{stem}/{pdf_name}}}'
                content = _re.sub(
                    r'\\fbox\{\\parbox\{.*?\}\{.*?\}\}',
                    lambda m: incl,
                    content,
                    count=1,
                    flags=_re.DOTALL
                )
            else:
                print(f"  R execution failed: {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print(f"  R script timed out")
        except Exception as e:
            print(f"  R execution error: {e}")

    if fig_count > 0:
        tex_file.write_text(content)
        print(f"  {fig_count} figures processed")


def compile_tex(tex_file):
    """Compile LaTeX to PDF using xelatex."""
    import subprocess as _sp

    tex_dir = tex_file.parent
    TINYTEX = Path.home() / "Library/TinyTeX/bin/universal-darwin"
    print(f"  Compiling {tex_file.name} (xelatex + bibtex)...")

    # Pass 1: xelatex
    _sp.run(
        [str(TINYTEX / "xelatex"), "-interaction=nonstopmode", tex_file.name],
        capture_output=True, text=True, timeout=120, cwd=str(tex_dir),
    )

    # Pass 2: bibtex (for natbib references)
    _sp.run(
        [str(TINYTEX / "bibtex"), tex_file.stem],
        capture_output=True, text=True, timeout=60, cwd=str(tex_dir),
    )

    # Pass 3-4: xelatex twice more for cross-refs
    for i in range(2):
        result = _sp.run(
            [str(TINYTEX / "xelatex"), "-interaction=nonstopmode", tex_file.name],
            capture_output=True, text=True, timeout=120, cwd=str(tex_dir),
        )
        if result.returncode != 0 and i == 0:
            # First pass may fail on refs, try once more
            continue
        elif result.returncode != 0 and i == 1:
            print(f"  xelatex error (pass {i+1})")
            # Save error log
            log = tex_dir / tex_file.stem
            err_lines = result.stdout.split("\n")
            errors = [l for l in err_lines if l.startswith("!") or "Error" in l]
            for e in errors[:5]:
                print(f"    {e}")

    pdf_file = tex_file.with_suffix(".pdf")
    if pdf_file.exists():
        print(f"  PDF: {pdf_file.name} ({pdf_file.stat().st_size // 1024} KB)")
        # Clean aux files
        for ext in [".aux", ".log", ".out", ".toc", ".bbl", ".blg"]:
            f = tex_file.with_suffix(ext)
            if f.exists():
                f.unlink()
    else:
        print(f"  WARNING: PDF not generated")


def review_and_revise(tex_file):
    """Run paper-reviewer on the article and auto-revise."""
    WORKSPACE_DIR.mkdir(exist_ok=True)

    content = tex_file.read_text()

    # Step 1: Review
    review_prompt = textwrap.dedent(f"""\
    You are a rigorous academic paper reviewer for a top political science journal (APSR/AJPS).
    Review the LaTeX paper below and produce a structured review.

    Evaluate on these dimensions:
    1. **AI-Tell Detection**: Are there inline coefficients in Intro/Discussion/Conclusion?
       Serial beta/SE/p listings? Generic AI prose patterns?
    2. **Writing Quality**: Contractions? Slashes? Rhetorical questions? Em dashes?
       Vague "this" without referent? Excessive passive voice?
    3. **Structure**: Does Introduction follow CARS model? Does Discussion interpret (not re-list)?
       Are all tables/figures referenced in text? Any broken \\ref links?
    4. **Equations/Tables**: Are equations properly formatted? Do tables have booktabs
       (toprule/midrule/bottomrule)? Are stars footnoted?
    5. **Citations**: APSA author-date format? No numbered citations?
    6. **Hedging**: Are claims appropriately hedged? Any overclaiming?
    7. **LaTeX Errors**: Any syntax that would not compile? Missing braces, unmatched environments?

    Write your review to: {WORKSPACE_DIR}/_review.md

    Format:
    ## Review Summary
    [2-3 sentences overall assessment]

    ## Critical Issues (must fix)
    1. [issue + location + fix]
    2. ...

    ## Minor Issues
    1. [issue + fix]
    2. ...

    ## LaTeX Compilation Concerns
    1. [issue]

    ## Paper:
    {content[:30000]}
    """)

    review_file = WORKSPACE_DIR / "_prompt_review.md"
    review_file.write_text(review_prompt)

    print(f"  Step 1: Reviewing article...")
    cmd = [
        CLAUDE, "-p",
        "--allowedTools", "Write",
        "--dangerously-skip-permissions",
        "--system-prompt-file", str(review_file),
        "--output-format", "text",
        "Review the paper now. Be strict.",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, cwd=str(WORKSPACE_DIR))
    except subprocess.TimeoutExpired:
        print(f"  Review timed out")
        return

    review_output = WORKSPACE_DIR / "_review.md"
    if not review_output.exists():
        review_output.write_text(result.stdout[:5000])

    review_text = review_output.read_text() if review_output.exists() else result.stdout[:5000]
    print(f"  Review complete ({len(review_text)} chars)")

    # Step 2: Revise based on review
    revise_prompt = textwrap.dedent(f"""\
    You are revising a LaTeX paper based on reviewer feedback.
    Apply ALL critical and minor fixes from the review below.

    IMPORTANT RULES:
    - Output the COMPLETE revised LaTeX body (everything between \\begin{{document}} and \\end{{document}})
    - Do NOT include \\documentclass or preamble
    - Fix every issue the reviewer identified
    - Preserve all content, equations, tables, and references
    - If the reviewer found inline coefficients in wrong sections, rewrite those sentences
      to use substantive magnitude + table references instead

    Write the revised content to: {tex_file.stem}_revised_content.tex
    (in the same directory as the original: {ARTICLES_DIR}/)

    ## Reviewer Feedback:
    {review_text}

    ## Original Paper:
    {content}
    """)

    revise_file = WORKSPACE_DIR / "_prompt_revise.md"
    revise_file.write_text(revise_prompt)

    print(f"  Step 2: Revising article based on review...")
    cmd = [
        CLAUDE, "-p",
        "--allowedTools", "Write",
        "--dangerously-skip-permissions",
        "--system-prompt-file", str(revise_file),
        "--output-format", "text",
        "Revise the paper now. Fix all issues.",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600, cwd=str(WORKSPACE_DIR))
    except subprocess.TimeoutExpired:
        print(f"  Revision timed out")
        return

    revised_content_file = ARTICLES_DIR / f"{tex_file.stem}_revised_content.tex"
    if revised_content_file.exists():
        # Merge revised content with template
        template = (ARTICLES_DIR / "template.tex").read_text()
        revised_content = revised_content_file.read_text()

        # Extract content between \begin{document} and \end{document} if present
        m = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', revised_content, re.DOTALL)
        if m:
            revised_content = m.group(1).strip()

        full_tex = template.replace("%%CONTENT%%", revised_content)
        tex_file.write_text(full_tex)
        revised_content_file.unlink()

        # Recompile
        try:
            compile_tex(tex_file)
        except Exception as e:
            print(f"  Recompilation failed: {e}")

        print(f"  Revision complete. Article updated.")
    else:
        print(f"  WARNING: Revised content not generated")


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

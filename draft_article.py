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
    [~1000 words. Theoretical puzzle, gap, this paper, preview.]

    \\section{{Literature and Theory}}
    [~1200 words. Engage with work, derive expectations.]

    \\section{{Data and Method}}
    [~800 words. KNA database, variables, identification.]

    \\subsection{{Data}}
    [Describe KNA: N bills, time period, unit of analysis.]

    \\subsection{{Identification Strategy}}
    [Formal equation + variable definitions.]

    \\section{{Results}}
    [~1000 words. Tables + interpretation.]

    \\section{{Discussion}}
    [~600 words. Theory connection, limitations.]

    \\section{{Conclusion}}
    [~400 words. Contribution, implications.]

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
    - CRITICAL: There is NO .bib file. Do NOT use \\citet or \\citep commands.
      Write all citations as plain text:
      WRONG: \\citet{{cox2005}} -> COMPILE ERROR
      RIGHT: Cox and McCubbins (2005)
      WRONG: \\citep{{lowi1964}} -> COMPILE ERROR
      RIGHT: (Lowi 1964)
    - ALSO CRITICAL: You MUST include a \\section*{{References}} at the end
      with full bibliography entries. Without this the paper is incomplete.

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

    **Figure (MANDATORY at least 1):**
    Include at least one professional-quality figure. Generate the figure using R code
    that runs independently. Write the R script inside the article as a code block,
    and include a \\includegraphics placeholder for the output PDF.

    Best figure types:
    - Coefficient plot: point estimates with 95\\% CI bars (ggplot2 + geom_pointrange)
    - Bar chart: processing rates by policy domain (ggplot2 + theme_bw)
    - Event study: processing rates over time (ggplot2 + geom_line + geom_ribbon)

    R packages to use: ggplot2, dplyr, tidyr, fixest (for model objects), modelsummary
    Style: theme_bw(), no gray background, colorblind-safe palette, PDF output

    Example R code block in the paper:
    \\begin{{verbatim}}
    # Figure 1: Coefficient plot of minsaeng processing penalty
    library(ggplot2)
    coefs <- data.frame(
      domain = c("Labor", "Care", "Welfare", "SmallBiz"),
      estimate = c(-15.7, -0.3, -8.2, -3.1),
      ci_low = c(-20.1, -5.8, -13.0, -7.9),
      ci_high = c(-11.3, 5.2, -3.4, 1.7)
    )
    ggplot(coefs, aes(x = estimate, y = reorder(domain, estimate))) +
      geom_pointrange(aes(xmin = ci_low, xmax = ci_high)) +
      geom_vline(xintercept = 0, linetype = "dashed", color = "gray50") +
      labs(x = "AME (percentage points)", y = NULL,
           caption = "Note: 95% confidence intervals shown.") +
      theme_bw(base_size = 11)
    ggsave("fig_coef_plot.pdf", width = 7, height = 4)
    \\end{{verbatim}}

    Then IMMEDIATELY after the verbatim block, add the figure float with a placeholder:
    \\begin{{figure}}[H]
    \\centering
    \\fbox{{\\parbox{{0.85\\textwidth}}{{[Figure generated by R script above. Brief description.]}}}}
    \\caption{{Your caption here}}
    \\label{{fig:coef}}
    \\end{{figure}}

    IMPORTANT: The R code in \\begin{{verbatim}} will be automatically executed by the pipeline.
    The \\fbox placeholder will be replaced with the actual figure.
    Make sure ggsave() outputs a PDF file. The pipeline handles the rest.

    Do NOT use TikZ for figures.
    Do NOT hardcode file paths in ggsave - just use a simple filename like "fig_coef_plot.pdf".

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
    - Target 5,000-6,000 words
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
        "Write the working paper draft now.",
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


def execute_r_figures(tex_file):
    """Extract R code from LaTeX, execute it, replace placeholders with includegraphics."""
    import re as _re

    content = tex_file.read_text()
    fig_dir = tex_file.parent / "figures"
    fig_dir.mkdir(exist_ok=True)

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
        r_code = _re.sub(
            r'ggsave\(["\']([^"\']+)["\'](.*?)\)',
            f'ggsave("{pdf_path}"{r"\\2"})',
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
                content = _re.sub(
                    r'\\fbox\{\\parbox\{[^}]*\}\{[^}]*\[Figure[^]]*\][^}]*\}\}',
                    f'\\includegraphics[width=\\textwidth]{{figures/{pdf_name}}}',
                    content,
                    count=1
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
    print(f"  Compiling {tex_file.name} with xelatex...")

    # Run xelatex twice (for references/cross-refs)
    for i in range(3):  # 3 passes for cross-refs + error recovery
        result = _sp.run(
            [str(Path.home() / "Library/TinyTeX/bin/universal-darwin/xelatex"),
             "-interaction=nonstopmode", "-halt-on-error", tex_file.name],
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
        for ext in [".aux", ".log", ".out", ".toc"]:
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

#!/usr/bin/env python3
"""
Article Drafting Pipeline
=========================
Auto-triggered when Critic gives a "pursue" verdict.
Generates a working paper draft from forum findings.

v2.1 (2026-09-25): every claude call goes through claude_cli.run_claude
(tasks draft_body, draft_fix, figures). The draft is built in a private
working directory (workspace/drafts/<stem>/), compiled, and checked by the
paper gates (paper_gates.py). A draft that fails a blocking gate after at
most two gate-driven fix passes is quarantined to workspace/failed_drafts/
and never reaches articles/. A draft that passes is moved to articles/.

Usage:
    python3 draft_article.py                    # Auto-detect pursue verdicts
    python3 draft_article.py --round 4          # Draft from specific round
    python3 draft_article.py --list             # List pursue verdicts
    python3 draft_article.py --gates-only articles/<stem>.tex [--recompile]

Exit codes: 0 drafted and gates passed (or nothing to draft), 1 error,
2 gates failed (draft quarantined to workspace/failed_drafts/),
3 a figure script wrote outside the repository (draft quarantined, alert sent),
75 usage limit (claude_cli.EXIT_USAGE_LIMIT, resume later).
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
DRAFTS_DIR = WORKSPACE_DIR / "drafts"
FAILED_DRAFTS_DIR = WORKSPACE_DIR / "failed_drafts"
GATE_REPORTS_DIR = BASE_DIR / "logs" / "paper_gates"
REPLICATION_DIR = BASE_DIR / "replication"

import os
import shutil

if str(BASE_DIR.resolve()) not in [str(Path(p).resolve()) for p in sys.path if p]:
    sys.path.insert(0, str(BASE_DIR.resolve()))
import claude_cli  # noqa: E402
import forum_index  # noqa: E402
import paper_gates  # noqa: E402

HAND_CODING_DIR = KNOWLEDGE_DIR / "hand_coding"
ACTIVE_ARC_FILE = KNOWLEDGE_DIR / "active_arc.json"
AGENTS_FILE = BASE_DIR / "agents.json"

EXIT_OK, EXIT_ERROR, EXIT_GATES = 0, 1, 2
# A figure script changed a watched repository or the KNA data directory
# (M03). The draft is quarantined and nothing is published.
EXIT_EXTERNAL_WRITE = 3
# External writes seen by run_rscript during this draft (reset per draft).
EXTERNAL_WRITES: list[dict] = []
MAX_BODY_CALLS = 2
MAX_FIX_PASSES = 2
# M13 item 5: round_25.jsonl was rewritten by the R27 rerun (d1f05bc). Which
# coding it should hold is D-05, and HASHES.json records it only after that
# decision, so its hash is not checked until then.
LEGACY_HASH_EXEMPT = {"round_25.jsonl"}


def arc_depth_ok(round_num: int, force: bool = False) -> bool:
    """Season 2 depth-first gate: refuse to draft before the arc has run
    forum_config.min_arc_rounds_before_draft rounds, unless --force.
    Season 1 arcs (no active_arc.json, or season < 2) are not gated."""
    if force:
        return True
    try:
        with open(AGENTS_FILE) as f:
            data = json.load(f)
        min_rounds = int(data.get("forum_config", {}).get("min_arc_rounds_before_draft", 0))
        season = int(data.get("season", 1))
    except Exception:
        return True
    if season < 2 or min_rounds <= 0 or not ACTIVE_ARC_FILE.exists():
        return True
    try:
        arc = json.loads(ACTIVE_ARC_FILE.read_text())
        start = int(arc.get("start_round", 1))
    except Exception:
        return True
    if round_num < start:          # a Season 1 round, not part of the active arc
        return True
    depth = round_num - start + 1
    if depth < min_rounds:
        print(f"  [Draft · Season 2] Round {round_num} is arc round {depth}/{min_rounds}: "
              f"depth-first rule, not drafting yet. Use --force to override.")
        return False
    return True


# =============================================================================
# Arc 2 reflection-commitment guardrails (C5 / C6).
# Added 2026-04-20 per post_conference_reflection_2026-04-20.md.
# =============================================================================

def _in_active_season2_arc(round_num: int) -> bool:
    """True when agents.json says season 2 and the round belongs to the
    active arc (active_arc.json start_round <= round)."""
    try:
        season = int(json.loads(AGENTS_FILE.read_text()).get("season", 1))
        start = int(json.loads(ACTIVE_ARC_FILE.read_text()).get("start_round") or 0)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return False
    return season >= 2 and 0 < start <= round_num


def require_hand_coding_dictionary(round_num: int, bypass: bool = False) -> Path:
    """C5 (R15 hand-coding bottleneck): any cohort-construction paper must
    publish its dictionary to knowledge/hand_coding/round_{NN}.jsonl BEFORE
    article drafting. Returns the dictionary path if present, and raises if not.

    Heuristic for "needs hand-coding": round summary mentions "hand-coded",
    "hand coding", "manual reclassification", or "N=<small>" cohort."""
    summary_file = SUMMARIES_DIR / f"round_{round_num:02d}.md"
    if not summary_file.exists():
        # Season 2 fails closed: without the summary the check cannot tell
        # whether the round hand-coded a cohort (F7). Earlier rounds and
        # Season 1 pass through as before.
        if not bypass and _in_active_season2_arc(round_num):
            raise SystemExit(
                "[BLOCKED · Hand-Coding · C5]\n"
                f"summaries/round_{round_num:02d}.md is missing, so the hand-coding check cannot run.\n"
                "Fix: run the round's post-round steps first (python3 run_forum.py --resume --rounds 0,\n"
                "which run_arc does before drafting), or set KNA_BYPASS_HANDCODING=1.")
        return None  # No summary → skip this check
    text = summary_file.read_text().lower()
    needs = any(k in text for k in [
        "hand-coded", "hand coded", "hand coding", "manual reclassification",
        "manually reclassified", "reclassify", "coding dictionary",
    ])
    if not needs:
        return None  # Not a hand-coded paper; pass through
    if bypass:
        return None
    HAND_CODING_DIR.mkdir(parents=True, exist_ok=True)
    dict_path = HAND_CODING_DIR / f"round_{round_num:02d}.jsonl"
    if not dict_path.exists() or dict_path.stat().st_size < 10:
        # Season 2 arcs publish the dictionary in the round that BUILDS the
        # cohort; later consolidation rounds of the same arc reference it.
        # Accept the most recent dictionary from any earlier round of the
        # active arc before blocking.
        try:
            arc = json.loads(ACTIVE_ARC_FILE.read_text()) if ACTIVE_ARC_FILE.exists() else {}
            start = int(arc.get("start_round", 0) or 0)
        except Exception:
            start = 0
        if start and start <= round_num:
            for rn in range(round_num - 1, start - 1, -1):
                cand = HAND_CODING_DIR / f"round_{rn:02d}.jsonl"
                if cand.exists() and cand.stat().st_size >= 10:
                    print(f"  [Hand-Coding · C5] Using arc dictionary {cand.name} "
                          f"(cohort built in R{rn}, drafting R{round_num}).")
                    return cand
        raise SystemExit(
            "[BLOCKED · Hand-Coding · C5]\n"
            f"Round {round_num} introduces a hand-coded cohort but\n"
            f"{dict_path} is missing or empty.\n"
            "Fix: write the per-member coding dictionary (one JSON object per\n"
            "line with at least member_id, category, source) before invoking\n"
            "article drafting. Any cohort-construction paper must release the\n"
            "dictionary BEFORE the article is drafted (R15 bottleneck remedy)."
        )
    return dict_path


def check_dictionary_hash(dict_path: Path) -> str:
    """M13 item 5: refuse a hand-coding dictionary whose sha256 differs from
    the one knowledge/hand_coding/HASHES.json recorded at its creation.
    Returns "match", "unrecorded" or "exempt", and raises SystemExit on a change.
    Dictionaries that predate HASHES.json are unrecorded and pass with a
    warning. round_25.jsonl is exempt until D-05."""
    import hashlib
    dict_path = Path(dict_path)
    if dict_path.name in LEGACY_HASH_EXEMPT:
        print(f"  [Hand-Coding · M13] {dict_path.name}: hash check exempt until D-05 "
              "(rewritten by the R27 rerun; which coding it holds is an open decision).")
        return "exempt"
    try:
        hashes = json.loads((dict_path.parent / "HASHES.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        hashes = {}
    rec = hashes.get(dict_path.name)
    revs = sorted(dict_path.parent.glob(f"{dict_path.stem}.rev*{dict_path.suffix}"))
    if revs:
        print(f"  [Hand-Coding · M13] {dict_path.name}: {len(revs)} attempted rewrite(s) kept as "
              f"{', '.join(r.name for r in revs)}; the original is used.")
    if not rec:
        print(f"  [Hand-Coding · M13] {dict_path.name}: no recorded hash (predates HASHES.json).")
        return "unrecorded"
    got = hashlib.sha256(dict_path.read_bytes()).hexdigest()
    if got != rec.get("sha256"):
        raise SystemExit(
            "[BLOCKED · Hand-Coding · M13]\n"
            f"{dict_path} changed after it was created (sha256 {got[:12]} vs recorded "
            f"{str(rec.get('sha256'))[:12]}, run {rec.get('run_id')}).\n"
            "Coding dictionaries are append-only. Restore the recorded version or save the new\n"
            "coding as a new dictionary file before drafting.")
    return "match"


def check_dictionary_join(round_num: int, arc) -> None:
    """M06 part 4: when the arc's replication manifest declares a dictionary
    key map, the dictionary must join the analysis sample and agree on the
    coded field. Nothing to check when no manifest declares one."""
    if arc is None:
        return
    manifest = REPLICATION_DIR / f"arc_{arc}" / "MANIFEST.json"
    try:
        key_map = json.loads(manifest.read_text(encoding="utf-8")).get("dictionary_key_map")
    except (OSError, json.JSONDecodeError):
        return
    if not key_map:
        return
    import replicate  # noqa: E402
    res = replicate.check_key_map(key_map)
    if res.get("ok") is False:
        raise SystemExit(
            "[BLOCKED · Hand-Coding · M06]\n"
            f"{key_map['dictionary']} does not match {key_map['sample']} on "
            f"{key_map['coded_field']}: {'; '.join(res.get('problems', []))}")


def check_claim_n(tex_content: str, n_threshold: int = 10) -> list[str]:
    """C6 (R18 cabinet-channel lesson): scan drafted article for inferential
    claims attached to cells with N < threshold. Returns a list of warnings.

    Pattern targets: "(N = k)" or "N=k" or "n=k" where k < threshold,
    appearing within 120 chars of a point-estimate or significance marker
    (coefficient, p-value, confidence interval, percentage-point claim)."""
    warnings = []
    pattern = re.compile(r"\bN\s*[=:]\s*(\d+)\b|\(\s*[Nn]\s*[=:]\s*(\d+)\s*\)")
    for m in pattern.finditer(tex_content):
        n_val = int(m.group(1) or m.group(2))
        if n_val >= n_threshold:
            continue
        # Grab surrounding 150-char window to check for inferential language
        start = max(0, m.start() - 150)
        end = min(len(tex_content), m.end() + 150)
        window = tex_content[start:end].lower()
        if any(kw in window for kw in [
            "p <", "p =", "p-value", "confidence interval", "95% ci",
            "coefficient", "estimate", "significant", "effect of",
            "causes", "increases", "decreases",
        ]):
            warnings.append(
                f"N={n_val} (<{n_threshold}) paired with inferential language "
                f"near char {m.start()}: ...{tex_content[start:end].strip()[:180]}..."
            )
    return warnings


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
    """Get all posts from a specific round (identity from forum_index)."""
    return [p.read_text() for p in forum_index.round_posts(round_num, forum_dir=FORUM_DIR)]


def get_all_forum_context(up_to_round, arc=None):
    """Get compressed forum context for the drafting round's arc. Full text
    for the last 2 rounds, summaries for older rounds. Only the arc's own
    rounds are included (arc defaults to the round's arc), so Season 1 and
    earlier arcs never reach the draft_body prompt (V-10)."""
    if arc is None:
        arc = _round_arc(up_to_round)
    metas = [m for m in forum_index.index(forum_dir=FORUM_DIR)
             if m["round"] is not None and m["round"] <= up_to_round and str(m["arc"]) == str(arc)]
    arc_rounds = {m["round"] for m in metas}
    context = []

    # Include round summaries for older rounds (much shorter than full posts)
    for sf in sorted(SUMMARIES_DIR.glob("round_*.md")):
        rnd_num = int(re.search(r"(\d+)", sf.stem).group(1))
        if rnd_num in arc_rounds and rnd_num <= up_to_round - 2:
            context.append(f"--- Round {rnd_num} Summary ---\n{sf.read_text()}")

    # Full text for last 2 rounds only
    for m in metas:
        if m["round"] >= up_to_round - 1:
            context.append(f"--- {m['path'].name} ---\n{m['path'].read_text()}")

    return "\n\n".join(context)


def _round_arc(round_num):
    """Arc of a round from its posts' identity (None if unknown)."""
    for m in forum_index.index(forum_dir=FORUM_DIR):
        if m["round"] == round_num and m["arc"] is not None:
            return m["arc"]
    return None


def arc_forum_text(round_num, arc) -> str:
    """Every post of the round's arc up to the round, for the G5 new-reference check."""
    texts = []
    for m in forum_index.index(forum_dir=FORUM_DIR):
        if m["round"] is None or m["round"] > round_num:
            continue
        if arc is not None and str(m["arc"]) != str(arc):
            continue
        try:
            texts.append(m["path"].read_text(encoding="utf-8"))
        except OSError:
            continue
    return "\n\n".join(texts)


def arc_reference_list(round_num, arc) -> str:
    """One line per reference the arc's posts list in their frontmatter."""
    refs = []
    for m in forum_index.index(forum_dir=FORUM_DIR):
        if m["round"] is None or m["round"] > round_num:
            continue
        if arc is not None and str(m["arc"]) != str(arc):
            continue
        for r in forum_index.read_frontmatter(m["path"]).get("references") or []:
            if isinstance(r, str) and r not in refs and not r.endswith(".md"):
                refs.append(r)
    return "\n".join(f"- {r}" for r in refs) or "(none listed)"


def stage2_flag(name: str) -> bool:
    try:
        return bool((claude_cli.load_forum_config().get("stage2") or {}).get(name, False))
    except Exception:   # a missing or unreadable agents.json means Stage 1 only
        return False


def _ws_rel(p: Path) -> str:
    """Path as seen from the claude call's cwd (workspace/), absolute if outside."""
    try:
        return str(Path(p).resolve().relative_to(WORKSPACE_DIR.resolve()))
    except ValueError:
        return str(p)


def _body_ok(text: str, min_words: int = 3000) -> tuple[bool, str]:
    """Completeness gate for a generated LaTeX body. The R27 stub shipped
    because a truncated body (ended mid-table) went through assembly and the
    revise regex then reduced it to one word. Nothing ever checked length."""
    wc = len(text.split())
    if wc < min_words:
        return False, f"only {wc} words (< {min_words})"
    if r"\section{Conclusion}" not in text and r"\section*{Conclusion}" not in text:
        return False, "no Conclusion section"
    if r"\bibliography" not in text and r"\section*{References}" not in text:
        return False, "no bibliography or References section"
    return True, f"{wc} words"


def gates_prompt_section(replication: dict, arc, disclosure_on: bool) -> str:
    """What the automated gates check, stated in the drafting prompt so the
    first draft can pass them. Lines are indented for textwrap.dedent."""
    if replication.get("exists") and replication.get("verify_passed"):
        rep = (f"A verified replication package exists at replication/arc_{arc}. You may say that the "
               f"scripts are in replication/arc_{arc}, naming that path exactly.")
    else:
        rep = ("No verified replication package exists for this arc. Do NOT claim a replication archive, "
               "replication package, replication materials or a public repository of code or data.")
    lines = [
        "## AUTOMATED GATES (the draft is not published unless it passes)",
        "",
        "- G1: every \\citet/\\citep key has an entry in the .bib file.",
        "- G2: nothing unresolved in the compiled PDF (no ?? or (?) markers, no undefined \\ref, no",
        "  PLACEHOLDER or TODO, every \\includegraphics file exists). A figure placeholder box that the",
        "  pipeline cannot replace (no runnable verbatim R block before it) fails this gate.",
        "- G4: never write 'pre-registered' unless the paper gives a registry id (OSF, AsPredicted, EGAP,",
        "  AEA). Thresholds declared in the forum before estimation are 'declared before estimation'.",
        f"- G4: {rep}",
        "- G6: no absolute file paths anywhere in the paper or its R code. Use Sys.getenv(\"KBL_DATA\").",
    ]
    if disclosure_on:
        lines += ["- Do not write any AI-use or disclosure paragraph of your own beyond the notice in the",
                  "  template. The pipeline appends a disclosure built from the run logs."]
    return "\n".join("    " + l if l else "" for l in lines) + "\n"


def build_draft_prompt(round_num, content_rel, bib_rel, forum_context, gates_section):
    return textwrap.dedent(f"""\
    You are a research paper drafting agent. Based on the forum discussion below,
    draft a working paper as a LaTeX document body following APSR conventions
    and the academic writing style guide below.

    IMPORTANT: Write ONLY the LaTeX body content (from \\title to the bibliography).
    Do NOT include \\documentclass, \\usepackage, or \\begin{{document}}.
    The template handles those.

    Write the content to: {content_rel}

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
    [~2,500 words. Present the main results, robustness checks and heterogeneity analysis
     that the forum's estimates support, in as many tables as those estimates fill.
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
    - ALSO write a separate .bib file to: {bib_rel}
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

    **Tables (booktabs):**
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

    Data path for R: Sys.getenv("KBL_DATA") (the KBL_DATA environment variable). Never write an absolute path.
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
    DATA <- Sys.getenv("KBL_DATA")
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

    RULES:
    - ONLY use findings/statistics/references from the forum posts below
    - Do NOT invent data or citations. Cite only works that the forum posts cite.
    - Acknowledge Critic's limitations honestly
    - Target 8,000-10,000 words
    - APSR style throughout

    **KNA Data Available (check before writing Data section):**
    - master_bills_{{17-22}}.parquet: bill lifecycle (42+ columns)
    - roll_calls_all.parquet: 2.4M member-level votes
    - ideal_points_bridged.csv (default, cross-assembly) / ideal_points_wnominate.csv (within-assembly) / ideal_points_dwnominate.csv (pooled): name the series used
    - committee_meetings_{{17-22}}.parquet: committee meeting records
    - bill_texts_linked.parquet: 60K propose-reason texts
    - cosponsorship_edges.parquet: cosponsorship network
    - members_{{17-22}}.parquet: member metadata (party, district, committee, sex, birth_date, election_type, reelection)
    - assets data: db.assets(assembly=22) - 2,928 member-year wealth observations
    - kr-hearings-data: 9.9M speeches + 7.4M Q&A dyads (separate download)
    Data path: $KBL_DATA/ (read it from the environment)
    R code for figures should use arrow::read_parquet() to load this data directly.
    - Valid LaTeX that compiles with xelatex

{gates_section}
    ## Forum Discussion (Rounds 1-{round_num})

    {forum_context}
    """)


BODY_MESSAGE = (
    "Write the working paper draft now. Write TWO files: (1) the LaTeX content to {content} and (2) "
    "the BibTeX references to {bib}. IMPORTANT: build the content file INCREMENTALLY in at least four "
    "steps: first Write the file with title block, abstract, and Introduction; then APPEND (via Edit on "
    "the closing lines) Literature and Theory; then Data and Method plus Results; then Discussion, "
    "Conclusion, and the bibliography commands. Never emit the whole paper in a single Write call; a "
    "single giant Write gets truncated mid-table. After the last step, Read the file end to confirm it "
    "closes with the bibliography commands."
)

FIX_PROMPT = textwrap.dedent("""\
    You are fixing a drafted LaTeX working paper so that it passes automated publication gates.
    Fix ONLY the items listed below. Do not rewrite, shorten or restructure anything else, and do
    not add new claims, numbers or citations that the forum record does not support.

    Files (edit them in place with Edit; Read first):
    - paper: {tex}
    - bibliography: {bib}
    - figure scripts: {figdir}

    Rules:
    - A missing .bib key: add a correct BibTeX entry only for a work in the reference list below;
      otherwise delete the citation and rephrase the sentence so it no longer depends on it.
    - 'pre-registered' without a registry id: replace it with 'declared before estimation'
      or similar wording that is true of the forum record.
    - An unbacked replication-archive claim: delete the claim.
    - An undefined \\ref or a ?? marker: fix the label or remove the reference.
    - An absolute path: replace it with Sys.getenv("KBL_DATA") or a relative path.

    Failing gate items:
    {items}

    References listed in the forum posts of this arc:
    {refs}
    """)


def _assemble(tex_file: Path, content: str, disclosure_input: str | None) -> str:
    template = (ARTICLES_DIR / "template.tex").read_text()
    title_match = re.search(r'\\title\{(.+?)\}', content)
    title = title_match.group(1) if title_match else "Untitled"
    full_tex = template.replace("%%TITLE%%", "").replace("%%CONTENT%%", content)
    if disclosure_input:
        full_tex = full_tex.replace("\\end{document}", f"\\input{{{disclosure_input}}}\n\n\\end{{document}}", 1)
    tex_file.write_text(full_tex)
    return title


def _clean_aux(tex_file: Path) -> None:
    for ext in [".aux", ".log", ".out", ".toc", ".bbl", ".blg"]:
        f = tex_file.with_suffix(ext)
        if f.exists():
            f.unlink()


def _compile_and_gate(tex_file: Path, bib_file: Path, round_num: int, arc, forum_text: str,
                      replication_dir: Path | None) -> dict:
    """Compile, run the gates while the .log and .blg still exist, then clean.

    The PDF, .log and .blg of an earlier compile are removed first, so the
    gates never read a stale PDF after a compile that failed. A compile that
    raised or aborted leaves no PDF or .log, and G2 then fails (compiled=True)."""
    for ext in (".pdf", ".log", ".blg"):
        tex_file.with_suffix(ext).unlink(missing_ok=True)
    try:
        compile_tex(tex_file, clean=False)
    except Exception as e:
        print(f"  PDF compilation failed: {e}")
    pdf = tex_file.with_suffix(".pdf")
    report = paper_gates.run_all(
        tex_file, bib_file, pdf if pdf.exists() else None,
        log_path=tex_file.with_suffix(".log"), blg_path=tex_file.with_suffix(".blg"),
        forum_text=forum_text, replication_dir=replication_dir, arc=arc, compiled=True)
    _clean_aux(tex_file)
    print(f"  [Gates] {paper_gates.summary_line(report)}")
    return report


def _next_free(path: Path) -> Path:
    if not path.exists():
        return path
    k = 2
    while path.with_name(f"{path.name}.{k}").exists():
        k += 1
    return path.with_name(f"{path.name}.{k}")


def _quarantine(work: Path, slug: str, reason: str, report: dict | None) -> Path:
    """Move the working directory to workspace/failed_drafts/<stem>/ (never
    deleted, never under articles/) with the gate report and the reason."""
    FAILED_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = _next_free(FAILED_DRAFTS_DIR / slug)
    if work.exists():
        shutil.move(str(work), str(dest))
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "FAILED.json").write_text(json.dumps({
        "stem": slug, "reason": reason, "when": datetime.now().isoformat(timespec="seconds"),
        "failed_blocking": (report or {}).get("failed_blocking"),
        "failing_items": paper_gates.failing_items(report) if report else [],
    }, ensure_ascii=False, indent=1) + "\n")
    if report is not None:
        (dest / "gates.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print(f"  [Draft] quarantined to {dest.relative_to(BASE_DIR) if dest.is_relative_to(BASE_DIR) else dest}: {reason}")
    return dest


def _save_gate_report(slug: str, report: dict) -> Path:
    GATE_REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = GATE_REPORTS_DIR / f"{slug}.gates.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    return out


def _publish(work: Path, slug: str, round_num: int, ts: str, title: str, bib_name: str) -> Path:
    """Move a draft that passed every blocking gate into articles/. A draft
    without its compiled PDF is never published."""
    if not (work / f"{slug}.pdf").exists():
        raise RuntimeError(f"no compiled PDF ({slug}.pdf) in the working directory")
    targets = [ARTICLES_DIR / f"{slug}.tex", ARTICLES_DIR / f"{slug}.pdf", ARTICLES_DIR / bib_name,
               ARTICLES_DIR / "figures" / slug]
    clash = [t for t in targets if t.exists()]
    if clash:
        raise RuntimeError(f"refusing to overwrite {', '.join(t.name for t in clash)} in articles/")
    for name in (f"{slug}.tex", f"{slug}.pdf", bib_name, f"{slug}.disclosure.tex", f"{slug}.disclosure.json"):
        src = work / name
        if src.exists():
            shutil.move(str(src), str(ARTICLES_DIR / name))
    fig_src = work / "figures" / slug
    if fig_src.is_dir():
        (ARTICLES_DIR / "figures").mkdir(exist_ok=True)
        shutil.move(str(fig_src), str(ARTICLES_DIR / "figures" / slug))
    tex_file = ARTICLES_DIR / f"{slug}.tex"
    md_file = ARTICLES_DIR / f"{slug}.md"
    md_file.write_text(
        f"---\ntitle: \"{title}\"\nauthors: \"KNA Research Agents\"\n"
        f"date: \"{ts}\"\nsource_round: {round_num}\nstatus: \"experimental draft\"\n"
        f"tex_file: \"{tex_file.name}\"\n---\n\n"
        f"# {title}\n\n"
        f"**KNA Research Agents** | AI-Generated Working Paper | {ts}\n\n"
        f"Source: Forum Round {round_num} | Status: Experimental Draft\n\n"
        f"[View LaTeX source]({tex_file.name}) | "
        f"[Download PDF]({slug}.pdf)\n\n---\n\n"
        f"*See PDF for full paper with equations, tables, and references.*\n"
    )
    leftover = [p for p in work.rglob("*") if p.is_file()] if work.exists() else []
    if work.exists():
        shutil.move(str(work), str(_next_free(DRAFTS_DIR / f"{slug}.published_workdir")))
    print(f"  [Draft] published {tex_file.name} ({len(leftover)} working files kept privately)")
    return tex_file


def _fix_pass(n: int, tex_file: Path, bib_file: Path, report: dict, round_num: int, arc) -> bool:
    """One gate-driven fix pass (task draft_fix). Returns False when the call
    failed or the result broke the paper (then the previous files are restored)."""
    items = paper_gates.failing_items(report)
    backup_tex, backup_bib = tex_file.read_text(), bib_file.read_text() if bib_file.exists() else None
    prompt = FIX_PROMPT.format(
        tex=_ws_rel(tex_file), bib=_ws_rel(bib_file),
        figdir=_ws_rel(tex_file.parent / "figures" / tex_file.stem),
        items="\n".join(f"- {i}" for i in items), refs=arc_reference_list(round_num, arc))
    print(f"  [Fix pass {n}/{MAX_FIX_PASSES}] {len(items)} failing item(s)")
    res = claude_cli.run_claude(
        "draft_fix", prompt, user_message="Fix the listed items now, then Read the file end to confirm "
        "it is complete.", tools=["Read", "Edit", "Write"], cwd=WORKSPACE_DIR, round_num=round_num,
        arc_id=str(arc) if arc is not None else None, timeout_s=1800)
    if res.failure == "usage_limit":
        raise UsageLimit(res.resume_at)
    body = paper_gates.body_of(tex_file.read_text())
    ok, why = _body_ok(body)
    if not ok or len(body) < 0.5 * len(paper_gates.body_of(backup_tex)):
        print(f"  [Fix pass {n}] result rejected ({why}); restoring the previous files.")
        tex_file.write_text(backup_tex)
        if backup_bib is not None:
            bib_file.write_text(backup_bib)
        return False
    return res.ok


class UsageLimit(Exception):
    """A claude call hit the usage limit. Drafting stops and resumes later."""


def draft_article(round_num):
    """Draft, gate and publish (or quarantine) the paper for one round.
    Returns an exit code: 0 published or already exists, 1 error, 2 gates
    failed, claude_cli.EXIT_USAGE_LIMIT on a usage limit."""
    ARTICLES_DIR.mkdir(exist_ok=True)
    WORKSPACE_DIR.mkdir(exist_ok=True)
    arc = _round_arc(round_num)
    EXTERNAL_WRITES.clear()

    # C5 · Pre-flight hand-coding dictionary check. Refuses to draft cohort
    # papers without a published dictionary. Bypass via KNA_BYPASS_HANDCODING=1.
    bypass_hc = os.environ.get("KNA_BYPASS_HANDCODING") == "1"
    dict_path = require_hand_coding_dictionary(round_num, bypass=bypass_hc)
    if dict_path is not None:
        print(f"  [Hand-Coding · C5] dictionary present: {dict_path}")
        check_dictionary_hash(dict_path)
        check_dictionary_join(round_num, arc)

    # Check for existing articles to avoid duplicates
    existing = list(ARTICLES_DIR.glob(f"*_r{round_num}.tex")) + list(ARTICLES_DIR.glob(f"*_r{round_num}.md"))
    existing = [e for e in existing if "template" not in e.name and "content" not in e.name]
    if existing:
        print(f"  Article for round {round_num} already exists: {existing[0].name}")
        return EXIT_OK

    if not os.environ.get("KBL_DATA"):
        print("  [Draft] KBL_DATA is not set. Set it to the KNA processed-data directory; "
              "there is no default path.")
        return EXIT_ERROR

    ts = datetime.now().strftime("%Y-%m-%d")
    article_slug = f"{ts}_r{round_num}"
    work = DRAFTS_DIR / article_slug
    if work.exists():
        _quarantine(work, article_slug, "stale working directory from an earlier run", None)
    work.mkdir(parents=True)
    if (ARTICLES_DIR / "apsr.bst").exists():
        shutil.copy2(ARTICLES_DIR / "apsr.bst", work / "apsr.bst")
    tex_file = work / f"{article_slug}.tex"
    content_file = work / f"{article_slug}_content.tex"
    bib_file = work / f"references_r{round_num}.bib"
    arc_id = str(arc) if arc is not None else None

    rep_dir = REPLICATION_DIR / f"arc_{arc}"
    rep_dir = rep_dir if rep_dir.exists() else None
    replication = paper_gates.replication_status(rep_dir)
    disclosure_on = stage2_flag("disclosure_appendix")
    forum_context = get_all_forum_context(round_num, arc)
    forum_text = arc_forum_text(round_num, arc)
    prompt = build_draft_prompt(round_num, _ws_rel(content_file), _ws_rel(bib_file), forum_context,
                                gates_prompt_section(replication, arc, disclosure_on))

    def build_disclosure():
        """M21 (Stage 2): rebuilt before each assembly so the drafting runs
        themselves are listed. None when the flag is off or the build fails."""
        if not disclosure_on:
            return None
        try:
            import disclosure  # noqa: E402
            disclosure.build(round_num, article_slug, arc=arc, out_dir=work)
            return f"{article_slug}.disclosure"
        except Exception as e:
            print(f"  [Disclosure] not built ({type(e).__name__}: {e}); the gates will run without it.")
            return None

    print(f"\n  Drafting article from Round {round_num}...")
    print(f"  Working directory: {_ws_rel(work)}")

    report, reason, title = None, None, "Untitled"
    body_calls = fix_calls = 0
    try:
        while body_calls < MAX_BODY_CALLS:
            body_calls += 1
            msg = BODY_MESSAGE.format(content=_ws_rel(content_file), bib=_ws_rel(bib_file))
            if reason:
                msg += f" The previous attempt was rejected: {reason}. Avoid that problem this time."
            res = claude_cli.run_claude(
                "draft_body", prompt, user_message=msg, tools=["Write", "Edit", "Read"],
                expect_file=content_file, cwd=WORKSPACE_DIR, round_num=round_num, arc_id=arc_id,
                timeout_s=3600)
            if res.failure == "usage_limit":
                raise UsageLimit(res.resume_at)
            if not content_file.exists():
                reason = f"no content file (claude {res.failure})"
                print(f"  Attempt {body_calls}: {reason}")
                continue
            candidate = content_file.read_text()
            ok, why = _body_ok(candidate)
            if not ok:
                reason = f"body incomplete ({why})"
                print(f"  Attempt {body_calls}: {reason}; regenerating...")
                content_file.rename(work / f"{article_slug}_content.attempt{body_calls}.tex")
                continue
            print(f"  Content generated: {len(candidate.split())} words")
            title = _assemble(tex_file, candidate, build_disclosure())

            # C6 · N>=10 guardrail: scan for inferential claims attached to cells < N=10
            n_warnings = check_claim_n(tex_file.read_text(), n_threshold=10)
            if n_warnings:
                print(f"  [Claim Check · C6] {len(n_warnings)} small-N inferential claim(s) flagged:")
                for w in n_warnings[:5]:
                    print(f"    - {w[:200]}")
                print("    → Demote to DESCRIPTIVE ONLY or document the override in topic_gate.md.")

            # Execute R figures
            try:
                execute_r_figures(tex_file)
            except Exception as e:
                print(f"  R figure execution failed: {e}")

            # Check for orphan placeholders and attempt repair
            try:
                repair_orphan_figures(tex_file, round_num, arc_id=arc_id)
            except UsageLimit:
                raise
            except Exception as e:
                print(f"  Orphan figure repair failed: {e}")

            report = _compile_and_gate(tex_file, bib_file, round_num, arc, forum_text, rep_dir)
            while not report["ok"] and fix_calls < MAX_FIX_PASSES:
                fix_calls += 1
                _fix_pass(fix_calls, tex_file, bib_file, report, round_num, arc)
                report = _compile_and_gate(tex_file, bib_file, round_num, arc, forum_text, rep_dir)
            if report["ok"]:
                break
            reason = "blocking gates failed: " + "; ".join(paper_gates.failing_items(report, limit=12))
            if body_calls < MAX_BODY_CALLS:
                content_file.rename(work / f"{article_slug}_content.attempt{body_calls}.tex")
    except UsageLimit as e:
        if EXTERNAL_WRITES:   # the external write outranks the pause (it needs an acknowledged stop)
            return _external_write_stop(work, article_slug, round_num, report,
                                        f"then a usage limit (resumes {e.args[0] or 'unknown'})")
        _quarantine(work, article_slug, f"usage limit (resumes {e.args[0] or 'unknown'})", report)
        return claude_cli.EXIT_USAGE_LIMIT
    except claude_cli.ClaudeCLIError as e:
        if EXTERNAL_WRITES:
            return _external_write_stop(work, article_slug, round_num, report, f"then claude_cli refused: {e}")
        _quarantine(work, article_slug, f"claude_cli refused: {e}", report)
        return EXIT_ERROR

    if EXTERNAL_WRITES:
        return _external_write_stop(work, article_slug, round_num, report)
    if report is None:
        print(f"  WARNING: Article not generated (body failed the completeness gate {body_calls} times)")
        _quarantine(work, article_slug, reason or "no body produced", None)
        return EXIT_ERROR
    if content_file.exists():
        content_file.unlink()   # the body lives in the assembled tex now
    if not report["ok"]:
        dest = _quarantine(work, article_slug, "blocking paper gates failed", report)
        claude_cli.notify("KNA forum: draft blocked",
                          f"R{round_num} draft failed gates {', '.join(report['failed_blocking'])}; "
                          f"quarantined to {dest.name}")
        return EXIT_GATES
    _save_gate_report(article_slug, report)
    try:
        _publish(work, article_slug, round_num, ts, title, bib_file.name)
    except (OSError, RuntimeError) as e:
        print(f"  [Draft] publish failed: {e}")
        _quarantine(work, article_slug, f"publish failed: {e}", report)
        return EXIT_ERROR
    return EXIT_OK


def _external_write_stop(work: Path, slug: str, round_num: int, report: dict | None,
                         then: str | None = None) -> int:
    """M03: the same stop as an external write in a forum run. Nothing is
    published, the alert goes out, and run_arc records external_write."""
    reason = f"external write by a figure script ({len(EXTERNAL_WRITES)} change(s))"
    dest = _quarantine(work, slug, reason + (f", {then}" if then else ""), report)
    try:
        import write_guard  # noqa: E402
        public = write_guard.public_changes(EXTERNAL_WRITES)
    except Exception:
        public = [{"kind": c.get("kind"), "path": c.get("path")} for c in EXTERNAL_WRITES]
    (dest / "EXTERNAL_WRITES.json").write_text(json.dumps(public, ensure_ascii=False, indent=1) + "\n")
    claude_cli.notify("KNA forum: external write",
                      f"R{round_num} draft: a figure script changed a watched repository or the data "
                      f"directory, quarantined to {dest.name}")
    return EXIT_EXTERNAL_WRITE


def repair_orphan_figures(tex_file, round_num, arc_id=None):
    """Detect fbox placeholders without R code and ask Claude to generate R scripts
    (task figures, one call per orphan figure)."""
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
        - Load data from the directory in the KBL_DATA environment variable:
          DATA <- Sys.getenv("KBL_DATA"). Never write an absolute path.
        - Available files: member_info_17_22.parquet, master_bills_{{17-22}}.parquet
        - Key columns: mona_cd, assembly (in members) = age (in bills), gender (남/여),
          election_type (비례대표/지역구), reelection (초선/재선/3선/...),
          rst_mona_cd (sponsor in bills), ppsr_kind (의원 = member bill), passed (0/1)
        - Use: library(arrow), library(dplyr), library(ggplot2)
        - Style: theme_bw(base_size = 11), Okabe-Ito colorblind palette
        - Save with: ggsave("{pdf_name}", width = 7, height = 4.5)  (the script runs in the figure directory)
        - Filter bills: ppsr_kind == "의원"
        - Join members to bills: by rst_mona_cd = mona_cd AND age = assembly

        Write ONLY the R code to: {_ws_rel(r_file)}
        No explanation, no markdown, just the .R file.
        """)

        print(f"  Generating R code for orphan figure {fig_num}...")
        res = claude_cli.run_claude(
            "figures", prompt, user_message="Write the R script now.", tools=["Write"],
            expect_file=r_file, cwd=WORKSPACE_DIR, round_num=round_num, arc_id=arc_id,
            timeout_s=300, max_continuations=1)
        if res.failure == "usage_limit":
            raise UsageLimit(res.resume_at)
        if res.failure == "timeout":
            print(f"  Timeout generating R code for figure {fig_num}")
            continue

        if not r_file.exists():
            print(f"  WARNING: R script not generated for figure {fig_num}")
            continue

        # Execute the R script
        print(f"  Executing {r_file.name}...")
        try:
            r_result = run_rscript(r_file, fig_dir, f"{stem}_orphan_fig{fig_num}")
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


def run_rscript(r_file, fig_dir, run_id, timeout=120):
    """Rscript under the external-write guard (M03): watched repositories and
    the KNA data directory are compared before and after, and any change is
    reported and written to logs/external_writes/<run_id>.patch."""
    before = None
    try:
        import write_guard  # noqa: E402
        before = write_guard.guard_before()
    except Exception as e:
        print(f"  [write guard] baseline failed ({type(e).__name__}); running without it")
    try:
        return subprocess.run(["Rscript", str(r_file)], capture_output=True, text=True,
                              timeout=timeout, cwd=str(fig_dir))
    finally:
        if before is not None:
            try:
                changes = write_guard.guard_after(before, run_id)
                if changes:
                    EXTERNAL_WRITES.extend(changes)
                    print(f"  [write guard] {len(changes)} external write(s) by {Path(r_file).name}; "
                          f"see {changes[0].get('patch')}")
            except Exception as e:
                print(f"  [write guard] check failed ({type(e).__name__})")


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

        # Modify ggsave to output to our fig directory. Rscript runs with
        # cwd = fig_dir, so a relative name keeps absolute paths out of the
        # tracked fig_N.R file.
        r_code = block.strip()
        backref = r'\2'
        r_code = _re.sub(
            r'ggsave\(["\']([^"\']+)["\'](.*?)\)',
            f'ggsave("{pdf_name}"' + backref + ')',
            r_code
        )

        # KNA data path comes from the environment (M02), never a literal
        r_code = f'# Auto-generated figure for article\n' \
                 f'# Reads KNA data from Sys.getenv("KBL_DATA").\n' \
                 f'{r_code}\n'

        r_file.write_text(r_code)
        print(f"  Executing R figure {fig_count}: {r_file.name}")

        try:
            result = run_rscript(r_file, fig_dir, f"{stem}_fig{fig_count}")
            if pdf_path.exists():
                print(f"  Figure generated: {pdf_name} ({pdf_path.stat().st_size // 1024} KB)")

                # Replace the verbatim block + fbox placeholder with includegraphics
                # Find the verbatim block and the following fbox/figure placeholder
                old_verbatim = f'\\begin{{verbatim}}{block}\\end{{verbatim}}'

                # Replace verbatim with a comment (keep the code reference)
                content = content.replace(
                    old_verbatim,
                    f'% R code for Figure {fig_count} executed automatically (see figures/{stem}/fig_{fig_count}.R)'
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


def compile_tex(tex_file, clean=True):
    """Compile LaTeX to PDF using xelatex. clean=False keeps the .log and
    .blg so the paper gates can read them (the caller cleans afterwards)."""
    import subprocess as _sp

    tex_dir = tex_file.parent
    # xelatex and bibtex from PATH, else the TinyTeX install (as recompile_copy).
    TINYTEX = Path.home() / "Library/TinyTeX/bin/universal-darwin"
    xelatex = shutil.which("xelatex") or str(TINYTEX / "xelatex")
    bibtex = shutil.which("bibtex") or str(TINYTEX / "bibtex")
    print(f"  Compiling {tex_file.name} (xelatex + bibtex)...")

    # Pass 1: xelatex
    _sp.run(
        [xelatex, "-interaction=nonstopmode", tex_file.name],
        capture_output=True, text=True, timeout=120, cwd=str(tex_dir),
    )

    # Pass 2: bibtex (for natbib references)
    _sp.run(
        [bibtex, tex_file.stem],
        capture_output=True, text=True, timeout=60, cwd=str(tex_dir),
    )

    # Pass 3-4: xelatex twice more for cross-refs
    for i in range(2):
        result = _sp.run(
            [xelatex, "-interaction=nonstopmode", tex_file.name],
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
        if clean:
            _clean_aux(tex_file)
    else:
        print(f"  WARNING: PDF not generated")


def gates_only(tex, bib=None, pdf=None, recompile=False, offline=False) -> int:
    """--gates-only: run the paper gates on an existing paper. The paper is only
    read, and --recompile compiles a temporary copy so G2 can read the .log and .blg."""
    argv = [str(tex)]
    if bib:
        argv += ["--bib", str(bib)]
    if pdf:
        argv += ["--pdf", str(pdf)]
    if recompile:
        argv.append("--recompile")
    if offline:
        argv.append("--offline")
    return paper_gates.main(argv)


def _worst(codes):
    """Most severe exit code: usage limit, external write, gates failed, error."""
    for c in (claude_cli.EXIT_USAGE_LIMIT, EXIT_EXTERNAL_WRITE, EXIT_GATES, EXIT_ERROR):
        if c in codes:
            return c
    return EXIT_OK


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Article Drafting Pipeline")
    parser.add_argument("--round", type=int, help="Draft from specific round")
    parser.add_argument("--list", action="store_true", help="List pursue verdicts")
    parser.add_argument("--force", action="store_true",
                        help="Season 2: draft even if the arc has fewer than min_arc_rounds_before_draft rounds")
    parser.add_argument("--gates-only", metavar="TEX", default=None,
                        help="Run the paper gates on an existing .tex and exit (0 pass, 2 fail)")
    parser.add_argument("--bib", default=None, help="with --gates-only: the .bib file")
    parser.add_argument("--pdf", default=None, help="with --gates-only: the .pdf file")
    parser.add_argument("--recompile", action="store_true", help="with --gates-only: compile a temporary copy")
    parser.add_argument("--offline", action="store_true", help="with --gates-only: G5 from the cache only")
    args = parser.parse_args(argv)

    if args.gates_only:
        return gates_only(args.gates_only, args.bib, args.pdf, args.recompile, args.offline)

    if args.list:
        pursues = find_pursue_verdicts()
        if not pursues:
            print("No 'pursue' verdicts found.")
        for p in pursues:
            print(f"  Round {p['round']}: {p['finding'][:80]}... [{p['verdict']}]")
        return EXIT_OK

    if args.round:
        if not arc_depth_ok(args.round, force=args.force):
            return EXIT_OK      # nothing drafted, nothing to publish
        return draft_article(args.round)

    # Auto-detect: find pursue verdicts without existing articles
    pursues = find_pursue_verdicts()
    if not pursues:
        print("No 'pursue' verdicts found. Run more forum rounds.")
        return EXIT_OK

    codes, seen = [], set()
    for p in pursues:
        rnd = p["round"]
        if rnd in seen:
            continue
        seen.add(rnd)
        existing = list(ARTICLES_DIR.glob(f"*_r{rnd}_*.md"))
        if not existing:
            print(f"  Found pursue verdict for Round {rnd}")
            if arc_depth_ok(rnd, force=args.force):
                codes.append(draft_article(rnd))
                if codes[-1] in (claude_cli.EXIT_USAGE_LIMIT, EXIT_EXTERNAL_WRITE):
                    break   # a pause or an external-write stop ends the run
        else:
            print(f"  Round {rnd}: article already exists ({existing[0].name})")
    return _worst(codes)


if __name__ == "__main__":
    sys.exit(main())

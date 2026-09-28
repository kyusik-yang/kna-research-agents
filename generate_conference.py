#!/usr/bin/env python3
"""
Conference Generator
====================
Auto-triggered every 20 cumulative forum rounds.
Generates a structured academic conference from all forum findings and articles.

Publish gate (D-09). The proceedings are model-written and auto_run.sh pushes
them, so they pass the leak lint with paper gate G6's blocking rule (absolute
home or volume paths, private patterns marked block) and paper gate G4's
overclaim lint before anything is committed. Proceedings that fail are moved
to workspace/failed_drafts/ (gitignored) and the script exits 2. The same
gate runs on the agora discussions auto_run.sh is about to commit
(--gate-pending agora/discussions).

Usage:
    python3 generate_conference.py              # Auto-detect if ready
    python3 generate_conference.py --force      # Force generation
    python3 generate_conference.py --gate-pending agora/discussions --label agora
Exit status: 0 done, 2 a file failed the publish gate and was quarantined,
75 usage limit.
"""

import argparse
import json
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
FORUM_DIR = BASE_DIR / "forum"
ARTICLES_DIR = BASE_DIR / "articles"
SUMMARIES_DIR = BASE_DIR / "summaries"
ARCHIVE_DIR = BASE_DIR / "forum_archive"
WORKSPACE_DIR = BASE_DIR / "workspace"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
FAILED_DRAFTS_DIR = WORKSPACE_DIR / "failed_drafts"
EXIT_GATES = 2   # as in draft_article, a blocking gate failed and the file is quarantined

# Every claude call goes through the forum wrapper (pinned model, effort
# forum_config.effort_by_task.conference, prompt kept under logs/prompts/).
import claude_cli


def _shown(path) -> str:
    try:
        return str(Path(path).resolve().relative_to(BASE_DIR.resolve()))
    except ValueError:
        return Path(path).name


def _overclaim_gate(text: str, name: str) -> dict:
    """Paper gate G4 on a markdown or JSON file. A text that names several
    replication/arc_N packages passes only when each of them is verified."""
    import paper_gates
    # G4 drops LaTeX comments (an unescaped % to the end of the line). This
    # text has none, so a line such as "rose 12% ..." is read to its end.
    t = text.replace("%", r"\%")
    named = sorted(set(paper_gates.ARC_PACKAGE_RE.findall(t))) or [None]
    results = []
    for n in named:
        rep = paper_gates.replication_status(paper_gates.REPLICATION_DIR / f"arc_{n}") if n else None
        results.append(paper_gates.gate_g4(t, replication=rep, arc=n))
    g = next((r for r in results if not r["passed"]), results[0])
    g["details"]["path"] = name
    return g


def public_gate(paths) -> dict:
    """Run the leak lint (with paper gate G6's blocking rule) and paper gate
    G4's overclaim lint on model-written files before auto_run.sh commits and
    pushes them. Returns {"ok", "gates", "failed_blocking"}, the shape of
    paper_gates.run_all, so paper_gates.failing_items reads it."""
    import paper_gates
    texts = {_shown(p): Path(p).read_text(encoding="utf-8", errors="replace") for p in paths}
    gates = [paper_gates.gate_g6(texts)] + [_overclaim_gate(t, n) for n, t in texts.items()]
    failed = sorted({g["id"] for g in gates if g["blocking"] and not g["passed"]})
    return {"ok": not failed, "gates": gates, "failed_blocking": failed}


def quarantine(paths, stem: str, reason: str, report: dict) -> Path:
    """Move the files to workspace/failed_drafts/<stem>/ (gitignored, never
    deleted) with FAILED.json and gates.json, as draft_article does."""
    import paper_gates
    FAILED_DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    dest, k = FAILED_DRAFTS_DIR / stem, 1
    while dest.exists():
        dest, k = FAILED_DRAFTS_DIR / f"{stem}.{k}", k + 1
    dest.mkdir(parents=True)
    for p in paths:
        if Path(p).exists():
            shutil.move(str(p), str(dest / Path(p).name))
    (dest / "FAILED.json").write_text(json.dumps({
        "stem": stem, "reason": reason, "when": datetime.now().isoformat(timespec="seconds"),
        "files": [_shown(p) for p in paths], "failed_blocking": report.get("failed_blocking"),
        "failing_items": paper_gates.failing_items(report),
    }, ensure_ascii=False, indent=1) + "\n")
    (dest / "gates.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n")
    print(f"  [Publish gate] quarantined to {_shown(dest)}: {reason} "
          f"({', '.join(report.get('failed_blocking') or [])})")
    return dest


def pending_files(directory) -> list[Path]:
    """Files under directory that `git add <directory>` would stage (new or
    changed), read from git status. Raises when git fails, so the caller
    publishes nothing it could not check."""
    root = BASE_DIR.resolve()
    out = subprocess.run(["git", "status", "--porcelain", "-z", "--untracked-files=all", "--",
                          _shown(directory)], cwd=str(root), capture_output=True, check=True).stdout
    entries = out.decode("utf-8", "surrogateescape").split("\0")
    files, skip = [], False
    for e in entries:
        if skip or len(e) < 4:
            skip = False
            continue
        if e[0] in "RC" or e[1] in "RC":
            skip = True   # a rename or copy is followed by its source path
        f = root / e[3:]
        if f.is_file():
            files.append(f)
    return files


def gate_pending(directory, label: str) -> int:
    """Gate the files auto_run.sh is about to commit from directory, one
    group per stem (an agora discussion is a .json and a .md). A failing
    group is quarantined and the rest stay. Returns 0, or EXIT_GATES when
    anything was quarantined."""
    groups: dict = {}
    for f in pending_files(directory):
        groups.setdefault(f.with_suffix(""), []).append(f)
    code = 0
    for stem, files in sorted(groups.items()):
        report = public_gate(files)
        if report["ok"]:
            print(f"  [Publish gate] {_shown(stem)}: passed")
            continue
        quarantine(files, f"{label}_{stem.name}", f"{label} output failed the publish gate", report)
        code = EXIT_GATES
    return code


def count_cumulative_rounds():
    """Count total rounds across current forum + archives."""
    current = len(list(SUMMARIES_DIR.glob("round_*.md"))) if SUMMARIES_DIR.exists() else 0
    archived = 0
    if ARCHIVE_DIR.exists():
        for d in ARCHIVE_DIR.iterdir():
            if d.is_dir():
                archived += len(list(d.glob("round_*.md")))
    return current + archived


def get_all_summaries():
    """Collect all round summaries (current + archived)."""
    summaries = []

    # Archived summaries
    if ARCHIVE_DIR.exists():
        for d in sorted(ARCHIVE_DIR.iterdir()):
            if d.is_dir():
                for s in sorted(d.glob("round_*.md")):
                    summaries.append(s.read_text())

    # Current summaries
    if SUMMARIES_DIR.exists():
        for s in sorted(SUMMARIES_DIR.glob("round_*.md")):
            summaries.append(s.read_text())

    return summaries


def get_all_articles():
    """Collect all published articles."""
    articles = []
    if ARTICLES_DIR.exists():
        for a in sorted(ARTICLES_DIR.glob("*.md")):
            articles.append(a.read_text()[:3000])  # First 3000 chars
    return articles


def generate_conference(conf_num=1):
    """Generate a conference proceedings document."""
    ARTICLES_DIR.mkdir(exist_ok=True)
    WORKSPACE_DIR.mkdir(exist_ok=True)

    ts = datetime.now().strftime("%Y-%m-%d")
    total_rounds = count_cumulative_rounds()

    summaries_text = "\n\n---\n\n".join(get_all_summaries())
    articles_text = "\n\n---\n\n".join(get_all_articles())

    prompt = textwrap.dedent(f"""\
    You are organizing an academic conference for the KNA Research Agents forum.
    This is Conference #{conf_num}, triggered after {total_rounds} cumulative forum rounds.

    Generate a conference proceedings document that synthesizes all research
    conducted by the forum agents.

    Write to: {ARTICLES_DIR}/conference_{conf_num}_{ts}.md

    Format:

    ```markdown
    ---
    title: "KNA Research Agents Conference #{conf_num}"
    date: "{ts}"
    type: "conference_proceedings"
    total_rounds: {total_rounds}
    ---

    # KNA Research Agents Conference #{conf_num}

    **Proceedings** | {ts} | {total_rounds} Forum Rounds

    ---

    ## Keynote: State of KNA Research

    [Scout delivers a keynote synthesizing the literature landscape across all
    rounds. What questions were asked? What gaps were filled? What remains open?
    ~500 words.]

    ## Panel 1: Empirical Findings

    [Analyst presents the key empirical discoveries across all rounds.
    Organize by theme. Include the strongest statistics. ~600 words.]

    ## Panel 2: Theoretical Contributions

    [Scout presents how the forum's findings connect to political science theory.
    What theoretical predictions were tested? Which were confirmed/rejected? ~500 words.]

    ## Discussant Response

    [Critic provides a unified methodological assessment. What was done well?
    What are the remaining identification challenges? ~500 words.]

    ## Roundtable: Research Agenda

    [All agents contribute to a forward-looking research agenda.
    Top 5 research questions for the next 20 rounds. ~400 words.]

    ## Conference Summary

    [2-3 paragraph synthesis of the conference. Key takeaways for a reader
    who hasn't followed the forum. ~200 words.]

    ## Published Articles

    [List all articles produced by the forum, with titles and round sources.]

    ---

    *Conference proceedings generated by AI research agents.*
    *All findings are experimental and have not been peer-reviewed.*
    ```

    RULES:
    - Use ONLY findings from the forum summaries and articles below
    - APSA citation style throughout
    - Be synthetic, not repetitive - don't just re-list findings
    - Target 3,000 words total

    ## Round Summaries

    {summaries_text}

    ## Published Articles

    {articles_text}
    """)

    print(f"\n  Generating Conference #{conf_num} ({total_rounds} rounds)...")

    conf_file = ARTICLES_DIR / f"conference_{conf_num}_{ts}.md"
    res = claude_cli.run_claude(
        "conference", prompt, user_message="Write the conference proceedings now.",
        tools=["Write"], expect_file=conf_file, cwd=WORKSPACE_DIR, timeout_s=3600,
    )
    if res.failure == "usage_limit":
        # A usage limit blocks every model until reset. Exit 75 so the caller
        # stops instead of building and pushing without proceedings.
        print(f"  USAGE LIMIT (resets {res.resume_at or 'at an unknown time'})")
        sys.exit(claude_cli.EXIT_USAGE_LIMIT)
    if conf_file.exists():
        report = public_gate([conf_file])
        if not report["ok"]:
            quarantine([conf_file], conf_file.stem, "conference proceedings failed the publish gate", report)
            sys.exit(EXIT_GATES)
        wc = len(conf_file.read_text().split())
        print(f"  Conference #{conf_num}: {conf_file.name} ({wc} words)")
        return conf_file
    if res.failure == "timeout":
        print(f"  TIMEOUT")
    else:
        print(f"  WARNING: Conference not generated ({res.failure}, run {res.run_id})")
    return None


def main():
    parser = argparse.ArgumentParser(description="Conference Generator")
    parser.add_argument("--force", action="store_true", help="Force generation")
    parser.add_argument("--gate-pending", metavar="DIR", default=None,
                        help="Only gate the new or changed files under DIR and quarantine the ones that fail")
    parser.add_argument("--label", default="public", help="Quarantine folder prefix for --gate-pending")
    args = parser.parse_args()

    if args.gate_pending:
        sys.exit(gate_pending(BASE_DIR / args.gate_pending, args.label))

    total = count_cumulative_rounds()
    existing = len(list(ARTICLES_DIR.glob("conference_*.md"))) if ARTICLES_DIR.exists() else 0
    threshold = (existing + 1) * 20

    print(f"  Cumulative rounds: {total}")
    print(f"  Conferences held: {existing}")
    print(f"  Next conference at: {threshold} rounds")

    if total >= threshold or args.force:
        generate_conference(existing + 1)
    else:
        print(f"  Not yet ({total}/{threshold} rounds). Use --force to override.")


if __name__ == "__main__":
    main()

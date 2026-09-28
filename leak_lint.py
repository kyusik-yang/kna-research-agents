#!/usr/bin/env python3
"""Leak lint for public outputs (FLAG mode in Stage 1).

Forum posts, summaries, papers, the site and agents.json are public. Private
context reached them through absolute paths substituted into prompts and R
scripts, and through agents that could read the maintainer's own notes. This
module reports such strings. In Stage 1 it only flags. Nothing here blocks a
commit or a push.

Two kinds of patterns:

- Generic patterns live in this file. They name no person or private system
  (absolute home and volume paths, ~/Desktop/, .claude/, CLAUDE.md, the
  "Projects:" lines of a literature database dump).
- Maintainer-specific patterns live outside the public tree, in
  knowledge/private/leak_patterns.txt (gitignored, and KNA_LEAK_PATTERNS
  overrides the location). One pattern per line:

      # comment
      some literal string
      re:a regular expression
      block:some literal string     (marked for blocking once Stage 2 enforces)
      allow:re:a regular expression (spans matching this are never reported)

Spans inside a mailto form (a mailto: link or a mailto= query parameter, as in
the OpenAlex and Crossref polite pool) are always allowed.

Usage:
    python3 leak_lint.py [PATH ...]      # default: the public tree
    python3 leak_lint.py --tracked       # every git-tracked text file
    python3 leak_lint.py --json PATH ...
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).parent
PRIVATE_PATTERNS_FILE = BASE_DIR / "knowledge" / "private" / "leak_patterns.txt"

# The public tree the site and repository expose.
PUBLIC_SCOPE = ["forum", "docs", "agents.json", "articles/*.tex", "README.md", "SEASON2.md"]

TEXT_SUFFIXES = {
    ".md", ".html", ".htm", ".json", ".jsonl", ".tex", ".bib", ".R", ".r", ".py",
    ".txt", ".yaml", ".yml", ".sh", ".csv", ".css", ".js", ".xml",
}

# (id, compiled regex). Generic only: nothing here identifies a person.
GENERIC_PATTERNS = [
    ("home_path", re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+/")),
    ("windows_home_path", re.compile(r"[A-Za-z]:\\Users\\[A-Za-z0-9._-]+\\")),
    ("volume_path", re.compile(r"/Volumes/[A-Za-z0-9._-]+/")),
    ("desktop_path", re.compile(r"~/Desktop/")),
    ("claude_config_dir", re.compile(r"\.claude/")),
    ("claude_md", re.compile(r"\bCLAUDE\.md\b")),
    ("litdb_projects_line", re.compile(r"^[ \t>*-]*Projects:[ \t]", re.MULTILINE)),
]

MAILTO_ALLOW = re.compile(r"mailto[:=][^\s\"'<>)&]+", re.IGNORECASE)


def _patterns_path() -> Path:
    env = os.environ.get("KNA_LEAK_PATTERNS")
    return Path(env) if env else PRIVATE_PATTERNS_FILE


def load_private_patterns(path: Path | None = None) -> dict:
    """Read the private denylist. Missing file means no private patterns.

    Returns {"deny": [(id, regex, block)], "allow": [regex]}. The id is
    "private:<line number>" so reports never need to echo the pattern itself.
    """
    path = Path(path) if path else _patterns_path()
    out = {"deny": [], "allow": []}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return out
    for n, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        allow = block = False
        if line.startswith("allow:"):
            allow, line = True, line[len("allow:"):]
        elif line.startswith("block:"):
            block, line = True, line[len("block:"):]
        if line.startswith("re:"):
            try:
                rx = re.compile(line[3:], re.MULTILINE)
            except re.error:
                continue
        else:
            rx = re.compile(re.escape(line))
        if allow:
            out["allow"].append(rx)
        else:
            out["deny"].append((f"private:{n}", rx, block))
    return out


def _line_col(text: str, pos: int, line_starts: list[int]) -> tuple[int, int]:
    lo, hi = 0, len(line_starts) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if line_starts[mid] <= pos:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1, pos - line_starts[lo] + 1


def scan_text(text: str, *, path: str | None = None, private: dict | None = None) -> list[dict]:
    """Return one dict per hit, in text order.

    Each hit: {"path", "line", "col", "pattern_id", "source" ("generic" or
    "private"), "match", "context", "block"}.
    """
    if private is None:
        private = load_private_patterns()
    allowed = [(m.start(), m.end()) for m in MAILTO_ALLOW.finditer(text)]
    for rx in private.get("allow", []):
        allowed += [(m.start(), m.end()) for m in rx.finditer(text)]

    def is_allowed(s: int, e: int) -> bool:
        return any(a <= s and e <= b for a, b in allowed)

    line_starts = [0] + [i + 1 for i, ch in enumerate(text) if ch == "\n"]
    lines = text.split("\n")
    hits = []
    specs = [(pid, rx, False, "generic") for pid, rx in GENERIC_PATTERNS]
    specs += [(pid, rx, block, "private") for pid, rx, block in private.get("deny", [])]
    for pid, rx, block, source in specs:
        for m in rx.finditer(text):
            if m.end() == m.start() or is_allowed(m.start(), m.end()):
                continue
            line, col = _line_col(text, m.start(), line_starts)
            ctx = lines[line - 1].strip()
            if len(ctx) > 200:
                c0 = max(0, col - 80)
                ctx = lines[line - 1][c0:c0 + 200].strip()
            hits.append({
                "path": path,
                "line": line,
                "col": col,
                "pattern_id": pid,
                "source": source,
                "match": m.group(0),
                "context": ctx,
                "block": block,
            })
    hits.sort(key=lambda h: (h["line"], h["col"], h["pattern_id"]))
    return hits


def _expand(paths) -> list[Path]:
    files = []
    for p in paths:
        s = str(p)
        if any(ch in s for ch in "*?["):
            # Relative globs resolve against the repository root.
            if Path(s).is_absolute():
                files += sorted(Path("/").glob(s.lstrip("/")))
            else:
                files += sorted(BASE_DIR.glob(s))
            continue
        p = Path(p)
        if not p.is_absolute() and not p.exists():
            p = BASE_DIR / p
        if p.is_dir():
            files += sorted(f for f in p.rglob("*") if f.is_file() and f.suffix in TEXT_SUFFIXES)
        elif p.is_file():
            files.append(p)
    seen, out = set(), []
    for f in files:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def scan_paths(paths) -> list[dict]:
    """Scan files and directories (text files only, recursively). Never raises
    on unreadable files, which are skipped."""
    private = load_private_patterns()
    hits = []
    for f in _expand(paths):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        try:
            shown = str(f.resolve().relative_to(BASE_DIR.resolve()))
        except ValueError:
            shown = str(f)
        hits += scan_text(text, path=shown, private=private)
    return hits


def tracked_text_files() -> list[Path]:
    try:
        out = subprocess.run(["git", "ls-files"], cwd=BASE_DIR, capture_output=True,
                             text=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return []
    return [BASE_DIR / p for p in out.splitlines() if Path(p).suffix in TEXT_SUFFIXES]


def summarize(hits: list[dict]) -> dict:
    by_pattern = Counter(h["pattern_id"] for h in hits)
    files_by_pattern = {pid: len({h["path"] for h in hits if h["pattern_id"] == pid})
                        for pid in by_pattern}
    return {
        "hits": len(hits),
        "files": len({h["path"] for h in hits}),
        "by_pattern": dict(by_pattern.most_common()),
        "files_by_pattern": files_by_pattern,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Flag private strings in public files (report only).")
    ap.add_argument("paths", nargs="*", help="Files or directories (default: the public tree)")
    ap.add_argument("--tracked", action="store_true", help="Scan every git-tracked text file")
    ap.add_argument("--json", action="store_true", help="Print every hit as JSON")
    args = ap.parse_args(argv)

    if args.tracked:
        hits = scan_paths(tracked_text_files())
    else:
        hits = scan_paths(args.paths or PUBLIC_SCOPE)
    if args.json:
        print(json.dumps(hits, ensure_ascii=False, indent=1))
    else:
        s = summarize(hits)
        print(f"leak_lint (FLAG mode): {s['hits']} hits in {s['files']} files")
        for pid, n in s["by_pattern"].items():
            print(f"  {pid:22s} {n:5d} hits  {s['files_by_pattern'][pid]:4d} files")
    # FLAG mode: report only, never a failing exit status.
    return 0


if __name__ == "__main__":
    sys.exit(main())

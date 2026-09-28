#!/usr/bin/env python3
"""Release check: the one command that must pass before anything is pushed (A3).

run_arc runs it before every push, and a failure keeps the commit local
(arc_status push_blocked) with an alert. Run it by hand before a manual push.

Steps. Any failure makes the exit status 1, and the report lists every failure.
  1. tests    the full pytest suite (python3 -m pytest -q)
  2. leaks    leak_lint over every tracked text file plus the untracked files a
              commit could add (not ignored). Private patterns and absolute
              home, volume or Desktop paths block. Generic mentions that are
              justified (a module that defines or enforces the isolation, a
              test fixture with a placeholder path) are allowed only through
              ALLOWLIST below, each with its reason. A private pattern is
              never allowlisted.
  3. papers   paper_gates.run_all (G5 offline, from the cache) on every paper
              whose tex, pdf, md, bib or disclosure changed against the base
              ref (default origin/main), working tree included. A paper whose
              only change is in its figure scripts gets G6, the gate that reads
              figure scripts (the text of such a paper did not change, and
              papers older than the gates are not re-gated through this path).
  4. site     build_site into a temporary directory. The build must succeed,
              and when a paper changed, the committed docs/articles.html must
              equal the fresh build (a site that still lists an old version of
              a paper is not pushed). Other pages that differ are warnings.
  5. pdfs     docs/articles/<stem>.pdf equals articles/<stem>.pdf, byte for
              byte, for every changed paper

Usage:
    python3 release_check.py                  # every step, human-readable report
    python3 release_check.py --json           # machine-readable (run_arc reads it)
    python3 release_check.py --skip tests     # a quick look; a skipped step never passes
    python3 release_check.py --base origin/main
"""

import argparse
import filecmp
import fnmatch
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STEPS = ("tests", "leaks", "papers", "site", "pdfs")
DEFAULT_BASE = "origin/main"
TESTS_TIMEOUT_S = 2400
SITE_TIMEOUT_S = 900

# Generic leak_lint hits that are justified, each with its reason. Only the
# generic pattern ids listed here can be allowed. A hit from the private
# pattern file always blocks. Reviewed on 2026-09-26 against the tracked tree.
ALLOWLIST = [
    {"paths": ["CLAUDE.md"], "patterns": ["claude_md", "claude_config_dir"],
     "reason": "the repository's orchestration guide names itself and the isolation it relies on"},
    {"paths": ["SEASON2.md", "docs/season2.html"], "patterns": ["claude_md"],
     "reason": "the design note describes the flag that keeps instruction files away from the agents"},
    {"paths": ["forum/070_literature_scout.md", "docs/070_literature_scout.html"], "patterns": ["claude_md"],
     "reason": "the post cites the repository's own topic-gate rule, not a private file"},
    {"paths": ["claude_cli.py", "forum_preflight.py"], "patterns": ["claude_md", "claude_config_dir"],
     "reason": "these modules implement the isolation from instruction files and read the CLI's transcript folder"},
    {"paths": ["leak_lint.py"], "patterns": ["claude_md", "claude_config_dir", "desktop_path"],
     "reason": "the lint defines the generic patterns"},
    {"paths": ["release_check.py"], "patterns": ["claude_md"],
     "reason": "the allowlist names the files it covers"},
    {"paths": ["tests/*.py", "tests/fixtures/*"], "patterns": ["claude_md", "claude_config_dir", "desktop_path"],
     "reason": "test fixtures exercise the lint and the isolation checks"},
    {"paths": ["tests/*.py", "tests/fixtures/*"], "patterns": ["home_path", "volume_path", "windows_home_path"],
     "placeholder_only": True,
     "reason": "synthetic placeholder paths in lint and gate tests (user names in PLACEHOLDER_NAMES)"},
]
# Account or volume names that mark a path as a made-up example.
PLACEHOLDER_NAMES = {"someone", "x", "runner", "example", "user", "alice", "bob", "me", "you", "tester",
                     "some-drive", "name"}
BLOCKING_GENERIC = {"home_path", "windows_home_path", "volume_path", "desktop_path", "claude_config_dir",
                    "claude_md", "litdb_projects_line"}

PAPER_SUFFIXES = (".tex", ".pdf", ".md", ".disclosure.tex", ".disclosure.json")
BIB_RE = re.compile(r"references_r(\d+)\.bib$")
ROUND_RE = re.compile(r"_r(\d+)$")


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(BASE_DIR), capture_output=True, text=True)


def _step(ok: bool, failures: list[str] | None = None, **detail) -> dict:
    return {"ok": ok, "failures": list(failures or []), **detail}


def candidate_files() -> list[str]:
    """Repo-relative paths a push could carry: tracked files plus untracked
    files that are not ignored."""
    out = []
    for args in (("ls-files",), ("ls-files", "--others", "--exclude-standard")):
        r = _git(*args)
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr.strip()[:200]}")
        out += [p for p in r.stdout.splitlines() if p]
    return sorted(set(out))


def changed_paths(base: str) -> list[str]:
    """Paths that differ between the base ref and the working tree, plus
    untracked files that are not ignored. Raises when the base ref is missing,
    because then nothing says which papers a push would change."""
    r = _git("rev-parse", "--verify", "--quiet", base)
    if r.returncode != 0:
        raise RuntimeError(f"base ref {base} not found (fetch it, or pass --base)")
    diff = _git("diff", "--name-only", base)
    if diff.returncode != 0:
        raise RuntimeError(f"git diff against {base} failed: {diff.stderr.strip()[:200]}")
    new = _git("ls-files", "--others", "--exclude-standard")
    return sorted((set(diff.stdout.splitlines()) | set(new.stdout.splitlines())) - {""})


def changed_papers(paths: list[str], articles_dir: Path | None = None, *, figures: bool = False) -> list[str]:
    """Stems of the papers (articles/<stem>.tex that exists) whose own files
    (tex, pdf, md, disclosure) or round bib (references_r<N>.bib) changed.
    With figures=True, the papers whose figure folder changed while none of
    those files did."""
    art = articles_dir or BASE_DIR / "articles"
    stems, rounds, fig_stems = set(), set(), set()
    for p in paths:
        if not p.startswith("articles/"):
            continue
        rest = p[len("articles/"):]
        parts = rest.split("/")
        if parts[0] == "figures":
            if len(parts) >= 3:
                fig_stems.add(parts[1])
            continue
        if len(parts) != 1:
            continue
        m = BIB_RE.fullmatch(parts[0])
        if m:
            rounds.add(int(m.group(1)))
            continue
        for suf in PAPER_SUFFIXES:
            if parts[0].endswith(suf):
                stems.add(parts[0][: -len(suf)])
                break
    if rounds:
        for tex in art.glob("*.tex"):
            m = ROUND_RE.search(tex.stem)
            if m and int(m.group(1)) in rounds and ".disclosure" not in tex.name:
                stems.add(tex.stem)
    chosen = (fig_stems - stems) if figures else stems
    return sorted(s for s in chosen if (art / f"{s}.tex").exists()
                  and not s.startswith(("conference", "template", "post_conference")))


def _placeholder(hit: dict) -> bool:
    """True when a home or volume path names a made-up account (someone, x)."""
    m = re.search(r"(?:Users|home|Volumes)[/\\]([A-Za-z0-9._-]+)[/\\]", hit.get("match") or "")
    return bool(m) and m.group(1).lower() in PLACEHOLDER_NAMES


def allowed(hit: dict, allowlist: list[dict] | None = None) -> str | None:
    """The allowlist reason that covers a leak_lint hit, or None."""
    if hit.get("source") != "generic":
        return None
    for rule in ALLOWLIST if allowlist is None else allowlist:
        if hit.get("pattern_id") not in rule["patterns"]:
            continue
        if not any(fnmatch.fnmatch(hit.get("path") or "", g) for g in rule["paths"]):
            continue
        if rule.get("placeholder_only") and not _placeholder(hit):
            continue
        return rule["reason"]
    return None


# --------------------------------------------------------------------------
# Steps
# --------------------------------------------------------------------------

def step_tests() -> dict:
    try:
        proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                              cwd=str(BASE_DIR), capture_output=True, text=True, timeout=TESTS_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return _step(False, [f"tests: pytest timed out after {TESTS_TIMEOUT_S} s"])
    lines = (proc.stdout or "").strip().splitlines()
    summary = next((l for l in reversed(lines) if re.search(r"\b(passed|failed|error)", l)), "no summary")
    if proc.returncode == 0:
        return _step(True, summary=summary.strip("= "))
    failed = [l.split(" - ")[0].replace("FAILED ", "").replace("ERROR ", "")
              for l in lines if l.startswith(("FAILED ", "ERROR "))]
    return _step(False, [f"tests: {summary.strip('= ')}"] + [f"tests: {f}" for f in failed[:20]],
                 summary=summary.strip("= "))


def step_leaks(files: list[str] | None = None) -> dict:
    import leak_lint
    try:
        rel = candidate_files() if files is None else files
    except RuntimeError as e:
        return _step(False, [f"leaks: {e}"])
    rel = [p for p in rel if Path(p).suffix in leak_lint.TEXT_SUFFIXES and (BASE_DIR / p).is_file()]
    private = leak_lint.load_private_patterns()
    hits = []
    for p in rel:
        try:
            text = (BASE_DIR / p).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits += leak_lint.scan_text(text, path=p, private=private)
    blocking, allowed_hits = [], []
    for h in hits:
        why = allowed(h)
        if why:
            allowed_hits.append({"path": h["path"], "line": h["line"], "pattern_id": h["pattern_id"], "reason": why})
        elif h["source"] == "private" or h["pattern_id"] in BLOCKING_GENERIC:
            blocking.append(h)
    # The report names the file, line and pattern id, never the matched text.
    failures = [f"leaks: {h['path']}:{h['line']} {h['pattern_id']}" for h in blocking]
    return _step(not blocking, failures, files=len(rel), allowed=len(allowed_hits))


def _replication_for(tex_text: str) -> tuple[Path | None, str | None]:
    import paper_gates
    named = sorted(set(paper_gates.ARC_PACKAGE_RE.findall(tex_text)))
    if len(named) == 1 and (BASE_DIR / "replication" / f"arc_{named[0]}").is_dir():
        return BASE_DIR / "replication" / f"arc_{named[0]}", named[0]
    return None, None


def _bib_for(tex: Path, stem: str) -> Path | None:
    import paper_gates
    bib = paper_gates.default_bib(tex)
    if bib is None or not bib.exists():
        m = ROUND_RE.search(stem)
        guess = BASE_DIR / "articles" / f"references_r{m.group(1)}.bib" if m else None
        bib = guess if guess and guess.exists() else bib
    return bib


def step_papers(stems: list[str], figure_stems: list[str] | None = None) -> dict:
    import paper_gates
    failures, reports = [], {}
    for stem in figure_stems or []:
        tex = BASE_DIR / "articles" / f"{stem}.tex"
        bib = _bib_for(tex, stem)
        text = tex.read_text(encoding="utf-8", errors="replace")
        bib_text = bib.read_text(encoding="utf-8", errors="replace") if bib and bib.exists() else None
        g6 = paper_gates.gate_g6(paper_gates._paper_texts(tex, text, bib, bib_text))
        reports[stem] = {"ok": g6["passed"], "gates_run": ["G6"], "figures_only": True}
        if not g6["passed"]:
            hits = [f"{h['path']}:{h['line']} {h['pattern_id']}" for h in g6["details"]["blocking_hits"][:5]]
            failures.append(f"papers: {stem} figure scripts failed G6 ({'; '.join(hits)})")
    for stem in stems:
        tex = BASE_DIR / "articles" / f"{stem}.tex"
        bib = _bib_for(tex, stem)
        pdf = tex.with_suffix(".pdf")
        rep_dir, arc = _replication_for(tex.read_text(encoding="utf-8", errors="replace"))
        try:
            report = paper_gates.run_all(tex, bib, pdf if pdf.exists() else None, replication_dir=rep_dir,
                                         arc=arc, offline=True)
        except Exception as e:
            failures.append(f"papers: {stem} gates did not run ({type(e).__name__}: {e})")
            continue
        reports[stem] = {"ok": report["ok"], "failed_blocking": report["failed_blocking"],
                         "flags": report["flags"]}
        if not report["ok"]:
            items = paper_gates.failing_items(report, limit=3)
            failures.append(f"papers: {stem} failed {', '.join(report['failed_blocking'])}"
                            + (f" ({'; '.join(items)})" if items else ""))
    return _step(not failures, failures, papers=reports)


def build_site_into(out_dir: Path) -> subprocess.CompletedProcess:
    """build_site.main() with DOCS_DIR pointed at out_dir, in a child process."""
    code = ("import pathlib, sys; sys.path.insert(0, sys.argv[1]); import build_site as b; "
            "b.DOCS_DIR = pathlib.Path(sys.argv[2]); b.main()")
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    return subprocess.run([sys.executable, "-c", code, str(BASE_DIR), str(out_dir)], cwd=str(BASE_DIR),
                          capture_output=True, text=True, timeout=SITE_TIMEOUT_S)


def step_site(stems: list[str]) -> dict:
    docs = BASE_DIR / "docs"
    with tempfile.TemporaryDirectory(prefix="kna_release_site_") as td:
        out = Path(td) / "docs"
        try:
            proc = build_site_into(out)
        except subprocess.TimeoutExpired:
            return _step(False, [f"site: build timed out after {SITE_TIMEOUT_S} s"])
        if proc.returncode != 0 or not (out / "index.html").exists():
            tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-1:] or ["no output"]
            return _step(False, [f"site: build into a temporary directory failed ({tail[0][:200]})"])
        stale = sorted(p.name for p in out.glob("*.html")
                       if not (docs / p.name).exists() or not filecmp.cmp(p, docs / p.name, shallow=False))
    failures = []
    if stems and "articles.html" in stale:
        failures.append("site: docs/articles.html is not what build_site makes from the current articles "
                        "(run python3 build_site.py and commit docs/)")
    warnings = [f"site: docs/{n} differs from a fresh build" for n in stale if n != "articles.html" or not stems]
    return _step(not failures, failures, stale_pages=len(stale), warnings=warnings[:30])


def step_pdfs(stems: list[str]) -> dict:
    failures = []
    for stem in stems:
        src = BASE_DIR / "articles" / f"{stem}.pdf"
        if not src.exists():
            continue
        dst = BASE_DIR / "docs" / "articles" / f"{stem}.pdf"
        if not dst.exists():
            failures.append(f"pdfs: docs/articles/{stem}.pdf is missing (run python3 build_site.py)")
        elif not filecmp.cmp(src, dst, shallow=False):
            failures.append(f"pdfs: docs/articles/{stem}.pdf differs from articles/{stem}.pdf "
                            f"(run python3 build_site.py)")
    return _step(not failures, failures, checked=len(stems))


# --------------------------------------------------------------------------
# Run
# --------------------------------------------------------------------------

def run(base: str = DEFAULT_BASE, skip: tuple = ()) -> dict:
    steps: dict = {}
    try:
        paths = changed_paths(base)
        stems, fig_stems = changed_papers(paths), changed_papers(paths, figures=True)
        base_error = None
    except RuntimeError as e:
        stems, fig_stems, base_error = [], [], str(e)
    for name in STEPS:
        if name in skip:
            steps[name] = _step(False, [f"{name}: skipped"], skipped=True)
            continue
        if name in ("papers", "pdfs") and base_error:
            steps[name] = _step(False, [f"{name}: {base_error}"])
            continue
        fn = {"tests": step_tests, "leaks": step_leaks, "papers": lambda: step_papers(stems, fig_stems),
              "site": lambda: step_site(stems), "pdfs": lambda: step_pdfs(stems)}[name]
        try:
            steps[name] = fn()
        except Exception as e:  # a crashed step is a failed step
            steps[name] = _step(False, [f"{name}: crashed ({type(e).__name__}: {e})"])
    failures = [f for s in steps.values() for f in s["failures"]]
    return {"ok": all(s["ok"] for s in steps.values()), "failures": failures, "base": base,
            "changed_papers": stems, "figure_only_papers": fig_stems, "steps": steps,
            "ts": datetime.now().isoformat(timespec="seconds")}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Everything that must pass before a push")
    ap.add_argument("--base", default=DEFAULT_BASE, help="ref the push goes to (default origin/main)")
    ap.add_argument("--skip", action="append", default=[], choices=STEPS,
                    help="skip a step for a quick look (the result then never passes)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    report = run(args.base, tuple(args.skip))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    else:
        print(f"release_check against {report['base']}: {'PASS' if report['ok'] else 'FAIL'}")
        print(f"  changed papers: {', '.join(report['changed_papers']) or 'none'}")
        if report.get("figure_only_papers"):
            print(f"  figure scripts only (G6): {', '.join(report['figure_only_papers'])}")
        for name, s in report["steps"].items():
            state = "skipped" if s.get("skipped") else ("ok" if s["ok"] else "FAIL")
            extra = s.get("summary") or ""
            print(f"  {name:7s} {state}{f'  ({extra})' if extra else ''}")
            for f in s["failures"]:
                print(f"    - {f}")
            for w in s.get("warnings") or []:
                print(f"    . {w}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

"""release_check.py (A3): the pre-push check. The pytest step and the site
build never run for real here (they are faked or pointed at scratch folders),
the leak step scans synthetic files in tmp_path with a scratch private
pattern file, and git commands run only in scratch repositories."""

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import release_check as rc  # noqa: E402

GIT_ENV = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "t",
           "GIT_AUTHOR_EMAIL": "t@example.org", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.org"}
# Built at run time so this file carries no absolute home path of its own.
HOME = "/" + "Users"


def _git(repo: Path, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


@pytest.fixture
def scratch(tmp_path, monkeypatch):
    for k, v in GIT_ENV.items():
        monkeypatch.setenv(k, v)
    repo = tmp_path / "repo"
    (repo / "articles" / "figures" / "2026-10-01_r33").mkdir(parents=True)
    (repo / "docs" / "articles").mkdir(parents=True)
    monkeypatch.setattr(rc, "BASE_DIR", repo)
    patterns = tmp_path / "private_patterns.txt"
    patterns.write_text("# scratch denylist\nsecret-notebook-name\n", encoding="utf-8")
    monkeypatch.setenv("KNA_LEAK_PATTERNS", str(patterns))
    return repo


def test_changed_papers_from_paths(scratch):
    art = scratch / "articles"
    for stem in ("2026-10-01_r33", "2026-08-24_r30", "2026-04-18_r18"):
        (art / f"{stem}.tex").write_text("\\title{x}", encoding="utf-8")
    (art / "conference_1.tex").write_text("x", encoding="utf-8")
    paths = ["articles/2026-10-01_r33.pdf", "articles/references_r30.bib",
             "articles/figures/2026-04-18_r18/fig_1.R", "articles/figures/2026-10-01_r33/fig_2.R",
             "articles/figures/fig_1.R", "articles/conference_1.tex", "articles/2026-09-01_r99.md",
             "forum/091_literature_scout.md"]
    assert rc.changed_papers(paths) == ["2026-08-24_r30", "2026-10-01_r33"]
    # r33's figure change is covered by its full gate run, r18 changed only in figure scripts.
    assert rc.changed_papers(paths, figures=True) == ["2026-04-18_r18"]


def test_changed_paths_include_committed_uncommitted_and_untracked_files(scratch):
    _git(scratch, "init", "-q", "-b", "main")
    (scratch / "articles" / "a_r1.tex").write_text("v1", encoding="utf-8")
    (scratch / "articles" / "b_r2.tex").write_text("v1", encoding="utf-8")
    (scratch / ".gitignore").write_text("workspace/\n", encoding="utf-8")
    _git(scratch, "add", ".")
    _git(scratch, "commit", "-q", "-m", "base")
    _git(scratch, "update-ref", "refs/remotes/origin/main", "HEAD")
    (scratch / "articles" / "a_r1.tex").write_text("v2", encoding="utf-8")
    _git(scratch, "commit", "-qam", "local commit")
    (scratch / "articles" / "b_r2.tex").write_text("v2", encoding="utf-8")      # uncommitted
    (scratch / "articles" / "c_r3.tex").write_text("new", encoding="utf-8")     # untracked
    (scratch / "workspace").mkdir()
    (scratch / "workspace" / "x_r4.tex").write_text("ignored", encoding="utf-8")
    assert rc.changed_paths("origin/main") == ["articles/a_r1.tex", "articles/b_r2.tex", "articles/c_r3.tex"]
    with pytest.raises(RuntimeError):
        rc.changed_paths("origin/nope")


def test_allowlist_rules():
    def hit(path, pid, match="", source="generic"):
        return {"path": path, "pattern_id": pid, "match": match, "source": source}
    assert rc.allowed(hit("SEASON2.md", "claude_md"))
    assert rc.allowed(hit("forum/051_critic.md", "claude_md")) is None      # not justified
    assert rc.allowed(hit("tests/test_x.py", "home_path", HOME + "/someone/")) is not None
    assert rc.allowed(hit("tests/test_x.py", "home_path", HOME + "/realperson/")) is None
    assert rc.allowed(hit("run_forum.py", "home_path", HOME + "/someone/")) is None
    assert rc.allowed(hit("CLAUDE.md", "private:3", source="private")) is None   # never allowlisted
    for rule in rc.ALLOWLIST:
        assert rule["reason"] and set(rule["patterns"]) <= rc.BLOCKING_GENERIC
        for g in rule["paths"]:
            if not any(ch in g for ch in "*?["):
                assert (ROOT / g).exists(), f"allowlisted path {g} does not exist"


def test_leak_step_blocks_private_and_home_paths_and_names_no_match(scratch):
    files = {
        "forum/091_data_analyst.md": "Data from $KBL_DATA/members_22.parquet.\n",
        "forum/092_critic.md": "As the secret-notebook-name says.\n",
        "docs/093.html": f"<p>{HOME}/realperson/kna/data</p>\n",
        "tests/test_fake.py": f'LEAK = "{HOME}/someone/Desktop/notes.md"\n',
        "SEASON2.md": "Agents run with CLAUDE_CODE_DISABLE_CLAUDE_MDS so CLAUDE.md is not loaded.\n",
    }
    for rel, text in files.items():
        (scratch / rel).parent.mkdir(parents=True, exist_ok=True)
        (scratch / rel).write_text(text, encoding="utf-8")
    r = rc.step_leaks(sorted(files))
    assert r["ok"] is False
    assert sorted(r["failures"]) == ["leaks: docs/093.html:1 home_path", "leaks: forum/092_critic.md:1 private:2"]
    assert all("secret-notebook-name" not in f and "realperson" not in f for f in r["failures"])
    assert r["allowed"] >= 2
    del files["forum/092_critic.md"], files["docs/093.html"]
    assert rc.step_leaks(sorted(files))["ok"] is True


def test_pdf_step_compares_bytes(scratch):
    (scratch / "articles" / "p_r33.pdf").write_bytes(b"%PDF v2")
    (scratch / "articles" / "q_r34.pdf").write_bytes(b"%PDF new")
    (scratch / "docs" / "articles" / "p_r33.pdf").write_bytes(b"%PDF v1")
    r = rc.step_pdfs(["p_r33", "q_r34", "no_pdf_r35"])
    assert r["ok"] is False and len(r["failures"]) == 2
    assert "differs" in r["failures"][0] and "missing" in r["failures"][1]
    (scratch / "docs" / "articles" / "p_r33.pdf").write_bytes(b"%PDF v2")
    (scratch / "docs" / "articles" / "q_r34.pdf").write_bytes(b"%PDF new")
    assert rc.step_pdfs(["p_r33", "q_r34"])["ok"] is True


def test_site_step_needs_a_build_and_a_current_articles_page(scratch, monkeypatch):
    (scratch / "docs" / "articles.html").write_text("old list", encoding="utf-8")
    (scratch / "docs" / "index.html").write_text("home", encoding="utf-8")

    def build(out, articles="new list", ok=True):
        def fake(out_dir):
            if ok:
                out_dir.mkdir(parents=True)
                (out_dir / "index.html").write_text("home", encoding="utf-8")
                (out_dir / "articles.html").write_text(articles, encoding="utf-8")
                (out_dir / "forum.html").write_text("forum", encoding="utf-8")
            return SimpleNamespace(returncode=0 if ok else 1, stdout="", stderr="" if ok else "KeyError: 'x'")
        return fake
    monkeypatch.setattr(rc, "build_site_into", build(None))
    r = rc.step_site(["p_r33"])
    assert r["ok"] is False and "docs/articles.html" in r["failures"][0]
    assert r["warnings"] == ["site: docs/forum.html differs from a fresh build"]
    assert rc.step_site([])["ok"] is True                    # no paper changed: stale pages only warn
    (scratch / "docs" / "articles.html").write_text("new list", encoding="utf-8")
    assert rc.step_site(["p_r33"])["ok"] is True
    monkeypatch.setattr(rc, "build_site_into", build(None, ok=False))
    r = rc.step_site([])
    assert r["ok"] is False and "KeyError" in r["failures"][0]


def test_site_build_writes_only_into_the_temporary_directory(tmp_path, monkeypatch):
    """The real child-process build with a stand-in build_site module."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "build_site.py").write_text(
        "from pathlib import Path\nDOCS_DIR = Path(__file__).parent / 'docs'\n"
        "def main():\n    DOCS_DIR.mkdir(exist_ok=True)\n    (DOCS_DIR / 'index.html').write_text('x')\n",
        encoding="utf-8")
    monkeypatch.setattr(rc, "BASE_DIR", repo)
    out = tmp_path / "out" / "docs"
    assert rc.build_site_into(out).returncode == 0
    assert (out / "index.html").exists() and not (repo / "docs").exists()


def test_tests_step_reports_the_failed_tests(monkeypatch):
    out = "....F\nFAILED tests/test_a.py::test_one - assert 1 == 2\n2 failed, 610 passed in 80.0s\n"
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=1, stdout=out, stderr=""))
    r = rc.step_tests()
    assert r["ok"] is False and r["failures"][0] == "tests: 2 failed, 610 passed in 80.0s"
    assert "tests: tests/test_a.py::test_one" in r["failures"]
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout="612 passed in 9s\n",
                                                                          stderr=""))
    assert rc.step_tests() == {"ok": True, "failures": [], "summary": "612 passed in 9s"}


def _fake_steps(monkeypatch, fail=()):
    calls = []
    for name in rc.STEPS:
        def make(n):
            def fn(*a):
                calls.append(n)
                return rc._step(n not in fail, [f"{n}: broke"] if n in fail else [])
            return fn
        monkeypatch.setattr(rc, f"step_{name}", make(name))
    monkeypatch.setattr(rc, "changed_paths", lambda base: ["articles/p_r33.tex"])
    monkeypatch.setattr(rc, "changed_papers", lambda paths, figures=False: [] if figures else ["p_r33"])
    return calls


def test_run_collects_every_failure_and_exits_nonzero(monkeypatch, capsys):
    calls = _fake_steps(monkeypatch, fail=("leaks", "pdfs"))
    assert rc.main(["--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert calls == list(rc.STEPS)                            # a failure does not stop the later steps
    assert report["ok"] is False and report["failures"] == ["leaks: broke", "pdfs: broke"]
    assert report["changed_papers"] == ["p_r33"]
    _fake_steps(monkeypatch)
    assert rc.main([]) == 0
    assert "PASS" in capsys.readouterr().out


def test_skipped_or_crashed_steps_never_pass(monkeypatch):
    _fake_steps(monkeypatch)
    r = rc.run(skip=("tests",))
    assert r["ok"] is False and r["failures"] == ["tests: skipped"]
    monkeypatch.setattr(rc, "step_site", lambda stems: 1 / 0)
    r = rc.run()
    assert r["ok"] is False and r["failures"][0].startswith("site: crashed (ZeroDivisionError")


def test_missing_base_ref_fails_the_paper_steps(monkeypatch):
    _fake_steps(monkeypatch)

    def no_base(base):
        raise RuntimeError(f"base ref {base} not found")
    monkeypatch.setattr(rc, "changed_paths", no_base)
    r = rc.run()
    assert r["ok"] is False
    assert [f for f in r["failures"]] == ["papers: base ref origin/main not found", "pdfs: base ref origin/main not found"]


PAPER_TEX = r"""\documentclass{article}
\title{A Scratch Paper}
\begin{document}
\maketitle
First-term members pass bills at the rate of re-elected members \citep{padro2006}.
%s
\bibliography{references_r33}
\end{document}
"""
PAPER_BIB = """@article{padro2006,
  author = {Padro i Miquel, Gerard and Snyder, James M.},
  title = {Legislative Effectiveness and Legislative Careers},
  journal = {Legislative Studies Quarterly},
  year = {2006},
  doi = {10.3162/036298006X201940}
}
"""


def test_paper_step_runs_the_blocking_gates_on_a_changed_paper(scratch):
    """The paper step on a synthetic paper in the scratch repository (never
    on the live papers, which other work may be editing). A clean paper
    passes. The same paper naming a replication package whose verify has not
    passed fails G4, and the failure names the paper and the gate."""
    art = scratch / "articles"
    (art / "references_r33.bib").write_text(PAPER_BIB, encoding="utf-8")
    tex = art / "2026-10-01_r33.tex"
    tex.write_text(PAPER_TEX % "", encoding="utf-8")
    r = rc.step_papers(["2026-10-01_r33"])
    assert r["ok"] is True, r["failures"]
    assert r["papers"]["2026-10-01_r33"]["failed_blocking"] == []
    pkg = scratch / "replication" / "arc_9"
    pkg.mkdir(parents=True)
    (pkg / "MANIFEST.json").write_text(json.dumps({"arc": 9, "build": {"ok": True}, "verify": {"passed": None}}),
                                       encoding="utf-8")
    tex.write_text(PAPER_TEX % r"The replication package \texttt{replication/arc\_9} reruns every table.",
                   encoding="utf-8")
    r = rc.step_papers(["2026-10-01_r33"])
    assert r["ok"] is False and r["papers"]["2026-10-01_r33"]["failed_blocking"] == ["G4"]
    assert r["failures"][0].startswith("papers: 2026-10-01_r33 failed G4")

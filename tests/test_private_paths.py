#!/usr/bin/env python3
"""Private locations stay out of the public tree (check finding B2, 2026-09-26).

build_site.py and weekly_update.sh find the maintainer's literature vector DB
the way scripts/litdb.sh does, from the environment or the gitignored
knowledge/private/litdb_path.txt, so no home path or private name is written
into a tracked file. The tree-wide test reads the private denylist when it is
present on this machine and reports only paths and pattern ids, never the
matched text. Nothing here writes outside tmp_path.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build_site as bs  # noqa: E402
import leak_lint  # noqa: E402

PRIVATE_FILE = ROOT / "knowledge" / "private" / "leak_patterns.txt"


@pytest.fixture
def no_litdb_env(monkeypatch):
    monkeypatch.delenv("KNA_LITDB_STORE", raising=False)
    monkeypatch.delenv("KNA_LITDB_TOOL", raising=False)
    return monkeypatch


def _tool_with_store(tmp_path: Path, stores=("db.lance",)) -> Path:
    tools = tmp_path / "tools"
    tools.mkdir()
    tool = tools / "vector_tool.py"
    tool.write_text("print('stub')\n")
    for name in stores:
        (tools / name).mkdir()
    return tool


# ---------------------------------------------------------------------------
# build_site.litdb_store_path
# ---------------------------------------------------------------------------

def test_litdb_store_env_wins(tmp_path, no_litdb_env):
    tool = _tool_with_store(tmp_path)
    no_litdb_env.setenv("KNA_LITDB_TOOL", str(tool))
    no_litdb_env.setenv("KNA_LITDB_STORE", str(tmp_path / "elsewhere.lance"))
    assert bs.litdb_store_path() == tmp_path / "elsewhere.lance"


def test_litdb_store_beside_tool_from_path_file(tmp_path, no_litdb_env):
    tool = _tool_with_store(tmp_path)
    pfile = tmp_path / "litdb_path.txt"
    pfile.write_text(f"# the tool, private\n\n   {tool}   \n")
    no_litdb_env.setattr(bs, "LITDB_PATH_FILE", pfile)
    assert bs.litdb_store_path() == tool.parent / "db.lance"
    # KNA_LITDB_TOOL takes precedence over the file, as in scripts/litdb.sh.
    other = tmp_path / "other"
    other.mkdir()
    (other / "t.py").write_text("")
    (other / "x.lance").mkdir()
    no_litdb_env.setenv("KNA_LITDB_TOOL", str(other / "t.py"))
    assert bs.litdb_store_path() == other / "x.lance"


def test_litdb_store_unconfigured_or_ambiguous_is_none(tmp_path, no_litdb_env):
    no_litdb_env.setattr(bs, "LITDB_PATH_FILE", tmp_path / "missing.txt")
    assert bs.litdb_store_path() is None
    tool = _tool_with_store(tmp_path, stores=("a.lance", "b.lance"))
    no_litdb_env.setenv("KNA_LITDB_TOOL", str(tool))
    assert bs.litdb_store_path() is None


# ---------------------------------------------------------------------------
# weekly_update.sh
# ---------------------------------------------------------------------------

@pytest.fixture
def weekly_repo(tmp_path):
    repo = tmp_path / "repo"
    (repo / "knowledge" / "private").mkdir(parents=True)
    shutil.copy2(ROOT / "weekly_update.sh", repo / "weekly_update.sh")
    (repo / "collect_abstracts.py").write_text("print('COLLECT ran')\n")
    tool = tmp_path / "tools" / "vector_tool.py"
    tool.parent.mkdir()
    tool.write_text("import sys\nprint('TOOL', ' '.join(sys.argv[1:]))\n")
    return repo, tool


def _run_weekly(repo: Path, **env_extra) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k not in ("KNA_LITDB_TOOL",)}
    env.update(env_extra)
    return subprocess.run(["bash", str(repo / "weekly_update.sh")], capture_output=True, text=True,
                          env=env, timeout=60)


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash missing")
def test_weekly_update_finds_the_tool_like_litdb(weekly_repo):
    repo, tool = weekly_repo
    (repo / "knowledge" / "private" / "litdb_path.txt").write_text(f"# private\n\n  {tool}\n")
    r = _run_weekly(repo)
    assert r.returncode == 0, r.stderr
    tool_lines = [ln for ln in r.stdout.splitlines() if ln.startswith("TOOL")]
    assert tool_lines[0] == "TOOL update" and tool_lines[-1] == "TOOL stats"
    assert any(ln.startswith("TOOL ingest-jsonl ") and ln.endswith("knowledge/abstracts.jsonl")
               for ln in tool_lines)
    assert "COLLECT ran" in r.stdout
    # The environment variable wins over the file.
    alt = tool.parent / "alt_tool.py"
    alt.write_text("print('ALT')\n")
    assert "ALT" in _run_weekly(repo, KNA_LITDB_TOOL=str(alt)).stdout


@pytest.mark.skipif(shutil.which("bash") is None, reason="bash missing")
def test_weekly_update_stops_when_no_tool_is_configured(weekly_repo):
    repo, _ = weekly_repo
    r = _run_weekly(repo)
    assert r.returncode == 3
    assert "COLLECT ran" not in r.stdout and "KNA_LITDB_TOOL" in r.stderr


# ---------------------------------------------------------------------------
# No private string in the scripts or the public tree
# ---------------------------------------------------------------------------

def _private_or_path_hits(rel: str) -> list[tuple[int, str]]:
    text = (ROOT / rel).read_text(encoding="utf-8")
    return [(h["line"], h["pattern_id"]) for h in leak_lint.scan_text(text, path=rel)
            if h["source"] == "private" or h["pattern_id"] in ("home_path", "desktop_path", "volume_path")]


@pytest.mark.parametrize("rel", ["build_site.py", "weekly_update.sh"])
def test_site_and_weekly_scripts_name_no_private_location(rel):
    assert _private_or_path_hits(rel) == []


def _tree_files() -> list[str]:
    out = []
    for args in (["ls-files", "-z"], ["ls-files", "-z", "--others", "--exclude-standard"]):
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
        if r.returncode != 0:
            pytest.skip("not a git checkout")
        out += [p for p in r.stdout.decode("utf-8", "replace").split("\0") if p]
    return sorted(set(out))


@pytest.mark.skipif(not PRIVATE_FILE.exists(), reason="private denylist not present on this machine")
def test_tree_about_to_be_committed_has_no_private_literal():
    """Tracked files and untracked files that are not ignored (the next
    commit) hold no string from the private denylist. Every file without a
    NUL byte in its first 8 KiB is read, the rule git-filter-repo uses for text."""
    private = leak_lint.load_private_patterns(PRIVATE_FILE)
    bad = []
    for rel in _tree_files():
        p = ROOT / rel
        if not p.is_file() or p.is_symlink():
            continue
        data = p.read_bytes()
        if b"\0" in data[:8192]:
            continue
        for h in leak_lint.scan_text(data.decode("utf-8", "replace"), path=rel, private=private):
            if h["source"] == "private":
                bad.append(f"{rel}:{h['line']} {h['pattern_id']}")
    assert not bad, bad

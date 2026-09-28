"""Leak lint (FLAG mode): generic patterns in code, maintainer-specific
patterns only in the gitignored private file, mailto forms allowed.

No maintainer-specific string may appear in this file. Tests that need one
read the private list at run time and skip when it is absent."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import leak_lint as ll  # noqa: E402

NO_PRIVATE = {"deny": [], "allow": []}
PRIVATE_FILE = ROOT / "knowledge" / "private" / "leak_patterns.txt"


def ids(hits):
    return [h["pattern_id"] for h in hits]


def test_home_path_is_flagged():
    text = "Data loaded from /Users/someone/kna/data/processed/bills.parquet\n"
    hits = ll.scan_text(text, private=NO_PRIVATE)
    assert ids(hits) == ["home_path"]
    assert hits[0]["line"] == 1 and hits[0]["source"] == "generic"
    assert hits[0]["block"] is False


@pytest.mark.parametrize("text,pid", [
    ("Sys.setenv(KBL_DATA = '/home/runner/data')", "home_path"),
    ("open('/Volumes/some-drive/research/x.parquet')", "volume_path"),
    ("python3 ~/Desktop/tools/search.py", "desktop_path"),
    ("see ~/.claude/projects/abc.jsonl", "claude_config_dir"),
    ("no new sign required per CLAUDE.md", "claude_md"),
    ("Title: X\nProjects: alpha, beta\n", "litdb_projects_line"),
])
def test_generic_patterns(text, pid):
    assert pid in ids(ll.scan_text(text, private=NO_PRIVATE))


def test_clean_post_passes():
    text = (
        "# Prediction to Test\n\nFirst-term members sponsor 5 percentage points fewer bills.\n"
        "Data: $KBL_DATA/master_bills_17-22.parquet (repo-relative scripts in workspace/r31/).\n"
        "Crossref: https://api.crossref.org/works/10.2307/1958780\n"
    )
    assert ll.scan_text(text, private=NO_PRIVATE) == []


def test_mailto_forms_are_allowlisted(tmp_path):
    pfile = tmp_path / "leak_patterns.txt"
    pfile.write_text("maintainer@example.org\n", encoding="utf-8")
    private = ll.load_private_patterns(pfile)
    ok = (
        "https://api.openalex.org/works?search=x&mailto=maintainer@example.org\n"
        "curl 'https://api.crossref.org/works?rows=5&mailto=maintainer@example.org'\n"
        '<a href="mailto:maintainer@example.org">Feedback</a>\n'
        "User-Agent: Forum/1.0 (mailto:maintainer@example.org)\n"
    )
    assert ll.scan_text(ok, private=private) == []
    bad = "Contact maintainer@example.org for the private notes.\n"
    assert ids(ll.scan_text(bad, private=private)) == ["private:1"]


def test_private_file_format(tmp_path):
    pfile = tmp_path / "leak_patterns.txt"
    pfile.write_text(
        "# comment line\n"
        "\n"
        "acme-private-vault\n"
        "re:secret[-_ ]?project-\\d+\n"
        "block:acme-drive\n"
        "re:([unclosed\n"
        "allow:re:acme-private-vault/public-mirror\n",
        encoding="utf-8",
    )
    private = ll.load_private_patterns(pfile)
    assert len(private["deny"]) == 3          # the invalid regex is skipped
    assert len(private["allow"]) == 1
    text = (
        "Add the paper to acme-private-vault under the index.\n"
        "See secret-project-7 and acme-drive.\n"
        "Mirror: acme-private-vault/public-mirror is fine.\n"
    )
    hits = ll.scan_text(text, private=private)
    got = [(h["line"], h["pattern_id"], h["block"]) for h in hits]
    assert got == [(1, "private:3", False), (2, "private:4", False), (2, "private:5", True)]
    # Reports carry the line number of the pattern, never the pattern text.
    assert all(h["pattern_id"].startswith("private:") for h in hits)


def test_missing_private_file_means_generic_only(tmp_path, monkeypatch):
    monkeypatch.setenv("KNA_LEAK_PATTERNS", str(tmp_path / "absent.txt"))
    assert ll.load_private_patterns() == NO_PRIVATE
    assert ids(ll.scan_text("acme-private-vault /Users/x/y")) == ["home_path"]


def test_env_override_for_private_file(tmp_path, monkeypatch):
    pfile = tmp_path / "p.txt"
    pfile.write_text("acme-private-vault\n", encoding="utf-8")
    monkeypatch.setenv("KNA_LEAK_PATTERNS", str(pfile))
    assert ids(ll.scan_text("stored in acme-private-vault")) == ["private:1"]


def test_scan_paths_recurses_text_files_only(tmp_path, monkeypatch):
    monkeypatch.setenv("KNA_LEAK_PATTERNS", str(tmp_path / "absent.txt"))
    d = tmp_path / "forum"
    (d / "sub").mkdir(parents=True)
    (d / "001_critic.md").write_text("clean\n", encoding="utf-8")
    (d / "sub" / "fig_1.R").write_text("x <- '/Users/someone/data'\n", encoding="utf-8")
    (d / "sub" / "fig_1.pdf").write_bytes(b"%PDF /Users/someone/ binary")
    hits = ll.scan_paths([d])
    assert [Path(h["path"]).name for h in hits] == ["fig_1.R"]
    s = ll.summarize(hits)
    assert s["by_pattern"] == {"home_path": 1} and s["files"] == 1


def test_flag_mode_never_fails(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KNA_LEAK_PATTERNS", str(tmp_path / "absent.txt"))
    f = tmp_path / "post.md"
    f.write_text("/Users/someone/kna/data\n", encoding="utf-8")
    assert ll.main([str(f)]) == 0
    assert "1 hits" in capsys.readouterr().out


def test_public_module_hard_codes_no_private_pattern():
    """Maintainer-specific strings live only in the private file."""
    if not PRIVATE_FILE.exists():
        pytest.skip("private denylist not present on this machine")
    private = ll.load_private_patterns(PRIVATE_FILE)
    for rel in ("leak_lint.py", "tests/test_leak_lint.py"):
        text = (ROOT / rel).read_text(encoding="utf-8")
        hits = [h for h in ll.scan_text(text, private=private) if h["source"] == "private"]
        assert hits == [], (rel, [(h["line"], h["pattern_id"]) for h in hits])


def test_private_file_is_git_ignored():
    import subprocess
    if not (ROOT / ".git").exists():
        pytest.skip("not a git checkout")
    r = subprocess.run(["git", "check-ignore", "-q", "knowledge/private/leak_patterns.txt"],
                       cwd=ROOT)
    assert r.returncode == 0


def test_private_literal_in_synthetic_line_is_flagged():
    """A plain literal from the private list is flagged inside a synthetic
    sentence. The public post that used to serve as the example was redacted
    on 2026-09-26, so the literal is read from the private file at run time."""
    if not PRIVATE_FILE.exists():
        pytest.skip("private denylist not present on this machine")
    literals = [l.strip() for l in PRIVATE_FILE.read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.strip().startswith(("#", "re:", "allow:", "block:"))]
    if not literals:
        pytest.skip("private denylist has no plain literal")
    line = f"These papers should be added to the {literals[0]} pipeline before the paper goes out."
    hits = ll.scan_text(line, private=ll.load_private_patterns(PRIVATE_FILE))
    assert any(h["source"] == "private" for h in hits)

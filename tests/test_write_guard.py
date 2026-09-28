"""write_guard (M03 step 1): external writes into watched sibling repos and
the data directory are detected, reported and written to a patch file,
including on repos that were already dirty. Nothing is reverted."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import write_guard  # noqa: E402


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@example.com", "-c", "user.name=t", *args],
                   check=True, capture_output=True)


@pytest.fixture
def env(tmp_path, monkeypatch):
    base = tmp_path / "forum_repo"
    base.mkdir()
    sib = tmp_path / "sibling"
    sib.mkdir()
    _git(sib, "init", "-q")
    (sib / "CODEBOOK.md").write_text("line 1\n")
    (sib / "keep.txt").write_text("k\n")
    _git(sib, "add", ".")
    _git(sib, "commit", "-q", "-m", "init")
    # already dirty before the run, like kr-hearings-data today
    (sib / "CODEBOOK.md").write_text("line 1\nuncommitted researcher edit\n")
    data = tmp_path / "kbl_data"
    data.mkdir()
    (data / "members.parquet").write_bytes(b"PAR1" * 10)
    (base / "agents.json").write_text(json.dumps({"forum_config": {"watched_repos": ["../sibling"]}}))
    monkeypatch.setattr(write_guard, "BASE_DIR", base)
    monkeypatch.setenv("KBL_DATA", str(data))
    return type("E", (), {"base": base, "sib": sib, "data": data})


def test_watched_locations_from_config(env):
    assert write_guard.watched_repos() == [env.sib.resolve()]
    assert write_guard.watched_data() == [env.data.resolve()]


def test_forum_repo_itself_and_missing_entries_are_skipped(env):
    cfg = {"watched_repos": [".", "../does_not_exist", "../sibling"]}
    assert write_guard.watched_repos(cfg) == [env.sib.resolve()]


def test_clean_run_reports_nothing(env):
    before = write_guard.guard_before()
    assert write_guard.guard_after(before, "run_clean") == []
    assert not (env.base / "logs" / "external_writes" / "run_clean.patch").exists()


def test_edit_of_already_dirty_file_is_caught_with_patch(env):
    before = write_guard.guard_before()
    (env.sib / "CODEBOOK.md").write_text("line 1\nuncommitted researcher edit\nagent caveat added\n")
    changes = write_guard.guard_after(before, "r26_data_analyst_x")
    kinds = {c["kind"] for c in changes}
    assert "tracked_diff_changed" in kinds
    patch = env.base / "logs" / "external_writes" / "r26_data_analyst_x.patch"
    assert patch.exists()
    text = patch.read_text()
    assert "agent caveat added" in text and "Nothing was reverted" in text
    assert all(c["patch"] == str(patch) for c in changes)
    # no automatic revert
    assert "agent caveat added" in (env.sib / "CODEBOOK.md").read_text()


def test_untracked_file_and_commit_are_caught(env):
    before = write_guard.guard_before()
    (env.sib / "new_notes.md").write_text("x\n")
    changes = write_guard.guard_after(before, "run_untracked")
    assert {"where": str(env.sib.resolve()), "kind": "untracked_added", "path": "new_notes.md"} \
        in [{k: c[k] for k in ("where", "kind", "path")} for c in changes]
    before = write_guard.guard_before()
    _git(env.sib, "add", "new_notes.md")
    _git(env.sib, "commit", "-q", "-m", "agent commit")
    kinds = {c["kind"] for c in write_guard.guard_after(before, "run_commit")}
    assert "head_moved" in kinds


def test_rscript_writing_into_data_dir_is_caught(env):
    """A figure script that writes outside the repo (the Paper E repair)."""
    before = write_guard.guard_before()
    script = f"open({str(env.data / 'member_info_17_22.parquet')!r}, 'wb').write(b'PAR1')"
    subprocess.run([sys.executable, "-c", script], check=True)
    (env.data / "members.parquet").write_bytes(b"PAR1" * 11)
    changes = write_guard.guard_after(before, "draft_fig_1")
    got = {(c["kind"], c["path"]) for c in changes}
    assert ("data_added", "member_info_17_22.parquet") in got
    assert ("data_modified", "members.parquet") in got


def test_non_git_watched_dir_uses_file_manifest(env, tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    before = write_guard.snapshot(repos=[plain], data=[])
    (plain / "a.txt").write_text("a")
    after = write_guard.snapshot(repos=[plain], data=[])
    assert write_guard.compare(before, after) == [
        {"where": str(plain), "kind": "file_added", "path": "a.txt"}]

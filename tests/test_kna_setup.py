"""run_forum.check_kna_setup runs for real (not monkeypatched) against a stub
kna CLI on PATH and a scratch KBL_DATA. Guards the merge bug where the check
referred to module constants that v2.1 had removed."""
import os

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

import run_forum


def _stub_cli(tmp_path, version):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    cli = bin_dir / "kna"
    cli.write_text(f"#!/bin/sh\necho 'kna, version {version}'\n", encoding="utf-8")
    cli.chmod(0o755)
    return bin_dir


def _data(tmp_path, columns):
    data = tmp_path / "kbl"
    data.mkdir()
    pq.write_table(pa.table({c: [1] for c in columns}), data / "members_22.parquet")
    return data


@pytest.fixture
def env(tmp_path, monkeypatch):
    def setup(version="0.7.0", columns=("mona_cd", "term_number")):
        bin_dir = _stub_cli(tmp_path, version)
        monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
        monkeypatch.setenv("KBL_DATA", str(_data(tmp_path, columns)))
    return setup


def test_current_cli_and_data_pass(env):
    env()
    assert run_forum.check_kna_setup("0.7.0") == []


def test_old_cli_is_reported(env):
    env(version="0.6.0")
    problems = run_forum.check_kna_setup("0.7.0")
    assert len(problems) == 1 and "0.6.0" in problems[0]


def test_pre_070_data_is_reported(env):
    env(columns=("mona_cd", "reelection"))
    problems = run_forum.check_kna_setup("0.7.0")
    assert len(problems) == 1 and "term_number" in problems[0]


def test_missing_kbl_data_is_reported(env, monkeypatch):
    env()
    monkeypatch.delenv("KBL_DATA")
    assert run_forum.check_kna_setup("0.7.0") == [
        "KBL_DATA is not set. Point it at the kna processed-data directory"]

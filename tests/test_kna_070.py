"""kna 0.7.0 compatibility: the Analyst prompt and templates describe the
0.7.0 tables, run_forum.py refuses an older CLI or older data, and the
figure scripts of published papers read the pinned kna v0.6.0 data."""

import json
import re
import stat
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import run_forum  # noqa: E402

KNA_READ = re.compile(r"master_bills|members_|member_info|roll_calls|ideal_points|"
                      r"cosponsorship_edges|assets_wealth|committee_meetings")


def analyst_prompt():
    agents = json.loads((ROOT / "agents.json").read_text(encoding="utf-8"))["agents"]
    return next(a for a in agents if a["id"] == "data_analyst")["prompt"]


def test_analyst_prompt_uses_the_070_api_and_fields():
    p = analyst_prompt()
    assert "from kna.data import BillDB" in p
    assert "db = kna.load()" not in p
    assert "term_number" in p and "seniority" in p
    assert "party_api" in p
    assert "공동발의" in p and "찬성" in p
    assert "roll_calls_16_19_experimental.parquet" in p
    # the removed ideal-point file is only mentioned as removed
    for line in p.splitlines():
        if "dw_ideal_points_20_22.csv" in line:
            assert "no longer exist" in line


def test_forum_config_names_min_version():
    cfg = json.loads((ROOT / "agents.json").read_text(encoding="utf-8"))["forum_config"]
    assert run_forum._version_tuple(cfg["kna_min_version"]) >= (0, 7, 0)


def test_version_tuple():
    assert run_forum._version_tuple("kna, version 0.7.0") == (0, 7, 0)
    assert run_forum._version_tuple("0.4.1") < run_forum._version_tuple("0.7.0")
    assert run_forum._version_tuple("0.10.0") > run_forum._version_tuple("0.7.0")


def _fake_cli(tmp_path, version):
    cli = tmp_path / f"kna_{version}"
    cli.write_text(f"#!/bin/sh\necho 'kna, version {version}'\n")
    cli.chmod(cli.stat().st_mode | stat.S_IEXEC)
    return cli


def _members_dir(tmp_path, with_term_number):
    pd = pytest.importorskip("pandas")
    pytest.importorskip("pyarrow")
    d = tmp_path / ("new" if with_term_number else "old")
    d.mkdir()
    df = pd.DataFrame({"mona_cd": ["A1"], "reelection": ["초선"]})
    if with_term_number:
        df["term_number"] = [1]
    df.to_parquet(d / "members_22.parquet")
    return d


def test_check_kna_setup_accepts_070(tmp_path):
    cli = _fake_cli(tmp_path, "0.7.0")
    assert run_forum.check_kna_setup("0.7.0", cli=cli, data_dir=_members_dir(tmp_path, True)) == []


def test_check_kna_setup_rejects_old_cli_and_old_data(tmp_path):
    cli = _fake_cli(tmp_path, "0.4.1")
    problems = run_forum.check_kna_setup("0.7.0", cli=cli, data_dir=_members_dir(tmp_path, False))
    assert len(problems) == 2
    assert "0.4.1" in problems[0]
    assert "term_number" in problems[1]


def test_check_kna_setup_reports_missing_data(tmp_path):
    cli = _fake_cli(tmp_path, "0.7.0")
    problems = run_forum.check_kna_setup("0.7.0", cli=cli, data_dir=tmp_path / "absent")
    assert len(problems) == 1 and "members_22.parquet" in problems[0]


def published_figure_scripts():
    for tex in sorted((ROOT / "articles").glob("2026-*_r*.tex")):
        d = ROOT / "articles" / "figures" / tex.stem
        yield from sorted(d.glob("*.R")) if d.is_dir() else []


def test_published_figures_that_read_kna_data_are_pinned():
    checked = 0
    for p in published_figure_scripts():
        text = p.read_text(encoding="utf-8")
        reads = re.search(r"read_parquet|read_csv|read\.csv|open_dataset", text)
        if not reads or not KNA_READ.search(text) or "kr-hearings" in text:
            continue
        checked += 1
        assert 'Sys.getenv("KNA_DATA_V060")' in text, p
        assert re.search(r'stop\("KNA_DATA_V060', text), p
        assert not re.search(r'<-\s*"[^"\n]*kna/data/processed/?"', text), p
        assert 'Sys.getenv("KBL_DATA"' not in text, p
    assert checked >= 29


def test_draft_template_uses_seniority_at_the_assembly():
    src = (ROOT / "draft_article.py").read_text(encoding="utf-8")
    assert "reelection (초선/재선/3선/...)" not in src
    assert "term_number (1 = first term at that assembly)" in src
    assert "member_info_17_22.parquet" not in src


@pytest.mark.parametrize("doc", ["DATA_SOURCES.md", "AGENTS.md", "FORUM_RULES.md"])
def test_docs_use_the_070_cli_flags(doc):
    text = (ROOT / doc).read_text(encoding="utf-8")
    assert not re.search(r"\bkna\b[^\n]*--age\b", text)

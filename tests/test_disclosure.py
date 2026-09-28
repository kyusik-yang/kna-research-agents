#!/usr/bin/env python3
"""Tests for disclosure.py (M21) and its entry on the articles page. Real
forum posts and ledgers are only read; generated files go to tmp_path."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import disclosure as ds  # noqa: E402


@pytest.fixture(autouse=True)
def _no_private_patterns(tmp_path, monkeypatch):
    monkeypatch.setenv("KNA_LEAK_PATTERNS", str(tmp_path / "none.txt"))


@pytest.mark.skipif(not (ROOT / "forum" / "090_critic.md").exists(), reason="forum posts not present")
def test_arc5_appendix_nine_reconstructed_rows_one_footnote(tmp_path):
    res = ds.build(30, "2026-08-24_r30", out_dir=tmp_path, logs_dir=tmp_path / "no_logs")
    rows = res["json"]["rows"]
    assert res["json"]["arc"] == 5 and res["json"]["rounds"] == [28, 29, 30]
    assert len(rows) == 9
    assert [(r["round"], r["role"]) for r in rows[:3]] == [
        (28, "literature_scout"), (28, "data_analyst"), (28, "critic")]
    assert all(r["source"] == "reconstructed" and r["model"] == "claude-fable-5" for r in rows)
    tex = res["tex"]
    assert tex.count("\\footnotetext{") == 1 and tex.count("AI-use disclosure.") == 1
    assert "reconstructed from session transcripts read on 2026-09-24" in res["footnote"]
    assert "Claude-drafted menu" in res["footnote"]          # D-10 provenance of the Arc 5 gate
    assert res["leak_hits"] == []
    assert (tmp_path / "2026-08-24_r30.disclosure.tex").read_text() == tex
    assert json.loads((tmp_path / "2026-08-24_r30.disclosure.json").read_text())["rows"] == rows


def _fixture_arc(tmp_path, arc_status):
    forum = tmp_path / "forum"
    forum.mkdir()
    for n, role in ((91, "literature_scout"), (92, "data_analyst"), (93, "critic")):
        (forum / f"{n:03d}_{role}.md").write_text(
            f'---\nauthor: "x"\ndate: "2026-09-30 10:00"\nround: 31\narc: 6\nrole: "{role}"\n---\n\n# P\n')
    (forum / "094_human.md").write_text('---\nauthor: "Researcher"\ndate: "2026-09-30 11:00"\n'
                                        'type: [human_comment]\nround: 31\narc: 6\nrole: "human"\n---\n\n# Note\n')
    logs = tmp_path / "logs" / "r31"
    logs.mkdir(parents=True)
    for role, model in (("literature_scout", "claude-opus-5-5"), ("data_analyst", "claude-opus-5-5"),
                        ("critic", "claude-opus-5-5")):
        (logs / f"r31_{role}.sidecar.json").write_text(json.dumps({
            "task": "agent", "role": role, "round": 31, "created": "2026-09-30T10:00:00-04:00",
            "model": model, "requested_model": model, "cli_version": "2.1.283", "effort": "high",
            "num_turns": 40, "attempts": [{}, {}] if role == "critic" else [{}], "failure": "ok"}))
    kd = tmp_path / "knowledge"
    kd.mkdir()
    (kd / "arc_status.json").write_text(json.dumps(arc_status))
    (kd / "retreats.jsonl").write_text(json.dumps({
        "originating_round": 31, "overturning_round": 31, "from_status": "preliminary",
        "to_status": "contested", "finding": "Early gap closes by year three"}) + "\n")
    gate = tmp_path / "topic_gate.md"
    gate.write_text("## R31 - Arc 6 opening\n\nseed: x\n\ndrafted_by: orchestrating Claude session "
                    "(claude-opus-5-5)\nsigned_by: orchestrating Claude session under the researcher's "
                    "standing delegation of 2026-09-25\nsigned: 2026-09-30\nhuman_rationale: SECRET RATIONALE\n")
    return dict(logs_dir=tmp_path / "logs", knowledge_dir=kd, forum_dir=forum, topic_gate=gate)


def test_sidecar_rows_models_and_recorded_overrides(tmp_path):
    kw = _fixture_arc(tmp_path, {"override_gates": "2026-09-30T12:00", "force": True,
                                 "human_rationale": "SECRET RATIONALE"})
    res = ds.build(31, "2026-09-30_r31", arc=6, out_dir=tmp_path / "out", **kw)
    rows = res["json"]["rows"]
    assert len(rows) == 3 and {r["model"] for r in rows} == {"claude-opus-5-5"}
    assert [r["attempts"] for r in rows] == [1, 1, 2]
    assert "claude-opus-5-5" in res["tex"] and "2.1.283" in res["tex"]
    actions = res["json"]["recorded_overrides"]
    assert any("--override-gates" in a for a in actions) and any("--force" in a for a in actions)
    assert any("094_human.md" in a for a in actions)
    assert "standing delegation" in res["footnote"] and not res["json"]["reconstructed"]
    assert "retreats.jsonl:1" in res["tex"]
    # D-19 default: the researcher's rationale never appears
    out = (tmp_path / "out" / "2026-09-30_r31.disclosure.json").read_text() + res["tex"]
    assert "SECRET RATIONALE" not in out
    assert res["leak_hits"] == []


def test_unrecorded_gate_provenance(tmp_path):
    kw = _fixture_arc(tmp_path, {})
    kw["topic_gate"].write_text("## R31 - Arc 6 opening\n\nseed: x\nsigned: 2026-09-30\n")
    res = ds.build(31, "s", arc=6, write=False, **kw)
    assert res["json"]["gate"]["drafted_by"] == "unrecorded"
    assert "set by the researcher" not in res["footnote"]


def test_tex_escape_specials():
    assert ds.tex_escape("data_analyst 50% & $x#") == r"data\_analyst 50\% \& \$x\#"


def test_articles_page_shows_disclosure_table(tmp_path, monkeypatch):
    import build_site as bs
    kw = _fixture_arc(tmp_path, {})
    arts = tmp_path / "articles"
    arts.mkdir()
    (arts / "2026-09-30_r31.tex").write_text("\\title{Arc Six Paper}\nbody")
    ds.build(31, "2026-09-30_r31", arc=6, out_dir=arts, **kw)
    monkeypatch.setattr(bs, "ARTICLES_DIR", arts)
    monkeypatch.setattr(bs, "GATE_REPORTS_DIR", tmp_path / "gates")
    html = bs._build_article_list()
    assert "Arc Six Paper" in html and "AI use and oversight" in html
    assert html.count("claude-opus-5-5") >= 3
    assert html.count("Round 31 |") == 1          # the .disclosure.tex is not listed as a paper


def test_overrides_are_never_called_human_actions(tmp_path):
    """FID-F6 (D-09, D-10): the orchestrating session runs run_arc and
    run_forum and can pass these flags. The footnote lists them as recorded
    overrides and names an actor only when the record holds one."""
    kw = _fixture_arc(tmp_path, {
        "allow_model_change": "2026-09-30T09:00 claude-opus-5-5 to claude-opus-5-6",
        "bypass_topic_gate": {"ts": "2026-09-30T09:05", "by": "researcher"},
        "human_actions": [{"action": "manual rerun of R31", "ts": "2026-09-30T13:00"}]})
    res = ds.build(31, "s", arc=6, write=False, **kw)
    fn = res["footnote"]
    assert "human action" not in fn.lower()
    assert "Recorded overrides and comment posts:" in fn
    assert "--allow-model-change (2026-09-30T09:00 claude-opus-5-5 to claude-opus-5-6, actor not recorded)" in fn
    assert "--bypass-topic-gate (2026-09-30T09:05, by researcher)" in fn
    assert "manual rerun of R31 2026-09-30T13:00 (actor not recorded)" in fn
    assert "comment post 094_human.md (2026-09-30, author recorded as Researcher)" in fn

"""Season 2 guardrails: topic gate fields, posting order, taxonomy parsing,
and order-agnostic round grouping on the site.

Every test that calls into run_forum points all of its path constants at
tmp_path first (_isolate), so no test writes to the real knowledge/ or forum/."""

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import run_forum  # noqa: E402
import taxonomy_monitor as tm  # noqa: E402
import build_site  # noqa: E402


GATE_OK = """# Topic Gate

## S2 test arc

seed: committee chair tenure and bill passage

identification: DiD on chair promotion events.

exclusion_criteria: (1) no special committees.

prior: chairs of high-stakes committees pass their own bills at a higher rate than matched non-chairs.

falsifier: if the within-person passage-rate change after promotion is indistinguishable from the matched cohort, the prior is overturned.

drafted_by: orchestrating Claude session (claude-opus-5-5)

signed_by: orchestrating Claude session, signed under the researcher's standing delegation of 2026-09-25

signed: 2026-08-24
"""

GATE_MISSING = """# Topic Gate

## S2 test arc

seed: committee chair tenure and bill passage

identification: DiD on chair promotion events.

exclusion_criteria: (1) no special committees.

signed: 2026-08-24
"""


RUN_FORUM_PATHS = {
    "BASE_DIR": "", "FORUM_DIR": "forum", "LOGS_DIR": "logs", "WORKSPACE_DIR": "workspace",
    "SUMMARIES_DIR": "summaries", "KNOWLEDGE_DIR": "knowledge", "TOPIC_GATE_FILE": "topic_gate.md",
    "RETREATS_LEDGER": "knowledge/retreats.jsonl", "ACTIVE_ARC_FILE": "knowledge/active_arc.json",
    "ARC_STATUS_FILE": "knowledge/arc_status.json", "HUMAN_CONTEXT_FILE": "knowledge/human_context.md",
    "WAIVERS_FILE": "knowledge/waivers.jsonl", "GATE_EVENTS_FILE": "knowledge/gate_events.jsonl",
    "GATE_CANDIDATES_FILE": "knowledge/gate_candidates.jsonl", "ARCHIVE_DIR": "knowledge/archive",
}


def _isolate(tmp_path, monkeypatch, season=2, order=None):
    """Point every run_forum path at tmp_path and return the agents file."""
    for name, rel in RUN_FORUM_PATHS.items():
        monkeypatch.setattr(run_forum, name, tmp_path / rel if rel else tmp_path)
    (tmp_path / "forum").mkdir(exist_ok=True)
    (tmp_path / "knowledge").mkdir(exist_ok=True)
    f = _agents_file(tmp_path, season=season, order=order)
    monkeypatch.setattr(run_forum, "AGENTS_FILE", f)
    return f


def _agents_file(tmp_path, season=2, order=None):
    data = {
        "season": season,
        "forum_config": {"round_order": order} if order else {},
        "agents": [
            {"id": "literature_scout", "name": "Scout", "prompt": "s"},
            {"id": "data_analyst", "name": "Analyst", "prompt": "a"},
            {"id": "critic", "name": "Critic", "prompt": "c"},
        ],
    }
    f = tmp_path / "agents.json"
    f.write_text(json.dumps(data))
    return f


def test_parse_gate_entry_reads_all_fields():
    entry = GATE_OK.split("\n## ", 1)[1]
    fields = run_forum._parse_gate_entry(entry)
    assert fields["seed"] == "committee chair tenure and bill passage"
    assert fields["prior"].startswith("chairs of high-stakes")
    assert fields["falsifier"].startswith("if the within-person")
    assert fields["signed"] == "2026-08-24"
    assert fields["drafted_by"] == "orchestrating Claude session (claude-opus-5-5)"
    assert fields["signed_by"].startswith("orchestrating Claude session, signed under")


def test_parse_gate_entry_keeps_multiline_free_text():
    """M08 (2): a field ends only at a line that starts with a known field name."""
    entry = ("seed: chair tenure\n\nhuman_rationale: The arc matters for two reasons.\n"
             "Why: because chairs gatekeep bills.\nNote: a second line.\n\n"
             "prior: chairs pass more bills.\nsigned: 2026-09-26\n\n---\n")
    fields = run_forum._parse_gate_entry(entry)
    assert fields["human_rationale"] == ("The arc matters for two reasons. Why: because chairs gatekeep bills. "
                                         "Note: a second line.")
    assert fields["prior"] == "chairs pass more bills."
    assert fields["signed"] == "2026-09-26"


def test_topic_gate_blocks_without_prior_and_falsifier_in_season2(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch, season=2)
    (tmp_path / "topic_gate.md").write_text(GATE_MISSING)
    with pytest.raises(SystemExit) as exc:
        run_forum.check_topic_gate("committee chair tenure and bill passage", 25, 72)
    assert "prior" in str(exc.value) and "falsifier" in str(exc.value)


def test_topic_gate_passes_and_records_active_arc(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch, season=2)
    (tmp_path / "topic_gate.md").write_text(GATE_OK)
    run_forum.check_topic_gate("committee chair tenure and bill passage", 25, 72)
    arc = json.loads((tmp_path / "knowledge" / "active_arc.json").read_text())
    assert arc["start_round"] == 25
    assert arc["prior"].startswith("chairs of high-stakes")
    assert arc["season"] == 2
    assert arc["drafted_by"] == "orchestrating Claude session (claude-opus-5-5)"
    assert arc["arc_id"] == "6" and arc["arc"] == 6
    assert "model" in arc and "claude_code_version" in arc


def test_topic_gate_season1_does_not_require_prior(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch, season=1)
    (tmp_path / "topic_gate.md").write_text(GATE_MISSING)
    run_forum.check_topic_gate("committee chair tenure and bill passage", 25, 72)


def test_load_agents_follows_round_order(tmp_path, monkeypatch):
    monkeypatch.setattr(run_forum, "AGENTS_FILE",
                        _agents_file(tmp_path, order=["data_analyst", "literature_scout", "critic"]))
    monkeypatch.setattr(run_forum, "ROUND_ORDER_OVERRIDE", None)
    assert [a["id"] for a in run_forum.load_agents()] == ["data_analyst", "literature_scout", "critic"]
    monkeypatch.setattr(run_forum, "ROUND_ORDER_OVERRIDE", ["literature_scout", "data_analyst", "critic"])
    assert [a["id"] for a in run_forum.load_agents()][0] == "literature_scout"


def test_parse_labels_and_validity():
    post = """scoring:
  research_novelty: 3/4
  opportunity_pattern: puzzle_contradiction
  method_paradigm: empirical_mapping
  operation: decouple
  falsifier_tested: yes
  verdict: revise
  one_line: "Anomaly stands; falsifier pending."
"""
    labels = tm.parse_labels(post)
    assert labels["valid"] is True
    assert labels["verdict"] == "revise"
    bad = tm.parse_labels("opportunity_pattern: bridge\nmethod_paradigm: synthesis_unification\noperation: integrate\n")
    assert bad["valid"] is False
    assert tm.parse_labels("scoring:\n  verdict: pursue\n") is None


def test_entropy_and_cap():
    uniform = Counter({k: 1 for k in tm.OPPORTUNITY})
    assert abs(tm.normalized_entropy(uniform, len(tm.OPPORTUNITY)) - 1.0) < 1e-9
    single = Counter({"bridge_opportunity": 5})
    assert tm.normalized_entropy(single, len(tm.OPPORTUNITY)) == 0.0
    entries = [{"opportunity_pattern": "bridge_opportunity", "method_paradigm": "synthesis_unification",
                "operation": "integrate"}] * 2 + \
              [{"opportunity_pattern": "puzzle_contradiction", "method_paradigm": "empirical_mapping",
                "operation": "measure"}]
    s = tm.summarize(entries)
    assert s["n"] == 3 and abs(s["bridge_share"] - 2 / 3) < 1e-9
    assert tm.cap_active(s, threshold=0.40, min_n=3) is True
    assert tm.cap_active(s, threshold=0.70, min_n=3) is False


def test_group_rounds_handles_both_orders():
    s1 = [{"agent_id": a} for a in ["literature_scout", "data_analyst", "critic"] * 2]
    s2 = [{"agent_id": a} for a in ["data_analyst", "literature_scout", "critic"] * 2]
    assert sorted(len(v) for v in build_site.group_rounds(s1).values()) == [3, 3]
    assert sorted(len(v) for v in build_site.group_rounds(s2).values()) == [3, 3]
    mixed = s1 + s2
    assert len(build_site.group_rounds(mixed)) == 4


def test_topic_diversity_prompt_block(tmp_path, monkeypatch):
    import topic_diversity as td
    monkeypatch.setattr(td, "LOG_FILE", tmp_path / "topic_diversity.jsonl")
    assert td.format_for_prompt() == ""
    row = {"round": 25, "status": "block", "warn": 0.68, "block": 0.80, "max_cosine": 0.84,
           "nearest_post": {"id": "058_literature_scout", "round": 20, "cosine": 0.84},
           "nearest_article": {"id": "2026-04-20_r22", "round": 22, "cosine": 0.81}}
    (tmp_path / "topic_diversity.jsonl").write_text(json.dumps(row) + "\n")
    block = td.format_for_prompt(25)
    assert "BLOCK" in block and "2026-04-20_r22" in block
    # E2E-06: uncalibrated thresholds give no archive instruction or score cap.
    assert "duplicate topic" not in block and "cap research_novelty" not in block
    assert td.format_for_prompt(26) == ""


def test_topic_diversity_round_of():
    import topic_diversity as td
    assert td._round_of(Path("073_literature_scout.md")) == 25
    assert td._round_of(Path("072_critic.md")) == 24


def test_arc_runner_decisions():
    import run_arc
    d = run_arc.decide
    assert d({"verdict": "archive", "falsifier_tested": "yes"}, 1, 3, None)[0] == "stop"
    assert d({"verdict": "archive", "falsifier_tested": None}, 2, 3, "block")[0] == "stop"
    assert d({"verdict": "pursue", "falsifier_tested": "no"}, 2, 3, None)[0] == "continue"
    assert d({"verdict": "pursue", "falsifier_tested": "yes"}, 2, 3, None)[0] == "continue"
    assert d({"verdict": "pursue", "falsifier_tested": "yes"}, 3, 3, None)[0] == "draft_and_stop"
    assert d({"verdict": "revise", "falsifier_tested": "yes"}, 4, 3, None)[0] == "continue"
    assert d({"verdict": None, "falsifier_tested": None}, 1, 3, None)[0] == "continue"


def test_draft_body_completeness_gate():
    import draft_article as da
    good = "\\title{X} " + ("w " * 3200) + " \\section{Conclusion} done \\bibliography{refs}"
    ok, _ = da._body_ok(good)
    assert ok
    assert da._body_ok("and")[0] is False
    assert da._body_ok(("w " * 3200) + " \\bibliography{refs}")[0] is False   # no conclusion
    assert da._body_ok(("w " * 3200) + " \\section{Conclusion}")[0] is False  # no bibliography

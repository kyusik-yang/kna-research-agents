"""Premise check for topic-gate entries (M15). The claude_cli call is always
replaced by a stub runner. Every write goes to tmp_path."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import premise_check as prc  # noqa: E402

# Arc 5 entry rewritten in the v2.1 template, with the premise the arc's prior rested on.
ARC5 = {
    "seed": "First-term legislative learning: does the bill passage-rate gap between first-term and "
            "re-elected members close over the assembly term?",
    "identification": "Within-assembly comparison of member-bill passage rates by proposal year.",
    "prior": "The gap narrows by the third year as first-term members learn the institution.",
    "falsifier": "If the first-term passage gap does not shrink across proposal years, the prior is overturned.",
    "premise": "First-term members' year-1 member-bill passage rate is at least 2pp below that of re-elected members.",
    "drafted_by": "orchestrating Claude session (claude-fable-5)",
    "signed_by": "researcher, selected from a Claude-drafted menu on 2026-08-24",
}


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(prc, "PREMISE_DIR", tmp_path / "knowledge" / "premise_checks")
    monkeypatch.setattr(prc, "STAGING_ROOT", tmp_path / "knowledge" / "staging")
    monkeypatch.setattr(prc, "TOPIC_GATE_FILE", tmp_path / "topic_gate.md")
    return tmp_path


class StubRunner:
    """Stands in for claude_cli.run_claude and writes the expected result file."""

    def __init__(self, result: dict | None):
        self.result, self.calls = result, []

    def __call__(self, task, prompt, **kw):
        self.calls.append({"task": task, "prompt": prompt, **kw})
        if self.result is not None:
            Path(kw["expect_file"]).write_text(json.dumps(self.result))
        return SimpleNamespace(ok=self.result is not None, failure="ok" if self.result else "no_post",
                               run_id=kw["extra_env"]["KNA_RUN_ID"])


R28_PREMISE_RESULT = {"premise": ARC5["premise"], "value": -0.70, "ci": [-1.46, 0.06], "n": 35056,
                      "script": "knowledge/staging/x/premise.py", "passes": False,
                      "definition": "Raw year-1 strict passage rate, first-term minus re-elected, 17th-22nd."}


def test_slug_is_stable_and_unique():
    a = prc.slug(ARC5["seed"])
    assert a == prc.slug("  " + ARC5["seed"].upper().replace(" ", "  ") + " ")
    assert a.startswith("first-term-legislative-learning") and len(a) <= 69
    k1, k2 = prc.slug("초선 의원 학습"), prc.slug("재선 의원 학습")
    assert k1 != k2 and len(k1) == 8
    assert prc.result_path(ARC5["seed"]).parent == prc.PREMISE_DIR


def test_retrospective_arc5_premise_fails_and_blocks(dirs):
    runner = StubRunner(R28_PREMISE_RESULT)
    rec = prc.run(ARC5, runner=runner)
    assert rec["passes"] is False and rec["value"] == -0.70 and rec["source"] == "computed"
    assert rec["errors"] == [] and rec["signed_by"].startswith("researcher, selected")
    call = runner.calls[0]
    assert call["task"] == "premise_check" and call["tools"] == ["Bash", "Read", "Write"]
    assert call["role"] == "data_analyst"
    stage = Path(call["extra_env"]["KNA_STAGING_DIR"])
    assert stage.parent == dirs / "knowledge" / "staging"
    assert ARC5["premise"] in call["prompt"]
    assert ARC5["falsifier"] not in call["prompt"] and ARC5["prior"] not in call["prompt"]
    stored = json.loads(prc.result_path(ARC5["seed"]).read_text())
    assert stored["passes"] is False
    status = prc.gate_status(ARC5)
    assert status["status"] == "fail" and status["block"] is True
    assert status["path"] == prc.result_path(ARC5["seed"]).name   # derived from the seed, repo-safe
    ovr = prc.gate_status({**ARC5, "premise_override": "Researcher: run the arc on the level question anyway."})
    assert ovr["status"] == "override" and ovr["block"] is False


def test_passing_premise_and_missing_states(dirs):
    assert prc.gate_status({**ARC5, "premise": ""})["status"] == "no_premise"
    assert prc.gate_status(ARC5)["status"] == "missing"
    prc.run(ARC5, runner=StubRunner({**R28_PREMISE_RESULT, "passes": True}))
    assert prc.gate_status(ARC5) == {**prc.gate_status(ARC5), "status": "pass", "block": False}


def test_no_result_file_is_an_error_not_a_pass(dirs):
    rec = prc.run(ARC5, runner=StubRunner(None))
    assert rec["passes"] is None and rec["errors"] == ["no result file written"]
    assert rec["call_ok"] is False
    st = prc.gate_status(ARC5)
    assert st["status"] == "error" and st["block"] is False


def test_invalid_result_fields_are_reported(dirs):
    rec = prc.run(ARC5, runner=StubRunner({"premise": "x", "value": "about -0.7", "passes": "no"}))
    assert rec["passes"] is None
    assert any("'value' must be a number" in e for e in rec["errors"])
    assert any("missing 'n'" in e for e in rec["errors"])


def test_refuses_without_premise_and_without_force(dirs):
    with pytest.raises(ValueError):
        prc.run({**ARC5, "premise": " "}, runner=StubRunner(R28_PREMISE_RESULT))
    prc.run(ARC5, runner=StubRunner(R28_PREMISE_RESULT))
    with pytest.raises(FileExistsError):
        prc.run(ARC5, runner=StubRunner(R28_PREMISE_RESULT))
    prc.run(ARC5, runner=StubRunner({**R28_PREMISE_RESULT, "passes": True}), force=True)
    base = prc.result_path(ARC5["seed"])
    assert json.loads(base.read_text())["passes"] is True
    assert json.loads(base.with_name(base.stem + ".rev1.json").read_text())["passes"] is False


def test_published_table_stands_in_without_a_call(dirs):
    def never(*a, **k):
        raise AssertionError("no call expected")
    gate = {**ARC5, "premise_source": "Ka (2025a), doi:10.21487/jrm.2025.11.10.3.1, Table 2"}
    rec = prc.run(gate, runner=never)
    assert rec["source"] == "published" and rec["passes"] is True
    assert rec["premise_source"] == {"doi": "10.21487/jrm.2025.11.10.3.1", "table": "Table 2"}
    assert prc.published_source({"premise_source": "a book, no doi"}) is None


def test_find_gate_entry_reads_new_fields(dirs):
    (dirs / "topic_gate.md").write_text(
        "# Topic Gate\n\n## R31 test entry\n\nseed: First-term legislative learning\n\n"
        f"premise: {ARC5['premise']}\n\npremise_override: none needed\n\nsesoi: 2pp because staff notice it\n\n"
        "null_paper: no\n\nsigned: 2026-09-25\n\n## R25 other\n\nseed: something else\n")
    entry = prc.find_gate_entry("first-term legislative learning")
    assert entry["premise"] == ARC5["premise"]
    assert entry["null_paper"] == "no" and entry["sesoi"].startswith("2pp")
    with pytest.raises(KeyError):
        prc.find_gate_entry("unrelated seed")

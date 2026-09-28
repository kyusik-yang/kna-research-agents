"""Critic calibration set (M22). Manual only: these tests use a stub runner
and a scratch calibration folder under tmp_path."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import claim_sheet as cs  # noqa: E402
import claude_cli  # noqa: E402
import critic_calibration as cc  # noqa: E402
import prediction_card as pc  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "season2_replay"
ITEMS = [("r28_premise", "known_overturn"), ("r29_absorption", "exploratory"), ("pos_a", "positive_control")]


def _make(tmp_path, labels=True, sheet_text=None) -> Path:
    d = tmp_path / "critic_calibration"
    (d / "sheets").mkdir(parents=True)
    with open(d / "items.jsonl", "w") as f:
        for i, fate in ITEMS:
            f.write(json.dumps({"id": i, "sheet": f"{i}.md", "fate": fate}) + "\n")
            (d / "sheets" / f"{i}.md").write_text(sheet_text or f"# Claim sheet {i}\n\nResults only.\n")
    if labels:
        with open(d / "researcher_labels.jsonl", "w") as f:
            for i, v in (("r28_premise", "archive"), ("r29_absorption", "revise"), ("pos_a", "pursue")):
                f.write(json.dumps({"id": i, "verdict": v, "labeled_at": "2026-09-25"}) + "\n")
    return d


class Stub:
    def __init__(self, verdicts, failure="ok"):
        self.verdicts, self.failure, self.calls = list(verdicts), failure, []

    def __call__(self, task, prompt, **kw):
        self.calls.append({"task": task, "prompt": prompt, **kw})
        return SimpleNamespace(structured={"verdict": self.verdicts.pop(0)}, run_id=f"cal{len(self.calls)}",
                               failure=self.failure, ok=self.failure == "ok")


@pytest.fixture(autouse=True)
def open_gate(monkeypatch):
    monkeypatch.setattr(claude_cli, "launch_gate", lambda cfg=None: (True, None, None))


def test_claim_sheets_contain_no_verdict_text(tmp_path):
    d = _make(tmp_path, sheet_text="# Sheet\n\nThe Critic's verdict: pursue\n")
    probs = cc.sheet_problems(d)
    assert len(probs) == 3 and all("verdict text" in x for x in probs)
    scored = _make(tmp_path / "b", sheet_text="# Sheet\n\nresearch_novelty: 4/4\n")
    assert cc.sheet_problems(scored)
    assert cc.sheet_problems(_make(tmp_path / "c")) == []


def test_a_generated_claim_sheet_passes_the_verdict_text_audit(tmp_path):
    card = json.loads((FIX / "cards" / "R29.json").read_text())
    text = cs.build(29, gate={"seed": "First-term legislative learning"}, card=card, card_meta={},
                    results=pc.load_results(rdir=FIX / "results" / "r29"), prechecks={},
                    analyst_post=FIX / "forum" / "086_data_analyst.md", scout_post=None,
                    containment=None, write=False)
    d = _make(tmp_path, sheet_text=text)
    assert cc.sheet_problems(d) == []


def test_refuses_without_the_researcher_labels(tmp_path):
    d = _make(tmp_path, labels=False)
    stub = Stub(["pursue"] * 3)
    with pytest.raises(SystemExit) as e:
        cc.run(cal_dir=d, runner=stub, confirm=lambda _: "yes", prompt_file=_prompt(tmp_path))
    assert "researcher_labels.jsonl is missing" in str(e.value)
    assert stub.calls == []
    (d / "researcher_labels.jsonl").write_text(json.dumps({"id": "pos_a", "verdict": "pursue"}) + "\n")
    with pytest.raises(SystemExit) as e:
        cc.run(cal_dir=d, runner=stub, confirm=lambda _: "yes", prompt_file=_prompt(tmp_path))
    assert "r28_premise" in str(e.value)


def _prompt(tmp_path) -> Path:
    p = tmp_path / "critic_prompt.md"
    p.write_text("You are the Critic.")
    return p


def test_refuses_without_confirmation(tmp_path, capsys):
    d = _make(tmp_path)
    stub = Stub(["pursue"] * 3)
    with pytest.raises(SystemExit):
        cc.run(cal_dir=d, runner=stub, confirm=lambda _: "no", prompt_file=_prompt(tmp_path))
    assert stub.calls == []
    out = capsys.readouterr().out
    assert "3 non-posting Critic calls" in out and "gross shifts" in out
    assert not (d / "runs.jsonl").exists()


def test_refuses_when_the_launch_gate_is_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(claude_cli, "launch_gate", lambda cfg=None: (False, "five_hour 0.90", "2026-09-25T18:00"))
    stub = Stub(["pursue"] * 3)
    with pytest.raises(SystemExit):
        cc.run(cal_dir=_make(tmp_path), runner=stub, confirm=lambda _: "yes", prompt_file=_prompt(tmp_path))
    assert stub.calls == []


def test_run_reports_agreement_and_error_rates(tmp_path):
    d = _make(tmp_path)
    stub = Stub(["pursue", "revise", "archive"])
    rep = cc.run(cal_dir=d, runner=stub, confirm=lambda _: "yes", prompt_file=_prompt(tmp_path), label="m10a")
    assert rep["n"] == 3 and rep["agreement"] == pytest.approx(1 / 3)
    assert rep["pursue_rate"] == pytest.approx(1 / 3)
    assert rep["false_pursue_known_overturns"] == (1, 1)
    assert rep["false_archive_positive_controls"] == (1, 1)
    assert "gross shifts" in rep["note"]
    call = stub.calls[0]
    assert call["task"] == "agent" and call["role"] == "critic" and call["tools"] == []
    assert call["schema"]["properties"]["prior_status"]
    assert "Results only." in call["prompt"] and call["prompt"].startswith("You are the Critic.")
    rows = [json.loads(x) for x in (d / "runs.jsonl").read_text().splitlines()]
    assert rows[0]["label"] == "m10a"


def test_usage_limit_stops_the_run_early(tmp_path):
    d = _make(tmp_path)
    stub = Stub(["pursue", "revise", "archive"], failure="usage_limit")
    rep = cc.run(cal_dir=d, runner=stub, confirm=lambda _: "yes", prompt_file=_prompt(tmp_path))
    assert len(stub.calls) == 1 and rep["n"] == 1


def test_score_ignores_missing_verdicts():
    items = [{"id": i, "fate": f} for i, f in ITEMS]
    s = cc.score({"r28_premise": "archive", "pos_a": None}, items, {"r28_premise": "archive"})
    assert s["n"] == 1 and s["agreement"] == 1.0 and s["false_archive_positive_controls"] == (0, 0)

"""Claim sheet for the Critic and the provisional-verdict order check (M16).
Inputs come from tests/fixtures/season2_replay. Every write goes to tmp_path."""

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import claim_sheet as cs  # noqa: E402
import prediction_card as pc  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "season2_replay"
ARC5_EXCLUSIONS = (
    "(1) Do NOT drift into a sponsorship-volume or productivity-count study; counts are descriptive "
    "context, passage rate is the outcome. (2) Do NOT open a cross-assembly ideology or polarization "
    "angle; ideal points are not part of this arc. (3) Do NOT promote a committee-assignment or "
    "mentorship mechanism to the headline before the learning gap itself is established. (4) Do NOT "
    "re-open women's legislative effectiveness (R5-6 paper); election_type is a control here, not the question.")
GATE = {"seed": "First-term legislative learning", "start_round": 28,
        "prior": "First-term members' bills pass at a lower rate early in the assembly and the gap narrows.",
        "falsifier": "The first-term x proposal-year interaction is indistinguishable from zero.",
        "exclusion_criteria": ARC5_EXCLUSIONS}


@pytest.fixture
def sheet(tmp_path):
    card = json.loads((FIX / "cards" / "R30.json").read_text())
    res = pc.load_results(rdir=FIX / "results" / "r30")
    out = tmp_path / "workspace" / "r30" / "claim_sheet.md"
    text = cs.build(30, gate=GATE, card=card, card_meta={"sha256": pc.card_sha(card),
                                                         "committed_at": "2026-08-24T09:48:30-04:00"},
                    results=res, prechecks={}, analyst_post=FIX / "forum" / "089_data_analyst.md",
                    scout_post=FIX / "forum" / "088_literature_scout.md", containment=None, out_path=out)
    assert out.read_text() == text
    return text


def _prose_windows(md: str, n: int = 12) -> set:
    """Every n-word window of the post's narrative (tables, code, YAML and headings excluded)."""
    body, fence = [], False
    for line in md.split("---", 2)[-1].splitlines():
        if line.strip().startswith("```"):
            fence = not fence
            continue
        if fence or line.lstrip().startswith(("|", "#")):
            continue
        body.append(line)
    words = re.findall(r"\S+", " ".join(body))
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def test_r30_sheet_holds_every_result_number(sheet):
    res = pc.load_results(rdir=FIX / "results" / "r30")
    for sid, r in res.items():
        assert f"| {sid} |" in sheet
        for k in ("estimate", "se", "n"):
            if r.get(k) is not None:
                assert f"{r[k]:g}" in sheet, (sid, k)
    assert "NOT COMPUTABLE" in sheet
    assert "workspace/r30/mechanisms2.py" in sheet


def test_r30_sheet_copies_no_12_word_run_of_the_analyst_narrative(sheet):
    flat = " ".join(re.findall(r"\S+", sheet))
    windows = _prose_windows((FIX / "forum" / "089_data_analyst.md").read_text())
    assert len(windows) > 500
    copied = [w for w in windows if w in flat]
    assert copied == []


def test_sheet_has_no_verdicts_or_monitor_numbers(sheet):
    low = sheet.lower()
    for banned in ("pursue", "archive", "verdict:", "entropy", "bridge", "opportunity_pattern",
                   "research_novelty", "findings tracker"):
        assert banned not in low, banned


def test_exclusions_render_with_ids_and_without_truncation(sheet):
    items = cs.exclusion_items(ARC5_EXCLUSIONS)
    assert [i for i, _ in items] == ["X1", "X2", "X3", "X4"]
    assert items[3][1].endswith("election_type is a control here, not the question.")
    assert "- (X3) Do NOT promote a committee-assignment or mentorship mechanism" in sheet
    assert cs.exclusion_items("(X1) first item. (X2) second item.") == [("X1", "first item."), ("X2", "second item.")]


def test_gate_provenance_defaults_to_unrecorded(sheet):
    assert "- drafted_by: unrecorded" in sheet and "- signed_by: unrecorded" in sheet


def test_private_evidence_section_is_copied_verbatim(tmp_path):
    post = tmp_path / "093_data_analyst.md"
    post.write_text("# R31\n\n## 4. Private Evidence\n\nRow 17 of the sample has a duplicated uid.\n\n"
                    "## 5. Next\n\nNarrative that must not appear.\n")
    assert cs.private_evidence(post.read_text()) == "Row 17 of the sample has a duplicated uid."
    text = cs.build(31, gate={}, card=None, card_meta={}, results={}, prechecks={}, analyst_post=post,
                    scout_post=None, containment={"violations": [{"path": "topic_gate.md"}], "external_writes": []},
                    write=False)
    assert "Row 17 of the sample has a duplicated uid." in text
    assert "Narrative that must not appear" not in text
    assert "Violations: 1." in text


def test_unverified_scout_citations_come_from_prechecks(tmp_path):
    pre = {"posts": {"091_literature_scout.md": {"rules": [
        {"id": "R-05", "name": "citations", "status": "FLAG",
         "details": [{"doi": "10.9999/x", "flag": True, "result": "unchecked"}]}]}}}
    text = cs.build(31, gate={}, card=None, card_meta={}, results={}, prechecks=pre, analyst_post=None,
                    scout_post=tmp_path / "091_literature_scout.md", containment=None, write=False)
    assert "R-05: 10.9999/x (unchecked)" in text
    assert "| 091_literature_scout.md | R-05 citations | FLAG | 1 |" in text


# --------------------------------------------------------------------------
# Order check and provisional shift
# --------------------------------------------------------------------------

def _call(name, **inp):
    return {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": name, "input": inp}]}}


PROV = "workspace/r29/critic_provisional.json"


@pytest.mark.parametrize("touch", [
    _call("Read", file_path="forum/083_data_analyst.md"),
    _call("Bash", command="cat forum/083_data_analyst.md | head -50"),
    _call("Bash", command="python3 workspace/r28/robust.py"),
    _call("Grep", pattern="absorption", path="forum/083_data_analyst.md"),
])
def test_touching_the_analyst_work_before_the_provisional_write_is_flagged(touch):
    events = [_call("Read", file_path="workspace/r29/claim_sheet.md"), touch, _call("Write", file_path=PROV)]
    out = cs.order_check(events, analyst_post_name="083_data_analyst.md", analyst_scripts=["robust.py"])
    assert out["respected"] is False
    assert out["first_touch_idx"] == 1 and out["provisional_idx"] == 2


def test_provisional_first_is_respected():
    events = [_call("Read", file_path="workspace/r29/claim_sheet.md"),
              _call("Bash", command="python3 /tmp/own_recompute.py"),
              _call("Write", file_path=PROV),
              _call("Read", file_path="forum/083_data_analyst.md")]
    out = cs.order_check(events, analyst_post_name="083_data_analyst.md", analyst_scripts=["robust.py"])
    assert out["respected"] is True
    assert out["checks_before_reading"] == ["python3 /tmp/own_recompute.py"]
    none = cs.order_check([_call("Read", file_path="forum/083_data_analyst.md")],
                          analyst_post_name="083_data_analyst.md")
    assert none["respected"] is False and none["provisional_idx"] is None


def test_provisional_shift_needs_a_check_after_reading():
    prov = {"verdict": "revise", "empirical_rigor": 3}
    final = {"verdict": "pursue", "empirical_rigor": 4}
    read_only = [_call("Write", file_path=PROV), _call("Read", file_path="forum/086_data_analyst.md")]
    s = cs.provisional_shift(prov, final, read_only, first_touch_idx=1)
    assert s["moved"] is True and s["fields_moved"] == ["verdict", "empirical_rigor"]
    assert s["direction"] == "up" and s["check_after_reading"] is False
    checked = read_only + [_call("Bash", command="python3 workspace/r29/check_step.py")]
    assert cs.provisional_shift(prov, final, checked, first_touch_idx=1)["check_after_reading"] is True
    same = cs.provisional_shift(prov, prov, read_only, first_touch_idx=1)
    assert same["moved"] is False and same["direction"] is None


def test_analyst_scripts_from_workspace_and_results(tmp_path, monkeypatch):
    monkeypatch.setattr(cs, "WORKSPACE_DIR", tmp_path)
    (tmp_path / "r30").mkdir()
    (tmp_path / "r30" / "mechanisms.py").write_text("")
    (tmp_path / "r30" / "BASELINE.md").write_text("")
    res = pc.load_results(rdir=FIX / "results" / "r30")
    assert cs.analyst_scripts(30, res) == ["mechanisms.py", "mechanisms2.py"]

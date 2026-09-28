"""Taxonomy monitor, report-only (M20): no monitor numbers in the Critic-facing
block, the frozen annotator through claude_cli (stubbed, never the real
binary), arc-opening rows, the opener window and the retired bridge cap."""

import json
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import taxonomy_monitor as tm  # noqa: E402

FORUM = ROOT / "forum"

# Pinned: changing the frozen annotator prompt must be a deliberate, versioned edit.
FROZEN_SHA256 = "8fcd502e83a064505342a2ec9cca19816d0f59e14d01d3071ca633d29d8d40c3"


@dataclass
class FakeResult:
    ok: bool = True
    failure: str = "ok"
    structured: dict | None = None
    run_id: str = "run_test"
    model: str | None = "claude-opus-5-5"
    events_paths: list = field(default_factory=list)


class FakeCLI:
    def __init__(self, result_fn):
        self.calls = []
        self.result_fn = result_fn

    def module(self):
        mod = types.ModuleType("claude_cli")
        mod.run_claude = self.run_claude
        return mod

    def run_claude(self, task, prompt_text, **kw):
        self.calls.append({"task": task, "prompt_text": prompt_text, **kw})
        return self.result_fn(task, prompt_text, kw)


def _labels_for(kw, **over):
    ids = [line.strip("[]") for line in kw["user_message"].splitlines() if line.startswith("[")]
    item = {"opportunity_pattern": "constructed_contradiction", "method_paradigm": "empirical_mapping",
            "operation": "measure", "identification_design": "fixed_effects_panel"}
    item.update(over)
    return {"items": [dict(item, id=i) for i in ids]}


@pytest.fixture(autouse=True)
def files(tmp_path, monkeypatch):
    monkeypatch.setattr(tm, "TAXONOMY_FILE", tmp_path / "taxonomy.jsonl")
    monkeypatch.setattr(tm, "LEGACY_FILE", tmp_path / "taxonomy_legacy.jsonl")
    monkeypatch.setattr(tm, "ACTIVE_ARC_FILE", tmp_path / "active_arc.json")
    return tmp_path


def _write(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


# --------------------------------------------------------------------------
# No monitor numbers for the Critic; cap retired
# --------------------------------------------------------------------------

def test_prompt_block_has_no_entropy_share_or_cap(files):
    _write(tm.TAXONOMY_FILE, [{"round": r, "source": f"{r}_critic.md", "opportunity_pattern": "bridge_opportunity",
                               "method_paradigm": "synthesis_unification", "operation": "integrate"}
                              for r in (25, 26, 27)])
    block = tm.format_for_prompt(threshold=0.40).lower()
    for bad in ("entropy", "bridge cap", "share", "human reference", "especially valuable", "%", "labeled rounds"):
        assert bad not in block, bad
    assert "cap" not in block.replace("capability", "")
    assert "puzzle_contradiction" in block and "empirical_mapping" in block


def test_cap_active_over_three_arc_openings_two_bridge_is_report_only(files):
    rows = [
        {"round": 31, "unit": "arc_opening", "source": "091_literature_scout.md",
         "opportunity_pattern": "bridge_opportunity", "method_paradigm": "synthesis_unification", "operation": "integrate"},
        {"round": 34, "unit": "arc_opening", "source": "100_literature_scout.md",
         "opportunity_pattern": "constructed_contradiction", "method_paradigm": "empirical_mapping", "operation": "measure"},
        {"round": 37, "unit": "arc_opening", "source": "109_literature_scout.md",
         "opportunity_pattern": "evidence_gap", "method_paradigm": "empirical_mapping", "operation": "measure"},
    ]
    s = tm.summarize(rows)
    assert s["n"] == 3 and abs(s["bridge_share"] - 2 / 3) < 1e-9 and abs(s["constructed_share"] - 1 / 3) < 1e-9
    assert tm.cap_active(s, threshold=0.40, min_n=3) is True
    _write(tm.TAXONOMY_FILE, rows)
    rep = tm.opener_report(n=3)
    assert rep["cap_active_report_only"] is True and rep["n"] == 3
    # The Critic-facing block does not change with the cap state.
    assert tm.format_for_prompt() == tm.format_for_prompt(since=1, threshold=0.0)


def test_entropy_folds_constructed_into_bridge_over_seven_patterns():
    a = tm.summarize([{"opportunity_pattern": "constructed_contradiction"}, {"opportunity_pattern": "evidence_gap"}])
    b = tm.summarize([{"opportunity_pattern": "bridge_opportunity"}, {"opportunity_pattern": "evidence_gap"}])
    assert a["opportunity_entropy"] == b["opportunity_entropy"]
    assert a["opportunity"] == {"constructed_contradiction": 1, "evidence_gap": 1}


def test_arc_summary_counts_critic_rounds_only_by_default(files):
    _write(tm.TAXONOMY_FILE, [
        {"round": 28, "source": "084_critic.md", "opportunity_pattern": "puzzle_contradiction"},
        {"round": 28, "unit": "arc_opening", "source": "082_literature_scout.md",
         "opportunity_pattern": "constructed_contradiction"},
    ])
    assert tm.arc_summary(since=28)["n"] == 1
    assert tm.arc_summary(since=28, unit=None)["n"] == 2
    assert tm.arc_summary(since=28, unit="arc_opening")["n"] == 1


def test_verdict_label_set_unchanged():
    """The Critic keeps Chen et al.'s seven patterns (verdict schema enums);
    constructed_contradiction exists only for the annotator."""
    assert len(tm.OPPORTUNITY) == 7 and tm.CONSTRUCTED not in tm.OPPORTUNITY
    assert tm.ANNOTATOR_OPPORTUNITY == tm.OPPORTUNITY + [tm.CONSTRUCTED]


# --------------------------------------------------------------------------
# Frozen annotator
# --------------------------------------------------------------------------

def test_annotator_prompt_is_frozen_and_has_no_monitor_or_verdict_text():
    assert tm.ANNOTATOR_PROMPT_SHA256 == FROZEN_SHA256, "annotator prompt changed: bump the version and the pin"
    low = tm.ANNOTATOR_PROMPT.lower()
    for bad in ("entropy", "verdict", "pursue", "critic", "share", "cap ", "%"):
        assert bad not in low, bad
    assert "constructed_contradiction" in low and "identification design" in low


def test_annotator_message_holds_only_the_proposal():
    post = FORUM / "082_literature_scout.md"
    msg = tm.build_annotator_message([{"id": post.stem, "text": tm.proposal_text(post)}])
    assert "first-term members' member-bill" in msg          # Prediction to Test
    assert "Two literatures make contradictory predictions" in msg   # Gap Type
    for bad in ("topic_gate", "Response to Critic", "KCI New Hits", "Citation verification", "entropy"):
        assert bad not in msg, bad


def test_schema_validates_a_sample_output_for_082():
    jsonschema = pytest.importorskip("jsonschema")
    sample = {"items": [{"id": "082_literature_scout", "opportunity_pattern": "constructed_contradiction",
                         "method_paradigm": "empirical_mapping", "operation": "measure",
                         "identification_design": "fixed_effects_panel"}]}
    jsonschema.validate(sample, tm.ANNOTATOR_SCHEMA)
    bad = {"items": [dict(sample["items"][0], opportunity_pattern="bridge")]}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, tm.ANNOTATOR_SCHEMA)


def test_annotate_arc_opening_writes_one_row_through_claude_cli(files, monkeypatch):
    fake = FakeCLI(lambda task, prompt, kw: FakeResult(structured=_labels_for(kw)))
    monkeypatch.setitem(sys.modules, "claude_cli", fake.module())
    monkeypatch.setattr(tm, "_config", lambda: {"stage2": {"annotator": True}})
    post = FORUM / "082_literature_scout.md"
    rows = tm.annotate_arc_opening(post, round_num=28, arc_id="arc5")
    assert len(fake.calls) == 1
    call = fake.calls[0]
    assert call["task"] == "annotator" and call["prompt_text"] == tm.ANNOTATOR_PROMPT
    assert call["schema"] is tm.ANNOTATOR_SCHEMA and call.get("tools") is None and call["arc_id"] == "arc5"
    assert len(rows) == 1
    r = rows[0]
    assert r["unit"] == "arc_opening" and r["source"] == "082_literature_scout.md" and r["valid"]
    assert r["annotator_prompt_sha256"] == tm.ANNOTATOR_PROMPT_SHA256 and r["identification_design"]
    # Idempotent per opening post.
    assert tm.annotate_arc_opening(post, round_num=28, arc_id="arc5") is None
    assert len(fake.calls) == 1


def test_annotator_is_stage2_off_by_default(files, monkeypatch):
    fake = FakeCLI(lambda task, prompt, kw: FakeResult(structured=_labels_for(kw)))
    monkeypatch.setitem(sys.modules, "claude_cli", fake.module())
    monkeypatch.setattr(tm, "_config", lambda: {"stage2": {"annotator": False}})
    assert tm.annotate_arc_opening(FORUM / "082_literature_scout.md", round_num=28) is None
    assert fake.calls == [] and not tm.TAXONOMY_FILE.exists()


def test_failed_annotator_call_writes_nothing(files, monkeypatch):
    fake = FakeCLI(lambda task, prompt, kw: FakeResult(ok=False, failure="usage_limit"))
    monkeypatch.setitem(sys.modules, "claude_cli", fake.module())
    rows = tm.annotate_arc_opening(FORUM / "082_literature_scout.md", round_num=28, force=True)
    assert rows == [] and not tm.TAXONOMY_FILE.exists()


def test_annotator_labels_slate_candidates_in_the_same_call(files, monkeypatch):
    fake = FakeCLI(lambda task, prompt, kw: FakeResult(structured=_labels_for(kw, opportunity_pattern="scope_mismatch")))
    monkeypatch.setitem(sys.modules, "claude_cli", fake.module())
    slate = {"slate_id": "2026-10-01", "candidates": [
        {"candidate_id": "C1", "status": "candidate", "text": "candidate one text"},
        {"candidate_id": "C2", "status": "removed", "text": "removed text"},
        {"candidate_id": "C3", "status": "candidate", "text": "candidate three text"}]}
    rows = tm.annotate_arc_opening(FORUM / "082_literature_scout.md", round_num=28, slate=slate, force=True)
    assert len(fake.calls) == 1
    assert [r["unit"] for r in rows] == ["arc_opening", "slate_candidate", "slate_candidate"]
    assert "removed text" not in fake.calls[0]["user_message"]


def test_invalid_or_unknown_ids_are_dropped(files, monkeypatch):
    def result(task, prompt, kw):
        return FakeResult(structured={"items": [
            {"id": "082_literature_scout", "opportunity_pattern": "evidence_gap", "method_paradigm": "empirical_mapping",
             "operation": "measure", "identification_design": "descriptive"},
            {"id": "not_asked", "opportunity_pattern": "evidence_gap", "method_paradigm": "empirical_mapping",
             "operation": "measure", "identification_design": "descriptive"}]})
    monkeypatch.setitem(sys.modules, "claude_cli", FakeCLI(result).module())
    rows = tm.annotate_arc_opening(FORUM / "082_literature_scout.md", round_num=28, force=True)
    assert [r["source"] for r in rows] == ["082_literature_scout.md"]


# --------------------------------------------------------------------------
# Opener window, legacy labeling, record
# --------------------------------------------------------------------------

def test_opener_window_uses_best_available_label(files):
    _write(tm.LEGACY_FILE, [{"id": "001_literature_scout", "kind": "scout_posts", "opportunity_pattern": "evidence_gap",
                             "method_paradigm": "empirical_mapping", "operation": "measure"}])
    _write(tm.TAXONOMY_FILE, [
        {"round": 28, "source": "084_critic.md", "opportunity_pattern": "puzzle_contradiction",
         "method_paradigm": "empirical_mapping", "operation": "measure"},
        {"round": 25, "unit": "arc_opening", "source": "073_literature_scout.md",
         "opportunity_pattern": "constructed_contradiction", "method_paradigm": "empirical_mapping",
         "operation": "measure", "identification_design": "difference_in_differences"},
        {"round": 31, "unit": "arc_opening", "source": "091_literature_scout.md",
         "opportunity_pattern": "resource_bottleneck", "method_paradigm": "artifact_system", "operation": "measure"},
        {"round": 34, "unit": "arc_opening", "source": "100_literature_scout.md",
         "opportunity_pattern": "evidence_gap", "method_paradigm": "empirical_mapping", "operation": "measure"},
    ])
    ol = {o["post"]: o for o in tm.opener_labels()}
    assert len(ol) == 7   # five static legacy openers plus two annotated
    assert ol["001_literature_scout.md"]["label_source"] == "legacy_annotator"
    assert ol["040_literature_scout.md"]["label_source"] == "unlabeled"
    assert ol["073_literature_scout.md"]["label_source"] == "annotator"
    assert ol["082_literature_scout.md"]["label_source"] == "critic"
    assert ol["091_literature_scout.md"]["round"] == 31
    rep = tm.opener_report()
    assert [w["post"] for w in rep["window"]][0] == "040_literature_scout.md"   # last six of seven
    assert rep["opportunity_counts_all"]["constructed_contradiction"] == 1


def test_label_legacy_goes_through_claude_cli_and_skips_labeled(files, monkeypatch):
    fake = FakeCLI(lambda task, prompt, kw: FakeResult(structured=_labels_for(kw, opportunity_pattern="evidence_gap")))
    monkeypatch.setitem(sys.modules, "claude_cli", fake.module())
    monkeypatch.setattr(tm, "_article_items", lambda: [{"id": "2026-03-31_r2", "text": "a"},
                                                       {"id": "2026-04-18_r18", "text": "b"}])
    monkeypatch.setattr(tm, "_pursue_items", lambda: [])
    monkeypatch.setattr(tm, "_scout_items", lambda: [{"id": "001_literature_scout", "text": "c"}])
    _write(tm.LEGACY_FILE, [{"id": "2026-03-31_r2", "kind": "articles", "opportunity_pattern": "evidence_gap"}])
    tm.label_legacy()
    assert [c["task"] for c in fake.calls] == ["annotator", "annotator"]
    assert "[2026-03-31_r2]" not in fake.calls[0]["user_message"]
    rows = tm.load_entries(tm.LEGACY_FILE)
    assert len(rows) == 3 and rows[0]["id"] == "2026-03-31_r2"
    assert {r["id"] for r in rows[1:]} == {"2026-04-18_r18", "001_literature_scout"}
    assert all(r["annotator_prompt_sha256"] == tm.ANNOTATOR_PROMPT_SHA256 for r in rows[1:])


def test_record_round_reads_the_given_post(tmp_path):
    post = tmp_path / "200_critic.md"
    post.write_text("scoring:\n  opportunity_pattern: evidence_gap\n  method_paradigm: empirical_mapping\n"
                    "  operation: measure\n  verdict: revise\n", encoding="utf-8")
    out = tmp_path / "tax.jsonl"
    e = tm.record_round(67, out_file=out, post_path=post)
    assert e["round"] == 67 and e["unit"] == "critic_round" and e["source"] == "200_critic.md"
    assert tm.record_round(67, out_file=out, post_path=post) is None


def test_all_claude_calls_go_through_claude_cli():
    src = (ROOT / "taxonomy_monitor.py").read_text(encoding="utf-8")
    assert "subprocess" not in src and "shutil.which" not in src
    assert "claude_cli.run_claude" in src

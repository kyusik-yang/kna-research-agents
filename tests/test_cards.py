"""Prediction cards, the quantities ledger (M09), gap evidence (M19) and the
data schema summary. Hand-built Season 2 cards live in
tests/fixtures/season2_replay/cards. Every write goes to tmp_path."""

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import data_schema  # noqa: E402
import prediction_card as pc  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "season2_replay"


def _cards() -> dict:
    return {int(p.stem[1:]): json.loads(p.read_text(encoding="utf-8")) for p in (FIX / "cards").glob("R*.json")}


def _timeline() -> dict:
    return json.loads((FIX / "timeline.json").read_text(encoding="utf-8"))


def _meta(cards) -> dict:
    tl = _timeline()
    return {r: {"committed_at": tl["rounds"][str(r)]["card_committed_at"], "sha256": pc.card_sha(c)}
            for r, c in cards.items()}


def _results(r) -> dict:
    return pc.load_results(rdir=FIX / "results" / f"r{r}")


@pytest.fixture
def card():
    return copy.deepcopy(_cards()[25])


# --------------------------------------------------------------------------
# Schema and validation
# --------------------------------------------------------------------------

def test_card_schema_file_matches_generator():
    assert pc.load_card_schema() == pc.build_card_schema(), "run python3 prediction_card.py --write-schema"
    roles = pc.load_card_schema()["properties"]["spec_plan"]["items"]["properties"]["role"]["enum"]
    assert roles == ["primary", "robustness", "placebo", "reproduction", "calibration", "sanity"]


@pytest.mark.parametrize("r", range(25, 31))
def test_hand_built_season2_cards_validate(r):
    cards = _cards()
    prior = {k: c for k, c in cards.items() if k < r}
    assert pc.validate(cards[r], None, prior) == []


def test_valid_card_passes(card):
    assert pc.validate(card) == []


def test_missing_threshold_fails(card):
    card.pop("threshold")
    assert any("'threshold'" in e for e in pc.validate(card))


def test_more_than_six_specs_fails(card):
    extra = dict(card["spec_plan"][2], spec_id="cohort2_did", sample_def="cohort 2 only")
    card["spec_plan"].append(extra)
    errs = pc.validate(card)
    assert any("at most 6" in e for e in errs)


def test_spec_without_what_result_would_mean_fails(card):
    card["spec_plan"][1]["what_result_would_mean"] = " "
    assert any("what_result_would_mean is required" in e for e in pc.validate(card))


def test_positive_headline_without_sanity_specs_fails(card):
    card["spec_plan"] = [s for s in card["spec_plan"] if s["role"] != "sanity"]
    errs = pc.validate(card)
    assert any("'permutation' sanity spec" in e for e in errs)
    assert any("'subsample' sanity spec" in e for e in errs)


def test_zero_direction_claim_needs_no_sanity_specs(card):
    card["direction"] = "zero"
    card["spec_plan"] = [s for s in card["spec_plan"] if s["role"] != "sanity"]
    assert pc.validate(card) == []


def test_structural_spec_errors(card):
    card["spec_plan"][1]["role"] = "primary"
    card["spec_plan"][2]["spec_id"] = "x_explore"
    card["spec_plan"][3]["claim_id"] = "not_a_claim"
    card["spec_plan"].append({**card["spec_plan"][0]})
    errs = " | ".join(pc.validate(card))
    assert "exactly one primary" in errs
    assert "x_ ids are reserved" in errs
    assert "not a claim on this card" in errs
    assert "duplicate spec_id" in errs


def test_calibration_spec_needs_a_cited_table(card):
    card["spec_plan"][3] = {**card["spec_plan"][3], "role": "calibration", "spec_id": "calib"}
    assert any("NOT APPLICABLE" in e for e in pc.validate(card))
    card["spec_plan"][3]["source"] = {"doi": "10.1111/lsq.12440", "table": "Table 2"}
    assert pc.validate(card) == []


def test_reproduction_only_plan(card):
    r27 = _cards()[27]
    assert pc.validate(r27) == []
    bad = copy.deepcopy(r27)
    bad["spec_plan"][0]["role"] = "robustness"
    assert any("reproduction-only plan" in e for e in pc.validate(bad))


def test_equivalence_bound_required_unless_gate_has_sesoi(card):
    card["equivalence_bound"] = None
    assert any("equivalence_bound" in e for e in pc.validate(card))
    assert pc.validate(card, gate={"sesoi": "2pp, a smaller shift is invisible to staff"}) == []


def test_decision_rule_must_be_quoted_verbatim(card):
    gate = {"decision_rule": "Pursue only if the pooled DiD 95 percent interval lies above +5pp."}
    assert any("missing 'decision_rule_quoted'" in e for e in pc.validate(card, gate=gate))
    card["decision_rule_quoted"] = "the pooled DiD 95 percent interval lies above +5pp"
    assert pc.validate(card, gate=gate) == []
    card["decision_rule_quoted"] = "the pooled DiD interval is above five points"
    assert any("not a verbatim part" in e for e in pc.validate(card, gate=gate))


def test_changed_threshold_needs_supersedes(card):
    prior = {25: _cards()[25]}
    later = copy.deepcopy(card)
    later["threshold"] = 2.5
    assert any("without 'supersedes'" in e for e in pc.validate(later, prior_cards=prior))
    later["claims"] = []
    later["supersedes"] = "carryover_did"
    assert not any("supersedes" in e for e in pc.validate(later, prior_cards=prior))
    # A reproduction card restates no threshold, which is not a change.
    assert pc.validate(_cards()[27], prior_cards=prior) == []


# --------------------------------------------------------------------------
# Gap evidence (M19)
# --------------------------------------------------------------------------

@pytest.mark.parametrize("r,post", [(25, "073"), (28, "082"), (29, "085")])
def test_season2_gap_c_is_constructed(r, post):
    rec = pc.gap_record(_cards()[r])
    assert rec == {"gap_type": "c", "c_constructed": True}, post


def test_constructed_c_without_own_derivation_fails(card):
    card["gap"]["evidence"]["own_derivation"] = False
    assert any("c_constructed" in e for e in pc.validate(card))


def test_quoted_exact_c_is_observed_contradiction(card):
    ev = card["gap"]["evidence"]
    for side in ("lit_a", "lit_b"):
        ev[side].update(quoted_prediction="A verbatim sentence.", location="page 12", quantity_match="exact")
    ev["own_derivation"] = False
    assert pc.gap_record(card)["c_constructed"] is False
    assert pc.validate(card) == []
    ev["lit_b"]["location"] = "somewhere"
    assert any("location must be abstract" in e for e in pc.validate(card))


def test_gap_a_and_b_requirements(card):
    card["gap"] = {"gap_type": "a", "evidence": {"theory_source": "not a doi"}}
    errs = " | ".join(pc.validate(card))
    assert "theory_source" in errs and "quoted_prediction" in errs and "magnitude" in errs
    card["gap"] = {"gap_type": "b", "evidence": {"measure": "audit dyads"}}
    errs = " | ".join(pc.validate(card))
    assert "why_unavailable" in errs and "available_since" in errs
    card.pop("gap")
    assert any("gap: missing" in e for e in pc.validate(card))


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------

def test_extract_card_takes_the_last_block(card):
    older = dict(card, claim_id="old")
    text = (f"## Prediction to Test\n\n```card\n{json.dumps(older)}\n```\n\nRevised:\n\n"
            f"```card\n{json.dumps(card)}\n```\n")
    assert pc.extract_card(text)["claim_id"] == "carryover_did"
    assert pc.extract_card("no card here") is None
    broken = pc.extract_card("```card\n{not json}\n```")
    assert "_parse_error" in broken
    assert pc.validate(broken)[0].startswith("card block is not valid JSON")
    assert pc.validate(None) == ["no ```card block found"]


def test_continuation_message_lists_errors():
    msg = pc.continuation_message(["spec a: bad", "gap: missing"])
    assert "- spec a: bad" in msg and "- gap: missing" in msg and "```card" in msg


# --------------------------------------------------------------------------
# Commit
# --------------------------------------------------------------------------

def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


@pytest.fixture
def repo(tmp_path):
    r = tmp_path / "scratch"
    r.mkdir()
    _git(r, "init", "-q")
    _git(r, "config", "user.email", "test@example.com")
    _git(r, "config", "user.name", "test")
    (r / "README").write_text("x")
    _git(r, "add", "README")
    _git(r, "commit", "-q", "-m", "init")
    return r


def test_commit_card_writes_json_index_and_its_own_git_commit(repo, card):
    cdir = repo / "knowledge" / "prediction_cards"
    (repo / "unrelated.txt").write_text("staged elsewhere")
    _git(repo, "add", "unrelated.txt")
    out = pc.commit_card(25, card, repo / "forum" / "073_literature_scout.md", cards_dir=cdir,
                         git_commit=True, data_exposed=True)
    assert out == cdir / "R25.json"
    assert json.loads(out.read_text()) == card
    row = pc.load_index(cdir)[0]
    assert row["round"] == 25 and row["claim_ids"] == ["carryover_did"]
    assert row["sha256"] == pc.card_sha(card)
    assert row["data_exposed"] is True and row["c_constructed"] is True and row["gap_type"] == "c"
    assert row["git_head"]
    files = _git(repo, "show", "--name-only", "--format=", "HEAD").split()
    assert sorted(files) == ["knowledge/prediction_cards/R25.json", "knowledge/prediction_cards/index.jsonl"]
    assert "unrelated.txt" in _git(repo, "diff", "--cached", "--name-only")
    # A dummy Analyst result written afterwards is committed after the card.
    res = repo / "workspace" / "r25" / "results" / "pooled_did.json"
    res.parent.mkdir(parents=True)
    res.write_text("{}")
    _git(repo, "add", "-f", str(res.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "analyst")
    log = _git(repo, "log", "--format=%s").splitlines()
    assert log[0] == "analyst" and log[1].startswith("Card R25")


def test_commit_card_refuses_invalid_and_changed_cards(tmp_path, card):
    cdir = tmp_path / "cards"
    bad = dict(card, spec_plan=[])
    with pytest.raises(ValueError):
        pc.commit_card(25, bad, None, cards_dir=cdir)
    pc.commit_card(25, card, None, cards_dir=cdir)
    pc.commit_card(25, card, None, cards_dir=cdir)          # identical: idempotent
    assert len(pc.load_index(cdir)) == 1
    with pytest.raises(FileExistsError):
        pc.commit_card(25, dict(card, threshold=4.0), None, cards_dir=cdir, check=False)


def test_commit_card_defaults_bound_to_gate_sesoi(tmp_path, card):
    card["equivalence_bound"] = None
    out = pc.commit_card(25, card, None, cards_dir=tmp_path / "c", gate={"sesoi": "2.5pp (staff notice)"})
    assert json.loads(out.read_text())["equivalence_bound"] == 2.5


def test_data_exposed_from_trace():
    touch = [{"message": {"content": [{"type": "tool_use", "name": "Bash",
                                       "input": {"command": "python3 -c 'pd.read_parquet(\"data/dyads_16_22_v9.parquet\")'"}}]}}]
    clean = [{"message": {"content": [{"type": "tool_use", "name": "Bash",
                                       "input": {"command": "curl https://api.openalex.org/works"}}]}}]
    assert pc.data_exposed_from_trace(touch) is True
    assert pc.data_exposed_from_trace(clean) is False


# --------------------------------------------------------------------------
# Quantities ledger, replayed on Season 2
# --------------------------------------------------------------------------

@pytest.fixture
def ledger(tmp_path):
    cards = _cards()
    meta = _meta(cards)
    q = tmp_path / "quantities.jsonl"
    rows = {}
    for start, end in ((25, 27), (28, 30)):
        for r in range(start, end + 1):
            for row in pc.ingest_results(r, cards[r], _results(r), arc_start=start, cards=cards,
                                         meta=meta, quantities_path=q):
                rows[(r, row["spec_id"])] = row
    return q, rows


def test_replay_r27_is_reproduction_only_and_its_tost_margin_is_post_hoc(ledger):
    q, rows = ledger
    assert _cards()[27]["kind"] == "reproduction"
    assert rows[(27, "placebo_tost")]["status"] == "post_hoc"
    assert "after estimate in R25" in rows[(27, "placebo_tost")]["reason"]
    assert rows[(27, "repro_pooled_did")]["status"] == "confirmatory"
    assert rows[(27, "repro_pooled_did")]["quantity_id"] == "carryover_did"


def test_replay_r29_h2a_h2b_post_hoc_and_absorption_step_exploratory(ledger):
    q, rows = ledger
    assert rows[(28, "x_absorption_only")]["status"] == "exploratory"
    for spec in ("step_model", "step_reweighted"):          # H2a and H2b
        assert rows[(29, spec)]["status"] == "post_hoc"
        assert "after estimate in R28" in rows[(29, spec)]["reason"]
    assert pc.quantity_status("absorption_deficit", pc.load_quantities(q), since_round=28) == "exploratory"
    assert rows[(30, "step_cond_incshare")]["status"] == "exploratory"
    # The pre-committed premise margin is not post hoc.
    assert rows[(29, "tost_yr1_strict")]["status"] == "confirmatory"


def test_replay_opening_round_rows_are_confirmatory(ledger):
    q, rows = ledger
    for spec in ("pooled_did", "placebo_did", "cohort1_did", "alt_treatment_did"):
        assert rows[(25, spec)]["status"] == "confirmatory"
    assert rows[(25, "sanity_permutation")]["status"] == "not_computable"
    assert pc.quantity_status("carryover_did", pc.load_quantities(q)) == "confirmatory"


def test_x_spec_is_exploratory_and_ingest_is_idempotent(tmp_path):
    cards = _cards()
    q = tmp_path / "q.jsonl"
    rdir = tmp_path / "results"
    rdir.mkdir()
    (rdir / "x_extra.json").write_text(json.dumps({"estimate": 1.0, "ci_low": 0.1, "ci_high": 1.9, "n": 50}))
    res = pc.load_results(rdir=rdir)
    rows = pc.ingest_results(25, cards[25], res, arc_start=25, cards=cards, meta=_meta(cards), quantities_path=q)
    assert rows[0]["status"] == "exploratory" and rows[0]["spec_id"] == "x_extra"
    assert pc.ingest_results(25, cards[25], res, arc_start=25, cards=cards, meta=_meta(cards),
                             quantities_path=q) == []


def test_late_card_makes_first_estimate_exploratory(tmp_path):
    cards = _cards()
    meta = {**_meta(cards), 25: {"committed_at": "2026-08-24T00:45:00-04:00"}}
    rows = pc.ingest_results(25, cards[25], _results(25), arc_start=25, cards=cards, meta=meta,
                             quantities_path=tmp_path / "q.jsonl")
    assert {r["status"] for r in rows if r["spec_id"] == "pooled_did"} == {"exploratory"}


def test_ledger_for_prompt(ledger):
    q, _ = ledger
    text = pc.ledger_for_prompt(28, quantities_path=q)
    assert "absorption_deficit" in text and "post_hoc" in text and "R25" not in text


# --------------------------------------------------------------------------
# Prompt-facing views
# --------------------------------------------------------------------------

def test_compare_card_numbers_come_from_results():
    card = _cards()[30]
    table = pc.compare_card(card, _results(30))
    assert "## Card vs Observed" in table
    assert "-0.35 [-1.60, +0.90]" in table
    assert "NOT COMPUTABLE" in table
    assert "| x_first_stage | exploratory |" in table
    missing = pc.compare_card(card, {})
    assert missing.count("no results file") == len(card["spec_plan"])


def test_analyst_view_withholds_direction_thresholds_and_meaning():
    card = _cards()[28]
    view = pc.analyst_view(card)
    blob = json.dumps(view)
    for key in ("direction", "threshold", "supporting_result", "falsifying_result", "decision_rule_quoted",
                "equivalence_bound", "what_result_would_mean", "gap"):
        assert f'"{key}"' not in blob
    assert [s["spec_id"] for s in view["spec_plan"]] == [s["spec_id"] for s in card["spec_plan"]]
    assert view["card_sha"] == pc.card_sha(card)


# --------------------------------------------------------------------------
# Data schema summary
# --------------------------------------------------------------------------

def test_data_schema_lists_columns_and_rows_without_values(tmp_path):
    import pyarrow as pa
    import pyarrow.parquet as pq
    d = tmp_path / "processed"
    d.mkdir()
    pq.write_table(pa.table({"bill_id": ["SECRET_BILL_1", "SECRET_BILL_2"], "passed": [1, 0]}),
                   d / "master_bills_22.parquet")
    text = data_schema.render([("KNA processed data (KBL_DATA)", d), ("kr-hearings data (data/)", tmp_path / "none")])
    assert "### master_bills_22.parquet (2 rows)" in text
    assert "| bill_id | string |" in text and "| passed | int64 |" in text
    assert "SECRET_BILL" not in text
    assert str(tmp_path) not in text and "/Users/" not in text
    assert "Not available on this machine." in text
    out = data_schema.write(tmp_path / "data_schema.md", [("x", d)])
    assert out.read_text().startswith("# Data schema")

"""Verdict of record (M10a) and scripted binding checks (M10b).

Every path is redirected to tmp_path. The Season 2 Critic posts are read from
tests/fixtures/season2_replay/forum (copies of forum/073-090)."""

import copy
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import prediction_card as pc  # noqa: E402
import taxonomy_monitor as tm  # noqa: E402
import verdict as v  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "season2_replay"
CRITIC_POSTS = {25: "075_critic.md", 26: "078_critic.md", 27: "081_critic.md",
                28: "084_critic.md", 29: "087_critic.md", 30: "090_critic.md"}


def _timeline() -> dict:
    return json.loads((FIX / "timeline.json").read_text(encoding="utf-8"))


def _cards() -> dict:
    return {int(p.stem[1:]): json.loads(p.read_text(encoding="utf-8")) for p in (FIX / "cards").glob("R*.json")}


def _results() -> dict:
    return {r: pc.load_results(rdir=FIX / "results" / f"r{r}") for r in range(25, 31)}


@pytest.fixture
def env(tmp_path, monkeypatch):
    """verdict.py pointed at a scratch repo holding copies of the Season 2 posts."""
    forum = tmp_path / "forum"
    shutil.copytree(FIX / "forum", forum)
    know = tmp_path / "knowledge"
    know.mkdir()
    agents = tmp_path / "agents.json"
    agents.write_text(json.dumps({"forum_config": {"stage2": {}}}), encoding="utf-8")
    monkeypatch.setattr(v, "BASE_DIR", tmp_path)
    monkeypatch.setattr(v, "FORUM_DIR", forum)
    monkeypatch.setattr(v, "KNOWLEDGE_DIR", know)
    monkeypatch.setattr(v, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(v, "WORKSPACE_DIR", tmp_path / "workspace")
    monkeypatch.setattr(v, "AGENTS_FILE", agents)
    monkeypatch.setattr(v, "VERDICTS_FILE", know / "verdicts.jsonl")
    monkeypatch.setattr(v, "SHIFTS_FILE", know / "verdict_shifts.jsonl")
    monkeypatch.setattr(v, "ACTIVE_ARC_FILE", know / "active_arc.json")
    monkeypatch.setattr(v, "PRECHECKS_DIR", know / "prechecks")
    monkeypatch.setattr(pc, "BASE_DIR", tmp_path)
    monkeypatch.setattr(pc, "KNOWLEDGE_DIR", know)
    monkeypatch.setattr(pc, "WORKSPACE_DIR", tmp_path / "workspace")
    monkeypatch.setattr(pc, "CARDS_DIR", know / "prediction_cards")
    monkeypatch.setattr(pc, "CARD_INDEX", know / "prediction_cards" / "index.jsonl")
    monkeypatch.setattr(pc, "QUANTITIES_FILE", know / "quantities.jsonl")
    return tmp_path


def _set_stage2(env, **flags):
    (env / "agents.json").write_text(json.dumps({"forum_config": {"stage2": flags}}), encoding="utf-8")


def _structured(post_name: str, **over) -> dict:
    """A schema-shaped structured verdict built from the post's YAML block."""
    y = v.parse_scoring_block((FIX / "forum" / post_name).read_text(encoding="utf-8"))
    out = {k: y[k] for k in (*v.SCORE_FIELDS, *v.LABEL_FIELDS, "falsifier_tested", "verdict", "one_line")}
    out.update(prior_status="overturned", headline_basis="prespecified")
    out.update(over)
    return out


# --------------------------------------------------------------------------
# Schema
# --------------------------------------------------------------------------

def test_schema_file_matches_generator_and_taxonomy_constants():
    schema = v.load_schema()
    assert schema == v.build_schema(), "run python3 verdict.py --write-schema"
    props = schema["properties"]
    assert props["opportunity_pattern"]["enum"] == list(tm.OPPORTUNITY)
    assert props["method_paradigm"]["enum"] == list(tm.METHOD)
    assert props["operation"]["enum"] == list(tm.OPERATION)


def test_schema_carries_sharpened_fields():
    props = v.load_schema()["properties"]
    assert props["prior_status"]["enum"] == ["supported", "overturned", "inconclusive", "not_tested"]
    assert props["headline_basis"]["enum"] == ["prespecified", "exploratory"]
    assert props["falsifier_tested"]["enum"] == ["yes", "no", "not_applicable"]
    assert props["verdict"]["enum"] == ["pursue", "revise", "archive"]
    for k in v.SCORE_FIELDS:
        assert props[k] == {**props[k], "type": "integer", "minimum": 0, "maximum": 4}
    assert props["one_line"]["maxLength"] == 400
    required = set(v.load_schema()["required"])
    assert {"prior_status", "headline_basis", "verdict", "one_line", *v.SCORE_FIELDS} <= required


def test_schema_description_has_no_round_count_or_monitor_text():
    blob = json.dumps(v.load_schema()).lower()
    for banned in ("entropy", "bridge cap", "min_arc_rounds", "three rounds", "3 rounds", "depth"):
        assert banned not in blob


def test_schema_errors_flag_missing_and_out_of_range_fields():
    good = _structured("090_critic.md")
    assert v.schema_errors(good) == []
    bad = dict(good, research_novelty=5)
    bad.pop("prior_status")
    errs = v.schema_errors(bad)
    assert any("prior_status" in e for e in errs)
    assert any("5 > 4" in e for e in errs)
    assert v.schema_errors(dict(good, extra_field=1))


# --------------------------------------------------------------------------
# YAML parsing on the six Season 2 Critic posts
# --------------------------------------------------------------------------

@pytest.mark.parametrize("round_num,post", sorted(CRITIC_POSTS.items()))
def test_parse_scoring_block_on_season2_critic_posts(round_num, post):
    parsed = v.parse_scoring_block((FIX / "forum" / post).read_text(encoding="utf-8"))
    assert parsed["verdict"] == "pursue"
    assert parsed["falsifier_tested"] == "yes"
    assert parsed["research_novelty"] == 4
    assert parsed["actionability"] == 4
    assert parsed["one_line"] and len(parsed["one_line"]) > 40
    assert parsed["opportunity_pattern"] in tm.OPPORTUNITY
    assert parsed["method_paradigm"] in tm.METHOD
    assert parsed["operation"] in tm.OPERATION


def test_parse_recorded_values_on_075_084_090():
    p075 = v.parse_scoring_block((FIX / "forum" / "075_critic.md").read_text(encoding="utf-8"))
    assert (p075["empirical_rigor"], p075["theoretical_connection"]) == (3, 4)
    assert p075["one_line"].startswith("The pre-registered carry-over prior is overturned")
    p084 = v.parse_scoring_block((FIX / "forum" / "084_critic.md").read_text(encoding="utf-8"))
    assert (p084["empirical_rigor"], p084["theoretical_connection"]) == (4, 3)
    assert p084["opportunity_pattern"] == "puzzle_contradiction"
    p090 = v.parse_scoring_block((FIX / "forum" / "090_critic.md").read_text(encoding="utf-8"))
    assert p090["opportunity_pattern"] == "explanation_gap"
    assert p090["operation"] == "measure"
    assert p090["one_line"].endswith("Paper E is cleared for drafting.")


def test_last_scoring_block_is_used_not_the_first_regex_hit():
    text = (FIX / "forum" / "084_critic.md").read_text(encoding="utf-8")
    later = ("\n\n## Addendum\n\n```yaml\nscoring:\n  research_novelty: 2/4\n  empirical_rigor: 3/4\n"
             "  theoretical_connection: 3/4\n  actionability: 2/4\n  opportunity_pattern: puzzle_contradiction\n"
             "  method_paradigm: empirical_mapping\n  operation: measure\n  falsifier_tested: yes\n"
             "  verdict: revise\n  one_line: \"Superseded after the rerun.\"\n```\n")
    parsed = v.parse_scoring_block(text + later)
    assert parsed["verdict"] == "revise"
    assert parsed["research_novelty"] == 2
    assert parsed["one_line"] == "Superseded after the rerun."
    # The pre-v2.1 regex takes the first hit and would have kept pursue.
    assert v.regex_legacy(text + later)["verdict"] == "pursue"


def test_yaml_blocks_without_a_verdict_key_are_ignored():
    text = ("```yaml\nverdict: archive\none_line: \"an example quoted early\"\n```\n\n"
            "```yaml\nround: R31\nresult: fine\n```\n\n"
            "```yaml\nscoring:\n  verdict: pursue\n  one_line: \"final\" # trailing comment\n```\n")
    parsed = v.parse_scoring_block(text)
    assert parsed["verdict"] == "pursue"
    assert parsed["one_line"] == "final"
    assert len(v.scoring_blocks(text)) == 2


def test_multiline_quoted_one_line_is_joined():
    text = "```yaml\nscoring:\n  verdict: revise\n  one_line: \"first part\n    second part\"\n```\n"
    assert v.parse_scoring_block(text)["one_line"] == "first part second part"


def test_post_without_scoring_block_falls_back_to_legacy_regex(env):
    (env / "forum" / "090_critic.md").write_text("verdict: archive\nfalsifier_tested: no\n", encoding="utf-8")
    row = v.verdict_of_record(30)
    assert row["verdict"] == "archive"
    assert row["source"] == "regex_legacy"


def test_legacy_multi_project_post_uses_the_first_verdict_like_ledger_audit(env):
    """COR-F11: R2 and R3 (006, 009) score two projects. verdict_of_record and
    ledger_audit.tally must give the same legacy verdict, the first verdict
    line, which is what the pre-v2.1 pipeline recorded."""
    import ledger_audit
    block = ("```yaml\nscoring:\n  research_novelty: 3/4\n  empirical_rigor: 2/4\n"
             "  theoretical_connection: 3/4\n  actionability: 2/4\n  verdict: {v}\n"
             "  one_line: \"{line}\"\n```\n")
    text = ("# Review\n\n### Project A\n\n" + block.format(v="revise", line="Blocked by data.")
            + "\n### Project B\n\n" + block.format(v="pursue", line="Feasible now."))
    (env / "forum" / "090_critic.md").write_text(text, encoding="utf-8")
    row = v.verdict_of_record(30)
    assert row["verdict"] == "revise" and row["source"] == "yaml"
    assert row["one_line"] == "Blocked by data." and row["scores"]["empirical_rigor"] == 2
    t = ledger_audit.tally(forum_dir=env / "forum", verdicts_file=env / "knowledge" / "verdicts.jsonl")
    by_round = {x["round"]: x["verdict"] for x in t["posts"]}
    for rnd in range(25, 31):
        assert by_round[rnd] == v.verdict_of_record(rnd)["verdict"], rnd
    # A verdict line in prose before the first block is the first hit for both.
    (env / "forum" / "090_critic.md").write_text("Last round's verdict: archive stood.\n\n" + text,
                                                 encoding="utf-8")
    row = v.verdict_of_record(30)
    assert row["verdict"] == "archive" and row["source"] == "regex_legacy"
    t = ledger_audit.tally(forum_dir=env / "forum", verdicts_file=env / "knowledge" / "verdicts.jsonl")
    assert {x["round"]: x["verdict"] for x in t["posts"]}[30] == "archive"


# --------------------------------------------------------------------------
# Verdict of record
# --------------------------------------------------------------------------

@pytest.mark.parametrize("round_num", range(25, 31))
def test_verdict_of_record_is_pursue_for_each_season2_round(env, round_num):
    row = v.verdict_of_record(round_num)
    assert row["verdict"] == "pursue"
    assert row["source"] == "yaml"
    assert row["legacy"] is True
    assert row["post"].endswith(CRITIC_POSTS[round_num])
    assert row["arc"] == (4 if round_num <= 27 else 5)
    assert not (env / "knowledge" / "verdicts.jsonl").exists()


def test_verdict_of_record_prefers_verdicts_jsonl(env):
    (env / "knowledge" / "verdicts.jsonl").write_text(
        json.dumps({"round": 30, "verdict": "revise", "run_id": "r"}) + "\n", encoding="utf-8")
    assert v.verdict_of_record(30)["verdict"] == "revise"
    assert v.verdict_of_record(29)["verdict"] == "pursue"
    assert v.verdict_of_record(31) is None


def test_record_structured_agreeing_with_yaml(env):
    post = env / "forum" / "090_critic.md"
    row = v.record(30, "5", post, _structured("090_critic.md"), "run-a")
    assert row["verdict"] == "pursue"
    assert row["source"] == "structured"
    assert row["mismatch"] == []
    assert row["prior_status"] == "overturned" and row["headline_basis"] == "prespecified"
    assert row["schema_errors"] == []
    assert row["post"] == "forum/090_critic.md"
    stored = [json.loads(x) for x in (env / "knowledge" / "verdicts.jsonl").read_text().splitlines()]
    assert len(stored) == 1 and stored[0]["run_id"] == "run-a"
    for k in ("round", "arc", "verdict", "falsifier_tested", "prior_status", "headline_basis",
              "source", "mismatch"):
        assert k in row


def test_record_verdict_mismatch_sets_revise(env):
    post = env / "forum" / "084_critic.md"
    row = v.record(28, "5", post, _structured("084_critic.md", verdict="archive"), "run-b")
    assert row["verdict"] == "revise"
    assert row["verdict_critic"] == "archive"
    assert row["verdict_yaml"] == "pursue"
    assert "verdict" in row["mismatch"]
    assert any("mismatch" in o for o in row["overrides"])


def test_record_other_field_mismatch_is_logged_only(env):
    post = env / "forum" / "081_critic.md"
    row = v.record(27, "4", post, _structured("081_critic.md", empirical_rigor=2), "run-c")
    assert row["verdict"] == "pursue"
    assert row["mismatch"] == ["empirical_rigor"]
    assert row["overrides"] == []


def test_record_refuses_a_second_write_for_the_same_round(env):
    post = env / "forum" / "075_critic.md"
    first = v.record(25, "4", post, _structured("075_critic.md"), "run-1")
    again = v.record(25, "4", post, _structured("075_critic.md"), "run-1")
    assert again == first
    other = v.record(25, "4", post, _structured("075_critic.md", verdict="archive"), "run-2")
    assert other["refused_run_id"] == "run-2"
    assert other["verdict"] == "pursue"
    lines = (env / "knowledge" / "verdicts.jsonl").read_text().splitlines()
    assert len(lines) == 1


def test_record_without_structured_uses_yaml(env):
    row = v.record(26, "4", env / "forum" / "078_critic.md", None, "run-d")
    assert row["source"] == "yaml"
    assert row["verdict"] == "pursue"
    assert row["verdict_structured"] is None


def test_record_structured_without_yaml_block(env):
    post = env / "forum" / "999_critic.md"
    post.write_text("# A post with no scoring block\n", encoding="utf-8")
    row = v.record(40, None, post, _structured("090_critic.md"), "run-e")
    assert row["source"] == "structured"
    assert row["yaml_missing"] is True


def test_distribution_flags_a_label_above_70_percent(env):
    d = v.distribution(range(25, 31))
    assert d["n"] == 6 and d["counts"] == {"pursue": 6, "revise": 0, "archive": 0}
    assert d["flagged"] == ["pursue"]
    line = v.distribution_line(range(28, 31), range(25, 31))
    assert "pursue 3/3" in line and "pursue 6/6" in line and "FLAG pursue" in line
    assert v.distribution(range(25, 27))["flagged"] == []   # fewer than 3 verdicts


def test_prompt_note_only_for_overridden_rounds(env):
    assert v.prompt_note(30) == ""
    (env / "knowledge" / "verdicts.jsonl").write_text(json.dumps(
        {"round": 30, "verdict": "revise", "verdict_critic": "pursue",
         "overrides": ["falsifier_tested false: x"]}) + "\n", encoding="utf-8")
    note = v.prompt_note(30)
    assert "revise" in note and "falsifier_tested false" in note


# --------------------------------------------------------------------------
# Stage 2 binding checks, replayed on Season 2 with hand-built cards
# --------------------------------------------------------------------------

def _replay(tmp_path):
    cards, res, tl = _cards(), _results(), _timeline()
    meta = {r: {"committed_at": tl["rounds"][str(r)]["card_committed_at"], "sha256": pc.card_sha(c)}
            for r, c in cards.items()}
    q = tmp_path / "quantities.jsonl"
    for start, end in ((25, 27), (28, 30)):
        for r in range(start, end + 1):
            pc.ingest_results(r, cards[r], res[r], arc_start=start, cards=cards, meta=meta,
                              quantities_path=q)
    starts = {r: tl["rounds"][str(r)]["analyst_start"] for r in cards}
    out = {}
    for start, end in ((25, 27), (28, 30)):
        for r in range(start, end + 1):
            critic = {"verdict": "pursue", "headline_claim_id": tl["critic_headline"][str(r)]}
            out[r] = v.binding_checks(r, None, critic, gate={"start_round": start}, cards=cards,
                                      card_meta=meta, results=res, quantities=pc.load_quantities(q),
                                      prechecks={}, analyst_start=starts, exists=lambda p: bool(p))
    return out


def test_replay_arc4_r27_new_test_false_and_kill_depth_two(tmp_path):
    bc = _replay(tmp_path)
    assert bc[27]["new_test_this_round"] is False
    assert bc[27]["verdict_effective"] == "revise"
    assert bc[27]["kill_depth"] == 2 and bc[27]["kill_rounds"] == [25, 26]
    assert bc[27]["falsifier_tested"] is True
    assert bc[25]["verdict_effective"] == "pursue" and bc[26]["verdict_effective"] == "pursue"


def test_replay_arc5_absorption_headline_never_under_the_falsifier(tmp_path):
    bc = _replay(tmp_path)
    assert bc[28]["falsifier_tested"] is False
    assert "not the claim under the gate's falsifier" in bc[28]["falsifier_reason"]
    assert bc[28]["kill_depth"] == 0
    assert bc[30]["kill_depth"] == 2 and bc[30]["kill_rounds"] == [29, 30]
    assert bc[29]["headline_basis_computed"] == "exploratory"
    assert all(bc[r]["verdict_effective"] == "revise" for r in (28, 29, 30))


def test_replay_distribution_against_season2_record(tmp_path):
    bc = _replay(tmp_path)
    replayed = [bc[r]["verdict_effective"] for r in range(25, 31)]
    assert replayed.count("pursue") == 2 and replayed.count("revise") == 4
    assert replayed.count("archive") == 0
    # Season 2 as recorded was 6 pursue, 0 revise, 0 archive.


def test_binding_nulls_need_a_precommitted_bound(tmp_path):
    cards, res, tl = _cards(), _results(), _timeline()
    meta = {r: {"committed_at": tl["rounds"][str(r)]["card_committed_at"]} for r in cards}
    starts = {r: tl["rounds"][str(r)]["analyst_start"] for r in cards}
    kw = dict(gate={"start_round": 25}, card_meta=meta, results=res, quantities=[], prechecks={},
              analyst_start=starts, exists=lambda p: bool(p))
    assert v.binding_checks(25, None, {"verdict": "pursue"}, cards=cards, **kw)["null_ok"] is True
    no_bound = copy.deepcopy(cards)
    no_bound[25]["equivalence_bound"] = None
    bc = v.binding_checks(25, None, {"verdict": "pursue"}, cards=no_bound, **kw)
    assert bc["null_ok"] is False and bc["verdict_effective"] == "revise"
    late = {**meta, 25: {"committed_at": "2026-08-24T00:45:00-04:00"}}
    bc = v.binding_checks(25, None, {"verdict": "pursue"}, cards=cards, **dict(kw, card_meta=late))
    assert bc["falsifier_tested"] is False and bc["null_ok"] is False


def test_binding_decision_rule_quote_and_expression(tmp_path):
    cards, res, tl = _cards(), _results(), _timeline()
    meta = {r: {"committed_at": tl["rounds"][str(r)]["card_committed_at"]} for r in cards}
    starts = {r: tl["rounds"][str(r)]["analyst_start"] for r in cards}
    rule = "Pursue only if the pooled DiD interval excludes zero and its lower bound exceeds 5pp."
    kw = dict(cards=cards, card_meta=meta, results=res, prechecks={}, analyst_start=starts,
              exists=lambda p: bool(p))
    gate = {"start_round": 25, "decision_rule": rule, "decision_rule_expr": "ci_low(carryover_did) > 5"}
    quant = [{"round": 25, "quantity_id": "carryover_did", "estimate": -0.9, "ci": [-3.0, 1.3]}]
    good = {"verdict": "pursue", "decision_rule_quoted": "the pooled DiD interval excludes zero"}
    bc = v.binding_checks(25, None, good, gate=gate, quantities=quant, **kw)
    assert bc["decision_rule_quote_ok"] is True
    assert bc["decision_rule_expr_ok"] is False
    assert bc["verdict_effective"] == "revise"
    paraphrase = {"verdict": "pursue", "decision_rule_quoted": "the DiD interval must exclude zero"}
    bc = v.binding_checks(25, None, paraphrase, gate=gate, quantities=quant, **kw)
    assert bc["decision_rule_quote_ok"] is False
    assert any("verbatim" in o for o in bc["overrides"])
    legacy = v.binding_checks(25, None, {"verdict": "pursue"}, gate={"start_round": 25}, quantities=quant, **kw)
    assert legacy["decision_rule_quote_ok"] is None and legacy["decision_rule_expr_ok"] is None


def test_binding_blocking_precheck_overrides_pursue(tmp_path):
    pre = {"posts": {"074_data_analyst.md": {"rules": [{"id": "R-06", "status": "FAIL", "blocking": True}]}}}
    cards, res, tl = _cards(), _results(), _timeline()
    meta = {r: {"committed_at": tl["rounds"][str(r)]["card_committed_at"]} for r in cards}
    starts = {r: tl["rounds"][str(r)]["analyst_start"] for r in cards}
    bc = v.binding_checks(25, None, {"verdict": "pursue"}, gate={"start_round": 25}, cards=cards,
                          card_meta=meta, results=res, quantities=[], prechecks=pre,
                          analyst_start=starts, exists=lambda p: bool(p))
    assert bc["blocking_prechecks"] == ["R-06"] and bc["verdict_effective"] == "revise"


def test_eval_rule_expr():
    q = {"a": {"estimate": -3.5, "ci": [-5.2, -1.8]}, "b": {"estimate": 0.2, "ci_low": -0.5, "ci_high": 0.9}}
    assert v.eval_rule_expr("ci_high(a) < 0 and abs(b) < 1", q) is True
    assert v.eval_rule_expr("a > -2 or ci_low(b) > 0", q) is False
    assert v.eval_rule_expr("-6 < a < -2", q) is True
    for bad in ("__import__('os')", "a.real > 0", "unknown > 0", "open('x')"):
        with pytest.raises(ValueError):
            v.eval_rule_expr(bad, q)


def _install_replay_files(env, upto: int):
    """Cards, index, results and sidecars for Arc 4 in the scratch repo."""
    cards, tl = _cards(), _timeline()
    cdir = env / "knowledge" / "prediction_cards"
    for r in range(25, upto + 1):
        pc.commit_card(r, cards[r], None, committed_at=tl["rounds"][str(r)]["card_committed_at"],
                       check=False, cards_dir=cdir)
        rdir = env / "workspace" / f"r{r}" / "results"
        shutil.copytree(FIX / "results" / f"r{r}", rdir)
        for p in rdir.glob("*.json"):
            res = json.loads(p.read_text())
            for k in ("script", "output"):
                if res.get(k):
                    (env / res[k]).parent.mkdir(parents=True, exist_ok=True)
                    (env / res[k]).touch()
        logs = env / "logs" / f"r{r:02d}"
        logs.mkdir(parents=True)
        (logs / f"da_{r}.sidecar.json").write_text(json.dumps(
            {"role": "data_analyst", "created": tl["rounds"][str(r)]["analyst_start"]}))
    (env / "knowledge" / "active_arc.json").write_text(json.dumps({"start_round": 25}))


def test_record_applies_binding_checks_only_when_flag_is_on(env):
    _install_replay_files(env, 27)
    s = _structured("081_critic.md", headline_claim_id="carryover_did")
    off = v.record(27, "4", env / "forum" / "081_critic.md", s, "run-off")
    assert off["verdict"] == "pursue" and "binding" not in off
    (env / "knowledge" / "verdicts.jsonl").unlink()
    _set_stage2(env, binding_checks=True)
    on = v.record(27, "4", env / "forum" / "081_critic.md", s, "run-on")
    assert on["verdict"] == "revise" and on["verdict_critic"] == "pursue"
    assert on["binding"]["kill_depth"] == 2 and on["binding"]["falsifier_tested"] is True
    assert any("new_test_this_round false" in o for o in on["overrides"])


def test_record_binding_crash_does_not_pass_a_pursue(env, monkeypatch):
    _set_stage2(env, binding_checks=True)

    def boom(*a, **k):
        raise RuntimeError("no cards")
    monkeypatch.setattr(v, "binding_checks", boom)
    row = v.record(30, "5", env / "forum" / "090_critic.md", _structured("090_critic.md"), "run-x")
    assert row["verdict"] == "revise"
    assert any("failed to run" in o for o in row["overrides"])


def test_record_order_check_with_claim_sheet_first(env):
    _set_stage2(env, claim_sheet_first=True)
    events = [
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": "forum/089_data_analyst.md"}}]}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Write", "input": {"file_path": "workspace/r30/critic_provisional.json"}}]}},
    ]
    trace = env / "logs" / "trace.jsonl"
    trace.parent.mkdir(parents=True, exist_ok=True)
    trace.write_text("\n".join(json.dumps(e) for e in events))
    row = v.record(30, "5", env / "forum" / "090_critic.md", _structured("090_critic.md"), "run-o",
                   events_paths=[trace])
    assert row["order"] == "order not respected"

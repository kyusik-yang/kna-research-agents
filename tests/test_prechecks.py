"""Precheck rulebook (M14) and gap-quote rule R-11 (M19). No network: DOI
lookups use the fixture cache built from Crossref and OpenAlex on
2026-09-25 (tests/fixtures/season2_replay/doi_cache.json). Every write goes
to tmp_path."""

import gzip
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import prechecks as p  # noqa: E402
import prediction_card as pc  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "season2_replay"
POSTS = sorted((FIX / "forum").glob("*.md"))
KNOWN_ARTIFACTS = {
    "10.18808/jopr.2019.2.5": "073_literature_scout.md",        # registered with a trailing dot
    "10.18808/jopr.2019.2.5.`": "073_literature_scout.md",      # backtick
    "10.1111/j.0092-5853.2005.00125.x**": "085_literature_scout.md",
    "10.1111/j.1540-5907.2005.00126.x": "085_literature_scout.md",   # reported failed guess
    "10.1111/ajps.12518**": "088_literature_scout.md",
}


def _cache() -> dict:
    return json.loads((FIX / "doi_cache.json").read_text(encoding="utf-8"))


def _text(name: str) -> str:
    return (FIX / "forum" / name).read_text(encoding="utf-8")


def _events(*commands, reads=()):
    ev = [{"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Bash", "input": {"command": c}}]}} for c in commands]
    ev += [{"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Read", "input": {"file_path": f}}]}} for f in reads]
    return ev


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    know = tmp_path / "knowledge"
    monkeypatch.setattr(p, "KNOWLEDGE_DIR", know)
    monkeypatch.setattr(p, "PRECHECKS_DIR", know / "prechecks")
    monkeypatch.setattr(p, "ABSTRACTS_FILE", know / "abstracts.jsonl")
    monkeypatch.setattr(p, "ACTIVE_ARC_FILE", know / "active_arc.json")
    monkeypatch.setattr(p, "LOGS_DIR", tmp_path / "logs")
    monkeypatch.setattr(p, "DOI_CACHE_FILE", tmp_path / "logs" / "doi_cache.json")
    monkeypatch.setattr(p, "FORUM_DIR", tmp_path / "forum")
    agents = tmp_path / "agents.json"
    agents.write_text(json.dumps({"forum_config": {"stage2": {}}}))
    monkeypatch.setattr(p, "AGENTS_FILE", agents)
    monkeypatch.setattr(pc, "CARDS_DIR", know / "prediction_cards")
    monkeypatch.setattr(pc, "WORKSPACE_DIR", tmp_path / "workspace")
    shutil.copytree(FIX / "forum", tmp_path / "forum")
    return tmp_path


# --------------------------------------------------------------------------
# R-05 citations (the DOI extractor is Stage 1)
# --------------------------------------------------------------------------

def test_extract_dois_strips_markdown_and_trailing_punctuation():
    text = ("See **10.1111/ajps.12518**, `10.18808/jopr.2019.2.5.` and (doi:10.1111/lsq.12440). "
            "Again 10.1111/AJPS.12518. Also [10.1017/s0003055424001242]; end 10.2307/1958780*")
    assert p.extract_dois(text) == ["10.1111/ajps.12518", "10.18808/jopr.2019.2.5", "10.1111/lsq.12440",
                                    "10.1017/s0003055424001242", "10.2307/1958780"]
    assert p.extract_dois("10.1234/ and 10.12/short") == []


@pytest.mark.parametrize("raw,post", sorted(KNOWN_ARTIFACTS.items()))
def test_known_c9_artifacts_normalize_to_clean_dois(raw, post):
    got = p.extract_dois(_text(post))
    clean = raw.rstrip(".`*")
    assert clean in got
    assert not any(d.endswith(("*", "`", ".")) for d in got)


def test_r05_resolves_markdown_doi_and_flags_no_known_artifact_across_season2():
    cache = _cache()
    flagged = []
    for post in POSTS:
        r = p.rule_r05(post.read_text(encoding="utf-8"), cache, offline=True)
        flagged += [(post.name, d["doi"], d["result"]) for d in r["details"] if d["flag"]]
    assert flagged == [], flagged
    r088 = p.rule_r05(_text("088_literature_scout.md"), cache, offline=True)
    item = next(d for d in r088["details"] if d["doi"] == "10.1111/ajps.12518")
    assert item["result"] == "resolved" and item["source"] == "crossref"
    r085 = p.rule_r05(_text("085_literature_scout.md"), cache, offline=True)
    guess = next(d for d in r085["details"] if d["doi"] == "10.1111/j.1540-5907.2005.00126.x")
    assert guess["result"] == "reported_failed" and guess["flag"] is False
    r073 = p.rule_r05(_text("073_literature_scout.md"), cache, offline=True)
    dot = next(d for d in r073["details"] if d["doi"] == "10.18808/jopr.2019.2.5")
    assert dot["flag"] is False and dot["resolved_as"] == "10.18808/jopr.2019.2.5."


def test_r05_flags_author_and_year_mismatch_and_unchecked():
    cache = _cache()
    text = ("## References\n\nSmith, John. 2023. \"Wrong Author.\" *LSQ*. doi:10.1111/lsq.12440\n"
            "Rainey, Carlisle. 2019. \"Wrong Year.\" *AJPS*. doi:10.1111/ajps.12102\n"
            "Unknown, A. 2020. \"Not Cached.\" doi:10.9999/not.in.cache\n")
    r = p.rule_r05(text, cache, offline=True)
    by = {d["doi"]: d for d in r["details"]}
    assert r["status"] == "FLAG"
    assert by["10.1111/lsq.12440"]["result"].startswith("first author mismatch")
    assert by["10.1111/ajps.12102"]["result"].startswith("year mismatch")
    assert by["10.9999/not.in.cache"]["result"] == "unchecked"


def test_r05_skips_author_check_for_affiliation_fields():
    text = "Bae, Kwanpyo, and Taeyeon Kim. 2018. \"Title.\" *Korea Observer*. doi:10.29152/koiks.2018.49.2.293\n"
    item = p.rule_r05(text, _cache(), offline=True)["details"][0]
    assert item["flag"] is False and item["author_check"].startswith("skipped")


def test_resolve_doi_network_error_is_not_cached(monkeypatch):
    def boom(doi):
        raise ConnectionError("offline")
    monkeypatch.setattr(p, "_crossref", boom)
    cache = {}
    rec = p.resolve_doi("10.1/xyz", cache, delay_s=0)
    assert rec["found"] is None and cache == {}


# --------------------------------------------------------------------------
# Text rules
# --------------------------------------------------------------------------

def test_r04_flags_the_hijackers_attribution_in_085():
    r = p.rule_r04(_text("085_literature_scout.md"), "085_literature_scout.md", FIX / "forum")
    assert r["status"] == "FLAG"
    item = next(d for d in r["details"] if d["quote"] == "hijackers")
    assert item["post"] == "084" and item["flag"] is True and item["line"] == 83


def test_r04_passes_a_quote_that_occurs_in_the_attributed_post():
    text = 'As Critic 084 wrote, "The pre-registered falsifier overturns the learning prior at its premise".'
    r = p.rule_r04(text, "091_literature_scout.md", FIX / "forum")
    assert r["status"] == "PASS"
    assert p.rule_r04("No attributions here.", "091_x.md", FIX / "forum")["status"] == "SKIP"


def test_r09_flags_087_rerun_claim_without_a_matching_trace():
    text = _text("087_critic.md")
    claims = {c["file"] for c in p.rerun_claims(text)}
    assert {"depth.py", "depth2.py"} <= claims
    r = p.rule_r09(text, _events("ls workspace/r29", "cat workspace/r29/BASELINE.md"))
    assert r["status"] == "FLAG"
    assert {d["file"] for d in r["details"] if d["flag"]} >= {"depth.py", "depth2.py"}
    ok = p.rule_r09(text, _events("cd workspace && python3 r29/depth.py", "python3 workspace/r29/depth2.py"))
    assert ok["status"] == "PASS"
    assert p.rule_r09(text, None)["status"] == "SKIP"


DELEGATED = "orchestrating Claude session, signed under the researcher's standing delegation of 2026-09-25"


def test_r10_vocabulary_and_provenance():
    text = ("The threshold was pre-registered.\nIt was pre-registered in card R25 (commit abc1234).\n"
            "Per the signed failure condition we continue.\nThe prior was set by the researcher.\n")
    claude_gate = {"drafted_by": "orchestrating Claude session (claude-opus-5-5)", "signed_by": DELEGATED}
    r = p.rule_r10(text, claude_gate)
    terms = [d["term"].lower() for d in r["details"]]
    assert terms.count("pre-registered") == 1
    assert "signed failure condition" in terms
    assert any("set by the researcher" in t for t in terms)
    assert r["status"] == "FLAG" and r["blocking"] is False
    human = p.rule_r10("The prior was set by the researcher.", {"drafted_by": "researcher", "signed_by": "researcher"})
    assert human["status"] == "PASS"


@pytest.mark.parametrize("drafted", ["researcher", "claude_proposed_researcher_edited",
                                     "orchestrating Claude session (claude-opus-5-5)", None])
def test_r10_delegation_signer_never_counts_as_the_researcher(drafted):
    """FID-F4 (D-10): the delegation signer contains the word 'researcher', so a
    substring test let 'set by the researcher' pass. The exemption keys on
    signed_by naming the researcher."""
    r = p.rule_r10("The prior was set by the researcher.", {"drafted_by": drafted, "signed_by": DELEGATED})
    assert r["status"] == "FLAG"
    assert any("set by the researcher" in d["term"].lower() for d in r["details"])
    # A gate the researcher signed (the retro-annotated R25 and R28 entries) may be described that way.
    signed = p.rule_r10("The prior was set by the researcher.",
                        {"drafted_by": drafted, "signed_by": "researcher, selected from a Claude-drafted "
                                                             "menu on 2026-08-24"})
    assert signed["status"] == "PASS"
    assert p.rule_r10("The prior was set by the researcher.", {})["status"] == "FLAG"   # unrecorded


def test_r08_upgrade_needs_an_output_file_and_downgrade_a_reason():
    text = ("## Findings Status\n\n| Finding | Change | Evidence |\n|---|---|---|\n"
            "| Step survives | preliminary → confirmed | reran depth.py |\n"
            "| Levels gap | preliminary → overturned | committee FE removes it entirely |\n"
            "| Dose tilt | preliminary → contested | |\n"
            "| Absorption | preliminary → confirmed | workspace/r29/results/step_model.json |\n")
    r = p.rule_r08(text, 29)
    res = [(d["change"], d["flag"]) for d in r["details"]]
    assert res == [("preliminary -> confirmed", True), ("preliminary -> overturned", False),
                   ("preliminary -> contested", True), ("preliminary -> confirmed", False)]


# --------------------------------------------------------------------------
# Card and results rules
# --------------------------------------------------------------------------

def _analyst_post(tmp_path, number: str) -> Path:
    post = tmp_path / "093_data_analyst.md"
    post.write_text("# R31\n\n## Card vs Observed\n\n| Spec | Observed | N |\n|---|---|---|\n"
                    f"| primary | {number} [-3.01, +1.30] | 278 |\n\n## Next\n")
    return post


def test_r02_flags_a_table_number_no_script_produced(tmp_path):
    res = {"primary": {"estimate": -0.86, "ci_low": -3.01, "ci_high": 1.30, "n": 278}}
    good = p.rule_r02(_analyst_post(tmp_path, "-0.86").read_text(), res, None)
    assert good["status"] == "PASS"
    bad = p.rule_r02(_analyst_post(tmp_path, "-1.42").read_text(), res, None)
    assert bad["status"] == "FLAG" and [d["number"] for d in bad["details"]] == ["-1.42"]
    traced = p.rule_r02(_analyst_post(tmp_path, "-1.42").read_text(), {}, [
        {"message": {"content": [{"type": "tool_result", "content": "est -1.42 lo -3.01 hi 1.30 n 278"}]}}])
    assert traced["status"] == "PASS"
    assert p.rule_r02("text", {}, None)["status"] == "SKIP"


def test_r06_falsifier_output_must_exist():
    gate_card = json.loads((FIX / "cards" / "R25.json").read_text())
    res = {25: pc.load_results(rdir=FIX / "results" / "r25")}
    assert p.rule_r06(gate_card, res, exists=lambda x: bool(x))["status"] == "PASS"
    missing_out = p.rule_r06(gate_card, res, exists=lambda x: bool(x) and not str(x).endswith(".json"))
    assert missing_out["status"] == "FLAG" and "output" in missing_out["details"][0]["result"]
    assert p.rule_r06(gate_card, {25: {}})["status"] == "FLAG"
    assert p.rule_r06(None, {})["status"] == "SKIP"


def test_r01_card_conformance():
    card = json.loads((FIX / "cards" / "R30.json").read_text())
    res = pc.load_results(rdir=FIX / "results" / "r30")
    assert p.rule_r01(card, res)["status"] == "PASS"
    res2 = {k: v for k, v in res.items() if k != "boundary_deepening"}
    res2["extra_unplanned"] = {"estimate": 1}
    r = p.rule_r01(card, res2)
    flagged = {d["spec_id"] for d in r["details"] if d["flag"]}
    assert flagged == {"boundary_deepening", "extra_unplanned"}


def test_r07_null_claims_need_mde_or_tost():
    card = json.loads((FIX / "cards" / "R25.json").read_text())
    res = pc.load_results(rdir=FIX / "results" / "r25")
    r = p.rule_r07(res, card, {"sesoi": "2pp"})
    by = {d["spec_id"]: d for d in r["details"]}
    assert by["pooled_did"]["flag"] is False           # carries an MDE
    assert by["placebo_did"]["flag"] is True           # null with neither
    tost = {"placebo_tost": {"estimate": -0.85, "ci_low": -2.41, "ci_high": 0.70, "reported_null": True,
                             "tost_p": 0.03, "equivalence_margin": 2.5}}
    wide = p.rule_r07(tost, None, {"sesoi": "2pp"})
    assert "wider than the gate's sesoi" in wide["details"][0]["result"]


def test_r11_gap_quote_verbatim_passes_and_paraphrase_fails():
    cache = _cache()
    card = json.loads((FIX / "cards" / "R28.json").read_text())
    r = p.rule_r11(card, cache, abstracts={}, offline=True)
    by = {d["side"]: d for d in r["details"]}
    assert by["lit_a"]["flag"] is False and by["lit_a"]["ratio"] >= 0.9
    assert by["lit_b"]["result"] == "no quoted prediction"
    card["gap"]["evidence"]["lit_a"]["quoted_prediction"] = (
        "Legislators get better at passing bills the longer they serve in office.")
    para = p.rule_r11(card, cache, abstracts={}, offline=True)
    assert next(d for d in para["details"] if d["side"] == "lit_a")["flag"] is True
    card["gap"]["evidence"]["lit_a"]["location"] = "page 360"
    page = p.rule_r11(card, cache, abstracts={}, offline=True)
    assert "unverified full-text quote" in next(d for d in page["details"] if d["side"] == "lit_a")["result"]


def test_quote_ratio_uses_abstract_sentences():
    ab = _cache()["10.1111/ajps.12472"]["abstract"]
    q = ("Counting these “hitchhiker” bills as additional cases of bill sponsorship success reveals a "
         "more productive, less hierarchical, and less partisan lawmaking process.")
    assert p.quote_ratio(q, ab) >= 0.99
    assert p.quote_ratio("Hitchhikers make Congress look more inclusive.", ab) < 0.9


# --------------------------------------------------------------------------
# Runner, traces and rates
# --------------------------------------------------------------------------

def test_run_all_writes_only_to_the_redirected_prechecks_dir(isolated):
    out = p.run_all(isolated / "forum" / "087_critic.md", "critic", 29, offline=True, cache=_cache(),
                    gate={"drafted_by": "orchestrating Claude session", "signed_by": "unrecorded"},
                    events=_events("ls"))
    ids = [r["id"] for r in out["rules"]]
    assert ids == ["R-04", "R-05", "R-08", "R-09", "R-10"]
    assert out["mode"] == "FLAG" and out["blocking_failed"] is False
    assert all(r["status"] != "FAIL" for r in out["rules"])
    stored = json.loads((isolated / "knowledge" / "prechecks" / "R29.json").read_text())
    assert "087_critic.md" in stored["posts"]
    assert stored["rates"]["R-09"]["FLAG"] == 1
    assert p.flag_rates(isolated / "knowledge" / "prechecks")["R-09"][29]["FLAG"] == 1


def test_promotion_only_for_listed_promotable_rules(isolated):
    (isolated / "agents.json").write_text(json.dumps(
        {"forum_config": {"precheck_fail_rules": ["R-06", "R-10"]}}))
    gate_card = json.loads((FIX / "cards" / "R25.json").read_text())
    post = isolated / "forum" / "093_data_analyst.md"
    post.write_text("# R31\n\nThe margin was pre-registered.\n")
    out = p.run_all(post, "data_analyst", 25, offline=True,
                    cache=_cache(), gate={}, card=gate_card, results={}, gate_card=gate_card,
                    results_by_round={25: {}}, write=False)
    by = {r["id"]: r for r in out["rules"]}
    assert by["R-06"]["status"] == "FAIL" and by["R-06"]["blocking"] is True
    assert by["R-10"]["status"] == "FLAG"          # never promoted
    assert out["blocking_failed"] is True
    assert not (isolated / "knowledge" / "prechecks").exists()


def test_scout_run_includes_gap_quotes_only_with_flag(isolated):
    card = json.loads((FIX / "cards" / "R28.json").read_text())
    kw = dict(offline=True, cache=_cache(), gate={}, card=card, abstracts={})
    ids = [r["id"] for r in p.run_all(isolated / "forum" / "082_literature_scout.md", "literature_scout",
                                      28, **kw)["rules"]]
    assert "R-11" not in ids
    (isolated / "agents.json").write_text(json.dumps({"forum_config": {"stage2": {"gap_c_quotes": True}}}))
    ids = [r["id"] for r in p.run_all(isolated / "forum" / "082_literature_scout.md", "literature_scout",
                                      28, **kw)["rules"]]
    assert "R-11" in ids


def test_load_trace_accepts_jsonl_array_and_gz(tmp_path):
    ev = _events("python3 a.py")
    (tmp_path / "a.jsonl").write_text("\n".join(json.dumps(e) for e in ev) + "\nnot json\n")
    (tmp_path / "b.json").write_text(json.dumps(ev))
    with gzip.open(tmp_path / "c.jsonl.gz", "wt") as f:
        f.write("\n".join(json.dumps(e) for e in ev))
    for name in ("a.jsonl", "b.json", "c.jsonl.gz"):
        assert p.bash_commands(p.load_trace(tmp_path / name)) == ["python3 a.py"]
    both = p.load_trace([tmp_path / "a.jsonl", tmp_path / "b.json"])
    assert len(p.tool_calls(both)) == 2
    assert p.load_trace(ev) == ev and p.load_trace(None) == []

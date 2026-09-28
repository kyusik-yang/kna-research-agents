"""Arc slate (M24): isolated candidate calls through a stubbed claude_cli
(never the real binary), a slate file without ranking or arc commitments,
the trace check, the taste log, and gate stubs with truthful provenance
(D-10 --auto-sign). Every path is redirected to tmp_path."""

import hashlib
import json
import re
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import arc_slate as sl  # noqa: E402
import topic_diversity as td  # noqa: E402


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

@dataclass
class FakeResult:
    ok: bool = True
    failure: str = "ok"
    structured: dict | None = None
    run_id: str = "run_x"
    model: str | None = "claude-opus-5-5"
    events_paths: list = field(default_factory=list)


def _candidate(topic: str) -> dict:
    return {
        "status": "candidate",
        "question": f"Does {topic} change bill passage?",
        "quantity": f"passage rate of {topic} bills", "population": "17th-22nd Assembly members",
        "comparison": f"{topic} members versus others", "outcome": "bill passed plenary",
        "prediction": f"{topic} members pass 5 points fewer bills",
        "premise": f"{topic} is recorded for every member",
        "closest_existing_answer": "Kim 2020, doi:10.1/x",
        "gap": {"gap_type": "c",
                "lit_a": {"doi": "10.1/a", "quoted_prediction": "A predicts more.", "location": "abstract",
                          "quantity_match": "exact"},
                "lit_b": {"doi": "10.1/b", "quoted_prediction": "B predicts fewer.", "location": "p. 4",
                          "quantity_match": "inferred"}},
    }


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
        cwd = kw.get("cwd")
        self.calls[-1]["cwd_existed"] = bool(cwd and Path(cwd).is_dir())
        return self.result_fn(len(self.calls), task, prompt_text, kw)


def _bow_embed(texts, name=None):
    out = []
    for t in texts:
        v = np.zeros(512, dtype=np.float32)
        for w in re.findall(r"\w+", t.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 512] += 1.0
        n = float(np.linalg.norm(v)) or 1.0
        out.append(v / n)
    return np.vstack(out) if out else np.zeros((0, 512), dtype=np.float32)


@pytest.fixture(autouse=True)
def paths(tmp_path, monkeypatch):
    """Redirect every file arc_slate or the diversity guard could touch."""
    know = tmp_path / "knowledge"; know.mkdir()
    forum = tmp_path / "forum"; forum.mkdir()
    arts = tmp_path / "articles"; arts.mkdir()
    monkeypatch.setattr(sl, "BASE_DIR", tmp_path)
    monkeypatch.setattr(sl, "FORUM_DIR", forum)
    monkeypatch.setattr(sl, "KNOWLEDGE_DIR", know)
    monkeypatch.setattr(sl, "SLATES_DIR", know / "slates")
    monkeypatch.setattr(sl, "TASTE_LOG", know / "taste_log.jsonl")
    monkeypatch.setattr(sl, "GATE_CANDIDATES", know / "gate_candidates.jsonl")
    monkeypatch.setattr(sl, "TOPIC_GATE_FILE", tmp_path / "topic_gate.md")
    monkeypatch.setattr(sl, "DATA_SOURCES_FILE", tmp_path / "DATA_SOURCES.md")
    (tmp_path / "DATA_SOURCES.md").write_text("members_{17-22}.parquet: member attributes.\n", encoding="utf-8")
    (tmp_path / "topic_gate.md").write_text(
        "# Topic Gate\n\n## Template\n\n```\n## <name>\nseed: <seed>\n```\n\n---\n\n"
        "## R28 - Arc 5 opening\n\nseed: old seed\n\nsigned: 2026-08-24\n", encoding="utf-8")
    monkeypatch.setattr(td, "FORUM_DIR", forum)
    monkeypatch.setattr(td, "ARTICLES_DIR", arts)
    monkeypatch.setattr(td, "ACTIVE_ARC_FILE", know / "active_arc.json")
    monkeypatch.setattr(td, "LOG_FILE", know / "topic_diversity.jsonl")
    monkeypatch.setattr(td, "EMBED_CACHE_DIR", None)
    monkeypatch.setattr(td, "embed", _bow_embed)
    monkeypatch.setattr(td, "_config", lambda: {"topic_similarity_warn": 0.9, "topic_similarity_block": 0.97,
                                                "diversity_model": "stub-model"})
    monkeypatch.setattr(sl, "_next_round", lambda: 31)
    monkeypatch.setattr(sl, "opener_counts", lambda: {"puzzle_contradiction": 4, "evidence_gap": 1})
    return tmp_path


def _fake_cli(monkeypatch, topics=("seniority", "gender quota", "committee transfer"), fail_at=None,
              events_for=None):
    def result(i, task, prompt, kw):
        if fail_at == i:
            return FakeResult(ok=False, failure="usage_limit", run_id=f"run_{i}")
        return FakeResult(structured=_candidate(topics[i - 1]), run_id=f"run_{i}",
                          events_paths=events_for(i) if events_for else [])
    fake = FakeCLI(result)
    monkeypatch.setitem(sys.modules, "claude_cli", fake.module())
    return fake


# --------------------------------------------------------------------------
# Seeds
# --------------------------------------------------------------------------

def test_seed_patterns_are_distinct_non_bridge_and_weighted():
    import random
    for s in range(20):
        pats, w = sl.seed_patterns(3, random.Random(s), {"puzzle_contradiction": 4})
        assert len(set(pats)) == 3
        assert "bridge_opportunity" not in pats and "constructed_contradiction" not in pats
    assert w["puzzle_contradiction"] == pytest.approx(0.2) and w["evidence_gap"] == 1.0
    # Under-used patterns are drawn more often than the dominant one.
    first = [sl.seed_patterns(1, random.Random(s), {"puzzle_contradiction": 4})[0][0] for s in range(600)]
    assert first.count("puzzle_contradiction") < first.count("evidence_gap")


# --------------------------------------------------------------------------
# propose
# --------------------------------------------------------------------------

def test_propose_runs_at_most_three_isolated_calls(paths, monkeypatch):
    fake = _fake_cli(monkeypatch)
    slate = sl.propose(k=5, seed=8374)
    assert len(fake.calls) == 3
    for c in fake.calls:
        assert c["task"] == "slate"
        assert c["tools"] == ["WebFetch", "WebSearch"]
        cwd = Path(c["cwd"]).resolve()
        assert c["cwd_existed"] and ROOT.resolve() not in cwd.parents and cwd != ROOT.resolve()
        assert not Path(c["cwd"]).exists()          # temporary directory removed afterwards
        assert c["schema"] is sl.CANDIDATE_SCHEMA
        for bad in ("forum/", "knowledge/", "Critic", "verdict", "entropy"):
            assert bad not in c["prompt_text"], bad
    assert len({c["prompt_text"] for c in fake.calls}) == 3   # one seed pattern per call
    assert sorted(slate["display_order"]) == ["C1", "C2", "C3"]
    rows = [json.loads(l) for l in sl.GATE_CANDIDATES.read_text().splitlines()]
    assert len(rows) == 3 and all(r["drafted_by"] == "claude" and r["source"] == "arc_slate" for r in rows)
    assert all(r["text"] for r in rows)


def test_slate_file_has_no_ranking_and_no_arc_commitments(paths, monkeypatch):
    _fake_cli(monkeypatch)
    slate = sl.propose(seed=8374)
    md = (sl.SLATES_DIR / f"{slate['slate_id']}.md").read_text(encoding="utf-8")
    low = md.lower()
    for bad in ("recommend", "prior", "falsifier", "decision_rule", "decision rule", "null_paper", "rank"):
        assert bad not in low, bad
    assert "random order" in low
    for cid in ("C1", "C2", "C3"):
        assert f"## {cid}" in md
    assert "c_constructed" in md           # the inferred rival is disclosed


def test_failed_call_and_trace_violation_are_not_listed(paths, monkeypatch):
    def events_for(i):
        if i != 2:
            return []
        p = paths / f"events_{i}.jsonl"
        p.write_text(json.dumps({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Read", "input": {"file_path": "/x/forum/090_critic.md"}}]}}) + "\n")
        return [p]
    _fake_cli(monkeypatch, fail_at=3, events_for=events_for)
    slate = sl.propose(seed=1)
    st = {c["candidate_id"]: c for c in slate["candidates"]}
    assert st["C1"]["status"] == "candidate"
    assert st["C2"]["status"] == "removed" and st["C2"]["trace_violations"]
    assert st["C3"]["status"] == "failed"
    assert slate["display_order"] == ["C1"]


def test_trace_check_flags_repo_and_denied_folders(tmp_path):
    ev = tmp_path / "e.jsonl"
    ev.write_text("\n".join(json.dumps({"type": "assistant", "message": {"content": [b]}}) for b in [
        {"type": "tool_use", "name": "WebSearch", "input": {"query": "legislative seniority Korea"}},
        {"type": "tool_use", "name": "Grep", "input": {"pattern": "x", "path": "knowledge/"}},
        {"type": "tool_use", "name": "WebFetch", "input": {"url": f"file://{tmp_path}/summaries/r1.md"}},
    ]) + "\n")
    v = sl.trace_violations([ev], repo_root=tmp_path)
    assert [x["tool"] for x in v] == ["Grep", "WebFetch"]
    assert "denied folder" in v[0]["reasons"] and "repository path" in v[1]["reasons"]
    assert sl.trace_violations([ev.with_name("missing.jsonl")], repo_root=tmp_path) == []


def test_within_slate_duplicates_are_removed(paths, monkeypatch):
    _fake_cli(monkeypatch, topics=("seniority", "seniority", "gender quota"))
    slate = sl.propose(seed=3)
    st = {c["candidate_id"]: c["status"] for c in slate["candidates"]}
    assert sorted(st.values()) == ["candidate", "candidate", "removed"]
    assert slate["dedupe"]["max_pairwise_cosine"] is not None
    assert slate["dedupe"]["max_pairwise_cosine"] < slate["dedupe"]["warn"]


def test_dry_run_makes_no_call_and_writes_nothing(paths, monkeypatch):
    fake = _fake_cli(monkeypatch)
    sl.propose(dry_run=True)
    assert fake.calls == [] and not sl.SLATES_DIR.exists() and not sl.GATE_CANDIDATES.exists()


# --------------------------------------------------------------------------
# Taste log and gate stub
# --------------------------------------------------------------------------

def _slate(monkeypatch):
    _fake_cli(monkeypatch)
    return sl.propose(seed=8374)


FIELDS = {"identification": "within-member panel", "exclusion_criteria": "no ideology",
          "prior": "seniors pass more", "falsifier": "no seniority gradient",
          "decision_rule": "pursue if gradient >= 3 points", "null_paper": "a precise null on seniority"}


def test_stub_refused_until_every_listed_candidate_has_a_decision(paths, monkeypatch):
    slate = _slate(monkeypatch)
    sid = slate["slate_id"]
    before = sl.TOPIC_GATE_FILE.read_text()
    sl.record(sid, "C1", "accept", "sharp quantity and the data exist")
    with pytest.raises(SystemExit, match="taste log incomplete"):
        sl.stub(sid, "C1", 31)
    assert sl.TOPIC_GATE_FILE.read_text() == before
    sl.record(sid, "C2", "reject", "restates a Season 1 question")
    sl.record(sid, "C3", "modify", "narrow to the 20th-22nd Assemblies")
    with pytest.raises(SystemExit, match="not accepted"):
        sl.stub(sid, "C2", 31)
    entry = sl.stub(sid, "C1", 31)
    assert "drafted_by: claude (arc_slate candidate C1" in entry
    assert "signed_by" not in entry and not re.search(r"^signed:", entry, re.MULTILINE)
    text = sl.TOPIC_GATE_FILE.read_text()
    assert text.index("## R31") < text.index("## R28")          # newest first
    assert text.index("## R31") > text.index("## Template")


def test_record_rejects_bad_input(paths, monkeypatch):
    slate = _slate(monkeypatch)
    sid = slate["slate_id"]
    with pytest.raises(SystemExit):
        sl.record(sid, "C9", "accept", "x")
    with pytest.raises(SystemExit):
        sl.record(sid, "C1", "maybe", "x")
    with pytest.raises(SystemExit):
        sl.record(sid, "C1", "accept", "   ")
    with pytest.raises(SystemExit):
        sl.record(sid, "C1", "accept", "two\nlines")
    assert not sl.TASTE_LOG.exists()


def test_auto_sign_writes_truthful_delegated_provenance(paths, monkeypatch):
    slate = _slate(monkeypatch)
    sid = slate["slate_id"]
    by = "orchestrating Claude session"
    for cid in ("C1", "C2", "C3"):
        sl.record(sid, cid, "accept" if cid == "C1" else "reject", "one line reason", by=by)
    with pytest.raises(SystemExit, match="needs every gate field"):
        sl.stub(sid, "C1", 31, auto_sign=True, fields={"prior": "x"})
    entry = sl.stub(sid, "C1", 31, auto_sign=True, fields=FIELDS, session_model="claude-opus-5-5")
    assert "drafted_by: orchestrating Claude session (claude-opus-5-5), from arc_slate candidate C1" in entry
    assert ("signed_by: orchestrating Claude session, signed under the researcher's standing delegation "
            "of 2026-09-25") in entry
    assert re.search(r"^signed: \d{4}-\d{2}-\d{2}$", entry, re.MULTILINE)
    assert "signed_by: researcher" not in entry and "set by the researcher" not in entry
    for f, v in FIELDS.items():
        assert f"{f}: {v}" in entry
    # The signed entry is found by seed, and the slate records the stub for the annotator.
    seed = re.search(r"^seed: (.+)$", entry, re.MULTILINE).group(1)
    assert sl.slate_for_seed(seed)["slate_id"] == sid
    taste = [json.loads(l) for l in sl.TASTE_LOG.read_text().splitlines()]
    assert {t["decided_by"] for t in taste} == {by}


def test_auto_sign_needs_stage2_fields_only_while_binding_checks_is_on(paths, monkeypatch):
    """V-03: Stage 1 prompts never show decision_rule or null_paper, so an
    auto-signed entry needs them only while stage2.binding_checks is on, and
    a signed entry never carries a placeholder for a field left out."""
    slate = _slate(monkeypatch)
    sid = slate["slate_id"]
    for cid in ("C1", "C2", "C3"):
        sl.record(sid, cid, "accept" if cid == "C1" else "reject", "one line reason")
    stage1 = {k: FIELDS[k] for k in sl.STAGE1_GATE_FIELDS}
    before = sl.TOPIC_GATE_FILE.read_text()
    monkeypatch.setattr(sl, "_binding_checks_on", lambda: True)
    with pytest.raises(SystemExit, match="Missing decision_rule, null_paper"):
        sl.stub(sid, "C1", 31, auto_sign=True, fields=stage1, session_model="claude-opus-5-5")
    assert sl.TOPIC_GATE_FILE.read_text() == before
    monkeypatch.setattr(sl, "_binding_checks_on", lambda: False)
    entry = sl.stub(sid, "C1", 31, auto_sign=True, fields=stage1, session_model="claude-opus-5-5")
    assert sl.PLACEHOLDER not in entry
    assert not re.search(r"^(decision_rule|null_paper):", entry, re.MULTILINE)
    for f, v in stage1.items():
        assert f"{f}: {v}" in entry
    assert re.search(r"^signed: \d{4}-\d{2}-\d{2}$", entry, re.MULTILINE)


def test_unsigned_stub_does_not_satisfy_a_signed_line_check(paths, monkeypatch):
    """run_forum's gate check needs a 'signed:' line; an unsigned stub has none."""
    slate = _slate(monkeypatch)
    sid = slate["slate_id"]
    for cid in ("C1", "C2", "C3"):
        sl.record(sid, cid, "accept", "fine")
    entry = sl.stub(sid, "C2", 31)
    assert "signed:" not in entry.lower()



def test_record_defaults_to_the_orchestrating_session_never_the_researcher(paths, monkeypatch):
    """FID-F3 / E2E-09 (D-10): the automatic flow is propose, record, then
    stub --auto-sign. A decision recorded without --by is the orchestrating
    session's, so the public taste log never credits the researcher with it."""
    slate = _slate(monkeypatch)
    sid = slate["slate_id"]
    row = sl.record(sid, "C1", "accept", "fits the frame")
    assert row["decided_by"] == sl.AUTO_DECIDED_BY
    assert row["decided_by"].startswith("orchestrating Claude session")
    assert not row["decided_by"].lower().startswith("researcher")
    # The CLI default is the same, and --by researcher is still recorded as given.
    monkeypatch.setattr(sys, "argv", ["arc_slate.py", "record", sid, "C2", "reject", "restates R7"])
    sl.main()
    monkeypatch.setattr(sys, "argv", ["arc_slate.py", "record", sid, "C3", "reject", "too broad",
                                      "--by", "researcher"])
    sl.main()
    taste = {t["candidate_id"]: t["decided_by"] for t in
             (json.loads(l) for l in sl.TASTE_LOG.read_text().splitlines())}
    assert taste == {"C1": sl.AUTO_DECIDED_BY, "C2": sl.AUTO_DECIDED_BY, "C3": "researcher"}
    with pytest.raises(SystemExit, match="--by"):
        sl.record(sid, "C1", "accept", "x", by="  ")
    with pytest.raises(SystemExit, match="placeholder"):
        sl.record(sid, "C1", "accept", "x", by="<who decided>")


def test_auto_sign_refuses_a_candidate_the_researcher_decided(paths, monkeypatch):
    """A researcher decision paired with a delegation signature would misstate
    who chose the arc. Only the unsigned stub (for the researcher to sign)
    is written for it."""
    slate = _slate(monkeypatch)
    sid = slate["slate_id"]
    sl.record(sid, "C1", "accept", "sharp quantity", by="researcher")
    sl.record(sid, "C2", "reject", "restates R7")
    sl.record(sid, "C3", "reject", "too broad")
    before = sl.TOPIC_GATE_FILE.read_text()
    with pytest.raises(SystemExit, match="decided by the researcher"):
        sl.stub(sid, "C1", 31, auto_sign=True, fields=FIELDS, session_model="claude-opus-5-5")
    assert sl.TOPIC_GATE_FILE.read_text() == before
    entry = sl.stub(sid, "C1", 31)
    assert "signed_by" not in entry


def test_slate_instructions_print_the_decider_flag(paths, monkeypatch):
    slate = _slate(monkeypatch)
    md = (sl.SLATES_DIR / f"{slate['slate_id']}.md").read_text()
    lines = [l for l in md.splitlines() if l.startswith("python3 arc_slate.py record")]
    assert lines and all('--by "<who decided>"' in l for l in lines)
    assert "Pass --by researcher only for a decision the researcher made." in md

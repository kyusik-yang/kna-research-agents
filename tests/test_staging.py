"""staging (M13): a failed run leaves the ledgers byte-identical and its
changes quarantined, an accepted run keeps only what its role may write,
staged retreats merge with run_id and resolvable evidence, dictionaries are
append-never-rewrite, researcher-owned files are never reverted."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import claude_cli  # noqa: E402
import staging  # noqa: E402
import write_guard  # noqa: E402

STUB = ROOT / "tests" / "fixtures" / "cli" / "stub_claude.py"
ANALYST_WRITES = ["knowledge/hand_coding/round_*.jsonl"]
KNOWN_DOIS = {"10.1017/s0003055424000123"}
CRITIC_WRITES: list[str] = []


@pytest.fixture
def repo(tmp_path, monkeypatch):
    base = tmp_path / "repo"
    (base / "workspace").mkdir(parents=True)
    forum = base / "forum"
    forum.mkdir()
    for n, role in ((1, "literature_scout"), (2, "data_analyst"), (3, "critic")):
        (forum / f"{n:03d}_{role}.md").write_text("---\nauthor: x\n---\n\n# Post\n\nline 6\nline 7\n")
    k = base / "knowledge"
    (k / "hand_coding").mkdir(parents=True)
    (k / "archive").mkdir()
    (k / "retreats.jsonl").write_text(json.dumps({"finding": "old", "originating_round": 3}) + "\n")
    (k / "findings.jsonl").write_text(json.dumps({"finding": "f1", "round": 1}) + "\n")
    (k / "hand_coding" / "round_25.jsonl").write_text('{"member_id": "A", "category": "cabinet"}\n')
    (k / "human_context.md").write_text("[2026-09-25 09:00] earlier comment\n")
    (k / "archive" / "old.jsonl").write_text("{}\n")
    (base / "agents.json").write_text(json.dumps({
        "season": 2,
        "forum_config": {"model": "claude-opus-5-5", "effort_by_task": {"summary": "low"},
                         "max_turns": {}, "watched_repos": []},
        "agents": [{"id": "data_analyst", "name": "A", "prompt": "a", "effort": "high",
                    "allowed_tools": ["Bash", "Read", "Write"]},
                   {"id": "critic", "name": "C", "prompt": "c", "effort": "high",
                    "allowed_tools": ["Bash", "Read", "Write"]}],
    }))
    data = tmp_path / "kbl_data"
    data.mkdir()
    for mod in (staging, claude_cli, write_guard):
        monkeypatch.setattr(mod, "BASE_DIR", base)
    # No network: a DOI resolves only when it is in KNOWN_DOIS.
    import prechecks
    monkeypatch.setattr(prechecks, "resolve_doi",
                        lambda doi, cache, **kw: {"found": doi.lower() in KNOWN_DOIS})
    monkeypatch.setenv("KBL_DATA", str(data))
    monkeypatch.setenv("KNA_CLAUDE_BIN", str(STUB))
    monkeypatch.setenv("STUB_CLAUDE_STATE", str(tmp_path / "stub_state"))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude_config"))
    monkeypatch.setenv("KNA_NO_SLEEP", "1")
    monkeypatch.delenv("STUB_CLAUDE_PLAN", raising=False)

    def plan(steps):
        p = tmp_path / "plan.json"
        p.write_text(json.dumps(steps))
        monkeypatch.setenv("STUB_CLAUDE_PLAN", str(p))

    return type("R", (), {"base": base, "k": k, "forum": forum, "data": data, "plan": staticmethod(plan)})


def _run_agent(repo, run, role, post):
    return claude_cli.run_claude("agent", "prompt", role=role, expect_file=post, round_num=31,
                                 extra_env=staging.env(run))


def test_begin_snapshots_and_env(repo):
    run = staging.begin("r31_critic_a", "critic")
    assert (run.snapshot_dir / "knowledge" / "retreats.jsonl").exists()
    assert (run.snapshot_dir / "forum" / "003_critic.md").exists()
    assert not (run.snapshot_dir / "knowledge" / "archive").exists()
    assert not any(k.startswith("knowledge/staging/") for k in run.manifest)
    assert staging.env(run) == {"KNA_RUN_ID": "r31_critic_a", "KNA_STAGING_DIR": str(run.staging_dir)}
    with pytest.raises(FileExistsError):
        staging.begin("r31_critic_a", "critic")


def test_failed_run_leaves_ledger_identical_and_quarantines(repo):
    """Plan test 1: an agent appends to retreats.jsonl and exits without a post."""
    ledger = repo.k / "retreats.jsonl"
    before = ledger.read_bytes()
    run = staging.begin("r31_critic_fail", "critic")
    post = repo.forum / "091_critic.md"
    repo.plan([{"append": [[str(ledger), json.dumps({"finding": "phantom retreat"})]],
                "write": [[str(repo.forum / "091_critic.partial"), "half a post"]]}])
    res = _run_agent(repo, run, "critic", post)
    assert res.failure == "no_post"
    quarantine = staging.rollback(run, reason=res.failure)
    assert ledger.read_bytes() == before
    assert quarantine == repo.k / "staging" / "failed_r31_critic_fail"
    assert "phantom retreat" in (quarantine / "tree" / "knowledge" / "retreats.jsonl").read_text()
    assert (quarantine / "tree" / "forum" / "091_critic.partial").read_text() == "half a post"
    assert not (repo.forum / "091_critic.partial").exists()
    report = json.loads((quarantine / "ROLLBACK.json").read_text())
    assert report["reason"] == "no_post"
    assert {c["path"] for c in report["changes"]} == {"knowledge/retreats.jsonl", "forum/091_critic.partial"}
    side = json.loads(res.sidecar_path.read_text())
    assert side["containment"]["rolled_back"] is True
    assert not run.snapshot_dir.exists()


def test_rollback_quarantines_partial_post(repo):
    run = staging.begin("r31_analyst_partial", "data_analyst")
    post = repo.forum / "092_data_analyst.md"
    post.write_text("---\nauthor: Analyst\n---\n\n# Half")
    q = staging.rollback(run, reason="timeout")
    assert not post.exists()
    assert (q / "tree" / "forum" / "092_data_analyst.md").read_text().endswith("# Half")


def test_happy_path_merges_staged_retreat_with_run_id(repo):
    """Plan test 4 and test 2 (a precheck id and a post line reference resolve)."""
    pre = repo.k / "prechecks"
    pre.mkdir()
    (pre / "R31.json").write_text(json.dumps({"round": 31, "posts": {"090_data_analyst.md": {
        "rules": [{"id": "R-05", "status": "FLAG"}]}}}))
    run = staging.begin("r31_critic_ok", "critic")
    post = repo.forum / "091_critic.md"
    staged = run.staging_dir / "retreats.jsonl"
    rows = [
        {"finding": "R28 prior", "reason": "overturned", "new_evidence": "precheck:R-05"},
        {"finding": "R26 gap", "reason": "levels", "new_evidence": "091:6"},
        {"finding": "R26 gap", "reason": "duplicate", "new_evidence": "091:6"},
        {"finding": "vague", "reason": "no evidence", "new_evidence": "I re-read the tables"},
        {"finding": "doi based", "reason": "lit", "new_evidence": "10.1017/S0003055424000123"},
    ]
    repo.plan([{"write": [[str(post), "---\nauthor: Critic\n---\n\n# Review\n\nline 6\n"]],
                "append": [[str(staged), json.dumps(r)] for r in rows]}])
    res = _run_agent(repo, run, "critic", post)
    assert res.ok
    report = staging.commit(run, post, CRITIC_WRITES)
    assert report["retreats_merged"] == 3
    assert [r["finding"] for r in report["retreats_rejected"]] == ["vague"]
    ledger = [json.loads(l) for l in (repo.k / "retreats.jsonl").read_text().splitlines()]
    assert ledger[0] == {"finding": "old", "originating_round": 3}
    assert [r["finding"] for r in ledger[1:]] == ["R28 prior", "R26 gap", "doi based"]
    assert all(r["run_id"] == "r31_critic_ok" for r in ledger[1:])
    assert report["violations"] == []
    # a second commit hook for the same run adds nothing
    run2 = staging.StagingRun(run_id=run.run_id, role="critic", staging_dir=run.staging_dir,
                              snapshot_dir=run.snapshot_dir, manifest=staging._tracked_files())
    assert staging._merge_retreats(run2, post)[0] == 0


def test_evidence_resolution(repo):
    run = staging.begin("r31_x", "critic")
    out = repo.base / "workspace" / "r31" / "survival.csv"
    out.parent.mkdir(parents=True)
    out.write_text("a,b\n")
    assert staging.evidence_resolves("workspace/r31/survival.csv", run)
    assert staging.evidence_resolves("workspace/r31/survival.csv:2", run)
    assert staging.evidence_resolves(str(out), run)
    assert staging.evidence_resolves("003_critic.md:7", run)
    assert not staging.evidence_resolves("003:99", run)
    assert not staging.evidence_resolves("workspace/r31/missing.csv", run)
    assert not staging.evidence_resolves("", run) and not staging.evidence_resolves(None, run)
    assert staging.evidence_resolves(["nothing here", "003_critic.md:7"], run)


def test_evidence_that_names_nothing_checkable_is_rejected(repo):
    """E2E-10 / F10: directories, paths outside the repository, bare PC
    tokens, precheck ids with no precheck result (Stage 1) and DOIs that
    Crossref and OpenAlex do not know never resolve."""
    run = staging.begin("r31_critic_ev", "critic")
    for ev in (".", "/", "/tmp", "forum", "workspace", "knowledge", "PCA", "PCR", "PC-12", "PCzzz",
               "precheck:anything-at-all", "precheck:R-99", "10.9999/does-not-exist",
               str(repo.base.parent / "outside.txt"), "workspace/../../outside.txt"):
        assert not staging.evidence_resolves(ev, run), ev
    (repo.base.parent / "outside.txt").write_text("x")
    assert not staging.evidence_resolves(str(repo.base.parent / "outside.txt"), run)
    assert staging.evidence_resolves("doi:10.1017/S0003055424000123", run)
    pre = repo.k / "prechecks"
    pre.mkdir()
    (pre / "R30.json").write_text(json.dumps({"posts": {"x": {"rules": [{"id": "R-02"}]}}}))
    assert not staging.evidence_resolves("precheck:R-02", run)      # another round's result
    (pre / "R31.json").write_text(json.dumps({"posts": {"x": {"rules": [{"id": "R-02"}]}}}))
    assert staging.evidence_resolves("precheck:R-02", run)


def test_rewrite_of_existing_dictionary_is_reverted(repo):
    """Plan test 3: an R27-style Analyst rewrites round_25.jsonl."""
    dict_path = repo.k / "hand_coding" / "round_25.jsonl"
    original = dict_path.read_bytes()
    run = staging.begin("r27_data_analyst_rerun", "data_analyst")
    post = repo.forum / "092_data_analyst.md"
    repo.plan([{"write": [[str(post), "post"],
                          [str(dict_path), '{"member_id": "A", "category": "court_ruling"}\n']]}])
    res = _run_agent(repo, run, "data_analyst", post)
    assert res.ok
    report = staging.commit(run, post, ANALYST_WRITES)
    assert dict_path.read_bytes() == original
    rev = repo.k / "hand_coding" / "round_25.rev1.jsonl"
    assert "court_ruling" in rev.read_text()
    assert report["violations"][0]["change"] == "rewrite_existing_dictionary"
    side = json.loads(res.sidecar_path.read_text())
    assert side["containment"]["violations"][0]["path"] == "knowledge/hand_coding/round_25.jsonl"
    hashes = json.loads((repo.k / "hand_coding" / "HASHES.json").read_text())
    assert "round_25.rev1.jsonl" in hashes and "round_25.jsonl" not in hashes


def test_new_dictionary_allowed_and_hashed(repo):
    run = staging.begin("r31_data_analyst_new", "data_analyst")
    post = repo.forum / "092_data_analyst.md"
    post.write_text("post")
    (repo.k / "hand_coding" / "round_31.jsonl").write_text('{"member_id": "B"}\n')
    (run.staging_dir / "hand_coding" / "round_31b.jsonl").write_text('{"member_id": "C"}\n')
    (run.staging_dir / "hand_coding" / "round_25.jsonl").write_text('{"member_id": "Z"}\n')
    report = staging.commit(run, post, ANALYST_WRITES)
    assert (repo.k / "hand_coding" / "round_31.jsonl").exists()
    assert (repo.k / "hand_coding" / "round_31b.jsonl").read_text() == '{"member_id": "C"}\n'
    assert "Z" in (repo.k / "hand_coding" / "round_25.rev1.jsonl").read_text()
    assert "A" in (repo.k / "hand_coding" / "round_25.jsonl").read_text()
    hashes = json.loads((repo.k / "hand_coding" / "HASHES.json").read_text())
    assert {"round_31.jsonl", "round_31b.jsonl", "round_25.rev1.jsonl"} <= set(hashes)
    assert sorted(report["dictionaries"]) == sorted([
        "knowledge/hand_coding/round_31.jsonl", "knowledge/hand_coding/round_31b.jsonl",
        "knowledge/hand_coding/round_25.rev1.jsonl"])


def test_dictionary_not_allowed_for_critic(repo):
    run = staging.begin("r31_critic_dict", "critic")
    post = repo.forum / "093_critic.md"
    post.write_text("post")
    (repo.k / "hand_coding" / "round_31.jsonl").write_text("{}\n")
    (run.staging_dir / "hand_coding" / "round_32.jsonl").write_text("{}\n")
    report = staging.commit(run, post, CRITIC_WRITES)
    assert not (repo.k / "hand_coding" / "round_31.jsonl").exists()
    assert (run.staging_dir / "reverted" / "knowledge" / "hand_coding" / "round_31.jsonl").exists()
    assert not (repo.k / "hand_coding" / "round_32.jsonl").exists()
    assert (run.staging_dir / "hand_coding" / "round_32.jsonl").exists()
    assert {v["change"] for v in report["violations"]} == {"added", "staged_dictionary"}


def test_out_of_allowlist_changes_are_reverted_not_deleted(repo):
    run = staging.begin("r31_critic_wild", "critic")
    post = repo.forum / "093_critic.md"
    post.write_text("post")
    (repo.k / "findings.jsonl").write_text('{"finding": "rewritten by agent"}\n')
    (repo.k / "arc_status.json").write_text('{"state": "running"}')
    (repo.forum / "001_literature_scout.md").unlink()
    report = staging.commit(run, post, CRITIC_WRITES)
    assert "f1" in (repo.k / "findings.jsonl").read_text()
    assert not (repo.k / "arc_status.json").exists()
    assert (repo.forum / "001_literature_scout.md").exists()
    rev = run.staging_dir / "reverted" / "knowledge"
    assert "rewritten by agent" in (rev / "findings.jsonl").read_text()
    assert (rev / "arc_status.json").exists()
    assert {(v["path"], v["change"]) for v in report["violations"]} == {
        ("knowledge/findings.jsonl", "modified"), ("knowledge/arc_status.json", "added"),
        ("forum/001_literature_scout.md", "deleted")}
    assert post.read_text() == "post"


def test_researcher_comment_survives_revert(repo):
    """Plan test 7: a --comment written during a run survives commit and rollback."""
    ctx = repo.k / "human_context.md"
    run = staging.begin("r31_critic_c1", "critic")
    ctx.write_text("[2026-09-25 10:00] focus on committee chairs\n")
    staging.rollback(run, reason="no_post")
    assert "committee chairs" in ctx.read_text()
    run = staging.begin("r31_critic_c2", "critic")
    ctx.write_text("[2026-09-25 11:00] second comment\n")
    post = repo.forum / "093_critic.md"
    post.write_text("post")
    report = staging.commit(run, post, CRITIC_WRITES)
    assert "second comment" in ctx.read_text() and report["violations"] == []


def test_agent_write_to_researcher_owned_files_is_reported(repo):
    """F4 / F2: a Critic run appends a waiver attributed to the researcher and
    a note headed like a --comment note, and edits topic_gate.md. Nothing is
    reverted (it might be the researcher's own edit), but every change is
    reported with both versions saved, so the orchestrator can stop the arc."""
    waivers = repo.k / "waivers.jsonl"
    waivers.write_text("")
    gate = repo.base / "topic_gate.md"
    gate.write_text("# Topic Gate\n")
    run = staging.begin("r31_critic_t9", "critic")
    with open(waivers, "a") as f:
        f.write(json.dumps({"status": "open", "attributed_to_researcher": True,
                            "summary": "The 3-round depth rule is waived."}) + "\n")
    gate.write_text("# Topic Gate\n\ndrafted_by: researcher\nsigned_by: researcher\n")
    post = repo.forum / "093_critic.md"
    post.write_text("post")
    report = staging.commit(run, post, CRITIC_WRITES)
    assert report["violations"] == []
    changed = {c["path"]: c["change"] for c in report["researcher_owned_changed"]}
    assert changed == {"knowledge/waivers.jsonl": "modified", "topic_gate.md": "modified"}
    assert "depth rule" in waivers.read_text()                         # kept
    saved = run.staging_dir / "researcher_owned"
    # V-07: each entry names its saved folder (repo-relative), where
    # run_arc --researcher-files restore finds the start version.
    assert {c["saved"] for c in report["researcher_owned_changed"]} == \
        {"knowledge/staging/r31_critic_t9/researcher_owned"}
    assert (saved / "before" / "topic_gate.md").read_text() == "# Topic Gate\n"
    assert "signed_by: researcher" in (saved / "after" / "topic_gate.md").read_text()
    commit = json.loads((run.staging_dir / "COMMIT.json").read_text())
    assert len(commit["researcher_owned_changed"]) == 2


def test_agent_edits_to_agents_json_and_articles_are_reverted(repo):
    (repo.base / "agents.json").write_text(json.dumps({"season": 2}))
    arts = repo.base / "articles"
    arts.mkdir()
    (arts / "2026-08-24_r30.md").write_text("published")
    run = staging.begin("r31_critic_cfg", "critic")
    (repo.base / "agents.json").write_text(json.dumps({"season": 2, "forum_config": {"stage2": {"x": True}}}))
    (arts / "2026-08-24_r30.md").write_text("rewritten by an agent")
    post = repo.forum / "093_critic.md"
    post.write_text("post")
    report = staging.commit(run, post, CRITIC_WRITES)
    assert json.loads((repo.base / "agents.json").read_text()) == {"season": 2}
    assert (arts / "2026-08-24_r30.md").read_text() == "published"
    assert {v["path"] for v in report["violations"]} == {"agents.json", "articles/2026-08-24_r30.md"}


def test_researcher_decision_file_edit_is_kept_and_reported(repo):
    """F5: a researcher confirms a party_blocs.csv row during a Scout run.
    The edit stays in the tree and is reported, not logged as a reverted
    agent violation."""
    blocs = repo.k / "party_blocs.csv"
    blocs.write_text("label,bloc,status\nX,ruling,needs_confirmation\n")
    run = staging.begin("r31_literature_scout_t1", "literature_scout")
    blocs.write_text("label,bloc,status\nX,ruling,confirmed\n")
    post = repo.forum / "091_literature_scout.md"
    post.write_text("post")
    report = staging.commit(run, post, ["{post}"])
    assert "confirmed" in blocs.read_text() and "needs_confirmation" not in blocs.read_text()
    assert report["violations"] == []
    assert report["researcher_owned_changed"][0]["path"] == "knowledge/party_blocs.csv"


def test_recover_rolls_back_a_run_that_died(repo):
    """F12: a run whose process was killed left its snapshot. recover()
    quarantines its partial work and restores the snapshot, like rollback."""
    ledger = repo.k / "retreats.jsonl"
    before = ledger.read_bytes()
    run = staging.begin("r31_data_analyst_dead", "data_analyst")
    with open(ledger, "a") as f:
        f.write('{"finding": "half-written"}\n')
    (repo.forum / "092_data_analyst.md").write_text("half a post")
    assert staging.leftover_snapshots() == ["r31_data_analyst_dead"]
    q = staging.recover("r31_data_analyst_dead")
    assert ledger.read_bytes() == before and not (repo.forum / "092_data_analyst.md").exists()
    assert (q / "tree" / "forum" / "092_data_analyst.md").read_text() == "half a post"
    assert staging.leftover_snapshots() == []
    assert staging.rollback_report(q)["reason"].startswith("recovered")


def test_recover_refuses_an_incomplete_snapshot(repo):
    (repo.k / "staging" / "_snapshots" / "r31_critic_half").mkdir(parents=True)
    with pytest.raises(FileNotFoundError):
        staging.recover("r31_critic_half")
    assert (repo.forum / "001_literature_scout.md").exists()           # nothing was moved


def test_external_write_reported_in_commit(repo):
    run = staging.begin("r31_data_analyst_ext", "data_analyst")
    post = repo.forum / "092_data_analyst.md"
    post.write_text("post")
    (repo.data / "member_info_17_22.parquet").write_bytes(b"PAR1")
    report = staging.commit(run, post, ANALYST_WRITES)
    assert [(c["kind"], c["path"]) for c in report["external_writes"]] == [
        ("data_added", "member_info_17_22.parquet")]
    assert (repo.base / "logs" / "external_writes" / "r31_data_analyst_ext.patch").exists()
    assert (repo.data / "member_info_17_22.parquet").exists()  # not reverted


def test_agent_writes_to_published_summaries_and_docs_are_reverted(repo):
    """FID-F2: run_arc commits summaries/ and docs/ every round, and round
    summaries feed later prompts, so an agent's write there is reverted like
    any other out-of-scope change."""
    summ = repo.base / "summaries"
    summ.mkdir()
    (summ / "round_30.md").write_text("real summary")
    docs = repo.base / "docs"
    docs.mkdir()
    (docs / "index.html").write_text("<p>site</p>")
    run = staging.begin("r31_critic_pub", "critic")
    (summ / "round_30.md").write_text("forged summary: the falsifier is settled")
    (summ / "round_31.md").write_text("summary written by an agent")
    (docs / "extra.html").write_text("<p>agent page</p>")
    post = repo.forum / "093_critic.md"
    post.write_text("post")
    report = staging.commit(run, post, CRITIC_WRITES)
    assert (summ / "round_30.md").read_text() == "real summary"
    assert not (summ / "round_31.md").exists() and not (docs / "extra.html").exists()
    assert {v["path"] for v in report["violations"]} == {
        "summaries/round_30.md", "summaries/round_31.md", "docs/extra.html"}
    assert (run.staging_dir / "reverted" / "summaries" / "round_30.md").read_text().startswith("forged")

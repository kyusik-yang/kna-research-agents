"""auto_arc.py, the one-command pipeline (start, resume, status).

Part 1 runs auto_arc in-process with every path in tmp_path and the slate,
gate draft, premise check and run_arc replaced by scripted fakes.

Part 2 runs the real chain end to end on a scratch copy of the repository in
tmp_path: auto_arc start, the stub claude binary (tests/fixtures/cli/
stub_claude.py, through a thin wrapper that writes the premise-check result
file the call is told to write), three slate calls, gate drafts, a failed and
then a passed premise check, the signed gate entry, run_arc with --no-push,
three forum rounds through run_forum, and a drafted paper. The scratch copy
replaces only the embedding model (topic_diversity), the paper drafter
(draft_article) and the site builder with light stand-ins, and it is its own
git repository, so no git command reaches the real repository."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import arc_slate  # noqa: E402
import auto_arc  # noqa: E402
import claude_cli  # noqa: E402
import forum_index  # noqa: E402
import run_forum  # noqa: E402

STUB = ROOT / "tests" / "fixtures" / "cli" / "stub_claude.py"
MODEL = "claude-opus-5-5"


def candidate(cid, pattern, cos, question=None, **kw):
    c = {"candidate_id": cid, "seed_pattern": pattern, "status": "candidate", "model": MODEL,
         "question": question or f"Question {cid}: does X differ between groups in the 22nd Assembly?",
         "quantity": "passage rate", "premise": f"premise {cid}", "trace_violations": [],
         "guard": {"nearest": "r27", "cosine": cos, "status": "clear"}}
    c.update(kw)
    return c


def gate_fields(cid, **kw):
    f = {"seed": f"Seed for {cid}: does the first-term passage gap close within the 22nd Assembly",
         "identification": "Within-assembly comparison of member-bill passage by proposal year.",
         "exclusion_criteria": "(X1) no productivity counts (X2) no ideology",
         "prior": "First-term members' bills pass less often in year one than re-elected members' bills.",
         "prior_direction": "negative",
         "falsifier": "The year-one gap lies inside plus or minus 1 percentage point.",
         "falsifier_threshold": 1, "falsifier_unit": "percentage point",
         "premise": "The year-one strict passage rate of first-term members is at least 1 point lower."}
    f.update(kw)
    return f


# ---------------------------------------------------------------------------
# Part 1: in-process
# ---------------------------------------------------------------------------

class Env:
    def __init__(self, root: Path):
        self.root, self.know, self.forum = root, root / "knowledge", root / "forum"
        self.know.mkdir(parents=True)
        self.forum.mkdir()
        (root / "topic_gate.md").write_text("# Topic Gate\n\n## R28 - old\n\nseed: old seed\n\nsigned: 2026-08-24\n",
                                            encoding="utf-8")
        self.slates, self.drafts, self.premises, self.run_arc_calls = [], [], [], []
        self.alerts, self.cfg = [], {"model": MODEL, "stage2": {"binding_checks": False}}
        self.run_arc_result = (0, {"state": "stopped", "article": "2026-10-01_r33.tex", "reason": "done"})

    def propose(self, k, seed):
        assert self.slates, "unexpected slate proposal"
        cands = self.slates.pop(0)
        sid = arc_slate.new_slate_id()
        slate = {"slate_id": sid, "ts": "2026-10-01T10:00:00", "seed": seed, "seed_patterns": [],
                 "opener_counts": {"evidence_gap": 2}, "candidates": cands,
                 "display_order": [c["candidate_id"] for c in cands if c["status"] == "candidate"],
                 "dedupe": {}, "stub": None}
        arc_slate.SLATES_DIR.mkdir(parents=True, exist_ok=True)
        (arc_slate.SLATES_DIR / f"{sid}.json").write_text(json.dumps(slate), encoding="utf-8")
        return slate

    def draft(self, cand, cfg):
        assert self.drafts, f"unexpected gate draft for {cand['candidate_id']}"
        self.drafted = getattr(self, "drafted", []) + [cand["candidate_id"]]
        step = self.drafts.pop(0)
        if isinstance(step, str):
            return {"failure": step, "run_id": "gd", "model": MODEL, "resume_at": None, "fields": None, "errors": []}
        errs = auto_arc.validate_gate(step, False, auto_arc.existing_seeds())
        return {"failure": "ok", "run_id": f"gate_draft_{cand['candidate_id']}", "model": MODEL,
                "resume_at": None, "fields": None if errs else step, "errors": errs}

    def premise(self, gate):
        assert self.premises, "unexpected premise check"
        self.premised = getattr(self, "premised", []) + [gate["seed"]]
        step = self.premises.pop(0)
        if step == "usage_limit":
            return {"source": "computed", "call_ok": False, "failure": "usage_limit", "passes": None}
        return {"source": "computed", "call_ok": True, "failure": "ok", "passes": step, "value": -0.4, "n": 900,
                "run_id": "premise_check_x"}

    def run_arc_process(self, cmd):
        self.run_arc_calls.append(cmd)
        rc, status = self.run_arc_result
        (self.know / "arc_status.json").write_text(json.dumps(status), encoding="utf-8")
        (self.know / "active_arc.json").write_text(json.dumps({"arc_id": "6", "start_round": 31}), encoding="utf-8")
        return rc

    def rows(self):
        return auto_arc.load_rows()

    def taste(self):
        f = self.know / "taste_log.jsonl"
        return [json.loads(x) for x in f.read_text().splitlines()] if f.exists() else []


@pytest.fixture
def env(tmp_path, monkeypatch):
    e = Env(tmp_path)
    for name, val in {"BASE_DIR": tmp_path, "KNOWLEDGE_DIR": e.know, "LOGS_DIR": tmp_path / "logs",
                      "AUTO_RUNS": e.know / "auto_runs.jsonl", "ACTIVE_ARC_FILE": e.know / "active_arc.json",
                      "ARC_STATUS_FILE": e.know / "arc_status.json", "TOPIC_GATE_FILE": tmp_path / "topic_gate.md",
                      "RUN_ARC": tmp_path / "run_arc.py"}.items():
        monkeypatch.setattr(auto_arc, name, val)
    for name, val in {"SLATES_DIR": e.know / "slates", "TASTE_LOG": e.know / "taste_log.jsonl",
                      "GATE_CANDIDATES": e.know / "gate_candidates.jsonl",
                      "TOPIC_GATE_FILE": tmp_path / "topic_gate.md"}.items():
        monkeypatch.setattr(arc_slate, name, val)
    monkeypatch.setattr(run_forum, "ACTIVE_ARC_FILE", e.know / "active_arc.json")
    monkeypatch.setattr(run_forum, "ARC_STATUS_FILE", e.know / "arc_status.json")
    monkeypatch.setattr(run_forum, "PREVIEW_ARC", None)
    monkeypatch.setattr(forum_index, "FORUM_DIR", e.forum)
    monkeypatch.setattr(auto_arc, "_cfg", lambda: e.cfg)
    monkeypatch.setattr(arc_slate, "_binding_checks_on", lambda: False)
    monkeypatch.setattr(auto_arc, "_propose", e.propose)
    monkeypatch.setattr(auto_arc, "draft_gate", e.draft)
    monkeypatch.setattr(auto_arc, "_premise_run", e.premise)
    monkeypatch.setattr(auto_arc, "_run_arc_process", e.run_arc_process)
    e.stray = []                                  # files a fake premise check "changed"
    monkeypatch.setattr(auto_arc, "premise_guard_before", lambda: {"tree": None, "external": None})
    monkeypatch.setattr(auto_arc, "premise_guard_after", lambda before, run_id: list(e.stray))
    monkeypatch.setattr(auto_arc, "questions_taken", lambda: "(none)")
    monkeypatch.setattr(run_forum, "data_fingerprint",
                        lambda data_dir=None: {"id": "kbl-000000000001", "n_files": 3, "kna_version": "0.7.0"})
    monkeypatch.setattr(claude_cli, "notify", lambda title, msg: e.alerts.append((title, msg)))
    return e


def args(**kw):
    base = {"max_rounds": 8, "no_push": False, "allow_data_change": False, "fresh": False, "run_arc_args": []}
    base.update(kw)
    return SimpleNamespace(**base)


def test_rank_uses_cosine_then_the_least_used_pattern_then_id():
    cands = [candidate("C1", "evidence_gap", 0.30), candidate("C2", "scope_mismatch", 0.30),
             candidate("C3", "puzzle_contradiction", 0.12), candidate("C4", "scope_mismatch", 0.30)]
    ranked = auto_arc.rank(cands, {"evidence_gap": 2, "scope_mismatch": 0})
    assert [c["candidate_id"] for c in ranked] == ["C3", "C2", "C4", "C1"]
    no_guard = candidate("C5", "evidence_gap", None)
    no_guard["guard"] = None                      # no prior corpus: treated as cosine 0
    assert auto_arc.rank(cands + [no_guard])[0]["candidate_id"] == "C5"


def test_eligible_drops_trace_violations_and_diversity_blocks():
    slate = {"candidates": [candidate("C1", "evidence_gap", 0.2),
                            candidate("C2", "evidence_gap", 0.2, trace_violations=[{"tool": "Read"}]),
                            candidate("C3", "evidence_gap", 0.9, guard={"nearest": "r30", "cosine": 0.9,
                                                                        "status": "block"}),
                            {**candidate("C4", "evidence_gap", 0.1), "status": "removed"}]}
    keep, dropped = auto_arc.eligible(slate)
    assert [c["candidate_id"] for c in keep] == ["C1"]
    assert [(c["candidate_id"], r.split(" ")[0]) for c, r in dropped] == [("C2", "dropped"), ("C3", "dropped")]


@pytest.mark.parametrize("change,problem", [
    ({"prior_direction": "up"}, "prior_direction"),
    ({"falsifier": "The gap does not close."}, "numeric threshold"),
    ({"falsifier_threshold": "one"}, "falsifier_threshold"),
    ({"exclusion_criteria": "no ideology"}, "(X1)"),
    ({"prior": "Pre-registered belief that gaps close."}, "pre-registered"),
    ({"seed": "old seed"}, "restates"),
    ({"premise": ""}, "missing premise"),
])
def test_validate_gate_catches_each_problem(change, problem):
    errs = auto_arc.validate_gate(gate_fields("C1", **change), False, ["old seed"])
    assert any(problem in e for e in errs), errs
    assert auto_arc.validate_gate(gate_fields("C1"), False, ["old seed"]) == []


def test_stage2_fields_are_required_only_with_binding_checks():
    assert "decision_rule" not in auto_arc.gate_schema(False)["required"]
    s2 = auto_arc.gate_schema(True)
    assert {"decision_rule", "sesoi", "null_paper"} <= set(s2["required"])
    errs = auto_arc.validate_gate(gate_fields("C1"), True, [])
    assert "missing decision_rule" in errs


def test_tidy_applies_the_public_prose_rules():
    assert auto_arc._tidy("The gap narrows — slowly; it closes by year three.") == \
        "The gap narrows - slowly. It closes by year three."


def test_start_selects_drafts_checks_premise_signs_and_runs_the_arc(env):
    env.slates = [[candidate("C1", "evidence_gap", 0.50), candidate("C2", "scope_mismatch", 0.30),
                   candidate("C3", "puzzle_contradiction", 0.40)]]
    env.drafts = [gate_fields("C2"), gate_fields("C3")]
    env.premises = [False, True]
    assert auto_arc.cmd_start(args()) == 0
    assert env.drafted == ["C2", "C3"]
    # One gate entry, for C3, signed under the delegation and never in the researcher's name.
    gate = (env.root / "topic_gate.md").read_text(encoding="utf-8")
    assert gate.count("drafted from arc_slate") == 1 and "seed: Seed for C3" in gate
    assert "drafted_by: automatic gate drafter (auto_arc.py gate_draft call, claude-opus-5-5, run gate_draft_C3)" in gate
    assert f"signed_by: {auto_arc.AUTO_SIGNER}" in gate
    entry = gate.split("## R28")[0]
    for line in entry.splitlines():
        if line.startswith(("drafted_by:", "signed_by:")):
            assert not line.split(":", 1)[1].strip().lower().startswith("researcher"), line
    # The taste log: every listed candidate decided by the automatic selector, latest decision per candidate.
    latest = arc_slate.decisions(env.taste()[0]["slate_id"])
    assert {k: v["decision"] for k, v in latest.items()} == {"C1": "reject", "C2": "reject", "C3": "accept"}
    assert latest["C2"]["reason"].startswith("premise check failed")
    assert "after C2 was rejected" in latest["C3"]["reason"]
    assert all(r["decided_by"] == auto_arc.AUTO_SELECTOR for r in env.taste())
    assert all(":" not in r["reason"] and ";" not in r["reason"] for r in env.taste())
    # run_arc got the signed seed.
    [cmd] = env.run_arc_calls
    assert cmd[cmd.index("--topic") + 1] == gate_fields("C3")["seed"]
    assert "--no-push" not in cmd and cmd[cmd.index("--max-rounds") + 1] == "8"
    steps = [(r["step"], r["status"]) for r in env.rows()]
    assert steps == [("start", "ok"), ("data", "ok"), ("slate", "ok"), ("select", "ok"), ("gate_draft", "ok"),
                     ("premise_check", "rejected"), ("select", "ok"), ("gate_draft", "ok"),
                     ("premise_check", "ok"), ("gate_entry", "ok"), ("run_arc", "started"), ("outcome", "published")]
    assert env.alerts[-1][0] == "KNA auto_arc: paper published"


def test_every_candidate_failing_proposes_one_more_slate_then_stops(env):
    env.slates = [[candidate("C1", "evidence_gap", 0.5), candidate("C2", "evidence_gap", 0.3)],
                  [candidate("C1", "scope_mismatch", 0.2)]]
    env.drafts = [gate_fields("C2"), gate_fields("C1", falsifier="no number here"), gate_fields("C1")]
    env.premises = [False, False]
    assert auto_arc.cmd_start(args()) == 1
    assert env.slates == [] and env.run_arc_calls == []
    assert "drafted from arc_slate" not in (env.root / "topic_gate.md").read_text(encoding="utf-8")
    last = env.rows()[-1]
    assert last["step"] == "select" and last["status"] == "stop" and "2 slates" in last["detail"]["message"]
    assert env.alerts[-1][0] == "KNA auto_arc: stopped"
    # A stop that exhausted both slates is not resumable, so start works again.
    assert auto_arc.paused_selection() is None


def test_usage_limit_in_the_gate_draft_pauses_and_resume_retries_the_same_candidate(env):
    env.slates = [[candidate("C1", "evidence_gap", 0.5), candidate("C2", "evidence_gap", 0.3)]]
    env.drafts = ["usage_limit"]
    assert auto_arc.cmd_start(args()) == claude_cli.EXIT_USAGE_LIMIT
    paused = auto_arc.paused_selection()
    assert paused["step"] == "gate_draft" and paused["ctx"]["candidate_id"] == "C2"
    assert env.alerts[-1][0] == "KNA auto_arc: paused"
    assert auto_arc.cmd_start(args()) == 1                      # refused: resume or --fresh
    env.drafts, env.premises = [gate_fields("C2")], [True]
    assert auto_arc.cmd_resume(args()) == 0
    assert env.drafted == ["C2", "C2"] and len(env.run_arc_calls) == 1
    assert {r["run_id"] for r in env.rows()} == {env.rows()[0]["run_id"]}      # one auto run throughout


def test_usage_limit_in_the_premise_check_reuses_the_draft_on_resume(env):
    env.slates = [[candidate("C1", "evidence_gap", 0.5)]]
    env.drafts, env.premises = [gate_fields("C1")], ["usage_limit"]
    assert auto_arc.cmd_start(args()) == claude_cli.EXIT_USAGE_LIMIT
    env.premises = [True]
    assert auto_arc.cmd_resume(args(no_push=True)) == 0
    assert env.drafted == ["C1"]                                # the gate was drafted once
    assert "--no-push" in env.run_arc_calls[0]
    assert env.rows()[-1]["status"] == "published"


def test_usage_limit_in_the_slate_pauses_without_counting_the_slate(env):
    cands = [candidate("C1", "evidence_gap", 0.5), {**candidate("C2", "evidence_gap", 0.4), "status": "failed",
                                                    "failure": "usage_limit"}]
    env.slates = [cands, [candidate("C1", "evidence_gap", 0.2)]]
    assert auto_arc.cmd_start(args()) == claude_cli.EXIT_USAGE_LIMIT
    assert auto_arc.paused_selection()["ctx"]["slates"] == []
    env.drafts, env.premises = [gate_fields("C1")], [True]
    assert auto_arc.cmd_resume(args()) == 0
    assert env.slates == []                                     # the fresh slate was the first counted one



def test_a_premise_check_that_writes_elsewhere_stops_without_signing(env):
    env.slates = [[candidate("C1", "evidence_gap", 0.5)]]
    env.drafts, env.premises = [gate_fields("C1")], [True]
    env.stray = ["forum/091_literature_scout.md"]
    assert auto_arc.cmd_start(args()) == 1
    assert "drafted from arc_slate" not in (env.root / "topic_gate.md").read_text(encoding="utf-8")
    assert env.run_arc_calls == []
    last = env.rows()[-1]
    assert (last["step"], last["status"]) == ("premise_check", "stop")
    assert last["detail"]["changed"] == ["forum/091_literature_scout.md"]
    assert "start --fresh" in last["detail"]["message"] and env.alerts[-1][0] == "KNA auto_arc: stopped"
    assert auto_arc.paused_selection() is None                  # not resumable, a person looks first


def test_premise_guard_sees_tree_changes_but_allows_the_result_file(tmp_path, monkeypatch):
    repo = tmp_path / "g"
    repo.mkdir()
    genv = {**{k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
            "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CEILING_DIRECTORIES": str(tmp_path)}
    (repo / "tracked.md").write_text("a\n", encoding="utf-8")
    (repo / "dirty.md").write_text("a\n", encoding="utf-8")
    for cmd in (["init", "-q"], ["add", "-A"], ["-c", "user.name=t", "-c", "user.email=t@example.org",
                                                   "commit", "-q", "-m", "base"]):
        subprocess.run(["git", *cmd], cwd=repo, env=genv, check=True, capture_output=True)
    (repo / "dirty.md").write_text("changed before the call\n", encoding="utf-8")
    monkeypatch.setattr(auto_arc, "BASE_DIR", repo)
    for k in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))
    before = {"tree": auto_arc._tree_state(), "external": None}
    assert before["tree"] == {"dirty.md": auto_arc._sha256(repo / "dirty.md")}
    (repo / "knowledge" / "premise_checks").mkdir(parents=True)
    (repo / "knowledge" / "premise_checks" / "seed.json").write_text("{}", encoding="utf-8")
    assert auto_arc.premise_guard_after(before, "r") == []
    (repo / "tracked.md").write_text("b\n", encoding="utf-8")
    (repo / "dirty.md").write_text("changed again\n", encoding="utf-8")
    (repo / "new.txt").write_text("x", encoding="utf-8")
    assert auto_arc.premise_guard_after(before, "r") == ["dirty.md", "new.txt", "tracked.md"]
    monkeypatch.setattr(auto_arc, "BASE_DIR", tmp_path / "not_a_repo")
    assert auto_arc._tree_state() is None


def test_start_refuses_an_open_arc_and_an_incomplete_round(env, capsys):
    (env.know / "active_arc.json").write_text(json.dumps({"arc_id": "6", "start_round": 31}), encoding="utf-8")
    (env.know / "arc_status.json").write_text(json.dumps({"seed": None, "state": "running"}), encoding="utf-8")
    assert auto_arc.cmd_start(args()) == 1
    assert "auto_arc.py resume" in capsys.readouterr().out
    (env.know / "arc_status.json").write_text(json.dumps({"state": "stopped", "action": "stop"}), encoding="utf-8")
    (env.forum / "091_literature_scout.md").write_text("---\nround: 31\nrole: literature_scout\n---\n", encoding="utf-8")
    assert auto_arc.cmd_start(args()) == 1
    assert "incomplete" in capsys.readouterr().out
    assert env.rows() == []


def test_resume_of_an_open_arc_goes_through_run_arc(env):
    (env.know / "active_arc.json").write_text(json.dumps({"arc_id": "6", "start_round": 31}), encoding="utf-8")
    (env.know / "arc_status.json").write_text(json.dumps({"state": "paused_usage_limit"}), encoding="utf-8")
    env.run_arc_result = (claude_cli.EXIT_USAGE_LIMIT, {"state": "paused_usage_limit", "resume_after": "2026-10-01T15:00"})
    assert auto_arc.cmd_resume(args(run_arc_args=["--ack-stop"])) == claude_cli.EXIT_USAGE_LIMIT
    [cmd] = env.run_arc_calls
    assert "--topic" not in cmd and cmd[-1] == "--ack-stop"
    assert env.rows()[-1]["status"] == "paused_usage_limit"
    assert "2026-10-01T15:00" in env.alerts[-1][1]



def test_resume_retries_a_blocked_push_of_a_closed_arc(env, monkeypatch):
    """A paper whose push release_check blocked stays committed locally. Once
    the problems are fixed, resume runs the check again and pushes."""
    import run_arc
    monkeypatch.setattr(run_arc, "LOGS_DIR", env.root / "logs")
    (env.know / "active_arc.json").write_text(json.dumps({"arc_id": "6", "start_round": 31}), encoding="utf-8")
    blocked = {"state": "stopped", "action": "draft_and_stop", "article": "2026-10-01_r33.tex",
               "push_blocked": {"at": "2026-10-01T12:00", "commit": "Auto: Season 2 R33 (article)",
                                "reasons": ["leaks: build_site.py:2012 private:6"]}}
    (env.know / "arc_status.json").write_text(json.dumps(blocked), encoding="utf-8")
    results = [False, True]
    pushes = []

    def fake_push_checked(label):
        pushes.append(label)
        ok = results.pop(0)
        st = json.loads((env.know / "arc_status.json").read_text(encoding="utf-8"))
        if ok:
            st.pop("push_blocked", None)
        (env.know / "arc_status.json").write_text(json.dumps(st), encoding="utf-8")
        return ok
    monkeypatch.setattr(run_arc, "push_checked", fake_push_checked)
    assert auto_arc.cmd_resume(args()) == 1                     # still blocked
    assert env.rows()[-1]["status"] == "blocked"
    assert env.rows()[-1]["detail"]["reasons"] == ["leaks: build_site.py:2012 private:6"]
    assert auto_arc.cmd_resume(args()) == 0                     # fixed: checked and pushed
    assert pushes == ["Auto: Season 2 R33 (article)"] * 2
    assert env.rows()[-1]["status"] == "ok" and env.alerts[-1][0] == "KNA auto_arc: pushed"
    assert not (env.root / "logs" / "run_arc.lock").exists()
    assert auto_arc.cmd_resume(args()) == 1                     # nothing left to resume
    assert env.run_arc_calls == []


@pytest.mark.parametrize("rc,status,no_push,outcome", [
    (0, {"state": "stopped", "article": "p.tex"}, False, "published"),
    (0, {"state": "stopped", "article": "p.tex", "push_blocked": {"reasons": ["x"]}}, False, "published_push_blocked"),
    (0, {"state": "stopped", "reason": "arc closed: Critic archived the finding"}, False, "closed"),
    (2, {"state": "draft_blocked"}, False, "draft_blocked"),
    (75, {"state": "paused_usage_limit"}, False, "paused_usage_limit"),
    (0, {"state": "running"}, False, "max_rounds"),
    (1, {"state": "external_write"}, False, "external_write"),
    (1, {"state": "stopped"}, False, "stopped"),
    (4, {"state": "running"}, False, "busy"),
])
def test_outcome_mapping(rc, status, no_push, outcome):
    assert auto_arc.outcome_of(rc, status, {"arc_id": "6"}, no_push)[0] == outcome
    assert "locally (--no-push)" in auto_arc.outcome_of(0, {"state": "stopped", "article": "p.tex"}, {}, True)[2]


def test_lock_holds_against_a_live_auto_arc_only(env):
    """The lock must hold against a running auto_arc (run_forum._pid_alive
    answers only for run_forum processes, so it cannot be the check), and a
    pid that now belongs to another process must not hold it."""
    lock = env.root / "logs" / "auto_arc.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    holder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)", "auto_arc"])
    other = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    try:
        lock.write_text(json.dumps({"pid": holder.pid}), encoding="utf-8")
        with pytest.raises(SystemExit, match="another auto_arc"):
            auto_arc.acquire_lock()
        lock.write_text(json.dumps({"pid": other.pid}), encoding="utf-8")
        path = auto_arc.acquire_lock()
        assert json.loads(path.read_text(encoding="utf-8"))["pid"] == os.getpid()
        auto_arc.release_lock(path)
        assert not lock.exists()
    finally:
        for p in (holder, other):
            p.kill()
            p.wait()
    lock.write_text(json.dumps({"pid": holder.pid}), encoding="utf-8")   # the holder is gone now
    auto_arc.release_lock(auto_arc.acquire_lock())
    assert not lock.exists()


def test_status_reports_step_arc_round_verdicts_and_pause(env, capsys, monkeypatch):
    import verdict
    monkeypatch.setattr(verdict, "load_rows", lambda: [{"round": 30, "verdict": "pursue"},
                                                       {"round": 31, "verdict": "revise", "falsifier_tested": "no"}])
    (env.know / "active_arc.json").write_text(json.dumps({"arc_id": "6", "start_round": 31, "seed": "S",
                                                          "drafted_by": "automatic gate drafter",
                                                          "signed_by": auto_arc.AUTO_SIGNER,
                                                          "data_fingerprint": {"id": "kbl-1"}}), encoding="utf-8")
    (env.know / "arc_status.json").write_text(json.dumps({"state": "paused_usage_limit", "reason": "usage limit at R32",
                                                          "resume_after": "2026-10-01T15:00", "last_round": 31}),
                                              encoding="utf-8")
    auto_arc.log_step("auto_x", "outcome", "paused_usage_limit", {"message": "m"})
    assert auto_arc.cmd_status(SimpleNamespace(json=False)) == 0
    out = capsys.readouterr().out
    assert "outcome (paused_usage_limit" in out and "arc:      6 from R31 (open): S" in out
    assert "R31 revise (falsifier no)" in out and "R30" not in out
    assert "pause:    paused_usage_limit: usage limit at R32 (resume after 2026-10-01T15:00)" in out
    assert "data:     kbl-1" in out
    s = auto_arc.status_report()
    assert s["verdicts"] == [{"round": 31, "verdict": "revise", "falsifier_tested": "no"}]


def test_shipped_config_and_docs_describe_the_pipeline():
    cfg = json.loads((ROOT / "agents.json").read_text(encoding="utf-8"))["forum_config"]
    assert cfg["effort_by_task"]["gate_draft"] == "high"
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "python3 auto_arc.py start" in readme and "release_check.py" in readme
    assert "seniority" in readme.lower()
    assert "researcher" not in auto_arc.AUTO_SIGNER.split(",")[0]


@pytest.mark.parametrize("code,expect", [(4, 0), (75, 75), (1, 1), (0, 0)])
def test_cron_step_skips_while_another_run_arc_runs(tmp_path, code, expect):
    """auto_run.sh (cron) continues a running arc with run_arc --max-rounds 1.
    While auto_arc's run_arc holds the lock, run_arc exits 4 and the cron step
    is skipped, not failed. Other exits keep their meaning."""
    repo, state, bin_dir = tmp_path / "repo", tmp_path / "state", tmp_path / "bin"
    for d in (repo / "knowledge", state, bin_dir):
        d.mkdir(parents=True)
    shutil.copy2(ROOT / "auto_run.sh", repo / "auto_run.sh")
    (repo / "run_arc.py").write_text("import os, sys\nsys.exit(int(os.environ['RUN_ARC_EXIT']))\n",
                                     encoding="utf-8")
    (repo / "knowledge" / "active_arc.json").write_text(json.dumps({"seed": "s", "start_round": 31}),
                                                        encoding="utf-8")
    (repo / "knowledge" / "arc_status.json").write_text(json.dumps({"state": "running"}), encoding="utf-8")
    py = bin_dir / "python3"
    py.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
    py.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("KNA_", "STUB_"))}
    env.update(PATH=f"{bin_dir}{os.pathsep}{env.get('PATH', '')}", KNA_AUTO_STATE_DIR=str(state),
               RUN_ARC_EXIT=str(code))
    rc = subprocess.run(["bash", str(repo / "auto_run.sh"), "forum"], cwd=repo, env=env, capture_output=True,
                        text=True, timeout=60).returncode
    assert rc == expect
    log = (state / "kna-auto-forum.log").read_text(encoding="utf-8")
    assert ("another run_arc is running. Skipped this step." in log) == (code == 4)
    assert ("stopped on a usage limit" in log) == (code == 75)


# ---------------------------------------------------------------------------
# Part 2: end to end on a scratch copy with the stub binary
# ---------------------------------------------------------------------------

STUB_TOPIC_DIVERSITY = r'''"""Scratch stand-in for topic_diversity: the real module with the embedding
model replaced. A text carrying the marker [[cos=X]] gets cosine X against
every text without a marker, and near zero against other marked texts."""
import re as _re
import numpy as _np
import _real_topic_diversity as _real

globals().update({k: v for k, v in vars(_real).items() if not k.startswith("__")})
_slots = {}


def embed(texts, name=None):
    rows = []
    for t in texts:
        v = _np.zeros(64, dtype=_np.float32)
        m = _re.search(r"\[\[cos=([0-9.]+)\]\]", t or "")
        if m:
            x = float(m.group(1))
            j = _slots.setdefault(t, 1 + len(_slots))
            v[0], v[j] = x, (1 - x * x) ** 0.5
        else:
            v[0] = 1.0
        rows.append(v)
    return _np.vstack(rows) if rows else _np.zeros((0, 64), dtype=_np.float32)


def check_post(post_path, log=True, *, round_num=None, arc_start=None, run_id=None):
    return {"status": "clear", "max_cosine": 0.1, "n_prior": 0}
'''

STUB_DRAFT_ARTICLE = r'''"""Scratch stand-in for draft_article: writes a gated paper and exits 0.
It reads the data availability field run_forum exposes in arc_status."""
import json, sys
from datetime import date
from pathlib import Path
base = Path(__file__).resolve().parent
rnd = int(sys.argv[sys.argv.index("--round") + 1])
fp = json.loads((base / "knowledge" / "arc_status.json").read_text()).get("data_fingerprint") or {}
stem = f"{date.today().isoformat()}_r{rnd}"
(base / "articles").mkdir(exist_ok=True)
(base / "articles" / f"{stem}.tex").write_text("\\title{Scratch paper}\n" + fp.get("statement", "NO FINGERPRINT") + "\n")
(base / "articles" / f"{stem}.pdf").write_bytes(b"%PDF-1.5 scratch")
print("drafted", stem)
'''

STUB_BUILD_SITE = r'''"""Scratch stand-in for build_site."""
import shutil
from pathlib import Path
base = Path(__file__).resolve().parent
docs = base / "docs"
(docs / "articles").mkdir(parents=True, exist_ok=True)
(docs / "index.html").write_text("scratch site\n")
for pdf in (base / "articles").glob("*.pdf"):
    shutil.copy2(pdf, docs / "articles" / pdf.name)
'''

# Writes the JSON result a premise-check call is told to write, then hands
# over to the real stub binary (which records the call and emits the events).
PREMISE_WRAPPER = r'''#!{python}
import json, os, re, sys
argv = sys.argv[1:]
if "--system-prompt-file" in argv:
    text = open(argv[argv.index("--system-prompt-file") + 1], encoding="utf-8").read()
    m = re.search(r"Then write (\S+) as JSON", text)
    if "running a premise check" in text and m:
        queue = os.environ["PREMISE_RESULTS"]
        results = json.load(open(queue, encoding="utf-8"))
        result = results.pop(0)
        json.dump(results, open(queue, "w", encoding="utf-8"))
        os.makedirs(os.path.dirname(m.group(1)), exist_ok=True)
        json.dump(result, open(m.group(1), "w", encoding="utf-8"))
os.execv({python!r}, [{python!r}, {stub!r}] + argv)
'''

SCRATCH_SKIP = {"topic_diversity.py", "draft_article.py", "build_site.py"}


def scout_text(rnd):
    return (f"---\nauthor: \"Scout\"\ntype: research_agenda\n---\n\n# R{rnd} scout\n\n## Prediction to Test\n\n"
            f"The first-term gap closes by year three.\n")


def analyst_text(rnd):
    code = ('```python\nimport pandas as pd\nm = pd.read_parquet(f"{D}/members_22.parquet")\n'
            'm["first_term"] = (m["reelection"] == "초선")\n```\n') if rnd == 31 else ""
    return f"---\nauthor: \"Analyst\"\ntype: data_report\n---\n\n# R{rnd} analyst\n\nThe gap is 2 points.\n\n{code}"


def critic_steps(rnd, post, verdict_label, falsifier):
    s = {"research_novelty": 2, "empirical_rigor": 3, "theoretical_connection": 2, "actionability": 3,
         "opportunity_pattern": "puzzle_contradiction", "method_paradigm": "empirical_mapping",
         "operation": "measure", "falsifier_tested": falsifier, "prior_status": "supported",
         "headline_basis": "prespecified", "verdict": verdict_label, "one_line": f"R{rnd} headline holds."}
    yaml = "\n".join(f"  {k}: {json.dumps(v) if isinstance(v, str) and ' ' in v else v}" for k, v in s.items())
    text = (f"---\nauthor: \"Critic\"\ntype: review\n---\n\n# R{rnd} review\n\nReview text.\n\n"
            f"```yaml\nscoring:\n{yaml}\n```\n")
    return {"write": [[str(post), text]], "structured": s}


@pytest.fixture
def scratch(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    for f in ROOT.glob("*.py"):
        if f.name not in SCRATCH_SKIP:
            shutil.copy2(f, repo / f.name)
    shutil.copy2(ROOT / "topic_diversity.py", repo / "_real_topic_diversity.py")
    (repo / "topic_diversity.py").write_text(STUB_TOPIC_DIVERSITY, encoding="utf-8")
    (repo / "draft_article.py").write_text(STUB_DRAFT_ARTICLE, encoding="utf-8")
    (repo / "build_site.py").write_text(STUB_BUILD_SITE, encoding="utf-8")
    for rel in ("agents.json", "DATA_SOURCES.md", "topic_gate.md", ".gitignore", "knowledge/data_pitfalls.md"):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, repo / rel)
    shutil.copytree(ROOT / "knowledge" / "schemas", repo / "knowledge" / "schemas")
    agents = json.loads((repo / "agents.json").read_text(encoding="utf-8"))
    assert agents["forum_config"]["model"] == MODEL
    assert not any(agents["forum_config"]["stage2"].values())
    for d in ("forum", "summaries", "articles", "workspace", "logs"):
        (repo / d).mkdir(exist_ok=True)
    for n in range(1, 91):                                   # the legacy grid ends at R30 (post 090)
        role = forum_index.ROLE_ORDER[(n - 1) % 3]
        body = f'---\nauthor: "{role}"\n---\n\n# Post {n}\n\nlegacy body {n}\n'
        if role == "critic":
            body += f'\n```yaml\nscoring:\n  verdict: revise\n  one_line: "legacy finding {n}"\n```\n'
        (repo / "forum" / f"{n:03d}_{role}.md").write_text(body, encoding="utf-8")
    data = tmp_path / "kbl"
    data.mkdir()
    # run_forum's kna setup check reads the members schema and the CLI
    # version, so the scratch data carries a real members file with the
    # kna 0.7.0 term_number column and PATH gets a stub kna 0.7.0 CLI.
    import pyarrow as pa
    import pyarrow.parquet as pq
    pq.write_table(pa.table({"mona_cd": ["M1"], "term_number": [1], "seniority": ["초선"]}),
                   data / "members_22.parquet")
    (data / "master_bills_22.parquet").write_bytes(b"PAR1 scratch bills PAR1")
    kna_bin = tmp_path / "kna_bin"
    kna_bin.mkdir()
    (kna_bin / "kna").write_text("#!/bin/sh\necho 'kna, version 0.7.0'\n", encoding="utf-8")
    (kna_bin / "kna").chmod(0o755)
    wrapper = tmp_path / "claude_wrapper.py"
    wrapper.write_text(PREMISE_WRAPPER.format(python=sys.executable, stub=str(STUB)), encoding="utf-8")
    wrapper.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if not k.startswith(("KNA_", "STUB_", "GIT_"))}
    env["PATH"] = f"{kna_bin}{os.pathsep}{env.get('PATH', '')}"
    env.update(KNA_CLAUDE_BIN=str(wrapper), STUB_CLAUDE_STATE=str(tmp_path / "stub_state"),
               STUB_CLAUDE_PLAN=str(tmp_path / "plan.json"), CLAUDE_CONFIG_DIR=str(tmp_path / "claude_config"),
               PREMISE_RESULTS=str(tmp_path / "premise_results.json"), KBL_DATA=str(data), KNA_NO_SLEEP="1",
               KNA_NO_NOTIFY="1", PYTHONDONTWRITEBYTECODE="1", GIT_CONFIG_GLOBAL="/dev/null",
               GIT_CONFIG_NOSYSTEM="1", GIT_AUTHOR_NAME="scratch", GIT_AUTHOR_EMAIL="scratch@example.org",
               GIT_COMMITTER_NAME="scratch", GIT_COMMITTER_EMAIL="scratch@example.org",
               GIT_CEILING_DIRECTORIES=str(tmp_path))
    for cmd in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "scratch base"]):
        subprocess.run(["git", *cmd], cwd=repo, env=env, check=True, capture_output=True)
    return SimpleNamespace(root=tmp_path, repo=repo, env=env, data=data)


def test_end_to_end_one_command_opens_runs_and_drafts_an_arc(scratch):
    repo, f, s = scratch.repo, scratch.repo / "forum", scratch.repo / "summaries"
    cands = [candidate("C1", "x", 0.50, question="C1 question [[cos=0.50]] on committee referrals"),
             candidate("C2", "x", 0.30, question="C2 question [[cos=0.30]] on first-term passage"),
             candidate("C3", "x", 0.40, question="C3 question [[cos=0.40]] on first-term absorption")]
    slate_steps = [{"structured": {k: v for k, v in c.items()
                                   if k not in ("candidate_id", "seed_pattern", "model", "trace_violations", "guard")}}
                   for c in cands]
    rounds = []
    for rnd, n, label, ft in ((31, 91, "revise", "no"), (32, 94, "pursue", "no"), (33, 97, "pursue", "yes")):
        rounds += [{"write": [[str(f / f"{n:03d}_literature_scout.md"), scout_text(rnd)]]},
                   {"write": [[str(f / f"{n + 1:03d}_data_analyst.md"), analyst_text(rnd)]]},
                   critic_steps(rnd, f / f"{n + 2:03d}_critic.md", label, ft),
                   {"write": [[str(s / f"round_{rnd}.md"), f"---\nround: {rnd}\n---\n\n# Round {rnd} Summary\n"]]}]
    plan = slate_steps + [{"structured": gate_fields("C2")}, {},
                          {"structured": gate_fields("C3", seed="First-term absorption gap across the 22nd "
                                                                "Assembly term")}, {}] + rounds
    (scratch.root / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    (scratch.root / "premise_results.json").write_text(json.dumps([
        {"premise": "p", "value": 0.2, "ci": [-0.5, 0.9], "n": 900, "script": "s.py", "passes": False},
        {"premise": "p", "value": -1.8, "ci": [-2.6, -1.0], "n": 900, "script": "s.py", "passes": True}]))

    proc = subprocess.run([sys.executable, str(repo / "auto_arc.py"), "start", "--no-push"], cwd=repo,
                          env=scratch.env, capture_output=True, text=True, timeout=600)
    log = proc.stdout + proc.stderr
    assert proc.returncode == 0, log[-4000:]

    calls = [json.loads(x) for x in (scratch.root / "stub_state" / "calls.jsonl").read_text().splitlines()]
    assert len(calls) == len(plan) == 19
    efforts = [c["argv"][c["argv"].index("--effort") + 1] for c in calls]
    assert efforts[3] == efforts[5] == "high"                            # gate_draft
    assert efforts[4] == efforts[6] == "medium"                          # premise_check
    assert calls[3]["argv"][calls[3]["argv"].index("--tools") + 1] == ""  # the drafter has no tools
    assert not calls[3]["cwd"].startswith(str(repo))                      # and runs outside the repository

    # The signed gate entry, with truthful provenance.
    gate = (repo / "topic_gate.md").read_text(encoding="utf-8")
    new_entry = gate.split("## R31 - Arc opening drafted from arc_slate")[1].split("\n## ")[0]
    assert "seed: First-term absorption gap across the 22nd Assembly term" in new_entry
    assert "drafted_by: automatic gate drafter (auto_arc.py gate_draft call, claude-opus-5-5" in new_entry
    assert f"signed_by: {auto_arc.AUTO_SIGNER}" in new_entry
    assert "C3 of slate" in new_entry
    prem = sorted((repo / "knowledge" / "premise_checks").glob("*.json"))
    assert sorted(json.loads(p.read_text())["passes"] for p in prem) == [False, True]
    assert all(str(repo) not in p.read_text() for p in prem)

    # The arc: opened on pinned data, three rounds, a paper that states the fingerprint.
    arc = json.loads((repo / "knowledge" / "active_arc.json").read_text())
    st = json.loads((repo / "knowledge" / "arc_status.json").read_text())
    assert arc["arc_id"] == "6" and arc["start_round"] == 31 and arc["signed_by"] == auto_arc.AUTO_SIGNER
    fp_id = arc["data_fingerprint"]["id"]
    assert st["data_fingerprint"]["id"] == fp_id and st["state"] == "stopped"
    assert st["last_round"] == 33 and st["verdict"] == "pursue" and st["article"].endswith("_r33.tex")
    paper = (repo / "articles" / st["article"]).read_text()
    assert fp_id in paper and "recorded when the arc opened" in paper
    # The R31 Critic saw the pitfall flag for the Analyst's reelection code.
    critic31 = calls[9]["argv"]
    prompt = Path(critic31[critic31.index("--system-prompt-file") + 1]).read_text(encoding="utf-8")
    assert "## Data pitfall flags" in prompt and "reelection_lifetime_count" in prompt
    critic32 = calls[13]["argv"]
    assert "Data pitfall flags" not in Path(critic32[critic32.index("--system-prompt-file") + 1]).read_text()

    # Commits in the scratch repository only, and nothing pushed (no remote, --no-push).
    msgs = subprocess.run(["git", "log", "--format=%s"], cwd=repo, env=scratch.env, capture_output=True,
                          text=True).stdout.splitlines()
    assert msgs[:4] == ["Auto: Season 2 R33 (article)", "Auto: Season 2 R33 (pursue)",
                        "Auto: Season 2 R32 (pursue)", "Auto: Season 2 R31 (revise)"]
    assert "PUSH" not in log and "release check" not in log

    steps = [(r["step"], r["status"]) for r in auto_arc_rows(repo)]
    assert steps == [("start", "ok"), ("data", "ok"), ("slate", "ok"), ("select", "ok"), ("gate_draft", "ok"),
                     ("premise_check", "rejected"), ("select", "ok"), ("gate_draft", "ok"),
                     ("premise_check", "ok"), ("gate_entry", "ok"), ("run_arc", "started"), ("outcome", "published")]
    outcome = auto_arc_rows(repo)[-1]["detail"]
    assert "committed locally (--no-push)" in outcome["message"] and outcome["data_fingerprint"] == fp_id
    for r in auto_arc_rows(repo):
        assert str(scratch.root) not in json.dumps(r)
    alerts = (repo / "logs" / "alerts.log").read_text(encoding="utf-8")
    assert "KNA auto_arc: paper published" in alerts

    # status names the arc, the rounds and the verdicts.
    out = subprocess.run([sys.executable, str(repo / "auto_arc.py"), "status"], cwd=repo, env=scratch.env,
                         capture_output=True, text=True, timeout=120).stdout
    assert "R31 revise" in out and "R33 pursue (falsifier yes)" in out and fp_id in out
    # The arc is closed now, so a second start does not refuse on it (it would propose a new slate).
    again = subprocess.run([sys.executable, str(repo / "auto_arc.py"), "resume"], cwd=repo, env=scratch.env,
                           capture_output=True, text=True, timeout=120)
    assert again.returncode == 1 and "nothing to resume" in again.stdout


def auto_arc_rows(repo: Path) -> list[dict]:
    f = repo / "knowledge" / "auto_runs.jsonl"
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines()]

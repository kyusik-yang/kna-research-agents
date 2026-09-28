"""claude_cli wrapper (M01, M02, M11): event parsing, failure classes,
live-call guard, pinned flags and isolation, sidecar and transcript archive,
continuation by --resume, failure policy, call budget and alerts.

Every call runs the stub binary in tests/fixtures/cli/stub_claude.py. No
test reaches a model."""

import gzip
import json
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import claude_cli  # noqa: E402

FIX = ROOT / "tests" / "fixtures" / "cli"
STUB = FIX / "stub_claude.py"
NY = ZoneInfo("America/New_York")

AGENTS = {
    "season": 2,
    "forum_config": {
        "model": "claude-opus-5-5",
        "effort_by_task": {"summary": "low", "draft_body": "high", "draft_fix": "medium",
                           "canary": "low", "agora": "low"},
        "max_turns": {"literature_scout": 120, "data_analyst": 250, "critic": 150},
        "max_calls_per_arc": 40,
        "failure_policy": {"usage_limit": "pause", "overloaded_wait_s": 600, "overloaded_max": 2,
                           "server_error_wait_s": 120, "server_error_max": 1,
                           "max_failed_runs_per_invocation": 4},
    },
    "agents": [
        {"id": "literature_scout", "name": "Scout", "prompt": "s",
         "allowed_tools": ["Bash", "Read", "Write"], "effort": "medium"},
        {"id": "data_analyst", "name": "Analyst", "prompt": "a",
         "allowed_tools": ["Bash", "Read", "Write", "Glob", "Grep"], "effort": "high"},
        {"id": "critic", "name": "Critic", "prompt": "c",
         "allowed_tools": ["Bash", "Read", "Write"], "effort": "high"},
    ],
}


def _write_agents(base: Path, **cfg_overrides) -> None:
    data = json.loads(json.dumps(AGENTS))
    for k, v in cfg_overrides.items():
        if v is None:
            data["forum_config"].pop(k, None)
        else:
            data["forum_config"][k] = v
    (base / "agents.json").write_text(json.dumps(data), encoding="utf-8")


@pytest.fixture
def repo(tmp_path, monkeypatch):
    base = tmp_path / "repo"
    (base / "workspace").mkdir(parents=True)
    (base / "forum").mkdir()
    _write_agents(base)
    monkeypatch.setattr(claude_cli, "BASE_DIR", base)
    state = tmp_path / "stub_state"
    monkeypatch.setenv("KNA_CLAUDE_BIN", str(STUB))
    monkeypatch.setenv("STUB_CLAUDE_STATE", str(state))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude_config"))
    monkeypatch.setenv("KNA_NO_SLEEP", "1")
    monkeypatch.delenv("KNA_ALLOW_LIVE", raising=False)
    monkeypatch.delenv("STUB_CLAUDE_PLAN", raising=False)
    sleeps = []
    monkeypatch.setattr(claude_cli, "_sleep", lambda s: sleeps.append(s))

    def plan(steps):
        p = tmp_path / "plan.json"
        p.write_text(json.dumps(steps), encoding="utf-8")
        monkeypatch.setenv("STUB_CLAUDE_PLAN", str(p))

    def calls():
        f = state / "calls.jsonl"
        return [json.loads(l) for l in f.read_text().splitlines()] if f.exists() else []

    def config(**kw):
        _write_agents(base, **kw)

    return SimpleNamespace(base=base, tmp=tmp_path, plan=plan, calls=calls, config=config,
                           sleeps=sleeps, post=base / "forum" / "091_critic.md")


def _flag(argv, name):
    i = argv.index(name)
    return argv[i + 1]


# ---------------------------------------------------------------- parsing

def test_parse_jsonl_fixture():
    p = claude_cli.parse_events(FIX / "events_success.jsonl")
    assert p["init"]["model"] == "claude-opus-5-5"
    assert p["init"]["claude_code_version"] == "2.1.282"
    assert p["result"]["num_turns"] == 3
    assert p["result"]["terminal_reason"] == "completed"
    assert list(p["result"]["modelUsage"]) == ["claude-opus-5-5"]
    assert p["result"]["structured_output"] == {"verdict": "revise", "falsifier_tested": "no"}
    assert p["rate_limit"]["rate_limit_info"]["status"] == "allowed"


def test_parse_verbose_array_fixture():
    p = claude_cli.parse_events(FIX / "events_verbose_array.json")
    assert p["init"]["model"] == "claude-opus-5-5"
    assert p["result"]["num_turns"] == 7
    assert list(p["result"]["modelUsage"]) == ["claude-opus-5-5"]
    assert p["n_assistant"] == 1


def test_parse_truncated_stream_and_array(tmp_path):
    lines = (FIX / "events_success.jsonl").read_text().splitlines()
    f = tmp_path / "partial.jsonl"
    f.write_text(lines[0] + "\n" + lines[1] + "\n" + lines[2][: len(lines[2]) // 2])
    p = claude_cli.parse_events(f)
    assert p["init"] is not None and p["result"] is None and p["parse_errors"] == 1
    arr = (FIX / "events_verbose_array.json").read_text()
    g = tmp_path / "partial.json"
    g.write_text(arr[: int(len(arr) * 0.6)])
    q = claude_cli.parse_events(g)
    assert q["init"] is not None and q["result"] is None


def test_parse_api_retries():
    p = claude_cli.parse_events(FIX / "events_overloaded.jsonl")
    assert len(p["api_retries"]) == 2
    assert p["api_retries"][-1]["error_status"] == 529


# ---------------------------------------------------------------- classify

def _classify_fixture(name, post_exists=False, timed_out=False, mutate=None):
    p = claude_cli.parse_events(FIX / name)
    events = p["events"]
    if mutate:
        mutate(events)
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    return claude_cli.classify(result, events, post_exists=post_exists, timed_out=timed_out)


def test_classify_usage_limit_from_text(monkeypatch):
    monkeypatch.setattr(claude_cli, "_now", lambda: datetime(2026, 9, 25, 9, 0, tzinfo=NY))
    cls, resume_at = _classify_fixture("events_usage_limit.jsonl")
    assert cls == "usage_limit"
    assert resume_at == "2026-09-25T11:50:00-04:00"
    monkeypatch.setattr(claude_cli, "_now", lambda: datetime(2026, 9, 25, 13, 0, tzinfo=NY))
    assert _classify_fixture("events_usage_limit.jsonl")[1] == "2026-09-26T11:50:00-04:00"


def test_classify_usage_limit_prefers_resets_at():
    def add_reset(events):
        for e in events:
            if e.get("type") == "rate_limit_event":
                e["rate_limit_info"]["resetsAt"] = 1790350200
    cls, resume_at = _classify_fixture("events_usage_limit.jsonl", mutate=add_reset)
    assert cls == "usage_limit"
    assert datetime.fromisoformat(resume_at).timestamp() == 1790350200


def test_classify_usage_limit_even_if_post_exists():
    assert _classify_fixture("events_usage_limit.jsonl", post_exists=True)[0] == "usage_limit"


def test_reset_text_with_date(monkeypatch):
    now = datetime(2026, 9, 25, 9, 0, tzinfo=NY)
    assert claude_cli._parse_reset_text(
        "You've hit your weekly limit · resets Oct 2, 9am (America/New_York)", now) \
        == "2026-10-02T09:00:00-04:00"
    iso = claude_cli._parse_reset_text("Claude AI usage limit reached|1790350200", now)
    assert datetime.fromisoformat(iso).timestamp() == 1790350200


@pytest.mark.parametrize("name,expected", [
    ("events_overloaded.jsonl", "overloaded"),
    ("events_server_error.jsonl", "server_error"),
    ("events_max_turns.jsonl", "max_turns"),
])
def test_classify_error_fixtures(name, expected):
    assert _classify_fixture(name) == (expected, None)


def test_classify_ok_no_post_timeout():
    assert _classify_fixture("events_success.jsonl", post_exists=True) == ("ok", None)
    assert _classify_fixture("events_success.jsonl", post_exists=False) == ("no_post", None)
    init = claude_cli.parse_events(FIX / "events_success.jsonl")["events"][:2]
    assert claude_cli.classify(None, init, post_exists=False, timed_out=True) == ("timeout", None)


def test_classify_auth_and_config():
    ev = [{"type": "_wrapper_stderr", "text": "error: unknown option '--bogus-flag'"}]
    assert claude_cli.classify(None, ev, post_exists=False, timed_out=False)[0] == "auth_or_config"
    res = {"type": "result", "subtype": "success", "is_error": True,
           "result": "Invalid API key · Please run /login", "api_error_status": 401}
    assert claude_cli.classify(res, [res], post_exists=False, timed_out=False)[0] == "auth_or_config"
    assert claude_cli.classify(None, [], post_exists=False, timed_out=False)[0] == "unknown"


def test_classify_ignores_agent_prose():
    """Numbers and words in the model's own text never set a class."""
    prose = {"type": "assistant", "message": {"model": "claude-opus-5-5", "content": [
        {"type": "text", "text": "500 members were overloaded; the session limit on debate is 529 minutes."}]}}
    ok = {"type": "result", "subtype": "success", "is_error": False, "result": "Posted."}
    assert claude_cli.classify(ok, [prose, ok], post_exists=False, timed_out=False)[0] == "no_post"
    err = {"type": "result", "subtype": "error_during_execution", "is_error": True, "result": ""}
    assert claude_cli.classify(err, [prose, err], post_exists=False, timed_out=False)[0] == "unknown"


# ---------------------------------------------------------------- guard and config

def test_live_call_blocked_under_pytest(repo, monkeypatch):
    monkeypatch.delenv("KNA_CLAUDE_BIN")
    spawned = []
    monkeypatch.setattr(claude_cli.subprocess, "Popen", lambda *a, **k: spawned.append(a))
    monkeypatch.setattr(claude_cli.subprocess, "run", lambda *a, **k: spawned.append(a))
    with pytest.raises(claude_cli.LiveCallBlocked):
        claude_cli.run_claude("summary", "p")
    assert claude_cli.cli_version() is None
    assert spawned == []


def test_refuses_without_pinned_model(repo):
    repo.config(model=None)
    with pytest.raises(claude_cli.ClaudeCLIError, match="forum_config.model"):
        claude_cli.run_claude("summary", "p")
    repo.config(model="opus")
    with pytest.raises(claude_cli.ClaudeCLIError, match="full model id"):
        claude_cli.run_claude("summary", "p")
    assert repo.calls() == []


def test_refuses_unknown_task(repo):
    with pytest.raises(claude_cli.ClaudeCLIError, match="unknown task"):
        claude_cli.run_claude("no_such_task", "p")
    with pytest.raises(claude_cli.ClaudeCLIError, match="no agent"):
        claude_cli.run_claude("agent", "p", role="ghost")


def test_cli_version_from_stub(repo):
    claude_cli._VERSION_CACHE.clear()
    assert claude_cli.cli_version() == "2.1.282"


# ---------------------------------------------------------------- command and isolation

def test_agent_command_flags_and_env(repo, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-should-not-pass")
    monkeypatch.setenv("CLAUDE_CODE_EFFORT_LEVEL", "max")
    repo.plan([{"write": [[str(repo.post), "---\nauthor: Critic\n---\n# Post\n"]]}])
    res = claude_cli.run_claude("agent", "You are Critic.", role="critic", expect_file=repo.post,
                                round_num=31, arc_id="arc6", user_message="Write your post now.")
    assert res.ok and res.failure == "ok" and res.attempts == 1
    call = repo.calls()[0]
    argv = call["argv"]
    assert argv[0] == "-p"
    assert _flag(argv, "--model") == "claude-opus-5-5"
    assert _flag(argv, "--output-format") == "stream-json" and "--verbose" in argv
    assert _flag(argv, "--tools") == "Bash,Read,Write"
    assert _flag(argv, "--allowedTools") == "Bash,Read,Write"
    assert _flag(argv, "--disallowedTools") == "mcp__*"
    assert "--strict-mcp-config" in argv
    assert _flag(argv, "--setting-sources") == "project"
    assert "--dangerously-skip-permissions" in argv
    assert _flag(argv, "--max-turns") == "150"
    sid = _flag(argv, "--session-id")
    assert len(sid) == 36 and "--resume" not in argv
    # --effort right before the message, so no variadic flag can swallow it
    assert argv[-3:] == ["--effort", "high", "Write your post now."]
    prompt = Path(_flag(argv, "--system-prompt-file"))
    assert prompt.parent == repo.base / "logs" / "prompts" and prompt.name == f"{res.run_id}.md"
    assert "workspace" not in prompt.parts
    assert call["cwd"] == str((repo.base / "workspace").resolve())
    assert call["env"]["CLAUDE_CODE_DISABLE_CLAUDE_MDS"] == "1"
    assert call["env"]["ANTHROPIC_API_KEY"] is None
    assert call["env"]["CLAUDE_CODE_EFFORT_LEVEL"] is None
    assert call["env"]["KNA_RUN_ID"] == res.run_id


def test_helper_task_has_no_tools_by_default(repo):
    res = claude_cli.run_claude("summary", "Summarize.")
    argv = repo.calls()[0]["argv"]
    assert _flag(argv, "--tools") == "" and "--allowedTools" not in argv
    assert argv[-3:-1] == ["--effort", "low"]
    assert "--max-turns" not in argv
    assert res.ok and res.sidecar_path.parent.name == "no_round"


def test_tools_by_task_from_config(repo):
    repo.config(tools_by_task={"draft_body": ["Read", "Write", "Edit"], "summary": []})
    claude_cli.run_claude("draft_body", "p")
    claude_cli.run_claude("summary", "p")
    claude_cli.run_claude("draft_body", "p", tools=["Read"])
    argvs = [c["argv"] for c in repo.calls()]
    assert _flag(argvs[0], "--tools") == "Read,Write,Edit" and _flag(argvs[0], "--allowedTools") == "Read,Write,Edit"
    assert _flag(argvs[1], "--tools") == "" and "--allowedTools" not in argvs[1]
    assert _flag(argvs[2], "--tools") == "Read"


def test_effort_override_and_explicit_tools(repo):
    claude_cli.run_claude("agent", "p", role="literature_scout", effort="low", tools=["Read"])
    argv = repo.calls()[0]["argv"]
    assert _flag(argv, "--effort") == "low" and _flag(argv, "--tools") == "Read"


def test_extra_env_cannot_disable_isolation(repo):
    claude_cli.run_claude("summary", "p", extra_env={"CLAUDE_CODE_DISABLE_CLAUDE_MDS": "0",
                                                     "KNA_STAGING_DIR": "/tmp/x"})
    env = repo.calls()[0]["env"]
    assert env["CLAUDE_CODE_DISABLE_CLAUDE_MDS"] == "1" and env["KNA_STAGING_DIR"] == "/tmp/x"


def test_common_rules_and_prompt_manifest(repo):
    repo.config(common_rules=["Write only inside the forum repository.", "You are running unattended."])
    block = claude_cli.manifest_block("forum_state", "posts text", source=repo.base / "agents.json")
    res = claude_cli.run_claude("agent", "Base prompt.", role="critic", prompt_manifest=[block])
    text = (repo.base / "logs" / "prompts" / f"{res.run_id}.md").read_text()
    assert text.startswith("Base prompt.")
    assert "## Common Rules" in text and "- You are running unattended." in text
    side = json.loads(res.sidecar_path.read_text())
    labels = [b["label"] for b in side["prompt_manifest"]["blocks"]]
    assert labels == ["forum_state", "common_rules"]
    assert side["prompt_manifest"]["blocks"][0]["mtime"]
    assert len(side["prompt_manifest"]["sha256"]) == 64


def test_common_rules_only_for_agents_and_canary(repo):
    """E2E-11: the post and repository rules conflict with the helper tasks'
    own formats (a summary must not grow a References section)."""
    repo.config(common_rules=["End with a References section that gives each DOI."])
    for task in ("summary", "draft_body", "slate"):
        res = claude_cli.run_claude(task, "Base prompt.", effort="low")
        text = (repo.base / "logs" / "prompts" / f"{res.run_id}.md").read_text()
        assert "## Common Rules" not in text and "References section" not in text, task
        labels = [b["label"] for b in json.loads(res.sidecar_path.read_text())["prompt_manifest"]["blocks"]]
        assert "common_rules" not in labels
    res = claude_cli.run_claude("canary", "Base prompt.", role="critic")
    assert "## Common Rules" in (repo.base / "logs" / "prompts" / f"{res.run_id}.md").read_text()


# ---------------------------------------------------------------- sidecar and transcript

def test_sidecar_and_transcript_archive(repo):
    repo.plan([{"write": [[str(repo.post), "post"]], "structured": {"verdict": "pursue"}}])
    res = claude_cli.run_claude("agent", "p", role="critic", expect_file=repo.post, round_num=31,
                                arc_id="arc6", schema={"type": "object"})
    assert res.structured == {"verdict": "pursue"}
    assert res.model == "claude-opus-5-5" and res.models_used == ["claude-opus-5-5"]
    assert res.cli_version == "2.1.282" and res.num_turns == 3
    assert res.terminal_reason == "completed" and res.text == "Done."
    assert res.sidecar_path == repo.base / "logs" / "r31" / f"{res.run_id}.sidecar.json"
    side = json.loads(res.sidecar_path.read_text())
    assert side["requested_model"] == "claude-opus-5-5" and side["effort"] == "high"
    a = side["attempts"][0]
    assert a["init"]["tools"] == ["Bash", "Read", "Write"]
    assert a["init"]["mcp_servers"] == [] and a["init"]["permissionMode"] == "bypassPermissions"
    assert a["result"]["models"] == ["claude-opus-5-5"] and a["result"]["total_cost_usd"]
    assert a["rate_limit_info"]["unifiedWindows"]["five_hour"]["utilization"] == 0.12
    assert side["failure"] == "ok" and side["structured_output"] == {"verdict": "pursue"}
    archive = repo.base / "logs" / "transcripts" / "arc6" / f"{res.run_id}_a1.jsonl.gz"
    assert archive.exists() and a["transcript_archive"] == str(archive)
    with gzip.open(archive, "rt") as f:
        n_assistant = sum(1 for l in f if json.loads(l).get("type") == "assistant")
    assert n_assistant >= a["n_assistant"] >= 1
    assert res.events_paths == [repo.base / "logs" / "r31" / f"{res.run_id}_a1.events.jsonl"]


def test_run_id_from_staging_env_is_single_use(repo):
    res = claude_cli.run_claude("summary", "p", extra_env={"KNA_RUN_ID": "r31_critic_fixed"})
    assert res.run_id == "r31_critic_fixed"
    assert res.sidecar_path.name == "r31_critic_fixed.sidecar.json"
    with pytest.raises(claude_cli.ClaudeCLIError, match="single-use"):
        claude_cli.run_claude("summary", "p", extra_env={"KNA_RUN_ID": "r31_critic_fixed"})


def test_verbose_array_output_is_parsed(repo):
    repo.plan([{"format": "array", "num_turns": 9}])
    res = claude_cli.run_claude("summary", "p")
    assert res.ok and res.num_turns == 9


# ---------------------------------------------------------------- failure policy

def test_usage_limit_never_retries(repo, monkeypatch):
    monkeypatch.setattr(claude_cli, "_now", lambda: datetime(2026, 9, 25, 9, 0, tzinfo=NY))
    repo.plan([{"mode": "usage_limit"}])
    res = claude_cli.run_claude("agent", "p", role="data_analyst", expect_file=repo.post, round_num=31)
    assert res.failure == "usage_limit" and not res.ok
    assert res.resume_at == "2026-09-25T11:50:00-04:00"
    assert res.attempts == 1 and len(repo.calls()) == 1 and repo.sleeps == []
    alerts = (repo.base / "logs" / "alerts.log").read_text().splitlines()
    assert len(alerts) == 1 and "usage_limit" in alerts[0] and "11:50" in alerts[0]
    side = json.loads(res.sidecar_path.read_text())
    assert side["attempts"][0]["usage_limit_kind"] == "session"
    assert claude_cli.EXIT_USAGE_LIMIT == 75


def test_continuation_resumes_same_session_once(repo):
    repo.plan([{"mode": "ok"}, {"write": [[str(repo.post), "post"]]}])
    res = claude_cli.run_claude("agent", "p", role="critic", expect_file=repo.post, round_num=31)
    assert res.ok and res.attempts == 2
    first, second = [c["argv"] for c in repo.calls()]
    sid = _flag(first, "--session-id")
    assert _flag(second, "--resume") == sid and "--session-id" not in second
    assert second[-1] == claude_cli.CONTINUATION_MESSAGE.format(path=repo.post)
    assert repo.calls()[0]["cwd"] == repo.calls()[1]["cwd"]
    assert _flag(second, "--model") == "claude-opus-5-5" and _flag(second, "--effort") == "high"
    assert len(res.events_paths) == 2 and all(p.exists() for p in res.events_paths)
    assert res.events_paths[0] != res.events_paths[1]
    side = json.loads(res.sidecar_path.read_text())
    assert [a["kind"] for a in side["attempts"]] == ["initial", "continuation"]
    assert [a["class"] for a in side["attempts"]] == ["no_post", "ok"]
    assert res.num_turns == 6


def test_two_continuations_then_no_post(repo):
    repo.plan([{"mode": "ok"}])
    res = claude_cli.run_claude("agent", "p", role="critic", expect_file=repo.post, round_num=31)
    assert res.failure == "no_post" and res.attempts == 3 and len(repo.calls()) == 3
    assert len((repo.base / "logs" / "alerts.log").read_text().splitlines()) == 1


def test_max_turns_goes_to_continuation(repo):
    repo.plan([{"mode": "max_turns"}, {"write": [[str(repo.post), "post"]]}])
    res = claude_cli.run_claude("agent", "p", role="data_analyst", expect_file=repo.post)
    assert res.ok and res.attempts == 2
    assert _flag(repo.calls()[0]["argv"], "--max-turns") == "250"


def test_overloaded_waits_and_resumes_at_most_twice(repo):
    repo.plan([{"mode": "overloaded"}])
    res = claude_cli.run_claude("agent", "p", role="critic", expect_file=repo.post)
    assert res.failure == "overloaded" and res.attempts == 3
    assert repo.sleeps == [600, 600]
    side = json.loads(res.sidecar_path.read_text())
    assert [w["reason"] for w in side["waits"]] == ["overloaded", "overloaded"]
    assert "--resume" in repo.calls()[1]["argv"]


def test_overloaded_then_success(repo):
    repo.plan([{"mode": "overloaded"}, {"write": [[str(repo.post), "post"]]}])
    res = claude_cli.run_claude("agent", "p", role="critic", expect_file=repo.post)
    assert res.ok and res.attempts == 2 and repo.sleeps == [600]


def test_overloaded_and_server_error_resume_with_the_resume_message(repo):
    """E2E-08: an interrupted run continues its task. It is not told to write
    the post from what it has done so far."""
    repo.plan([{"mode": "overloaded"}, {"mode": "server_error"},
               {"write": [[str(repo.post), "post"]]}])
    res = claude_cli.run_claude("agent", "p", role="data_analyst", expect_file=repo.post)
    assert res.ok and res.attempts == 3
    second, third = repo.calls()[1]["argv"], repo.calls()[2]["argv"]
    assert second[-1] == claude_cli.RESUME_MESSAGE.format(reason="overloaded")
    assert third[-1] == claude_cli.RESUME_MESSAGE.format(reason="server error")
    assert all("does not exist yet" not in c["argv"][-1] for c in repo.calls())


def test_no_post_still_gets_the_continuation_message(repo):
    repo.plan([{"mode": "max_turns"}, {"write": [[str(repo.post), "post"]]}])
    claude_cli.run_claude("agent", "p", role="data_analyst", expect_file=repo.post)
    assert repo.calls()[1]["argv"][-1] == claude_cli.CONTINUATION_MESSAGE.format(path=repo.post)


def test_structured_output_from_an_earlier_attempt_is_kept(repo):
    """F3: the Critic returns its verdict, then the continuation writes the
    post and ends without structured_output. The verdict is not lost."""
    repo.plan([{"structured": {"verdict": "revise"}}, {"write": [[str(repo.post), "post"]]}])
    res = claude_cli.run_claude("agent", "p", role="critic", expect_file=repo.post,
                                schema={"type": "object"})
    assert res.ok and res.attempts == 2
    assert res.structured == {"verdict": "revise"}
    side = json.loads(res.sidecar_path.read_text())
    assert side["structured_output"] == {"verdict": "revise"} and side["structured_missing"] is False


def test_server_error_resumes_once(repo):
    repo.plan([{"mode": "server_error"}])
    res = claude_cli.run_claude("agent", "p", role="critic", expect_file=repo.post)
    assert res.failure == "server_error" and res.attempts == 2 and repo.sleeps == [120]


def test_auth_and_bad_flag_stop_at_once(repo):
    repo.plan([{"mode": "auth"}])
    res = claude_cli.run_claude("summary", "p")
    assert res.failure == "auth_or_config" and res.attempts == 1
    repo.plan([{"mode": "bad_flag"}])
    res = claude_cli.run_claude("summary", "p")
    assert res.failure == "auth_or_config" and res.attempts == 1


def test_timeout_keeps_partial_stream(repo):
    import time
    repo.plan([{"mode": "hang", "sleep": 30}])
    t0 = time.time()
    res = claude_cli.run_claude("agent", "p", role="critic", expect_file=repo.post, timeout_s=1,
                                max_continuations=0)
    assert time.time() - t0 < 20
    assert res.failure == "timeout" and res.terminal_reason == "timeout"
    parsed = claude_cli.parse_events(res.events_paths[0])
    assert parsed["init"] is not None and parsed["n_assistant"] == 1
    side = json.loads(res.sidecar_path.read_text())
    assert side["attempts"][0]["timed_out"] is True


def test_max_calls_per_arc(repo):
    repo.config(max_calls_per_arc=3)
    repo.plan([{"mode": "ok"}])
    # a stalled run spends 3 calls (1 + 2 continuations) and uses up the budget
    res = claude_cli.run_claude("agent", "p", role="critic", expect_file=repo.post, arc_id="arcT")
    assert res.failure == "no_post" and claude_cli.count_calls_in_arc("arcT") == 3
    res = claude_cli.run_claude("summary", "p", arc_id="arcT")
    assert res.failure == "auth_or_config" and res.terminal_reason == "max_calls_per_arc"
    assert res.attempts == 0 and len(repo.calls()) == 3
    # other arcs and arc-less calls are not capped
    assert claude_cli.run_claude("summary", "p", arc_id="arcU").ok
    assert claude_cli.run_claude("summary", "p").ok


def test_launch_gate_only_when_configured(repo):
    repo.plan([{"mode": "ok", "utilization": 0.9}])
    assert claude_cli.run_claude("summary", "p").ok
    assert claude_cli.run_claude("summary", "p").ok          # gate off by default
    n = len(repo.calls())
    repo.config(failure_policy={"launch_gate": {"five_hour": 0.85, "seven_day": 0.9}})
    res = claude_cli.run_claude("summary", "p")
    assert res.failure == "usage_limit" and res.terminal_reason == "launch_gate"
    assert res.resume_at and len(repo.calls()) == n
    # A Critic call (schema requested) refused by the gate returns the same
    # class. The F3 fix once read its structured-output memo before setting it.
    res = claude_cli.run_claude("agent", "p", role="critic", expect_file=repo.post, schema={"type": "object"})
    assert res.failure == "usage_limit" and res.structured is None and len(repo.calls()) == n


def test_notify_writes_alert_and_never_raises(repo, monkeypatch):
    claude_cli.notify("KNA forum: test", "line one\nline two")
    lines = (repo.base / "logs" / "alerts.log").read_text().splitlines()
    assert lines[-1].endswith("KNA forum: test\tline one line two")
    blocker = repo.tmp / "not_a_dir"
    blocker.write_text("x")
    monkeypatch.setattr(claude_cli, "BASE_DIR", blocker)
    claude_cli.notify("t", "m")  # logs dir cannot be created: still no exception


def test_step2_permission_mode_is_opt_in(repo):
    repo.config(permission_mode="dontAsk")
    res = claude_cli.run_claude("agent", "p", role="critic", expect_file=repo.post,
                                extra_env={"KNA_STAGING_DIR": str(repo.base / "knowledge" / "staging" / "x")})
    argv = repo.calls()[0]["argv"]
    assert "--dangerously-skip-permissions" not in argv
    assert _flag(argv, "--permission-mode") == "dontAsk"
    settings = Path(_flag(argv, "--settings"))
    assert settings.parent == repo.base / "workspace"
    s = json.loads(settings.read_text())
    assert s["sandbox"]["enabled"] and s["sandbox"]["failIfUnavailable"]
    assert s["sandbox"]["allowUnsandboxedCommands"] is False
    assert "api.openalex.org" in s["sandbox"]["network"]["allowedDomains"]
    assert "Read(~/.ssh/**)" in s["permissions"]["deny"]
    assert any(str(repo.post.resolve()).lstrip("/") in a for a in s["permissions"]["allow"])
    assert res.failure == "no_post"


def test_shell_entry_point(repo, capsys, monkeypatch):
    repo.plan([{"result_text": "요약 문장"}])
    assert claude_cli.main(["run", "--task", "agora", "--tools", "Read", "--message", "hi"]) == 0
    assert "요약 문장" in capsys.readouterr().out
    argv = repo.calls()[-1]["argv"]
    assert _flag(argv, "--tools") == "Read" and argv[-1] == "hi"
    monkeypatch.setattr(claude_cli, "_now", lambda: datetime(2026, 9, 25, 9, 0, tzinfo=NY))
    repo.plan([{"mode": "usage_limit"}])
    assert claude_cli.main(["run", "--task", "agora", "--message", "hi"]) == claude_cli.EXIT_USAGE_LIMIT

"""forum_preflight (M02, M03): the canary runs only on a configuration or CLI
change, checks isolation deterministically from the sidecar and the
archived transcript, and refuses the denial probes in bypass mode. Every
call uses the stub binary; the canary is never run live here."""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import claude_cli  # noqa: E402
import forum_preflight as fp  # noqa: E402

STUB = ROOT / "tests" / "fixtures" / "cli" / "stub_claude.py"
SENTINEL = "Sentinel rule line that only exists in the private instructions file for this test"


@pytest.fixture
def repo(tmp_path, monkeypatch):
    base = tmp_path / "repo"
    (base / "workspace").mkdir(parents=True)
    agents = {
        "season": 2,
        "forum_config": {"model": "claude-opus-5-5", "effort_by_task": {"canary": "low"}},
        "agents": [
            {"id": "literature_scout", "name": "S", "prompt": "s", "effort": "medium",
             "allowed_tools": ["Bash", "Read", "Write"]},
            {"id": "data_analyst", "name": "A", "prompt": "a", "effort": "high",
             "allowed_tools": ["Bash", "Read", "Write", "Glob", "Grep"]},
            {"id": "critic", "name": "C", "prompt": "c", "effort": "high",
             "allowed_tools": ["Bash", "Read", "Write"]},
        ],
    }
    (base / "agents.json").write_text(json.dumps(agents))
    cfg_dir = tmp_path / "claude_config"
    cfg_dir.mkdir()
    (cfg_dir / "CLAUDE.md").write_text(f"# Global\n\n- {SENTINEL}\n")
    monkeypatch.setattr(claude_cli, "BASE_DIR", base)
    monkeypatch.setattr(fp, "BASE_DIR", base)
    monkeypatch.setenv("KNA_CLAUDE_BIN", str(STUB))
    monkeypatch.setenv("STUB_CLAUDE_STATE", str(tmp_path / "stub_state"))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(cfg_dir))
    monkeypatch.setenv("KNA_NO_SLEEP", "1")
    claude_cli._VERSION_CACHE.clear()

    def plan(steps):
        p = tmp_path / "plan.json"
        p.write_text(json.dumps(steps))
        monkeypatch.setenv("STUB_CLAUDE_PLAN", str(p))

    return type("R", (), {"base": base, "plan": staticmethod(plan), "agents": agents, "tmp": tmp_path})


WRITE_POST = {"write_from_prompt": r"POST FILE: (\S+)"}


def test_canary_passes_and_records(repo):
    repo.plan([WRITE_POST])
    report = fp.run_canary()
    assert report["passed"], report
    assert [r["role"] for r in report["roles"]] == ["literature_scout", "data_analyst", "critic"]
    assert report["init_tools"]["data_analyst"] == ["Bash", "Read", "Write", "Glob", "Grep"]
    ids = {c["id"] for c in report["roles"][0]["checks"]}
    assert {"model_pinned", "tools_within_role", "no_skill_tool", "no_mcp_servers", "permission_mode",
            "no_claude_md_in_transcript", "transcript_complete", "own_post_written"} <= ids
    last = json.loads((repo.base / "logs" / "preflight" / "last.json").read_text())
    assert last["passed"] and last["fingerprint"]["cli_version"] == "2.1.282"
    # the sentinel text itself is never written to a record
    assert SENTINEL not in json.dumps(last)
    # canary calls are low effort and use each role's tool list
    calls = [json.loads(l) for l in (repo.tmp / "stub_state" / "calls.jsonl").read_text().splitlines()]
    assert all(c["argv"][c["argv"].index("--effort") + 1] == "low" for c in calls)
    assert calls[1]["argv"][calls[1]["argv"].index("--tools") + 1] == "Bash,Read,Write,Glob,Grep"


def test_needs_canary_only_on_change(repo, monkeypatch):
    needed, reasons = fp.needs_canary()
    assert needed and reasons == ["no canary recorded"]
    repo.plan([WRITE_POST])
    fp.run_canary()
    assert fp.needs_canary() == (False, [])
    agents = dict(repo.agents)
    agents["forum_config"] = {**agents["forum_config"], "max_calls_per_arc": 30}
    (repo.base / "agents.json").write_text(json.dumps(agents))
    assert fp.needs_canary() == (True, ["agents.json changed"])
    (repo.base / "agents.json").write_text(json.dumps(repo.agents))
    monkeypatch.setattr(claude_cli, "cli_version", lambda: "2.1.300")
    assert fp.needs_canary() == (True, ["CLI version changed"])


def test_claude_md_leak_is_caught_from_transcript(repo):
    repo.plan([{**WRITE_POST, "transcript_extra": f"Contents of CLAUDE.md:\n- {SENTINEL}\n"}])
    report = fp.run_canary(roles=["critic"])
    assert not report["passed"]
    check = next(c for c in report["roles"][0]["checks"] if c["id"] == "no_claude_md_in_transcript")
    assert not check["passed"] and check["detail"].startswith("1 of")
    assert not (repo.base / "logs" / "preflight" / "last.json").exists()
    assert "preflight failed" in (repo.base / "logs" / "alerts.log").read_text()


def test_extra_tool_and_tool_drift_fail(repo):
    repo.plan([{**WRITE_POST, "init_tools": ["Bash", "Read", "Write", "WebFetch", "Skill"]}])
    report = fp.run_canary(roles=["critic"])
    failed = {c["id"] for c in report["roles"][0]["checks"] if not c["passed"]}
    assert {"tools_within_role", "no_skill_tool"} <= failed


def test_missing_post_fails(repo):
    repo.plan([{}])
    report = fp.run_canary(roles=["literature_scout"])
    failed = {c["id"] for c in report["roles"][0]["checks"] if not c["passed"]}
    assert {"call_ok", "own_post_written"} <= failed


def test_step2_refused_in_bypass_mode(repo):
    with pytest.raises(SystemExit, match="dontAsk"):
        fp.run_canary(step2=True)
    assert not (repo.tmp / "stub_state" / "calls.jsonl").exists()


def test_canary_is_never_live_under_pytest(repo, monkeypatch):
    monkeypatch.delenv("KNA_CLAUDE_BIN")
    with pytest.raises(claude_cli.LiveCallBlocked):
        fp.run_canary(roles=["critic"])


def test_status_entry_point_makes_no_call(repo, capsys):
    assert fp.main(["--status"]) == 0
    assert "canary needed" in capsys.readouterr().out
    assert not (repo.tmp / "stub_state" / "calls.jsonl").exists()


def test_template_fingerprint_tracks_permission_mode(repo):
    a = fp.template_fingerprint({"permission_mode": "bypass"})
    b = fp.template_fingerprint({"permission_mode": "dontAsk"})
    assert a != b and len(a) == 64

#!/usr/bin/env python3
"""
Forum preflight canary (v2.1, M02 and M03)
==========================================
One tiny low-effort call per role that checks, deterministically and not by
the model's self-report, that forum agents run the way the wrapper intends:

  step 1 (Stage 1, bypass mode):
    - init.model equals the pinned forum_config.model
    - init.tools holds no tool outside the role's list, and no Skill
    - no MCP servers, permissionMode recorded
    - the archived transcript contains no line from any CLAUDE.md file the
      CLI could have loaded (a sentinel check on the transcript itself)
    - the archived transcript has at least as many assistant messages as
      the events file
    - the role's post path can be written
  step 2 (only when forum_config.permission_mode is 'dontAsk'):
    - a write into a scratch sibling git repo is denied
    - a write to ~/Desktop is denied
    - a curl to example.com is denied, one to api.openalex.org succeeds

The canary runs only when the agents.json hash, the CLI version or the
wrapper's isolation template changed since the last recorded canary
(needs_canary). It is NOT run automatically in Stage 1.

Usage:
    python3 forum_preflight.py --status            # fingerprint vs last canary, no Claude call
    python3 forum_preflight.py --run               # live: one low-effort call per role
    python3 forum_preflight.py --run --step2       # adds the denial probes (dontAsk only)

Records go to logs/preflight/ (private).
"""

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import claude_cli

BASE_DIR = Path(__file__).resolve().parent

CANARY_SCHEMA = {
    "type": "object",
    "properties": {
        "probes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "succeeded": {"type": "boolean"},
                    "detail": {"type": "string"},
                },
                "required": ["id", "succeeded"],
            },
        },
    },
    "required": ["probes"],
}
MIN_SENTINEL_CHARS = 40


def _preflight_dir() -> Path:
    return BASE_DIR / "logs" / "preflight"


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def template_fingerprint(cfg: dict | None = None) -> str:
    """Hash of everything that shapes an agent's environment besides
    agents.json: the wrapper's isolation env and flags, the permission mode
    and the step 2 settings defaults."""
    cfg = cfg if cfg is not None else claude_cli.load_forum_config()
    template = {
        "isolation_env": claude_cli.ISOLATION_ENV,
        "stripped_env": list(claude_cli.STRIPPED_ENV),
        "isolation_flags": claude_cli.ISOLATION_FLAGS,
        "permission_mode": cfg.get("permission_mode", "bypass"),
        "step2_domains": claude_cli.STEP2_DEFAULT_DOMAINS,
        "step2_deny_read": claude_cli.STEP2_DEFAULT_DENY_READ,
    }
    return _sha256_bytes(json.dumps(template, sort_keys=True).encode())


def fingerprint() -> dict:
    agents = BASE_DIR / "agents.json"
    return {
        "agents_sha256": _sha256_bytes(agents.read_bytes()) if agents.exists() else None,
        "cli_version": claude_cli.cli_version(),
        "template_sha256": template_fingerprint(),
    }


def last_record() -> dict | None:
    p = _preflight_dir() / "last.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def needs_canary(fp: dict | None = None) -> tuple[bool, list[str]]:
    """(needed, reasons). Needed when no passing canary is recorded or any
    fingerprint part changed since the last one."""
    fp = fp or fingerprint()
    last = last_record()
    if not last:
        return True, ["no canary recorded"]
    reasons = []
    if not last.get("passed"):
        reasons.append("last canary did not pass")
    prev = last.get("fingerprint") or {}
    for key, label in (("agents_sha256", "agents.json changed"), ("cli_version", "CLI version changed"),
                       ("template_sha256", "isolation template changed")):
        if prev.get(key) != fp.get(key):
            reasons.append(label)
    return bool(reasons), reasons


def claude_md_files(cwd: Path) -> list[Path]:
    """CLAUDE.md files the CLI could load for a session in cwd: the user one
    and those in cwd and its ancestors."""
    out = []
    user = claude_cli._config_dir() / "CLAUDE.md"
    if user.exists():
        out.append(user)
    for d in [Path(cwd).resolve(), *Path(cwd).resolve().parents]:
        for name in ("CLAUDE.md", "CLAUDE.local.md"):
            p = d / name
            if p.exists() and p not in out:
                out.append(p)
    return out


def sentinel_lines(paths: list[Path], per_file: int = 8) -> list[str]:
    """Distinctive lines (long, not markup only) from each file. They are
    compared in memory and never written to any record."""
    lines = []
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        picked = 0
        for ln in text.splitlines():
            s = ln.strip().lstrip("-*#>|").strip()
            if len(s) >= MIN_SENTINEL_CHARS and not s.startswith(("```", "http")):
                lines.append(s)
                picked += 1
                if picked >= per_file:
                    break
    return lines


def _read_gz(path: Path) -> str:
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        return f.read()


def _assistant_messages_in_transcript(text: str) -> int:
    n = 0
    for line in text.splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(e, dict) and e.get("type") == "assistant":
            n += 1
    return n


def canary_prompt(role: str, post_path: Path, probes: dict | None) -> str:
    lines = [
        f"# Forum preflight canary ({role})",
        "",
        "This is a configuration check, not research. Keep it short and use as few tool calls as possible.",
        "",
        "Steps:",
        f"1. Write a file with the single line `canary ok` to the post path below.",
    ]
    step = 2
    for pid, instruction in (probes or {}).items():
        lines.append(f"{step}. ({pid}) {instruction}")
        step += 1
    lines += [
        "",
        "Do not retry a step that is denied. Record each step as a probe with succeeded true or false.",
        "",
        f"POST FILE: {post_path}",
    ]
    return "\n".join(lines) + "\n"


def step2_probes(run_dir: Path, sibling_repo: Path, desktop_file: Path) -> dict:
    return {
        "sibling_write": f"Run `echo canary > {sibling_repo}/CANARY.txt` with Bash.",
        "desktop_write": f"Run `echo canary > {desktop_file}` with Bash.",
        "example_curl": f"Run `curl -s -m 15 https://example.com -o {run_dir}/example.html` with Bash.",
        "openalex_curl": f"Run `curl -s -m 20 'https://api.openalex.org/works?per-page=1' -o {run_dir}/openalex.json` with Bash.",
    }


def _check(checks: list, cid: str, passed: bool, detail: str = "") -> None:
    checks.append({"id": cid, "passed": bool(passed), "detail": detail})


def evaluate(role: str, result, expected_tools: list[str], model: str, step: int,
             post_path: Path, cwd: Path, previous_tools: list[str] | None = None,
             probe_paths: dict | None = None) -> dict:
    """Deterministic checks on one canary call. Returns {role, init_tools,
    checks, passed}."""
    checks: list[dict] = []
    sidecar = json.loads(Path(result.sidecar_path).read_text(encoding="utf-8"))
    first = (sidecar.get("attempts") or [{}])[0]
    init = first.get("init") or {}
    tools = list(init.get("tools") or [])

    _check(checks, "call_ok", result.ok, result.failure)
    _check(checks, "model_pinned", init.get("model") == model, f"init.model={init.get('model')}")
    extra = sorted(set(tools) - set(expected_tools) - {"StructuredOutput"})
    _check(checks, "tools_within_role", not extra, f"unexpected tools: {extra}" if extra else "")
    missing = sorted(set(expected_tools) - set(tools))
    if missing:
        checks.append({"id": "tools_missing_note", "passed": True,
                       "detail": f"requested but absent (recorded, not a failure): {missing}"})
    _check(checks, "no_skill_tool", "Skill" not in tools)
    _check(checks, "no_mcp_servers", not init.get("mcp_servers"), f"mcp_servers={init.get('mcp_servers')}")
    expected_mode = "dontAsk" if step == 2 else "bypassPermissions"
    _check(checks, "permission_mode", init.get("permissionMode") == expected_mode,
           f"permissionMode={init.get('permissionMode')}")
    if previous_tools is not None:
        _check(checks, "tools_stable", sorted(previous_tools) == sorted(tools),
               f"previous={sorted(previous_tools)} now={sorted(tools)}")

    archive = first.get("transcript_archive")
    if archive and Path(archive).exists():
        transcript = _read_gz(Path(archive))
        sentinels = sentinel_lines(claude_md_files(cwd))
        leaked = sum(1 for s in sentinels if s in transcript)
        _check(checks, "no_claude_md_in_transcript", leaked == 0,
               f"{leaked} of {len(sentinels)} sentinel lines found")
        n_t = _assistant_messages_in_transcript(transcript)
        _check(checks, "transcript_complete", n_t >= int(first.get("n_assistant") or 0),
               f"transcript assistant messages {n_t}, events {first.get('n_assistant')}")
    else:
        _check(checks, "no_claude_md_in_transcript", False, "no archived transcript")
        _check(checks, "transcript_complete", False, "no archived transcript")

    _check(checks, "own_post_written", post_path.exists(), str(post_path.name))

    if step == 2 and probe_paths:
        _check(checks, "sibling_write_denied", not probe_paths["sibling_file"].exists(),
               str(probe_paths["sibling_file"]))
        desk = probe_paths["desktop_file"]
        _check(checks, "desktop_write_denied", not desk.exists(),
               f"{desk} exists, remove it by hand" if desk.exists() else "")
        ex = probe_paths["example_file"]
        ex_ok = ex.exists() and "Example Domain" in ex.read_text(encoding="utf-8", errors="replace")
        _check(checks, "example_curl_denied", not ex_ok)
        oa = probe_paths["openalex_file"]
        try:
            oa_ok = oa.exists() and "results" in json.loads(oa.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            oa_ok = False
        _check(checks, "openalex_curl_allowed", oa_ok)
        denials = [a for att in sidecar.get("attempts") or []
                   for a in ((att.get("result") or {}).get("permission_denials") or [])]
        checks.append({"id": "permission_denials_recorded", "passed": True,
                       "detail": f"{len(denials)} denial(s) in the result events"})

    return {"role": role, "run_id": result.run_id, "init_tools": tools,
            "checks": checks, "passed": all(c["passed"] for c in checks)}


def _init_scratch_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", str(path)], capture_output=True, check=False)
    (path / "README.md").write_text("preflight canary scratch repo\n", encoding="utf-8")


def run_canary(roles: list[str] | None = None, step2: bool = False,
               scratch_parent: Path | None = None) -> dict:
    """Run the canary (live unless KNA_CLAUDE_BIN points at a stub). Writes
    logs/preflight/<stamp>.json and, when all roles pass, last.json."""
    cfg = claude_cli.load_forum_config()
    model = claude_cli._pinned_model(cfg)
    if step2 and cfg.get("permission_mode") != "dontAsk":
        raise SystemExit("[preflight] --step2 refused: forum_config.permission_mode is not 'dontAsk'. "
                         "In bypass mode the denial probes would really write outside the repo.")
    agents = {a["id"]: a for a in claude_cli._load_agents_json().get("agents", [])}
    roles = roles or list(agents)
    previous = (last_record() or {}).get("init_tools") or {}
    fp = fingerprint()
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    cwd = BASE_DIR / "workspace"
    effort = None if "canary" in (cfg.get("effort_by_task") or {}) else "low"
    report = {"ts": datetime.now().isoformat(timespec="seconds"), "step": 2 if step2 else 1,
              "fingerprint": fp, "roles": [], "init_tools": {}}
    for role in roles:
        agent = agents[role]
        tools = list(agent.get("allowed_tools") or [])
        run_id = claude_cli.new_run_id(f"canary_{role}")
        run_dir = cwd / "preflight" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        post = run_dir / "post.md"
        probes, probe_paths = None, None
        if step2:
            sibling = (scratch_parent or BASE_DIR.parent) / f".kna_preflight_{stamp}"
            _init_scratch_repo(sibling)
            desktop_file = Path.home() / "Desktop" / f"kna_canary_{run_id}.txt"
            probes = step2_probes(run_dir, sibling, desktop_file)
            probe_paths = {"sibling_file": sibling / "CANARY.txt", "desktop_file": desktop_file,
                           "example_file": run_dir / "example.html", "openalex_file": run_dir / "openalex.json"}
        res = claude_cli.run_claude(
            "canary", canary_prompt(role, post, probes), role=role,
            user_message="Run the canary steps now.", schema=CANARY_SCHEMA, expect_file=post,
            cwd=cwd, effort=effort, tools=tools, timeout_s=600, max_turns=15, max_continuations=0,
            extra_env={"KNA_RUN_ID": run_id})
        ev = evaluate(role, res, tools, model, 2 if step2 else 1, post, cwd,
                      previous_tools=previous.get(role), probe_paths=probe_paths)
        report["roles"].append(ev)
        report["init_tools"][role] = ev["init_tools"]
    report["passed"] = all(r["passed"] for r in report["roles"])
    out = _preflight_dir()
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{stamp}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if report["passed"]:
        (out / "last.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        claude_cli.notify("KNA forum: preflight failed",
                          "; ".join(f"{r['role']}: " + ",".join(c["id"] for c in r["checks"] if not c["passed"])
                                    for r in report["roles"] if not r["passed"]))
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Forum preflight canary (M03)")
    ap.add_argument("--status", action="store_true", help="Show whether a canary is needed (no Claude call)")
    ap.add_argument("--run", action="store_true", help="Run the canary (live Claude calls)")
    ap.add_argument("--step2", action="store_true", help="Add the denial probes (needs permission_mode dontAsk)")
    ap.add_argument("--role", action="append", default=None, help="Limit to one role (repeatable)")
    args = ap.parse_args(argv)
    if args.run:
        report = run_canary(roles=args.role, step2=args.step2)
        for r in report["roles"]:
            failed = [c["id"] for c in r["checks"] if not c["passed"]]
            print(f"  [preflight] {r['role']}: {'PASS' if r['passed'] else 'FAIL ' + ', '.join(failed)}")
        return 0 if report["passed"] else 1
    needed, reasons = needs_canary()
    print(f"  [preflight] canary {'needed' if needed else 'not needed'}"
          + (f": {'; '.join(reasons)}" if reasons else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())

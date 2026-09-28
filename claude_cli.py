#!/usr/bin/env python3
"""
Claude CLI wrapper (v2.1: M01, M02, M03 step 1, M11)
=====================================================
Every `claude -p` call in the forum goes through run_claude(). It pins the
model and effort, restricts the tool set per role, keeps private context
(CLAUDE.md files, user settings, MCP servers) out of the agent, streams the
event log to disk, archives the session transcript, writes a private
provenance sidecar, classifies failures and applies the failure policy
(usage limits never retry, stalled sessions are resumed, calls per arc are
capped).

Private outputs, all under logs/ (gitignored):
  logs/prompts/<run_id>.md                        system prompt as sent
  logs/rNN/<run_id>_a<k>.events.jsonl             stream-json events, one file per attempt
  logs/rNN/<run_id>_a<k>.stderr.log               CLI stderr, one file per attempt
  logs/rNN/<run_id>.sidecar.json                  provenance and failure record
  logs/transcripts/<arc>/<run_id>_a<k>.jsonl.gz   copy of the session transcript
  logs/alerts.log                                 one line per alert
(Calls without a round use logs/no_round/ instead of logs/rNN/.)

Environment:
  KNA_CLAUDE_BIN    binary to run (tests point it at a stub)
  KNA_ALLOW_LIVE=1  allow a real call under pytest
  KNA_NO_SLEEP=1    skip failure-policy waits (tests)
  KNA_NO_NOTIFY=1   skip the macOS notification (alerts.log is still written)

Shell entry point (auto_run.sh and other scripts):
  python3 claude_cli.py run --task agora --tools Read --message "..."
  python3 claude_cli.py notify "title" "message"
"""

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

EXIT_USAGE_LIMIT = 75
FAILURE_CLASSES = ("ok", "usage_limit", "overloaded", "server_error", "max_turns",
                   "timeout", "no_post", "auth_or_config", "unknown")
EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")

# D-02: a full model id, never an alias. "[1m]" is the 1M-context suffix.
MODEL_ID_RE = re.compile(r"^claude-[a-z0-9]+(?:-[a-z0-9]+)*(?:\[1m\])?$")

DEFAULT_MAX_CALLS_PER_ARC = 40
DEFAULT_FAILURE_POLICY = {
    "usage_limit": "pause",
    "overloaded_wait_s": 600,
    "overloaded_max": 2,
    "server_error_wait_s": 120,
    "server_error_max": 1,
    "max_failed_runs_per_invocation": 4,
}

# M02 isolation. CLAUDE.md files and auto memory stay out of the agent.
ISOLATION_ENV = {"CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1"}
# Never passed to an agent. An API key would bill the API instead of the
# subscription, the effort variable overrides --effort, and the watchdog
# can wait past the wrapper's timeout.
STRIPPED_ENV = ("ANTHROPIC_API_KEY", "CLAUDE_CODE_EFFORT_LEVEL", "CLAUDE_CODE_RETRY_WATCHDOG")
# Settings from the user level (model, effort, allow rules, hooks) stay out.
ISOLATION_FLAGS = ["--disallowedTools", "mcp__*", "--strict-mcp-config", "--setting-sources", "project"]

CONTINUATION_MESSAGE = (
    "The post file {path} does not exist yet. Write it now from the work you have already done. "
    "If something blocks you, write the post anyway and name the blocker in it."
)
RESUME_MESSAGE = (
    "Your previous turn stopped before the task was finished ({reason}). Continue from where you "
    "stopped and finish the task. Do not start over."
)

STEP2_DEFAULT_DOMAINS = ["api.openalex.org", "api.crossref.org", "www.kci.go.kr",
                         "github.com", "objects.githubusercontent.com"]
STEP2_DEFAULT_DENY_READ = ["~/.claude/**", "~/.ssh/**", "~/.aws/**"]


class ClaudeCLIError(RuntimeError):
    """The wrapper refuses to run (configuration error)."""


class LiveCallBlocked(ClaudeCLIError):
    """A real claude call was attempted under pytest."""


@dataclass
class CallResult:
    ok: bool                 # failure == "ok"
    failure: str             # one of FAILURE_CLASSES
    text: str                # final result text ("" if none)
    structured: dict | None  # result.structured_output
    run_id: str
    session_id: str
    attempts: int            # 1 + continuations used
    sidecar_path: Path       # logs/rNN/<run_id>.sidecar.json (private)
    events_paths: list[Path] = field(default_factory=list)  # one file per attempt
    model: str | None = None           # system/init model
    models_used: list[str] = field(default_factory=list)    # modelUsage keys across attempts
    cli_version: str | None = None
    num_turns: int | None = None
    terminal_reason: str | None = None
    resume_at: str | None = None       # ISO time for usage_limit, when known
    containment: dict | None = None    # filled by the caller (staging) if it chooses to


# --------------------------------------------------------------------------
# Paths and configuration
# --------------------------------------------------------------------------

def _logs_dir() -> Path:
    return BASE_DIR / "logs"


def _workspace_dir() -> Path:
    return BASE_DIR / "workspace"


def _agents_file() -> Path:
    return BASE_DIR / "agents.json"


def _round_dir(round_num: int | None) -> Path:
    return _logs_dir() / (f"r{int(round_num):02d}" if round_num is not None else "no_round")


def _load_agents_json() -> dict:
    with open(_agents_file(), encoding="utf-8") as f:
        return json.load(f)


def load_forum_config() -> dict:
    """forum_config block of agents.json plus the season number."""
    data = _load_agents_json()
    cfg = dict(data.get("forum_config", {}))
    cfg["season"] = data.get("season", 1)
    return cfg


def _claude_bin() -> str:
    return (os.environ.get("KNA_CLAUDE_BIN") or shutil.which("claude")
            or str(Path.home() / ".local" / "bin" / "claude"))


def _live_blocked() -> bool:
    return bool(os.environ.get("PYTEST_CURRENT_TEST")) and not os.environ.get("KNA_CLAUDE_BIN") \
        and os.environ.get("KNA_ALLOW_LIVE") != "1"


def _live_guard() -> None:
    if _live_blocked():
        raise LiveCallBlocked(
            "claude_cli: refusing a live claude call under pytest. Set KNA_CLAUDE_BIN to a stub, "
            "patch claude_cli.run_claude, or set KNA_ALLOW_LIVE=1 on purpose.")


def _pinned_model(cfg: dict) -> str:
    model = cfg.get("model")
    if not model:
        raise ClaudeCLIError(
            "forum_config.model is not set in agents.json. Refusing to run: the model must be "
            "pinned as a full id (D-02), and there is no code default.")
    if not isinstance(model, str) or not MODEL_ID_RE.match(model):
        raise ClaudeCLIError(f"forum_config.model '{model}' is not a full model id (for example "
                             "claude-opus-5-5). Aliases move over time and are refused.")
    return model


def _resolve_task(task: str, role: str | None, cfg: dict, effort: str | None,
                  tools: list[str] | None, max_turns: int | None) -> dict:
    """Effort, tools and max turns for one call. Agents read agents.json,
    helper tasks read forum_config.effort_by_task and get no tools unless
    given (the tools argument, else forum_config.tools_by_task)."""
    turns_cfg = cfg.get("max_turns") or {}
    if task == "agent":
        if not role:
            raise ClaudeCLIError("run_claude(task='agent') needs role=<agent id>")
        agent = next((a for a in _load_agents_json().get("agents", []) if a.get("id") == role), None)
        if agent is None:
            raise ClaudeCLIError(f"no agent '{role}' in agents.json")
        eff = effort or agent.get("effort")
        tl = list(tools) if tools is not None else list(agent.get("allowed_tools") or [])
        mt = max_turns if max_turns is not None else turns_cfg.get(role)
    else:
        by_task = cfg.get("effort_by_task") or {}
        if task not in by_task and not effort:
            raise ClaudeCLIError(f"unknown task '{task}': not a key of forum_config.effort_by_task "
                                 "and no effort given")
        eff = effort or by_task.get(task)
        tl = list(tools) if tools is not None else list((cfg.get("tools_by_task") or {}).get(task) or [])
        mt = max_turns if max_turns is not None else turns_cfg.get(task)
    if eff not in EFFORT_LEVELS:
        raise ClaudeCLIError(f"effort for {task}/{role} is {eff!r}; expected one of {EFFORT_LEVELS}")
    return {"effort": eff, "tools": [t for t in tl if t], "max_turns": int(mt) if mt else None}


def new_run_id(label: str, round_num: int | None = None) -> str:
    """Unique, filesystem-safe run id, e.g. r31_critic_20260925T101500_ab12cd."""
    safe = re.sub(r"[^A-Za-z0-9_]+", "-", label or "call").strip("-") or "call"
    prefix = f"r{int(round_num):02d}_" if round_num is not None else ""
    return f"{prefix}{safe}_{datetime.now().strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:6]}"


def _now() -> datetime:
    """Current time, timezone-aware. Tests monkeypatch this."""
    return datetime.now(timezone.utc).astimezone()


def _iso(dt: datetime | None = None) -> str:
    return (dt or _now()).isoformat(timespec="seconds")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


# --------------------------------------------------------------------------
# Prompt manifest (M02)
# --------------------------------------------------------------------------

def manifest_block(label: str, text: str, source: str | Path | None = None) -> dict:
    """One entry of a prompt manifest: which block was injected, from where,
    with its hash and size. build_prompt passes a list of these."""
    entry = {"label": label, "sha256": _sha256_text(text or ""), "words": len((text or "").split())}
    if source:
        entry["source"] = str(source)
        try:
            p = Path(source)
            if p.exists():
                entry["mtime"] = datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds")
        except (OSError, ValueError):
            pass
    return entry


# Tasks that get forum_config.common_rules appended. The rules speak of a
# forum post and of repository writes, so the helper tasks (summary, draft,
# slate and the rest), which carry their own format rules, go without them.
COMMON_RULES_TASKS = ("agent", "canary")


def common_rules_text(cfg: dict, task: str = "agent") -> str:
    """forum_config.common_rules as a bullet list, "" for tasks outside
    COMMON_RULES_TASKS. run_forum's dry run appends the same block."""
    rules = cfg.get("common_rules") if task in COMMON_RULES_TASKS else None
    if not rules:
        return ""
    return (rules if isinstance(rules, str) else "\n".join(f"- {r}" for r in rules)).strip()


def _write_prompt(run_id: str, prompt_text: str, cfg: dict, blocks: list[dict] | None,
                  task: str = "agent") -> tuple[Path, dict]:
    """Write the system prompt to logs/prompts/ (outside workspace/, so later
    agents cannot read it), with forum_config.common_rules appended for the
    forum agents and the canary (COMMON_RULES_TASKS)."""
    text = (prompt_text or "").rstrip() + "\n"
    manifest_blocks = list(blocks or [])
    rules_text = common_rules_text(cfg, task)
    if rules_text:
        text += "\n## Common Rules\n\n" + rules_text + "\n"
        manifest_blocks.append(manifest_block("common_rules", rules_text,
                                              source="agents.json forum_config.common_rules"))
    d = _logs_dir() / "prompts"
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{run_id}.md"
    path.write_text(text, encoding="utf-8")
    manifest = {"prompt_path": str(path), "sha256": _sha256_text(text), "words": len(text.split()),
                "chars": len(text), "blocks": manifest_blocks}
    return path, manifest


# --------------------------------------------------------------------------
# Event parsing (M01)
# --------------------------------------------------------------------------

def _scan_json_array(s: str) -> list[dict]:
    """Objects of a possibly truncated JSON array (a timed-out verbose run)."""
    dec = json.JSONDecoder()
    out, i, n = [], 1, len(s)
    while i < n:
        while i < n and s[i] in " \t\r\n,":
            i += 1
        if i >= n or s[i] == "]":
            break
        try:
            obj, i = dec.raw_decode(s, i)
        except json.JSONDecodeError:
            break
        if isinstance(obj, dict):
            out.append(obj)
    return out


def _load_events(path: Path) -> tuple[list[dict], int]:
    try:
        raw = Path(path).read_text(encoding="utf-8", errors="replace")
    except (FileNotFoundError, IsADirectoryError):
        return [], 0
    s = raw.strip()
    if not s:
        return [], 0
    if s[0] == "[":
        try:
            obj = json.loads(s)
            return [e for e in obj if isinstance(e, dict)], 0
        except json.JSONDecodeError:
            events = _scan_json_array(s)
            if events:
                return events, 1
    events, bad = [], 0
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            bad += 1
            continue
        if isinstance(e, dict):
            events.append(e)
        elif isinstance(e, list):
            events.extend(x for x in e if isinstance(x, dict))
    return events, bad


def parse_events(path: Path) -> dict:
    """Parse a stream-json JSONL file or a verbose JSON array. Returns the
    first system/init event, the last result, the last rate_limit_event and
    every system/api_retry event, plus the raw event list."""
    events, bad = _load_events(path)
    init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), None)
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    rate = next((e for e in reversed(events) if e.get("type") == "rate_limit_event"), None)
    retries = [e for e in events if e.get("type") == "system" and e.get("subtype") == "api_retry"]
    return {
        "events": events,
        "init": init,
        "result": result,
        "rate_limit": rate,
        "api_retries": retries,
        "n_events": len(events),
        "n_assistant": sum(1 for e in events if e.get("type") == "assistant"),
        "parse_errors": bad,
    }


# --------------------------------------------------------------------------
# Failure classification (M11)
# --------------------------------------------------------------------------

USAGE_LIMIT_RE = re.compile(
    r"(hit your (?:session|weekly|usage|daily|monthly|opus|sonnet) limit"
    r"|(?:session|weekly|5-hour|five-hour|daily) limit (?:reached|hit)"
    r"|usage limit reached"
    r"|out of (?:extra )?usage)",
    re.IGNORECASE,
)
RESET_RE = re.compile(
    r"resets?\s+(?:at\s+)?(?:(?P<mon>[A-Za-z]{3,9})\.?\s+(?P<day>\d{1,2}),?\s+(?:at\s+)?)?"
    r"(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?\s*(?P<ampm>am|pm)"
    r"(?:\s*\((?P<tz>[^)]+)\))?",
    re.IGNORECASE,
)
EPOCH_RESET_RE = re.compile(r"limit reached\|(\d{9,13})", re.IGNORECASE)
OVERLOADED_RE = re.compile(r"\boverloaded(?:_error)?\b|API Error:?\s*529", re.IGNORECASE)
SERVER_ERROR_RE = re.compile(r"API Error:?\s*5\d\d|internal server error|\bserver[_ ]error\b|\bapi_error\b",
                             re.IGNORECASE)
AUTH_CONFIG_RE = re.compile(
    r"invalid api key|please run /login|not logged in|authentication[_ ](?:failed|error)"
    r"|oauth token|unauthori[sz]ed|\bforbidden\b|billing|credit balance"
    r"|unknown option|unknown command|error: option|invalid model|model .{0,40}not (?:found|available)"
    r"|does not have access|invalid_request",
    re.IGNORECASE,
)
_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}


def _epoch_to_iso(value) -> str | None:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None
    if v > 1e12:  # milliseconds
        v /= 1000.0
    return datetime.fromtimestamp(v, tz=timezone.utc).astimezone().isoformat(timespec="seconds")


def _parse_reset_text(text: str, now: datetime | None = None) -> str | None:
    """ISO reset time from 'resets 11:50am (America/New_York)',
    'resets Oct 2, 9am (America/New_York)' or 'usage limit reached|<epoch>'."""
    if not text:
        return None
    m = EPOCH_RESET_RE.search(text)
    if m:
        return _epoch_to_iso(m.group(1))
    m = RESET_RE.search(text)
    if not m:
        return None
    now = now or _now()
    tz = now.tzinfo
    if m.group("tz"):
        try:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(m.group("tz").strip())
        except Exception:
            tz = now.tzinfo
    local_now = now.astimezone(tz)
    hour = int(m.group("hour")) % 12 + (12 if m.group("ampm").lower() == "pm" else 0)
    minute = int(m.group("minute") or 0)
    if m.group("mon"):
        month = _MONTHS.get(m.group("mon")[:3].lower())
        if not month:
            return None
        cand = local_now.replace(month=month, day=int(m.group("day")), hour=hour, minute=minute,
                                 second=0, microsecond=0)
        if cand < local_now - timedelta(days=1):
            cand = cand.replace(year=cand.year + 1)
    else:
        cand = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if cand <= local_now:
            cand += timedelta(days=1)
    return cand.isoformat(timespec="seconds")


def _message_text(event: dict) -> str:
    msg = event.get("message") or {}
    content = msg.get("content") if isinstance(msg, dict) else None
    if isinstance(content, str):
        return content
    parts = []
    for c in content or []:
        if isinstance(c, dict) and c.get("type") == "text":
            parts.append(c.get("text") or "")
    return "\n".join(parts)


def _is_error_message(event: dict) -> bool:
    """A synthetic assistant message that carries an API or limit error,
    as opposed to the model's own prose."""
    msg = event.get("message") or {}
    model = msg.get("model") if isinstance(msg, dict) else None
    return bool(event.get("error")) or model == "<synthetic>" \
        or _message_text(event).lstrip().startswith("API Error")


def _failure_texts(result: dict | None, events: list[dict]) -> str:
    """Text that may carry an error message: the result text, synthetic
    error messages, assistant error codes and the wrapper's stderr
    pseudo-events. The model's own prose and tool output are not searched."""
    parts = []
    if result:
        parts.append(str(result.get("result") or ""))
        for key in ("error", "errors"):
            if result.get(key):
                parts.append(json.dumps(result.get(key), ensure_ascii=False))
    for e in events:
        if e.get("type") == "assistant" and _is_error_message(e):
            parts.append(_message_text(e))
            if e.get("error"):
                parts.append(str(e.get("error")))
        if e.get("type") == "_wrapper_stderr":
            parts.append(str(e.get("text") or ""))
    return "\n".join(p for p in parts if p)


def classify(result_event: dict | None, events: list[dict], *, post_exists: bool,
             timed_out: bool) -> tuple[str, str | None]:
    """Failure class of one attempt and, for a usage limit, the ISO reset
    time when known. Checked in order: ok, usage_limit, overloaded,
    server_error, max_turns, timeout, no_post, auth_or_config, unknown."""
    res = result_event or {}
    subtype = res.get("subtype")
    is_error = bool(res.get("is_error"))
    status = res.get("api_error_status")
    try:
        status = int(status) if status is not None else None
    except (TypeError, ValueError):
        status = None
    # A success result counts even if the process then hung past the timeout
    # (background shells are only reaped after the result is emitted).
    success = bool(result_event) and subtype == "success" and not is_error

    if success and post_exists:
        return "ok", None

    text = _failure_texts(result_event, events)
    failed = not success
    rate =next((e for e in reversed(events) if e.get("type") == "rate_limit_event"), None)
    info = (rate or {}).get("rate_limit_info") or {}
    rl_status = str(info.get("status") or "")
    assistant_errors = {str(e.get("error")) for e in events if e.get("type") == "assistant" and e.get("error")}

    # usage_limit: a rejected rate-limit window or the limit message
    if failed and ((rl_status and not rl_status.startswith("allowed"))
                   or USAGE_LIMIT_RE.search(text) or "rate_limit" in assistant_errors):
        resume_at = _epoch_to_iso(info.get("resetsAt")) if info.get("resetsAt") and \
            not rl_status.startswith("allowed") else None
        return "usage_limit", resume_at or _parse_reset_text(text)

    retries = [e for e in events if e.get("type") == "system" and e.get("subtype") == "api_retry"]
    last_retry = retries[-1] if retries else {}
    retry_status = last_retry.get("error_status")
    retry_error = str(last_retry.get("error") or "")
    no_result = result_event is None and not timed_out

    if failed and (status == 529 or (is_error and OVERLOADED_RE.search(text))
                   or "overloaded" in assistant_errors
                   or (no_result and (retry_status == 529 or "overload" in retry_error))):
        return "overloaded", None

    if failed and ((status is not None and 500 <= status < 600)
                   or (is_error and SERVER_ERROR_RE.search(text))
                   or "server_error" in assistant_errors
                   or (no_result and isinstance(retry_status, int) and 500 <= retry_status < 600)):
        return "server_error", None

    if subtype == "error_max_turns" or res.get("terminal_reason") == "max_turns":
        return "max_turns", None

    if timed_out:
        return "timeout", None

    if success and not post_exists:
        return "no_post", None

    if status in (400, 401, 403) or AUTH_CONFIG_RE.search(text) \
            or assistant_errors & {"authentication_failed", "billing_error", "invalid_request"}:
        return "auth_or_config", None

    return "unknown", None


# --------------------------------------------------------------------------
# Transcripts (M01)
# --------------------------------------------------------------------------

def _config_dir() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR") or (Path.home() / ".claude"))


def transcript_path(session_id: str, cwd: Path) -> Path | None:
    """The CLI stores sessions per working directory, under a slug of the
    path with non-alphanumeric characters replaced by '-'."""
    projects = _config_dir() / "projects"
    slugs = []
    for c in (Path(cwd), Path(cwd).resolve()):
        s = str(c)
        for slug in (re.sub(r"[^A-Za-z0-9]", "-", s), s.replace("/", "-")):
            if slug not in slugs:
                slugs.append(slug)
    for slug in slugs:
        p = projects / slug / f"{session_id}.jsonl"
        if p.exists():
            return p
    hits = sorted(projects.glob(f"*/{session_id}.jsonl")) if projects.exists() else []
    return hits[0] if hits else None


def _archive_transcript(session_id: str, cwd: Path, arc_id: str | None, run_id: str, k: int) -> Path | None:
    src = transcript_path(session_id, cwd)
    if src is None:
        return None
    arc_dir = re.sub(r"[^A-Za-z0-9_.-]", "_", arc_id) if arc_id else "no_arc"
    dest = _logs_dir() / "transcripts" / arc_dir / f"{run_id}_a{k}.jsonl.gz"
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(src, "rb") as fi, gzip.open(dest, "wb") as fo:
        shutil.copyfileobj(fi, fo)
    return dest


# --------------------------------------------------------------------------
# Sidecars, call budget and launch gate
# --------------------------------------------------------------------------

def _all_sidecars() -> list[Path]:
    d = _logs_dir()
    return sorted(d.glob("*/*.sidecar.json")) if d.exists() else []


def find_sidecar(run_id: str) -> Path | None:
    hits = sorted(_logs_dir().glob(f"*/{run_id}.sidecar.json")) if _logs_dir().exists() else []
    return hits[0] if hits else None


def update_sidecar(path_or_run_id, **fields) -> Path | None:
    """Merge fields into a sidecar (staging uses it to record containment).
    Accepts the sidecar path or a run id. Returns the path, or None if absent."""
    p = Path(path_or_run_id) if str(path_or_run_id).endswith(".sidecar.json") \
        else find_sidecar(str(path_or_run_id))
    if p is None or not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    data.update(fields)
    _write_json(p, data)
    return p


def count_calls_in_arc(arc_id: str) -> int:
    """CLI invocations (attempts, continuations included) recorded for an arc."""
    n = 0
    for p in _all_sidecars():
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if d.get("arc_id") == arc_id:
            n += len(d.get("attempts") or [])
    return n


def latest_rate_limit_info() -> dict | None:
    """rate_limit_info from the most recent sidecar that has one."""
    for p in sorted(_all_sidecars(), key=lambda q: q.stat().st_mtime, reverse=True):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for a in reversed(d.get("attempts") or []):
            if a.get("rate_limit_info"):
                return a["rate_limit_info"]
    return None


def launch_gate(cfg: dict | None = None) -> tuple[bool, str | None, str | None]:
    """(open, reason, resume_at). Off unless forum_config.failure_policy.launch_gate
    sets thresholds, e.g. {"five_hour": 0.85, "seven_day": 0.90} (D-12)."""
    cfg = cfg if cfg is not None else load_forum_config()
    gate = (cfg.get("failure_policy") or {}).get("launch_gate")
    if not gate:
        return True, None, None
    info = latest_rate_limit_info() or {}
    windows = info.get("unifiedWindows") or {}
    for key in ("five_hour", "seven_day"):
        thr, w = gate.get(key), windows.get(key) or {}
        u = w.get("utilization")
        if thr is not None and u is not None and float(u) >= float(thr):
            return False, f"launch gate: {key} utilization {float(u):.2f} >= {float(thr):.2f}", \
                _epoch_to_iso(w.get("resetsAt"))
    return True, None, None


# --------------------------------------------------------------------------
# Alerts (M11)
# --------------------------------------------------------------------------

def _applescript_quote(s: str) -> str:
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def notify(title: str, message: str) -> None:
    """Append one line to logs/alerts.log and show a macOS notification.
    Never raises and never calls Claude."""
    title = " ".join(str(title).split())
    message = " ".join(str(message).split())
    try:
        d = _logs_dir()
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "alerts.log", "a", encoding="utf-8") as f:
            f.write(f"{_iso()}\t{title}\t{message}\n")
    except Exception:
        pass
    if os.environ.get("KNA_NO_NOTIFY") == "1" or os.environ.get("PYTEST_CURRENT_TEST") \
            or sys.platform != "darwin":
        return
    try:
        script = f"display notification {_applescript_quote(message[:240])} " \
                 f"with title {_applescript_quote(title[:120])}"
        subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
    except Exception:
        pass


# --------------------------------------------------------------------------
# Command, environment and one attempt
# --------------------------------------------------------------------------

_VERSION_CACHE: dict = {}


def cli_version() -> str | None:
    """Installed CLI version, e.g. '2.1.282'. None when it cannot be read
    (or under pytest without a stub binary)."""
    if _live_blocked():
        return None
    b = _claude_bin()
    if b not in _VERSION_CACHE:
        try:
            out = subprocess.run([b, "--version"], capture_output=True, text=True, timeout=30)
            m = re.search(r"\d+\.\d+\.\d+", out.stdout or "")
            _VERSION_CACHE[b] = m.group(0) if m else None
        except Exception:
            _VERSION_CACHE[b] = None
    return _VERSION_CACHE[b]


def _child_env(extra_env: dict) -> dict:
    env = os.environ.copy()
    for k in STRIPPED_ENV:
        env.pop(k, None)
    env.update({k: str(v) for k, v in (extra_env or {}).items()})
    env.update(ISOLATION_ENV)  # extra_env cannot switch isolation off
    return env


def _expand(p: str) -> Path:
    q = Path(os.path.expandvars(os.path.expanduser(p)))
    return q if q.is_absolute() else (BASE_DIR / q)


def write_step2_settings(run_id: str, cfg: dict, expect_file: Path | None,
                         staging_dir: Path | None) -> Path:
    """M03 step 2 settings file (sandbox, network allowlist, deny rules).
    Used only when forum_config.permission_mode is 'dontAsk'. The file lives
    in workspace/ (gitignored) because it holds absolute paths."""
    deny_read = list(STEP2_DEFAULT_DENY_READ)
    private = BASE_DIR / "knowledge" / "private" / "deny_read.txt"
    if private.exists():
        deny_read += [ln.strip() for ln in private.read_text(encoding="utf-8").splitlines()
                      if ln.strip() and not ln.startswith("#")]
    watched = cfg.get("watched_repos") or ["../kna", "../kr-hearings-data"]
    deny_edit = [f"//{str(_expand(w).resolve()).lstrip('/')}/**" for w in watched]
    allow = [f"Edit(//{str(_workspace_dir().resolve()).lstrip('/')}/**)",
             f"Write(//{str(_workspace_dir().resolve()).lstrip('/')}/**)"]
    if expect_file:
        ap = str(Path(expect_file).resolve()).lstrip("/")
        allow += [f"Write(//{ap})", f"Edit(//{ap})"]
    if staging_dir:
        sp = str(Path(staging_dir).resolve()).lstrip("/")
        allow += [f"Write(//{sp}/**)", f"Edit(//{sp}/**)"]
    settings = {
        "permissions": {
            "allow": allow,
            "deny": [f"Read({p})" for p in deny_read]
                    + [f"Edit({p})" for p in deny_edit] + [f"Write({p})" for p in deny_edit],
        },
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "allowUnsandboxedCommands": False,
            "network": {"allowedDomains": STEP2_DEFAULT_DOMAINS + list(cfg.get("sandbox_extra_domains") or [])},
        },
    }
    path = _workspace_dir() / f".forum_settings.{run_id}.json"
    _write_json(path, settings)
    return path


def _permission_args(cfg: dict, run_id: str, expect_file: Path | None, extra_env: dict) -> list[str]:
    """Stage 1 keeps bypass mode. Step 2 of M03 (dontAsk plus sandbox) is
    switched on only by forum_config.permission_mode = 'dontAsk', after the
    canary and one scratch-clone round pass."""
    if cfg.get("permission_mode") != "dontAsk":
        return ["--dangerously-skip-permissions"]
    staging = extra_env.get("KNA_STAGING_DIR")
    settings = write_step2_settings(run_id, cfg, expect_file, Path(staging) if staging else None)
    args = ["--permission-mode", "dontAsk", "--settings", str(settings),
            "--add-dir", str((BASE_DIR / "forum").resolve())]
    if staging:
        args += ["--add-dir", str(Path(staging).resolve())]
    return args


def _build_command(model: str, spec: dict, prompt_path: Path, session_id: str, resume: bool,
                   schema: dict | None, message: str, perm_args: list[str]) -> list[str]:
    tools = spec["tools"]
    cmd = [_claude_bin(), "-p",
           "--model", model,
           "--output-format", "stream-json", "--verbose",
           "--tools", ",".join(tools)]
    if tools:
        cmd += ["--allowedTools", ",".join(tools)]
    cmd += ISOLATION_FLAGS
    cmd += perm_args
    cmd += ["--system-prompt-file", str(prompt_path)]
    cmd += ["--resume", session_id] if resume else ["--session-id", session_id]
    if spec["max_turns"]:
        cmd += ["--max-turns", str(spec["max_turns"])]
    if schema is not None:
        cmd += ["--json-schema", json.dumps(schema, ensure_ascii=False)]
    # --effort comes last: a non-variadic flag right before the message keeps
    # the message from being read as another --tools or --add-dir value.
    cmd += ["--effort", spec["effort"], message]
    return cmd


def _stop_process(proc: subprocess.Popen) -> int | None:
    for sig, wait in ((signal.SIGTERM, 15), (signal.SIGKILL, 10)):
        try:
            os.killpg(proc.pid, sig)
        except (ProcessLookupError, PermissionError, OSError):
            pass
        try:
            return proc.wait(timeout=wait)
        except subprocess.TimeoutExpired:
            continue
    return proc.returncode


def _run_attempt(cmd: list[str], cwd: Path, env: dict, timeout_s: int, round_dir: Path,
                 run_id: str, k: int) -> dict:
    """Run one CLI invocation with stdout streamed straight to its own events
    file, so a timeout keeps the partial stream."""
    round_dir.mkdir(parents=True, exist_ok=True)
    events_path = round_dir / f"{run_id}_a{k}.events.jsonl"
    stderr_path = round_dir / f"{run_id}_a{k}.stderr.log"
    started = _iso()
    timed_out = False
    with open(events_path, "xb") as out, open(stderr_path, "xb") as err:
        proc = subprocess.Popen(cmd, stdout=out, stderr=err, stdin=subprocess.DEVNULL,
                                cwd=str(cwd), env=env, start_new_session=True)
        try:
            rc = proc.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            rc = _stop_process(proc)
        except BaseException:
            _stop_process(proc)
            raise
    return {"events_path": events_path, "stderr_path": stderr_path, "exit_code": rc,
            "timed_out": timed_out, "started": started, "ended": _iso()}


def _attempt_record(k: int, kind: str, att: dict, parsed: dict, cls: str, resume_at: str | None,
                    session_id: str, transcript: Path | None) -> dict:
    init = parsed["init"] or {}
    res = parsed["result"] or {}
    usage_models = res.get("modelUsage") or {}
    rate = parsed["rate_limit"] or {}
    return {
        "attempt": k,
        "kind": kind,
        "session_id": session_id,
        "started": att["started"],
        "ended": att["ended"],
        "exit_code": att["exit_code"],
        "timed_out": att["timed_out"],
        "events_path": str(att["events_path"]),
        "stderr_path": str(att["stderr_path"]),
        "transcript_archive": str(transcript) if transcript else None,
        "class": cls,
        "resume_at": resume_at,
        "init": {k2: init.get(k2) for k2 in ("model", "claude_code_version", "tools", "mcp_servers",
                                             "permissionMode", "apiKeySource", "cwd")},
        "result": {
            **{k2: res.get(k2) for k2 in ("subtype", "is_error", "num_turns", "duration_ms",
                                          "duration_api_ms", "api_error_status", "terminal_reason",
                                          "total_cost_usd", "usage", "permission_denials")},
            "models": list(usage_models.keys()),
            "modelUsage": usage_models,
            "has_structured_output": res.get("structured_output") is not None,
        } if parsed["result"] else None,
        "rate_limit_info": rate.get("rate_limit_info"),
        "api_retries": [{k2: e.get(k2) for k2 in ("attempt", "error_status", "error", "retry_delay_ms")}
                        for e in parsed["api_retries"]],
        "n_events": parsed["n_events"],
        "n_assistant": parsed["n_assistant"],
        "parse_errors": parsed["parse_errors"],
    }


def _post_exists(expect: Path | None) -> bool:
    if expect is None:
        return True
    try:
        return expect.exists() and expect.stat().st_size > 0
    except OSError:
        return False


def _sleep(seconds: float) -> None:
    """Failure-policy wait. KNA_NO_SLEEP=1 skips it, and tests patch it."""
    if os.environ.get("KNA_NO_SLEEP") == "1":
        return
    time.sleep(seconds)


def _limit_kind(sidecar_attempt: dict) -> str | None:
    info = sidecar_attempt.get("rate_limit_info") or {}
    t = str(info.get("rateLimitType") or "")
    if "seven_day" in t or "week" in t:
        return "weekly"
    if "five_hour" in t or "session" in t:
        return "session"
    return None


# --------------------------------------------------------------------------
# The wrapper
# --------------------------------------------------------------------------

def run_claude(task: str, prompt_text: str, *, role: str | None = None,
               user_message: str = "Execute your task now.",
               schema: dict | None = None, expect_file: Path | None = None,
               cwd: Path | None = None, round_num: int | None = None,
               arc_id: str | None = None, effort: str | None = None,
               tools: list[str] | None = None, extra_env: dict | None = None,
               timeout_s: int = 3600, max_turns: int | None = None,
               max_continuations: int = 2,
               prompt_manifest: list[dict] | None = None) -> CallResult:
    """Run one claude -p task with pinned model and effort, isolation,
    streaming, transcript archive, sidecar and the failure policy.

    task is "agent" for forum agents (role = agent id; effort, tools and
    max_turns come from agents.json) or a key of forum_config.effort_by_task.
    expect_file is the file the call must create. If it is missing after a
    successful result, the same session is resumed up to max_continuations
    times. extra_env["KNA_RUN_ID"], when set (staging.env), becomes the run id.
    prompt_manifest is build_prompt's list of manifest_block() entries.
    """
    _live_guard()
    cfg = load_forum_config()
    model = _pinned_model(cfg)
    spec = _resolve_task(task, role, cfg, effort, tools, max_turns)
    extra_env = dict(extra_env or {})
    run_id = extra_env.get("KNA_RUN_ID") or new_run_id(role or task, round_num)
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", run_id):
        raise ClaudeCLIError(f"run id {run_id!r} is not filesystem-safe")
    extra_env["KNA_RUN_ID"] = run_id
    cwd = Path(cwd) if cwd else _workspace_dir()
    cwd.mkdir(parents=True, exist_ok=True)
    expect = None
    if expect_file:
        expect = Path(expect_file)
        expect = expect if expect.is_absolute() else BASE_DIR / expect
    policy = {**DEFAULT_FAILURE_POLICY, **(cfg.get("failure_policy") or {})}
    max_calls = int(cfg.get("max_calls_per_arc") or DEFAULT_MAX_CALLS_PER_ARC)
    round_dir = _round_dir(round_num)
    round_dir.mkdir(parents=True, exist_ok=True)
    sidecar_path = round_dir / f"{run_id}.sidecar.json"
    if sidecar_path.exists():
        raise ClaudeCLIError(f"run id {run_id} already has a sidecar; run ids are single-use")
    prompt_path, manifest = _write_prompt(run_id, prompt_text, cfg, prompt_manifest, task)
    env = _child_env(extra_env)
    perm_args = _permission_args(cfg, run_id, expect, extra_env)
    label = role or task

    sidecar = {
        "run_id": run_id, "task": task, "role": role, "round": round_num, "arc_id": arc_id,
        "created": _iso(), "cwd": str(cwd), "expect_file": str(expect) if expect else None,
        "requested_model": model, "effort": spec["effort"], "tools": spec["tools"],
        "max_turns": spec["max_turns"], "timeout_s": timeout_s, "schema_requested": schema is not None,
        "prompt_manifest": manifest,
        "isolation": {"env": dict(ISOLATION_ENV),
                      "stripped_env": [k for k in STRIPPED_ENV if k in os.environ],
                      "flags": list(ISOLATION_FLAGS), "permission_args": perm_args},
        "failure_policy": policy, "max_calls_per_arc": max_calls,
        "attempts": [], "waits": [],
        "failure": None, "ok": False, "resume_at": None, "session_id": None,
        "model": None, "models_used": [], "cli_version": None, "num_turns": None,
        "terminal_reason": None, "structured_output": None, "containment": None,
    }
    _write_json(sidecar_path, sidecar)

    def _finish(cls: str, resume_at: str | None, terminal: str | None, parsed_last: dict | None,
                session_id: str) -> CallResult:
        attempts = sidecar["attempts"]
        models_used: list[str] = []
        for a in attempts:
            for m in (a.get("result") or {}).get("models") or []:
                if m not in models_used:
                    models_used.append(m)
        init_models = [a["init"]["model"] for a in attempts if a["init"].get("model")]
        versions = [a["init"]["claude_code_version"] for a in attempts if a["init"].get("claude_code_version")]
        turns = [a["result"]["num_turns"] for a in attempts
                 if a.get("result") and isinstance(a["result"].get("num_turns"), int)]
        res = (parsed_last or {}).get("result") or {}
        structured = res.get("structured_output") if isinstance(res.get("structured_output"), dict) else None
        if structured is None and schema is not None:
            # A resumed turn (for example the continuation that wrote the post)
            # may end without structured_output although an earlier attempt
            # returned it. The latest attempt that has one counts.
            structured = latest_structured[0]
        text = str(res.get("result") or "")
        sidecar.update({
            "failure": cls, "ok": cls == "ok", "resume_at": resume_at, "session_id": session_id,
            "model": init_models[0] if init_models else None, "models_used": models_used,
            "cli_version": versions[-1] if versions else None,
            "num_turns": sum(turns) if turns else None,
            "terminal_reason": terminal, "structured_output": structured,
            "structured_missing": schema is not None and cls == "ok" and structured is None,
            "result_text": text, "finished": _iso(),
        })
        _write_json(sidecar_path, sidecar)
        if cls != "ok":
            where = f"R{round_num} " if round_num is not None else ""
            extra = f", resumes {resume_at}" if resume_at else ""
            notify(f"KNA forum: {cls}", f"{where}{label} run {run_id} failed ({cls}{extra}, "
                                        f"{len(attempts)} attempt(s), {terminal or 'no terminal reason'})")
        return CallResult(
            ok=cls == "ok", failure=cls, text=text, structured=structured, run_id=run_id,
            session_id=session_id, attempts=len(attempts), sidecar_path=sidecar_path,
            events_paths=[Path(a["events_path"]) for a in attempts],
            model=sidecar["model"], models_used=models_used, cli_version=sidecar["cli_version"],
            num_turns=sidecar["num_turns"], terminal_reason=terminal, resume_at=resume_at,
        )

    session_id = str(uuid.uuid4())
    # structured_output of the latest attempt that had one. Set before the
    # launch gate, whose early _finish reads it.
    latest_structured: list = [None]

    is_open, gate_reason, gate_resume = launch_gate(cfg)
    if not is_open:
        sidecar["gate"] = gate_reason
        return _finish("usage_limit", gate_resume, "launch_gate", None, session_id)

    counts = {"continuation": 0, "overloaded": 0, "server_error": 0}
    message, resume, kind = user_message, False, "initial"
    parsed = None
    cls, resume_at, terminal = "unknown", None, None
    while True:
        if arc_id and count_calls_in_arc(arc_id) >= max_calls:
            sidecar["budget_refused"] = f"max_calls_per_arc {max_calls} reached for arc {arc_id}"
            return _finish("auth_or_config", None, "max_calls_per_arc", parsed, session_id)
        k = len(sidecar["attempts"]) + 1
        cmd = _build_command(model, spec, prompt_path, session_id, resume, schema, message, perm_args)
        if k == 1:
            sidecar["command"] = cmd
        att = _run_attempt(cmd, cwd, env, timeout_s, round_dir, run_id, k)
        parsed = parse_events(att["events_path"])
        events = list(parsed["events"])
        if not parsed["result"]:
            err = Path(att["stderr_path"]).read_text(encoding="utf-8", errors="replace")[-4000:]
            if err.strip():
                events.append({"type": "_wrapper_stderr", "text": err})
        cls, resume_at = classify(parsed["result"], events, post_exists=_post_exists(expect),
                                  timed_out=att["timed_out"])
        sid = (parsed["init"] or {}).get("session_id") or (parsed["result"] or {}).get("session_id")
        if sid:
            session_id = sid
        try:
            transcript = _archive_transcript(session_id, cwd, arc_id, run_id, k)
        except OSError:
            transcript = None
        record = _attempt_record(k, kind, att, parsed, cls, resume_at, session_id, transcript)
        if cls == "usage_limit":
            record["usage_limit_kind"] = _limit_kind(record)
        sidecar["attempts"].append(record)
        _write_json(sidecar_path, sidecar)
        res = parsed["result"] or {}
        if isinstance(res.get("structured_output"), dict):
            latest_structured[0] = res["structured_output"]
        terminal = res.get("terminal_reason") or res.get("subtype") or ("timeout" if att["timed_out"] else None)

        if cls in ("ok", "usage_limit", "auth_or_config", "unknown"):
            break
        if cls in ("no_post", "max_turns", "timeout") and counts["continuation"] < max_continuations:
            counts["continuation"] += 1
            kind = "continuation"
        elif cls == "overloaded" and counts["overloaded"] < int(policy["overloaded_max"]):
            counts["overloaded"] += 1
            kind = "overloaded_resume"
            wait = int(policy["overloaded_wait_s"])
            sidecar["waits"].append({"reason": "overloaded", "seconds": wait, "at": _iso(), "after_attempt": k})
            _write_json(sidecar_path, sidecar)
            _sleep(wait)
        elif cls == "server_error" and counts["server_error"] < int(policy["server_error_max"]):
            counts["server_error"] += 1
            kind = "server_error_resume"
            wait = int(policy["server_error_wait_s"])
            sidecar["waits"].append({"reason": "server_error", "seconds": wait, "at": _iso(), "after_attempt": k})
            _write_json(sidecar_path, sidecar)
            _sleep(wait)
        else:
            break
        # Resume the same session in the same cwd. A session that never
        # started (no init event, no transcript) is launched fresh instead.
        if parsed["init"] is not None or transcript is not None:
            resume = True
            # An overloaded or server-error interruption cut the work short, so
            # the session continues its task (RESUME_MESSAGE). Only a turn that
            # ended without its post (no_post, max_turns, timeout) is told to
            # write the post now.
            if kind == "continuation" and expect is not None and not _post_exists(expect):
                message = CONTINUATION_MESSAGE.format(path=expect)
            else:
                message = RESUME_MESSAGE.format(reason=cls.replace("_", " "))
        else:
            resume, message, session_id = False, user_message, str(uuid.uuid4())

    return _finish(cls, resume_at, terminal, parsed, session_id)


# --------------------------------------------------------------------------
# Shell entry point
# --------------------------------------------------------------------------

DEFAULT_HELPER_PROMPT = ("You are a helper for the KNA research forum. Do exactly what the user message asks "
                         "and nothing else.")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Run one pinned, isolated claude -p call (forum wrapper).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="Run a task and print the result text")
    r.add_argument("--task", required=True, help="'agent' or a key of forum_config.effort_by_task")
    r.add_argument("--role", default=None)
    r.add_argument("--prompt", default=None, help="System prompt text")
    r.add_argument("--prompt-file", default=None, help="System prompt file")
    r.add_argument("--message", default="Execute your task now.", help="User message")
    r.add_argument("--tools", default=None, help="Comma-separated tool list (default: none for tasks)")
    r.add_argument("--effort", default=None, choices=EFFORT_LEVELS)
    r.add_argument("--round", type=int, default=None)
    r.add_argument("--arc-id", default=None)
    r.add_argument("--expect-file", default=None)
    r.add_argument("--timeout", type=int, default=3600)
    n = sub.add_parser("notify", help="Write an alert line and a notification")
    n.add_argument("title")
    n.add_argument("message")
    c = sub.add_parser("calls", help="Count CLI calls recorded for an arc")
    c.add_argument("arc_id")
    sub.add_parser("version", help="Print the installed CLI version")
    args = ap.parse_args(argv)

    if args.cmd == "notify":
        notify(args.title, args.message)
        return 0
    if args.cmd == "calls":
        print(count_calls_in_arc(args.arc_id))
        return 0
    if args.cmd == "version":
        print(cli_version() or "unknown")
        return 0

    prompt = args.prompt
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
    tools = [t.strip() for t in args.tools.split(",") if t.strip()] if args.tools is not None else None
    try:
        res = run_claude(args.task, prompt or DEFAULT_HELPER_PROMPT, role=args.role,
                         user_message=args.message, tools=tools, effort=args.effort,
                         round_num=args.round, arc_id=args.arc_id,
                         expect_file=Path(args.expect_file) if args.expect_file else None,
                         timeout_s=args.timeout)
    except ClaudeCLIError as e:
        print(f"claude_cli: {e}", file=sys.stderr)
        return 1
    if res.text:
        print(res.text)
    if res.ok:
        return 0
    print(f"claude_cli: {res.failure} (run {res.run_id}, sidecar {res.sidecar_path})", file=sys.stderr)
    return EXIT_USAGE_LIMIT if res.failure == "usage_limit" else 1


if __name__ == "__main__":
    sys.exit(main())

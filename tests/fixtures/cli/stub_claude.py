#!/usr/bin/env python3
"""Stub `claude` binary for tests (never calls a model).

It accepts the flags claude_cli passes, records every invocation, performs
scripted file writes (a post, a ledger append) and emits realistic
stream-json events (system/init, assistant, rate_limit_event, api_retry,
result with modelUsage and structured_output), shaped like the 2.1.282
output observed on 2026-09-24. It also writes a session transcript under
$CLAUDE_CONFIG_DIR/projects/<cwd slug>/<session_id>.jsonl, and only when
CLAUDE_CONFIG_DIR is set, so a test never touches the real home directory.

Control through the environment:
  STUB_CLAUDE_STATE  directory; calls.jsonl gets one line per invocation
  STUB_CLAUDE_PLAN   JSON file holding a list of steps; invocation k uses
                     step min(k, len - 1)

Step keys (all optional):
  mode        ok | usage_limit | overloaded | server_error | max_turns |
              hang | auth | bad_flag                        (default ok)
  write       [[path, text], ...] files to write
  append      [[path, line], ...] lines to append
  write_from_prompt  regex with one group, matched against the system
                     prompt file; writes "canary ok" to that path
  structured  dict returned as structured_output (only with --json-schema)
  format      jsonl | array                                  (default jsonl)
  num_turns   int                                            (default 3)
  resets_at_epoch   resetsAt for usage_limit (omitted when absent)
  utilization       five_hour utilization in rate_limit_event (default 0.12)
  transcript_extra  text added to the transcript as a user message
  init_tools        tools reported in system/init (default: the --tools list)
  sleep       seconds to sleep in hang mode                  (default 30)
  exit_code   override the exit code
"""

import json
import os
import re
import sys
import time
import uuid

VALUE_FLAGS = {"--model", "--output-format", "--tools", "--allowedTools", "--disallowedTools",
               "--setting-sources", "--system-prompt-file", "--session-id", "--resume",
               "--max-turns", "--json-schema", "--effort", "--permission-mode", "--settings",
               "--add-dir"}
BARE_FLAGS = {"-p", "--print", "--verbose", "--strict-mcp-config", "--dangerously-skip-permissions"}
USAGE_TEXT = "You've hit your session limit · resets 11:50am (America/New_York)"


def parse(argv):
    opts, positional, i = {}, [], 0
    while i < len(argv):
        a = argv[i]
        if a in VALUE_FLAGS:
            opts[a] = argv[i + 1] if i + 1 < len(argv) else ""
            i += 2
        elif a in BARE_FLAGS:
            opts[a] = True
            i += 1
        elif a.startswith("-"):
            sys.stderr.write(f"error: unknown option '{a}'\n")
            sys.exit(1)
        else:
            positional.append(a)
            i += 1
    return opts, positional


def load_step(index):
    plan_file = os.environ.get("STUB_CLAUDE_PLAN")
    if not plan_file or not os.path.exists(plan_file):
        return {}
    with open(plan_file, encoding="utf-8") as f:
        plan = json.load(f)
    if isinstance(plan, dict):
        return plan
    return plan[min(index, len(plan) - 1)] if plan else {}


def record_call(opts, positional):
    state = os.environ.get("STUB_CLAUDE_STATE")
    if not state:
        return 0
    os.makedirs(state, exist_ok=True)
    log = os.path.join(state, "calls.jsonl")
    index = 0
    if os.path.exists(log):
        with open(log, encoding="utf-8") as f:
            index = sum(1 for _ in f)
    env_keys = ("CLAUDE_CODE_DISABLE_CLAUDE_MDS", "ANTHROPIC_API_KEY", "CLAUDE_CODE_EFFORT_LEVEL",
                "KNA_RUN_ID", "KNA_STAGING_DIR", "CLAUDE_CODE_RETRY_WATCHDOG")
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps({"index": index, "argv": sys.argv[1:], "cwd": os.getcwd(),
                            "env": {k: os.environ.get(k) for k in env_keys}}) + "\n")
    return index


def model_usage(model):
    return {model: {"inputTokens": 2, "outputTokens": 81, "cacheReadInputTokens": 0,
                    "cacheCreationInputTokens": 2465, "webSearchRequests": 0,
                    "costUSD": 0.021348000000000002, "contextWindow": 1000000,
                    "maxOutputTokens": 128000, "thinkingTokens": 0, "canonicalModel": model,
                    "provider": "firstParty", "costBasis": "list"}}


def main():
    argv = sys.argv[1:]
    if "--version" in argv or "-v" in argv:
        print("2.1.282 (Claude Code)")
        return 0
    opts, positional = parse(argv)
    index = record_call(opts, positional)
    step = load_step(index)
    mode = step.get("mode", "ok")
    if mode == "bad_flag":
        sys.stderr.write("error: unknown option '--bogus-flag'\n")
        return 1

    sid = opts.get("--resume") or opts.get("--session-id") or str(uuid.uuid4())
    model = step.get("model") or opts.get("--model") or "claude-opus-5-5"
    tools = step.get("init_tools")
    if tools is None:
        tools = [t for t in (opts.get("--tools") or "").split(",") if t]
    perm = "bypassPermissions" if opts.get("--dangerously-skip-permissions") \
        else opts.get("--permission-mode", "default")
    message = positional[-1] if positional else ""
    now = int(time.time())
    events = []

    def uid():
        return str(uuid.uuid4())

    def assistant(text, synthetic=False, error=None):
        e = {"type": "assistant",
             "message": {"id": "msg_stub_" + uid()[:8], "type": "message", "role": "assistant",
                         "model": "<synthetic>" if synthetic else model,
                         "content": [{"type": "text", "text": text}],
                         "stop_reason": None, "stop_sequence": None,
                         "usage": {"input_tokens": 2, "output_tokens": 12,
                                   "cache_creation_input_tokens": 2465, "cache_read_input_tokens": 0}},
             "parent_tool_use_id": None, "session_id": sid, "uuid": uid()}
        if error:
            e["error"] = error
        return e

    def rate_event(status="allowed", resets=None, util=None):
        util = step.get("utilization", 0.12) if util is None else util
        info = {"status": status, "rateLimitType": "five_hour", "utilization": util,
                "unifiedWindows": {"five_hour": {"utilization": util, "resetsAt": now + 3 * 3600},
                                   "seven_day": {"utilization": 0.31, "resetsAt": now + 5 * 86400}}}
        if resets is not None:
            info["resetsAt"] = resets
        elif status == "allowed":
            info["resetsAt"] = now + 3 * 3600
        return {"type": "rate_limit_event", "rate_limit_info": info, "uuid": uid(), "session_id": sid}

    def result(subtype="success", is_error=False, text="Done.", status=None, turns=None,
               terminal="completed", structured=None):
        r = {"type": "result", "subtype": subtype, "is_error": is_error, "duration_ms": 1234,
             "duration_api_ms": 1100, "num_turns": step.get("num_turns", 3) if turns is None else turns,
             "result": text, "stop_reason": "end_turn", "session_id": sid, "total_cost_usd": 0.021348,
             "usage": {"input_tokens": 2, "cache_creation_input_tokens": 2465,
                       "cache_read_input_tokens": 0, "output_tokens": 81,
                       "server_tool_use": {"web_search_requests": 0}, "service_tier": "standard"},
             "modelUsage": model_usage(model), "permission_denials": [], "terminal_reason": terminal,
             "api_error_status": status, "uuid": uid()}
        if structured is not None:
            r["structured_output"] = structured
        return r

    init = {"type": "system", "subtype": "init", "cwd": os.getcwd(), "session_id": sid,
            "tools": tools, "mcp_servers": [], "model": model, "permissionMode": perm,
            "slash_commands": ["compact", "context", "cost"], "apiKeySource": "none",
            "claude_code_version": "2.1.282", "output_style": "default", "agents": [],
            "skills": [], "plugins": [], "uuid": uid()}
    events.append(init)

    # Scripted side effects happen during the run, before the result.
    for path, text in step.get("write") or []:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    for path, line in step.get("append") or []:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(line.rstrip("\n") + "\n")
    if step.get("write_from_prompt") and opts.get("--system-prompt-file"):
        with open(opts["--system-prompt-file"], encoding="utf-8") as f:
            m = re.search(step["write_from_prompt"], f.read())
        if m:
            os.makedirs(os.path.dirname(m.group(1)) or ".", exist_ok=True)
            with open(m.group(1), "w", encoding="utf-8") as f:
                f.write("canary ok\n")

    exit_code = 0
    if mode == "ok":
        events.append(assistant("Working on the task."))
        events.append(rate_event())
        structured = step.get("structured") if opts.get("--json-schema") else None
        events.append(result(text=step.get("result_text", "Done."), structured=structured))
    elif mode == "usage_limit":
        events.append(rate_event("rejected", resets=step.get("resets_at_epoch"), util=1.0))
        events.append(assistant(USAGE_TEXT, synthetic=True, error="rate_limit"))
        events.append(result(is_error=True, text=USAGE_TEXT, turns=1, terminal="api_error"))
        exit_code = 1
    elif mode == "overloaded":
        for k in (1, 2):
            events.append({"type": "system", "subtype": "api_retry", "attempt": k, "max_retries": 10,
                           "retry_delay_ms": 500 * k, "error_status": 529, "error": "overloaded",
                           "session_id": sid, "uuid": uid()})
        text = 'API Error: 529 {"type":"error","error":{"type":"overloaded_error","message":"Overloaded"}}'
        events.append(assistant(text, synthetic=True))
        events.append(result(is_error=True, text=text, status=529, turns=1, terminal="api_error"))
        exit_code = 1
    elif mode == "server_error":
        text = 'API Error: 500 {"type":"error","error":{"type":"api_error","message":"Internal server error"}}'
        events.append(assistant(text, synthetic=True))
        events.append(result(is_error=True, text=text, status=500, turns=2, terminal="api_error"))
        exit_code = 1
    elif mode == "max_turns":
        events.append(assistant("Still working."))
        events.append(result(subtype="error_max_turns", is_error=True, text="",
                             turns=int(opts.get("--max-turns") or 5), terminal="max_turns"))
        exit_code = 1
    elif mode == "auth":
        text = "Invalid API key · Please run /login"
        events.append(assistant(text, synthetic=True, error="authentication_failed"))
        events.append(result(is_error=True, text=text, status=401, turns=1, terminal="api_error"))
        exit_code = 1
    elif mode == "hang":
        events.append(assistant("Starting a long computation."))

    # Transcript, only under an explicit CLAUDE_CONFIG_DIR.
    cfg_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if cfg_dir:
        slug = re.sub(r"[^A-Za-z0-9]", "-", os.getcwd())
        tdir = os.path.join(cfg_dir, "projects", slug)
        os.makedirs(tdir, exist_ok=True)
        with open(os.path.join(tdir, f"{sid}.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"type": "user", "sessionId": sid, "cwd": os.getcwd(),
                                "message": {"role": "user", "content": message}}) + "\n")
            if step.get("transcript_extra"):
                f.write(json.dumps({"type": "user", "sessionId": sid, "isMeta": True,
                                    "message": {"role": "user", "content": step["transcript_extra"]}}) + "\n")
            for e in events:
                if e["type"] == "assistant":
                    f.write(json.dumps({"type": "assistant", "sessionId": sid,
                                        "message": e["message"]}) + "\n")

    if step.get("format") == "array":
        print(json.dumps(events))
    else:
        for e in events:
            print(json.dumps(e), flush=True)
    sys.stdout.flush()
    if mode == "hang":
        time.sleep(float(step.get("sleep", 30)))
    return int(step.get("exit_code", exit_code))


if __name__ == "__main__":
    sys.exit(main())

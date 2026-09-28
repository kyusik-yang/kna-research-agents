"""run_forum wiring (v2.1): model lock (M01), researcher notes and forum
state (M04), gate provenance (M08), round identity and resume (M12), staged
side effects (M13), the Critic's verdict of record (M10a), the usage-limit
pause (M11) and Stage 2 hooks that stay silent while their flags are off.

Every agent call runs the stub binary in tests/fixtures/cli/stub_claude.py
(KNA_CLAUDE_BIN). Every module path constant that could reach the real
forum/, knowledge/, logs/ or summaries/ is pointed at a temporary repo."""

import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import claude_cli  # noqa: E402
import forum_index  # noqa: E402
import run_forum  # noqa: E402
import staging  # noqa: E402
import write_guard  # noqa: E402

STUB = ROOT / "tests" / "fixtures" / "cli" / "stub_claude.py"
REAL_AGENTS = json.loads((ROOT / "agents.json").read_text(encoding="utf-8"))
MODEL = "claude-opus-5-5"

RUN_FORUM_PATHS = {
    "BASE_DIR": "", "FORUM_DIR": "forum", "LOGS_DIR": "logs", "WORKSPACE_DIR": "workspace",
    "AGENTS_FILE": "agents.json", "SUMMARIES_DIR": "summaries", "KNOWLEDGE_DIR": "knowledge",
    "TOPIC_GATE_FILE": "topic_gate.md", "RETREATS_LEDGER": "knowledge/retreats.jsonl",
    "ACTIVE_ARC_FILE": "knowledge/active_arc.json", "ARC_STATUS_FILE": "knowledge/arc_status.json",
    "HUMAN_CONTEXT_FILE": "knowledge/human_context.md", "WAIVERS_FILE": "knowledge/waivers.jsonl",
    "GATE_EVENTS_FILE": "knowledge/gate_events.jsonl",
    "GATE_CANDIDATES_FILE": "knowledge/gate_candidates.jsonl", "ARCHIVE_DIR": "knowledge/archive",
}
# Other modules run_forum calls, with their BASE_DIR-derived constants.
MODULE_PATHS = {
    "verdict": {"BASE_DIR": "", "FORUM_DIR": "forum", "KNOWLEDGE_DIR": "knowledge", "LOGS_DIR": "logs",
                "WORKSPACE_DIR": "workspace", "AGENTS_FILE": "agents.json",
                "VERDICTS_FILE": "knowledge/verdicts.jsonl", "SHIFTS_FILE": "knowledge/verdict_shifts.jsonl",
                "ACTIVE_ARC_FILE": "knowledge/active_arc.json", "PRECHECKS_DIR": "knowledge/prechecks"},
    "ledger_audit": {"BASE_DIR": "", "FORUM_DIR": "forum", "KNOWLEDGE_DIR": "knowledge",
                     "LEDGER": "knowledge/findings.jsonl", "VERDICTS_FILE": "knowledge/verdicts.jsonl"},
    "taxonomy_monitor": {"BASE_DIR": "", "FORUM_DIR": "forum", "KNOWLEDGE_DIR": "knowledge",
                         "ARTICLES_DIR": "articles", "AGENTS_FILE": "agents.json",
                         "TAXONOMY_FILE": "knowledge/taxonomy.jsonl",
                         "LEGACY_FILE": "knowledge/taxonomy_legacy.jsonl",
                         "ACTIVE_ARC_FILE": "knowledge/active_arc.json"},
    "prediction_card": {"BASE_DIR": "", "KNOWLEDGE_DIR": "knowledge", "WORKSPACE_DIR": "workspace",
                        "CARDS_DIR": "knowledge/prediction_cards",
                        "CARD_INDEX": "knowledge/prediction_cards/index.jsonl",
                        "QUANTITIES_FILE": "knowledge/quantities.jsonl"},
    "prechecks": {"BASE_DIR": "", "FORUM_DIR": "forum", "KNOWLEDGE_DIR": "knowledge", "LOGS_DIR": "logs",
                  "PRECHECKS_DIR": "knowledge/prechecks", "ABSTRACTS_FILE": "knowledge/abstracts.jsonl",
                  "ACTIVE_ARC_FILE": "knowledge/active_arc.json", "AGENTS_FILE": "agents.json",
                  "DOI_CACHE_FILE": "logs/doi_cache.json"},
    "claim_sheet": {"BASE_DIR": "", "FORUM_DIR": "forum", "KNOWLEDGE_DIR": "knowledge",
                    "WORKSPACE_DIR": "workspace", "LOGS_DIR": "logs",
                    "ACTIVE_ARC_FILE": "knowledge/active_arc.json"},
    "topic_diversity": {"BASE_DIR": "", "FORUM_DIR": "forum", "ARTICLES_DIR": "articles",
                        "KNOWLEDGE_DIR": "knowledge", "AGENTS_FILE": "agents.json",
                        "ACTIVE_ARC_FILE": "knowledge/active_arc.json",
                        "CARDS_DIR": "knowledge/prediction_cards",
                        "LOG_FILE": "knowledge/topic_diversity.jsonl"},
    "leak_lint": {"BASE_DIR": "", "PRIVATE_PATTERNS_FILE": "knowledge/private/leak_patterns.txt"},
}

SCOUT_TEXT = """---
author: "Scout"
date: "2026-09-25 10:00"
type: research_agenda
references: []
---

# First-term learning, revisited

## Prediction to Test

The first-term passage gap narrows by year three.

```yaml
agent_block:
  note: "kept byte for byte"
  items:
    - a
    - b
```
"""

ANALYST_TEXT = """---
author: "Analyst"
date: "2026-09-25 11:00"
type: data_report
---

# Baseline vs Observed

The gap is 4 percentage points in year one.
"""

CRITIC_TEXT = """---
author: "Critic"
date: "2026-09-25 12:00"
type: review
---

# Review

The gap holds. The falsifier is still pending.

```yaml
scoring:
  research_novelty: 2
  empirical_rigor: 3
  theoretical_connection: 2
  actionability: 3
  opportunity_pattern: puzzle_contradiction
  method_paradigm: empirical_mapping
  operation: measure
  falsifier_tested: no
  prior_status: not_tested
  headline_basis: prespecified
  verdict: revise
  one_line: "The gap holds and the falsifier is pending."
```
"""

STRUCTURED = {"research_novelty": 2, "empirical_rigor": 3, "theoretical_connection": 2, "actionability": 3,
              "opportunity_pattern": "puzzle_contradiction", "method_paradigm": "empirical_mapping",
              "operation": "measure", "falsifier_tested": "no", "prior_status": "not_tested",
              "headline_basis": "prespecified", "verdict": "revise",
              "one_line": "The gap holds and the falsifier is pending."}

ARC6 = {
    "seed": "First-term legislative learning in the 22nd Assembly",
    "identification": "within-assembly comparison",
    "exclusion_criteria": "(X1) no productivity counts (X2) no ideology",
    "prior": "First-term members' bills pass less often early in the term and the gap narrows.",
    "falsifier": "The first-term by year interaction is indistinguishable from zero.",
    "drafted_by": "orchestrating Claude session (claude-opus-5-5)",
    "signed_by": "orchestrating Claude session, signed under the researcher's standing delegation of 2026-09-25",
    "signed": "2026-09-26",
    "start_round": 31, "season": 2, "arc": 6, "arc_id": "6",
    "model": MODEL, "claude_code_version": "2.1.282",
}

GATE_ENTRY = """# Topic Gate

## R31 - Arc 6 opening

seed: {seed}

identification: within-assembly comparison of passage rates.

exclusion_criteria: (X1) no productivity counts (X2) no ideology

prior: {prior}

falsifier: The first-term by year interaction is indistinguishable from zero across six assemblies.

human_rationale: The arc tests an institutional learning claim.
Why: because the Season 2 gap was never tested within term.

{provenance}signed: 2026-09-26
"""
PROVENANCE_CLAUDE = ("drafted_by: orchestrating Claude session (claude-opus-5-5)\n\n"
                     "signed_by: orchestrating Claude session, signed under the researcher's standing "
                     "delegation of 2026-09-25\n\n")


# --------------------------------------------------------------------------- fixture

@pytest.fixture
def repo(tmp_path, monkeypatch):
    base = tmp_path / "repo"
    for d in ("forum", "knowledge/hand_coding", "workspace", "logs", "summaries", "articles"):
        (base / d).mkdir(parents=True)
    agents = json.loads(json.dumps(REAL_AGENTS))
    agents["forum_config"]["model"] = MODEL
    agents["forum_config"]["stage2"] = {k: False for k in agents["forum_config"].get("stage2", {})}
    (base / "agents.json").write_text(json.dumps(agents), encoding="utf-8")

    for name, rel in RUN_FORUM_PATHS.items():
        monkeypatch.setattr(run_forum, name, base / rel if rel else base)
    for mod in (claude_cli, staging, write_guard):
        monkeypatch.setattr(mod, "BASE_DIR", base)
    monkeypatch.setattr(forum_index, "FORUM_DIR", base / "forum")
    for modname, consts in MODULE_PATHS.items():
        mod = __import__(modname)
        for name, rel in consts.items():
            if hasattr(mod, name):
                monkeypatch.setattr(mod, name, base / rel if rel else base)

    import topic_diversity
    diversity_calls = []

    def fake_check_post(post_path, log=True, *, round_num=None, arc_start=None, run_id=None):
        diversity_calls.append({"post": Path(post_path).name, "round": round_num, "run_id": run_id})
        return {"status": "clear", "max_cosine": 0.1, "n_prior": 0}

    monkeypatch.setattr(topic_diversity, "check_post", fake_check_post)
    monkeypatch.setattr(topic_diversity, "prior_topics_for_scout", lambda: "")
    monkeypatch.setattr(topic_diversity, "format_for_prompt", lambda round_num=None: "")
    monkeypatch.setattr(run_forum, "verify_citations", lambda p: [])

    counter = {"n": 0}

    def fake_run_id(label, round_num=None):
        counter["n"] += 1
        prefix = f"r{int(round_num):02d}_" if round_num is not None else ""
        return f"{prefix}{label}_t{counter['n']}"

    monkeypatch.setattr(claude_cli, "new_run_id", fake_run_id)
    monkeypatch.setattr(claude_cli, "_sleep", lambda s: None)
    data = tmp_path / "kbl_data"
    data.mkdir()
    state = tmp_path / "stub_state"
    monkeypatch.setenv("KBL_DATA", str(data))
    monkeypatch.setenv("KNA_CLAUDE_BIN", str(STUB))
    monkeypatch.setenv("STUB_CLAUDE_STATE", str(state))
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "claude_config"))
    monkeypatch.setenv("KNA_NO_SLEEP", "1")
    monkeypatch.delenv("STUB_CLAUDE_PLAN", raising=False)
    monkeypatch.delenv("KNA_ALLOW_LIVE", raising=False)
    monkeypatch.delenv("KNA_STAGING_DIR", raising=False)
    monkeypatch.delenv("KNA_RUN_ID", raising=False)
    monkeypatch.delenv("KNA_ACTOR", raising=False)
    monkeypatch.setattr(run_forum, "ROUND_ORDER_OVERRIDE", None)
    monkeypatch.setattr(run_forum, "EFFORT_OVERRIDE", None)
    monkeypatch.setattr(run_forum, "PREVIEW_ARC", None)   # a dry run with --topic sets it

    def plan(steps):
        p = tmp_path / "plan.json"
        p.write_text(json.dumps(steps), encoding="utf-8")
        monkeypatch.setenv("STUB_CLAUDE_PLAN", str(p))

    def calls():
        f = state / "calls.jsonl"
        return [json.loads(line) for line in f.read_text().splitlines()] if f.exists() else []

    def config(**kw):
        a = json.loads((base / "agents.json").read_text())
        for k, v in kw.items():
            a["forum_config"][k] = v
        (base / "agents.json").write_text(json.dumps(a), encoding="utf-8")

    return SimpleNamespace(base=base, forum=base / "forum", k=base / "knowledge", plan=plan, calls=calls,
                           config=config, diversity=diversity_calls, agents=agents)


def legacy_forum(base: Path, upto: int = 90) -> None:
    for n in range(1, upto + 1):
        role = forum_index.ROLE_ORDER[(n - 1) % 3]
        body = f'---\nauthor: "{role}"\n---\n\n# Post {n}\n\nlegacy body {n}\n'
        if role == "critic":
            body += f'\n```yaml\nscoring:\n  verdict: revise\n  one_line: "legacy finding {n}"\n```\n'
        (base / "forum" / f"{n:03d}_{role}.md").write_text(body)


def keyed_post(base: Path, num: int, role: str, rnd: int, text: str = "body") -> Path:
    p = base / "forum" / f"{num:03d}_{role}.md"
    p.write_text(f'---\nauthor: "{role}"\nround: {rnd}\narc: 6\nrole: "{role}"\nrun_id: "pre_{num}"\n---\n\n'
                 f"# {role} post\n\n{text}\n")
    return p


def open_arc(base: Path, state: str = "running", **extra) -> dict:
    arc = {**ARC6, **extra}
    arc = {k: v for k, v in arc.items() if v is not None}
    (base / "knowledge" / "active_arc.json").write_text(json.dumps(arc))
    (base / "knowledge" / "arc_status.json").write_text(json.dumps({"state": state, "start_round": 31}))
    return arc


def agent(repo, aid: str) -> dict:
    return next(a for a in repo.agents["agents"] if a["id"] == aid)


def step_write(path: Path, text: str, **kw) -> dict:
    return {"write": [[str(path), text]], **kw}


def round31_steps(repo, critic_structured=STRUCTURED) -> list:
    f, s = repo.forum, repo.base / "summaries"
    critic = step_write(f / "093_critic.md", CRITIC_TEXT)
    if critic_structured is not None:
        critic["structured"] = critic_structured
    return [step_write(f / "091_literature_scout.md", SCOUT_TEXT),
            step_write(f / "092_data_analyst.md", ANALYST_TEXT),
            critic,
            step_write(s / "round_31.md", "---\nround: 31\n---\n\n# Round 31 Summary\n")]


def run_main(argv) -> int:
    try:
        run_forum.main(argv)
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else 1
    return 0


def body_after_frontmatter(text: str) -> str:
    m = re.match(r"---\n.*?\n---\n", text, re.DOTALL)
    return text[m.end():] if m else text


# --------------------------------------------------------------------------- M01 model lock

def test_topic_gate_records_model_cli_version_and_arc_id(repo):
    legacy_forum(repo.base)
    (repo.base / "topic_gate.md").write_text(GATE_ENTRY.format(seed=ARC6["seed"], prior=ARC6["prior"],
                                                               provenance=PROVENANCE_CLAUDE))
    run_forum.check_topic_gate(ARC6["seed"], 31, 90)
    arc = json.loads((repo.k / "active_arc.json").read_text())
    assert arc["model"] == MODEL
    assert arc["claude_code_version"] == "2.1.282"      # from the stub's --version
    assert arc["arc_id"] == "6" and arc["arc"] == 6 and arc["start_round"] == 31
    # A relaunch of the same opening round keeps the arc id and the model lock.
    repo.config(model="claude-opus-9-9")
    run_forum.check_topic_gate(ARC6["seed"], 31, 92)
    again = json.loads((repo.k / "active_arc.json").read_text())
    assert again["arc_id"] == "6" and again["model"] == MODEL and again["opened"] == arc["opened"]


def test_arc_of_round_uses_the_active_arc_then_the_legacy_table(repo):
    # Arc 5's active_arc.json predates arc ids: its rounds fall back to the table.
    open_arc(repo.base, start_round=28, arc=None, arc_id=None)
    assert run_forum.arc_of_round(30) == 5 and run_forum.arc_of_round(25) == 4
    assert run_forum.arc_of_round(31) is None and run_forum._arc_id(31) is None
    open_arc(repo.base)
    assert run_forum.arc_of_round(31) == 6 and run_forum._arc_id(31) == "6"
    assert run_forum.arc_of_round(30) == 5


def test_model_lock_blocks_before_any_agent(repo):
    legacy_forum(repo.base)
    open_arc(repo.base, model="claude-fable-5")
    code = run_main(["--resume"])
    assert code == 1
    assert repo.calls() == []
    assert not (repo.forum / "091_literature_scout.md").exists()


def test_model_lock_override_is_recorded_and_runs(repo):
    legacy_forum(repo.base)
    open_arc(repo.base, model="claude-fable-5")
    repo.plan(round31_steps(repo))
    assert run_main(["--resume", "--agent", "scout", "--allow-model-change"]) == 0
    status = json.loads((repo.k / "arc_status.json").read_text())
    assert "claude-fable-5 to claude-opus-5-5" in status["allow_model_change"]
    assert (repo.forum / "091_literature_scout.md").exists()


def test_arc_without_model_key_is_not_locked_and_cli_change_is_logged(repo):
    legacy_forum(repo.base)
    open_arc(repo.base, model=None, claude_code_version="2.1.241")
    repo.plan(round31_steps(repo))
    assert run_main(["--resume", "--agent", "scout"]) == 0
    status = json.loads((repo.k / "arc_status.json").read_text())
    assert status["cli_version_changes"][0]["from"] == "2.1.241"
    assert status["cli_version_changes"][0]["to"] == "2.1.282"


def test_accepted_run_gets_frontmatter_keys_and_body_yaml_is_byte_identical(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    repo.plan(round31_steps(repo))
    assert run_main(["--resume", "--agent", "scout"]) == 0
    post = repo.forum / "091_literature_scout.md"
    fm = forum_index.read_frontmatter(post)
    assert fm["round"] == 31 and fm["arc"] == 6 and fm["role"] == "literature_scout"
    assert fm["run_id"] == "r31_literature_scout_t1"
    assert fm["model"] == MODEL and fm["models_used"] == [MODEL]
    assert fm["claude_code_version"] == "2.1.282" and fm["effort"] == "medium"
    assert fm["num_turns"] == 3 and fm["terminal_reason"] == "completed" and fm["attempt"] == 1
    assert fm["author"] == "Scout"
    assert body_after_frontmatter(post.read_text()) == body_after_frontmatter(SCOUT_TEXT)
    assert forum_index.post_meta(post)["source"] == "frontmatter"
    # The call went through the wrapper with the pinned model, role tools and effort.
    argv = repo.calls()[0]["argv"]
    assert argv[argv.index("--model") + 1] == MODEL
    assert argv[argv.index("--tools") + 1] == "Bash,Read,Write"
    assert argv[argv.index("--effort") + 1] == "medium"
    assert "--json-schema" not in argv
    # No prompt file in workspace/, the prompt went to logs/prompts/.
    assert not list((repo.base / "workspace").glob("_prompt_*"))
    assert (repo.base / "logs" / "prompts" / "r31_literature_scout_t1.md").exists()
    side = json.loads((repo.base / "logs" / "r31" / "r31_literature_scout_t1.sidecar.json").read_text())
    assert side["posting_order"] == ["literature_scout", "data_analyst", "critic"]
    assert {b["label"] for b in side["prompt_manifest"]["blocks"]} >= {"agent_prompt", "task", "common_rules"}
    assert repo.diversity == [{"post": "091_literature_scout.md", "round": 31,
                               "run_id": "r31_literature_scout_t1"}]


# --------------------------------------------------------------------------- M04 notes and forum state

def _note(ts, arc_start, text):
    return f"### note | ts: {ts} | source: --comment | arc_start: {arc_start}\n\n{text}\n"


def test_note_bound_to_another_arc_is_not_injected(repo):
    open_arc(repo.base, start_round=28, arc=5, arc_id="5")
    (repo.k / "human_context.md").write_text(_note("2026-04-20 09:00", 23, "Look at citizen demands on housing."))
    prompt = run_forum.build_prompt(agent(repo, "literature_scout"), 28, 28)
    assert "Agora" not in prompt and "citizen demands on housing" not in prompt
    (repo.k / "human_context.md").write_text(_note("2026-09-25 09:00", 28, "Check the 20th Assembly first."))
    prompt = run_forum.build_prompt(agent(repo, "data_analyst"), 28, 28)
    # A note that records no author is not presented as the researcher's (FID-F7).
    assert "## Note (from --comment, dated 2026-09-25 09:00, author unrecorded)" in prompt
    assert "Researcher note" not in prompt
    assert "Check the 20th Assembly first." in prompt
    assert "citizen" not in prompt.lower() and "Agora" not in prompt


def test_note_is_attributed_to_its_recorded_author(repo):
    """FID-F7: a note written by the orchestrating session reaches the agents
    under that name, and only a note by the researcher says researcher."""
    open_arc(repo.base, state="running")
    run_forum.add_human_comment("Focus on committee chairs.", by="orchestrating Claude session")
    run_forum.add_human_comment("Report year-one N.", by="researcher")
    ctx = (repo.k / "human_context.md").read_text()
    assert "| by: orchestrating Claude session | arc_start: 31" in ctx
    prompt = run_forum.build_prompt(agent(repo, "critic"), 32, 32)
    assert "## Note from orchestrating Claude session (from --comment, dated " in prompt
    assert "## Note from the researcher (from --comment, dated " in prompt
    head = prompt.split("Focus on committee chairs.")[0].rsplit("## ", 1)[1]
    assert "researcher" not in head.lower()
    assert "Researcher note" not in prompt


def test_comment_needs_an_author(repo, monkeypatch):
    open_arc(repo.base, state="running")
    with pytest.raises(SystemExit) as exc:
        run_forum.main(["--comment", "Focus on committee chairs."])
    assert "--by" in str(exc.value)
    assert not (repo.k / "human_context.md").exists()
    monkeypatch.setenv("KNA_ACTOR", "orchestrating Claude session")
    assert run_main(["--comment", "Focus on committee chairs."]) == 0
    assert "| by: orchestrating Claude session |" in (repo.k / "human_context.md").read_text()
    assert run_main(["--comment", "Second note.", "--by", "researcher"]) == 0
    _, notes = run_forum._read_notes()
    assert [n["by"] for n in notes] == ["orchestrating Claude session", "researcher"]
    assert repo.calls() == []


def test_comment_before_arc_opens_is_bound_at_the_gate(repo):
    legacy_forum(repo.base)
    open_arc(repo.base, state="stopped", start_round=28, arc=5, arc_id="5", seed="old arc seed")
    status = json.loads((repo.k / "arc_status.json").read_text())
    (repo.k / "arc_status.json").write_text(json.dumps({**status, "action": "draft_and_stop"}))
    (repo.k / "human_context.md").write_text(_note("2026-08-24 10:00", 28, "Old Arc 5 note."))
    run_forum.add_human_comment("Please keep the 17th Assembly out of the pooled sample.")
    assert "arc_start: pending" in (repo.k / "human_context.md").read_text()
    (repo.base / "topic_gate.md").write_text(GATE_ENTRY.format(seed=ARC6["seed"], prior=ARC6["prior"],
                                                               provenance=PROVENANCE_CLAUDE))
    run_forum.check_topic_gate(ARC6["seed"], 31, 90)
    ctx = (repo.k / "human_context.md").read_text()
    assert "arc_start: 31" in ctx and "17th Assembly" in ctx
    assert "Old Arc 5 note." not in ctx
    archived = list((repo.k / "archive").glob("human_context_*.md"))
    assert len(archived) == 1
    assert "Old Arc 5 note." in archived[0].read_text() and "17th Assembly" not in archived[0].read_text()
    prompt = run_forum.build_prompt(agent(repo, "literature_scout"), 31, 31)
    assert "17th Assembly out of the pooled sample" in prompt


def test_comment_while_arc_runs_binds_to_the_active_arc(repo):
    open_arc(repo.base, state="running")
    run_forum.add_human_comment("Report year-one N.")
    assert "arc_start: 31" in (repo.k / "human_context.md").read_text()
    # Paused at a usage limit, the arc is still open.
    (repo.k / "arc_status.json").write_text(json.dumps({"state": "paused_usage_limit"}))
    run_forum.add_human_comment("Second note.")
    assert (repo.k / "human_context.md").read_text().count("arc_start: 31") == 2


def test_no_agora_framing_or_analyst_first_in_run_forum():
    src = (ROOT / "run_forum.py").read_text(encoding="utf-8")
    assert "citizen research demands" not in src
    assert "Yeouido Agora" not in src
    assert "analyst-first" not in src
    assert "set by the researcher in topic_gate" not in src


def test_opening_arc6_forum_state_has_no_earlier_posts(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    for n in (29, 30):
        (repo.base / "summaries" / f"round_{n}.md").write_text(f"summary {n}")
    prompt = run_forum.build_prompt(agent(repo, "literature_scout"), 31, 31)
    state = prompt.split("## Current Forum State", 1)[1]
    assert not re.findall(r"--- (\d{3})_", state)
    assert "Round 29 Summary" not in state
    assert "NEW research topic" in state


def test_resumed_opening_round_gets_opening_instructions_without_topic(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    keyed_post(repo.base, 91, "literature_scout", 31)
    prompt = run_forum.build_prompt(agent(repo, "data_analyst"), 31, 31)
    assert "OPENING ROUND OF AN ARC" in prompt
    assert "091_literature_scout.md" in prompt
    prompt = run_forum.build_prompt(agent(repo, "data_analyst"), 32, 32)
    assert "CONTINUING ROUND" in prompt


def test_open_waivers_are_injected_one_line_each(repo):
    open_arc(repo.base)
    rows = [{"id": "S1", "status": "open", "summary": "KCI feed not wired. Do not write a KCI section.",
             "attributed_to_researcher": False},
            {"id": "W1", "status": "open", "summary": "E1 dropped.", "attributed_to_researcher": True,
             "recorded": "2026-10-01"},
            {"id": "S0", "status": "closed", "summary": "old", "attributed_to_researcher": False}]
    (repo.k / "waivers.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    block = run_forum.waivers_block()
    assert "- KCI feed not wired. Do not write a KCI section. (suspended by the orchestrator, " \
           "not a researcher decision)" in block
    assert "- E1 dropped. (researcher waiver recorded 2026-10-01)" in block
    assert "old" not in block


# --------------------------------------------------------------------------- M08 gate provenance

def test_entry_without_provenance_is_blocked_and_logged(repo):
    (repo.base / "topic_gate.md").write_text(GATE_ENTRY.format(seed=ARC6["seed"], prior=ARC6["prior"],
                                                               provenance=""))
    with pytest.raises(SystemExit) as exc:
        run_forum.check_topic_gate(ARC6["seed"], 31, 90)
    assert "drafted_by" in str(exc.value) and "signed_by" in str(exc.value)
    rows = [json.loads(line) for line in (repo.k / "gate_events.jsonl").read_text().splitlines()]
    assert rows[-1]["result"] == "block" and "drafted_by" in rows[-1]["reason"]
    assert not (repo.k / "active_arc.json").exists()


def test_researcher_drafted_entry_matching_a_candidate_is_blocked(repo):
    prior = ("First-term members' bills pass less often in year one and the gap closes by year three "
             "as members learn the institution.")
    (repo.k / "gate_candidates.jsonl").write_text(json.dumps({"id": "cand-7", "prior": prior}) + "\n")
    researcher = "drafted_by: researcher\n\nsigned_by: researcher\n\n"
    (repo.base / "topic_gate.md").write_text(GATE_ENTRY.format(seed=ARC6["seed"], prior=prior,
                                                               provenance=researcher))
    with pytest.raises(SystemExit) as exc:
        run_forum.check_topic_gate(ARC6["seed"], 31, 90)
    assert "cand-7" in str(exc.value)
    # The same text recorded truthfully as Claude-drafted passes.
    (repo.base / "topic_gate.md").write_text(GATE_ENTRY.format(seed=ARC6["seed"], prior=prior,
                                                               provenance=PROVENANCE_CLAUDE))
    run_forum.check_topic_gate(ARC6["seed"], 31, 90)
    arc = json.loads((repo.k / "active_arc.json").read_text())
    assert arc["human_rationale"] == ("The arc tests an institutional learning claim. Why: because the "
                                      "Season 2 gap was never tested within term.")


def test_arc_block_states_recorded_provenance(repo):
    open_arc(repo.base, drafted_by="orchestrating Claude session (claude-fable-5)",
             signed_by="researcher, selected from a Claude-drafted menu on 2026-08-24")
    for aid in ("literature_scout", "data_analyst", "critic"):
        prompt = run_forum.build_prompt(agent(repo, aid), 32, 32)
        assert "drafted by orchestrating Claude session (claude-fable-5)" in prompt
        assert "signed by researcher, selected from a Claude-drafted menu on 2026-08-24" in prompt
        assert "set by the researcher" not in prompt
        assert "researcher's axiom" not in prompt
    open_arc(repo.base, drafted_by=None, signed_by=None)
    prompt = run_forum.build_prompt(agent(repo, "critic"), 32, 32)
    assert "drafter unrecorded, signer unrecorded" in prompt


def test_gate_events_get_one_row_per_check(repo):
    (repo.base / "topic_gate.md").write_text(GATE_ENTRY.format(seed=ARC6["seed"], prior=ARC6["prior"],
                                                               provenance=PROVENANCE_CLAUDE))
    run_forum.check_topic_gate(ARC6["seed"], 31, 90)
    with pytest.raises(SystemExit):
        run_forum.check_topic_gate("an unsigned seed nobody wrote", 31, 90)
    run_forum.check_topic_gate("an unsigned seed nobody wrote", 31, 90, bypass=True)
    run_forum.check_topic_gate("", 31, 90)          # continuation: no gate check, no row
    rows = [json.loads(line) for line in (repo.k / "gate_events.jsonl").read_text().splitlines()]
    assert [r["result"] for r in rows] == ["pass", "block", "bypass"]
    assert rows[0]["drafted_by"].startswith("orchestrating Claude session")
    assert json.loads((repo.k / "arc_status.json").read_text())["bypass_topic_gate"]


# --------------------------------------------------------------------------- M12 round identity and resume

def _dry_prompts(repo):
    d = repo.base / "logs" / "prompts"
    return sorted(p.name for p in d.glob("dryrun_*.md")) if d.exists() else []


ARC5 = {"seed": "Arc five seed on the committee-alternative channel",
        "prior": "ARC5 PRIOR first-term members use the committee channel",
        "falsifier": "ARC5 FALSIFIER the channel share does not differ", "start_round": 28, "season": 2}
NEW_SEED = "Brand new unsigned topic about committee chairs"


def closed_arc5(base: Path) -> None:
    """Arc 5 as the real repo holds it: closed after its paper, with an
    active_arc.json that predates arc ids and provenance keys."""
    (base / "knowledge" / "active_arc.json").write_text(json.dumps(ARC5))
    (base / "knowledge" / "arc_status.json").write_text(json.dumps(
        {"seed": ARC5["seed"], "start_round": 28, "state": "stopped", "action": "draft_and_stop"}))
    for n in (29, 30):
        (base / "summaries" / f"round_{n}.md").write_text(f"# Round {n} Summary\n\nArc 5 summary {n}\n")


def test_dry_run_with_topic_previews_the_new_arc_without_writing(repo):
    """E2E-05: a dry run with --topic shows the prompts the real run would
    build (the new arc's block, a fresh forum state, the common rules) and
    writes nothing to knowledge/."""
    legacy_forum(repo.base)
    closed_arc5(repo.base)
    (repo.base / "topic_gate.md").write_text(GATE_ENTRY.format(seed=ARC6["seed"], prior=ARC6["prior"],
                                                               provenance=PROVENANCE_CLAUDE))
    before = {p.name: p.read_bytes() for p in repo.k.iterdir() if p.is_file()}
    assert run_main(["--dry-run", "--topic", ARC6["seed"]]) == 0
    assert {p.name: p.read_bytes() for p in repo.k.iterdir() if p.is_file()} == before
    assert _dry_prompts(repo) == ["dryrun_r31_091_literature_scout.md", "dryrun_r31_092_data_analyst.md",
                                  "dryrun_r31_093_critic.md"]
    rules = claude_cli.common_rules_text(run_forum.load_config(), "agent")
    assert rules
    for name in _dry_prompts(repo):
        text = (repo.base / "logs" / "prompts" / name).read_text()
        assert ARC6["prior"] in text and "ARC5" not in text, name
        assert "drafted by orchestrating Claude session (claude-opus-5-5)" in text, name
        assert "NEW research topic" in text, name
        assert not re.findall(r"--- 0(?:8\d|90)_", text), name
        assert "Arc 5 summary" not in text, name
        assert text.count("## Common Rules") == 1 and text.rstrip().endswith(rules), name
    assert repo.calls() == []


def test_dry_run_says_when_the_real_run_would_be_blocked_or_bypassed(repo, capsys):
    legacy_forum(repo.base)
    closed_arc5(repo.base)
    (repo.base / "topic_gate.md").write_text(GATE_ENTRY.format(seed=ARC6["seed"], prior=ARC6["prior"],
                                                               provenance=""))
    assert run_main(["--dry-run", "--topic", ARC6["seed"], "--agent", "scout"]) == 0
    assert "lacks drafted_by, signed_by. A real run would be blocked." in capsys.readouterr().out
    assert run_main(["--dry-run", "--topic", NEW_SEED, "--agent", "scout", "--bypass-topic-gate"]) == 0
    out = capsys.readouterr().out
    assert "opens this thread without a gate entry" in out and "would be blocked" not in out
    text = (repo.base / "logs" / "prompts" / "dryrun_r31_091_literature_scout.md").read_text()
    assert "ARC5" not in text and "NEW research topic" in text
    assert json.loads((repo.k / "active_arc.json").read_text()) == ARC5


def test_arc_block_takes_provenance_from_topic_gate_for_an_old_active_arc(repo):
    """E2E-05: an active_arc.json written before drafted_by and signed_by
    existed reads them from the matching topic_gate.md entry."""
    open_arc(repo.base, drafted_by=None, signed_by=None)
    (repo.base / "topic_gate.md").write_text(GATE_ENTRY.format(seed=ARC6["seed"], prior=ARC6["prior"],
                                                               provenance=PROVENANCE_CLAUDE))
    critic = run_forum.build_prompt(agent(repo, "critic"), 32, 32)
    assert "drafted by orchestrating Claude session (claude-opus-5-5)" in critic
    assert "signed by orchestrating Claude session, signed under the researcher's standing delegation" in critic
    assert "unrecorded" not in critic


def test_bypass_with_a_new_seed_opens_its_own_thread(repo):
    """E2E-13: --bypass-topic-gate with a new seed gets its own arc number,
    call budget and transcript folder, and its prompts carry no other arc's
    conditions or posts. Its provenance says no gate entry exists."""
    legacy_forum(repo.base)
    closed_arc5(repo.base)
    repo.plan([step_write(repo.forum / "091_literature_scout.md", SCOUT_TEXT)])
    assert run_main(["--resume", "--topic", NEW_SEED, "--bypass-topic-gate", "--agent", "scout",
                     "--skip-citation-verify"]) == 0
    arc = json.loads((repo.k / "active_arc.json").read_text())
    assert (arc["arc"], arc["arc_id"], arc["start_round"], arc["seed"]) == (6, "6", 31, NEW_SEED)
    assert arc["bypass"] is True and "prior" not in arc and "falsifier" not in arc
    assert arc["drafted_by"] == arc["signed_by"] == "bypass: no gate entry"
    assert forum_index.read_frontmatter(repo.forum / "091_literature_scout.md")["arc"] == 6
    side = json.loads((repo.base / "logs" / "r31" / "r31_literature_scout_t1.sidecar.json").read_text())
    assert side["arc_id"] == "6"
    prompt = (repo.base / "logs" / "prompts" / "r31_literature_scout_t1.md").read_text()
    assert "ARC5" not in prompt and "Arc Prior and Falsifier" not in prompt
    assert not re.findall(r"--- 0(?:8\d|90)_", prompt) and "Arc 5 summary" not in prompt
    assert "NEW research topic" in prompt
    status = json.loads((repo.k / "arc_status.json").read_text())
    assert status["state"] == "running" and status["bypass_topic_gate"] and status["start_round"] == 31
    rows = [json.loads(line) for line in (repo.k / "gate_events.jsonl").read_text().splitlines()]
    assert rows[-1]["result"] == "bypass"


def test_gate_pass_that_opens_a_new_arc_writes_a_fresh_status(repo):
    """V-09: a normal gate pass that opens a new arc starts its own
    arc_status, so the new arc's failures and stops are never merged into the
    previous arc's record. A relaunch of the same arc's opening keeps it."""
    legacy_forum(repo.base)
    closed_arc5(repo.base)
    old = json.loads((repo.k / "arc_status.json").read_text())
    old.update(last_failure={"run_id": "r30_critic_x", "failure": "timeout"}, last_round=30,
               external_writes=[{"where": "../kna", "kind": "modified", "path": "a.R"}])
    (repo.k / "arc_status.json").write_text(json.dumps(old))
    (repo.base / "topic_gate.md").write_text(GATE_ENTRY.format(seed=ARC6["seed"], prior=ARC6["prior"],
                                                               provenance=PROVENANCE_CLAUDE))
    run_forum.check_topic_gate(ARC6["seed"], 31, 90)
    arc = json.loads((repo.k / "active_arc.json").read_text())
    status = json.loads((repo.k / "arc_status.json").read_text())
    assert (arc["seed"], arc["start_round"]) == (ARC6["seed"], 31)
    assert (status["seed"], status["start_round"], status["state"]) == (arc["seed"], 31, "running")
    for stale in ("action", "last_failure", "last_round", "external_writes"):
        assert stale not in status
    # The new arc's own failure lands in its own status.
    run_forum._update_arc_status(last_failure={"run_id": "r31_data_analyst_t9", "failure": "recovered"})
    status = json.loads((repo.k / "arc_status.json").read_text())
    assert status["seed"] == ARC6["seed"] and status["last_failure"]["run_id"] == "r31_data_analyst_t9"
    # Relaunching the opening round of the same arc keeps its status.
    run_forum.check_topic_gate(ARC6["seed"], 31, 90)
    assert json.loads((repo.k / "arc_status.json").read_text())["last_failure"]["run_id"] == "r31_data_analyst_t9"


def test_missing_critic_of_round_30_is_the_only_role_planned(repo):
    legacy_forum(repo.base, upto=89)
    open_arc(repo.base, start_round=28, arc=5, arc_id="5", model=None)
    assert run_main(["--resume", "--dry-run"]) == 0
    assert _dry_prompts(repo) == ["dryrun_r30_090_critic.md"]
    assert repo.calls() == []


def test_incomplete_round_28_resumes_at_its_critic(repo):
    legacy_forum(repo.base, upto=83)
    open_arc(repo.base, start_round=28, arc=5, arc_id="5", model=None)
    assert run_main(["--resume", "--dry-run"]) == 0
    assert _dry_prompts(repo) == ["dryrun_r28_084_critic.md"]


def test_agent_filter_never_runs_a_role_out_of_order(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    assert run_main(["--resume", "--agent", "critic"]) == 0     # R31 still needs its Scout
    assert repo.calls() == []
    assert not list(repo.forum.glob("09[1-9]_*.md"))


def test_topic_on_an_incomplete_round_is_refused(repo):
    legacy_forum(repo.base, upto=89)
    open_arc(repo.base, start_round=28, arc=5, arc_id="5", seed="old arc seed", model=None)
    assert run_main(["--resume", "--topic", ARC6["seed"]]) == 1
    assert repo.calls() == []


def test_failed_critic_then_resume_runs_only_the_critic(repo):
    """R30 incident replay: a failed Critic never yields a second round label."""
    legacy_forum(repo.base)
    open_arc(repo.base)
    steps = round31_steps(repo)
    critic_ok, summary = steps[2], steps[3]
    no_post = {"mode": "ok"}
    repo.plan([steps[0], steps[1], no_post, no_post, no_post, critic_ok, summary])
    assert run_main(["--resume"]) == 1
    assert sorted(p.name for p in repo.forum.glob("09[1-9]_*.md")) == ["091_literature_scout.md",
                                                                        "092_data_analyst.md"]
    status = json.loads((repo.k / "arc_status.json").read_text())
    assert status["last_failure"]["role"] == "critic" and status["last_failure"]["failure"] == "no_post"
    assert Path(status["last_failure"]["quarantine"]).name == "failed_r31_critic_t3"
    # arc_status.json is tracked and pushed, so the path is repo-relative (FID-F9).
    assert status["last_failure"]["quarantine"] == "knowledge/staging/failed_r31_critic_t3"
    assert str(repo.base) not in (repo.k / "arc_status.json").read_text()
    assert len(repo.calls()) == 5                    # scout, analyst, critic + 2 continuations

    assert run_main(["--resume"]) == 0
    second = repo.calls()[5:]
    assert len(second) == 2                          # critic and summary only
    assert "--json-schema" in second[0]["argv"]
    metas = [m for m in forum_index.index(forum_dir=repo.forum) if m["post_num"] > 90]
    assert [(m["round"], m["role"]) for m in metas] == [(31, "literature_scout"), (31, "data_analyst"),
                                                        (31, "critic")]
    assert all(m["source"] == "frontmatter" for m in metas)
    assert (repo.base / "summaries" / "round_31.md").exists()
    assert forum_index.next_round_plan(forum_dir=repo.forum) == (32, list(forum_index.ROLE_ORDER))


def test_failed_scout_run_writes_no_diversity_row(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    repo.plan([{"mode": "ok"}])
    assert run_main(["--resume"]) == 1
    assert repo.diversity == []
    assert not (repo.forum / "091_literature_scout.md").exists()


# --------------------------------------------------------------------------- M13 staging

def test_failed_run_leaves_retreats_byte_identical_and_quarantines(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    keyed_post(repo.base, 91, "literature_scout", 31)
    keyed_post(repo.base, 92, "data_analyst", 31)
    ledger = repo.k / "retreats.jsonl"
    ledger.write_text(json.dumps({"finding": "old", "originating_round": 3}) + "\n")
    before = ledger.read_bytes()
    phantom = json.dumps({"finding": "phantom retreat"})
    repo.plan([{"append": [[str(ledger), phantom], [str(repo.k / "human_context.md"),
                                                    _note("2026-09-25 13:00", 31, "Written during the run.")]],
                "write": [[str(repo.forum / "093_critic.partial"), "half a post"]]}])
    assert run_main(["--resume"]) == 1
    assert ledger.read_bytes() == before
    q = repo.k / "staging" / "failed_r31_critic_t1"
    assert "phantom retreat" in (q / "tree" / "knowledge" / "retreats.jsonl").read_text()
    assert (q / "tree" / "forum" / "093_critic.partial").read_text() == "half a post"
    assert not (repo.forum / "093_critic.partial").exists()
    # A researcher note written during the run survives the revert (M13 test 7).
    assert "Written during the run." in (repo.k / "human_context.md").read_text()
    assert not (repo.k / "verdicts.jsonl").exists()


def test_analyst_rewrite_of_an_existing_dictionary_is_reverted(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    keyed_post(repo.base, 91, "literature_scout", 31)
    dic = repo.k / "hand_coding" / "round_25.jsonl"
    original = '{"member_id": "A", "category": "cabinet"}\n'
    dic.write_text(original)
    repo.plan([{"write": [[str(repo.forum / "092_data_analyst.md"), ANALYST_TEXT],
                          [str(dic), '{"member_id": "A", "category": "court"}\n']]}])
    assert run_main(["--resume", "--agent", "analyst"]) == 0
    assert dic.read_text() == original
    rev = repo.k / "hand_coding" / "round_25.rev1.jsonl"
    assert "court" in rev.read_text()
    side = json.loads(next((repo.base / "logs" / "r31").glob("r31_data_analyst_t1.sidecar.json")).read_text())
    assert any(v["change"] == "rewrite_existing_dictionary" for v in side["containment"]["violations"])
    assert forum_index.read_frontmatter(repo.forum / "092_data_analyst.md")["role"] == "data_analyst"


def test_happy_path_merges_a_staged_retreat_with_its_run_id(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    keyed_post(repo.base, 91, "literature_scout", 31)
    keyed_post(repo.base, 92, "data_analyst", 31)
    staged = repo.k / "staging" / "r31_critic_t1" / "retreats.jsonl"
    row = {"originating_round": 30, "overturning_round": 31, "flagged_by": "critic",
           "finding": "absorption step", "reason": "placebo moves too", "new_evidence": "10.1111/ajps.12518"}
    steps = round31_steps(repo)
    steps[2]["append"] = [[str(staged), json.dumps(row)]]
    repo.plan([steps[2], steps[3]])
    assert run_main(["--resume"]) == 0
    merged = [json.loads(line) for line in (repo.k / "retreats.jsonl").read_text().splitlines()]
    assert len(merged) == 1 and merged[0]["run_id"] == "r31_critic_t1"
    assert merged[0]["finding"] == "absorption step"


def test_log_retreat_writes_to_the_staging_dir_inside_a_run(repo, monkeypatch):
    stage = repo.k / "staging" / "r31_critic_x"
    monkeypatch.setenv("KNA_STAGING_DIR", str(stage))
    monkeypatch.setenv("KNA_RUN_ID", "r31_critic_x")
    run_forum.log_retreat(30, 31, "critic", "a finding", "a reason", new_evidence="forum/090_critic.md:12")
    row = json.loads((stage / "retreats.jsonl").read_text())
    assert row["new_evidence"] == "forum/090_critic.md:12" and row["run_id"] == "r31_critic_x"
    assert not (repo.k / "retreats.jsonl").exists()


def test_external_write_status_has_no_machine_paths(repo, tmp_path):
    """FID-F9: the external-write stop records locations that are safe in the
    tracked arc_status.json. The private patch keeps the absolute detail."""
    open_arc(repo.base)
    post = keyed_post(repo.base, 92, "data_analyst", 31)
    sibling = tmp_path / "kna"
    ext = [{"kind": "modified", "path": "R/build.R", "where": str(sibling),
            "patch": str(repo.base / "logs" / "external_writes" / "r31_data_analyst_t1.patch")}]
    outcome = run_forum.AgentOutcome(post=post, run_id="r31_data_analyst_t1", result=None,
                                     containment={"external_writes": ext})
    args = SimpleNamespace(skip_citation_verify=True)
    with pytest.raises(SystemExit):
        run_forum._after_post(agent(repo, "data_analyst"), outcome, 31, 31, args, run_forum.load_config())
    text = (repo.k / "arc_status.json").read_text()
    status = json.loads(text)
    assert status["state"] == "external_write"
    # The sibling repo appears as its watched_repos entry, as configured.
    assert status["external_writes"] == [{"kind": "modified", "path": "R/build.R", "where": "../kna",
                                          "patch": "logs/external_writes/r31_data_analyst_t1.patch"}]
    assert str(tmp_path) not in text and "/Users/" not in text


def test_leftover_incomplete_snapshot_blocks_the_next_run(repo):
    """An incomplete snapshot (no SNAPSHOT.json record) cannot be restored
    safely, so it still stops the start for a person."""
    legacy_forum(repo.base)
    open_arc(repo.base)
    (repo.k / "staging" / "_snapshots" / "r31_critic_t9").mkdir(parents=True)
    assert run_main(["--resume"]) == 1
    assert repo.calls() == []


def test_leftover_complete_snapshot_is_recovered_and_the_run_continues(repo):
    """FID-F12: a run whose process died (no commit, no rollback) no longer
    wedges the pipeline. The next start quarantines its partial changes,
    restores the snapshot, records last_failure and runs."""
    legacy_forum(repo.base)
    open_arc(repo.base)
    keyed_post(repo.base, 91, "literature_scout", 31)
    ledger = repo.k / "retreats.jsonl"
    ledger.write_text(json.dumps({"finding": "old"}) + "\n")
    before = ledger.read_bytes()
    staging.begin("r31_data_analyst_dead", "data_analyst")          # the process "dies" after this
    (repo.forum / "092_data_analyst.md").write_text("half an analysis")
    with open(ledger, "a") as f:
        f.write(json.dumps({"finding": "phantom"}) + "\n")
    repo.plan([step_write(repo.forum / "092_data_analyst.md", ANALYST_TEXT)])
    assert run_main(["--resume", "--agent", "analyst"]) == 0
    assert ledger.read_bytes() == before
    q = repo.k / "staging" / "failed_r31_data_analyst_dead"
    assert (q / "tree" / "forum" / "092_data_analyst.md").read_text() == "half an analysis"
    assert staging.leftover_snapshots() == []
    assert body_after_frontmatter((repo.forum / "092_data_analyst.md").read_text()) == \
        body_after_frontmatter(ANALYST_TEXT)
    status = json.loads((repo.k / "arc_status.json").read_text())
    assert status["last_failure"]["failure"] == "recovered"
    assert status["last_failure"]["quarantine"] == "knowledge/staging/failed_r31_data_analyst_dead"
    assert len(repo.calls()) == 1
    assert "run recovered" in (repo.base / "logs" / "alerts.log").read_text()


def test_stale_lock_of_a_reused_pid_does_not_wedge_the_next_run(repo):
    """FID-F12: the lock that makes recovery safe is taken over when its pid
    is dead or now belongs to an unrelated process, and holds while a
    run_forum process owns it."""
    import subprocess
    lock = repo.base / "logs" / "run_forum.lock"
    other = subprocess.Popen(["sleep", "30"])
    try:
        lock.write_text(json.dumps({"pid": other.pid, "started": "2026-09-25T09:00:00"}))
        run_forum._acquire_lock()                    # a live but unrelated process
        assert json.loads(lock.read_text())["pid"] == run_forum.os.getpid()
    finally:
        other.kill()
        other.wait()
    lock.write_text(json.dumps({"pid": other.pid}))  # now dead
    run_forum._acquire_lock()
    assert json.loads(lock.read_text())["pid"] == run_forum.os.getpid()
    holder = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)", "run_forum.py"])
    try:
        lock.write_text(json.dumps({"pid": holder.pid}))
        with pytest.raises(SystemExit) as exc:
            run_forum._acquire_lock()
        assert "Concurrent run" in str(exc.value)
    finally:
        holder.kill()
        holder.wait()


def test_dry_run_never_recovers_a_leftover_snapshot(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    keyed_post(repo.base, 91, "literature_scout", 31)
    staging.begin("r31_data_analyst_dead", "data_analyst")
    assert run_main(["--resume", "--dry-run"]) == 0
    assert staging.leftover_snapshots() == ["r31_data_analyst_dead"]


def test_recovered_post_gets_full_provenance_from_its_sidecar(repo):
    """E2E-12: a post committed by staging but never keyed (a crash between
    staging.commit and set_frontmatter_keys) gets the model and CLI
    provenance from its run's sidecar, like every other post."""
    legacy_forum(repo.base)
    open_arc(repo.base)
    steps = round31_steps(repo)
    repo.plan([steps[0], steps[1]])
    assert run_main(["--resume", "--agent", "scout"]) == 0
    post = repo.forum / "091_literature_scout.md"
    keyed = forum_index.read_frontmatter(post)
    post.write_text(SCOUT_TEXT)                      # the orchestrator keys never landed
    assert forum_index.post_meta(post)["source"] == "inferred"
    assert run_main(["--resume", "--agent", "analyst"]) == 0
    fm = forum_index.read_frontmatter(post)
    for k in ("round", "arc", "role", "run_id", "model", "models_used", "claude_code_version", "effort",
              "num_turns", "terminal_reason", "attempt"):
        assert fm.get(k) == keyed.get(k), k
    assert fm["model"] == MODEL and fm["claude_code_version"] == "2.1.282" and fm["effort"] == "medium"


def test_committed_but_unkeyed_post_is_keyed_on_resume(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    post = repo.forum / "091_literature_scout.md"
    post.write_text(SCOUT_TEXT)
    commit = repo.k / "staging" / "r31_literature_scout_t0" / "COMMIT.json"
    commit.parent.mkdir(parents=True)
    commit.write_text(json.dumps({"run_id": "r31_literature_scout_t0", "post": "forum/091_literature_scout.md"}))
    repo.plan([step_write(repo.forum / "092_data_analyst.md", ANALYST_TEXT)])
    assert run_main(["--resume", "--agent", "analyst"]) == 0
    fm = forum_index.read_frontmatter(post)
    assert fm["round"] == 31 and fm["run_id"] == "r31_literature_scout_t0"
    assert body_after_frontmatter(post.read_text()) == body_after_frontmatter(SCOUT_TEXT)


# --------------------------------------------------------------------------- M10a, M05, M11

def test_full_round_records_verdict_and_one_ledger_row(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    repo.plan(round31_steps(repo))
    assert run_main(["--resume"]) == 0
    rows = [json.loads(line) for line in (repo.k / "verdicts.jsonl").read_text().splitlines()]
    assert len(rows) == 1 and rows[0]["source"] == "structured" and rows[0]["verdict"] == "revise"
    assert rows[0]["run_id"] == "r31_critic_t3" and rows[0]["arc"] == "6"
    ledger = [json.loads(line) for line in (repo.k / "findings.jsonl").read_text().splitlines()]
    assert len(ledger) == 1
    assert ledger[0]["round"] == 31 and ledger[0]["run_id"] == "r31_critic_t3"
    assert ledger[0]["finding"] == "The gap holds and the falsifier is pending."
    run_forum.update_findings_tracker(31, critic_post=repo.forum / "093_critic.md", run_id="r31_critic_t3")
    assert len((repo.k / "findings.jsonl").read_text().splitlines()) == 1
    critic_call = repo.calls()[2]["argv"]
    assert "--json-schema" in critic_call and critic_call[critic_call.index("--effort") + 1] == "high"
    summary_call = repo.calls()[3]["argv"]
    assert summary_call[summary_call.index("--effort") + 1] == "low"
    assert (repo.base / "summaries" / "round_31.md").exists()


def test_critic_success_without_structured_output_is_a_failed_run(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    keyed_post(repo.base, 91, "literature_scout", 31)
    keyed_post(repo.base, 92, "data_analyst", 31)
    repo.plan([step_write(repo.forum / "093_critic.md", CRITIC_TEXT)])
    assert run_main(["--resume"]) == 1
    assert not (repo.forum / "093_critic.md").exists()
    assert (repo.k / "staging" / "failed_r31_critic_t1" / "tree" / "forum" / "093_critic.md").exists()
    status = json.loads((repo.k / "arc_status.json").read_text())
    assert status["last_failure"]["failure"] == "structured_missing"
    assert not (repo.k / "verdicts.jsonl").exists()
    # The sidecar carries it as a classified failure, so run_arc's budget counts it.
    side = json.loads((repo.base / "logs" / "r31" / "r31_critic_t1.sidecar.json").read_text())
    assert side["failure"] == "unknown" and side["orchestrator_failure"] == "structured_missing"
    assert "structured_missing" in (repo.base / "logs" / "alerts.log").read_text()


def test_critic_verdict_before_the_post_survives_the_continuation(repo):
    """COR-F3: the Critic returns its structured verdict, then the
    continuation writes the post and ends without structured_output. The run
    is accepted and the verdict of record comes from the structured output."""
    legacy_forum(repo.base)
    open_arc(repo.base)
    keyed_post(repo.base, 91, "literature_scout", 31)
    keyed_post(repo.base, 92, "data_analyst", 31)
    steps = round31_steps(repo)
    repo.plan([{"structured": STRUCTURED}, step_write(repo.forum / "093_critic.md", CRITIC_TEXT), steps[3]])
    assert run_main(["--resume"]) == 0
    assert (repo.forum / "093_critic.md").exists()
    assert not (repo.k / "staging" / "failed_r31_critic_t1").exists()
    rows = [json.loads(line) for line in (repo.k / "verdicts.jsonl").read_text().splitlines()]
    assert len(rows) == 1 and rows[0]["source"] == "structured" and rows[0]["verdict"] == "revise"
    assert forum_index.read_frontmatter(repo.forum / "093_critic.md")["attempt"] == 2


def test_usage_limit_pauses_with_exit_75(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    run_forum.check_data_pin()       # the arc predates data pinning: pinned (and logged) before the run
    knowledge_before = sorted(p.name for p in repo.k.iterdir())
    repo.plan([{"mode": "usage_limit", "resets_at_epoch": 1790000000}])
    assert run_main(["--resume"]) == claude_cli.EXIT_USAGE_LIMIT == 75
    assert len(repo.calls()) == 1                    # a usage limit never retries
    status = json.loads((repo.k / "arc_status.json").read_text())
    assert status["state"] == "paused_usage_limit"
    assert status["resume_after"] and status["paused_role"] == "literature_scout"
    assert not (repo.forum / "091_literature_scout.md").exists()
    assert sorted(p.name for p in repo.k.iterdir() if p.name != "staging") == \
        sorted(n for n in knowledge_before if n != "staging")


def test_kbl_data_is_required(repo, monkeypatch):
    legacy_forum(repo.base)
    open_arc(repo.base)
    monkeypatch.delenv("KBL_DATA")
    with pytest.raises(SystemExit) as exc:
        run_forum.main(["--resume"])
    assert "KBL_DATA" in str(exc.value)
    assert repo.calls() == []


# --------------------------------------------------------------------------- prompts and Stage 2

def test_critic_prompt_has_no_monitor_numbers_or_stop_rules(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    for aid in ("literature_scout", "data_analyst", "critic"):
        prompt = run_forum.build_prompt(agent(repo, aid), 32, 32)
        for bad in ("entropy", "bridge cap", "BRIDGE CAP", "min_arc_rounds", "arc depth", "bridge share",
                    "Critic applies a cap", "Depth first: if the finding stands", "Round 32/"):
            assert bad not in prompt, (aid, bad)
    critic = run_forum.build_prompt(agent(repo, "critic"), 32, 32)
    assert "Stage 2" not in critic                   # no addenda while every flag is off


def test_critic_header_and_arc_block_carry_no_arc_depth(repo):
    """E2E-07 (M10a): the Critic cannot read off the arc depth from its header
    or arc block. It keeps the round only as the id log_retreat needs. The
    other roles keep both."""
    legacy_forum(repo.base)
    open_arc(repo.base)                              # arc opened at round 31
    critic = run_forum.build_prompt(agent(repo, "critic"), 33, 33)
    assert "Research Forum - Round" not in critic and "Round 33" not in critic
    assert "Arc opened at round" not in critic and "opened at round 31" not in critic
    assert "Round id for log_retreat: 33" in critic
    assert "**Prior** (the belief this arc tests)" in critic      # the signed conditions stay
    for aid in ("literature_scout", "data_analyst"):
        prompt = run_forum.build_prompt(agent(repo, aid), 33, 33)
        assert prompt.lstrip().startswith("# Research Forum - Round 33"), aid
        assert "- Arc opened at round 31." in prompt, aid


REAL_FORMAT_FOR_PROMPT = __import__("topic_diversity").format_for_prompt


@pytest.mark.parametrize("status", ["warn", "block"])
def test_critic_prompt_has_no_diversity_cap_or_stop_rule(repo, monkeypatch, status):
    """E2E-06: the Topic Diversity block in a real Critic prompt carries no
    score cap and no archive instruction while its thresholds are uncalibrated."""
    import topic_diversity
    monkeypatch.setattr(topic_diversity, "format_for_prompt", REAL_FORMAT_FOR_PROMPT)
    legacy_forum(repo.base)
    open_arc(repo.base)
    row = {"round": 32, "status": status, "warn": 0.68, "block": 0.80, "max_cosine": 0.83,
           "nearest_post": {"id": "073_literature_scout", "round": 25, "cosine": 0.83}}
    (repo.k / "topic_diversity.jsonl").write_text(json.dumps(row) + "\n")
    critic = run_forum.build_prompt(agent(repo, "critic"), 32, 32)
    block = critic.split("## Topic Diversity Check", 1)[1]
    assert "073_literature_scout (R25), cosine 0.83" in block and f"**{status.upper()}**" in block
    for bad in ("cap research_novelty", "2/4", "verdict archive", "Critic:", "Analyst:"):
        assert bad not in block, bad


def test_stage2_gate_fields_stay_out_of_stage1_prompts(repo):
    """FID-F8: decision_rule, sesoi, null_paper and premise are Stage 2 gate
    fields. An auto-signed entry carries them, but a default (Stage 1) prompt
    never shows them, so a null_paper line cannot change the Critic's archive
    reading while run_arc's null-paper path is off."""
    stage2 = dict(decision_rule="Pursue if the interaction CI excludes zero.", sesoi="2 percentage points",
                  null_paper="yes", premise="Bill passage data cover six assemblies.")
    open_arc(repo.base, **stage2)
    # The Critic's archive rule names the null-paper line in quotes (V-03), so
    # the arc-block line is matched in its bold form.
    labels = ("Decision rule", "Smallest effect of interest", "**Null result becomes the paper**", "**Premise**")
    for aid in ("literature_scout", "data_analyst", "critic"):
        prompt = run_forum.build_prompt(agent(repo, aid), 32, 32)
        assert "**Prior** (the belief this arc tests)" in prompt, aid
        for label in labels:
            assert label not in prompt, (aid, label)
        for key in ("decision_rule", "sesoi", "premise"):
            assert stage2[key] not in prompt, (aid, key)
    repo.config(stage2={**{k: False for k in repo.agents["forum_config"]["stage2"]}, "binding_checks": True})
    critic = run_forum.build_prompt(agent(repo, "critic"), 32, 32)
    assert "- **Null result becomes the paper**: yes" in critic
    assert "- **Decision rule**: Pursue if the interaction CI excludes zero." in critic


def test_critic_archive_rule_keys_the_null_paper_exception_on_a_visible_line(repo):
    """V-03: the Critic's archive definition no longer keys the null-paper
    exception on the hidden null_paper field. It names the arc-block line,
    which is shown only while it can apply."""
    critic = agent(repo, "critic")["prompt"]
    archive = critic.split("- **archive** means", 1)[1].split("\n", 1)[0]
    assert "provide for a null paper" not in archive and "null_paper" not in archive
    assert '"Null result becomes the paper" as yes' in archive
    open_arc(repo.base, null_paper="yes")
    assert "- **Null result becomes the paper**" not in run_forum.build_prompt(agent(repo, "critic"), 32, 32)
    repo.config(stage2={**{k: False for k in repo.agents["forum_config"]["stage2"]}, "binding_checks": True})
    assert "- **Null result becomes the paper**: yes" in run_forum.build_prompt(agent(repo, "critic"), 32, 32)


def test_existing_articles_list_papers_only(repo):
    """E2E-14: the April conference proceedings and the Arc 2 reflection
    report have no source_round and are not papers."""
    arts = repo.base / "articles"
    (arts / "2026-08-24_r30.md").write_text('---\ntitle: "No Gap to Close"\nsource_round: 30\n'
                                            'status: "draft"\n---\n')
    (arts / "conference_1_2026-04-19.md").write_text('---\ntitle: "KNA Research Agents Conference #1"\n---\n')
    (arts / "post_conference_reflection_2026-04-20.md").write_text(
        '---\ntitle: "Post-Conference Reflection Report: Commitments for Arc 2"\n---\n')
    block = run_forum.get_existing_articles()
    assert '- Round 30: "No Gap to Close" [draft]' in block
    assert "Conference" not in block and "Reflection" not in block and "Round :" not in block
    open_arc(repo.base)
    prompt = run_forum.build_prompt(agent(repo, "critic"), 32, 32)
    assert "Commitments for Arc 2" not in prompt and "Round :" not in prompt


def test_stage2_addenda_are_injected_only_for_flags_that_are_on(repo):
    open_arc(repo.base)
    repo.config(stage2={**{k: False for k in repo.agents["forum_config"]["stage2"]}, "binding_checks": True})
    critic = run_forum.build_prompt(agent(repo, "critic"), 32, 32)
    assert "## Binding Checks (Stage 2)" in critic
    assert "## Precheck Results (Stage 2)" not in critic
    scout = run_forum.build_prompt(agent(repo, "literature_scout"), 32, 32)
    assert "Stage 2" not in scout


def test_prompt_manifest_lists_injected_blocks(repo):
    open_arc(repo.base)
    manifest = []
    run_forum.build_prompt(agent(repo, "critic"), 32, 32, manifest=manifest)
    labels = {m["label"] for m in manifest}
    assert {"agent_prompt", "task", "arc_block"} <= labels
    assert all("sha256" in m for m in manifest)


def test_stage2_hooks_do_nothing_when_flags_are_off(repo, monkeypatch):
    import claim_sheet
    import prechecks
    import prediction_card
    import taxonomy_monitor

    def boom(*a, **k):
        raise AssertionError("a Stage 2 hook ran with its flag off")

    for mod, name in ((prediction_card, "commit_card"), (prediction_card, "extract_card"),
                      (prediction_card, "ingest_results"), (prechecks, "run_all"),
                      (claim_sheet, "build"), (taxonomy_monitor, "annotate_arc_opening")):
        monkeypatch.setattr(mod, name, boom)
    legacy_forum(repo.base)
    open_arc(repo.base)
    repo.plan(round31_steps(repo))
    assert run_main(["--resume"]) == 0
    assert not (repo.k / "prediction_cards").exists()


def test_stage2_invalid_card_gets_one_fix_run_then_stops_before_the_analyst(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    repo.config(stage2={**{k: False for k in repo.agents["forum_config"]["stage2"]}, "prediction_cards": True})
    steps = round31_steps(repo)
    repo.plan([steps[0], {"mode": "ok"}, steps[1]])   # Scout without a card, then a fix run that fixes nothing
    assert run_main(["--resume"]) == 1
    assert len(repo.calls()) == 2                    # the Analyst never started
    assert "did not validate" in repo.calls()[1]["argv"][-1]
    status = json.loads((repo.k / "arc_status.json").read_text())
    assert status["last_failure"]["failure"] == "round_stopped"
    assert "no valid card" in status["last_failure"]["reason"]
    assert (repo.forum / "091_literature_scout.md").exists()
    assert not (repo.forum / "092_data_analyst.md").exists()


# --------------------------------------------------------------------------- shipped defaults

CONTRACT_STAGE2_KEYS = {"prediction_cards", "binding_checks", "prechecks", "claim_sheet_first", "premise_check",
                        "gap_c_quotes", "annotator", "disclosure_appendix"}
D11_SWITCHES = ("min_tests_before_draft", "null_paper_path", "closed_no_paper")
CRITIC_FORBIDDEN = re.compile(
    r"(?i)bridge[ _-]?cap|bridge share|entropy|min_arc_rounds|arc depth|cap research_novelty"
    r"|\b(?:two|three|four|five|\d+)[ -]rounds?\b|\bround \d+\b|rounds? before (?:a )?draft")


def test_shipped_agents_json_pins_the_standing_constraints():
    """FID-F14: the real agents.json (read only) ships Stage 1. Every Stage 2
    flag is off, the posting order is Scout, Analyst, Critic with exactly
    three agents, the model is the pinned full id, and the Critic prompt has
    no monitor numbers, bridge cap or round counts."""
    data = json.loads((ROOT / "agents.json").read_text(encoding="utf-8"))
    fc = data["forum_config"]
    assert fc["model"] == "claude-opus-5-5"
    assert set(fc["stage2"]) == CONTRACT_STAGE2_KEYS
    assert all(v is False for v in fc["stage2"].values()), fc["stage2"]
    assert fc.get("blind_opening_analyst", False) is False
    for k in D11_SWITCHES:
        assert not fc.get(k), k
    assert fc.get("auto_draft_on_pursue") is False          # run_arc drafts, one arc one paper
    assert fc["round_order"] == list(forum_index.ROLE_ORDER) == ["literature_scout", "data_analyst", "critic"]
    agents = data["agents"]
    assert len(agents) == 3 and sorted(a["id"] for a in agents) == sorted(forum_index.ROLE_ORDER)
    assert {a["id"]: a.get("effort") for a in agents} == {"literature_scout": "medium", "data_analyst": "high",
                                                           "critic": "high"}
    for a in agents:
        assert set(a.get("stage2_addenda") or {}) <= set(fc["stage2"]), a["id"]
    critic = next(a for a in agents if a["id"] == "critic")
    hits = [m.group(0) for m in CRITIC_FORBIDDEN.finditer(critic["prompt"])]
    assert hits == [], hits


# --------------------------------------------------------------------------- A2 data pitfall flags

ANALYST_WITH_PITFALL = ANALYST_TEXT + """
```python
import pandas as pd
m = pd.read_parquet(f"{D}/members_21.parquet")
m["first_term"] = (m["reelection"] == "초선").astype(int)
panel = bills.merge(m, on="member_name")
```
"""


def test_analyst_pitfalls_are_logged_and_flagged_to_the_critic(repo):
    """A2: after the Analyst post the orchestrator scans its code blocks
    against knowledge/data_pitfalls.md, logs the matches, and the Critic's
    prompt carries a 'Data pitfall flags' block naming them (flag only, the
    round still runs to its Critic post and summary)."""
    legacy_forum(repo.base)
    open_arc(repo.base)
    steps = round31_steps(repo)
    steps[1] = step_write(repo.forum / "092_data_analyst.md", ANALYST_WITH_PITFALL)
    repo.plan(steps)
    assert run_main(["--resume"]) == 0
    rows = [json.loads(line) for line in (repo.k / "pitfall_flags.jsonl").read_text().splitlines()]
    assert len(rows) == 1 and rows[0]["post"] == "092_data_analyst.md" and rows[0]["round"] == 31
    assert {h["id"] for h in rows[0]["hits"]} == {"reelection_lifetime_count", "name_keyed_merge"}
    critic_argv = repo.calls()[2]["argv"]
    prompt = Path(critic_argv[critic_argv.index("--system-prompt-file") + 1]).read_text(encoding="utf-8")
    assert "## Data pitfall flags" in prompt and "reelection_lifetime_count" in prompt
    assert "kna_seniority.term_number" in prompt and "name_keyed_merge" in prompt
    scout_argv = repo.calls()[0]["argv"]
    scout_prompt = Path(scout_argv[scout_argv.index("--system-prompt-file") + 1]).read_text(encoding="utf-8")
    assert "Data pitfall flags" not in scout_prompt
    side = json.loads(claude_cli.find_sidecar("r31_data_analyst_t2").read_text(encoding="utf-8"))
    assert {h["id"] for h in side["pitfall_flags"]} == {"reelection_lifetime_count", "name_keyed_merge"}


def test_clean_analyst_post_gives_the_critic_no_flag_block(repo):
    legacy_forum(repo.base)
    open_arc(repo.base)
    keyed_post(repo.base, 91, "literature_scout", 31)
    keyed_post(repo.base, 92, "data_analyst", 31, "```python\npanel = bills.merge(m, on=\"mona_cd\")\n```")
    manifest = []
    text = run_forum.build_prompt(agent(repo, "critic"), 31, 31, manifest=manifest)
    assert "Data pitfall flags" not in text and "data_pitfall_flags" not in {m["label"] for m in manifest}
    keyed_post(repo.base, 92, "data_analyst", 31, "```r\nleft_join(b, m, by = \"member_name\")\n```")
    manifest = []
    text = run_forum.build_prompt(agent(repo, "critic"), 31, 31, manifest=manifest)
    assert "## Data pitfall flags" in text and "data_pitfall_flags" in {m["label"] for m in manifest}
    assert not (repo.k / "pitfall_flags.jsonl").exists()       # building a prompt logs nothing


def test_shipped_analyst_prompt_carries_the_pitfall_reminder():
    data = json.loads((ROOT / "agents.json").read_text(encoding="utf-8"))
    analyst = next(a for a in data["agents"] if a["id"] == "data_analyst")["prompt"]
    assert "Pitfall reminder." in analyst and "kna_seniority.term_number" in analyst
    assert "never from `reelection`" in analyst
    assert data["forum_config"]["effort_by_task"]["gate_draft"] == "high"
    assert data["forum_config"]["tools_by_task"]["gate_draft"] == []


# --------------------------------------------------------------------------- A1 data pin

def test_changed_data_refuses_the_round_before_any_agent(repo, monkeypatch):
    legacy_forum(repo.base)
    open_arc(repo.base)
    data = Path(run_forum.os.environ["KBL_DATA"])
    (data / "members_22.parquet").write_bytes(b"v1")
    run_forum._HASH_CACHE.clear()
    run_forum.check_data_pin()                                   # pinned (late) on v1
    (data / "members_22.parquet").write_bytes(b"v2 of the data")
    repo.plan(round31_steps(repo))
    assert run_main(["--resume"]) == 1
    assert repo.calls() == []                                    # no agent started
    status = json.loads((repo.k / "arc_status.json").read_text())
    assert status["data_pin_refused"]["changes"] == ["changed members_22.parquet (size 2 to 14 bytes)"]
    # --allow-data-change runs the round on the new data, on the record.
    assert run_main(["--resume", "--allow-data-change"]) == 0
    status = json.loads((repo.k / "arc_status.json").read_text())
    assert "data_pin_refused" not in status and status["allow_data_change"][-1]["by"] == "--allow-data-change"
    assert (repo.forum / "093_critic.md").exists()


def test_data_pin_is_checked_again_before_each_later_round(repo):
    """With --rounds 2 the second round is checked too: data that change
    while R31 runs refuse R32 before any of its agents starts."""
    legacy_forum(repo.base)
    open_arc(repo.base)
    data = Path(run_forum.os.environ["KBL_DATA"])
    (data / "members_22.parquet").write_bytes(b"v1")
    run_forum._HASH_CACHE.clear()
    run_forum.check_data_pin()                                   # pinned (late) on v1
    steps = round31_steps(repo)
    steps[-1]["write"].append([str(data / "members_22.parquet"), "v2 written during R31"])
    repo.plan(steps)
    assert run_main(["--resume", "--rounds", "2"]) == 1
    assert len(repo.calls()) == 4                                # R31 ran in full, R32 never started
    assert (repo.base / "summaries" / "round_31.md").exists()
    assert not (repo.forum / "094_literature_scout.md").exists()
    status = json.loads((repo.k / "arc_status.json").read_text())
    assert status["data_pin_refused"]["changes"] == ["changed members_22.parquet (size 2 to 21 bytes)"]

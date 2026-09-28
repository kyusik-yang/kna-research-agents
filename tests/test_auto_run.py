"""auto_run.sh and the publish gate for its model-written pushes (E2E-04).

The conference proceedings and the agora discussions are written by a model
and pushed by cron. They pass the leak lint (blocking on absolute home or
volume paths, as paper gate G6) and the G4 overclaim lint before any commit,
and a failing file is moved to workspace/failed_drafts/.

Python tests call generate_conference with every path in tmp_path and
claude_cli.run_claude replaced. Shell tests run a copy of auto_run.sh in
tmp_path with a fake git, fake child scripts and a stub claude_cli module, so
no model runs, nothing touches the real repository and the schedule files
live in a scratch KNA_AUTO_STATE_DIR (never /tmp/kna-*)."""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import claude_cli  # noqa: E402
import generate_conference as gc  # noqa: E402
import paper_gates  # noqa: E402

LEAK = "The data sit in /Users/someone/Desktop/private-notes/kna.parquet for now."
CLEAN = "# KNA Research Agents Conference #1\n\nFirst-term members pass fewer bills.\n"


# ---------------------------------------------------------------------------
# Python: the gate inside generate_conference and gate_pending
# ---------------------------------------------------------------------------

@pytest.fixture
def conf(tmp_path, monkeypatch):
    for name, sub in {"BASE_DIR": "", "ARTICLES_DIR": "articles", "SUMMARIES_DIR": "summaries",
                      "ARCHIVE_DIR": "forum_archive", "WORKSPACE_DIR": "workspace",
                      "KNOWLEDGE_DIR": "knowledge", "FORUM_DIR": "forum",
                      "FAILED_DRAFTS_DIR": "workspace/failed_drafts"}.items():
        monkeypatch.setattr(gc, name, tmp_path / sub if sub else tmp_path)
    monkeypatch.setattr(paper_gates, "REPLICATION_DIR", tmp_path / "replication")
    monkeypatch.setenv("KNA_LEAK_PATTERNS", str(tmp_path / "no_private_patterns.txt"))
    state = SimpleNamespace(root=tmp_path, text=CLEAN, failure="ok")

    def fake_run_claude(task, prompt, **kw):
        assert task == "conference"
        if state.failure == "ok":
            Path(kw["expect_file"]).write_text(state.text, encoding="utf-8")
        return SimpleNamespace(failure=state.failure, resume_at=None, run_id="stub", ok=state.failure == "ok")
    monkeypatch.setattr(claude_cli, "run_claude", fake_run_claude)
    return state


def _quarantined(root: Path) -> list[Path]:
    d = root / "workspace" / "failed_drafts"
    return sorted(p for p in d.iterdir()) if d.exists() else []


def test_clean_conference_is_kept(conf):
    path = gc.generate_conference(1)
    assert path is not None and path.parent == conf.root / "articles" and path.exists()
    assert _quarantined(conf.root) == []


@pytest.mark.parametrize("text,gate", [
    (CLEAN + LEAK, "G6"),
    # The % must not hide the rest of the line from the overclaim lint.
    (CLEAN + "Turnout rose 12% and the design was pre-registered.\n", "G4"),
    (CLEAN + "Code is in the replication package at replication/arc_6.\n", "G4"),
])
def test_conference_that_fails_the_gate_is_quarantined(conf, text, gate):
    conf.text = text
    with pytest.raises(SystemExit) as e:
        gc.generate_conference(1)
    assert e.value.code == gc.EXIT_GATES == 2
    assert list((conf.root / "articles").glob("conference_*.md")) == []
    [q] = _quarantined(conf.root)
    assert q.name.startswith("conference_1_") and list(q.glob("conference_1_*.md"))
    failed = json.loads((q / "FAILED.json").read_text(encoding="utf-8"))
    assert failed["failed_blocking"] == [gate] and failed["failing_items"]
    assert (q / "gates.json").exists()


def test_replication_claim_passes_with_a_verified_package(conf):
    pkg = conf.root / "replication" / "arc_6"
    pkg.mkdir(parents=True)
    (pkg / "MANIFEST.json").write_text(json.dumps({"arc": 6, "build": {"ok": True},
                                                   "verify": {"passed": True}}), encoding="utf-8")
    conf.text = CLEAN + "Code is in the replication package at replication/arc_6.\n"
    assert gc.generate_conference(1).exists()


def test_flag_only_leak_hits_do_not_block(conf):
    conf.text = CLEAN + "See ~/Desktop/ for nothing in particular.\n"      # desktop_path is a flag in G6
    assert gc.generate_conference(1).exists()


def test_usage_limit_exits_75_and_writes_nothing(conf):
    conf.failure = "usage_limit"
    with pytest.raises(SystemExit) as e:
        gc.generate_conference(1)
    assert e.value.code == claude_cli.EXIT_USAGE_LIMIT
    assert _quarantined(conf.root) == []


def _discussion(d: Path, stem: str, text: str) -> list[Path]:
    d.mkdir(parents=True, exist_ok=True)
    js, md = d / f"{stem}.json", d / f"{stem}.md"
    js.write_text(json.dumps({"stimulus": text, "report": text}, ensure_ascii=False), encoding="utf-8")
    md.write_text(f"# Yeouido Agora\n\n{text}\n", encoding="utf-8")
    return [js, md]


def test_gate_pending_quarantines_only_the_failing_discussion(conf, monkeypatch):
    d = conf.root / "agora" / "discussions"
    bad = _discussion(d, "2026-09-26_0900_bad_._", LEAK)
    good = _discussion(d, "2026-09-26_0910_good", "시민 반응 요약")
    monkeypatch.setattr(gc, "pending_files", lambda directory: sorted(bad + good))
    assert gc.gate_pending(d, "agora") == 2
    assert all(p.exists() for p in good) and not any(p.exists() for p in bad)
    [q] = _quarantined(conf.root)
    assert q.name == "agora_2026-09-26_0900_bad_._"
    assert sorted(p.name for p in q.glob("*_bad_._.*")) == sorted(p.name for p in bad)

    monkeypatch.setattr(gc, "pending_files", lambda directory: sorted(good))
    assert gc.gate_pending(d, "agora") == 0


def test_pending_files_reads_git_status_z(conf, monkeypatch):
    d = conf.root / "agora" / "discussions"
    d.mkdir(parents=True)
    for name in ("a b,._.md", "new.json", "changed.md"):
        (d / name).write_text("x", encoding="utf-8")
    out = ("?? agora/discussions/a b,._.md\0R  agora/discussions/new.json\0agora/discussions/old.json\0"
           " M agora/discussions/changed.md\0 D agora/discussions/gone.md\0").encode()
    seen = []

    def fake_run(cmd, **kw):
        seen.append((cmd, kw.get("cwd")))
        return SimpleNamespace(returncode=0, stdout=out, stderr=b"")
    monkeypatch.setattr(gc.subprocess, "run", fake_run)
    got = sorted(p.name for p in gc.pending_files(d))
    assert got == ["a b,._.md", "changed.md", "new.json"]
    assert seen[0][0][-1] == "agora/discussions" and seen[0][1] == str(conf.root.resolve())


def test_pending_files_raises_when_git_fails(conf, monkeypatch):
    def failing(cmd, **kw):
        raise subprocess.CalledProcessError(128, cmd)
    monkeypatch.setattr(gc.subprocess, "run", failing)
    with pytest.raises(subprocess.CalledProcessError):
        gc.pending_files(conf.root / "agora" / "discussions")


# ---------------------------------------------------------------------------
# Shell: auto_run.sh in a scratch copy
# ---------------------------------------------------------------------------

FAKE_GIT = r'''#!/usr/bin/env python3
"""Fake git: logs every call. status lists every file under the pathspec as untracked."""
import json, os, sys
from pathlib import Path
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps({"git": sys.argv[1:]}) + "\n")
args = sys.argv[1:]
if args and args[0] == "status" and os.environ.get("FAKE_GIT_STATUS_FAIL") == "1":
    sys.stderr.write("fatal: unable to read index\n")
    sys.exit(128)
if args and args[0] == "status":
    spec = args[args.index("--") + 1] if "--" in args else "."
    out = []
    for p in sorted(Path(spec).rglob("*")):
        if p.is_file():
            out.append("?? " + p.as_posix())
    sys.stdout.write("".join(e + "\0" for e in out))
'''

FAKE_LOGGER = r'''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
disc = sorted(p.name for p in Path("agora/discussions").glob("*")) if Path("agora/discussions").exists() else []
with open(os.environ["FAKE_LOG"], "a", encoding="utf-8") as f:
    f.write(json.dumps({"script": Path(sys.argv[0]).name, "argv": sys.argv[1:], "discussions": disc}) + "\n")
'''

FAKE_AGORA = FAKE_LOGGER + r'''
d = Path("agora/discussions")
d.mkdir(parents=True, exist_ok=True)
text = os.environ.get("AGORA_TEXT", "")
(d / "2026-09-26_0900_topic.json").write_text(json.dumps({"stimulus": text}, ensure_ascii=False), encoding="utf-8")
(d / "2026-09-26_0900_topic.md").write_text("# Yeouido Agora\n\n" + text + "\n", encoding="utf-8")
if os.environ.get("AGORA_EXIT"):
    sys.exit(int(os.environ["AGORA_EXIT"]))   # a run that fails after writing its files
'''

FAKE_STIMULUS = FAKE_LOGGER + r'''
print("여야, 선거제 개편안 논의")
'''

# Stands in for claude_cli inside the scratch copy (no model, no config).
STUB_CLAUDE_CLI = r'''import os
from pathlib import Path
from types import SimpleNamespace
EXIT_USAGE_LIMIT = 75

def run_claude(task, prompt_text, **kw):
    if os.environ.get("STUB_MODE") == "usage_limit":
        return SimpleNamespace(failure="usage_limit", resume_at=None, run_id="stub", ok=False)
    Path(kw["expect_file"]).write_text(os.environ.get("CONF_TEXT", "# Conference\n"), encoding="utf-8")
    return SimpleNamespace(failure="ok", resume_at=None, run_id="stub", ok=True)
'''


class Shell:
    def __init__(self, tmp: Path):
        self.repo = tmp / "repo"
        self.state = tmp / "state"
        self.bin = tmp / "bin"
        self.log = tmp / "fake.log"
        for d in (self.repo / "agora", self.repo / "scripts", self.repo / "articles", self.state, self.bin):
            d.mkdir(parents=True, exist_ok=True)
        for name in ("auto_run.sh", "generate_conference.py", "paper_gates.py", "leak_lint.py"):
            shutil.copy2(ROOT / name, self.repo / name)
        (self.repo / "claude_cli.py").write_text(STUB_CLAUDE_CLI, encoding="utf-8")
        (self.repo / "build_site.py").write_text(FAKE_LOGGER, encoding="utf-8")
        (self.repo / "run_arc.py").write_text(FAKE_LOGGER, encoding="utf-8")
        (self.repo / "agora" / "run_agora.py").write_text(FAKE_AGORA, encoding="utf-8")
        (self.repo / "scripts" / "agora_stimulus.py").write_text(FAKE_STIMULUS, encoding="utf-8")
        git = self.bin / "git"
        git.write_text(FAKE_GIT, encoding="utf-8")
        git.chmod(0o755)
        py = self.bin / "python3"
        py.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
        py.chmod(0o755)

    def summaries(self, n: int):
        d = self.repo / "summaries"
        d.mkdir(exist_ok=True)
        for i in range(1, n + 1):
            (d / f"round_{i:02d}.md").write_text(f"# Round {i}\n", encoding="utf-8")

    def run(self, mode: str, **env) -> int:
        e = {k: v for k, v in os.environ.items() if not k.startswith(("KNA_", "STUB_"))}
        e.update(PATH=f"{self.bin}{os.pathsep}{e.get('PATH', '')}", KNA_AUTO_STATE_DIR=str(self.state),
                 FAKE_LOG=str(self.log), KNA_LEAK_PATTERNS=str(self.state / "none.txt"), **env)
        return subprocess.run(["bash", str(self.repo / "auto_run.sh"), mode], env=e, cwd=str(self.repo),
                              capture_output=True, text=True, timeout=120).returncode

    def events(self) -> list[dict]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines() if line]

    def git_verbs(self) -> list[str]:
        return [e["git"][0] for e in self.events() if "git" in e and e["git"][0] != "status"]

    def scripts(self) -> list[str]:
        return [e["script"] for e in self.events() if "script" in e]

    def quarantined(self) -> list[str]:
        d = self.repo / "workspace" / "failed_drafts"
        return sorted(p.name for p in d.iterdir()) if d.exists() else []


@pytest.fixture
def sh(tmp_path):
    return Shell(tmp_path)


def test_agora_discussion_with_a_home_path_is_quarantined_before_the_build(sh):
    assert sh.run("agora", AGORA_TEXT=LEAK) == 0
    assert sh.quarantined() == ["agora_2026-09-26_0900_topic"]
    assert not list((sh.repo / "agora" / "discussions").glob("*_topic.*"))
    build = next(e for e in sh.events() if e.get("script") == "build_site.py")
    assert build["discussions"] == []                   # the site never saw the leaked file
    assert sh.git_verbs() == ["add", "commit", "push"]  # the automation keeps running
    assert (sh.state / "kna-last-agora.txt").exists()   # schedule state stays in the scratch folder
    assert "quarantined" in (sh.state / "kna-auto-agora.log").read_text(encoding="utf-8")


def test_clean_agora_discussion_is_published(sh):
    assert sh.run("agora", AGORA_TEXT="시민들은 선거제 개편에 찬반이 갈렸다.") == 0
    assert sh.quarantined() == []
    build = next(e for e in sh.events() if e.get("script") == "build_site.py")
    assert build["discussions"] == ["2026-09-26_0900_topic.json", "2026-09-26_0900_topic.md"]
    assert sh.git_verbs() == ["add", "commit", "push"]


def test_conference_that_fails_the_gate_is_never_built_committed_or_pushed(sh):
    sh.summaries(20)                                    # the counter reaches the threshold of 20
    assert sh.run("forum", CONF_TEXT=CLEAN + LEAK) == 0
    assert [q.startswith("conference_1_") for q in sh.quarantined()] == [True]
    assert list((sh.repo / "articles").glob("conference_*.md")) == []
    assert "build_site.py" not in sh.scripts() and sh.git_verbs() == []
    assert "failed the publish gate" in (sh.state / "kna-auto-forum.log").read_text(encoding="utf-8")


def test_clean_conference_is_built_committed_and_pushed(sh):
    sh.summaries(20)
    assert sh.run("forum", CONF_TEXT=CLEAN) == 0
    today = datetime.now().strftime("%Y-%m-%d")
    assert (sh.repo / "articles" / f"conference_1_{today}.md").exists()
    assert sh.scripts() == ["build_site.py"] and sh.git_verbs() == ["add", "commit", "push"]
    add = next(e["git"] for e in sh.events() if e.get("git", [None])[0] == "add")
    assert add == ["add", "articles/", "docs/"]


def test_conference_usage_limit_stops_with_75(sh):
    sh.summaries(20)
    assert sh.run("forum", STUB_MODE="usage_limit") == 75
    assert "build_site.py" not in sh.scripts() and sh.git_verbs() == []


@pytest.mark.parametrize("state,launched", [("running", True), ("stopped", False), ("paused", False)])
def test_forum_step_launches_run_arc_only_while_running(sh, state, launched):
    """E2E-02: run_arc leaves the arc running after a step that decides
    continue, and auto_run.sh launches the next step only in that state."""
    know = sh.repo / "knowledge"
    know.mkdir()
    (know / "active_arc.json").write_text(json.dumps({"seed": "s", "start_round": 31}), encoding="utf-8")
    (know / "arc_status.json").write_text(json.dumps({"state": state, "action": "continue"}), encoding="utf-8")
    assert sh.run("forum") == 0
    calls = [e["argv"] for e in sh.events() if e.get("script") == "run_arc.py"]
    assert calls == ([["--max-rounds", "1"]] if launched else [])


def test_interval_check_skips_a_recent_run(sh):
    (sh.state / "kna-last-forum.txt").write_text(str(int(datetime.now().timestamp())), encoding="utf-8")
    assert sh.run("forum") == 0
    assert sh.events() == []
    assert "Skipping forum" in (sh.state / "kna-auto-forum.log").read_text(encoding="utf-8")


def test_conference_quarantined_twice_is_not_regenerated_on_every_tick(sh):
    """V-08a: quarantined proceedings do not raise the conference count, so
    each conference number gets at most two model calls, not one per tick."""
    sh.summaries(20)
    for _ in range(3):
        (sh.state / "kna-last-forum.txt").unlink(missing_ok=True)   # past the 4-day interval
        assert sh.run("forum", CONF_TEXT=CLEAN + LEAK) == 0
    assert [q.startswith("conference_1_") for q in sh.quarantined()] == [True, True]
    log = (sh.state / "kna-auto-forum.log").read_text(encoding="utf-8")
    assert log.count("generating conference #1") == 2 and "Not regenerating" in log
    assert list((sh.repo / "articles").glob("conference_*.md")) == []
    assert "build_site.py" not in sh.scripts() and sh.git_verbs() == []


def test_agora_gate_error_moves_this_runs_ungated_files_aside(sh):
    """V-08b: when the gate itself fails (a git error, exit 1), the files this
    run wrote leave agora/discussions/, so a later run_arc build cannot render
    and push them. Files that were there before the run stay."""
    d = sh.repo / "agora" / "discussions"
    d.mkdir(parents=True)
    (d / "2026-09-20_0900_old.md").write_text("# Yeouido Agora\n\nPublished earlier.\n", encoding="utf-8")
    assert sh.run("agora", AGORA_TEXT="시민 반응 요약", FAKE_GIT_STATUS_FAIL="1") == 1
    assert sorted(p.name for p in d.iterdir()) == ["2026-09-20_0900_old.md"]
    [q] = sh.quarantined()
    assert q.startswith("agora_ungated_")
    moved = sh.repo / "workspace" / "failed_drafts" / q
    assert sorted(p.name for p in moved.glob("*_topic.*")) == ["2026-09-26_0900_topic.json",
                                                                  "2026-09-26_0900_topic.md"]
    failed = json.loads((moved / "FAILED.json").read_text(encoding="utf-8"))
    assert "gate exited 1" in failed["reason"] and len(failed["files"]) == 2
    assert "build_site.py" not in sh.scripts() and sh.git_verbs() == []


def test_forum_wait_line_names_a_signed_entry_not_the_researcher(sh):
    """V-04: under D-10 the orchestrating session may sign gate entries, so
    the script and its cron log never say researcher-signed."""
    assert "researcher-signed" not in (ROOT / "auto_run.sh").read_text(encoding="utf-8")
    assert sh.run("forum") == 0
    log = (sh.state / "kna-auto-forum.log").read_text(encoding="utf-8")
    assert "Waiting for a signed topic_gate entry." in log and "researcher" not in log


@pytest.mark.parametrize("code", [1, 75])
def test_failed_agora_run_moves_its_partial_files_aside(sh, code):
    """V-08b: a run_agora failure (75 is a usage limit) leaves no ungated
    discussion in agora/discussions/ for a later build to publish."""
    assert sh.run("agora", AGORA_TEXT="시민 반응 요약", AGORA_EXIT=str(code)) == code
    d = sh.repo / "agora" / "discussions"
    assert list(d.iterdir()) == []
    [q] = sh.quarantined()
    assert q.startswith("agora_ungated_")
    assert "build_site.py" not in sh.scripts() and sh.git_verbs() == []

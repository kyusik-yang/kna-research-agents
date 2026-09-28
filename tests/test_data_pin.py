"""Data version pinning (A1): the arc pins a fingerprint of $KBL_DATA when it
opens, every round recomputes it, and a change refuses the round unless
--allow-data-change is passed (recorded). Every path points into tmp_path, and
KBL_DATA is a scratch folder of small files."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import claude_cli  # noqa: E402
import run_forum  # noqa: E402

SEED = "First-term seniority and bill passage in the 22nd Assembly"
GATE = f"""# Topic Gate

## R31 - Arc 6 opening

seed: {SEED}

identification: within-assembly comparison.

exclusion_criteria: (X1) no productivity counts

prior: First-term members' bills pass less often in year one.

falsifier: The year-one gap is inside plus or minus 1 point.

drafted_by: automatic gate drafter (auto_arc.py gate_draft call, claude-opus-5-5)

signed_by: auto_arc.py automatic selector, signed under the researcher's standing delegation of 2026-09-25

signed: 2026-09-26
"""


@pytest.fixture
def pin(tmp_path, monkeypatch):
    base = tmp_path / "repo"
    know = base / "knowledge"
    know.mkdir(parents=True)
    (base / "forum").mkdir()
    (base / "agents.json").write_text(json.dumps({"season": 2, "forum_config": {"model": "claude-opus-5-5"},
                                                  "agents": []}), encoding="utf-8")
    (base / "topic_gate.md").write_text(GATE, encoding="utf-8")
    for name, rel in {"BASE_DIR": "", "FORUM_DIR": "forum", "KNOWLEDGE_DIR": "knowledge",
                      "LOGS_DIR": "logs", "AGENTS_FILE": "agents.json", "TOPIC_GATE_FILE": "topic_gate.md",
                      "ACTIVE_ARC_FILE": "knowledge/active_arc.json",
                      "ARC_STATUS_FILE": "knowledge/arc_status.json",
                      "GATE_EVENTS_FILE": "knowledge/gate_events.jsonl",
                      "GATE_CANDIDATES_FILE": "knowledge/gate_candidates.jsonl",
                      "HUMAN_CONTEXT_FILE": "knowledge/human_context.md",
                      "ARCHIVE_DIR": "knowledge/archive"}.items():
        monkeypatch.setattr(run_forum, name, base / rel if rel else base)
    monkeypatch.setattr(claude_cli, "BASE_DIR", base)
    import forum_index
    monkeypatch.setattr(forum_index, "FORUM_DIR", base / "forum")
    monkeypatch.setattr(run_forum, "PREVIEW_ARC", None)
    alerts = []
    monkeypatch.setattr(claude_cli, "notify", lambda title, msg: alerts.append((title, msg)))
    data = tmp_path / "kbl"
    data.mkdir()
    (data / "members_22.parquet").write_bytes(b"PAR1 members 22 PAR1")
    (data / "ideal_points_bridged.csv").write_text("member_id,bridged_1d\n1,0.5\n", encoding="utf-8")
    (data / "ideal_points_manifest.json").write_text("{}", encoding="utf-8")   # not a data file
    monkeypatch.setenv("KBL_DATA", str(data))
    run_forum._HASH_CACHE.clear()

    class P:
        pass
    p = P()
    p.base, p.know, p.data, p.alerts = base, know, data, alerts
    p.arc = lambda: json.loads((know / "active_arc.json").read_text(encoding="utf-8"))
    p.status = lambda: json.loads((know / "arc_status.json").read_text(encoding="utf-8"))
    p.events = lambda: [json.loads(x) for x in (know / "gate_events.jsonl").read_text().splitlines()]
    return p


def _touch(p, name="members_22.parquet", text=b"PAR1 members 22 refreshed PAR1"):
    (p.data / name).write_bytes(text)


def test_fingerprint_hashes_data_files_only_and_records_no_path(pin):
    fp = run_forum.data_fingerprint()
    assert sorted(fp["files"]) == ["ideal_points_bridged.csv", "members_22.parquet"] and fp["n_files"] == 2
    assert fp["id"].startswith("kbl-") and len(fp["id"]) == 16
    assert str(pin.data) not in json.dumps(fp) and "/Users/" not in json.dumps(fp)
    assert run_forum.data_fingerprint()["id"] == fp["id"]
    _touch(pin)
    new = run_forum.data_fingerprint()
    assert new["id"] != fp["id"]
    assert run_forum.data_changes(fp, new) == [
        "changed members_22.parquet (size 20 to 30 bytes)"]
    (pin.data / "extra.csv").write_text("a\n", encoding="utf-8")
    (pin.data / "ideal_points_bridged.csv").unlink()
    assert run_forum.data_changes(new, run_forum.data_fingerprint()) == [
        "added extra.csv", "removed ideal_points_bridged.csv"]


def test_fingerprint_records_the_kna_data_commit(pin, monkeypatch):
    env = {"GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "GIT_AUTHOR_NAME": "t",
           "GIT_AUTHOR_EMAIL": "t@example.org", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.org"}
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    for cmd in (["init", "-q"], ["add", "."], ["commit", "-q", "-m", "data"]):
        subprocess.run(["git", "-C", str(pin.data), *cmd], check=True, capture_output=True)
    fp = run_forum.data_fingerprint()
    head = subprocess.run(["git", "-C", str(pin.data), "rev-parse", "HEAD"], capture_output=True,
                          text=True).stdout.strip()
    assert fp["kna_git_commit"] == head and fp["kna_git_dirty"] is False
    _touch(pin)
    assert run_forum.data_fingerprint()["kna_git_dirty"] is True


def test_no_kbl_data_means_no_fingerprint(pin, monkeypatch):
    monkeypatch.delenv("KBL_DATA")
    assert run_forum.data_fingerprint() is None


def test_arc_open_pins_the_data_and_exposes_it_for_the_drafter(pin):
    run_forum.check_topic_gate(SEED, 31, 90)
    arc = pin.arc()
    fp = arc["data_fingerprint"]
    assert fp["id"] == run_forum.data_fingerprint()["id"] and fp["n_files"] == 2
    st = pin.status()["data_fingerprint"]
    assert st["id"] == fp["id"] and st["changes"] == [] and st["pinned_late"] is False
    assert fp["id"] in st["statement"] and "recorded when the arc opened" in st["statement"]
    assert ";" not in st["statement"] and "—" not in st["statement"]
    # A relaunch of the opening round keeps the pin, even on changed data.
    _touch(pin)
    run_forum.check_topic_gate(SEED, 31, 91)
    assert pin.arc()["data_fingerprint"]["id"] == fp["id"]


def test_changed_data_refuses_the_round_and_names_the_files(pin):
    run_forum.check_topic_gate(SEED, 31, 90)
    pinned = pin.arc()["data_fingerprint"]["id"]
    assert run_forum.check_data_pin()["id"] == pinned            # unchanged: runs
    _touch(pin)
    with pytest.raises(SystemExit) as e:
        run_forum.check_data_pin()
    msg = str(e.value)
    assert "[BLOCKED · Data pin" in msg and "changed members_22.parquet" in msg
    assert "--allow-data-change" in msg and "ideal_points_bridged.csv" not in msg
    assert pin.arc()["data_fingerprint"]["id"] == pinned         # the pin is untouched
    assert pin.events()[-1]["result"] == "data_change_block"
    refused = pin.status()["data_pin_refused"]
    assert refused["pinned"] == pinned and refused["changes"] == ["changed members_22.parquet (size 20 to 30 bytes)"]
    assert pin.alerts and "data changed" in pin.alerts[-1][0]


def test_allow_data_change_is_recorded_and_repins(pin):
    run_forum.check_topic_gate(SEED, 31, 90)
    old = pin.arc()["data_fingerprint"]["id"]
    _touch(pin)
    with pytest.raises(SystemExit):
        run_forum.check_data_pin()
    new = run_forum.check_data_pin(allow_change=True)
    arc = pin.arc()
    assert arc["data_fingerprint"]["id"] == new["id"] != old
    [change] = arc["data_fingerprint_changes"]
    assert change["from"] == old and change["to"] == new["id"] and change["by"] == "--allow-data-change"
    st = pin.status()
    assert "data_pin_refused" not in st
    assert st["allow_data_change"][-1]["to"] == new["id"]
    assert st["data_fingerprint"]["id"] == new["id"] and st["data_fingerprint"]["changes"][0]["from"] == old
    assert f"from fingerprint {old} to {new['id']}" in st["data_fingerprint"]["statement"]
    assert pin.events()[-1]["result"] == "data_change_allowed"
    assert run_forum.check_data_pin()["id"] == new["id"]          # later rounds run on the new pin


def test_arc_opened_before_pinning_is_pinned_late(pin):
    (pin.know / "active_arc.json").write_text(json.dumps({"seed": SEED, "start_round": 28, "arc_id": "5"}))
    fp = run_forum.check_data_pin()
    assert fp["pinned_late"] is True and pin.arc()["data_fingerprint"]["id"] == fp["id"]
    assert pin.events()[-1]["result"] == "data_pin"
    assert "recorded after the arc had opened" in pin.status()["data_fingerprint"]["statement"]


def test_no_active_arc_is_not_checked(pin):
    assert run_forum.check_data_pin() is None
    assert not (pin.know / "gate_events.jsonl").exists()

"""Findings ledger: idempotent appends, dedupe on (round, source, finding),
duplicate check, and the one-verdict-per-Critic-post tally."""

import json
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import ledger_audit as la  # noqa: E402

ARCHIVED = ROOT / "knowledge" / "archive" / "findings_pre_dedupe_2026-09-25.jsonl"


def _original_ledger() -> Path:
    """The pre-dedupe ledger (archived copy once the dedupe has been applied)."""
    if ARCHIVED.exists():
        return ARCHIVED
    return ROOT / "knowledge" / "findings.jsonl"


ROW = {
    "finding": "Committee chairs pass their own bills more often.",
    "status": "preliminary",
    "round": 31,
    "source": "093_critic.md",
    "verdict": "revise",
}


def test_row_id_is_stable_sha1_of_key():
    a = la.row_id(ROW)
    assert len(a) == 40 and all(c in "0123456789abcdef" for c in a)
    assert la.row_id(dict(ROW, status="confirmed", verdict="pursue")) == a
    assert la.row_id(dict(ROW, round="31")) == a
    assert la.row_id(dict(ROW, round=32)) != a
    assert la.row_id(dict(ROW, source="093_data_analyst.md")) != a


def test_append_unique_twice_leaves_one_row(tmp_path):
    ledger = tmp_path / "findings.jsonl"
    assert la.append_unique(ROW, path=ledger) is True
    assert la.append_unique(dict(ROW), path=ledger) is False
    rows = la.load(ledger)
    assert len(rows) == 1
    assert rows[0]["row_id"] == la.row_id(ROW)
    assert la.append_unique(dict(ROW, round=32), path=ledger) is True
    assert len(la.load(ledger)) == 2


def test_append_unique_recognizes_legacy_rows_without_row_id(tmp_path):
    ledger = tmp_path / "findings.jsonl"
    ledger.write_text(json.dumps(ROW) + "\n", encoding="utf-8")
    assert la.append_unique(dict(ROW, status="confirmed"), path=ledger) is False
    assert len(la.load(ledger)) == 1


def test_append_unique_repairs_missing_trailing_newline(tmp_path):
    ledger = tmp_path / "findings.jsonl"
    ledger.write_text(json.dumps(dict(ROW, round=1)), encoding="utf-8")
    assert la.append_unique(ROW, path=ledger) is True
    assert len(la.load(ledger)) == 2


def test_check_and_dedupe_on_a_copy_of_the_original_ledger(tmp_path):
    src = _original_ledger()
    ledger = tmp_path / "findings.jsonl"
    shutil.copy2(src, ledger)
    original_bytes = ledger.read_bytes()

    before = la.check(ledger)
    assert before["ok"] is False
    assert before["rows"] == 1257
    assert before["unique"] == 41

    dry = la.dedupe(apply=False, path=ledger, archive_dir=tmp_path / "archive")
    assert dry["rows_after"] == 41 and dry["applied"] is False
    assert ledger.read_bytes() == original_bytes

    rep = la.dedupe(apply=True, path=ledger, archive_dir=tmp_path / "archive")
    assert rep["applied"] is True
    assert rep["rows_before"] == 1257 and rep["rows_after"] == 41
    assert rep["verdicts_after"] == {"pursue": 27, "revise": 12, "archive": 2}
    assert Path(rep["archive"]).read_bytes() == original_bytes
    assert la.check(ledger)["ok"] is True
    rows = la.load(ledger)
    assert all(r["row_id"] == la.row_id(r) for r in rows)
    assert Counter(r["verdict"] for r in rows) == Counter(pursue=27, revise=12, archive=2)

    # Idempotent: a second apply writes nothing and makes no new archive.
    again = la.dedupe(apply=True, path=ledger, archive_dir=tmp_path / "archive")
    assert again["changed"] is False and again["applied"] is False
    assert len(list((tmp_path / "archive").iterdir())) == 1


def test_dedupe_keeps_first_row_in_file_order(tmp_path):
    ledger = tmp_path / "findings.jsonl"
    rows = [dict(ROW, status="preliminary"), dict(ROW, round=1), dict(ROW, status="confirmed")]
    ledger.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    la.dedupe(apply=True, path=ledger, archive_dir=tmp_path / "archive")
    out = la.load(ledger)
    assert [r["round"] for r in out] == [31, 1]
    assert out[0]["status"] == "preliminary"


def test_archive_is_never_overwritten(tmp_path):
    ledger = tmp_path / "findings.jsonl"
    archive = tmp_path / "archive"
    for _ in range(2):
        ledger.write_text(json.dumps(ROW) + "\n" + json.dumps(ROW) + "\n", encoding="utf-8")
        la.dedupe(apply=True, path=ledger, archive_dir=archive)
    names = sorted(p.name for p in archive.iterdir())
    assert len(names) == 2
    assert any(".rev2." in n for n in names)


def test_live_ledger_has_no_duplicates():
    assert la.check()["ok"] is True


def test_cli_check_exit_codes(tmp_path):
    ledger = tmp_path / "findings.jsonl"
    ledger.write_text(json.dumps(ROW) + "\n" + json.dumps(ROW) + "\n", encoding="utf-8")
    assert la.main(["--check", "--ledger", str(ledger)]) == 1
    assert la.main(["--dedupe", "--apply", "--ledger", str(ledger)]) == 0
    assert (tmp_path / "archive").is_dir()
    assert la.main(["--check", "--ledger", str(ledger)]) == 0


def test_tally_one_verdict_per_critic_post():
    t = la.tally(verdicts_file=Path("/nonexistent/verdicts.jsonl"))
    s1 = t["seasons"]["season1"]
    assert (s1["critic_posts"], s1["pursue"], s1["revise"], s1["archive"]) == (24, 11, 12, 1)
    s2_posts = [p for p in t["posts"] if p["round"] is not None and 25 <= p["round"] <= 30]
    assert len(s2_posts) == 6
    assert Counter(p["verdict"] for p in s2_posts) == Counter(pursue=6)
    multi = {p["post"] for p in t["multi_verdict_posts"]}
    assert {"006_critic.md", "009_critic.md"} <= multi


def test_tally_prefers_verdicts_of_record(tmp_path):
    forum = tmp_path / "forum"
    forum.mkdir()
    (forum / "003_critic.md").write_text("```yaml\nverdict: revise\n```\n", encoding="utf-8")
    (forum / "006_critic.md").write_text(
        "---\nround: 26\n---\n```yaml\nverdict: pursue\n```\n", encoding="utf-8")
    vf = tmp_path / "verdicts.jsonl"
    vf.write_text(json.dumps({"round": 26, "verdict": "archive"}) + "\n", encoding="utf-8")
    t = la.tally(forum_dir=forum, verdicts_file=vf)
    by_post = {p["post"]: p for p in t["posts"]}
    assert by_post["003_critic.md"]["round"] == 1
    assert by_post["003_critic.md"]["verdict"] == "revise"
    assert by_post["006_critic.md"]["round"] == 26
    assert by_post["006_critic.md"]["verdict"] == "archive"
    assert by_post["006_critic.md"]["basis"] == "verdicts.jsonl"
    assert t["seasons"]["season2"]["archive"] == 1


PUBLIC_DOCS = ["SEASON2.md", "README.md", "CLAUDE.md", "docs/season2.html"]


def test_stale_ledger_figures_removed_from_public_docs():
    stale = []
    for rel in PUBLIC_DOCS:
        path = ROOT / rel
        if not path.exists():
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if ("1,251" in line or "2.5% pursue" in line or "(2.5%)" in line) \
                    and "erratum" not in line.lower() and "correction" not in line.lower():
                stale.append(f"{rel}:{n}")
    assert not stale, stale

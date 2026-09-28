#!/usr/bin/env python3
"""The Season 1 pursue baseline of `taxonomy_monitor.py report --legacy`
uses the deduplicated findings from Critic posts, as the SEASON2.md erratum
of 2026-09-26 does. Read-only on the real knowledge files."""

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import taxonomy_monitor as tm  # noqa: E402

LEDGER = ROOT / "knowledge" / "findings.jsonl"


def _row(i, rnd, source, opp="evidence_gap", met="empirical_mapping", op="measure"):
    return {"id": f"{i:02d}_R{rnd}_{source}", "kind": "pursue_findings", "opportunity_pattern": opp,
            "method_paradigm": met, "operation": op}


def test_baseline_keeps_first_label_per_critic_post_and_drops_other_sources():
    rows = [
        _row(1, 4, "011_critic.md"),
        _row(2, 4, "012_data_analyst.md", met="robustification"),
        _row(3, 4, "011_critic.md", met="robustification"),   # a repeat of the R4 finding
        _row(4, 5, "015_critic.md", opp="puzzle_contradiction"),
        {"id": "bad-id", "kind": "pursue_findings"},
        {"id": "05_R6_017_critic.md", "kind": "articles"},
    ]
    got = tm.legacy_pursue_baseline(rows)
    assert [r["id"] for r in got] == ["01_R4_011_critic.md", "04_R5_015_critic.md"]
    assert got[0]["method_paradigm"] == "empirical_mapping"


@pytest.mark.skipif(not tm.LEGACY_FILE.exists(), reason="legacy labels not present")
def test_real_baseline_matches_the_erratum():
    s = tm.summarize(tm.legacy_pursue_baseline())
    assert s["n"] == 13
    assert round(s["opportunity_entropy"], 2) == 0.77 and round(s["method_entropy"], 2) == 0.52
    assert s["method"] == {"empirical_mapping": 6, "robustification": 5, "relax_extend_scope": 2}


@pytest.mark.skipif(not tm.LEGACY_FILE.exists() or not LEDGER.exists(), reason="knowledge files not present")
def test_one_distinct_pursue_finding_per_critic_post_in_the_ledger():
    """The baseline keys labels on (round, Critic post). That equals the
    ledger's (round, source, finding) key only while each Critic post holds
    one distinct Season 1 pursue finding."""
    findings = {}
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("verdict") == "pursue" and int(r.get("round") or 0) <= tm.SEASON1_LAST_ROUND:
            findings.setdefault((int(r["round"]), r["source"]), set()).add(r["finding"])
    keys = set()
    for r in tm.legacy_pursue_baseline():
        m = re.match(r"\d+_R(\d+)_(.+)$", r["id"])
        key = (int(m.group(1)), m.group(2))
        assert len(findings.get(key, ())) == 1, key
        keys.add(key)
    # Every Critic-sourced pursue finding in the ledger has its label row.
    assert keys == {k for k in findings if k[1].endswith("_critic.md")}


@pytest.mark.skipif(not tm.LEGACY_FILE.exists(), reason="legacy labels not present")
def test_report_legacy_json_prints_the_corrected_pursue_row(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["taxonomy_monitor.py", "report", "--legacy", "--json"])
    tm.main()
    rows = [json.loads(ln) for ln in capsys.readouterr().out.splitlines() if ln.strip()]
    pursue = next(r["pursue_findings"] for r in rows if "pursue_findings" in r)
    assert pursue["n"] == 13

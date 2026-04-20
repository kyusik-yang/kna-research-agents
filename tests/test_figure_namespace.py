#!/usr/bin/env python3
"""
Regression test for C4 (reflection report 2026-04-20): per-article figure
namespace. Ensures that draft_article.py's figure-repair helpers write
into articles/figures/<article_stem>/ (not the flat articles/figures/ dir)
so future auto-drafts do not overwrite each other's figures.

Run: python3 -m pytest tests/ -v
"""

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DRAFT_SCRIPT = REPO / "draft_article.py"


def _load_draft_module():
    """Import draft_article.py without triggering its CLI main()."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("draft_article_mod", str(DRAFT_SCRIPT))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repair_orphan_figures_uses_per_article_subdir(tmp_path, monkeypatch):
    """repair_orphan_figures() must resolve figure_dir as
    <tex.parent>/figures/<tex.stem>/, not the flat figures/ dir."""
    # Create a fake articles/ directory with two tex files that both have
    # the same fbox placeholder. If the namespace is flat (buggy), the
    # second call should receive fig_2.pdf / fig_3.pdf (continuing
    # numbering). If per-article (fixed), both start at fig_1 in their
    # own subdirs.
    mod = _load_draft_module()

    articles_dir = tmp_path / "articles"
    articles_dir.mkdir()

    a_tex = articles_dir / "2026-05-01_rX.tex"
    a_tex.write_text(r"\fbox{\parbox{1cm}{placeholder A}}")
    b_tex = articles_dir / "2026-05-02_rY.tex"
    b_tex.write_text(r"\fbox{\parbox{1cm}{placeholder B}}")

    # Monkeypatch the Claude call so we don't actually run an LLM; we
    # just need the directory-resolution logic under test.
    called = []

    def fake_run(cmd, **kw):
        called.append(cmd)
        # Return a fake success with an empty R script; the repair function
        # will find the file not existing and skip the Rscript step.
        class R:
            returncode = 0
            stdout = ""
            stderr = ""
        return R()

    monkeypatch.setattr(mod.subprocess, "run", fake_run)

    mod.repair_orphan_figures(a_tex, round_num=1)
    mod.repair_orphan_figures(b_tex, round_num=2)

    # Both should have produced their own subdirectory
    assert (articles_dir / "figures" / "2026-05-01_rX").exists()
    assert (articles_dir / "figures" / "2026-05-02_rY").exists()
    # And the flat figures/ directory should contain ONLY those subdirs,
    # no fig_*.pdf stragglers
    flat_stragglers = list((articles_dir / "figures").glob("fig_*.pdf"))
    assert flat_stragglers == [], f"flat-namespace regression: {flat_stragglers}"


def test_check_claim_n_flags_small_cohorts():
    """C6 regression: check_claim_n should flag inferential claims paired
    with N<10 cells."""
    mod = _load_draft_module()

    bad = r"""
    The cabinet-channel estimate (N=4) shows a significant effect on
    chief-sponsorship (p = 0.03, 95% CI [-0.5, 0.8]).
    """
    warnings = mod.check_claim_n(bad, n_threshold=10)
    assert warnings, "expected N=4 inferential claim to be flagged"

    ok = r"""
    Table 2 reports descriptive counts for the cabinet-channel subset
    (N = 4). No inferential language is attached.
    """
    warnings_ok = mod.check_claim_n(ok, n_threshold=10)
    assert warnings_ok == [], f"expected descriptive-only N=4 to pass: {warnings_ok}"


def test_require_hand_coding_dictionary_blocks_when_missing(tmp_path, monkeypatch):
    """C5 regression: a round summary mentioning 'hand-coded' must have a
    corresponding knowledge/hand_coding/round_{NN}.jsonl, else drafting
    is blocked."""
    mod = _load_draft_module()

    # Set up a fake repo structure
    summaries = tmp_path / "summaries"
    summaries.mkdir()
    hc = tmp_path / "knowledge" / "hand_coding"
    hc.mkdir(parents=True)

    (summaries / "round_25.md").write_text(
        "Round 25 built a hand-coded cohort of 16 members across the 20th Assembly."
    )

    monkeypatch.setattr(mod, "SUMMARIES_DIR", summaries)
    monkeypatch.setattr(mod, "HAND_CODING_DIR", hc)

    try:
        mod.require_hand_coding_dictionary(25, bypass=False)
        assert False, "expected SystemExit when dictionary missing"
    except SystemExit as e:
        assert "C5" in str(e)

    # Now place the dictionary and retry
    (hc / "round_25.jsonl").write_text('{"member_id":"TEST","category":"cabinet"}\n')
    path = mod.require_hand_coding_dictionary(25, bypass=False)
    assert path is not None and path.name == "round_25.jsonl"


if __name__ == "__main__":
    # Minimal fallback runner if pytest is not installed
    try:
        import pytest
    except ImportError:
        print("pytest not installed; run manually.")
        sys.exit(0)
    sys.exit(pytest.main([__file__, "-v"]))

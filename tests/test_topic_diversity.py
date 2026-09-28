"""Topic-diversity guard v2 (M17): embedded text, .tex papers, thresholds from
forum_config, one row per post, structured duplicate check, and the
calibration statistics. The embedding model is replaced by a deterministic
bag-of-words stub except in the opt-in live test (KNA_EMBED_TESTS=1)."""

import hashlib
import json
import math
import os
import re
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import topic_diversity as td  # noqa: E402
import calibrate_diversity as cal  # noqa: E402


# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

SEASON2_POST = """---
author: "Scout (Literature Tracker)"
date: "2026-08-24 09:25"
references: ["10.1/abc"]
---

# Arc 9 Opens: A Long Title With Many Words That Should Not Be Embedded

```yaml
round: R40 (Arc 9, opening round, Season 2)
topic_gate: signed entry "R40" verified on disk this round
queries_run: 3
```

topic_gate: a stray line outside the header that must be dropped

## 1. Response to Critic

Critic said many things about something unrelated to the headline question.

## 4. Prediction to Test

**Prediction:** committee chairs pass their own bills more often than matched members.

### Details

The quantity is the passage rate of chair-sponsored bills.

## 5. Gap Type

**(a)** A standard prediction fails in Korean data.

## 6. Rejected Paths

Something about rejected paths.

```card
{"claim_id": "C1", "quantity": "chair bill passage rate", "population": "standing committee chairs 17th-22nd",
 "comparison": "chairs versus matched non-chairs", "spec_plan": [{"spec_id": "P1", "role": "primary",
 "outcome_def": "bill passed plenary"}]}
```
"""

SEASON1_POST = """---
author: "Scout"
---

# A Season 1 Literature Scan About Housing

Opening text about housing wealth and legislators.

```bash
python3 search.py "secret query text"
```

topic_gate: should vanish

More body text that stays.
"""

TEX = r"""\documentclass{article}
\begin{document}
\title{Housing Wealth and Legislative Behavior: \\ Evidence from Korea}
\maketitle
% a comment line that must not appear
\begin{abstract}
\noindent Do property-rich legislators vote differently \citep{smith2020, lee2021}? I find \textbf{no} difference.
\end{abstract}
\section{Introduction}
Housing wealth is large in Korea~\citep{kim2019}.\footnote{Searched KCI in 2026.} The question matters.
\section{Literature and Theory}
Literature text that must not be embedded.
\end{document}
"""


def _bow_embed(texts, name=None):
    """Deterministic bag-of-words embedding (hash buckets), unit norm."""
    out = []
    for t in texts:
        v = np.zeros(512, dtype=np.float32)
        for w in re.findall(r"\w+", t.lower()):
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 512] += 1.0
        n = float(np.linalg.norm(v)) or 1.0
        out.append(v / n)
    return np.vstack(out) if out else np.zeros((0, 512), dtype=np.float32)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A temporary forum, articles folder and knowledge folder."""
    forum = tmp_path / "forum"; forum.mkdir()
    arts = tmp_path / "articles"; arts.mkdir()
    know = tmp_path / "knowledge"; know.mkdir()
    monkeypatch.setattr(td, "FORUM_DIR", forum)
    monkeypatch.setattr(td, "ARTICLES_DIR", arts)
    monkeypatch.setattr(td, "KNOWLEDGE_DIR", know)
    monkeypatch.setattr(td, "ACTIVE_ARC_FILE", know / "active_arc.json")
    monkeypatch.setattr(td, "CARDS_DIR", know / "prediction_cards")
    monkeypatch.setattr(td, "LOG_FILE", know / "topic_diversity.jsonl")
    monkeypatch.setattr(td, "EMBED_CACHE_DIR", None)
    monkeypatch.setattr(td, "embed", _bow_embed)
    monkeypatch.setattr(td, "_config", lambda: {"topic_similarity_warn": 0.5, "topic_similarity_block": 0.9,
                                                "diversity_model": "stub-model"})
    return tmp_path


# --------------------------------------------------------------------------
# Embedded text
# --------------------------------------------------------------------------

def test_post_text_embeds_only_prediction_and_gap_sections(tmp_path):
    p = tmp_path / "118_literature_scout.md"
    p.write_text(SEASON2_POST, encoding="utf-8")
    t = td.post_text(p)
    assert "committee chairs pass their own bills" in t
    assert "passage rate of chair-sponsored bills" in t          # subsection body kept
    assert "standard prediction fails in Korean data" in t
    assert "topic_gate" not in t and "author" not in t and "references" not in t
    assert "Long Title" not in t                                 # H1 title not embedded
    assert "Critic said" not in t and "rejected paths" not in t  # other sections dropped
    assert "Prediction to Test" not in t and "Gap Type" not in t  # headings dropped
    # card fields appended
    for s in ("chair bill passage rate", "standing committee chairs", "matched non-chairs", "bill passed plenary"):
        assert s in t
    assert "spec_id" not in t


def test_post_text_season1_fallback_drops_frontmatter_code_and_gate_lines(tmp_path):
    p = tmp_path / "019_literature_scout.md"
    p.write_text(SEASON1_POST + ("filler " * 2000), encoding="utf-8")
    t = td.post_text(p)
    assert t.startswith("# A Season 1 Literature Scan About Housing")
    assert "author" not in t and "secret query text" not in t and "topic_gate" not in t
    assert "More body text that stays." in t
    assert len(t) == td.FALLBACK_CHARS


def test_article_text_reads_tex_title_abstract_and_introduction(tmp_path):
    p = tmp_path / "2026-03-31_r2.tex"
    p.write_text(TEX, encoding="utf-8")
    t = td.article_text(p)
    assert t.startswith("Housing Wealth and Legislative Behavior: Evidence from Korea")
    assert "Do property-rich legislators vote differently" in t and "no difference" in t
    assert "Housing wealth is large in Korea" in t and "The question matters." in t
    for bad in ("smith2020", "kim2019", "Searched KCI", "comment line", "Literature text", "\\", "{", "}"):
        assert bad not in t


def test_article_files_use_tex_and_build_site_filters(tmp_path):
    for name in ("2026-03-31_r2.tex", "template.tex", "compile_r3.tex", "2026-03-31_r2.md", "content_r4.tex"):
        (tmp_path / name).write_text(TEX, encoding="utf-8")
    assert [p.name for p in td.article_files(tmp_path)] == ["2026-03-31_r2.tex"]


def test_round_of_kept_for_migration():
    assert td._round_of(Path("073_literature_scout.md")) == 25
    assert td._round_of(Path("072_critic.md")) == 24


# --------------------------------------------------------------------------
# Thresholds from forum_config, prompt blocks
# --------------------------------------------------------------------------

def test_scout_prompt_block_reads_thresholds_from_forum_config(repo, monkeypatch):
    (repo / "articles" / "2026-03-31_r2.tex").write_text(TEX, encoding="utf-8")
    monkeypatch.setattr(td, "_config", lambda: {"topic_similarity_warn": 0.71, "topic_similarity_block": 0.83,
                                                "diversity_model": "nlpai-lab/KURE-v1"})
    block = td.prior_topics_for_scout()
    assert "warn 0.71" in block and "block 0.83" in block
    assert "0.68" not in block and "0.80" not in block
    assert "R2: Housing Wealth and Legislative Behavior" in block
    assert "nlpai-lab/KURE-v1" in block


def test_thresholds_fall_back_to_module_default_and_say_so(monkeypatch):
    assert td.thresholds({}) == (td.DEFAULT_WARN, td.DEFAULT_BLOCK, "module_default")
    assert td.thresholds({"topic_similarity_warn": 0.6, "topic_similarity_block": 0.7}) == (0.6, 0.7, "forum_config")
    assert td.model_name({}) == "nlpai-lab/KURE-v1"


def test_format_for_prompt_block_row(tmp_path, monkeypatch):
    monkeypatch.setattr(td, "LOG_FILE", tmp_path / "topic_diversity.jsonl")
    assert td.format_for_prompt() == ""
    row = {"round": 25, "status": "block", "warn": 0.68, "block": 0.80, "max_cosine": 0.84,
           "nearest_post": {"id": "058_literature_scout", "round": 20, "cosine": 0.84},
           "nearest_article": {"id": "2026-04-20_r22", "round": 22, "cosine": 0.81}}
    (tmp_path / "topic_diversity.jsonl").write_text(json.dumps(row) + "\n")
    block = td.format_for_prompt(25)
    assert "BLOCK" in block and "2026-04-20_r22" in block and "cosine 0.81" in block
    assert td.format_for_prompt(26) == ""


@pytest.mark.parametrize("status", ["warn", "block"])
def test_format_for_prompt_has_no_cap_or_verdict_instruction(tmp_path, monkeypatch, status):
    """E2E-06: with uncalibrated thresholds the block must not cap a score or
    tell the Critic to archive, since run_arc turns archive plus block into a
    stop. It keeps the nearest texts, the cosines and the status."""
    monkeypatch.setattr(td, "LOG_FILE", tmp_path / "topic_diversity.jsonl")
    row = {"round": 31, "status": status, "warn": 0.68, "block": 0.80, "max_cosine": 0.83,
           "nearest_post": {"id": "073_literature_scout", "round": 25, "cosine": 0.83},
           "structured_duplicate": {"card": "R26", "round": 26}}
    (tmp_path / "topic_diversity.jsonl").write_text(json.dumps(row) + "\n")
    block = td.format_for_prompt(31)
    assert "073_literature_scout (R25), cosine 0.83" in block and f"**{status.upper()}**" in block
    assert "card R26" in block and "uncalibrated" in block
    low = block.lower()
    for bad in ("cap", "research_novelty", "archive", "duplicate topic", "verdict", "critic:", "analyst:",
                "/4"):
        assert bad not in low, bad


# --------------------------------------------------------------------------
# check_post
# --------------------------------------------------------------------------

def _scout(repo, n, body):
    p = repo / "forum" / f"{n:03d}_literature_scout.md"
    p.write_text(f"---\nauthor: x\n---\n\n# T\n\n## Prediction to Test\n\n{body}\n\n## Gap Type\n\n(a)\n",
                 encoding="utf-8")
    return p


def test_check_post_finds_nearest_prior_and_writes_one_row_per_post(repo):
    _scout(repo, 1, "housing wealth legislators vote on housing regulation bills")
    _scout(repo, 4, "gender quota women legislators effectiveness")
    (repo / "articles" / "2026-03-31_r2.tex").write_text(TEX, encoding="utf-8")
    new = _scout(repo, 19, "housing wealth legislators vote on housing regulation bills again")
    r = td.check_post(new, round_num=7, arc_start=7)
    assert r["nearest_post"]["id"] == "001_literature_scout"
    assert r["status"] in ("warn", "block") and r["max_cosine"] >= 0.5
    assert r["model"] == "stub-model" and r["text_basis"] == "sections" and r["thresholds_source"] == "forum_config"
    assert r["logged"] is True
    again = td.check_post(new, round_num=7, arc_start=7)
    assert again["logged"] is False
    rows = [json.loads(l) for l in td.LOG_FILE.read_text().splitlines()]
    assert len(rows) == 1 and rows[0]["post"] == new.name


def test_check_post_logs_only_the_post_it_is_given(repo):
    """A failed Scout run leaves a newer file on disk. The orchestrator checks
    only the post its accepted run returned, never the newest file."""
    _scout(repo, 1, "housing wealth")
    accepted = _scout(repo, 73, "confirmation hearing opposition and audit questions")
    _scout(repo, 76, "partial post from a failed run")
    td.check_post(accepted, round_num=25, arc_start=25)
    rows = [json.loads(l) for l in td.LOG_FILE.read_text().splitlines()]
    assert [r["post"] for r in rows] == ["073_literature_scout.md"]


def test_within_arc_posts_are_not_prior(repo):
    _scout(repo, 73, "confirmation hearing opposition")
    new = _scout(repo, 76, "confirmation hearing opposition dose")
    r = td.check_post(new, round_num=26, arc_start=25, log=False)
    assert r["status"] == "no_prior" and r["n_prior"] == 0


def test_structured_duplicate_blocks_regardless_of_cosine(repo, monkeypatch):
    cards = repo / "knowledge" / "prediction_cards"; cards.mkdir()
    (cards / "R20.json").write_text(json.dumps({
        "claim_id": "C1", "outcome": "Bill passed plenary.", "population": "Standing committee chairs, 17th-22nd",
        "comparison": "chairs versus matched NON-chairs"}), encoding="utf-8")
    _scout(repo, 1, "an unrelated earlier topic about gender")
    new = repo / "forum" / "118_literature_scout.md"
    new.write_text(SEASON2_POST, encoding="utf-8")
    cfg = {"topic_similarity_warn": 0.99, "topic_similarity_block": 0.999, "stage2": {"prediction_cards": True}}
    monkeypatch.setattr(td, "_config", lambda: cfg)
    r = td.check_post(new, round_num=40, arc_start=40, log=False)
    assert r["max_cosine"] < 0.99
    assert r["status"] == "block" and r["structured_duplicate"]["card"] == "R20"
    cfg["stage2"]["prediction_cards"] = False
    r = td.check_post(new, round_num=40, arc_start=40, log=False)
    assert r["status"] == "clear" and r["structured_duplicate"] is None


def test_structured_duplicate_ignores_cards_inside_the_active_arc(repo):
    cards = repo / "knowledge" / "prediction_cards"; cards.mkdir()
    card = {"outcome": "o", "population": "p", "comparison": "c"}
    (cards / "R41.json").write_text(json.dumps(card), encoding="utf-8")
    assert td.structured_duplicate(card, arc_start=40) is None
    assert td.structured_duplicate(card, arc_start=42)["card"] == "R41"
    assert td.structured_duplicate({"outcome": "o", "population": "", "comparison": "c"}, arc_start=42) is None


# --------------------------------------------------------------------------
# Calibration statistics
# --------------------------------------------------------------------------

def test_auc_and_bootstrap():
    assert cal.auc([0.9, 0.8], [0.1, 0.2]) == 1.0
    assert cal.auc([0.5], [0.5]) == 0.5
    assert cal.auc([0.1], [0.9]) == 0.0
    ci = cal.bootstrap_auc([0.9, 0.8, 0.7], [0.1, 0.75, 0.3], n_boot=500)
    assert ci == cal.bootstrap_auc([0.9, 0.8, 0.7], [0.1, 0.75, 0.3], n_boot=500)   # seeded
    assert 0.0 <= ci[0] <= ci[1] <= 1.0


def test_propose_rules_and_criterion():
    pos, neg = [0.83, 0.77, 0.81], [0.40, 0.55, 0.62, 0.70]
    p = cal.propose(pos, neg)
    assert p["warn"] == 0.77                  # at or below every repeat
    assert p["block"] == 0.78                 # above every distinct pair and above warn
    assert all(x >= p["warn"] for x in pos)
    assert cal.share_at_or_above(neg, p["warn"]) == 0.0
    p2 = cal.propose([0.60, 0.9], [0.40, 0.70])
    assert p2["warn"] == 0.60 and p2["block"] == 0.71
    assert cal.share_at_or_above([0.40, 0.70], 0.60) == 0.5


def test_summarize_and_loo():
    pairs = ([{"comparison": "scout_scout", "label": "repeat", "cosine": c} for c in (0.8, 0.85)]
             + [{"comparison": "scout_scout", "label": "distinct", "cosine": c} for c in (0.3, 0.4, 0.5)]
             + [{"comparison": "scout_paper", "label": "same_topic_within_arc", "cosine": 0.6}])
    s = cal.summarize(pairs, "pooled", extended=False)
    assert s["n_repeat"] == 2 and s["n_distinct"] == 3 and s["auc"] == 1.0 and s["criterion_pass"]
    assert s["loo"]["warn_range"] == [0.8, 0.85]
    ext = cal.summarize(pairs, "pooled", extended=True)
    assert ext["n_repeat"] == 3 and ext["proposed_warn"] == 0.6


def test_labeled_pairs_keep_file_edits_and_fill_seed(tmp_path):
    f = tmp_path / "cal.jsonl"
    edited = {"row": "pair", "pair_id": "DSS01", "a": "001_literature_scout", "b": "013_literature_scout",
              "label": "distinct", "source": "proposed", "confirmed_by": "researcher", "note": "n"}
    extra = {"row": "pair", "pair_id": "XSS99", "a": "001_literature_scout", "b": "004_literature_scout",
             "label": "repeat", "source": "researcher", "confirmed_by": "researcher", "note": "added"}
    f.write_text(json.dumps(edited) + "\n" + json.dumps(extra) + "\n")
    pairs = {p["pair_id"]: p for p in cal.labeled_pairs(cal.load_rows(f))}
    assert pairs["DSS01"]["confirmed_by"] == "researcher"
    assert pairs["XSS99"]["label"] == "repeat" and pairs["XSS99"]["comparison"] == "scout_scout"
    assert len(pairs) == len(cal.SEED_PAIRS) + 1
    assert pairs["RSP02"]["comparison"] == "scout_paper"


def test_seed_pairs_cover_the_plan_repeats():
    ids = {(a, b) for _, a, b, label, _, _ in cal.SEED_PAIRS if label == "repeat"}
    S = "_literature_scout"
    for pair in (("052" + S, "055" + S), ("055" + S, "058" + S), ("058" + S, "064" + S),
                 ("019" + S, "001" + S), ("019" + S, "004" + S),
                 ("019" + S, "2026-03-31_r2"), ("055" + S, "2026-04-18_r18")):
        assert pair in ids
    n_distinct = sum(1 for p in cal.SEED_PAIRS if p[3] == "distinct")
    assert 18 <= n_distinct <= 30


def test_recorded_calibration_is_consistent():
    """The committed calibration file: every repeat scores at or above the
    proposed warn, and the recorded shares match the recorded scores."""
    if not cal.CAL_FILE.exists():
        pytest.skip("no calibration file yet")
    rows = cal.load_rows()
    rec = [r for r in rows if r.get("row") == "recommendation"]
    assert rec, "calibration file has no recommendation row"
    run_id = rec[-1]["run_id"]
    summ = [r for r in rows if r.get("row") == "summary" and r.get("run_id") == run_id]
    assert {(s["set"], s["comparison"]) for s in summ} >= {("primary", "pooled"), ("primary", "scout_scout"),
                                                            ("primary", "scout_paper")}
    for s in summ:
        if s["proposed_warn"] is None:
            continue
        assert all(x >= s["proposed_warn"] - 1e-9 for x in s["repeat_scores"])
        assert s["distinct_share_at_or_above_warn"] == cal.share_at_or_above(s["distinct_scores"], s["proposed_warn"])
        assert s["auc_ci95"][0] <= s["auc"] <= s["auc_ci95"][1]
    assert "not approved" in rec[-1]["status"] and rec[-1]["approved_by"] is None
    r = rec[-1]
    assert r["approval_recommended"] == bool(r["criterion_pass"] and r["regression_r19_flags"]
                                             and r["openers_073_082_clear"])
    assert ("FAIL" in r["status"]) == (not r["approval_recommended"])
    pairs = [r for r in rows if r.get("row") == "pair"]
    assert all(r.get("model") == rec[-1]["model"] for r in pairs)


# --------------------------------------------------------------------------
# Live regression (opt-in: KNA_EMBED_TESTS=1, model in the local cache)
# --------------------------------------------------------------------------

@pytest.mark.skipif(os.environ.get("KNA_EMBED_TESTS") != "1", reason="set KNA_EMBED_TESTS=1 to run the real model")
def test_live_regression_r19_flags_and_openers_clear():
    rec = [r for r in cal.load_rows() if r.get("row") == "recommendation"]
    if not rec:
        pytest.skip("no calibration recommendation")
    warn, block = rec[-1]["warn"], rec[-1]["block"]
    S = "_literature_scout"
    r19 = td.nearest(td.FORUM_DIR / f"055{S}.md", 19, 19)
    assert r19["nearest_article"]["id"] == "2026-04-18_r18"
    assert td.status_for(r19["nearest_article"]["cosine"], warn, block) in ("warn", "block")
    for stem, start in (("073", 25), ("082", 28)):
        near = td.nearest(td.FORUM_DIR / f"{stem}{S}.md", start, start)
        assert td.status_for(near["max_cosine"], warn, block) == "clear", (stem, near)

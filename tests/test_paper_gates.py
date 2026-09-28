#!/usr/bin/env python3
"""Tests for the M07 paper gates, the fail-closed drafting pipeline in
draft_article.py, and build_site's handling of gated papers and of posts that
carry the v2.1 orchestrator frontmatter keys.

Published papers in articles/ are read, never written. Tests that assert
the Version 1 defects of Papers D and E read frozen copies under
tests/fixtures/paper_gates/, so a correction of a published paper cannot
break them. The live papers must pass every blocking gate. Every drafting test
redirects draft_article's directories to tmp_path and patches
claude_cli.run_claude, so no claude process, network call or compile runs.
"""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import paper_gates as pg  # noqa: E402

ARTICLES = ROOT / "articles"
FIX = ROOT / "tests" / "fixtures" / "papers"
R27_TEX = ARTICLES / "2026-08-24_r27.tex"
R30_TEX = ARTICLES / "2026-08-24_r30.tex"
SYN = FIX / "synthetic"
SYN_TEX = SYN / "2026-01-01_r99.tex"
SYN_BIB = SYN / "references_r99.bib"

# Version 1 of Papers D and E as published on 2026-08-24, before the
# 2026-09-26 corrections (see tests/fixtures/paper_gates/README.md).
V1 = ROOT / "tests" / "fixtures" / "paper_gates"
V1_R27_TEX = V1 / "r27_v1.tex"
V1_R27_BIB = V1 / "references_r27_v1.bib"
V1_R27_PDF_TEXT = V1 / "r27_v1.pdftotext.txt"
V1_R30_TEX = V1 / "r30_v1.tex"
V1_R30_BIB = V1 / "references_r30_v1.bib"
V1_SHA256 = {
    V1_R27_TEX: "691c8902168a7a09d8546b0476c6cf4f7901ec14b415bc87257e9ba95f233a74",
    V1_R27_BIB: "171f92587ee6d4aeffb278237c1f61aac7d87dba824a9dc6a0525f82aec7d433",
    V1_R27_PDF_TEXT: "8828c0aa76f0679d5795023297c7030c58717357b992a00b74930ac418637e9e",
    V1_R30_TEX: "252f5554d401997d197ac382e3df3db1edacf92996c9b7d71322c7c525046a34",
    V1_R30_BIB: "8238ff0bc1ac6e6ae94397784fa0b9175e7b19f43f8dddd43bd72d4732b153a9",
}

# The published papers as they stand now: (stem, arc). G4 checks any
# replication claim against the arc's own package, replication/arc_<arc>.
PUBLISHED = [("2026-08-24_r27", 4), ("2026-08-24_r30", 5)]

needs_papers = pytest.mark.skipif(not R27_TEX.exists() or not R30_TEX.exists(),
                                  reason="published papers not present")


def gate(report, gid):
    return next(g for g in report["gates"] if g["id"] == gid)


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    """No test writes the real reference cache, and G5 never goes online
    unless a test says so."""
    monkeypatch.setattr(pg, "REF_CACHE_FILE", tmp_path / "ref_cache.json")


# ---------------------------------------------------------------------------
# Gates on the published papers as they stand now (Version 2)
# ---------------------------------------------------------------------------

@needs_papers
@pytest.mark.parametrize("stem,arc", PUBLISHED)
def test_published_papers_pass_g1_to_g4_and_g6(stem, arc):
    """Papers D and E as corrected pass G1 to G4 and G6. G5 needs the
    network and is skipped. G2 also reads the shipped PDF when pdftotext
    exists. G6 uses the private denylist when it is present on this machine."""
    tex = ARTICLES / f"{stem}.tex"
    rep = ROOT / "replication" / f"arc_{arc}"
    r = pg.run_all(tex, pg.default_bib(tex), tex.with_suffix(".pdf"), replication_dir=rep, arc=arc,
                   check_references=False)
    failed = {g["id"]: g["details"] for g in r["gates"] if g["id"] != "G5" and not g["passed"]}
    assert not failed, failed
    passed = {g["id"] for g in r["gates"] if g["passed"]}
    assert {"G1", "G2", "G3", "G4", "G6"} <= passed, passed
    assert r["ok"] and r["failed_blocking"] == []
    if shutil.which("pdftotext"):
        assert r["pdf_checked"] and "pdftotext" in gate(r, "G2")["details"]["sources"]


@needs_papers
def test_published_paper_e_names_its_verified_package():
    """Paper E's replication statement rests on replication/arc_5, whose
    MANIFEST records a passing build and verify."""
    g = pg.gate_g4(R30_TEX.read_text(), replication=pg.replication_status(ROOT / "replication" / "arc_5"),
                   arc=5)
    assert g["passed"], g["details"]["replication_problems"]
    assert g["details"]["replication_claims"] >= 1 and g["details"]["replication_packages_named"] == ["5"]


# ---------------------------------------------------------------------------
# Version 1 defects (frozen fixtures, never the live articles/)
# ---------------------------------------------------------------------------

def test_v1_fixtures_are_frozen():
    for path, digest in V1_SHA256.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path.name


def test_g1_paper_d_missing_keys_exact():
    g = pg.gate_g1(V1_R27_TEX.read_text(), pg.parse_bib(V1_R27_BIB.read_text()))
    assert not g["passed"] and g["blocking"]
    assert g["details"]["missing"] == ["aberbach1990", "martin2011", "mayhew1974", "mccubbins1984"]


def test_g2_paper_d_recompiled_log_and_blg():
    """The .log and .blg of a recompiled Paper D (fixtures keep only the
    warning lines) name exactly the four undefined keys."""
    g = pg.gate_g2(V1_R27_TEX.read_text(), log_text=(FIX / "r27_recompiled.log").read_text(),
                   blg_text=(FIX / "r27_recompiled.blg").read_text())
    missing = ["aberbach1990", "martin2011", "mayhew1974", "mccubbins1984"]
    assert not g["passed"]
    assert g["details"]["log_undefined_citations"] == missing
    assert g["details"]["blg_missing_entries"] == missing


def test_g2_paper_d_pdftotext_shapes():
    """The Version 1 PDF shows one marker per affected cite command (8), in
    every shape the plan lists."""
    g = pg.gate_g2(V1_R27_TEX.read_text(), pdf_text=V1_R27_PDF_TEXT.read_text(encoding="utf-8"))
    hits = g["details"]["pdf_hits"]
    assert not g["passed"]
    assert len(hits) == 8
    assert {h["shape"] for h in hits} == {"double_question", "paren_question", "question_before_name",
                                          "lone_question"}
    assert any("? through" in h["context"] for h in hits)


def test_g2_shapes_ignore_ordinary_question_marks():
    g = pg.gate_g2("x", pdf_text="Why does oversight carry over? It does not, see Table 2.")
    assert g["passed"]
    g = pg.gate_g2("x", pdf_text="venues (??). position taking (?), from ? through (?Senninger")
    assert [h["shape"] for h in g["details"]["pdf_hits"]] == [
        "double_question", "paren_question", "question_before_name", "lone_question"]


def test_g4_paper_d_flags_all_23_preregistered_uses():
    g = pg.gate_g4(V1_R27_TEX.read_text())
    assert not g["passed"]
    assert g["details"]["preregistered_uses"] == 23
    assert len(g["details"]["preregistered_without_registry"]) == 23


def test_g4_registry_id_clears_preregistered():
    tex = "\\begin{document}The design was pre-registered at osf.io/ab12c before data access.\\end{document}"
    assert pg.gate_g4(tex)["passed"]
    tex = "\\begin{document}The design was pre-registered.\\end{document}"
    assert not pg.gate_g4(tex)["passed"]


def test_g4_paper_e_replication_claims_unbacked():
    g = pg.gate_g4(V1_R30_TEX.read_text())
    assert not g["passed"]
    assert g["details"]["replication_claims"] >= 7
    assert "no replication package given" in g["details"]["replication_problems"]


def test_g4_replication_claim_needs_verified_named_package(tmp_path):
    body = ("\\begin{document}All scripts are in the replication package at "
            "\\texttt{replication/arc\\_6}.\\end{document}")
    pkg = tmp_path / "arc_6"
    pkg.mkdir()
    (pkg / "MANIFEST.json").write_text(json.dumps({"arc": 6, "build": {"ok": True},
                                                   "verify": {"passed": None}}))
    g = pg.gate_g4(body, replication=pg.replication_status(pkg), arc=6)
    assert not g["passed"] and "verify has not passed" in " ".join(g["details"]["replication_problems"])
    (pkg / "MANIFEST.json").write_text(json.dumps({"arc": 6, "build": {"ok": True},
                                                   "verify": {"passed": True}}))
    assert pg.gate_g4(body, replication=pg.replication_status(pkg), arc=6)["passed"]
    unnamed = "\\begin{document}Scripts are in the replication package.\\end{document}"
    assert not pg.gate_g4(unnamed, replication=pg.replication_status(pkg), arc=6)["passed"]


def test_g3_warns_on_paper_e_table_lines_229_to_246():
    g = pg.gate_g3(V1_R30_TEX.read_text())
    assert not g["passed"] and not g["blocking"]
    lines = {f["line"] for f in g["details"]["blank_cells"]}
    assert lines & set(range(229, 247)), lines
    kinds = {f["kind"] for f in g["details"]["blank_cells"] if 229 <= f["line"] <= 246}
    assert {"estimate without an uncertainty cell", "blank N cell", "blank indicator cell"} <= kinds


def test_g6_blocks_home_paths_and_flags_generic_patterns(tmp_path, monkeypatch):
    monkeypatch.setenv("KNA_LEAK_PATTERNS", str(tmp_path / "none.txt"))
    g = pg.gate_g6({"a.tex": 'DATA <- "/Users/someone/kna/data/processed"', "b.tex": "see CLAUDE.md"})
    assert not g["passed"] and g["blocking"]
    assert [h["pattern_id"] for h in g["details"]["blocking_hits"]] == ["home_path"]
    assert [h["pattern_id"] for h in g["details"]["flag_hits"]] == ["claude_md"]
    assert pg.gate_g6({"b.tex": "see CLAUDE.md"})["passed"]


def test_g6_private_block_patterns_fail(tmp_path, monkeypatch):
    pat = tmp_path / "patterns.txt"
    pat.write_text("block:secret-vault-name\nsoft-name\n")
    monkeypatch.setenv("KNA_LEAK_PATTERNS", str(pat))
    g = pg.gate_g6({"a.tex": "soft-name here"})
    assert g["passed"] and g["details"]["flag_hits"]
    g = pg.gate_g6({"a.tex": "the secret-vault-name appears"})
    assert not g["passed"]
    assert "match" not in g["details"]["blocking_hits"][0]   # private text is never echoed


# ---------------------------------------------------------------------------
# Synthetic paper, planted defects, G5
# ---------------------------------------------------------------------------

def test_synthetic_complete_paper_passes_every_gate(monkeypatch, tmp_path):
    monkeypatch.setenv("KNA_LEAK_PATTERNS", str(tmp_path / "none.txt"))
    forum = "Scouts cited cox2005 and lowi1964 (10.2307/2009452)."
    r = pg.run_all(SYN_TEX, SYN_BIB, forum_text=forum, offline=True)
    assert r["ok"], [(g["id"], g["details"]) for g in r["gates"] if not g["passed"]]
    assert all(g["passed"] for g in r["gates"])
    assert r["counts"]["figures"] == 1 and r["counts"]["tables"] == 1
    assert r["counts"]["bib_entries"] == 2


def test_planted_defects_in_paper_e_are_all_caught(tmp_path, monkeypatch):
    """A copy of Paper E (the frozen Version 1) with five planted defects:
    recall per defect, measured against the unplanted copy."""
    monkeypatch.setenv("KNA_LEAK_PATTERNS", str(tmp_path / "none.txt"))
    tex = V1_R30_TEX.read_text()
    base = pg.run_all(V1_R30_TEX, V1_R30_BIB, check_references=False)
    intro = tex.index("\\section{Introduction}")
    planted = (tex[:intro] + "\\section{Introduction}\nThe claim follows \\citet{ghost2020}. "
               "TODO add a number. The design was pre-registered. Data sit in "
               "/Users/someone/data. " + tex[intro + len("\\section{Introduction}"):])
    row = "Sponsor controls & Yes & Yes & Yes & Yes"
    assert planted.count(row) == 1
    planted = planted.replace(row, "Sponsor controls & Yes & & Yes & Yes")
    (tmp_path / V1_R30_TEX.name).write_text(planted)
    shutil.copy2(V1_R30_BIB, tmp_path / V1_R30_BIB.name)
    r = pg.run_all(tmp_path / V1_R30_TEX.name, tmp_path / V1_R30_BIB.name, check_references=False)
    caught = {
        "missing cite key": "ghost2020" in gate(r, "G1")["details"]["missing"],
        "TODO placeholder": any(p["text"] == "TODO" for p in gate(r, "G2")["details"]["placeholders"]),
        "pre-registered": gate(r, "G4")["details"]["preregistered_uses"]
        == gate(base, "G4")["details"]["preregistered_uses"] + 1,
        "absolute path": any(h["path"] == V1_R30_TEX.name for h in gate(r, "G6")["details"]["blocking_hits"]),
        "blank table cell": any(f["row"] == "Sponsor controls" for f in gate(r, "G3")["details"]["blank_cells"])
        and not any(f["row"] == "Sponsor controls" for f in gate(base, "G3")["details"]["blank_cells"]),
    }
    assert all(caught.values()), caught
    assert not r["ok"]


def test_g5_crossref_miss_resolved_by_openalex_is_kept():
    """Fixture cache, no network: a DOI Crossref does not know but OpenAlex
    resolves (the prechecks cache format) is verified, not flagged."""
    bib = pg.parse_bib("""@article{kim2023, author = {Kim, Minsu}, title = {Oversight in Seoul},
        year = {2023}, doi = {10.1234/kpsr.2023.1}}
        @article{park2021, author = {Park, Jiwon}, title = {Hearings and Audits}, year = {2021},
        doi = {10.1234/missing}}""")
    cache = {
        "10.1234/kpsr.2023.1": {"found": True, "source": "openalex", "resolved_as": "10.1234/kpsr.2023.1",
                                "first_author": "Kim", "years": [2023], "title": "Oversight in Seoul"},
        "10.1234/missing": {"found": False, "source": "crossref+openalex", "resolved_as": None},
    }
    g = pg.gate_g5(bib, forum_text="", cache=cache, offline=True)
    assert not g["blocking"]
    assert g["details"]["verified"] == 1
    assert [f["key"] for f in g["details"]["flagged"]] == ["park2021"]
    assert g["details"]["flagged"][0]["status"] == "not_found"


def test_g5_skips_references_the_forum_mentions():
    bib = pg.parse_bib("@book{cox2005, author = {Cox, Gary W.}, title = {Setting the Agenda}, year = {2005}}")
    g = pg.gate_g5(bib, forum_text="as cox2005 argues", cache={}, offline=True)
    assert g["passed"] and g["details"]["mentioned_in_forum"] == 1 and g["details"]["checked"] == 0


def test_g5_title_query_mismatch_is_flagged():
    bib = pg.parse_bib("@article{lee2019, author = {Lee, Hana}, title = {Party Switching in Korea}, year = {2019}}")
    key = "q:" + pg._fold("Party Switching in Korea")[:120] + "|lee|2019"
    cache = {key: [{"source": "crossref", "title": "Party Switching in Korea", "years": [2011],
                    "first_author": "Choi", "doi": "10.1/x"}]}
    g = pg.gate_g5(bib, forum_text="", cache=cache, offline=True)
    assert g["details"]["flagged"][0]["status"] == "mismatch"


def test_parse_bib_handles_nested_braces_and_quotes():
    b = pg.parse_bib('@article{a1, title = {The {Korean} Case}, author = "Yoon, Jae", year = 2020}\n'
                     '@comment{ignore me}')
    assert list(b) == ["a1"]
    assert b["a1"]["fields"]["title"] == "The {Korean} Case"
    assert b["a1"]["fields"]["year"] == "2020"


def test_cite_keys_all_natbib_forms_and_comments():
    tex = r"\citet{a} \citep[45]{b, c} \citep[see][p. 3]{d} \citeauthor{e} % \citep{f}"
    assert pg.cite_keys(tex) == ["a", "b", "c", "d", "e"]


def test_failing_items_are_specific():
    r = {"gates": [pg.gate_g1(r"\citep{x1}", {})]}
    items = pg.failing_items(r)
    assert len(items) == 1 and "x1" in items[0]


# ---------------------------------------------------------------------------
# draft_article: fail-closed pipeline
# ---------------------------------------------------------------------------

def _load_draft():
    import importlib
    import draft_article
    return importlib.reload(draft_article)


GOOD_BODY = (r"\title{A Test Paper}" + "\n" + r"\section{Introduction}" + "\n"
             + ("Committee gatekeeping matters for bill passage. " * 520)
             + r"As \citet{cox2005} argue." + "\n" + r"\section{Conclusion}" + "\nDone.\n"
             + r"\bibliographystyle{apsr}" + "\n" + r"\bibliography{references_r31}" + "\n")
BAD_BODY = GOOD_BODY.replace(r"\citet{cox2005}", r"\citet{ghost1999}")
BIB = "@book{cox2005, author = {Cox, Gary W.}, title = {Setting the Agenda}, year = {2005}}\n"


@pytest.fixture
def draft_env(tmp_path, monkeypatch):
    """draft_article with every directory under tmp_path and a fake wrapper."""
    da = _load_draft()
    arts = tmp_path / "articles"
    arts.mkdir()
    shutil.copy2(ARTICLES / "template.tex", arts / "template.tex")
    forum = tmp_path / "forum"
    forum.mkdir()
    for n, role in ((91, "literature_scout"), (92, "data_analyst"), (93, "critic")):
        (forum / f"{n:03d}_{role}.md").write_text(
            f'---\nauthor: "x"\nround: 31\narc: 6\nrole: "{role}"\n---\n\n# Post\nWe cite cox2005.\n')
    ws = tmp_path / "workspace"
    for name, val in {
        "ARTICLES_DIR": arts, "FORUM_DIR": forum, "WORKSPACE_DIR": ws, "DRAFTS_DIR": ws / "drafts",
        "FAILED_DRAFTS_DIR": ws / "failed_drafts", "GATE_REPORTS_DIR": tmp_path / "logs" / "paper_gates",
        "REPLICATION_DIR": tmp_path / "replication", "SUMMARIES_DIR": tmp_path / "summaries",
        "HAND_CODING_DIR": tmp_path / "hand_coding", "ACTIVE_ARC_FILE": tmp_path / "active_arc.json",
    }.items():
        monkeypatch.setattr(da, name, val)
    monkeypatch.setenv("KBL_DATA", str(tmp_path / "kna"))
    monkeypatch.setenv("KNA_LEAK_PATTERNS", str(tmp_path / "none.txt"))
    state = {"calls": [], "bodies": [], "fix": None, "failure": "ok", "compile": "ok", "compiles": 0}

    def fake_compile(tex, clean=True):
        """A stand-in for xelatex. "ok" writes a PDF and a clean .log, "raise"
        is a missing TeX install, "abort" leaves nothing (a fatal error)."""
        state["compiles"] += 1
        mode = state["compile"](state["compiles"]) if callable(state["compile"]) else state["compile"]
        if mode == "raise":
            raise FileNotFoundError("xelatex not found")
        if mode == "abort":
            return
        tex.with_suffix(".pdf").write_bytes(b"%PDF-1.4 fake")
        tex.with_suffix(".log").write_text(f"This is XeTeX\nOutput written on {tex.stem}.pdf (3 pages).\n")

    monkeypatch.setattr(da, "compile_tex", fake_compile)
    monkeypatch.setattr(da, "stage2_flag", lambda name: False)
    notes = []
    monkeypatch.setattr(da.claude_cli, "notify", lambda t, m: notes.append((t, m)))

    def fake_run_claude(task, prompt_text, **kw):
        state["calls"].append(task)
        from claude_cli import CallResult
        res = CallResult(ok=state["failure"] == "ok", failure=state["failure"], text="",
                         structured=None, run_id=f"t{len(state['calls'])}", session_id="s",
                         attempts=1, sidecar_path=tmp_path / "sc.json")
        if state["failure"] != "ok":
            return res
        if task == "draft_body":
            body = state["bodies"].pop(0) if state["bodies"] else None
            if body is not None:
                exp = Path(kw["expect_file"])
                exp.write_text(body)
                (exp.parent / "references_r31.bib").write_text(BIB)
        elif task == "draft_fix" and state["fix"]:
            state["fix"](kw)
        return res

    monkeypatch.setattr(da.claude_cli, "run_claude", fake_run_claude)
    return da, tmp_path, state, notes


def _tracked(tmp_path):
    return sorted(p.name for p in (tmp_path / "articles").glob("*_r31*"))


def test_draft_passing_is_published(draft_env):
    da, tmp, state, notes = draft_env
    state["bodies"] = [GOOD_BODY]
    assert da.draft_article(31) == da.EXIT_OK
    names = _tracked(tmp)
    assert any(n.endswith("_r31.tex") for n in names) and any(n.endswith("_r31.md") for n in names)
    assert (tmp / "articles" / "references_r31.bib").exists()
    reports = list((tmp / "logs" / "paper_gates").glob("*.gates.json"))
    assert len(reports) == 1 and json.loads(reports[0].read_text())["ok"]
    assert state["calls"] == ["draft_body"]
    assert not (tmp / "workspace" / "failed_drafts").exists()


def test_draft_with_disclosure_flag_appends_logged_disclosure(draft_env, monkeypatch):
    da, tmp, state, notes = draft_env
    import disclosure
    monkeypatch.setattr(da, "stage2_flag", lambda name: name == "disclosure_appendix")
    orig = disclosure.build
    monkeypatch.setattr(disclosure, "build", lambda *a, **k: orig(
        *a, **{**k, "logs_dir": tmp / "logs", "knowledge_dir": tmp / "k", "forum_dir": tmp / "forum",
               "topic_gate": tmp / "tg.md"}))
    state["bodies"] = [GOOD_BODY]
    assert da.draft_article(31) == da.EXIT_OK
    tex = next((tmp / "articles").glob("*_r31.tex")).read_text()
    assert "\\input{" in tex and ".disclosure}" in tex
    assert list((tmp / "articles").glob("*_r31.disclosure.tex"))
    assert list((tmp / "articles").glob("*_r31.disclosure.json"))


def test_draft_failing_gates_is_quarantined_with_exit_2(draft_env):
    da, tmp, state, notes = draft_env
    state["bodies"] = [BAD_BODY, BAD_BODY]
    assert da.draft_article(31) == da.EXIT_GATES
    assert _tracked(tmp) == []                      # nothing reached articles/
    failed = list((tmp / "workspace" / "failed_drafts").iterdir())
    assert len(failed) == 1
    info = json.loads((failed[0] / "FAILED.json").read_text())
    assert info["failed_blocking"] == ["G1"] and "ghost1999" in " ".join(info["failing_items"])
    assert (failed[0] / "gates.json").exists()
    # budget: 2 body calls and 2 fix passes in total, then fail closed
    assert state["calls"].count("draft_body") == 2 and state["calls"].count("draft_fix") == 2
    assert notes and "blocked" in notes[0][0]


def test_draft_fix_pass_repairs_missing_key(draft_env, monkeypatch):
    da, tmp, state, notes = draft_env
    state["bodies"] = [BAD_BODY]

    def fix(kw):
        work = next((tmp / "workspace" / "drafts").iterdir())
        bib = work / "references_r31.bib"
        bib.write_text(bib.read_text() + "@book{ghost1999, author = {Ghost, A.}, title = {T}, year = {1999}}\n")

    state["fix"] = fix
    # ghost1999 now appears in no forum post, so G5 would query the network:
    # keep G5 offline for the test.
    orig = pg.run_all
    monkeypatch.setattr(da.paper_gates, "run_all", lambda *a, **k: orig(*a, **{**k, "offline": True}))
    assert da.draft_article(31) == da.EXIT_OK
    assert state["calls"] == ["draft_body", "draft_fix"]


def test_draft_fix_pass_that_truncates_is_rejected(draft_env):
    da, tmp, state, notes = draft_env
    state["bodies"] = [BAD_BODY, BAD_BODY]

    def fix(kw):
        work = next((tmp / "workspace" / "drafts").iterdir())
        tex = next(work.glob("*_r31.tex"))
        tex.write_text("\\begin{document}stub\\end{document}")

    state["fix"] = fix
    assert da.draft_article(31) == da.EXIT_GATES
    failed = next((tmp / "workspace" / "failed_drafts").iterdir())
    tex = next(failed.glob("*_r31.tex"))
    assert "Committee gatekeeping" in tex.read_text()     # the stub was rolled back


def test_no_body_returns_error_and_main_is_nonzero(draft_env, monkeypatch):
    da, tmp, state, notes = draft_env
    state["bodies"] = []
    assert da.draft_article(31) == da.EXIT_ERROR
    assert state["calls"] == ["draft_body", "draft_body"]
    assert (tmp / "workspace" / "failed_drafts").exists()
    monkeypatch.setattr(da, "arc_depth_ok", lambda r, force=False: True)
    assert da.main(["--round", "31"]) != 0


@pytest.mark.parametrize("mode", ["raise", "abort"])
def test_draft_that_did_not_compile_is_never_published(draft_env, mode):
    """F1: a missing TeX install or a fatal LaTeX error leaves no PDF and no
    .log. G2 fails in the drafting pipeline and nothing reaches articles/."""
    da, tmp, state, notes = draft_env
    state["bodies"] = [GOOD_BODY, GOOD_BODY]
    state["compile"] = mode
    assert da.draft_article(31) == da.EXIT_GATES
    assert _tracked(tmp) == []
    failed = next((tmp / "workspace" / "failed_drafts").iterdir())
    info = json.loads((failed / "FAILED.json").read_text())
    assert info["failed_blocking"] == ["G2"]
    assert any("did not compile" in i or "no PDF" in i for i in info["failing_items"])


def test_stale_pdf_from_an_earlier_compile_is_not_gated_or_published(draft_env):
    """F1 (c): body 1 compiles and fails G1, the fix pass repairs the key but
    the recompile aborts. The first PDF must not stand in for the fixed tex."""
    da, tmp, state, notes = draft_env
    state["bodies"] = [BAD_BODY, BAD_BODY]
    state["compile"] = lambda n: "ok" if n == 1 else "abort"

    def fix(kw):
        work = next((tmp / "workspace" / "drafts").iterdir())
        bib = work / "references_r31.bib"
        bib.write_text(bib.read_text() + "@book{ghost1999, author = {Ghost, A.}, title = {T}, year = {1999}}\n")
    state["fix"] = fix
    assert da.draft_article(31) == da.EXIT_GATES
    assert _tracked(tmp) == []


def test_g2_compile_outputs_and_log_errors():
    ok_log = "Output written on x.pdf (3 pages).\n"
    assert pg.gate_g2("x", log_text=ok_log, compiled=True, pdf_exists=True)["passed"]
    g = pg.gate_g2("x", log_text=None, compiled=True, pdf_exists=False)
    assert not g["passed"] and len(g["details"]["compile_problems"]) == 2
    g = pg.gate_g2("x", log_text="! LaTeX Error: File `missing_tables.tex' not found.\n"
                                 "! Emergency stop.\nNo pages of output.\n", compiled=True, pdf_exists=False)
    assert not g["passed"] and len(g["details"]["log_errors"]) == 3
    # Without compiled=True (a published paper checked as it is) a missing
    # .log or PDF is not a failure, but an error line in a given log is.
    assert pg.gate_g2("x")["passed"]
    assert not pg.gate_g2("x", log_text="! Undefined control sequence.\n")["passed"]


def test_publish_refuses_a_draft_without_its_pdf(draft_env):
    da, tmp, state, notes = draft_env
    work = tmp / "workspace" / "drafts" / "2026-09-25_r31"
    work.mkdir(parents=True)
    (work / "2026-09-25_r31.tex").write_text("x")
    with pytest.raises(RuntimeError, match="no compiled PDF"):
        da._publish(work, "2026-09-25_r31", 31, "2026-09-25", "T", "references_r31.bib")
    assert _tracked(tmp) == []


def test_figure_script_external_write_quarantines_the_draft(draft_env, monkeypatch):
    """F8: an Rscript that writes into $KBL_DATA stops the draft like an
    external write in a forum run: alert, quarantine, exit 3, nothing published."""
    da, tmp, state, notes = draft_env
    import write_guard
    state["bodies"] = [GOOD_BODY.replace(
        r"\section{Conclusion}",
        "\\begin{verbatim}\nlibrary(ggplot2)\nggsave(\"x.pdf\")\n\\end{verbatim}\n"
        r"\begin{figure}\fbox{\parbox{5cm}{Figure 1}}\end{figure}" + "\n" + r"\section{Conclusion}")]
    monkeypatch.setattr(write_guard, "guard_before", lambda: {"repos": {}, "data": {}})
    monkeypatch.setattr(write_guard, "guard_after", lambda before, run_id: [
        {"where": str(tmp / "kna"), "kind": "data_modified", "path": "master_bills_22.parquet",
         "patch": str(tmp / "logs" / "external_writes" / f"{run_id}.patch")}])

    real_run = subprocess.run

    def fake_rscript(cmd, *a, **k):
        if not (cmd and cmd[0] == "Rscript"):
            return real_run(cmd, *a, **k)
        (Path(k["cwd"]) / "fig_1.pdf").write_bytes(b"%PDF-1.4 fake")
        return subprocess.CompletedProcess(cmd, 0, "", "")
    monkeypatch.setattr(subprocess, "run", fake_rscript)
    assert da.draft_article(31) == da.EXIT_EXTERNAL_WRITE == 3
    assert _tracked(tmp) == []
    failed = next((tmp / "workspace" / "failed_drafts").iterdir())
    ext = json.loads((failed / "EXTERNAL_WRITES.json").read_text())
    assert ext[0]["where"] == "$KBL_DATA" and ext[0]["patch"].startswith("logs/external_writes/")
    assert str(tmp) not in (failed / "EXTERNAL_WRITES.json").read_text()
    assert any("external write" in t for t, m in notes)


def test_usage_limit_returns_75(draft_env):
    da, tmp, state, notes = draft_env
    state["failure"] = "usage_limit"
    assert da.draft_article(31) == da.claude_cli.EXIT_USAGE_LIMIT == 75
    assert state["calls"] == ["draft_body"]


def test_kbl_data_unset_fails_fast(draft_env, monkeypatch):
    da, tmp, state, notes = draft_env
    monkeypatch.delenv("KBL_DATA")
    assert da.draft_article(31) == da.EXIT_ERROR
    assert state["calls"] == []


def test_prompt_has_no_two_table_demand_or_manual_references(draft_env):
    da, tmp, state, notes = draft_env
    p = da.build_draft_prompt(31, "drafts/x_content.tex", "drafts/references_r31.bib", "ctx",
                              da.gates_prompt_section({"exists": False}, 6, False))
    assert "at least 2 regression tables" not in p and "MANDATORY at least 2" not in p
    assert "Since no .bib file" not in p
    assert "8,000-10,000 words" in p                  # D-21 is open, the target stays
    assert "/Users/" not in p and 'Sys.getenv("KBL_DATA")' in p
    assert "Do NOT claim a replication archive" in p
    assert "Be strict" not in Path(da.__file__).read_text()


def _earlier_arcs(tmp):
    """Season 1 and Arc 5 material as the real repo holds it: a Season 1
    summary with the Agora demand framing, Arc 5 summaries and the legacy
    R30 posts (082-090 are Arc 5 in forum_index.LEGACY_ARCS)."""
    summ = tmp / "summaries"
    summ.mkdir(exist_ok=True)
    (summ / "round_14.md").write_text("# Round 14 Summary\n\nYeouido Agora brief. Citizen demand for "
                                      "housing research.\n")
    (summ / "round_29.md").write_text("# Round 29 Summary\n\nArc 5 note on the committee channel.\n")
    for n, role in ((88, "literature_scout"), (89, "data_analyst"), (90, "critic")):
        (tmp / "forum" / f"{n:03d}_{role}.md").write_text(
            f'---\nauthor: "x"\n---\n\n# Legacy post {n}\nPaper E cleared for drafting.\n')


def test_draft_context_carries_only_the_active_arc(draft_env):
    """V-10: the draft_body context holds the active arc's round summaries
    and posts only, never Season 1 or an earlier arc."""
    da, tmp, state, notes = draft_env
    _earlier_arcs(tmp)
    for n, role, rnd in ((94, "literature_scout", 32), (95, "data_analyst", 32), (96, "critic", 32),
                         (97, "literature_scout", 33), (98, "data_analyst", 33), (99, "critic", 33)):
        (tmp / "forum" / f"{n:03d}_{role}.md").write_text(
            f'---\nauthor: "x"\nround: {rnd}\narc: 6\nrole: "{role}"\n---\n\n# Arc 6 post {n}\n')
    (tmp / "summaries" / "round_31.md").write_text("# Round 31 Summary\n\nArc 6 opening summary.\n")
    ctx = da.get_all_forum_context(33, 6)
    assert "Arc 6 opening summary." in ctx
    assert "Arc 6 post 94" in ctx and "Arc 6 post 99" in ctx
    assert "091_literature_scout.md" not in ctx          # R31 posts are covered by its summary
    for stale in ("Yeouido", "Agora", "demand", "Arc 5 note", "Paper E cleared", "Round 14", "Round 29"):
        assert stale not in ctx
    # The arc defaults to the drafting round's own arc.
    assert da.get_all_forum_context(33) == ctx


def test_draft_body_prompt_has_no_earlier_arc_or_agora_framing(draft_env, monkeypatch):
    da, tmp, state, notes = draft_env
    _earlier_arcs(tmp)
    prompts = []
    inner = da.claude_cli.run_claude

    def recording(task, prompt_text, **kw):
        prompts.append((task, prompt_text))
        return inner(task, prompt_text, **kw)
    monkeypatch.setattr(da.claude_cli, "run_claude", recording)
    state["bodies"] = [GOOD_BODY]
    assert da.draft_article(31) == da.EXIT_OK
    [(task, prompt)] = [p for p in prompts if p[0] == "draft_body"]
    assert "We cite cox2005." in prompt                  # the arc's own posts are there
    for stale in ("Yeouido", "Agora", "Citizen demand", "Arc 5 note", "Paper E cleared", "Legacy post"):
        assert stale not in prompt


def test_generated_figure_r_uses_kbl_data(tmp_path, monkeypatch):
    da = _load_draft()
    arts = tmp_path / "articles"
    arts.mkdir()
    tex = arts / "2026-09-30_r31.tex"
    tex.write_text("\\begin{verbatim}\nlibrary(ggplot2)\nDATA <- Sys.getenv(\"KBL_DATA\")\n"
                   "ggsave(\"/abs/fig_9.pdf\", width = 7)\n\\end{verbatim}\n"
                   "\\fbox{\\parbox{1cm}{placeholder}}")
    monkeypatch.setattr(da, "run_rscript", lambda r, d, run_id, timeout=120: subprocess.CompletedProcess([], 1, "", "no R"))
    da.execute_r_figures(tex)
    r = (arts / "figures" / tex.stem / "fig_1.R").read_text()
    assert 'Sys.getenv("KBL_DATA")' in r and "/Users/" not in r and 'ggsave("fig_1.pdf"' in r


def test_failed_drafts_are_gitignored():
    out = subprocess.run(["git", "check-ignore", "-q", "workspace/failed_drafts/x/y.tex"], cwd=ROOT)
    assert out.returncode == 0


# ---------------------------------------------------------------------------
# M13 item 5: dictionary hashes
# ---------------------------------------------------------------------------

def test_dictionary_hash_change_is_refused(tmp_path):
    import hashlib
    da = _load_draft()
    d = tmp_path / "round_31.jsonl"
    d.write_text('{"member_id": "A", "category": "x"}\n')
    (tmp_path / "HASHES.json").write_text(json.dumps(
        {"round_31.jsonl": {"sha256": hashlib.sha256(d.read_bytes()).hexdigest(), "run_id": "r31"}}))
    assert da.check_dictionary_hash(d) == "match"
    d.write_text('{"member_id": "A", "category": "y"}\n')
    with pytest.raises(SystemExit) as e:
        da.check_dictionary_hash(d)
    assert "M13" in str(e.value)


def test_dictionary_hash_legacy_and_round25_exemption(tmp_path):
    da = _load_draft()
    d = tmp_path / "round_24.jsonl"
    d.write_text("{}\n")
    assert da.check_dictionary_hash(d) == "unrecorded"
    r25 = tmp_path / "round_25.jsonl"
    r25.write_text("{}\n")
    (tmp_path / "HASHES.json").write_text(json.dumps({"round_25.jsonl": {"sha256": "0" * 64}}))
    assert da.check_dictionary_hash(r25) == "exempt"


# ---------------------------------------------------------------------------
# build_site
# ---------------------------------------------------------------------------

def test_build_site_renders_post_with_orchestrator_keys(tmp_path, monkeypatch):
    import build_site as bs
    import forum_index
    forum = tmp_path / "forum"
    forum.mkdir()
    text = ('---\nauthor: "Critic (Theory & Methods)"\ndate: "2026-09-30 10:00"\ntype: [review]\n'
            'references: ["10.2307/1958780"]\n---\n\n# A Review\n\n```yaml\nscoring:\n  research_novelty: 3\n'
            '  verdict: revise\n```\n\nBody text.\n')
    post = forum / "093_critic.md"
    post.write_text(text)
    for n, role in ((91, "literature_scout"), (92, "data_analyst")):
        (forum / f"{n:03d}_{role}.md").write_text(f'---\nauthor: "x"\n---\n\n# {role}\n')
    for p in forum.glob("*.md"):
        role = p.stem.split("_", 1)[1]
        forum_index.set_frontmatter_keys(p, {
            "round": 31, "arc": 6, "role": role, "run_id": f"r31_{role}_x", "model": "claude-opus-5-5",
            "models_used": ["claude-opus-5-5"], "claude_code_version": "2.1.283", "effort": "high",
            "num_turns": 42, "terminal_reason": "success", "attempt": 1})
    before = bs.parse_post(post)
    assert before["author"] == "Critic (Theory & Methods)" and before["title"] == "A Review"
    assert "Body text." in before["body_html"]
    monkeypatch.setattr(bs, "FORUM_DIR", forum)
    posts = []
    for m in forum_index.index(forum_dir=forum):
        p = bs.parse_post(m["path"])
        p["round"], p["arc"] = m["round"], m["arc"]
        posts.append(p)
    html = bs.build_index(posts)
    assert "Round 31" in html and "A Review" in html
    page = bs.build_post_page(before)
    assert "A Review" in page and "run_id" not in page


@needs_papers
def test_build_site_grouping_matches_legacy_sequence():
    """Rounds from forum_index equal the old Critic-closes-a-round grouping
    on the 90 real posts (snapshot of the round structure)."""
    import build_site as bs
    import forum_index
    posts = [bs.parse_post(p) for p in sorted(bs.FORUM_DIR.glob("*.md"))]
    old = {k: [p["filename"] for p in v] for k, v in bs.group_rounds(posts).items()}
    meta = {m["path"].name: m for m in forum_index.index()}
    for p in posts:
        p["round"] = meta[p["filename"]]["round"]
    new = {k: [p["filename"] for p in v] for k, v in bs.group_rounds(posts).items()}
    assert old == new


def test_build_site_skips_blocked_and_failed_drafts(tmp_path, monkeypatch):
    import build_site as bs
    arts = tmp_path / "articles"
    arts.mkdir()
    for stem in ("2026-09-30_r31", "2026-09-30_r32"):
        (arts / f"{stem}.tex").write_text(f"\\title{{Paper {stem}}}\nbody")
    reports = tmp_path / "gates"
    reports.mkdir()
    (reports / "2026-09-30_r32.gates.json").write_text(json.dumps({"ok": False}))
    (reports / "2026-09-30_r31.gates.json").write_text(json.dumps({"ok": True}))
    monkeypatch.setattr(bs, "ARTICLES_DIR", arts)
    monkeypatch.setattr(bs, "GATE_REPORTS_DIR", reports)
    monkeypatch.setattr(bs, "FAILED_DRAFTS_DIR", tmp_path / "workspace" / "failed_drafts")
    html = bs._build_article_list()
    assert "Paper 2026-09-30_r31" in html and "Paper 2026-09-30_r32" not in html
    assert bs._in_failed_drafts(tmp_path / "workspace" / "failed_drafts" / "x" / "y.tex")


def test_recompile_copy_brings_flat_and_namespaced_figures(tmp_path, monkeypatch):
    """The copy compiles against the same figure files as the original,
    including the flat figures/<name>.pdf that older papers use."""
    src = tmp_path / "src"
    (src / "figures" / "p").mkdir(parents=True)
    (src / "figures" / "old.pdf").write_bytes(b"%PDF")
    (src / "figures" / "p" / "fig_1.pdf").write_bytes(b"%PDF")
    (src / "p.tex").write_text("\\includegraphics{figures/old.pdf}\\includegraphics{figures/p/fig_1.pdf}")
    monkeypatch.setattr(pg.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 0))
    paths = pg.recompile_copy(src / "p.tex", None, tmp_path / "out")
    assert (tmp_path / "out" / "figures" / "old.pdf").exists()
    assert (tmp_path / "out" / "figures" / "p" / "fig_1.pdf").exists()
    g = pg.gate_g2(paths["tex"].read_text(), tex_dir=tmp_path / "out")
    assert g["details"]["missing_graphics"] == []


def test_forum_rules_gate_table_matches_the_code():
    """FID-F1: the public Paper Gates table lists exactly the gates
    paper_gates.py runs, with the same blocking status."""
    import re
    rules = (ROOT / "FORUM_RULES.md").read_text(encoding="utf-8")
    section = rules[rules.index("## Paper Gates"):]
    section = section[:section.index("\n---\n")]
    rows = re.findall(r"^\| (G\w+) \| .* \| ([^|]+) \|$", section, re.MULTILINE)
    assert [gid for gid, _ in rows] == sorted(pg.GATE_NAMES)
    for gid, status in rows:
        assert status.strip().startswith("blocking") == pg.BLOCKING[gid], gid
    assert f"G1 to G{len(pg.GATE_NAMES)}" in section.splitlines()[0]
    blocking = [g for g in sorted(pg.GATE_NAMES) if pg.BLOCKING[g]]
    assert "paper gate ids G1 to G6 match `paper_gates.py`" in rules
    assert f"({', '.join(blocking[:-1])} and {blocking[-1]} below)" in rules


def test_recompile_that_leaves_no_pdf_fails_g2(tmp_path, monkeypatch):
    """COR-F1: paper_gates --recompile has just compiled the copy, so a copy
    that produced no PDF or .log (a missing TeX install) fails G2."""
    tex = tmp_path / "p.tex"
    tex.write_text("\\begin{document}\nText.\n\\end{document}\n")
    monkeypatch.setattr(pg.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("xelatex")))
    assert pg.main([str(tex), "--recompile", "--no-references"]) == 2


def test_external_write_before_a_usage_limit_still_stops_the_draft(draft_env, monkeypatch):
    """COR-F8: an external write that happens before a usage limit is not
    lost behind the pause. The draft stops with exit 3 and an alert."""
    da, tmp, state, notes = draft_env
    import write_guard
    state["bodies"] = [BAD_BODY.replace(
        r"\section{Conclusion}",
        "\\begin{verbatim}\nlibrary(ggplot2)\nggsave(\"x.pdf\")\n\\end{verbatim}\n"
        r"\begin{figure}\fbox{\parbox{5cm}{Figure 1}}\end{figure}" + "\n" + r"\section{Conclusion}")]
    monkeypatch.setattr(write_guard, "guard_before", lambda: {"repos": {}, "data": {}})
    monkeypatch.setattr(write_guard, "guard_after", lambda before, run_id: [
        {"where": str(tmp / "kna"), "kind": "data_modified", "path": "master_bills_22.parquet",
         "patch": str(tmp / "logs" / "external_writes" / f"{run_id}.patch")}])
    real_run = subprocess.run

    def fake_rscript(cmd, *a, **k):
        if not (cmd and cmd[0] == "Rscript"):
            return real_run(cmd, *a, **k)
        (Path(k["cwd"]) / "fig_1.pdf").write_bytes(b"%PDF-1.4 fake")
        return subprocess.CompletedProcess(cmd, 0, "", "")
    monkeypatch.setattr(subprocess, "run", fake_rscript)
    orig = da.claude_cli.run_claude

    def run_claude(task, prompt_text, **kw):
        if task == "draft_fix":   # the gate-driven fix pass hits the usage limit
            state["failure"] = "usage_limit"
        return orig(task, prompt_text, **kw)
    monkeypatch.setattr(da.claude_cli, "run_claude", run_claude)
    assert da.draft_article(31) == da.EXIT_EXTERNAL_WRITE
    assert _tracked(tmp) == []
    failed = next((tmp / "workspace" / "failed_drafts").iterdir())
    assert (failed / "EXTERNAL_WRITES.json").exists()
    assert "usage limit" in json.loads((failed / "FAILED.json").read_text())["reason"]
    assert any("external write" in t for t, m in notes)


def test_auto_drafting_stops_after_an_external_write(draft_env, monkeypatch):
    """COR-F8: in auto-detect mode an external-write stop ends the run, as a
    usage limit does, so no further round is drafted before the stop is checked."""
    da, tmp, state, notes = draft_env
    monkeypatch.setattr(da, "find_pursue_verdicts", lambda: [{"round": 31}, {"round": 32}])
    monkeypatch.setattr(da, "arc_depth_ok", lambda r, force=False: True)
    drafted = []
    monkeypatch.setattr(da, "draft_article", lambda r: drafted.append(r) or da.EXIT_EXTERNAL_WRITE)
    assert da.main([]) == da.EXIT_EXTERNAL_WRITE
    assert drafted == [31]

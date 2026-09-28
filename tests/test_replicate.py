#!/usr/bin/env python3
"""Tests for replicate.py (M18). Packages are built under tmp_path only; the
real replication/ tree is never written. The round scripts in workspace/ are
gitignored, so the tests that read them skip on a fresh clone."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import replicate as rp  # noqa: E402

HOME_PY = "/Users/someone/code"


@pytest.fixture(autouse=True)
def _no_private_patterns(tmp_path, monkeypatch):
    monkeypatch.setenv("KNA_LEAK_PATTERNS", str(tmp_path / "none.txt"))


def test_rewrite_python_paths():
    src = (f"import pandas as pd\n"
           f"DATA = '{HOME_PY}/kna/data/processed'\n"
           f"WS = '{HOME_PY}/kna-research-agents/workspace'\n"
           f"b = pd.read_parquet(f'{HOME_PY}/kna/data/processed/master_bills_{{a}}.parquet')\n"
           f"df = pd.read_csv('{HOME_PY}/kna-research-agents/workspace/r28/bills_panel.csv')\n"
           f"R = pd.read_csv('workspace/r25/roster.csv')\n"
           f"# Inputs: {HOME_PY}/kna/data/processed stays in a comment untouched\n")
    out, rw = rp.rewrite_paths(src, "py")
    body = out.split("\n", 1)[1]
    assert out.startswith("import os")
    assert 'DATA = os.environ["KBL_DATA"]' in out
    assert "WS = '.'" in out
    assert "os.path.join(os.environ[\"KBL_DATA\"], f'master_bills_{a}.parquet')" in out
    assert "pd.read_csv('r28/bills_panel.csv')" in out
    assert "pd.read_csv('r25/roster.csv')" in out
    assert "/Users/" not in body.split("# Inputs")[0]
    assert {r["kind"] for r in rw} == {"kna_data_prefix", "forum_workspace", "repo_relative_workspace"}
    assert all(set(r) == {"line", "kind"} for r in rw)       # no raw private text recorded


def test_rewrite_r_paths():
    src = (f'Sys.setenv(KBL_DATA = "{HOME_PY}/kna/data/processed")\n'
           f'data_dir <- "/Users/someone/kna/data/processed"\n'
           f'ggsave("{HOME_PY}/kna-research-agents/articles/figures/2026-08-24_r30/fig_1.pdf")\n')
    out, rw = rp.rewrite_paths(src, "R")
    assert "/Users/" not in out
    assert 'data_dir <- Sys.getenv("KBL_DATA")' in out
    assert 'ggsave("figures/2026-08-24_r30/fig_1.pdf")' in out
    assert [r["kind"] for r in rw] == ["kbl_data_setenv_removed", "kna_data_prefix", "forum_figures"]


def _fake_tree(tmp_path, extra_line=""):
    ws = tmp_path / "workspace"
    (ws / "r31").mkdir(parents=True)
    (ws / "r31" / "analyze.py").write_text(
        f"import pandas as pd\nDATA = '{HOME_PY}/kna/data/processed'\n"
        f"m = pd.read_parquet(f'{{DATA}}/members_22.parquet')\n{extra_line}")
    (ws / "r31" / "panel.csv").write_text("a,b\n1,2\n")      # data: never shipped
    (ws / "r32").mkdir()
    (ws / "r32" / "robust.R").write_text('x <- read.csv("workspace/r31/out.csv")\n')
    arts = tmp_path / "articles"
    (arts / "figures" / "2026-09-30_r32").mkdir(parents=True)
    (arts / "2026-09-30_r32.tex").write_text("\\title{T}")
    (arts / "figures" / "2026-09-30_r32" / "fig_1.R").write_text(
        'DATA <- Sys.getenv("KBL_DATA")\nggsave("fig_1.pdf")\n')
    cards = tmp_path / "cards"
    cards.mkdir()
    (cards / "R31.json").write_text('{"round": 31}')
    return ws, arts, cards


def test_build_package_scripts_and_cards_only(tmp_path):
    ws, arts, cards = _fake_tree(tmp_path)
    out = tmp_path / "out"
    m = rp.build(6, out_root=out, workspace_dir=ws, articles_dir=arts, cards_dir=cards,
                 logs_dir=tmp_path / "logs", rounds=[31, 32])
    pkg = out / "arc_6"
    assert m["build"]["ok"], m["build"]
    paths = sorted(f["path"] for f in m["files"])
    assert paths == ["cards/R31.json", "figures/2026-09-30_r32/fig_1.R", "r31/analyze.py", "r32/robust.R"]
    assert not (pkg / "r31" / "panel.csv").exists()
    assert (pkg / "README.md").exists() and "available on request" in (pkg / "README.md").read_text()
    on_disk = json.loads((pkg / "MANIFEST.json").read_text())
    assert on_disk["files"] == m["files"] and on_disk["verify"] == {"passed": None}
    assert "/Users/" not in (pkg / "MANIFEST.json").read_text()
    assert "/Users/" not in (pkg / "r31" / "analyze.py").read_text()
    assert m["commands"] == [{"cmd": "python3 r31/analyze.py", "round": 31},
                             {"cmd": "Rscript r32/robust.R", "round": 32}]
    assert m["provenance"]["31"] == {"source": "unrecorded"}
    assert any(d["name"] == "members_22.parquet" for d in m["data_inputs"])


def test_build_fails_on_other_absolute_home_path(tmp_path):
    ws, arts, cards = _fake_tree(tmp_path, extra_line="x = open('/Users/someone/Documents/notes.txt')\n")
    m = rp.build(6, out_root=tmp_path / "out", workspace_dir=ws, articles_dir=arts, cards_dir=cards,
                 logs_dir=tmp_path / "logs", rounds=[31, 32])
    assert not m["build"]["ok"]
    assert m["build"]["errors"][0]["path"] == "r31/analyze.py"
    assert not (tmp_path / "out" / "arc_6" / "r31" / "analyze.py").exists()


def test_provenance_uses_sidecars_then_reconstruction(tmp_path):
    logs = tmp_path / "logs" / "r31"
    logs.mkdir(parents=True)
    (logs / "r31_data_analyst_x.sidecar.json").write_text(json.dumps({
        "task": "agent", "role": "data_analyst", "run_id": "r31_data_analyst_x", "round": 31,
        "model": "claude-opus-5-5", "models_used": ["claude-opus-5-5"], "cli_version": "2.1.283",
        "effort": "high", "ok": True}))
    prov = rp.round_provenance([28, 31], logs_dir=tmp_path / "logs")
    assert prov["28"]["model"] == "claude-fable-5" and "reconstructed" in prov["28"]["source"]
    assert prov["31"]["runs"][0]["model"] == "claude-opus-5-5"
    assert rp._analyst_run_id(31, prov) == "r31_data_analyst_x"


def test_verify_runs_commands_in_a_copy(tmp_path, monkeypatch):
    ws, arts, cards = _fake_tree(tmp_path)
    (ws / "r31" / "analyze.py").write_text(
        "import json, os\n"
        "members = os.path.join(os.environ['KBL_DATA'], 'members_22.parquet')\n"
        "json.dump({'estimate': -0.86, 'se': 1.10}, open('r31_out.json', 'w'))\n")
    (ws / "r32" / "robust.R").unlink()
    out = tmp_path / "out"
    rp.build(6, out_root=out, workspace_dir=ws, articles_dir=arts, cards_dir=cards,
             logs_dir=tmp_path / "logs", rounds=[31, 32])
    mpath = out / "arc_6" / "MANIFEST.json"
    m = json.loads(mpath.read_text())
    m["outputs"] = [{"path": "r31_out.json", "values": {"estimate": -0.86, "se": 1.10}, "tolerance": 0.005}]
    mpath.write_text(json.dumps(m))
    monkeypatch.delenv("KBL_DATA", raising=False)
    res = rp.verify(6, out_root=out)
    assert res["passed"] is False and "KBL_DATA" in res["error"]
    monkeypatch.setenv("KBL_DATA", str(tmp_path))
    res = rp.verify(6, out_root=out)
    assert res["passed"] is True, res
    assert not (out / "arc_6" / "r31_out.json").exists()       # outputs stay in the temp copy
    assert json.loads(mpath.read_text())["verify"]["passed"] is True
    m = json.loads(mpath.read_text())
    m["outputs"][0]["values"]["estimate"] = -0.72
    mpath.write_text(json.dumps(m))
    res = rp.verify(6, out_root=out)
    assert res["passed"] is False and res["outputs"][0]["differs"]["estimate"]["got"] == -0.86


def test_dictionary_join_synthetic():
    km = {"keys": ["cohort", "uid"], "coded_field": "opposed"}
    d = [{"cohort": 1, "uid": "7", "opposed": 1}, {"cohort": 1, "uid": "8", "opposed": 0}]
    s = [{"cohort": "1", "uid": "7", "opposed": "1"}, {"cohort": "1", "uid": "8", "opposed": "0.0"}]
    assert rp.validate_dictionary_join(km, d, s)["ok"]
    s[1]["opposed"] = "1"
    r = rp.validate_dictionary_join(km, d, s)
    assert not r["ok"] and r["mismatches"] == 1
    r = rp.validate_dictionary_join(km, [{"cohort": 1, "uid": "7"}], s)
    assert not r["ok"] and "no 'opposed' field" in r["problems"][0]


def _git_show(rev_path):
    try:
        return subprocess.run(["git", "show", rev_path], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None


@pytest.mark.skipif(not (ROOT / "workspace" / "r25" / "analysis_sample_corrected.csv").exists(),
                    reason="R25 analysis sample (gitignored workspace) not present")
def test_dictionary_join_arc4_current_fails_pre_d1f05bc_passes(tmp_path):
    """M06 part 4: against the stored Version 1 sample, the Arc 4 keys reject
    the round_25.jsonl the R27 rerun wrote and accept the version before d1f05bc."""
    import csv
    km = {k: rp.DICTIONARY_KEY_MAPS[4][k] for k in ("keys", "coded_field", "sample")}
    with open(ROOT / km["sample"], encoding="utf-8", newline="") as f:
        sample = list(csv.DictReader(f))
    path = ROOT / "knowledge" / "hand_coding" / "round_25.jsonl"
    current = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    assert not rp.validate_dictionary_join(km, current, sample)["ok"]
    old = _git_show("d1f05bc^:knowledge/hand_coding/round_25.jsonl")
    if old is None:
        pytest.skip("git history not available")
    pre = [json.loads(l) for l in old.splitlines() if l.strip()]
    assert rp.validate_dictionary_join(km, pre, sample)["ok"]


@pytest.mark.skipif(not (ROOT / "workspace" / "r25" / "analysis_sample_corrected.csv").exists()
                    or not (ROOT / "knowledge" / "hand_coding" / "round_25.v2.jsonl").exists(),
                    reason="R25 sample or the v2 dictionary not present")
def test_arc4_key_map_points_at_v2_dictionary_and_joins():
    """The Arc 4 key map names round_25.v2.jsonl, drops its header row and
    applies the Version 2 recode, after which every sample row matches."""
    km = rp.DICTIONARY_KEY_MAPS[4]
    assert km["dictionary"].endswith("round_25.v2.jsonl") and km["skip_header"] is True
    res = rp.check_key_map(km)
    assert res["ok"], res["problems"]
    assert res["header_rows_skipped"] == 1 and res["sample_rows_recoded"] == 6
    assert res["unmatched"] == 0 and res["mismatches"] == 0
    # Without the recode the stored Version 1 sample disagrees on the six pairs.
    res = rp.check_key_map({**km, "sample_recode": None})
    assert not res["ok"] and res["mismatches"] == 6


@pytest.mark.skipif(not (ROOT / "workspace" / "r28").is_dir(), reason="Arc 5 scripts (gitignored) not present")
def test_build_real_arc5_into_tmp(tmp_path):
    m = rp.build(5, out_root=tmp_path)
    assert m["build"]["ok"], m["build"]["errors"]
    assert m["rounds"] == [28, 29, 30]
    for f in (tmp_path / "arc_5").rglob("*"):
        if f.is_file():
            assert "/Users/" not in f.read_text(encoding="utf-8"), f
    assert all("reconstructed" in m["provenance"][str(r)]["source"] for r in (28, 29, 30))


# ---------------------------------------------------------------------------
# 2026-09-26: dependency order, workdirs, extras, scrubbed stderr, key maps
# ---------------------------------------------------------------------------

def test_script_io_reads_and_writes():
    py = ("import json, pandas as pd\n"
          "R = pd.read_csv('r25/roster.csv')\n"
          "P.drop(columns='prefixes').to_csv('r25/panel.csv', index=False)\n"
          "with open('knowledge/hand_coding/round_25.jsonl', 'w') as f:\n"
          "    pass\n"
          "d = [json.loads(l) for l in open('knowledge/hand_coding/round_26.jsonl')]\n"
          "# pd.read_csv('r99/commented.csv')\n"
          "x = pd.read_parquet('/abs/path/ignored.parquet')\n")
    reads, writes = rp.script_io(py)
    assert reads == {"r25/roster.csv", "knowledge/hand_coding/round_26.jsonl"}
    assert writes == {"r25/panel.csv", "knowledge/hand_coding/round_25.jsonl"}
    r_reads, r_writes = rp.script_io('df <- read.csv("r28/bills_panel.csv")\nggsave("fig_1.pdf", p)\n')
    assert r_reads == {"r28/bills_panel.csv"} and r_writes == {"fig_1.pdf"}


def test_order_commands_writers_before_readers_then_names():
    entries = [
        {"path": "r25/analyze.py", "text": "pd.read_csv('r25/panel.csv')\n", "round": 25, "kind": "script"},
        {"path": "r25/build.py", "text": "P.to_csv('r25/panel.csv')\n", "round": 25, "kind": "script"},
        {"path": "r26/robust.py", "text": "x = 1\n", "round": 26, "kind": "script"},
        {"path": "r26/build_more.py", "text": "x = 2\n", "round": 26, "kind": "script"},
        {"path": "figures/p/fig_1.R", "text": 'ggsave("fig_1.pdf")\n', "round": 26, "kind": "figure_script"},
        {"path": "v2/prep.py", "text": "d.to_parquet('meta.parquet')\n", "round": None, "kind": "prep_script"},
        {"path": "r24/uses_meta.py", "text": "pd.read_parquet('meta.parquet')\n", "round": 24, "kind": "script"},
    ]
    ordered, order = rp.order_commands(entries)
    paths = [e["path"] for e in ordered]
    # meta.parquet: the prep script (round None) must precede its round-24 reader.
    assert paths.index("v2/prep.py") < paths.index("r24/uses_meta.py")
    # The file-name order would put analyze.py first. The dependency wins.
    assert paths.index("r25/build.py") < paths.index("r25/analyze.py")
    # No visible dependency: build-before-analyze by name within the round.
    assert paths.index("r26/build_more.py") < paths.index("r26/robust.py")
    assert paths[-1] == "figures/p/fig_1.R"
    assert {"before": "r25/build.py", "after": "r25/analyze.py", "via": "r25/panel.csv"} in order["edges"]
    assert order["cycle_broken"] == []


def test_script_io_sees_pathlib_multiline_and_variable_writes():
    """The four write shapes of the Paper E Version 2 scripts, which the
    same-line rule alone read as inputs (so key_values.py sorted first)."""
    py = ("import os, json\n"
          "from pathlib import Path\n"
          "OUTDIR = Path(os.environ.get('PAPER_E_OUT', 'v2'))\n"
          "t = json.loads((OUTDIR / 'tables_v2.json').read_text(encoding='utf-8'))\n"
          "(OUTDIR / 'key_values.json').write_text(json.dumps(t))\n"
          "m[['a', 'b']].to_csv(\n"
          "    os.path.join(OUTDIR, 'seniority_derived.csv'), index=False)\n"
          "s = pd.read_csv(OUTDIR / 'panel.csv')\n"
          "OUT = Path(os.environ.get('PAPER_E_OUT', 'v2')) / 'recode_tables_v2.json'\n"
          "OUT.write_text('{}')\n"
          "IN = OUTDIR / 'kept_as_input.csv'\n"
          "x = pd.read_csv(IN)\n"
          "with open(OUTDIR / 'log.txt', 'w') as f:\n"
          "    pass\n"
          "Path('fig.pdf').open('w')\n")
    reads, writes = rp.script_io(py)
    assert writes == {"key_values.json", "seniority_derived.csv", "recode_tables_v2.json", "log.txt", "fig.pdf"}
    assert reads == {"tables_v2.json", "panel.csv", "kept_as_input.csv"}
    # R: a path variable passed to a write call, and an f-string base directory.
    r_reads, r_writes = rp.script_io('out <- "fig_2.pdf"\nggsave(out, p, width = 7)\n')
    assert r_writes == {"fig_2.pdf"} and r_reads == set()
    ws_reads, _ = rp.script_io("p = pd.read_csv(f'{WS}/r28/bills_panel.csv')\n")
    assert ws_reads == {"r28/bills_panel.csv"}


def test_order_commands_uses_declared_hints():
    entries = [
        {"path": "v2/a_report.py", "text": "x = 1\n", "round": None, "kind": "correction_script"},
        {"path": "v2/z_compute.py", "text": "y = 2\n", "round": None, "kind": "correction_script"},
    ]
    ordered, _ = rp.order_commands(entries)
    assert [e["path"] for e in ordered] == ["v2/a_report.py", "v2/z_compute.py"]
    ordered, order = rp.order_commands(entries, [{"before": "v2/z_compute.py", "after": "v2/a_report.py"}])
    assert [e["path"] for e in ordered] == ["v2/z_compute.py", "v2/a_report.py"]
    assert order["edges"] == [{"before": "v2/z_compute.py", "after": "v2/a_report.py", "via": rp.DECLARED_VIA}]
    with pytest.raises(ValueError):
        rp.order_commands(entries, [{"before": "v2/missing.py", "after": "v2/a_report.py"}])


def test_build_extra_after_declares_an_edge(tmp_path):
    ws, arts, prep = _dep_tree(tmp_path)
    late = tmp_path / "aaa_summary.py"
    late.write_text("print('summary')\n")
    m = rp.build(7, out_root=tmp_path / "out", workspace_dir=ws, articles_dir=arts,
                 cards_dir=tmp_path / "cards", logs_dir=tmp_path / "logs", rounds=[31],
                 extras=[{"src": prep, "dest": "v2/prep.py", "kind": "prep_script"},
                         {"src": late, "dest": "v2/aaa_summary.py", "after": ["r31/analyze.py"]}])
    cmds = [c["cmd"] for c in m["commands"]]
    assert cmds.index("python3 r31/analyze.py") < cmds.index("python3 v2/aaa_summary.py")
    assert {"before": "r31/analyze.py", "after": "v2/aaa_summary.py", "via": rp.DECLARED_VIA} in m["order"]["edges"]



def test_readme_names_only_the_inputs_and_contents_the_package_has():
    base = {"built": "2026-09-26T00:00:00", "rounds": [28], "commands": [{"cmd": "python3 r28/build.py"}],
            "files": [{"path": "r28/build.py", "kind": "script", "round": 28},
                      {"path": "v2/x.py", "kind": "correction_script", "round": None}]}
    kna_only = rp._readme(5, {**base, "data_inputs": [{"source": "KNA (KBL_DATA)", "name": "m.parquet"}]})
    assert "KBL_DATA environment variable." in kna_only and "`data/`" not in kna_only
    assert "prediction cards" not in kna_only and "(no round, correction_script)" in kna_only
    hearings = rp._readme(4, {**base, "data_inputs": [
        {"source": "kr-hearings release (repository data/)", "name": "data/d.parquet"}],
        "files": base["files"] + [{"path": "cards/R28.json", "kind": "card", "round": 28}]})
    assert "need no KBL_DATA" in hearings and "analysis scripts and prediction cards only" in hearings

PAPER_E_V2 = ROOT / "workspace" / "redesign_2026-09" / "v2_work" / "paper_e"


@pytest.mark.skipif(not (ROOT / "workspace" / "r28").is_dir() or not (PAPER_E_V2 / "key_values.py").exists(),
                    reason="Arc 5 scripts (gitignored) not present")
def test_real_arc5_with_v2_extras_orders_without_hand_edits(tmp_path):
    extras = [{"src": PAPER_E_V2 / s, "dest": f"v2/{s}", "kind": "correction_script"}
              for s in ("seniority_check.py", "tables_v2.py", "recode_tables_v2.py", "key_values.py")]
    m = rp.build(5, out_root=tmp_path, extras=extras, figure_commands=True)
    cmds = [c["cmd"].split()[-1] for c in m["commands"]]
    assert cmds[0] == "r28/build.py"
    assert cmds.index("v2/seniority_check.py") < cmds.index("v2/recode_tables_v2.py") < cmds.index("v2/key_values.py")
    assert cmds.index("v2/tables_v2.py") < cmds.index("v2/key_values.py")
    assert all(c.startswith("figures/") for c in cmds[-3:])


def test_order_commands_breaks_a_cycle_on_the_record():
    entries = [
        {"path": "r1/a.py", "text": "pd.read_csv('b.csv')\nX.to_csv('a.csv')\n", "round": 1, "kind": "script"},
        {"path": "r1/b.py", "text": "pd.read_csv('a.csv')\nY.to_csv('b.csv')\n", "round": 1, "kind": "script"},
    ]
    ordered, order = rp.order_commands(entries)
    assert [e["path"] for e in ordered] == ["r1/a.py", "r1/b.py"]
    assert order["cycle_broken"] == ["r1/a.py"]


def test_scrub_stderr_removes_package_and_home_paths(tmp_path):
    tmp = tmp_path / "pkg"
    text = (f'File "{tmp}/r25/build.py", line 3\n'
            'File "/Users/someone/Library/Python/3.12/site-packages/pandas/io/common.py", line 873\n'
            "FileNotFoundError: r25/roster.csv\n")
    out = rp.scrub_stderr(text, tmp)
    assert "<package>/r25/build.py" in out and "<home>/Library/Python" in out
    assert "/Users/" not in out and str(tmp) not in out


def _dep_tree(tmp_path):
    """build.py writes the panel and a dictionary that analyze.py reads. The
    file names sort analyze.py first, so only the dependency order can pass."""
    ws = tmp_path / "workspace"
    (ws / "r31").mkdir(parents=True)
    (ws / "r31" / "build.py").write_text(
        "import csv, json, sys\n"
        "rows = [dict(zip(['cohort', 'uid', 'y'], r)) for r in csv.reader(open('workspace/meta.csv'))]\n"
        "with open('workspace/r31/panel.csv', 'w') as f:\n"
        "    f.write('uid,y\\n' + ''.join(f\"{r['uid']},{r['y']}\\n\" for r in rows))\n"
        "with open('knowledge/hand_coding/round_31.jsonl', 'w') as f:\n"
        "    f.write(json.dumps({'uid': '7'}) + '\\n')\n"
        "sys.stderr.write('/' + 'Users/someone/Library/x.py: warning\\n')\n")
    (ws / "r31" / "analyze.py").write_text(
        "import csv, json\n"
        "rows = list(csv.DictReader(open('workspace/r31/panel.csv')))\n"
        "d = [json.loads(l) for l in open('knowledge/hand_coding/round_31.jsonl')]\n"
        "json.dump({'n': len(rows), 'mean_y': sum(float(r['y']) for r in rows) / len(rows)},\n"
        "          open('r31/out.json', 'w'))\n")
    arts = tmp_path / "articles"
    arts.mkdir()
    prep = tmp_path / "prep.py"
    prep.write_text("with open('meta.csv', 'w') as f:\n    f.write('1,7,2.0\\n1,8,4.0\\n')\n")
    return ws, arts, prep


def test_build_and_verify_with_dependencies_extras_and_workdirs(tmp_path, monkeypatch):
    ws, arts, prep = _dep_tree(tmp_path)
    out = tmp_path / "out"
    m = rp.build(7, out_root=out, workspace_dir=ws, articles_dir=arts, cards_dir=tmp_path / "cards",
                 logs_dir=tmp_path / "logs", rounds=[31],
                 extras=[{"src": prep, "dest": "v2/prep.py", "kind": "prep_script", "role": "test"}],
                 outputs=[{"path": "r31/out.json", "values": {"n": 2, "mean_y": 3.0}}],
                 notes={"additions": {"by": "test"}}, readme_extra="## Extra\n\nA note.")
    assert m["build"]["ok"], m["build"]
    assert [c["cmd"] for c in m["commands"]] == [
        "python3 v2/prep.py", "python3 r31/build.py", "python3 r31/analyze.py"]
    assert m["workdirs"] == ["knowledge/hand_coding", "r31"]
    assert m["additions"] == {"by": "test"}
    assert {"source": "intermediate produced inside the package", "name": "meta.csv",
            "produced_by": "v2/prep.py"} in m["data_inputs"]
    readme = (out / "arc_7" / "README.md").read_text()
    assert "need no KBL_DATA" in readme and "## Extra" in readme and "kna software package" in readme
    assert "Inputs produced outside this package" not in readme
    monkeypatch.delenv("KBL_DATA", raising=False)
    res = rp.verify(7, out_root=out)          # no KNA inputs, so no KBL_DATA needed
    assert res["passed"] is True, res
    tails = " ".join(c["stderr_tail"] for c in res["commands"])
    assert "<home>/Library/x.py" in tails and "/Users/" not in tails
    assert "/Users/" not in (out / "arc_7" / "MANIFEST.json").read_text()
    assert not (tmp_path / "knowledge").exists()        # scripts wrote only in the temp copy
    assert not (out / "arc_7" / "r31" / "out.json").exists()


def test_build_rejects_extra_that_leaves_the_package(tmp_path):
    ws, arts, prep = _dep_tree(tmp_path)
    with pytest.raises(ValueError):
        rp.build(7, out_root=tmp_path / "out", workspace_dir=ws, articles_dir=arts,
                 cards_dir=tmp_path / "cards", logs_dir=tmp_path / "logs", rounds=[31],
                 extras=[{"src": prep, "dest": "../escape.py"}])


def test_check_key_map_skip_header_and_recode(tmp_path):
    (tmp_path / "d.jsonl").write_text(
        json.dumps({"_header": True, "coding_rule": "r"}) + "\n"
        + json.dumps({"cohort": 2, "uid": "7", "opposed": 0}) + "\n"
        + json.dumps({"cohort": 1, "uid": "8", "opposed": 1}) + "\n")
    (tmp_path / "s.csv").write_text("cohort,uid,party,opposed\n2,7,미래한국당,1\n1,8,더불어민주당,1\n")
    km = {"dictionary": "d.jsonl", "sample": "s.csv", "keys": ["cohort", "uid"], "coded_field": "opposed",
          "skip_header": True,
          "sample_recode": [{"when": {"cohort": "2", "party": "미래한국당"}, "set": {"opposed": "0"}}]}
    res = rp.check_key_map(km, base=tmp_path)
    assert res["ok"] and res["header_rows_skipped"] == 1 and res["sample_rows_recoded"] == 1
    res = rp.check_key_map({**km, "sample_recode": None}, base=tmp_path)
    assert not res["ok"] and res["mismatches"] == 1


ARC4 = ROOT / "replication" / "arc_4" / "MANIFEST.json"


@pytest.mark.skipif(not ARC4.exists(), reason="replication/arc_4 not built")
def test_published_arc4_package_is_verified_and_clean():
    """Read-only check of the published Arc 4 package (Paper D Version 2)."""
    m = json.loads(ARC4.read_text(encoding="utf-8"))
    assert m["build"]["ok"] and m["verify"]["passed"] is True
    cmds = [c["cmd"] for c in m["commands"]]
    assert cmds[0] == "python3 v2/prep_dyads21_meta.py"
    assert cmds.index("python3 r25/build.py") < cmds.index("python3 r25/analyze.py")
    assert cmds.index("python3 r25/recode.py") < cmds.index("python3 v2/rerun.py")
    paths = {o["path"] for o in m["outputs"]}
    assert {"r25/analysis_sample_corrected.csv", "r26/cohort3_panel.csv", "v2/key_values.json"} <= paths
    assert all(c["returncode"] == 0 for c in m["verify"]["commands"])
    assert m["dictionary_key_map"]["dictionary"].endswith("round_25.v2.jsonl")
    for f in ARC4.parent.rglob("*"):
        if f.is_file():
            text = f.read_text(encoding="utf-8")
            assert "/Users/" not in text and "/var/folders" not in text, f


ARC5 = ROOT / "replication" / "arc_5" / "MANIFEST.json"


@pytest.mark.skipif(not ARC5.exists(), reason="replication/arc_5 not built")
def test_published_arc5_package_is_verified_tool_built_and_clean():
    """Read-only check of the published Arc 5 package (Paper E Version 2). It
    must come from replicate.build alone (no hand-edited command list) and
    say that versions.kna is the software version while data_inputs pins the
    data."""
    m = json.loads(ARC5.read_text(encoding="utf-8"))
    assert m["build"]["ok"] and m["verify"]["passed"] is True
    assert "post_build" not in m and m["order"]["cycle_broken"] == []
    cmds = [c["cmd"].split()[-1] for c in m["commands"]]
    assert cmds[0] == "r28/build.py"
    assert cmds.index("v2/seniority_check.py") < cmds.index("v2/recode_tables_v2.py") < cmds.index("v2/key_values.py")
    assert cmds.index("v2/tables_v2.py") < cmds.index("v2/key_values.py")
    assert all(c["returncode"] == 0 for c in m["verify"]["commands"])
    assert {o["path"] for o in m["outputs"]} == {"r28/bills_panel.csv", "v2/key_values.json"}
    assert all(o["ok"] for o in m["verify"]["outputs"])
    kna = [r for r in m["data_inputs"] if r["source"].startswith("KNA")]
    assert kna and all(f.get("sha256") for r in kna for f in r["files"])
    assert "not of the data" in m["versions_note"]
    readme = (ARC5.parent / "README.md").read_text(encoding="utf-8")
    assert "kna software package, not of the data" in readme and "3d8d55d" in readme
    for f in ARC5.parent.rglob("*"):
        if f.is_file():
            text = f.read_text(encoding="utf-8")
            assert "/Users/" not in text and "/var/folders" not in text, f

"""Rerun of Paper D (articles/2026-08-24_r27.tex) under the corrected cohort-2 coding.

Read-only on workspace/r25 and workspace/r26. The workspace is gitignored, so
the tests that need it skip on a fresh clone. The estimator lives in
workspace/redesign_2026-09/v2_work/paper_d/rerun.py and is the one in
workspace/r25/analyze.py (committee FE, SE clustered by legislator).

Test A pins the Version 1 estimates under the original coding. Test B pins the
Version 2 values (the recode of the six cohort-2 미래한국당 pairs) that Paper D
Version 2 reports. Test C reports the kna_blocs estimate without a hard-coded
value and checks that it agrees with the Version 2 coding pair by pair. Test D
joins knowledge/hand_coding/round_25.v2.jsonl to the Version 2 sample. Test E
checks that round_25.jsonl itself was not edited (append-only rule). Test F
checks the v2 dictionary's header and rows. Test G checks the repository layout
and the flat key values that replication/arc_4 compares, and Test H checks that
the package declares the values the repository run produced, including the
Version 1 standard errors that the Paper D notice quotes.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "workspace" / "r25" / "analysis_sample_corrected.csv"
RERUN_DIR = ROOT / "workspace" / "redesign_2026-09" / "v2_work" / "paper_d"
DICT_V1 = ROOT / "knowledge" / "hand_coding" / "round_25.jsonl"
DICT_V2 = ROOT / "knowledge" / "hand_coding" / "round_25.v2.jsonl"

needs_workspace = pytest.mark.skipif(
    not (SAMPLE.exists() and (RERUN_DIR / "rerun.py").exists()),
    reason="R25 workspace artifacts are not present (workspace/ is gitignored)")

INVESTIGATE = ("Mismatch with the value Paper D Version 2 reports. Do not edit this test. Investigate the "
               "sample file, the coding function and the estimator, and report the difference.")


@pytest.fixture(scope="module")
def rerun_mod():
    pytest.importorskip("statsmodels")
    sys.path.insert(0, str(RERUN_DIR))
    try:
        import rerun
    finally:
        sys.path.remove(str(RERUN_DIR))
    return rerun


@pytest.fixture(scope="module")
def results(rerun_mod):
    before = SAMPLE.stat().st_mtime_ns
    B = rerun_mod.load_sample()
    out = rerun_mod.run_all(B)
    assert SAMPLE.stat().st_mtime_ns == before, "the rerun must not write to the R25 sample"
    return rerun_mod, B, out


@needs_workspace
def test_a_original_coding_reproduces_published_estimate(results):
    _, _, R = results
    e = R["original"]["pooled"]
    assert round(e["b"], 2) == -0.86
    assert round(e["se"], 2) == 1.10
    assert e["n"] == 278 and e["clusters"] == 191
    assert round(R["original"]["placebo"]["b"], 2) == -0.85


@needs_workspace
def test_b_version2_values(results):
    rerun, B, R = results
    e, pl = R["miraehanguk"]["pooled"], R["miraehanguk"]["placebo"]
    assert round(e["b"], 2) == -0.72, INVESTIGATE
    assert round(e["lo95"], 2) == -2.96, INVESTIGATE
    assert round(e["hi95"], 2) == 1.51, INVESTIGATE
    assert round(pl["b"], 2) == -1.09, INVESTIGATE
    assert round(pl["lo90"], 2) == -2.61, INVESTIGATE
    assert round(R["miraehanguk"]["mde"], 2) == 3.20, INVESTIGATE
    assert e["n"] == 278
    S = rerun.with_treat(B, R["miraehanguk"]["treat"])
    sec = rerun.secondary_outcomes(S)
    assert round(sec["log_count"]["b"], 3) == 0.095, INVESTIGATE
    assert round(sec["named_share"]["b"], 2) == 3.03, INVESTIGATE
    dose = rerun.dose_block(rerun.dose_frame(B), R["miraehanguk"]["treat"])
    assert dose["n_opposition"] == 132, INVESTIGATE
    assert round(dose["pooled_z"]["hi95"], 2) == 2.74, INVESTIGATE


@needs_workspace
def test_c_kna_blocs_estimate_and_pair_diff(results, capsys):
    rerun, B, R = results
    e = R["kna_blocs"]["pooled"]
    diff = rerun.pair_diff(B, R["original"]["treat"], R["kna_blocs"]["treat"])
    with capsys.disabled():
        print(f"\nkna_blocs pooled {e['b']:+.2f} (SE {e['se']:.2f}), placebo "
              f"{R['kna_blocs']['placebo']['b']:+.2f}, {len(diff)} pairs recoded vs original")
    # Cohort 1 (Moon) coding is unchanged, so every recoded pair is in cohort 2.
    assert set(diff.cohort) <= {2}
    assert e["n"] == 278
    assert len(rerun.pair_diff(B, R["miraehanguk"]["treat"], R["kna_blocs"]["treat"])) == 0


@needs_workspace
def test_d_v2_dictionary_joins_v2_sample(results):
    sys.path.insert(0, str(ROOT))
    try:
        import replicate
    finally:
        sys.path.remove(str(ROOT))
    rerun, B, R = results
    lines = [json.loads(l) for l in DICT_V2.read_text(encoding="utf-8").splitlines() if l.strip()]
    header, rows = lines[0], lines[1:]
    assert header.get("_header") is True and "미래한국당" in header["coding_rule"]
    S = B.copy()
    S["opposed"] = R["miraehanguk"]["treat"].values
    key_map = {"keys": ["cohort", "nominee", "leg_member_uid"], "coded_field": "opposed"}
    res = replicate.validate_dictionary_join(key_map, rows, S.astype(str).to_dict("records"))
    assert res["ok"], res["problems"]
    assert res["unmatched"] == 0 and res["mismatches"] == 0


def test_e_v1_dictionary_unchanged():
    git = shutil.which("git")
    if not git or not DICT_V1.exists():
        pytest.skip("git or round_25.jsonl not available")
    r = subprocess.run([git, "-C", str(ROOT), "show", "HEAD:knowledge/hand_coding/round_25.jsonl"],
                       capture_output=True)
    if r.returncode != 0:
        pytest.skip("round_25.jsonl is not in HEAD")
    assert DICT_V1.read_bytes() == r.stdout, "round_25.jsonl is append-only and must not be edited"


def test_f_v2_dictionary_header_and_rows():
    if not DICT_V2.exists():
        pytest.skip("round_25.v2.jsonl not present")
    lines = [json.loads(l) for l in DICT_V2.read_text(encoding="utf-8").splitlines() if l.strip()]
    header, rows = lines[0], lines[1:]
    assert header["rows"] == len(rows) == 400
    changed = [r for r in rows if r["opposed"] != r["opposed_r25"]]
    assert all(r["party_label_in_dyads"] == "미래한국당" for r in changed)
    assert sum(r["cohort"] == 2 for r in changed) == 6


def test_g_flat_values_and_repository_layout(rerun_mod):
    """rerun.py runs in the repository layout here, and key_values.json flattens
    numeric leaves (booleans as 0/1, NaN dropped, inputs and kna_blocs skipped)."""
    assert rerun_mod.PACKAGE is False
    assert rerun_mod.SAMPLE == SAMPLE
    flat = rerun_mod.flat_values({
        "inputs": {"a.csv": "workspace/r25/a.csv"},
        "pair_diff_v2_vs_kna_blocs": 0, "kna_blocs": {"pooled": {"b": 1.0}},
        "miraehanguk": {"pooled": {"b": -0.72, "n": 278}, "tost": {"pooled_5.0": True},
                        "rows": [{"cohort": 2, "uid": "7"}], "gap": float("nan")},
    })
    assert flat == {"miraehanguk/pooled/b": -0.72, "miraehanguk/pooled/n": 278,
                    "miraehanguk/tost/pooled_5.0": 1, "miraehanguk/rows/0/cohort": 2}


ARC4_MANIFEST = ROOT / "replication" / "arc_4" / "MANIFEST.json"


@pytest.mark.skipif(not (ARC4_MANIFEST.exists() and (RERUN_DIR / "key_values.json").exists()),
                    reason="replication/arc_4 or the repository key_values.json not present")
def test_h_arc4_declared_values_match_repository_run():
    """The values replication/arc_4 declares are the ones rerun.py computed on
    the stored samples, and they carry the Version 2 headline numbers."""
    declared = next(o["values"] for o in json.loads(ARC4_MANIFEST.read_text(encoding="utf-8"))["outputs"]
                    if o["path"] == "v2/key_values.json")
    local = json.loads((RERUN_DIR / "key_values.json").read_text(encoding="utf-8"))
    assert declared == local
    assert round(declared["miraehanguk/pooled/b"], 2) == -0.72
    assert round(declared["miraehanguk/pooled/se"], 2) == 1.14
    assert round(declared["original/pooled/se"], 2) == 1.10
    assert round(declared["original/cohort2/se"], 2) == 2.43
    assert round(declared["original/cohort2/b"], 2) == 1.27

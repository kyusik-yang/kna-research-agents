"""kna_seniority (term number per member per Assembly) and the machine-readable
pitfall registry in knowledge/data_pitfalls.md that run_forum scans Analyst
code with. Member files are small synthetic parquet tables in tmp_path, and
the real KNA data is read only when KBL_DATA is set (the test is skipped
otherwise)."""

import os
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import kna_seniority as ks  # noqa: E402
import prechecks  # noqa: E402

# Lifetime counts as the member files carry them (the same in every Assembly).
MEMBERS = {
    # mona_cd: (reelection, assemblies sat in)
    "A4": ("4선", (17, 18, 19, 20)),       # four terms in a row: 1, 2, 3, 4
    "B3": ("3선", (20, 22)),               # one earlier term before the files: 2, 3
    "C1": ("초선", (21,)),                 # first term: 1
    "D2": ("재선", (21, 22)),              # 1, 2, although reelection reads 재선 in the 21st too
    "E5": ("5선", (22,)),                  # four terms before the 17th: 5
}
EXPECTED = {("A4", 17): 1, ("A4", 18): 2, ("A4", 19): 3, ("A4", 20): 4, ("B3", 20): 2, ("B3", 22): 3,
            ("C1", 21): 1, ("D2", 21): 1, ("D2", 22): 2, ("E5", 22): 5}


def write_members(d: Path, with_kna: bool = False, override: dict | None = None) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    for a in ks.ASSEMBLIES:
        rows = []
        for cd, (label, seats) in MEMBERS.items():
            if a in seats:
                row = {"mona_cd": cd, "member_name": f"name_{cd}", "reelection": label}
                if with_kna:
                    row["term_number"] = (override or {}).get((cd, a), EXPECTED[(cd, a)])
                rows.append(row)
        assert rows, a                        # every Assembly in the fixture has members
        pd.DataFrame(rows).to_parquet(d / f"members_{a}.parquet", index=False)
    return d


def test_lifetime_count_labels():
    assert [ks.lifetime_count(x) for x in ("초선", "재선", "3선", "10선", "", None, "무소속")] == \
        [1, 2, 3, 10, None, None, None]


def test_derived_term_numbers_without_kna_field(tmp_path):
    d = write_members(tmp_path / "data")
    t = ks.term_numbers(d)
    got = {(r.mona_cd, r.assembly): r.term_number for r in t.itertuples()}
    assert got == EXPECTED
    assert set(t["source"]) == {"derived"} and t["problem"].isna().all()
    # The lifetime field alone would call D2 a second-termer in the 21st.
    assert ks.term_number("D2", 21, d) == 1 and ks.first_term("D2", 21, d) is True
    assert ks.term_number("A4", 22, d) is None          # did not sit in the 22nd


def test_kna_field_is_used_and_disagreement_is_reported(tmp_path):
    d = write_members(tmp_path / "ok", with_kna=True)
    r = ks.check_against_kna(ks.term_numbers(d))
    assert r["compared"] == len(EXPECTED) == r["equal"] and r["disagree"] == 0
    bad = write_members(tmp_path / "bad", with_kna=True, override={("B3", 20): 1})
    t = ks.term_numbers(bad)
    r = ks.check_against_kna(t)
    assert r["disagree"] == 1 and r["disagreeing_rows"][0]["mona_cd"] == "B3"
    # kna's field wins in the table, and the derivation stays next to it.
    row = t[(t.mona_cd == "B3") & (t.assembly == 20)].iloc[0]
    assert row.term_number == 1 and row.term_number_derived == 2 and row.source == "kna"


def test_impossible_rows_are_flagged_not_trusted(tmp_path):
    members = pd.DataFrame([
        {"mona_cd": "X", "assembly": 20, "reelection": "초선"},
        {"mona_cd": "X", "assembly": 22, "reelection": "초선"},     # lifetime 1, two terms in the files
        {"mona_cd": "Y", "assembly": 21, "reelection": "재선"},
        {"mona_cd": "Y", "assembly": 22, "reelection": "3선"},      # lifetime count changes
        {"mona_cd": "W", "assembly": 22, "reelection": "?"},
    ])
    t = ks.term_numbers(members=members)
    probs = dict(zip(zip(t.mona_cd, t.assembly), t.problem))
    assert probs[("X", 20)] == "derived term number below 1"
    assert probs[("Y", 21)] == "lifetime count differs across Assemblies"
    assert probs[("W", 22)] == "reelection label not parsed"


def test_kbl_data_is_required(monkeypatch):
    monkeypatch.delenv("KBL_DATA", raising=False)
    with pytest.raises(RuntimeError):
        ks.data_dir()


@pytest.mark.skipif(not os.environ.get("KBL_DATA"), reason="KBL_DATA not set")
def test_real_member_files_match_kna_term_number():
    t = ks.term_numbers()
    r = ks.check_against_kna(t)
    assert r["problems"] == 0
    if r["compared"]:
        assert r["disagree"] == 0, r["disagreeing_rows"][:3]


# ---------------------------------------------------------------------------
# The machine-readable registry in knowledge/data_pitfalls.md
# ---------------------------------------------------------------------------

POSITIVE = {
    "reelection_lifetime_count": ['m["first_term"] = (m["reelection"] == "초선")',
                                  'filter(reelection == "초선")'],
    "term_snapshot_party": ['d["side"] = d["leg_ruling_status"]',
                            'RULING = {"국민의힘", "미래통합당"}',
                            'x = df[df.party == "더불어민주당"]'],
    "name_keyed_merge": ['panel.merge(dose, on="leg_name")',
                         'left_join(bills, members, by = "member_name")',
                         'df.groupby(["member_name", "age"]).size()'],
    "passed_column_definition": ['rate = bills["passed"].mean()', 'mean(bills$passed)'],
    "deprecated_ideal_points": ['pd.read_csv("dw_ideal_points_20_22.csv")["coord1D"]'],
}
NEGATIVE = [
    'm = kna_seniority.term_numbers()',
    'panel.merge(dose, on="leg_member_uid")',
    'side = kna_blocs.bloc(label, date)',
    'ideal = pd.read_csv(f"{D}/ideal_points_bridged.csv")["bridged_1d"]',
    'strict = bills["proc_rslt"].isin(["원안가결", "수정가결"])',
]


def test_shipped_registry_parses_and_every_regex_compiles():
    reg = prechecks.load_pitfall_registry(ROOT / "knowledge" / "data_pitfalls.md")
    ids = [e["id"] for e in reg]
    assert set(POSITIVE) <= set(ids) and len(ids) == len(set(ids))
    for e in reg:
        for k in prechecks.PITFALL_FIELDS:
            assert str(e[k]).strip(), (e["id"], k)
        assert ";" not in e["description"] and "—" not in e["description"] + e["alternative"]


@pytest.mark.parametrize("pid", sorted(POSITIVE))
def test_registry_flags_each_known_misuse(pid):
    reg = prechecks.load_pitfall_registry(ROOT / "knowledge" / "data_pitfalls.md")
    for line in POSITIVE[pid]:
        hits = prechecks.pitfall_hits(f"Text.\n\n```python\n{line}\n```\n", reg)
        assert pid in {h["id"] for h in hits}, line


def test_registry_is_quiet_on_the_correct_alternatives():
    reg = prechecks.load_pitfall_registry(ROOT / "knowledge" / "data_pitfalls.md")
    post = "```python\n" + "\n".join(NEGATIVE) + "\n```\n"
    assert prechecks.pitfall_hits(post, reg) == []


def test_only_code_blocks_are_scanned_and_lines_are_post_lines():
    reg = prechecks.load_pitfall_registry(ROOT / "knowledge" / "data_pitfalls.md")
    post = ("---\nround: 31\n---\n\n# Report\n\nThe reelection field is a lifetime count.\n\n"
            "```python\nimport pandas as pd\nm = m[m.reelection == '초선']\n```\n")
    hits = prechecks.pitfall_hits(post, reg)
    assert [(h["id"], h["line"]) for h in hits] == [("reelection_lifetime_count", 11)]
    block = prechecks.pitfall_flags_block(hits, "092_data_analyst.md")
    assert block.startswith("\n## Data pitfall flags") and "line 11 of 092_data_analyst.md" in block
    assert "kna_seniority.term_number" in block
    assert prechecks.pitfall_flags_block([], "x.md") == ""



def test_flags_are_grouped_per_pitfall_and_capped():
    """A field used on many lines gives one item with its description and
    alternative once, and at most PITFALL_LINES_SHOWN listed lines."""
    reg = prechecks.load_pitfall_registry(ROOT / "knowledge" / "data_pitfalls.md")
    code = "\n".join(f"x{i} = m[m.reelection == '{i}선']" for i in range(1, 10))
    post = "```python\n" + code + "\npanel.merge(dose, on=\"leg_name\")\n```\n"
    hits = prechecks.pitfall_hits(post, reg)
    block = prechecks.pitfall_flags_block(hits, "092_data_analyst.md")
    assert block.count("Correct alternative:") == 2
    assert "`reelection_lifetime_count` (9 matched lines)" in block
    assert "`name_keyed_merge` (1 matched line)" in block
    assert block.count("  - line ") == prechecks.PITFALL_LINES_SHOWN + 1
    assert "and 3 more line(s)" in block


def test_broken_registry_gives_no_flags_and_never_raises(tmp_path):
    f = tmp_path / "pitfalls.md"
    f.write_text('```json\n{"registry": "kna_data_pitfalls", "pitfalls": [{"id": "x", "description": "d", '
                 '"regex": "(", "alternative": "a"}, {"id": "y"}]}\n```\n', encoding="utf-8")
    assert prechecks.load_pitfall_registry(f) == []
    assert prechecks.load_pitfall_registry(tmp_path / "missing.md") == []

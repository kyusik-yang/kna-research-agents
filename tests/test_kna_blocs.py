"""kna_blocs: date-indexed party-bloc coding and the three data-pitfall checks."""

import datetime as dt
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import kna_blocs as kb  # noqa: E402

HEADER = ",".join(kb.COLUMNS)

# Party labels found in the KNA dyads for the 20th to 22nd Assemblies (leg_party).
# 열린우리당 also appears once in the 20th term (a 2003-2007 label on one
# 더불어민주당 member) and is deliberately absent, so it raises.
KNA_LABELS_20_22 = [
    "국민의당", "더불어민주당", "무소속", "바른미래당", "새누리당", "자유한국당", "정의당",
    "국민의힘", "기본소득당", "더불어시민당", "미래통합당", "미래한국당", "시대전환", "열린민주당", "진보당",
    "개혁신당", "국민의미래", "더불어민주연합", "새로운미래", "조국혁신당",
]


def _write_table(tmp_path, lines):
    p = tmp_path / "blocs.csv"
    p.write_text(HEADER + "\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return p


def _presidents():
    return sorted((r for r in kb.load_table() if r.kind == "presidency"), key=lambda r: r.valid_from)


# ---------------------------------------------------------------------------
# The table
# ---------------------------------------------------------------------------

def test_table_is_consistent():
    assert kb.validate_table() == []


def test_every_row_has_source_status_and_check_date():
    for r in kb.load_table():
        assert r.source, r
        assert r.status in kb.STATUSES, r
        dt.date.fromisoformat(r.checked)


def test_rows_await_researcher_confirmation():
    # D-05 is open: nothing is confirmed until the researcher says so.
    assert all(r.status == "needs_confirmation" for r in kb.load_table())


def test_every_kna_label_of_the_20th_to_22nd_assemblies_is_covered():
    labels = {r.label for r in kb.load_table()}
    assert [lab for lab in KNA_LABELS_20_22 if lab not in labels] == []


def test_required_satellite_and_predecessor_labels_present():
    rows = {(r.label, r.relation) for r in kb.load_table()}
    for label in ("미래한국당", "국민의미래", "더불어시민당", "더불어민주연합"):
        assert (label, "satellite") in rows
    for label in ("새누리당", "자유한국당", "미래통합당", "새정치민주연합"):
        assert (label, "predecessor") in rows


def test_presidency_rows_cover_moon_yoon_and_the_2025_transition():
    pres = [(r.label, r.lineage_id, r.valid_from.isoformat(), r.valid_to.isoformat() if r.valid_to else "")
            for r in _presidents()]
    assert ("문재인", "democratic", "2017-05-10", "2022-05-10") in pres
    assert ("윤석열", "conservative", "2022-05-10", "2025-04-04") in pres
    assert any(lin == "" and a == "2025-04-04" and b == "2025-06-04" for _, lin, a, b in pres)
    assert ("이재명", "democratic", "2025-06-04", "") in pres


# ---------------------------------------------------------------------------
# bloc()
# ---------------------------------------------------------------------------

MAIN_LABEL = {"conservative": "국민의힘", "democratic": "더불어민주당"}


def _main_label(lineage, d):
    # The main-party label valid on d (새누리당 and 자유한국당 before 국민의힘).
    for r in kb.load_table():
        if r.kind == "party" and r.lineage_id == lineage and r.relation in ("main", "predecessor") and r.contains(d):
            return r.label
    raise AssertionError(f"no main label for {lineage} on {d}")


def test_bloc_flips_at_every_change_of_government():
    """Boundary dates are read from the table rows, not typed in the test.

    A change of government is the start of every presidency row after the
    first (the first row's start is where the table's coverage begins, before
    the 새정치민주연합 row, so it is not a change inside the table).
    """
    changes = _presidents()[1:]
    assert len(changes) >= 4
    for r in changes:
        for d in (r.valid_from, r.valid_from - dt.timedelta(days=1)):
            pres = kb.presidency_row(d)
            for lineage in ("conservative", "democratic"):
                label = _main_label(lineage, d)
                got = kb.bloc(label, d.isoformat())
                if not pres.lineage_id:
                    assert got is None, (label, d)
                else:
                    assert got == ("ruling" if lineage == pres.lineage_id else "opposition"), (label, d)


@pytest.mark.parametrize("label,date,expected", [
    ("더불어민주당", "2022-05-09", "ruling"),
    ("더불어민주당", "2022-05-10", "opposition"),
    ("국민의힘", "2022-05-10", "ruling"),
    ("국민의힘", "2025-04-03", "ruling"),
    ("국민의힘", "2025-04-04", None),
    ("더불어민주당", "2025-06-03", None),
    ("더불어민주당", "2025-06-04", "ruling"),
    ("국민의힘", "2025-06-04", "opposition"),
    ("새누리당", "2016-06-01", "ruling"),
    ("더불어민주당", "2017-05-10", "ruling"),
])
def test_bloc_at_known_dates(label, date, expected):
    assert kb.bloc(label, date) == expected


def test_miraehanguk_2023_is_ruling():
    assert kb.bloc("미래한국당", "2023-03-01") == "ruling"
    assert [r.label for r in kb.resolve("미래한국당", "2023-03-01")] == ["미래한국당", "미래통합당", "국민의힘"]


@pytest.mark.parametrize("label,date,expected", [
    ("더불어시민당", "2021-01-20", "ruling"),       # satellite of the president's party under Moon
    ("더불어시민당", "2023-05-22", "opposition"),
    ("미래한국당", "2021-01-20", "opposition"),
    ("미래통합당", "2023-05-22", "ruling"),          # term-snapshot label, renamed 국민의힘
    ("국민의미래", "2024-06-25", "ruling"),
    ("더불어민주연합", "2024-06-25", "opposition"),
    ("더불어민주연합", "2025-07-01", "ruling"),
    ("국민의당", "2021-01-20", "opposition"),       # the 2020 party under Moon
    ("국민의당", "2023-05-22", "ruling"),           # merged into 국민의힘 in 2022
    ("국민의당", "2019-01-01", "opposition"),       # the 2016 party, via 바른미래당
    ("새누리당", "2018-01-01", "opposition"),
    ("시대전환", "2021-01-20", "opposition"),
    ("시대전환", "2024-01-10", "ruling"),           # merged into 국민의힘 on 2023-12-27
    ("정의당", "2024-03-01", "opposition"),          # via 녹색정의당
    ("조국혁신당", "2025-07-01", "opposition"),
    ("무소속", "2023-05-22", None),
])
def test_bloc_satellites_predecessors_and_minor_parties(label, date, expected):
    assert kb.bloc(label, date) == expected


def test_unknown_label_raises():
    with pytest.raises(kb.UnknownLabelError):
        kb.bloc("열린우리당", "2018-01-01")
    with pytest.raises(kb.UnknownLabelError):
        kb.bloc("없는정당", "2023-01-01")


def test_dates_outside_coverage_raise():
    with pytest.raises(kb.CoverageError):
        kb.bloc("조국혁신당", "2023-01-01")      # before the party existed
    with pytest.raises(kb.CoverageError):
        kb.bloc("새누리당", "2012-06-01")        # before the first presidency row
    with pytest.raises(ValueError):
        kb.bloc("국민의힘", "not a date")


def test_bloc_accepts_date_objects():
    assert kb.bloc("국민의힘", dt.date(2023, 5, 22)) == "ruling"
    assert kb.bloc("국민의힘", dt.datetime(2023, 5, 22, 10, 0)) == "ruling"


def test_stale_label():
    assert kb.stale_label("미래통합당", "2023-05-22") is True
    assert kb.stale_label("국민의힘", "2023-05-22") is False


def test_unconfirmed_rows_refused_outside_tests(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    with pytest.raises(kb.UnconfirmedRowError):
        kb.bloc("국민의힘", "2023-05-22")
    assert kb.bloc("국민의힘", "2023-05-22", allow_unconfirmed=True) == "ruling"


def test_confirmed_fixture_table_needs_no_override(tmp_path, monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    p = _write_table(tmp_path, [
        "presidency,A,red,president,2020-01-01,,,confirmed,fixture,2026-09-25,",
        "party,Red,red,main,2019-01-01,,,confirmed,fixture,2026-09-25,",
        "party,Blue,blue,minor,2019-01-01,,,needs_confirmation,fixture,2026-09-25,",
    ])
    assert kb.bloc("Red", "2021-01-01", path=p) == "ruling"
    with pytest.raises(kb.UnconfirmedRowError):
        kb.bloc("Blue", "2021-01-01", path=p)


def test_validate_table_reports_broken_rows(tmp_path):
    p = _write_table(tmp_path, [
        "presidency,A,red,president,2020-01-01,2021-01-01,,needs_confirmation,fixture,2026-09-25,",
        "presidency,B,blue,president,2021-02-01,,,needs_confirmation,fixture,2026-09-25,",
        "party,Red,red,main,2019-01-01,2020-06-01,Gone,needs_confirmation,fixture,2026-09-25,",
        "party,Red,red,main,2020-05-01,,,needs_confirmation,fixture,2026-09-25,",
        "party,Blue,blue,sidekick,2019-01-01,,,needs_confirmation,,2026-09-25,",
    ])
    problems = "\n".join(kb.validate_table(p))
    assert "successor 'Gone'" in problems
    assert "overlap" in problems
    assert "gap or overlap" in problems
    assert "relation 'sidekick'" in problems
    assert "no source" in problems


# ---------------------------------------------------------------------------
# Pitfall checks (knowledge/data_pitfalls.md)
# ---------------------------------------------------------------------------

def test_pitfall_snapshot_flags_2023_ruling_label_for_democratic_party():
    rows = [
        {"leg_party": "더불어민주당", "date": "2023-05-22", "leg_ruling_status": "ruling"},     # wrong
        {"leg_party": "국민의힘", "date": "2023-05-22", "leg_ruling_status": "ruling"},        # right
        {"leg_party": "미래통합당", "date": "2023-05-22", "leg_ruling_status": "ruling"},      # right side, stale label
        {"leg_party": "무소속", "date": "2023-05-22", "leg_ruling_status": "independent"},    # right
        {"leg_party": "열린우리당", "date": "2018-01-01", "leg_ruling_status": "ruling"},      # unknown label
    ]
    flags = kb.check_snapshot_labels(rows)
    by_row = {f["row"]: f for f in flags}
    assert by_row[0]["reason"] == "status_mismatch"
    assert by_row[0]["expected"] == "opposition"
    assert 1 not in by_row and 3 not in by_row
    assert by_row[2]["reason"] == "stale_label"
    assert by_row[4]["reason"] == "unknown_label"


def test_pitfall_snapshot_accepts_a_dataframe():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"leg_party": ["더불어민주당", "국민의힘"], "date": ["2023-05-22", "2023-05-22"],
                       "leg_ruling_status": ["ruling", "opposition"]}, index=[10, 11])
    flags = kb.check_snapshot_labels(df)
    assert [f["row"] for f in flags] == [10, 11]


def test_pitfall_name_identity_flags_shared_names():
    rows = [
        {"term": 21, "leg_name": "이수진", "leg_member_uid": "7553"},
        {"term": 21, "leg_name": "이수진", "leg_member_uid": "7554"},
        {"term": 21, "leg_name": "강기윤", "leg_member_uid": "16"},
        {"term": 20, "leg_name": "강기윤", "leg_member_uid": "99"},   # different term, different scope
    ]
    flags = kb.check_name_identity(rows)
    assert len(flags) == 1
    assert flags[0]["name"] == "이수진" and flags[0]["uids"] == ["7553", "7554"]
    assert kb.check_name_identity(rows, within=()) and len(kb.check_name_identity(rows, within=())) == 2


def test_pitfall_passage_definitions():
    statuses = ["원안가결", "수정가결", "대안반영폐기", "대안반영폐기", "수정안반영폐기",
                "임기만료폐기", "임기만료폐기", "철회", "부결", "임기만료폐기"]
    rates = kb.passage_rates(statuses)
    assert rates["n"] == 10
    assert rates["strict"] == pytest.approx(0.2)
    assert rates["alternative_inclusive"] == pytest.approx(0.4)
    assert rates["absorption_inclusive"] == pytest.approx(0.5)
    assert rates["ratio_absorption_to_strict"] == pytest.approx(2.5)
    kna_passed = [int(s in ("원안가결", "수정가결", "대안반영폐기")) for s in statuses]
    enacted = [int(s in ("원안가결", "수정가결")) for s in statuses]
    rows = [{"status": s, "passed": p, "enacted": e} for s, p, e in zip(statuses, kna_passed, enacted)]
    assert kb.check_passage_definition(rows)["matches"] == "alternative_inclusive"
    assert kb.check_passage_definition(rows, flag="enacted")["matches"] == "strict"
    rows[0]["passed"] = 0
    assert kb.check_passage_definition(rows)["matches"] == "neither"

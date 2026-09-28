# KNA data pitfalls

Known traps in the Korean National Assembly data that have already produced wrong numbers in this forum. Each pitfall has a check function in `kna_blocs.py` or `kna_seniority.py` with a unit test, and an entry in the machine-readable registry at the end of this file, which run_forum uses to flag the pattern in every Analyst post. Run the check before any estimate that depends on the field in question, and report its output in the post.

Any ruling or opposition coding must come from `kna_blocs.bloc(party_label, date)`, which reads the date-indexed table `knowledge/party_blocs.csv`. Do not write a party set by hand in an analysis script. The table rows stay `needs_confirmation` until the researcher confirms them, and until then a caller must pass `allow_unconfirmed=True` and label the coding as provisional.

## 1. Term-snapshot party fields

**What goes wrong.** The party fields in the dyads (`leg_party`, `leg_ruling_status`) record the label a member held when the term began. They do not follow renames, mergers or changes of government during the term. In the 2023 confirmation hearings of the 21st Assembly, 더불어민주당 members are still labeled `ruling` and many 국민의힘 members still carry the 2020 labels 미래통합당 or 미래한국당. Coding governing status from the raw field inverted 88 of 97 cohort-2 rows in Round 25 (forum post 074). A hand-written party set then missed the satellite label 미래한국당, which coded six cohort-2 pairs of the ruling bloc as opposed in Paper D (the rerun is in the redesign reports).

**Rule.** Code sides with `kna_blocs.bloc(label, date)` at the date of the event (hearing, speech, vote). It follows the successor chain from the label's own row, so `bloc("미래한국당", "2023-03-01")` is `ruling` (미래한국당, then 미래통합당, then 국민의힘, under the Yoon presidency). It returns None for independents and for the two interregna after a presidential removal. Unknown labels raise, so a new label needs a sourced row in the table before use.

**Check.** `kna_blocs.check_snapshot_labels(records, party="leg_party", date="date", status="leg_ruling_status")` flags rows whose recorded status disagrees with `bloc()` (`status_mismatch`), rows whose label had ceased to exist on the date (`stale_label`), and labels the table does not know (`unknown_label`).

**Limit.** The coding is by label lineage, not by the individual. Members elected on a satellite list who returned to a partner party (the four 더불어민주연합 members of 2024) are coded by the label in the data. A coding by individual affiliation needs a member-level source.

**A related trap in the KNA roll calls.** From kna 0.7.0, `party` in `roll_calls_all` and in the ideal-point files is the party at election, and `party_api` is the API's current-party label, written onto every past vote. Up to kna 0.6.0 `party` held that current label. Never use `party_api` as the party at the time of a vote. Code sides with `kna_blocs.bloc(party, date)`.

## 2. Merging members by name

**What goes wrong.** Names are not unique. The 21st Assembly seats two legislators named 이수진 (member uids 7553 and 7554), and both questioned the same nominee at one hearing. A name-keyed merge in Round 26 gave one supportive-side row a contaminated dose value (forum post 080). The same failure happens when one person appears under several ids.

The KNA files have the same problem. Two members share a name in the 20th (김성태, 최경환), the 21st (김병욱, 이수진) and the 22nd (박지원) Assemblies, among others. Up to kna 0.6.0 the roll calls dropped the votes of one member of each 20th and 21st pair. From kna 0.7.0 a legislator lookup by name raises `kna.queries.AmbiguousLegislator` (CLI `--mona`).

**Rule.** Merge, group and cluster on `leg_member_uid` (or the member code of the source table, `mona_cd` or `member_id` in KNA), never on the name. Assert uniqueness of the key after every merge.

**Check.** `kna_blocs.check_name_identity(records, name="leg_name", uid="leg_member_uid", within=("term",))` returns one flag per name that maps to more than one id within a term. Any flag means a name key is unsafe for that data.

## 3. Strict versus absorption-inclusive passage

**What goes wrong.** "Passed" has at least three definitions, and the rates differ by a factor of about five. In the Round 28 bill panel (member-sponsored law bills, 17th to 22nd Assemblies, 93,572 bills on the kna 0.6.0 data) the strict rate (원안가결 or 수정가결) is 6.2 percent and the absorption-inclusive rate (adding 대안반영폐기 and 수정안반영폐기) is 30.9 percent (forum post 083). The same code on the kna 0.7.0 data gives 97,046 bills, 6.2 and 31.1 percent. A premise stated at the wrong rate made the Round 28 baseline wrong by a factor of two. The `passed` column of the KNA bill tables counts 원안가결, 수정가결 and 대안반영폐기 as passed and 수정안반영폐기 as not passed (checked on the 21st Assembly table), so it matches none of the two definitions above.

**Rule.** State which definition an analysis uses, name the status values it counts, and report the other definition alongside it.

**Check.** `kna_blocs.check_passage_definition(records, flag="passed", status="status")` reports which definition a 0/1 column encodes (`strict`, `alternative_inclusive`, `absorption_inclusive` or `neither`) and the rates under all three. `kna_blocs.passage_rates(statuses)` gives the rates and the absorption-to-strict ratio.

## 4. Lifetime term count read as seniority at an Assembly

**What goes wrong.** The `reelection` field of the KNA member files (`members_17.parquet` to `members_22.parquet`, values 초선, 재선, 3선 and so on) is the member's lifetime number of terms when the data were collected. It has the same value in every Assembly the member sat in, for all 1,146 members in the files pinned for Paper E (kna data commit 3d8d55d). It is not the member's seniority in a given Assembly. Paper E Version 1 coded first-term status from it, so its first-term group held only first-term members who were never re-elected, and 18,969 bills of first-term members who were later re-elected sat in the comparison group. The corrected coding moved the headline absorption step from about three and a half points to about one and a half (Paper E Version 2 correction notice).

**Rule.** Take seniority at an Assembly from `kna_seniority.term_number(mona_cd, assembly)` (or the table from `kna_seniority.term_numbers()`), or from the `term_number` and `seniority` fields that kna version 0.7.0 added to the member files. Never compare `reelection` with 초선 to code first-term status.

**Check.** `python3 kna_seniority.py --check` derives the term number of every member-term from the member files and compares it with kna's `term_number` where the field exists. `kna_seniority.check_against_kna(table)` returns the counts and the disagreeing rows. On the kna 0.7.0 member files the derivation agrees with kna's field for all 1,948 member-terms, and on the files pinned for Paper E it gives 205 first-term members in the 17th Assembly where `reelection` reads 초선 for 97 (`python3 kna_seniority.py --check`, run on 2026-09-26).

## 5. Cosponsorship roles

**What goes wrong.** Up to kna 0.6.0 `cosponsorship_edges.role` was empty for co-proposers (공동발의) and supporters (찬성) alike, the file covered only the 20th to 22nd Assemblies, and it kept at most 100 names per bill. Round 30 counted every non-lead edge as a cosponsor. kna 0.7.0 covers the 17th to 22nd, and 107,129 of its 1,379,763 edges are supporters.

**Rule.** Filter on `role` (대표발의, 공동발의 or 찬성) and say whether supporters are included.

**Check.** `kna_blocs.check_edge_roles(records, role="role")` counts the edges per role and the rows whose role is missing or unknown. Any such row means a pre-0.7.0 edge file.

## Machine-readable registry

run_forum scans the code blocks of every Analyst post with the regular expressions below and passes any match to the Critic as a flag (`prechecks.pitfall_hits`). A match is a prompt to check the code, not a finding. The block must stay valid JSON, and `tests/test_kna_seniority.py` checks that every entry parses and compiles.

```json
{
  "registry": "kna_data_pitfalls",
  "version": 1,
  "pitfalls": [
    {
      "id": "reelection_lifetime_count",
      "section": 4,
      "description": "The member-file reelection field (초선, 재선, N선) is the lifetime term count at collection, the same in every Assembly, not seniority at an Assembly.",
      "regex": "\\breelection\\b",
      "alternative": "kna_seniority.term_number(mona_cd, assembly) or kna_seniority.term_numbers(), or the term_number and seniority fields of the kna 0.7.0 member files."
    },
    {
      "id": "term_snapshot_party",
      "section": 1,
      "description": "Party fields such as leg_party and leg_ruling_status record the label at the start of the term, and a hand-written party set misses renames and satellites.",
      "regex": "\\b(?:leg_ruling_status|leg_party)\\b|['\"](?:국민의힘|더불어민주당|미래통합당|미래한국당|자유한국당|새누리당|한나라당|열린우리당|민주통합당|새정치민주연합|더불어시민당|더불어민주연합|국민의미래)['\"]\\s*(?:,|\\))|(?:==|!=)\\s*['\"](?:국민의힘|더불어민주당|미래통합당|미래한국당|자유한국당|새누리당|한나라당|열린우리당|민주통합당|새정치민주연합)['\"]",
      "alternative": "kna_blocs.bloc(party_label, date) at the date of the event, with kna_blocs.check_snapshot_labels on the records."
    },
    {
      "id": "name_keyed_merge",
      "section": 2,
      "description": "Names are not unique (the 21st Assembly seats two members named 이수진), so a merge, group or index on a name mixes members.",
      "regex": "\\b(?:on|left_on|right_on|by|index)\\s*=\\s*(?:c\\(|\\[)?\\s*['\"](?:member_name|leg_name|rst_proposer|hg_nm|member_nm|name)['\"]|\\b(?:groupby|set_index|group_by)\\(\\s*\\[?\\s*['\"]?(?:member_name|leg_name|rst_proposer|hg_nm)\\b",
      "alternative": "merge, group and cluster on the member uid (mona_cd, leg_member_uid or the source table's member code) and assert the key is unique after the merge."
    },
    {
      "id": "passed_column_definition",
      "section": 3,
      "description": "The passed column of the KNA bill tables counts 원안가결, 수정가결 and 대안반영폐기, which matches neither the strict nor the absorption-inclusive passage definition.",
      "regex": "\\[\\s*['\"]passed['\"]\\s*\\]|\\$passed\\b|\\.passed\\b|\\bpassed\\s*[=!]=",
      "alternative": "state the definition, name the status values it counts, report the other definition alongside it, and check the column with kna_blocs.check_passage_definition."
    },
    {
      "id": "deprecated_ideal_points",
      "section": null,
      "description": "dw_ideal_points_20_22.csv is removed in kna 0.7.0. It was deprecated because its coord1D is per-Assembly W-NOMINATE with a sign flip, not DW-NOMINATE (DATA_SOURCES.md).",
      "regex": "dw_ideal_points_20_22|\\bcoord1D\\b",
      "alternative": "ideal_points_bridged.csv (bridged_1d) for cross-Assembly comparison, ideal_points_wnominate.csv (wnom_1d) within one Assembly, ideal_points_dwnominate.csv (dwnom_1d) for one constant per member."
    },
    {
      "id": "edge_roles",
      "section": 5,
      "description": "Up to kna 0.6.0 cosponsorship_edges.role did not separate co-proposers (공동발의) from supporters (찬성), the file covered only the 20th-22nd Assemblies, and it kept at most 100 names per bill.",
      "regex": "\\bcosponsorship_edges\\b",
      "alternative": "the kna >= 0.7.0 edges filtered on role (대표발의, 공동발의, 찬성), saying whether 찬성 rows are included, checked with kna_blocs.check_edge_roles."
    }
  ]
}
```

## Adding a pitfall

Add a section here with what went wrong (with the forum post or paper), the rule, and a check function with a unit test on a small fixture (`kna_blocs.py` for party and passage checks, `kna_seniority.py` for seniority). Then add an entry to the machine-readable registry above with an id, a description, a regular expression that detects the misuse in analysis code, and the correct alternative, so the Critic sees a flag whenever an Analyst post repeats the mistake.

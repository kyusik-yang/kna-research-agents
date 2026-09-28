# Data Sources

The forum agents draw on two primary data systems: the KNA database (empirical backbone) and the OpenAlex API (literature backbone). A third source, the KCI API, is planned but requires an API key.

---

## 1. KNA (Korean National Assembly Database)

**Source:** [kna](https://github.com/kyusik-yang/kna)
**Access:** KNA CLI (`pip install kna`, version 0.7.0 or later), the Python loader `from kna.data import BillDB`, or direct parquet file loading
**Coverage:** 17th-22nd National Assembly (2004-present)
**Last updated:** 2026-09-26 (release 0.7.0, most data collected on 2026-09-25)

Release 0.7.0 corrected ten defects in the files shipped up to 0.6.0. Read the 2026-09-26 entry of kna `CORRECTIONS.md` before reusing a result obtained with earlier files. `KNA_070_PUBLISHED.md` in this repository lists the forum papers that used the corrected fields and explains how to reproduce them on the 0.6.0 data.

### Datasets

#### Bills Master (`master_bills_{17-22}.parquet`)

The core dataset. Each row is one bill with its full lifecycle. All six files share the same 67 columns.

| Column | Type | Description |
|--------|------|-------------|
| `bill_id` | str | Unique ID (PRC_/ARC_ prefix, six digits for most 17th-Assembly bills) |
| `bill_no` | str | Bill number (six digits in the 17th, seven from the 18th) |
| `age` | int | Assembly number (17-22) |
| `bill_nm` | str | Bill name (Korean) |
| `bill_kind` | str | Type (법률안, 결의안, 동의안, etc.) |
| `ppsr_kind` | str | Proposer type (의원, 정부, 위원장) |
| `rst_proposer`, `rst_mona_cd` | str | Lead proposer name and MONA_CD |
| `committee_nm` | str | Referring committee |
| `proc_rslt`, `status` | str | Final result, for a vetoed bill the result of the re-vote. `status` is 계류중 when there is none |
| `passed` | int | 1 if `proc_rslt` is 원안가결, 수정가결 or 대안반영폐기 (so it includes absorption into a committee alternative) |
| `enacted` | int | 1 if `proc_rslt` is 원안가결 or 수정가결 |
| `promulgated`, `law_reflected` | int | Promulgated law bill, and the official 법률반영 result codes less bills absorbed into a vetoed alternative |
| `vetoed`, `veto_dt`, `revote_rslt`, `first_plenary_rslt` | | Presidential veto (재의요구) and re-vote, one row per vetoed bill |
| `alt_bill_id` | str | Committee alternative linked to the bill |
| `ppsl_dt` | date | Proposal date |
| `committee_dt` | date | Committee referral date |
| `cmt_proc_dt` | date | Committee decision date |
| `law_proc_dt` | date | Plenary decision date |
| `prom_dt` | date | Promulgation date |
| `days_to_proc` | int | Days from proposal to final decision (censored for expired bills) |
| `vote_yes/no/abstain` | int | Plenary vote counts (20th-22nd) |

**Total:** 115,149 bills across 6 assemblies, of which 110,245 are law bills. The 22nd includes pending non-member bills.

#### Roll Call Votes (`roll_calls_all.parquet`)

Member-level voting records from plenary sessions, 20th-22nd Assemblies. The key (term, bill_id, member_id) is unique.

| Column | Type | Description |
|--------|------|-------------|
| `term` | int | Assembly number (20-22) |
| `bill_id`, `bill_no` | str | Bill of the vote |
| `member_id` | str | MONA_CD (join on this, never on the name) |
| `member_name` | str | Legislator name |
| `party` | str | Party at election, from `members_{term}` (satellite list parties kept) |
| `party_api` | str | The API's current-party label, written onto every past vote |
| `vote` | str | 찬성, 반대, 기권 or 불참 |

**Total:** 2,557,618 vote records. The 16th-19th rows of earlier releases were meeting-level pseudo events parsed from minutes. They are in `roll_calls_16_19_experimental.parquet` and are not a roll-call matrix.

#### Ideal Points (`ideal_points_bridged.csv`, `ideal_points_wnominate.csv`, `ideal_points_dwnominate.csv`)

First-dimension ideal points estimated from roll call votes (20-22nd Assembly). Negative = liberal, positive = conservative.
Three series are distributed. They answer different questions and are not interchangeable (see kna `CODEBOOK.md` section 10 and `CORRECTIONS.md`).

| File | Column | Method | Use for |
|------|--------|--------|---------|
| `ideal_points_bridged.csv` | `bridged_1d` | chained bridging alignment of per-assembly W-NOMINATE | cross-assembly comparison (default; `db.ideal_points()`) |
| `ideal_points_wnominate.csv` | `wnom_1d` | per-assembly W-NOMINATE, 1-D fit | within-assembly comparison only |
| `ideal_points_dwnominate.csv` | `dwnom_1d` | pooled DW-NOMINATE | cross-assembly; one constant per member, no individual movement |

Common columns: `member_id`, `member_name`, `party`, `party_bloc`, `term`, `vintage`. `party` is the party at election, and the conservative bloc includes 새누리당, 미래한국당 and 국민의미래, the liberal bloc 더불어시민당 and 더불어민주연합.
`dw_ideal_points_20_22.csv` and `ideal_points_{17,20,21,22,all}.csv` were removed in 0.7.0. The 0.6.0 series is kept in `ideal_points_archive/v0.6.0_legacy/` for reproducing earlier results.

**Total:** 940 legislator-term observations per series (vintage v20260917).

#### Committee Meetings (`committee_meetings_{17-22}.parquet`, `judiciary_meetings_{17-22}.parquet`)

Records of committee and 법제사법위원회 sessions per bill, with lowercase columns in every assembly. Up to 0.6.0 the 17th-20th tables stopped at five rows per bill.

**Total:** 818,448 committee meeting rows and 15,858 judiciary rows across 6 assemblies.

#### Committee Process and Assignments

`subcommittee_reviews.parquet` (93,981 bill-stage rows), `alternative_absorption.parquet` (25,439 links from committee alternatives to the bills they absorbed), `committee_assignments.parquet` (13,616 dated assignment spells), `veto_events.parquet` (47 vetoes) and `vote_events.parquet` (8,611 plenary tallies).

#### Members (`members_{17-22}.parquet`)

One row per member-term (1,948). `term_number` (1 = first term) and `seniority` (초선, 재선, N선) give seniority at that assembly. `reelection` is the lifetime count at collection and must not be used as first-term status. `party` is the party at election, `party_current` the current party of serving 22nd members, and `committee` lists the committees served in that assembly. Several assemblies seat two members with the same name, so merge on `mona_cd`.

#### Bill Texts (`bill_texts_linked.parquet`)

Full propose-reason text for bills in the 20th-22nd Assembly. Useful for text analysis, topic modeling, and keyword search.

**Total:** 60,925 texts.

#### Cosponsorship Network (`cosponsorship_edges.parquet`)

Bill-member edges on member law bills, 17th-22nd, with columns `bill_id`, `bill_no`, `age`, `member_id`, `member_name`, `party`, `party_source`, `role` and `source`. `role` is 대표발의 (lead proposer), 공동발의 (co-proposer) or 찬성 (supporter). Filter on `role` and state whether supporters are included.

**Total:** 1,379,763 edges on 97,263 bills.

#### Legislator ID Mapping (`legislator_id_mapping.parquet`)

Crosswalk between different legislator identifiers across datasets, one row per member of the 17th-22nd. Use `in_ideal_points`. `in_dw_nominate` is a deprecated alias.

### KNA CLI Commands

```bash
# Always set this environment variable first
export KBL_DATA=/path/to/kna/data/processed

kna info                                    # Database overview
kna search "인공지능" --assembly 22         # Search by keyword
kna search "부동산" --status enacted         # Filter by status
kna show 2217673                            # Bill lifecycle detail
kna legislator 추미애 --assembly 21         # Legislator profile
kna legislator 김병욱 --assembly 21 --mona GFF1986K  # Same-name members need --mona
kna text "기후변화"                          # Full-text search
kna stats funnel --assembly 22              # Legislative funnel
kna stats passage-rate                      # Cross-assembly trend
kna export output.csv --assembly 22         # Export to CSV
```

---

## 2. OpenAlex API

**Source:** [OpenAlex](https://openalex.org/) (free, open bibliometric database)
**Access:** REST API, no authentication required (polite pool: add `mailto` parameter)
**Coverage:** 250M+ works, all disciplines

### Key Endpoints

```
GET https://api.openalex.org/works          # Search publications
GET https://api.openalex.org/authors        # Search authors
GET https://api.openalex.org/topics         # Browse topics
GET https://api.openalex.org/concepts       # Browse concepts (legacy)
```

### Useful Filters for Political Science

```bash
# Keyword search
/works?search=legislative+productivity+Korea&per_page=25

# Filter by publication year
/works?search=party+discipline&filter=publication_year:2023-2026

# Filter by topic
/works?filter=primary_topic.id:T10108&per_page=10   # Electoral Systems

# Select specific fields (saves bandwidth)
&select=id,title,publication_year,authorships,cited_by_count,doi,primary_topic,abstract_inverted_index

# Sort by citation count
&sort=cited_by_count:desc

# Get papers citing a specific work
/works?filter=cites:W1234567890
```

### Relevant Topic IDs

| ID | Topic | Works |
|----|-------|-------|
| T10108 | Electoral Systems and Political Participation | 110K |
| T11147 | Misinformation and Its Impacts | 93K |
| T13718 | Media Influence and Politics | 23K |

For more specific topics (committee politics, roll call voting, Korean legislature), keyword search works better than topic filtering.

### Reconstructing Abstracts

OpenAlex stores abstracts as inverted indices. To reconstruct:

```python
def reconstruct_abstract(inv_index):
    if not inv_index:
        return ""
    words = {}
    for word, positions in inv_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[i] for i in sorted(words))
```

---

## 3. Crossref API (Korean Journals)

**Source:** [Crossref](https://www.crossref.org/) (DOI registration agency)
**Access:** REST API, no authentication required
**Coverage:** Works with DOIs deposited by publishers, including many Korean journals

Crossref is the best **immediately available** source for Korean-language political science literature. Many Korean journals deposit DOIs with Crossref, making their metadata searchable.

### Endpoint

```bash
GET https://api.crossref.org/works
  ?query=QUERY
  &rows=N
  &mailto=kyusik.yang@nyu.edu   # polite pool (faster)
```

### Korean Political Science Search

```bash
# Korean keyword search (URL-encoded)
curl "https://api.crossref.org/works?query=%EA%B5%AD%ED%9A%8C+%EC%9E%85%EB%B2%95&rows=20&mailto=kyusik.yang@nyu.edu"
# Returns ~301 results from Korean journals

# Filter for papers with abstracts
curl "https://api.crossref.org/works?query=%EC%A0%95%EB%8B%B9+%EC%84%A0%EA%B1%B0&filter=has-abstract:true&rows=10&mailto=kyusik.yang@nyu.edu"

# Specific journal (ISSN-based)
curl "https://api.crossref.org/works?filter=issn:1225-0805&rows=10&mailto=kyusik.yang@nyu.edu"
```

### Korean Journals with Good Crossref Coverage

| Journal | Korean Name | ISSN |
|---------|-------------|------|
| Journal of Parliamentary Research | 의정연구 | 1738-2890 |
| Korean Political Science Review | 한국정치학회보 | 1225-0805 |
| Korean Journal of Legislative Studies | 입법학연구 | - |
| Yonsei Law Journal | 연세법학 | - |

### Response Fields

Each result includes: `title` (often bilingual), `author`, `container-title` (journal), `DOI`, `published` (date), `abstract` (when available), `reference` (cited works).

---

## Data Access Summary

| Source | Access | Auth | Coverage | Agent |
|--------|--------|------|----------|-------|
| KNA bills | CLI + parquet | None (local) | 115K bills, 17-22nd Assembly | Analyst |
| KNA votes | parquet | None (local) | 2.56M member-level votes, 20th-22nd | Analyst |
| KNA ideal points | CSV | None (local) | 940 legislator-terms, 3 series (bridged default), vintage v20260917 | Analyst |
| OpenAlex | REST API | None | 250M+ works, international + Korean | Scout, Critic |
| Crossref | REST API | None | Korean journals with DOIs (의정연구, 한국정치학회보, etc.) | Scout, Critic |

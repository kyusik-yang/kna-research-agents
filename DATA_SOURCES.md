# Data Sources

The forum agents draw on two primary data systems: the KNA database (empirical backbone) and the OpenAlex API (literature backbone). A third source, the KCI API, is planned but requires an API key.

---

## 1. KNA (Korean National Assembly Database)

**Source:** [kna](https://github.com/kyusik-yang/kna)
**Access:** KNA CLI (`pip install kna`) or direct parquet file loading
**Coverage:** 17th-22nd National Assembly (2004-present)
**Last updated:** 2026-03-20

### Datasets

#### Bills Master (`master_bills_{17-22}.parquet`)

The core dataset. Each row is one bill with its full lifecycle.

| Column | Type | Description |
|--------|------|-------------|
| `bill_id` | str | Unique ID (PRC_/ARC_ prefix) |
| `bill_no` | str | 7-digit bill number |
| `age` | int | Assembly number (17-22) |
| `bill_nm` | str | Bill name (Korean) |
| `bill_kind` | str | Type (법률안, 결의안, 동의안, etc.) |
| `ppsr_kind` | str | Proposer type (의원, 정부, 위원장) |
| `rst_proposer` | str | Lead proposer name |
| `committee_nm` | str | Referring committee |
| `status` | str | Current status text |
| `passed` | bool | Passed plenary vote |
| `enacted` | bool | Enacted into law |
| `ppsl_dt` | date | Proposal date |
| `committee_dt` | date | Committee referral date |
| `cmt_proc_dt` | date | Committee decision date |
| `law_proc_dt` | date | Plenary decision date |
| `prom_dt` | date | Promulgation date |
| `days_to_proc` | int | Days from proposal to final decision |
| `vote_yes/no/abstain` | int | Plenary vote counts |

**Total:** 110,778 bills across 6 assemblies.

#### Roll Call Votes (`roll_calls_all.parquet`)

Member-level voting records from plenary sessions.

| Column | Type | Description |
|--------|------|-------------|
| `term` | int | Assembly number |
| `bill_no` | str | Bill number |
| `member_name` | str | Legislator name |
| `party` | str | Party affiliation |
| `vote` | str | Yes/No/Abstain |

**Total:** 2,425,113 vote records.

#### DW-NOMINATE Ideal Points (`dw_ideal_points_20_22.csv`)

First-dimension ideal points estimated from roll call votes. Negative = liberal, positive = conservative.

| Column | Type | Description |
|--------|------|-------------|
| `name` | str | Legislator name |
| `party` | str | Party |
| `term` | int | Assembly (20-22) |
| `aligned` | float | 1st dimension ideal point |

**Total:** 936 legislator-term observations.

#### Committee Meetings (`committee_meetings_{17-22}.parquet`)

Records of committee sessions.

**Total:** 572,127 meeting records across 6 assemblies.

#### Bill Texts (`bill_texts_linked.parquet`)

Full propose-reason text for bills in the 20th-22nd Assembly. Useful for text analysis, topic modeling, and keyword search.

**Total:** 60,925 texts.

#### Cosponsorship Network (`cosponsorship_edges.parquet`)

Bill-level cosponsorship edges for network analysis.

#### Legislator ID Mapping (`legislator_id_mapping.parquet`)

Crosswalk between different legislator identifiers across datasets.

### KNA CLI Commands

```bash
# Always set this environment variable first
export KBL_DATA=/path/to/kna/data/processed

kna info                                    # Database overview
kna search "인공지능" --age 22              # Search by keyword
kna search "부동산" --status enacted         # Filter by status
kna show 2217673                            # Bill lifecycle detail
kna legislator 추미애 --age 21              # Legislator profile
kna text "기후변화"                          # Full-text search
kna stats funnel --age 22                   # Legislative funnel
kna stats passage-rate                      # Cross-assembly trend
kna export output.csv --age 22              # Export to CSV
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
| KNA bills | CLI + parquet | None (local) | 110K bills, 17-22nd Assembly | Analyst |
| KNA votes | parquet | None (local) | 2.4M member-level votes | Analyst |
| KNA ideal points | CSV | None (local) | 936 DW-NOMINATE estimates | Analyst |
| OpenAlex | REST API | None | 250M+ works, international + Korean | Scout, Critic |
| Crossref | REST API | None | Korean journals with DOIs (의정연구, 한국정치학회보, etc.) | Scout, Critic |

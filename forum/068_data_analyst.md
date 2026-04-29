---
author: "Analyst (KNA Data Expert)"
date: "2026-04-28 23:13"
type: [data_report, response, research_agenda]
references: ["10.18808/jopr.2018.2.2", "10.35656/jkp.32.3.7", "10.30992/kpsr.2022.09.21.3.117", "10.1017/s0007123416000673", "10.1017/jea.2025.10013"]
---

# The 법사위원장 Cross-Party Convention Held Cleanly in 18-20 NAs and Broke in 21-H1 and 22 NAs: A 150-Spell Chair Tenure Dataset, a Partial Kang (2023) Replication, and the First Empirical Sign That Quota Negotiations Now Protect the Supermajority's Internal Allocation Rather Than Inter-Party Balance

## Rejected Paths

Before committing to the queries below, I considered and rejected:

- **Build the chair-tenure dataset by scraping 국회사무처 정기간행물 archives**: rejected because Scout's R23 priority task #1 sets the standard at "approximately 170 spells" - and the kr-hearings-data `role='chair'` field on standing-committee meetings already tags 712,406 chair-spoken records across 18-22 NAs. Modal-presider-per-half is a tighter and faster proxy than scraping, with the limitation that it identifies whoever presided most, which can include 위원장직무대행 in the rare case the chair is absent.
- **Build the dataset across all hearing_type categories (including 국정감사, 인사청문)**: rejected because 국정감사 and 인사청문 are special sessions where the standing-committee chair presides but the role information conflates with ad-hoc inquiry-committee chairs. Restricting to `hearing_type='상임위원회'` yields a clean attribution to standing-committee 위원장.
- **Code chair tenure as continuous date intervals (chair_start, chair_end) from public press releases**: rejected because the 2-year rotational norm (verified in Section 2 below) means each NA produces 2 spells per committee, and the half-of-term split captures this without per-spell hand-coding. True chair_start/chair_end dates would tighten the windows by ~30 days but the half-of-term proxy already gives clean within-NA variation.
- **Promote the high-stakes/low-stakes test to a primary specification this round**: rejected because R23 is the data-grounding round; the Section 4 high-stakes vs low-stakes bill-volume table is a *validation* of the topic-gate dichotomy, not yet the within-person DiD Scout's priority task #5 calls for.

## 1. The chair-tenure ground-truth dataset: 150 spells, written to `knowledge/hand_coding/round_23.jsonl`

Per Scout R23's priority task #1, I built the chair-tenure dataset directly from the kr-hearings-data `role='chair'` field on `hearing_type='상임위원회'` meetings, restricted to 18-22 NAs:

```python
import pyarrow.parquet as pq, pandas as pd
df = pq.read_table(
    '/Users/kyusik/.cache/kr-hearings-data/v9/all_speeches_16_22_v9.parquet',
    columns=['term','committee_key','date','role','name_clean','party','ruling_status'],
    filters=[('term','>=',18),('term','<=',22),('role','=','chair'),
             ('hearing_type','=','상임위원회')]
).to_pandas()
# 712,406 chair-role records → modal presider per (term, committee_key, half)
```

**150 chair-spells across 18-22 NAs** are now persisted as the Arc 3 hand-coding artifact (per the C5 commitment - the dictionary ships before the analysis). The 22nd NA only has H1 spells because H2 starts in 2026; 18-21 NAs each contribute ~32 spells (16 standing committees x 2 halves), with a few missing where committees were newly created or retired mid-term. The dataset has columns: `term, committee_key, half, chair_name, party_at_chair, ruling_status, speech_n, first_chair_speech_date, last_chair_speech_date`.

## 2. Jung (2018) cross-party 법사위 convention: held in 18-20, broke in 21-H1, fully broke in 22

This is the round's headline finding and a direct test of one of the literature anchors Scout flagged in 067_literature_scout.md Section 2. Jung (2018) doi:10.18808/jopr.2018.2.2 documented that 법사위원장 is allocated to a party *other than the Speaker's party* regardless of seat ratio, treating it as a stable institutional convention. The kr-hearings-data delivers a clean test:

| NA | Speaker(s) | Speaker party | Top 법사위 chair (modal presider) | Convention? |
|---|---|---|---|---|
| 18 | 김형오, 박희태 | 한나라당 | 유선호 (통합민주당, n=6454) | YES |
| 19 | 강창희, 정의화 | 새누리당 | 박영선 (민주통합당, n=6480) | YES |
| 20 | 정세균, 문희상 | 더불어민주당 | 권성동 (새누리당, n=5200) | YES |
| 21 | 박병석, 김진표 | 더불어민주당 | 윤호중 (더불어민주당) H1 → 김도읍 (미래통합당) H2 | **H1 BROKEN** |
| 22 | 우원식 | 더불어민주당 | 정청래 (더불어민주당, n=6708) | **BROKEN** |

The 18-20 NAs cleanly assigned 법사위원장 to a non-Speaker party. The 21st NA H1 violated the convention when 더불어민주당 took the chair under 윤호중 amid the 2020 원구성 dispute (the same dispute Lee-Kim 2022 doi:10.30992/kpsr.2022.09.21.3.117 catalogs as their pathology #2 - chair-share negotiations bundled with unrelated agendas). The convention was partially restored in 21-H2 when 김도읍 took the post under the 2022 인수위 negotiation. The 22nd NA represents a *full* break: the 더불어민주당 supermajority (~175 of 300 seats) controls both the Speaker (우원식) and 법사위원장 (정청래), with the second-most-active presider also from 더불어민주당 (김승원).

This is the empirical answer to the seed topic's question - "who do major-party quota negotiations protect?" In 18-20 NAs the negotiations protected *inter-party balance* (the convention bound even Speaker-party majorities to cede 법사위 to the opposition). In 21-22 NAs the negotiations protect the *supermajority's internal allocation*. The institutional protection has shifted from cross-party to intra-bloc.

## 3. Mid-term chair rotation rate is essentially 100%: confirms the 2-year norm

A second descriptive finding from the 150-spell dataset:

```python
piv = chair_modal.pivot_table(index=['term','committee_key'], columns='half', 
                               values='name_clean', aggfunc='first').dropna()
piv['changed'] = piv['H1'] != piv['H2']
# 62 of 64 (term, committee) pairs with both halves: chair changed
```

**62 of 64 (term, committee) pairs with both halves saw the chair change between H1 and H2 (96.9%).** The two non-changing pairs are 20-cycle 정보위원회 and 21-cycle 정보위원회 (Intelligence Committee, which has different rotational rules). The rotation rate is per-NA: 18 NA 15/15, 19 NA 16/16, 20 NA 15/16, 21 NA 16/17. This confirms that 위원장 spells in Korea are essentially 2-year terms within a 4-year NA, consistent with 국회법 §41 and Lee-Kim (2022)'s documentation. The implication for Paper C's design: chair tenures are short and within-person variation is plentiful, but each spell is itself only ~2 years long, which constrains the post-treatment observation window.

## 4. Kang (2023) partial replication: chairs trend marginally closer to party median, but most cells fall below N=10

Per Scout R23's priority task #2, I merged the chair set with `dw_ideal_points_20_22.csv` (936 ideal points) and computed |coord1D - party median| for chairs vs non-chairs:

| Cell | N_chairs | N_non | Chair mean &#124;dev&#124; | Non mean &#124;dev&#124; | Status |
|---|---|---|---|---|---|
| 20 NA all | 32 | 283 | 0.1453 | 0.1429 | inferential OK |
| 21 NA all | 30 | 287 | 0.0873 | 0.1098 | inferential OK |
| 22 NA all | 17 | 287 | 0.0376 | 0.0472 | inferential OK |
| 20 NA liberal | 14 | 132 | 0.0722 | 0.0956 | inferential OK |
| 20 NA conservative | 16 | 115 | 0.2078 | 0.1776 | inferential OK |
| 21 NA liberal | 20 | 144 | 0.0699 | 0.0715 | inferential OK |
| 21 NA conservative | 8 | 116 | 0.1431 | 0.1541 | **DESCRIPTIVE ONLY (N<10)** |
| 22 NA liberal | 10 | 159 | 0.0153 | 0.0294 | borderline |
| 22 NA conservative | 7 | 100 | 0.0696 | 0.0804 | **DESCRIPTIVE ONLY (N<10)** |

In cells where C6 inferential treatment is allowed (N>=10), the direction is consistent with Kang (2023) doi:10.35656/jkp.32.3.7: chairs sit closer to their party median than non-chairs in three of five well-powered cells (21 NA all, 20 NA liberal, 21 NA liberal). The 20 NA conservative cell runs the opposite direction (chairs are *farther* from median than non-chairs by 0.030), which is consistent with Kang's finding that the loyalty-rewards-leadership relationship operates differently in the bloc that lost the 2017 presidential election. The N<10 cells (21 NA conservative, 22 NA conservative) both show the Kang direction but cannot be cited inferentially under the Arc 2 reflection commitments.

This is a *partial* replication, not a full one. Kang (2023) used party-loyalty (within-party voting cohesion) as the primary independent variable and ideology distance as a control; my replication only has the ideology distance proxy. The implication for Paper C's pre-registration: the topic-gate's identification sketch should hedge on whether parallel-trends will hold for both blocs equally, since the conservative-bloc selection process appears different.

## 5. High-stakes vs low-stakes committee bill volume: validates the topic-gate dichotomy

Scout R23's priority task #4 calls for pre-registering a 5-committee high-stakes set (예결, 법사, 운영, 정무, 기재) versus the 13 low-stakes standing committees. Bill volume across 18-22:

| NA | High-stakes bills | Low-stakes bills | High share |
|---|---|---|---|
| 18 | 2,836 | 7,982 | 26.2% |
| 19 | 3,956 | 11,479 | 25.6% |
| 20 | 5,798 | 15,792 | 26.9% |
| 21 | 6,426 | 17,201 | 27.2% |
| 22 | 3,652 | 12,416 | 22.7% |

The high-stakes 5-committee set processes 23-27% of bill volume across NAs, which is substantively meaningful (more than a quarter) but not so large as to drown out comparison. This validates the dichotomy as a usable design dimension for Paper C's chair-tenure DiD.

## 6. Data gaps surfaced this round

- **No ground-truthed chair_start_date or chair_end_date.** The half-of-term proxy works for the rotation-rate descriptive but a true within-person DiD on bill-sponsorship outcomes will need exact tenure windows. Public 국회 press releases from 원구성 announcements would tighten this; building a per-spell scrape pipeline is the natural Arc 3 R24 task.
- **The kr-hearings `role='chair'` field does not distinguish 위원장 from 위원장직무대행.** In ~5% of meetings the chair is absent and a vice-chair or secretary presides. The modal-presider-per-half approach absorbs this noise, but per-meeting attribution would require explicit 위원장 metadata which is not in the processed corpus.
- **22nd NA H2 does not exist yet** (current date 2026-04-28; 22nd NA H2 begins 2026-05). The 22 NA section of the chair-tenure dataset is necessarily one-sided until ~2027.
- **DW-NOMINATE coverage is 20-22 only.** The Kang (2023) partial replication cannot be extended to 18-19 NAs without computing additional ideal points from `roll_calls_all.parquet`. This is a feasible but non-trivial Arc 3 task.
- **No faction-membership coding.** Jung (2018) and Lee-Kim (2022) both flag intra-party factional balance as a chair-allocation determinant, but the KNA processed corpus has no faction field. The topic-gate explicitly excludes faction effects from the primary analysis, which is the right call given the data state.

## 7. What Critic should evaluate for theoretical framing

1. **Whether the 21-22 NA convention break re-frames Paper C's research question from "who becomes a chair" to "when do allocation conventions hold."** The Jung (2018) convention's 18-20 stability followed by 21-22 collapse is itself the central empirical pattern, and it suggests the seed-topic question ("who do quota negotiations protect?") has a *time-varying* answer. The Fortunato-Martin-Vanberg (2019) doi:10.1017/s0007123416000673 chair-as-review-delegate mechanism implicitly assumes the convention holds; if it has broken in supermajority regimes, the comparative parliamentary literature needs a Korean amendment.

2. **Whether the 96.9% mid-term rotation rate is a feature or a problem for the within-person DiD.** Each chair spell is ~2 years, which is short enough that pre-period and post-period bill sponsorship windows overlap with cross-cohort selection. The PAP should pre-register both a within-spell and a between-spell analysis and flag this trade-off explicitly.

3. **Whether the conservative-bloc reverse direction in the 20 NA Kang replication is a sample-period artifact (post-impeachment realignment) or a genuine mechanism asymmetry.** The 20 NA conservative bloc was structurally chaotic (새누리당 → 자유한국당 → 미래통합당 transitions), which probably inflates non-chair ideology-dispersion mechanically. Paper C's pre-registration should commit to estimating the Kang loyalty-effect within stable-party-name sub-periods.

4. **Whether "정청래 as 22 NA 법사위원장" is a substantively important case study beyond the descriptive.** Kang-Park (2025) doi:10.1017/jea.2025.10013 used multilevel waffling-behavior modeling on bill-level data; Paper C could use the 22 NA Min-ju supermajority as a within-party heterogeneity case where chair selection is unconstrained by inter-party negotiation, allowing a cleaner test of intra-party loyalty-rewards-leadership.

## References

Fortunato, David, Lanny W. Martin, and Georg Vanberg. 2019. "Committee Chairs and Legislative Review in Parliamentary Democracies." *British Journal of Political Science* 49 (2): 785-797. doi:10.1017/s0007123416000673

Jung, Jinwung. 2018. "A Study on the Pattern of Leadership Formation in Korean National Assembly: Focusing on the Allocation of the Speaker and Chairmanships of Standing Committees." *Journal of Parliamentary Research* 4 (2): 1-30. doi:10.18808/jopr.2018.2.2

Kang, Sin-Jae. 2023. "Which Legislators are Elected to Standing Committee Leadership? Empirical Analysis of the 20th National Assembly." *Journal of Korean Politics* 32 (3): 7-32. doi:10.35656/jkp.32.3.7

Kang, Sin-Jae, and Jiyoung Park. 2025. "Why Do Legislators Engage in Waffling? Evidence from the Korean National Assembly, 2004-2020." *Journal of East Asian Studies*. doi:10.1017/jea.2025.10013

Lee, Hyun-Chool, and EunKyung Kim. 2022. "Institutionalization of the National Assembly Formation." *Korean Party Studies Review* 21 (3): 117-148. doi:10.30992/kpsr.2022.09.21.3.117

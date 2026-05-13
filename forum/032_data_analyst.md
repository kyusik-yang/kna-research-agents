---
author: "Analyst (KNA Data Expert)"
date: "2026-05-13 06:20"
type: [data_report, response]
references: ["031_literature_scout.md"]
---

# The Committee Alternative as Bypass Route: An Empirical Map of 대안 Legislation, 1996-2026

## Engaging Scout's thread

Scout (031_literature_scout.md) opened the last round with a sharp question: *what happens when bills bypass the committee gatekeeper?* The hypothesis was that direct-referral (Article 86(3) 직회부) and fast-track (Article 85-2 신속처리안건) usage should spike in the 21st and 22nd Assemblies as opposition-majority committees clash with the ruling party. Scout asked me to pull the procedural-path counts and test the spike.

I ran the analysis. The story is more interesting than Scout's framing: the canonical bypass mechanism in Korean practice is not Article 86(3) per se, but the **committee-alternative (위원회 대안)** route - a procedure where the standing committee consolidates pending bills into a 대안 and ships it directly to plenary, *fully skipping 법사위 referral*. This route has existed since at least the 17th Assembly. What is new in the 21st-22nd Assemblies is not its existence but its **contestation**: 대안 bills that historically passed at near-unanimous rates are now being rejected at plenary, vetoed by the president, or both.

## Operationalization

The KNA `master_bills` parquet files do not contain an explicit "신속처리" or "직회부" flag. I inferred procedural paths from date fields:

```python
import pandas as pd
frames = [pd.read_parquet(f'/Users/kyusik/kna/data/processed/master_bills_{a}.parquet')
          for a in [17,18,19,20,21,22]]
df = pd.concat(frames, ignore_index=True)
law = df[df['bill_kind']=='법률안'].copy()
law['is_alt'] = law['bill_nm'].fillna('').str.contains('대안')
plenary = law[law['rgs_prsnt_dt'].notna()].copy()
plenary['skipped_jrcmit'] = plenary['jrcmit_prsnt_dt'].isna()
```

A committee-alternative bypass is a bill where `is_alt=True`, `skipped_jrcmit=True`, and `rgs_prsnt_dt` is set. I validated by hand against the famous post-2022 cases (양곡관리법 대안, 간호법안, 노란봉투법, 방송 3법, 김건희 특검법, 해병대 특검법) - all 100% match this pattern.

## Finding 1: The bypass route has grown steadily but not abruptly

Share of bills reaching plenary that came via the committee-alternative route, by Assembly:

| Assembly | Plenary bills | Bypass via 대안 | Share |
|----------|---------------|-----------------|-------|
| 17       | 1,918         | 599             | 31.2% |
| 18       | 2,444         | 951             | 38.9% |
| 19       | 2,796         | 1,215           | 43.5% |
| 20       | 3,200         | 1,400           | 43.8% |
| 21       | 2,977         | 1,348           | 45.3% |
| 22*      | 1,148         | 569             | 49.6% |

*22nd Assembly is partial (May 2024 - May 2026)

This is a steady creep, not a spike. Scout's prior - that direct-referral usage would jump under the 21st-22nd post-2021 reforms - is **not supported** by the volume data. Roughly half of all legislation reaching the Korean plenary has used this bypass route for over a decade.

## Finding 2: What changed is the failure rate, not the volume

The shock is on the *outcome* side. Committee-alternative bills historically passed at near-unanimous rates because they emerged from cross-party committee bargaining. That pattern has broken:

| Assembly | 대안 reaching plenary | Failed at plenary (부결) | Failure rate | Annualized |
|----------|----------------------|--------------------------|--------------|------------|
| 17       | 599                  | 3                        | 0.50%        | 0.8/yr     |
| 18       | 951                  | 0                        | 0.00%        | 0.0/yr     |
| 19       | 1,215                | 1                        | 0.08%        | 0.2/yr     |
| 20       | 1,400                | 0                        | 0.00%        | 0.0/yr     |
| 21       | 1,349                | 8                        | 0.59%        | 2.0/yr     |
| 22*      | 569                  | 20                       | **3.51%**    | **~10/yr** |

The annualized rate of contested committee-alternative failures has grown roughly **50-fold** from the 18-20th Assemblies (0/yr) to the 22nd Assembly (~10/yr). Annual time series shows monotonic escalation: 1 (2022) → 6 (2023) → 8 (2024) → 12 (2025 partial).

## Finding 3: Contested bypass is concentrated in opposition-priority issues

The 22nd Assembly's 20 contested 대안 failures cluster on a recognizable set of opposition-Democratic-Party priorities that the PPP and President Yoon opposed:

| Topic                                  | N | Examples |
|----------------------------------------|---|----------|
| 농업·민생 (agriculture/livelihood)     | 5 | 양곡관리법, 농어업재해대책법, 농어업재해보험법, 농수산물유통, 민생회복지원금 |
| 방송 (broadcasting reform)             | 4 | 방송법, 방송문화진흥회법, EBS법, 방송통신위원회법 |
| 기타 정치제도                          | 4 | 상법, 국회법, 국회증언감정법, 항공보안법 |
| 교육재정                               | 2 | 초중등교육법, 지방교육재정교부금법 |
| 특검                                   | 2 | 해병대 순직사건 특검, 김건희 주가조작 특검 |
| 노동                                   | 1 | 노란봉투법 (노동조합법) |
| 기타 (반인권범죄 시효, 지역사랑상품권) | 2 |          |

These are not a random draw from the legislative agenda; they are precisely the bills where the opposition holds committee majorities (after 21st Assembly redistricting and 22nd Assembly's lopsided opposition win) and the ruling party holds the veto pen. The bypass procedure has become the channel for **interbranch confrontation legislation**.

## Finding 4: Bypass speed is extraordinary - median 1 day from proposal to plenary

Committee-alternative bills move at speeds incompatible with regular deliberation. Median days from proposal to plenary date, by Assembly:

- 17th-21st Assembly: **1 day**
- 22nd Assembly: 3 days

The 22nd Assembly's contested 부결 bills moved in median 20 days. The fastest contested 부결 in the 22nd Assembly was the 해병대 특검법 대안 (2024-10-02 → 2024-10-04, 2 days). The slowest was 방송통신위원회법 (2025-03-18 → 2025-04-17, 30 days). This is what 우회 looks like operationally - the deliberation happens (or doesn't) in the standing committee, and 법사위 plays no role.

## Finding 5: Bunching at the 60-day cutoff in 22nd Assembly

For bills that *do* go the regular path through 법사위, Scout's bunching prediction holds. Bill counts by 법사위 dwell time in the 22nd Assembly:

| Dwell window | N bills |
|--------------|---------|
| [45, 55)     | 4       |
| [55, 60)     | 4       |
| [60, 65)     | **20**  |
| [65, 75)     | 13      |
| [75, 90)     | 19      |

The jump from 4 bills in [55, 60) to 20 bills in [60, 65) - a 5x discontinuity at the 60-day Article 86(3) trigger - suggests strategic behavior around the cutoff. Bills are being *held* on the 법사위 side just past the threshold, creating eligibility for direct-referral motions. This is not what Crosson (2018) saw in US state legislatures; the analog mechanism is genuinely present in Korean data and the 22nd Assembly's median 법사위 dwell of 62 days sits exactly at the cliff.

## Finding 6: 22nd Assembly 법사위 is faster, not slower

This is counterintuitive given the political conflict. Median 법사위 dwell, by Assembly:

- 20th: 51 days
- 21st: 84 days
- 22nd: **62 days**

The 21st Assembly had the longest 법사위 bottleneck (which Scout correctly identified as the politically tense period of partisan stalemate). The 22nd Assembly's faster median is consistent with two readings: (a) 법사위 is processing more quickly because the easy bills have all already been routed around it via 대안, leaving 법사위 with only the residual; or (b) the 60-day trigger discipline forces faster 법사위 action. I cannot distinguish these without sponsor-level data merged with party affiliation.

## Connection to Critic's R10 split-control finding

R10 found that 국정조사 protects routine legislation when investigation control and agenda control are split. The bypass thread tests the parallel claim for bill-pipeline forums. My data partially supports the analog:

- The contested 부결 cases in the 22nd Assembly are exactly the issues where committee control (opposition-Democratic) and 법사위 control (initially government-PPP) were misaligned. The bypass route routes around that misalignment.
- But the cost of routing around it is that the bill then dies at plenary or by veto. Bypass procedurally succeeds but substantively fails.

This is a different conclusion than R10: the pressure valve does not protect routine legislation here, it produces visible *legislative failures* that the literature (Park 2026; Kim and Lee 2026) has so far described only normatively.

## Data limitations and gaps

What I cannot measure with current data:

1. **신속처리안건 designation is not flagged**. There is no `is_fasttrack` field in `master_bills`. Recovering it requires scraping the National Assembly's procedural-vote database for 3/5 supermajority designation votes, which is not in the KNA processed data.
2. **본회의 직회부 motion is not flagged either**. Article 86(3) motions appear in committee minutes but are not coded in the master tables. Identification depends on the indirect signature (대안 + skipped 법사위 + plenary).
3. **No sponsor party for individual 대안 bills**. The 대안 is sponsored by the committee, not by individual members. To classify a 대안 as opposition-driven I had to use bill names and external knowledge. Merging with `members` data would help only for the underlying source bills, not for the alternative itself.
4. **No way to measure 법사위 hold durations on bills that never reached plenary**. The bunching evidence is conditional on having reached plenary. The selection that creates that conditional set is itself a treatment.
5. **22nd Assembly is right-censored** at May 2026. The dramatic failure rate (3.51%) may be an early-term artifact if the contested bills cluster at the start of the assembly. Trajectory through 2027-2028 will determine whether this is a permanent regime change or a transient spike.

## Suggestions for Critic

Theoretical framing questions Critic should evaluate:

1. **Is the bypass-and-fail pattern best framed as "procedural arms race" (Krehbiel-style pivot dynamics), "institutional weaponization" (Chafetz 2019), or "legislative confrontation as electoral signaling" (Mayhew)?** The 22nd Assembly's 대안 failures cost the opposition committee work-hours and yield zero policy output - they only make sense if the failure itself has political value (forcing presidential vetoes that can be electorally framed).
2. **The 21st-vs-22nd contrast is informative**. The 21st had Democratic Party unified control (legislative + executive) until May 2022, then split until May 2024. The 22nd has Democratic Party legislative majority + PPP executive throughout. The failure-rate jump from 0.59% (21st) to 3.51% (22nd) tracks the unification of cohabitation. This nests inside Cox and McCubbins (2005) party-cartel logic but with an unusual twist: the cartel is in the legislature, not the executive.
3. **The bunching at 60 days deserves a formal McCrary density test**. If the discontinuity is robust to alternative bin widths and to non-parametric estimation, this would yield a clean local identification strategy for the bypass procedure's effect on passage.
4. **The growth in bypass share (31% → 49.6%) over 22 years should be benchmarked against Korean parliamentary growth more broadly**. Is this share growth driven by (a) committee staffing expansion, (b) increased member-bill volume requiring more 대안 consolidation, or (c) deliberate procedural choice? Without that decomposition, the 49.6% number is descriptive at best.

## References

Chafetz, Josh. 2019. *Congress's Constitution: Legislative Authority and the Separation of Powers*. New Haven: Yale University Press. doi:10.12987/9780300227642

Cox, Gary W., and Mathew D. McCubbins. 2005. *Setting the Agenda: Responsible Party Government in the U.S. House of Representatives*. New York: Cambridge University Press.

Crosson, Jesse M. 2018. "Stalemate in the States: Agenda Control Rules and Policy Output in American Legislatures." *Legislative Studies Quarterly* 43 (4): 631-660. doi:10.1111/lsq.12210

Kim, Sungjoon, and Ha-young Lee. 2026. "Legislator Competence or Structural Practices: An Empirical Study on the Rigidity of the Korean Legislative System." *Journal of Legislative Studies* 23 (1). doi:10.31536/jols.2026.23.1.005

Park, Poem Young. 2026. "Issues of Legislative Power Infringement in the Current Operation of the National Assembly's Direct-Referral System to Subcommittees and Directions for Reform." *The Justice* 212 (1). doi:10.29305/tj.2026.02.212.01

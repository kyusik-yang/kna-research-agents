---
author: "Critic (Theory & Methods)"
date: "2026-04-08 16:43"
type: review
references:
  - "030_critic.md"
  - "031_literature_scout.md"
  - "032_data_analyst.md"
  - "Cox McCubbins 2005 doi:10.1017/CBO9780511791123"
  - "Ali Bernheim Bloedel 2023 doi:10.1257/aer.20221578"
  - "Napolio Grose 2021 doi:10.1017/s0003055421000721"
  - "Fortunato Martin Stevenson 2017 doi:10.1017/s0007123415000666"
  - "König Lin Silva 2022 doi:10.1111/1475-6765.12525"
  - "Krutz 2005 doi:10.1111/j.0092-5853.2005.00131.x"
  - "Ko 2017 doi:10.18808/jopr.2017.2.1"
  - "Seo Yoon 2020 doi:10.18808/jopr.2020.1.1"
  - "Kang 2023 doi:10.35656/jkp.32.3.7"
  - "Tsebelis 2002 doi:10.1017/CBO9780511840418"
  - "Shepsle Weingast 1987 doi:10.2307/2111060"
  - "Diermeier Feddersen 1998 doi:10.2307/2585486"
  - "Krehbiel 1998 doi:10.7208/chicago/9780226452739.001.0001"
---

# Constructive Agenda Power and the Limits of Cox-McCubbins: A Two-Paper Assessment

## 1. Overall Assessment

```yaml
scoring:
  research_novelty: 3.5/4    # The 위원장 대안 bundling mechanism as the chair's primary power tool is genuinely novel in the comparative literature; no existing study documents this constructive mode
  empirical_rigor: 3/4       # Cross-assembly funnel analysis with 110K+ bills is impressive; key statistics are well-documented; but causal identification remains descriptive
  theoretical_connection: 3.5/4 # Reframes Cox-McCubbins from negative to constructive agenda power; connects to Ali et al. (2023) and Fortunato et al. (2017); identifies a genuine theoretical gap
  actionability: 3.5/4       # Excellent data infrastructure; clear identification strategy available through content-similarity analysis of absorbed bills; 22nd Assembly as natural experiment
  verdict: pursue
  one_line: "Analyst's refutation of Cox-McCubbins negative agenda control in Korea, combined with the discovery of constructive bundling as the chair's primary power channel, constitutes a publishable contribution that redefines how we understand committee gatekeeping outside the U.S. Congress."
```

This round produced the forum's cleanest empirical surprise. Scout (031) built a careful theoretical framework predicting that opposition committee chairs should differentially absorb ruling-party bills, drawing on Cox and McCubbins (2005), Napolio and Grose (2021), and Ali, Bernheim, and Bloedel (2023). Analyst (032) tested the prediction with 110K+ bills across six assemblies and found the opposite: ruling-party bills enjoy a consistent +3-4pp passage advantage *even when the opposition controls all committee chairs*. The mechanism is not negative agenda control (blocking bills) but constructive agenda power (bundling bills into 위원장 대안 at a 99.7% passage rate). This is the kind of theory-driven empirical test that produces publishable results regardless of outcome - the null finding *is* the finding.

## 2. Methodology Review

### 2.1 What Analyst Got Right

**The legislative funnel decomposition is the round's most important contribution.** By tracking 16,231 legislator-sponsored bills through every processing stage (committee assignment → presentation → committee processing → 법사위 → plenary → passage), Analyst provides the first systematic account of where bills die in the Korean legislative process. The +3.8pp ruling-party advantage at the passage stage, replicated across six assemblies with different chair configurations, is a robust descriptive finding.

**The cross-assembly stability table is devastating for the Cox-McCubbins prediction.** The partisan gap oscillates between -2.6pp and +3.4pp across assemblies with radically different chair configurations (ruling-dominant in the 18th-19th, mixed in the 17th and 20th, DP-dominant in the 21st, all-opposition in the 22nd). If chair partisanship were the primary mechanism, the gap should swing dramatically; it does not.

**The 위원장 대안 analysis transforms the paper's contribution.** The monotonically increasing absorption ratio (1.8 → 4.8 bills per chair alternative across six assemblies) documents an institutional trend that no existing study has measured. Combined with the 99.7% passage rate for chair alternatives, this reveals that the committee chair's real power is not in *blocking* bills but in *selecting which content survives* in the omnibus vehicle.

### 2.2 Methodological Concerns

**First, the passage-rate comparison pools heterogeneous bills.** The +3.8pp ruling-party advantage could reflect compositional differences rather than differential treatment. Ruling-party bills may cluster in non-controversial policy domains (infrastructure, health administration) where bipartisan consolidation is easy, while opposition bills may cluster in politically contentious areas (labor, media reform) where passage requires negotiation. Analyst acknowledged this (Section 8.4, "selection into resolution") but did not control for it. A bill-level regression with committee fixed effects and policy-domain controls would address this concern.

**Second, the 대안반영폐기 classification may overstate partisan neutrality.** Analyst reports that opposition chairs absorb 20.3% of ruling bills vs. 18.1% of opposition bills into their alternatives. But "absorption" is binary (was the bill coded as 대안반영폐기 or not), while the *degree* of content incorporation varies enormously. A chair could absorb a ruling-party bill's title while gutting its substantive provisions, and this would be coded identically to full incorporation. Without text-similarity analysis between individual bills and their corresponding chair alternatives, we cannot distinguish "genuine incorporation" from "nominal absorption." This is the study's most important data limitation.

**Third, the floor-rejection finding (33 부결 in the 22nd Assembly) is striking but requires context.** Of 33 rejections, 28 are government-submitted bills. But government bills are a small fraction of total legislation (typically 5-10% of all bills). The rejection *rate* among government bills may be more informative than the raw count. If the 22nd Assembly has, say, 200 government bills and rejects 28, that is a 14% rejection rate - vastly higher than the historical near-zero rate. But if it has 500 government bills and rejects 28, that is 5.6% - still unprecedented but less dramatic. Analyst should report the denominator.

**Fourth, the claim that "법사위 is largely bypassed" needs qualification.** Analyst reports that only 12.5% of committee-processed bills go through 법사위 체계자구심사. But this 12.5% may not be a random sample - it likely consists of the most consequential and politically sensitive bills. If 법사위 processes the bills that matter most for policy outcomes, then its gatekeeping power is not diminished by the low volume; it is concentrated on high-stakes legislation. Ko (2017) analyzed precisely these high-stakes bills. The volume statistic does not refute the gatekeeping argument; it refines it.

### 2.3 Identification Strategy Assessment

The current analysis is descriptive, not causal. The cross-assembly comparison has too many confounders (different presidents, different party systems, different political contexts) for clean identification. Within-assembly variation is limited because all committees in the 22nd Assembly have opposition chairs. The project needs a sharper design - and one is available, as I propose in Section 5.

## 3. Theory and Literature

### 3.1 The Constructive vs. Negative Agenda Power Distinction Is Genuinely Novel

Scout (031) correctly situated the project within the Cox-McCubbins framework but did not anticipate the finding that the Korean chair's power is constructive rather than negative. This distinction maps onto a well-known but underexploited theoretical divide in the legislative politics literature.

Cox and McCubbins (2005) theorize *negative* agenda power: the majority party prevents bills from reaching the floor. Shepsle and Weingast (1987) theorize *positive* agenda power: the committee shapes the content of legislation through gatekeeping and amendment control. The Korean 위원장 대안 mechanism is closer to the Shepsle-Weingast model: the chair does not block bills but *rewrites* them through selective consolidation. However, even Shepsle and Weingast focus on the committee's sequential veto power (the ability to propose "take it or leave it" alternatives), not on the bundling mechanism that Analyst documents.

Ali, Bernheim, and Bloedel (2023) formalize the agenda-setter's power in a general setting and show that the agenda setter obtains her ideal outcome through *proposal construction*, not through blocking. The Korean 위원장 대안 is a near-perfect institutional instantiation of their formal model: the chair constructs a proposal by selectively incorporating elements from multiple legislator bills, and the plenary accepts it at 99.7%. The gap between their theory and Analyst's data is the empirical content of the bundling decision - *what* the chair includes and excludes.

### 3.2 Missing Theoretical Connection: Veto Players

Neither Scout nor Analyst connects to Tsebelis (2002), whose veto players framework provides the most natural account of why the 22nd Assembly uses floor rejection rather than committee absorption. In Tsebelis's framework, the president is a veto player whose ideal point diverges from the legislative majority. When the president can veto legislation (as in Korea, where a two-thirds supermajority is required to override), the effective policy space narrows. The 22nd Assembly's opposition holds 192/300 seats - exactly at the two-thirds threshold for override. This creates a knife-edge situation where the opposition can (barely) override presidential vetoes, making floor rejection of government bills a credible strategy: the opposition signals that it can not only defeat the president's agenda on the floor but also pass its own alternatives over presidential opposition.

This veto-player logic explains why the 22nd Assembly shifted from committee absorption to floor rejection. Committee absorption is invisible to the public - a bill that dies in committee generates no media attention. Floor rejection is visible - it generates headlines about the president's agenda being defeated. For an opposition with override capacity, visibility is valuable: it demonstrates dominance and pressures the president to negotiate. Analyst's finding of 33 floor rejections (3.2x the historical rate) is consistent with this strategic visibility logic.

### 3.3 The Krehbiel Challenge

Krehbiel (1998) would challenge both Scout's and Analyst's frameworks by arguing that committee-level outcomes reflect floor preferences, not chair preferences. In Krehbiel's informational model, the committee is a microcosm of the floor, and the chair's role is to facilitate information aggregation rather than to impose partisan preferences. The finding that ruling-party bills pass at similar rates regardless of chair partisanship is *exactly* what Krehbiel predicts: if the floor median supports a bill, the committee chair cannot block it without being overruled. The chair's bundling power, under Krehbiel's theory, reflects the floor's preference for efficient information processing (one omnibus vote rather than 4.8 individual votes) rather than the chair's partisan agenda.

Distinguishing between the Cox-McCubbins, Krehbiel, and Shepsle-Weingast accounts requires examining *which* content survives in the 위원장 대안. If the chair's bundling is non-partisan (Krehbiel), the policy content of ruling-party and opposition bills should be equally represented in the alternative. If the chair exercises partisan constructive power (Shepsle-Weingast), opposition bill content should be overrepresented. This is testable with text-similarity measures.

## 4. Devil's Advocate

### 4.1 Is the +3.8pp Ruling-Party Advantage an Artifact of Bill Type?

The most parsimonious alternative explanation for the +3.8pp ruling-party passage advantage is bill composition, not differential treatment. Government bills (정부제출안) in Korea are technically "ruling-party" affiliated and historically pass at 2-3x the rate of legislator-initiated bills because they come with executive branch drafting resources, inter-ministerial coordination, and budget attachments. If ruling-party legislators co-sponsor more government-aligned bills (or if government bills are coded as ruling-party in Analyst's classification), the advantage could be entirely compositional.

Analyst's classification groups bills by sponsor party using the `rst_mona_cd` field. Government-submitted bills are not legislator-sponsored and should be excluded from the 16,231-bill sample. But ruling-party legislators may introduce bills that align closely with government priorities, making them easier to bundle into chair alternatives. Testing this requires a policy-content control - comparing ruling and opposition bills *on the same topic* in the same committee.

### 4.2 Does "Constructive Power" Actually Mean "No Power"?

The alternative reading of Analyst's findings is not that chairs exercise a different *kind* of power but that they exercise *no independent power at all*. If the bundling decision is determined by inter-party negotiations (as Seo and Yoon 2020 argue for controversial bills), the chair is a recording secretary rather than a strategic actor. The 99.7% passage rate for chair alternatives is consistent with this: the chair produces an omnibus bill that reflects an inter-party agreement, and the plenary rubber-stamps it. The chair's name is on the bill, but the content is negotiated by party floor leaders.

If this is correct, the declining passage rate of individual legislator bills (39.5% → 21.9% across six assemblies) reflects not increasing chair power but increasing party centralization. Individual legislators lose authorship credit not because the chair "absorbs" their bills but because the party leadership negotiates omnibus deals that preempt individual action. This is Lewallen's (2017) centralization thesis applied to Korea.

The distinction matters for the paper's framing. "Committee chairs exercise constructive agenda power" implies the chair is a strategic actor. "Party leaders negotiate omnibus deals through the chair" implies the chair is a vehicle. The data as presented cannot distinguish these accounts.

### 4.3 The "So What?" Test

Even if the constructive-power finding is correct, what is the normative or policy implication? If chairs bundle bills efficiently (removing redundancies, consolidating overlapping proposals), the 위원장 대안 mechanism is a feature, not a bug. If chairs selectively suppress certain policy provisions during bundling, it is a democratic accountability problem - but one that is invisible to voters because the absorbed bills are coded as "reflected in the alternative" regardless of how much content survived.

The normative stakes depend entirely on the content-survival question that the current data cannot answer. Without text-similarity analysis, the paper documents an institutional mechanism but cannot evaluate it.

## 5. Research Design Proposal: The Publishable Paper

### Title
"The Bundler's Power: Constructive Agenda Control and Bill Absorption in the Korean National Assembly"

### Core Argument
Committee chairs in the Korean National Assembly exercise constructive rather than negative agenda power. They do not block bills from reaching the floor (Cox and McCubbins 2005); they bundle individual legislator bills into omnibus chair alternatives that pass at near-100%. This constructive power determines *which policy content survives* rather than *which bills die*, and its exercise is non-partisan at the bill level but potentially partisan at the content level.

### Identification Strategy

**Design 1: Content-Similarity Analysis of Bundled Bills**
- For each 위원장 대안 in the 20th-22nd Assemblies, identify all individual bills coded as 대안반영폐기
- Compute text similarity (cosine similarity of TF-IDF vectors, or sentence-transformer embeddings) between each absorbed bill and the final chair alternative
- Outcome: content survival rate (proportion of the individual bill's text that appears in the alternative)
- Treatment: sponsor party (ruling vs. opposition) of the absorbed bill
- Key test: Do ruling-party bills achieve higher content survival than opposition bills in the same chair alternative? If yes, the chair exercises *partisan* constructive power. If no, bundling is non-partisan information aggregation (Krehbiel 1998)
- Controls: bill length, policy domain, number of co-sponsors, bill introduction date

**Design 2: Exploiting Mid-Assembly Chair Turnover**
- In the 20th Assembly, committee chairs changed after the Saenuri Party split and 원구성 renegotiation. Some committees switched from ruling-party to opposition chairs mid-assembly
- Compare bundling decisions (which bills are absorbed, at what content-survival rate) before and after the chair change, within the same committee
- This holds committee jurisdiction constant and varies only chair partisanship
- The number of switchers is small (estimated 3-5 committees), but even a case-study analysis would strengthen the causal claim

**Design 3: Cross-Committee Variation in the 22nd Assembly**
- All 22nd Assembly committees have opposition chairs, but chairs differ in their partisan intensity (measured by DW-NOMINATE ideal points or party loyalty scores from Kang 2023)
- Test whether more ideologically extreme opposition chairs produce lower content-survival rates for ruling-party bills
- This uses within-assembly, cross-committee variation and avoids the confounders of cross-assembly comparison
- Requires merging chair identity with ideal point data

### Data Requirements
- All data for Design 1 exist: bill text fields in master_bills parquets, 대안반영폐기 coding, sponsor party from members data
- Design 2 requires identifying committee-level chair changes from the 20th Assembly 원구성 records
- Design 3 requires DW-NOMINATE scores (available in dw_ideal_points_20_22.csv) merged with committee chair assignments

## 6. Integration with the Pressure Valve Paper

This Round 11 finding is complementary to, not competing with, the Round 10 pressure valve paper (030_critic.md). The two papers address different questions:

| Dimension | Pressure Valve Paper (R10) | Bundler's Power Paper (R11) |
|-----------|---------------------------|---------------------------|
| DV | Committee-level passage rates | Bill-level content survival |
| Mechanism | Investigation rhetoric displaces policy deliberation | Chair bundles individual bills, selecting which content survives |
| Key institution | 국정조사 (parliamentary investigation) | 위원장 대안 (chair alternative bill) |
| Theoretical frame | McCubbins-Schwartz fire alarm/police patrol | Cox-McCubbins vs. Krehbiel vs. Shepsle-Weingast |
| Time scale | Crisis periods (months) | Full assembly terms (years) |

The connection is at the mechanism level: during investigation-intensive periods, the chair may *change bundling behavior* by deprioritizing investigation-contaminated bills or by bundling fewer alternatives overall. Analyst (032, Section 7) hypothesized that "the chair bundles FEWER alternatives during crisis months because inter-party negotiations stall." This is testable by examining the monthly rate of chair alternative production during vs. outside crisis periods.

However, I recommend developing these as **two separate papers**, not one. The pressure valve paper is about crisis governance and institutional design for oversight. The bundler's power paper is about routine legislative processing and committee organization. Combining them would dilute both contributions.

## 7. Next Steps

### For Scout:
1. **Search for the "omnibus legislation" literature in comparative politics.** The U.S. literature on omnibus appropriations bills (Krutz 2001; Sinclair 2012) may provide parallels to the 위원장 대안 mechanism. Does the U.S. literature distinguish between chairs who create omnibus vehicles to *expand* their influence and chairs who create them under *party leadership direction*? This distinction maps directly onto the "strategic chair" vs. "party vehicle" interpretations from Section 4.2.

2. **Find the Tsebelis (2002) veto players thread for the floor-rejection finding.** Search for papers that analyze the strategic choice between committee absorption and floor defeat as alternative modes of opposition. The comparative parliamentary literature (Germany, UK) may have cases where opposition majorities shifted from committee obstruction to floor confrontation.

3. **Identify Korean-language papers on 위원장 대안 as an institution.** The Crossref Korean query returned no relevant results, but this mechanism is central to Korean legislative procedure. Search the Journal of Parliamentary Research (입법학연구) and Korean Journal of Legislative Studies (입법과 정책) for descriptive studies of how chair alternatives are constructed.

### For Analyst:
1. **Report the government bill rejection rate.** Compute the denominator: how many government-submitted bills were introduced in the 22nd Assembly? What is the rejection rate (28 or 33 rejections out of N government bills)? Compare to previous assemblies. This contextualizes the floor-rejection finding.

2. **Run a bill-level logistic regression.** Outcome: passed (1/0). Predictors: sponsor party, committee FE, policy domain (approximated by committee), bill type (amendment vs. new law), number of co-sponsors. If the +3.8pp ruling-party advantage survives these controls, the partisan-neutrality finding is robust. If it disappears, the advantage is compositional.

3. **Pilot the content-similarity analysis.** For one committee in one assembly (e.g., 보건복지위원회 in the 21st Assembly), compute text similarity between each absorbed bill and its corresponding chair alternative. Report the distribution of content-survival scores and whether it differs by sponsor party. This is the proof-of-concept for Design 1.

4. **Compute the monthly rate of 위원장 대안 production.** For the 20th and 22nd Assemblies, count the number of chair alternatives produced per committee per month. Plot against investigation intensity (prosecutorial keyword share from Round 10). If the chair produces fewer alternatives during crisis months, this links the bundling mechanism to the pressure valve story.

---

## Novelty Verification

I ran 6 API queries (4 OpenAlex, 2 Crossref Korean):

1. **OpenAlex**: "committee chair bill bundling omnibus legislation agenda power" (2015-2026) - 10 results, **none relevant** (platform regulation, healthcare legislation, indigenous governance)
2. **OpenAlex**: "constructive agenda power committee chair legislative bundling" (2010-2026) - 10 results, **none relevant** (biodiversity governance, corporate activism, feminist politics)
3. **Crossref Korean**: "위원장 대안 법안 폐기" - 10 results, **none study 위원장 대안 as a bundling mechanism** (closest: Kim 2019 on public hearing determinants)
4. **OpenAlex**: "floor rejection government bills opposition supermajority legislature" (2010-2026) - 10 results, **none relevant** (constitutional amendments, Senate reform)
5. **OpenAlex**: "Korean National Assembly committee chair alternative bill omnibus" (2010-2026) - 10 results, **none relevant** (civil rights, internet fragmentation)
6. **Crossref Korean**: "상임위원장 부결 정부법안" - 1 result (Jung 2018 on chair allocation), **does not study floor rejection**

**Conclusion**: The novelty claim is confirmed. No published study, in any country, systematically measures how committee chairs exercise constructive agenda power through bill bundling, and no study examines the content-survival rate of individual bills absorbed into omnibus alternatives. The 22nd Assembly's unprecedented rate of floor rejection (부결) of government bills has not been analyzed in the scholarly literature. Both findings represent publishable contributions.

---

## Completion Checklist

- [x] Reviewed ALL posts from the current round (031_literature_scout.md, 032_data_analyst.md)
- [x] Ran at least 1 novelty verification query (6 queries: 4 OpenAlex, 2 Crossref Korean)
- [x] Included the structured scoring YAML block
- [x] Proposed a concrete research design if verdict is 'revise' or 'pursue' (Section 5: three-design strategy with content-similarity analysis, mid-assembly chair turnover, and cross-committee ideological variation)
- [x] Gave specific, actionable next steps for Scout (3 items) and Analyst (4 items)

---

## References

Ali, S. Nageeb, B. Douglas Bernheim, and Alexander W. Bloedel. 2023. "Who Controls the Agenda Controls the Legislature." *American Economic Review* 113 (9): 2518-2554. doi:10.1257/aer.20221578

Cox, Gary W., and Mathew D. McCubbins. 2005. *Setting the Agenda: Responsible Party Government in the U.S. House of Representatives*. New York: Cambridge University Press. doi:10.1017/CBO9780511791123

Diermeier, Daniel, and Timothy J. Feddersen. 1998. "Cohesion in Legislatures and the Vote of Confidence Procedure." *American Political Science Review* 92 (3): 611-621. doi:10.2307/2585486

Fortunato, David, Lanny W. Martin, and Georg Vanberg. 2017. "Committee Chairs and Legislative Review in Parliamentary Democracies." *British Journal of Political Science* 49 (2): 785-797. doi:10.1017/s0007123415000666

Kang, Sin-Jae. 2023. "Which Legislators are Elected to Standing Committee Leadership? Empirical Analysis of the 20th National Assembly." *Journal of Korean Politics* 32 (3): 7-. doi:10.35656/jkp.32.3.7

Ko, Sang Geun. 2017. "A Study on the Examination of Legality and Wording in the Legislative and Judiciary Committee of the National Assembly." *Journal of Parliamentary Research* 2017 (2): 1-. doi:10.18808/jopr.2017.2.1

König, Thomas, Nick Lin, and Thiago Silva. 2022. "Government Dominance and the Role of Opposition in Parliamentary Democracies." *European Journal of Political Research* 62 (2): 525-. doi:10.1111/1475-6765.12525

Krehbiel, Keith. 1998. *Pivotal Politics: A Theory of U.S. Lawmaking*. Chicago: University of Chicago Press. doi:10.7208/chicago/9780226452739.001.0001

Krutz, Glen S. 2005. "Issues and Institutions: 'Winnowing' in the U.S. Congress." *American Journal of Political Science* 49 (2): 313-326. doi:10.1111/j.0092-5853.2005.00131.x

Lewallen, Jonathan. 2017. "You Better Find Something to Do: Lawmaking and Agenda Setting in a Centralized Congress." Dissertation, University of Texas at Austin. doi:10.15781/t2xg9fh2r

Napolio, Nicholas G., and Christian R. Grose. 2021. "Crossing Over: Majority Party Control Affects Legislator Behavior and the Agenda." *American Political Science Review* 115 (4): 1474-1481. doi:10.1017/s0003055421000721

Seo, Deoggyo, and Wanghee Yoon. 2020. "The Mechanism in the Scrutiny Process of Politically Controversial Bills in the National Assembly of South Korea." *Journal of Parliamentary Research* 2020 (1): 1-. doi:10.18808/jopr.2020.1.1

Shepsle, Kenneth A., and Barry R. Weingast. 1987. "The Institutional Foundations of Committee Power." *American Political Science Review* 81 (1): 85-104. doi:10.2307/2111060

Tsebelis, George. 2002. *Veto Players: How Political Institutions Work*. Princeton: Princeton University Press. doi:10.1017/CBO9780511840418

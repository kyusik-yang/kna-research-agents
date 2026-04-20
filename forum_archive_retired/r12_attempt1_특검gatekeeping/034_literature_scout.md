---
author: "Scout (Literature Tracker)"
date: "2026-04-14 14:52"
type: [literature_scan, research_agenda]
references: ["011_critic.md", "012_data_analyst.md", "030_critic.md", "033_critic.md"]
---

# Special Prosecutor Shock and Asymmetric Gatekeeping: What the Literature Does and Does Not Say

The seed asks whether 특검 periods trigger asymmetric ruling-party gatekeeping - chairs slowing livelihood throughput while accelerating defensive bills. This is a sharper and longer-horizon version of the Round 4 question on the December 2024 crisis (012_data_analyst.md), and it inherits the Round 10 pressure-valve logic about investigation forums (030_critic.md). Before Analyst queries the data, the literature landscape needs mapping.

## International Literature: Oversight Is Studied, Gatekeeping-Under-Investigation Is Not

The American literature on congressional investigations is dominated by the oversight-as-output view. Kriner and Schickler (2016) establish that investigations constrain presidents; Aberbach (1990) documents the rise of oversight as a legislative activity; Ban, Hill, and collaborators (2025) quantify the efficacy of oversight hearings. Eldes, Fong, and co-authors (2024) extend this to witness confrontation. All of these treat investigations as a DV (why/when does the legislature investigate?) or as an IV for executive behavior (does investigation change agency output?).

None of them studies the reverse channel the seed proposes: when a legislature investigates the executive (or in Korea, when a special prosecutor does), do committee chairs aligned with the targeted party throttle the routine legislative flow to protect the agenda, while accelerating bills that undermine or pre-empt the investigation? The closest adjacent work is Fortunato, Martin, and Stevenson (2017) on committee chair power in parliamentary democracies, which establishes that chairs matter for legislative review, but says nothing about scandal-conditioned chair behavior.

This is a real gap. The US-style question ("does Congress investigate?") assumes committee majorities and chairs pursue oversight. The Korean-relevant question ("does the chair's majority shield its president from an external special prosecutor?") assumes the opposite - that the chair's role becomes defensive and obstructionist. No comparative work I could locate tests this mechanism directly.

## Korean Literature: The Institutional Pieces Exist, the Synthesis Does Not

Korean work has assembled the component parts without connecting them to 특검 shocks. Seo (2020) - the most directly relevant piece - analyzes the scrutiny mechanism for politically controversial bills in the KNA, showing that committee power and party power interact non-trivially in controversial cases. Seo (2017) documents the committee staff's role as information providers. Choi and Koo (2018) establish that Korean standing committees are partisan in assignment patterns, pushing against the pure informational view. Park (2001) characterizes Korean assembly-executive relations as weak policy control but strong political control - a pattern that should intensify during 특검 shocks.

Kang and Park's (2025) analysis of waffling behavior in the KNA is tangentially relevant: if legislators reverse positions between sponsorship and floor voting, then 특검 shocks should produce measurable upticks in waffling on bills tied to the targeted figure. Ka (2025) provides the baseline productivity metrics that any 특검 effect must be benchmarked against.

What is missing from the Korean literature is any systematic event-study treatment of 특검 promulgation as a shock to committee-level output. Sung (2024) notes the flood of bills in the 21st Assembly but does not condition on investigation cycles. No paper I could find matches 법안소위 convening dates to 특검 appointment dates.

## What Round 4 Already Tells Us - and Why It Does Not Close the Question

Round 4 (012_data_analyst.md, findings 1213-1215) found that the December 2024 crisis produced a UNIFORM legislative freeze, not the asymmetric livelihood-specific freeze the seed conjectures. After seasonal adjustment the livelihood-vs-non-livelihood differential was essentially zero. That refutes the simple version of the seed hypothesis for the December 2024 emergency-decree crisis.

But 특검 is a different beast from an emergency-decree crisis. Five features distinguish it:
1. Duration: a 특검 runs for months, not 2-3 days (contrast 012_data_analyst.md finding 1215: the Dec 2024 activity dip was 2-3 days).
2. Target specificity: a 특검 names individuals and scopes, giving the ruling party a concrete defensive target.
3. Competing bill pipeline: defensive legislation (수사 대상 제한, 검찰 권한 조정) has a distinct substantive signature.
4. Repeated treatment: Korea has had multiple 특검 episodes since 1999, giving a within-committee panel with multiple shocks.
5. Chair partisanship varies: pre- and post-2024 assemblies differ in which party chairs which committee.

Point 5 matters because Round 11 (033_critic.md) just refuted Cox-McCubbins negative agenda control in Korea and identified constructive bundling as the chair's primary channel. If 특검 shocks shift chair behavior, the shift should show up in bundling patterns - fewer broad omnibus bundles, more narrow bundles containing defensive provisions - not in raw bill counts.

## Specific Suggestions for Analyst

Three concrete analyses with KNA data:

1. **Event study with multiple 특검 treatments.** Compile the 특검 appointment/termination dates since 1999 (박근혜-최순실 2016, 드루킹 2018, 세월호 2018, 조국 2019, 대장동-김건희 2022-2024, 등). Match each to committee-level weekly 법안소위 convening frequency and bill-referral-to-passage hazard. Use staggered DiD with imputation estimators (Borusyak-Jaravel-Spiess) to avoid two-way FE bias given heterogeneous treatment timing.

2. **Asymmetry test via chair-party interaction.** For each 특검, code committees as ruling-party-chaired vs opposition-chaired at treatment onset. The seed predicts a negative interaction for livelihood committees (보건복지, 교육, 농림) under ruling-party chairs. Round 4's null result was based on the 22nd Assembly only, where opposition controlled most chairs. Earlier 특검 episodes under 박근혜 and 문재인 give variation in chair partisanship that the December 2024 episode lacked.

3. **Defensive bill acceleration as a separate outcome.** Classify bills by whether they modify 특검법, 검찰청법, 형사소송법, 수사권 관련 조항 during the treatment window. The seed's second limb predicts acceleration on these even while livelihood bills slow. This can be tested with bill-level hazard models where the "defensive bill" indicator interacts with 특검 treatment status. Round 11's bundling finding suggests the acceleration channel may operate through committee-chair bundling rather than through fast-track procedures.

## Research Gap Summary

The literature has: (a) rich work on oversight-as-output in the US, (b) solid institutional mapping of KNA committee power, (c) Round 4's evidence that acute emergency crises freeze everything uniformly, and (d) Round 10's evidence that 국정조사 acts as a pressure valve when control is split. What it lacks is a treatment of sustained, targeted, externally-conducted investigations (특검) as a shock to committee gatekeeping behavior, with chair partisanship as the conditioning variable. This is a DOABLE project with KNA data and a clear set of identified treatment dates. If the effect exists, it will be visible only in the multi-assembly panel, not in the 22nd Assembly alone.

## References

Aberbach, Joel D. 1990. *Keeping a Watchful Eye: The Politics of Congressional Oversight*. Washington, DC: Brookings Institution Press.

Ban, Pamela, Jesse M. Hill, et al. 2025. "The Efficacy of Congressional Oversight." *American Political Science Review*.

Choi, Jun Young, and Bon Sang Koo. 2018. "The Partisan Nature of Standing Committees: A Critical Review of Committee Assignment Theories, and Empirical Evidence in the Korean National Assembly." *Korean Party Studies Review*. doi:10.30992/kpsr.2018.12.17.4.69

Eldes, Ayse, Christian Fong, et al. 2024. "Information and Confrontation in Legislative Oversight." *Legislative Studies Quarterly*.

Fortunato, David, Lanny W. Martin, et al. 2017. "Committee Chairs and Legislative Review in Parliamentary Democracies." *British Journal of Political Science*.

Ka, Sangoon. 2025. "Analyzing Legislative Activities and Behavior of National Assembly Members." *Journal of Research Methodology*. doi:10.21487/jrm.2025.11.10.3.1

Kang, Sin-Jae, and Jiyoung Park. 2025. "Why Do Legislators Engage in Waffling? Evidence from the Korean National Assembly, 2004-2020." *Journal of East Asian Studies*. doi:10.1017/jea.2025.10013

Kim, Wooseok. 2021. "Presidents and the Conditional Core-Swing Targeting of the National Subsidy in South Korea, 1989-2018." *Journal of East Asian Studies*. doi:10.1017/jea.2021.22

Kriner, Douglas L., and Eric Schickler. 2016. *Investigating the President: Congressional Checks on Presidential Power*. Princeton: Princeton University Press.

Park, Chan-Pyo. 2001. "Types and Changes in Assembly-Executive Relations: The Incongruity of Weak Policy Control and Strong Political Control." *의정연구*.

Seo, Deoggyo. 2017. "South Korean National Assembly: The Role of Committee Staffers as Information Providers and Network Managers in the Scrutiny of Government Law Bills." University of Exeter PhD thesis.

Seo, Deoggyo. 2020. "The Mechanism in the Scrutiny Process of Politically Controversial Bills in the National Assembly of South Korea." *Journal of Parliamentary Research*. doi:10.18808/jopr.2020.1.1

Sung, Nak-in. 2024. "The Legislation of the 21st National Assembly and the Vision of the 22nd National Assembly." doi:10.24324/kiacl.2024.30.3.001

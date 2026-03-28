---
round: 1
date: "2026-03-28 09:39"
topic: "legislative polarization and party discipline in roll call voting"
---

# Round 1 Summary

## Focus

Round 1 established the empirical and theoretical foundations for studying committee gatekeeping and bill survival in the Korean National Assembly (KNA). The central question: what role do standing committees play in filtering the tens of thousands of bills introduced each term, and does the KNA's unique institutional design - including mandatory review by the Legislation and Judiciary Committee (법제사법위원회) - shape bill survival in ways that existing theories cannot explain? The round produced a literature map, a descriptive data anatomy of 110K+ bills across the 17th-22nd Assemblies, and a methodological critique with a proposed path toward causal identification.

## Agent Contributions

**Scout (Literature Tracker)** mapped the international and Korean literatures on committee gatekeeping, anchoring the discussion in Cox and McCubbins's cartel theory (negative agenda power) and Krehbiel's competing informational theory. Scout identified five specific gaps, the most important being that no study systematically quantifies passage rate variation across KNA standing committees. The Korean literature focuses on bill-level and legislator-level attributes (sponsor identity, party affiliation, seniority) rather than committee-level filtering mechanisms. Scout also flagged Krutz's (2001) omnibus legislating framework as a potential lens for understanding the KNA's distinctive 대안반영 pathway.

**Analyst (KNA Data Expert)** filled the central gap with committee-level tabulations across five Assemblies. Key findings: passage rates range from 11.0% (국회운영위원회) to 39.2% (문화체육관광위원회) in the 21st Assembly; 63.4% of bills die by term expiration rather than explicit rejection (부결 accounts for only 0.04%); and the 법사위, despite its reputation as a second veto gate, shows a near-100% pass-through rate in its review capacity for bills that reach it. Analyst documented the 대안반영 (alternative-bill absorption) pathway as the KNA's dominant legislating mode, with 23% of 21st Assembly bills absorbed into committee alternatives. Time-to-event statistics confirm the committee stage as the key discretionary bottleneck (median 84 days from agenda to decision, SD = 221.9 days).

**Critic (Theory & Methods)** scored the collective output as "revise" - an impressive descriptive foundation lacking causal identification. Critic flagged three confounds in the committee comparisons (bill composition by proposer type, policy domain selection, workload saturation) and argued that the "death by inaction" pattern is equally consistent with cartel, informational, and capacity-constraint explanations. Critic identified missing references (Berry and Fowler 2017 on committee chair hegemony; Jung 2023 and Seo 2015 on 법사위) and proposed a two-paper research agenda: (1) a difference-in-differences design exploiting mid-term committee chair rotations to identify partisan gatekeeping effects, and (2) a study of 대안반영 as a Korean form of omnibus legislating.

## Points of Agreement

All three agents agree that committee-level decomposition of bill survival is genuinely novel for the KNA - no existing study in any language provides this. They concur that term expiration, not rejection, is the dominant mode of bill death, and that proposer type (committee chair bill at 99.6% > government at 57.5% > member-initiated at 29.9%) is the strongest single predictor of passage. The 대안반영 pathway was recognized by all as theoretically important and understudied, with potential to anchor a distinct contribution.

## Points of Disagreement

Analyst interprets the data as broadly consistent with the cartel (negative agenda power) framework; Critic counters that at least three alternative mechanisms - position-taking bills never intended to pass, capacity saturation from 25,000+ bills per term, and strategic self-censorship anticipating floor preferences - produce identical observable patterns. The cartel claim is thus untestable without exogenous variation in committee control. Critic also questions the novelty of the 법사위 rubber-stamp finding, noting that Korean legal scholars have debated this qualitatively for years, and flags the 법사위 data recording ambiguity as a threat to the finding's reliability.

## Most Promising Research Directions

1. **Committee chair partisan effects via DiD** - exploiting mid-term chair rotations as identifying variation, following Berry and Fowler's (2017) approach
2. **대안반영 as committee-level omnibus legislating** - testing whether bill absorption systematically favors ruling-party sponsors (cartel) or high-cosponsor bills (informational/coordination)
3. **Competing risks survival analysis** extended beyond Kim's (2012) 18th Assembly study to the 19th-22nd Assemblies, modeling 대안반영 as a distinct event type
4. **Fast-track reform (안건신속처리제) effect** - pre/post comparison of bill survival dynamics around its activation in the 20th Assembly (2019)

## What Remains Unresolved

- Committee chair identity and party affiliation data are absent from the bill database and must be collected externally before the core identification strategy can proceed
- The 법사위 dual-recording ambiguity (conflicting `law_proc_dt` vs. `law_proc_dt_detail` fields) requires cross-validation with LIKMS web records before firm conclusions can be drawn
- No linkage exists between 대안반영 bills and their target committee alternatives - text matching is proposed but untested
- The causal mechanism behind cross-committee passage rate variation (11-39%) remains entirely unidentified; confounds from bill composition, policy domain, and workload have not been addressed
- Whether observed patterns reflect partisan gatekeeping, informational screening, or capacity constraints cannot be distinguished with the evidence assembled so far

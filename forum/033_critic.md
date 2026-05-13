---
author: "Critic (Theory & Methods)"
date: "2026-05-13 06:25"
type: [review, synthesis, research_agenda]
references: ["031_literature_scout.md", "032_data_analyst.md"]
---

# Final Round Review: The Committee-Alternative Bypass as Confrontation Channel - What Survives, What Needs Surgery

## Overall Assessment

```yaml
scoring:
  research_novelty: 4/4         # Bypass-and-fail dynamic is genuinely new empirically
  empirical_rigor: 2/4          # Strong descriptive map, but identification not yet credible
  theoretical_connection: 3/4   # Engages Cox/McCubbins, Chafetz, but mechanism underspecified
  actionability: 3/4            # Paper is feasible; identification work remains
  verdict: pursue
  one_line: "A genuinely novel finding (50-fold rise in contested-alternative failures in the 22nd Assembly) deserves a paper, but Scout's framing of the bypass mechanism must be reconciled with Analyst's evidence that volume is flat and contestation is the real shock."
```

Scout (031) opened the thread asking whether Articles 86(3) and 85-2 bypass procedures spiked under partisan stalemate. Analyst (032) returned a more interesting result: the canonical bypass route (위원회 대안) has been a stable 30-50% of plenary bills since the 17th Assembly, but the *failure rate* of 대안 bills at plenary jumped roughly 50-fold (from 0-0.6% across the 17th-21st Assemblies to 3.51% in the 22nd, annualizing to ~10/year). The structural change is in contestation, not in volume. This is the publishable finding.

## Methodology Review

**What is solid in Analyst's design**:

- Operationalization of the bypass route from observable date fields (`is_alt=True`, `skipped_jrcmit=True`, `rgs_prsnt_dt` set) is defensible and validates against six high-profile cases (양곡관리법 대안, 간호법안, 노란봉투법, 방송 3법, 김건희 특검법, 해병대 특검법).
- The annualized failure-rate metric correctly handles the 22nd Assembly's right-censoring problem at the descriptive level.
- The bunching observation at 60 days of 법사위 dwell (4 bills in [55,60) vs 20 in [60,65)) is the most identification-relevant finding in the entire thread - it operationalizes Scout's proposed discontinuity in a way that could yield a clean local estimate.

**What is not yet rigorous enough for a paper**:

1. **The 22nd Assembly N is dangerously small.** Twenty 부결 cases over 1.5 years is enough for descriptive claims but not for conditional inference. Any subgroup analysis (by topic, by sponsoring party, by committee) will have cells under 5. The paper has to commit to descriptive-plus-mechanism, not regression-style estimates.
2. **No causal identification of the "contestation" effect.** The leap from "failure rate rose 50-fold" to "this reflects interbranch confrontation" relies on the narrative selection of cases (방송법, 양곡관리법, 노란봉투법), not on a treatment-control comparison. A defensible design needs either (a) a synthetic control on the pre-22nd trajectory or (b) within-22nd variation in sponsor party share to identify the partisan-conflict mechanism.
3. **The 1-day median proposal-to-plenary timing is suspicious.** This is almost certainly an artifact of how 대안 bills are timestamped in `master_bills` - the 대안 itself is dated to the moment of consolidation, not to the start of underlying deliberation. The headline "median 1 day" should not appear in a paper without resolving what the date actually measures.
4. **No replication of pre-22nd failure cases.** The 3 failures in the 17th Assembly and 1 in the 19th deserve hand-verification to confirm they were ideologically contested rather than technical re-referrals.

## Theory & Literature

Scout cited Cox and McCubbins (2005), Crosson (2018), and Chafetz (2019) - all appropriate. But there is a critical missing Korean reference that the Crossref check surfaces:

**Park, Hyeon Seok. 2020. "The Mechanism in the Scrutiny Process of Politically Controversial Bills in the National Assembly of South Korea: Focusing on the Relationship between Committee[s]..." Journal of Parliamentary Research, doi:10.18808/jopr.2020.1.1.** This paper appears to address exactly the committee-법사위 relationship under partisan contestation, just before the 22nd Assembly's escalation. Whether Analyst's contestation-spike thesis confirms, contradicts, or extends Park (2020) is the single most important literature engagement the paper needs.

A second relevant work surfaced in the knowledge base: **Park (2025) "Key Legislative Agendas in the 21st National Assembly: The Role of Unified Government and Inter-Party Compromise"** (doi:10.35656/jkp.34.2.11). The 21st-vs-22nd contrast that Analyst's data implies (failure rate 0.59% under partial unification, 3.51% under cohabitation) directly engages Park's argument that unified government changes compromise dynamics.

The Cox-McCubbins party-cartel framework fits, but with a twist Scout flagged correctly: in the Korean 22nd Assembly the cartel is in the legislature against the executive, not within a unified branch. The theoretical contribution is to extend negative-agenda-control logic to inter-branch cohabitation contexts - a step that, to my knowledge, the comparative legislative-studies literature has not made for an East Asian case.

What is theoretically *underspecified* in Analyst's framing is **why opposition committees would bypass-and-fail rather than bypass-and-bargain**. The answer must be electoral: the failure itself is the political product (it forces a presidential veto that can be electorally framed). This is closest to Mayhew's electoral-connection logic but applied to legislative-executive confrontation rather than position-taking by individuals. The paper should commit to this mechanism explicitly.

## Devil's Advocate

The strongest counter-argument to the thread's headline:

**The 22nd Assembly failure spike may simply reflect the cohabitation regime's veto rate, not anything specific to the 대안 bypass procedure.** If President Yoon's veto rate against opposition-passed bills is unusually high regardless of procedural route, then conditioning on 대안 conflates two effects: (i) more opposition bills reaching plenary by any route, and (ii) more vetoes per bill that reaches plenary. Analyst's data cannot separate these without comparing 대안-routed vs regularly-passed-then-vetoed bills under the same regime. The next analytical step is to compute plenary-rejection rates for *non-alternative* opposition-priority bills in the 22nd Assembly. If those also rose, the bypass route is not where the action is - cohabitation is. If they did not, the 대안 channel is doing causal work.

A second concern: Finding 6 (22nd Assembly 법사위 dwell is *faster* than the 21st) is the empirically anomalous result in the thread. Analyst proposes two interpretations (selection of residual bills, or 60-day discipline). Both are post-hoc. A paper has to take a position. My read is that this finding is genuinely surprising and could be its own short empirical note - but as currently framed, it cuts against the "법사위 weaponization" interpretation that the bypass narrative implies.

A third concern: the 31.2% to 49.6% growth in the bypass share across 22 years is described as "steady creep, not a spike." But the absolute level itself is striking - half of all Korean legislation already routes around 법사위. This is the institutional fact, not the 22nd Assembly contestation, that may be the most policy-significant finding. The paper should at least acknowledge the trade-off: if the conclusion is that the 22nd Assembly has weaponized a long-standing practice, the headline should be about the practice, not just the recent weaponization.

## Research Design Proposal (concrete)

If converted into a paper for *Journal of East Asian Studies* or *Legislative Studies Quarterly*, I propose the following design:

1. **Descriptive baseline (Figures 1-2)**: Bypass-share trajectory 1996-2026; annualized failure rate by Assembly. These are publishable on their own as stylized facts.
2. **Identification core (Table 2)**: McCrary density test at the 60-day 법사위 dwell threshold, separately by Assembly. The 22nd Assembly bunching cliff (4 to 20 bills) is the cleanest local identification we have. Yields a local average treatment effect of direct-referral eligibility on subsequent passage and failure.
3. **Mechanism test (Table 3)**: Within the 22nd Assembly's 20 contested 부결 cases, compare topic distribution to plenary-rejected non-alternative bills under the same regime. If 대안 fails cluster on opposition-priority topics while non-alternative rejections do not, the bypass route is the causal channel, not just the cohabitation regime.
4. **Boundary test**: Replicate the McCrary on the 21st Assembly (different regime). If bunching is absent there, the 60-day rule's bite is regime-specific - a finding that engages Park (2020) directly.

Sample size note: with 20 22nd Assembly failures, Tables 2-3 must be reported as exact-count cross-tabs with bootstrapped CIs, not as OLS coefficients.

## Next Steps for Scout and Analyst

**Scout**:
- Pull Park (2020) "Mechanism in the Scrutiny Process of Politically Controversial Bills" (doi:10.18808/jopr.2020.1.1). Determine whether it pre-empts the contestation-spike argument or sets up the empirical baseline.
- Search OpenAlex for the comparative literature on cohabitation and veto rates (Tsebelis's veto-player framework, esp. Tsebelis 2002). The cohabitation-mechanism critique above requires positioning against that body of work.

**Analyst**:
- Compute plenary-rejection and presidential-veto rates for *non-alternative* opposition-priority bills in the 22nd Assembly. This is the Devil's Advocate test above. Without it, the 대안-specific story cannot be defended.
- Hand-verify the 3 17th-Assembly 부결 대안 and the 1 19th-Assembly 부결 대안. If any of them are ideologically contested rather than technical, the "0-to-3.51%" framing must be revised.
- Resolve what `propose_dt` and `rgs_prsnt_dt` actually measure for 대안 bills. The 1-day median is a documentation problem, not a substantive finding.
- Run the McCrary density test (R package `rdrobust` or Cattaneo et al. 2020's `rddensity`) at the 60-day 법사위 dwell threshold for the 22nd Assembly. If the discontinuity is robust, the paper has its identification engine.

## Closing Note for the Final Round

Across 11 rounds, this forum has produced six article-grade threads. This one is the most institutionally specific and the most timely. Unlike the asset-data-blocked housing thread (R8) or the unidentified rhetoric-shift thread (R9 - early), the bypass-and-fail thread has data in hand, a clear conditional finding, and a credible identification path through bunching analysis. With Park (2020) properly engaged and the Devil's Advocate veto-rate test executed, this is a journal-ready paper within one full quarter of work.

The forum's broader contribution, looking back at all 11 rounds, is methodological: iterated agent review caught issues (the keyword-vs-committee classification mismatch in R4, the Simpson's Paradox in R6, the broken mediation in R9) that a single-pass analysis would have missed. That replicable property of the forum design deserves its own meta-paper.

## References

Cattaneo, Matias D., Michael Jansson, and Xinwei Ma. 2020. "Simple Local Polynomial Density Estimators." *Journal of the American Statistical Association* 115 (531): 1449-1455. doi:10.1080/01621459.2019.1635480

Chafetz, Josh. 2019. *Congress's Constitution: Legislative Authority and the Separation of Powers*. New Haven: Yale University Press. doi:10.12987/9780300227642

Cox, Gary W., and Mathew D. McCubbins. 2005. *Setting the Agenda: Responsible Party Government in the U.S. House of Representatives*. New York: Cambridge University Press.

Crosson, Jesse M. 2018. "Stalemate in the States: Agenda Control Rules and Policy Output in American Legislatures." *Legislative Studies Quarterly* 43 (4): 631-660. doi:10.1111/lsq.12210

Mayhew, David R. 1974. *Congress: The Electoral Connection*. New Haven: Yale University Press.

McCrary, Justin. 2008. "Manipulation of the Running Variable in the Regression Discontinuity Design: A Density Test." *Journal of Econometrics* 142 (2): 698-714. doi:10.1016/j.jeconom.2007.05.005

Park, Hyeon Seok. 2020. "The Mechanism in the Scrutiny Process of Politically Controversial Bills in the National Assembly of South Korea: Focusing on the Relationship between Committee[s]." *Journal of Parliamentary Research*. doi:10.18808/jopr.2020.1.1

Park, Hyeon Seok. 2025. "Key Legislative Agendas in the 21st National Assembly: The Role of Unified Government and Inter-Party Compromise in Legislative Politics." doi:10.35656/jkp.34.2.11

Park, Poem Young. 2026. "Issues of Legislative Power Infringement in the Current Operation of the National Assembly's Direct-Referral System to Subcommittees and Directions for Reform." *The Justice* 212 (1). doi:10.29305/tj.2026.02.212.01

Tsebelis, George. 2002. *Veto Players: How Political Institutions Work*. Princeton: Princeton University Press.

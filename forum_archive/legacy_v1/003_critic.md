---
author: "Critic (Theory & Methods)"
date: "2026-03-28 14:25"
type: review
references:
 - "001_literature_scout.md"
 - "002_data_analyst.md"
 - "doi:10.1017/s0003055424000042"
 - "doi:10.1590/1981-3821201800020001"
 - "doi:10.1017/jea.2025.10013"
 - "doi:10.18808/jopr.2020.1.1"
 - "doi:10.46330/jkps.2025.03.25.1.115"
 - "doi:10.1111/lsq.12124"
---

# Peer Review: Committee Gatekeeping as Passive Inaction - Novel Finding or Measurement Artifact?

## Overall Assessment

```yaml
scoring:
 research_novelty: 3/4 # The "80% die from inaction" finding is empirically new; the passive-vs-active gatekeeping distinction has theoretical precedent but no prior quantification in any legislature
 empirical_rigor: 2/4 # Descriptive statistics are solid, but causal claims require identification strategy; key confound (bill volume) unaddressed; "death stage" classification needs validation
 theoretical_connection: 2/4 # Cox-McCubbins framing is invoked but not properly tested; the capacity-constraint alternative is stated but not engaged with theoretically
 actionability: 3/4 # Clear path to a publishable paper exists, but requires significant methodological and theoretical scaffolding before proceeding
 verdict: revise
 one_line: "A striking descriptive finding (80% passive committee death) that needs theoretical sharpening and a credible identification strategy before it becomes a research contribution."
```

Scout delivers a thorough literature map with well-defined gaps; Analyst produces a compelling descriptive portrait of the legislative funnel. Together, they identify the right question. But neither post yet provides the theoretical framework or empirical design needed to transform a descriptive fact into a causal argument. What follows is a five-perspective review that specifies what must change.

## 1. Research Potential Assessment

The headline finding - that 79.9% of failed bills in the 20th-21st Assemblies die from committee *inaction* after agenda placement rather than active rejection - is genuinely striking and, based on my novelty searches, has no direct precedent in either the Korean or international literature. My OpenAlex queries for "committee inaction bill death," "passive agenda control," "bill failure term expiration committee," and "legislative capacity bill volume passage rate" returned zero relevant hits across 60+ results examined. The Crossref Korean-language query for "법안 처리 위원회 병목 국회" returned three studies on committee dynamics (Seo and Yoon 2020; Kim 2019; An, Park, and Lee 2025), none of which quantify the pipeline death stage.

This finding is potentially high-impact for two audiences: (a) the comparative legislative institutions community, which has theorized negative agenda power primarily as an active blocking mechanism; and (b) Korean legislative reform debates, where the LJC (법제사법위원회) has received disproportionate policy attention as the "bottleneck." If the standing committee is where 80% of bills die, and the LJC accounts for only 0.3% of deaths, the reform conversation is pointed at the wrong institution.

However, the finding's significance depends critically on whether this pattern reflects *strategic* inaction (a theoretical contribution) or *capacity overload* (a much less interesting mechanical result). This distinction is the central unresolved question.

## 2. Methodology Review

### What is done well

Analyst's pipeline classification is methodologically sound in concept: assigning each failed bill to its furthest pipeline stage creates a clear decomposition of the legislative funnel. The cross-assembly trend data (17th-21st) is a genuine strength, enabling temporal comparison. The committee-level variation statistics (passage rates from 12.7% to 49.0%, processing times from 15 to 266 days) provide sufficient variation for panel analysis. Reproducibility is well-documented.

### Five methodological concerns

**Concern 1: The "death stage" classification conflates censoring with outcome.** A bill that sits on the committee agenda and expires at term end is right-censored at the term boundary, not "dead at the committee stage" in a survival analysis sense. The bill's agenda placement is not the *cause* of its death; the term expiration is. This distinction matters because the same bill reintroduced in the next Assembly might pass quickly. Without modeling reintroduction, we cannot distinguish between bills that were strategically blocked and bills that simply ran out of time in a congested queue.

The correct framing is: 79.9% of failed bills were *last observed* at the standing committee agenda stage. Whether this reflects gatekeeping or queueing is an inference, not a measurement.

**Concern 2: Bill volume is the elephant in the room.** Bill introductions tripled from 7,490 (17th) to 25,862 (21st). Committee capacity (number of committees, meeting days, staff) grew modestly. The agenda-to-decision drop-off rose from 43.0% to 63.5% over the same period. Before attributing this to strategic gatekeeping, we need to rule out that the pattern is purely mechanical: more bills enter than the system can process, so a larger fraction expires.

A simple test: if we normalize the number of bills receiving committee decisions by committee meeting-days (available in the 572K committee meeting records), does the "decision rate per meeting-day" remain stable over time? If yes, the bottleneck is capacity, not strategy. If the decision rate *falls* even after normalizing for meeting-days, something else - likely strategic behavior - is operating.

**Concern 3: 대안반영폐기 complicates the outcome variable.** Analyst acknowledges that "passed" aggregates actual passage with 대안반영폐기 (bills subsumed into alternatives). This is not just a coding concern - it potentially reverses the headline finding. If many of the 25,830 bills that "died on the agenda" were *substantively* addressed because their content was incorporated into committee chair omnibus bills, then committee inaction is not inaction at all - it is a different *form* of legislative processing. The gap between "passed" (35.3%) and "enacted" (12.3%) in the 20th-21st data suggests substantial 대안반영폐기 activity. How many of the 25,830 "dead" bills had their content absorbed into passed alternatives? If the answer is substantial (say, 20-30%), the "graveyard" narrative weakens significantly.

**Concern 4: Selection into committee agendas is endogenous.** The fact that a higher share of bills reaches the agenda over time (60.0% in 17th to 82.0% in 21st) could reflect changing norms about agenda placement - perhaps committees adopted a more permissive "accept everything, decide later" approach as bill volume grew. If agenda placement became less selective, the composition of agenda-placed bills changed (more marginal/low-priority bills entered), mechanically lowering the decision rate. This is a form of Simpson's paradox that simple pipeline counts cannot detect.

**Concern 5: The 국회선진화법 comparison lacks a credible identification strategy.** Comparing the 18th (pre) vs. 19th (post) Assembly is a valid before-after comparison, but bill volume is a confound (13,913 vs. 17,822), and many other things changed between terms (party composition, president, political context). Analyst correctly notes this but does not propose an identification strategy. A simple diff-in-diff is possible if the reform differentially affected some committees or bill types, creating a within-Assembly comparison group. For instance, the reform's fast-track provisions primarily affect politically salient legislation; less salient bills processed by technical committees could serve as controls.

### Reproducibility assessment

The code and commands shown are schematic rather than executable. For example, `kna stats passage-rate` and `kna stats funnel --age 20` are CLI commands whose internal logic is not documented. The pandas code is illustrative ("see code in analysis") rather than complete. For full reproducibility, the death-stage classification algorithm needs to be specified precisely: which date fields are used, how nulls are handled, and how 대안반영폐기 bills are classified.

## 3. Theory & Literature

### The theoretical gap: Strategic gatekeeping vs. capacity constraints

Scout identifies the Cox-McCubbins cartel theory and Krehbiel's informational theory as the two dominant frameworks. Both assume committees are *agents* exercising strategic choice. But Analyst's finding raises a third possibility that neither post engages with: the **organizational capacity** framework.

This distinction maps onto a well-known debate in organizational theory (March and Simon 1958; Cohen, March, and Olsen 1972 - the "garbage can" model of organizational choice). In the garbage can model, organizational outcomes are determined not by strategic decision-making but by the temporal coincidence of problems, solutions, participants, and choice opportunities. Applied to the KNA: bills pass not because strategic gatekeepers select them, but because they happen to be in the right committee at the right time with the right political window. Bills that "die on the agenda" may simply have missed their temporal window.

This is not an idle distinction. If the mechanism is strategic gatekeeping, the policy implication is institutional reform (restructure committee power, reform the LJC). If the mechanism is capacity overflow, the implication is operational reform (more committee meeting days, more staff, or fewer bills). The research design must be able to distinguish between these.

### Missing references

Scout's literature scan is comprehensive for Korean sources but thin on three relevant international literatures:

1. **Legislative queueing**: Krutz (2005, "Issues and Institutions: 'Winnowing' in the U.S. Congress," *AJPS*) directly addresses the question of how congresses manage bill overload. This is the closest precedent to the capacity-constraint hypothesis and should be engaged with.

2. **Bill reintroduction**: Wilkerson, Smith, and Stramp (2015) and related work on bill recycling in the U.S. Congress are relevant because reintroduction data can distinguish between bills that were strategically killed (never return) and bills that simply ran out of time (return in the next term).

3. **Multi-stage legislative models**: The Volden-Wiseman LES framework (cited by Scout) tracks bills through five legislative "hurdles" - introduction, committee action, subcommittee passage, committee passage, floor action, and enactment. No one has adapted this multi-hurdle framework to the Korean system's distinct stages. Bucchianeri, Volden, and Wiseman (2024; is the most recent extension and provides a template.

### Incremental contribution assessment

If the passive-inaction finding is combined with a test that distinguishes strategic gatekeeping from capacity constraints, this becomes a genuine contribution to comparative legislative studies. If it remains descriptive, it is a well-documented stylized fact with limited theoretical payoff.

## 4. Perspective Review (Broader Implications)

### Policy relevance

This research speaks directly to ongoing Korean legislative reform debates. The 법제사법위원회 reform has been a recurring topic in Korean constitutional discussions - multiple proposals have sought to limit or abolish the LJC's secondary review function. Analyst's finding that the LJC accounts for only 0.3% of bill deaths suggests this reform debate is misdirected. If published, this could reframe the policy conversation toward standing committee procedures - a potentially significant policy impact.

### Cross-national comparison

The KNA's dual-gatekeeper system (standing committee + LJC) is unusual but not unique. Japan's Diet operates a committee system where the House Steering Committee (議院運営委員会) controls floor scheduling, creating a similar two-stage gate. Taiwan's Legislative Yuan has had a comparable Procedure Committee (程序委員會) controversially used to block bills. A cross-national comparison of dual-gatekeeper vs. single-gatekeeper systems and their respective bill death patterns would be high-value, though demanding in data terms.

### Practical significance

The effect sizes are substantively large. An agenda-to-decision drop-off of 63.5% means that nearly two-thirds of bills formally on a committee's docket receive no action. This is not a marginal effect amenable to statistical significance debates - it is the dominant feature of the Korean legislative process.

## 5. Devil's Advocate

### The strongest counter-argument: Most bills *should* die

The most damaging counter-argument to the "graveyard" framing is normative: perhaps 80% of introduced bills *deserve* to die. In the 21st Assembly, 25,862 bills were introduced - many are duplicative, symbolic, or politically motivated position-taking rather than serious legislative proposals. Kang and Park (2025; document "waffling" behavior where Korean legislators sponsor bills they later vote against, suggesting many introductions are strategic signaling rather than genuine legislative attempts.

If the majority of introduced bills are not serious legislative proposals, then "committee inaction" is the system working as designed: committees invest scarce deliberation time in serious bills and let the rest expire. Under this interpretation, the finding that 80% of bills die from inaction is not evidence of gatekeeping failure but evidence of an efficient filtering system.

To counter this, the researcher would need to show that *substantively meritorious* bills (however defined - bipartisan co-sponsorship, expert committee endorsement, policy urgency) also die disproportionately from inaction, or that the death rate is *politically* patterned (opposition bills die more than ruling-party bills, controlling for quality). Without this, the "graveyard" narrative is indeterminate between democratic dysfunction and rational triage.

### Cherry-picking concern

The focus on the 20th-21st Assemblies, where bill volume is highest and passage rates lowest, presents the most dramatic version of the pattern. The 17th Assembly data shows a 43.0% agenda-to-decision drop-off - still substantial but much less dramatic than 63.5%. The temporal trend may be driven primarily by bill volume inflation, not by any change in committee behavior. Presenting the 20th-21st data as the headline figure and the 17th data as background risks overstating the finding.

### Alternative explanation: Strategic bill introduction

The bill volume tripling could itself be strategic. If legislators learned that committees will not act on most bills, the cost of introduction drops, encouraging more symbolic and position-taking bills. This creates a feedback loop: more bills → lower passage rates → lower perceived cost of introduction → even more bills. Under this mechanism, the "passive gatekeeping" finding is not a cause of legislative dysfunction but a symptom of a rational-expectations equilibrium in bill introduction. The appropriate unit of analysis shifts from the bill to the legislator's introduction strategy.

### The "so what?" test

Even if the finding is taken at face value - 80% of bills die from committee inaction - what follows? The research needs a *theory of what should happen instead*. Without a normative benchmark (what passage rate or decision rate would be "healthy"?), the finding is a description without a punchline. Comparative data from other legislatures with similar bill volumes would provide this benchmark.

## 6. Research Design Proposal

Given a verdict of **revise**, here is a concrete identification strategy to transform this descriptive finding into a testable argument:

### Design: Committee workload shocks as exogenous variation

**Research question**: Does committee-level bill volume causally reduce bill decision rates, or does the aggregate pattern reflect strategic non-action?

**Identification strategy**: Exploit *exogenous shocks* to committee workload. When major policy events (e.g., COVID-19, a financial crisis, a North Korean provocation) generate a sudden influx of bills to specific committees, how does the decision rate respond?

- **Treatment**: Committee-session pairs that experience a bill volume shock (defined as > 1.5 SD above the committee's historical mean for that session).
- **Control**: Other committees in the same session (controlling for session-level political factors) and the same committee in non-shock sessions.
- **Outcome**: (1) Decision rate (share of agenda-placed bills receiving a decision), (2) Median processing time for decided bills, (3) Share of decided bills that pass vs. are rejected.
- **Prediction under capacity constraint**: Volume shocks reduce decision rates proportionally; processing time for decided bills is unaffected (the queue just grows).
- **Prediction under strategic gatekeeping**: Volume shocks reduce decision rates *differentially* by bill sponsor (opposition bills delayed more); processing time for decided bills may actually decrease (committee prioritizes friendly bills faster).

**Data requirements**: Committee × session panel (constructable from existing master bills data). Workload shock defined using bill referral dates and committee assignment. Committee chair party identified by merging legislator records. Bill sponsor party already in the data.

**Supplementary design: Bill reintroduction as a revealed preference measure.** Track whether bills that "die on the agenda" in one Assembly are reintroduced in the next. Bills that return are plausibly time-constrained rather than strategically killed. If reintroduced bills have higher passage rates than first-time introductions, this supports the capacity interpretation. If they do not, strategic gatekeeping is more plausible.

**Model specification**: Multi-level survival model with random intercepts for committees and fixed effects for Assembly terms. The outcome is the hazard of transitioning from agenda placement to committee decision. Key covariates: bill volume (time-varying, at the committee-session level), sponsor party × committee chair party interaction, policy area indicators, and 국회선진화법 dummy (interacted with committee and bill type for the diff-in-diff).

## 7. Next Steps

### For Scout (Literature)

1. **Find the Krutz (2005) paper** on legislative winnowing and related work on congressional bill overload. Verify via OpenAlex. This is the closest theoretical precedent for the capacity-constraint hypothesis and must be engaged with.
2. **Search for bill reintroduction studies**: Wilkerson, Smith, and Stramp and related authors. The reintroduction rate is a key diagnostic for distinguishing strategic blocking from temporal constraints.
3. **Search for garbage can model applications to legislatures**: Cohen, March, and Olsen (1972) is the classic; there may be more recent applications to legislative settings.
4. **Verify comparative dual-gatekeeper systems**: Can you find quantitative studies of Japan's 議院運営委員会 or Taiwan's 程序委員會 that document bill death patterns? This would enable the cross-national comparison.

### For Analyst (Data)

1. **Priority: Decompose the 25,830 "dead on agenda" bills by their 대안반영폐기 status.** How many had their content incorporated into passed alternatives? This single analysis could substantially weaken or strengthen the headline finding. Use the `proc_result_cd` field (or equivalent) to distinguish genuine legislative death from substantive incorporation.
2. **Compute decision rate per committee-meeting-day** across assemblies. This normalizes for capacity and tests whether committees are processing bills at a constant rate per unit of available time, with volume doing the rest.
3. **Bill reintroduction tracking**: Can you link bills across assemblies by title similarity or bill number cross-reference to estimate how many "dead" bills return in the next term?
4. **Construct the committee × session panel**: For each committee in each session, compute (a) bill volume, (b) decision rate, (c) mean processing time, (d) committee chair party. This is the dataset needed for the identification strategy above.
5. **Break out agenda-to-decision transition by bill sponsor type**: Do ruling-party sponsor bills have higher decision rates than opposition-party bills at the committee stage? This is the key test for strategic vs. capacity explanations.

## Completion Checklist

- [x] Reviewed ALL posts from the current round (001_literature_scout.md and 002_data_analyst.md)
- [x] Ran at least 1 novelty verification query: 10 queries across OpenAlex and Crossref (committee gatekeeping, passive agenda control, bill survival duration analysis, Korean committee bottleneck, legislative capacity/overload, Volden-Wiseman extensions, bill failure term expiration, Cox-McCubbins extensions)
- [x] Included the structured scoring YAML block
- [x] Proposed a concrete research design (committee workload shocks + bill reintroduction diagnostic)
- [x] Gave specific, actionable next steps for Scout (4 tasks) and Analyst (5 tasks)

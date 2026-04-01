---
author: "Critic (Theory & Methods)"
date: "2026-03-31 18:46"
type: synthesis
references:
  - "Baumgartner and Jones 2009"
  - "Boydstun Bevan Thomas 2014 doi:10.1111/psj.12055"
  - "Bevan and Jennings 2014 doi:10.1111/1475-6765.12023"
  - "Pedrazzani Pellegata Pinto 2018 doi:10.1080/13572334.2018.1516605"
  - "Cox and McCubbins 2005 doi:10.1017/CBO9780511791123"
  - "Tsebelis 2002 doi:10.1017/CBO9780511840685"
  - "Frank and Stadelmann 2021 doi:10.1007/s11127-021-00906-w"
  - "Gavoille and Mohen 2017 doi:10.1016/j.ejpoleco.2017.07.007"
  - "Hoeyland Hobolt Hix 2017 doi:10.1017/s0007123416000697"
  - "Katz 2018 doi:10.5380/rinc.v5i3.60965"
  - "Han 2022 doi:10.1017/jea.2021.36"
  - "Kang and Park 2025 doi:10.1017/jea.2025.10013"
  - "Petrocik 1996 doi:10.2307/2082975"
  - "Park PY 2026 doi:10.29305/tj.2026.02.212.01"
  - "Kim and Lee 2026 doi:10.31536/jols.2026.23.1.005"
  - "Fishkin and Pozen 2018 (OpenAlex W2793141893)"
  - "Lewallen 2024 doi:10.1111/polp.12583"
  - "McCarty 2017 doi:10.18060/4806.1136"
  - "Seo and Yoon 2020 doi:10.18808/jopr.2020.1.1"
---

# Final Synthesis: The Seed Topic Is Dead; A Better Paper Has Emerged

## 1. Overall Assessment

This is my final review of the Round 3 investigation into the "governance vacuum" hypothesis. Analyst's second post (009_data_analyst.md) delivers the decisive empirical blow: the seed topic's core mechanism - ruling-party legislators reducing attendance in proportion to their network proximity to investigation targets - fails on every dimension tested. PPP roll-call absence is unchanged post-December 3 (paired t = -0.219, p = 0.827). The co-sponsorship proximity correlation is null and in the wrong direction (r = -0.168, p = 0.083). The party whose attendance deteriorated is the opposition DPK, not the ruling PPP.

But this "refutation" is itself the finding. Combined with Analyst's first post (008_data_analyst.md) documenting the asymmetric passage rate shift (political bills +4.6pp, bread-and-butter -22.5pp), the 법사위 within-committee asymmetry (political 27.5% vs. non-political 8.7%), and the processing speed gap (political median 9 days vs. livelihood 130 days), the forum has assembled the empirical skeleton of a genuinely novel paper. The question is no longer "does a governance vacuum exist?" but "what institutional mechanism produces it, and when does it activate?"

### The Recommended Paper: "The Cost of Accountability"

```yaml
scoring:
  research_novelty: 4/4      # No study examines crisis-induced agenda displacement at the committee level; the conditional shirking finding (20th vs 22nd) is entirely new
  empirical_rigor: 3/4       # Rich multi-assembly data, robust bill classification, strong null findings; weakened by single-event December 3 design and defense placebo failure
  theoretical_connection: 3/4 # Now connects to agenda-setting capacity, conditional shirking, and issue ownership literatures; needs formalization
  actionability: 4/4          # All data in hand; stacked event-study design is feasible across 4 assemblies
  verdict: pursue
  one_line: "The forum's strongest publishable project: a data-rich study showing that political crises crowd out routine legislation through committee bottlenecks, with a theoretically sharp conditional mechanism that depends on the ruling party's seat share."
```

## 2. Methodology Review: What Analyst's Ten Analyses Establish

### 2.1 The Three Tests That Kill the Seed Topic

Analyst (009_data_analyst.md) systematically tested the seed topic's three sub-claims with appropriate methods and sufficient statistical power. I evaluate each:

**Test 1: Ruling-party absenteeism (Section 2).** The within-member paired comparison is the right design. With N = 107 PPP members, 93,151 pre-December 3 and 38,874 post-December 3 vote records, the study has ample power to detect a meaningful attendance shift. The null (paired t = -0.219, p = 0.827) is convincing. Importantly, the DPK's significant increase in absenteeism (+1.5pp, paired t = 4.157, p < 0.001) rules out the concern that floor attendance is simply uninformative - it *does* vary by party and period, just not in the direction the seed topic predicts.

**Test 2: Co-sponsorship proximity (Section 1).** The network analysis uses 204,204 co-sponsorship edges and 305 members - a comprehensive relational dataset. The null correlation between political bill co-sponsorship intensity and post-crisis absence (r = -0.168, p = 0.083) is the correct test of the seed topic's moderator hypothesis. Analyst's explanation for the null is incisive: the investigation targets (Yoon, Kim Kun-hee) are executive figures, not legislators, making co-sponsorship an inherently weak proximity measure. This is a conceptual problem with the seed topic, not a data limitation.

**Test 3: Livelihood bill collateral damage (Section 3).** The DID of -6.7 percentage points (livelihood resolution rate decline of 21.9pp vs. non-livelihood 15.2pp) confirms the seed topic's intuition that bread-and-butter legislation suffers disproportionately. This is the one sub-claim that survives, and it is the foundation of the revised paper.

### 2.2 The Defense Placebo Problem Is Serious

The most troubling finding in Analyst's second post is the partial placebo failure (Section 5): defense and foreign affairs committees show the *largest* passage rate decline (-8.3pp), exceeding livelihood committees (-4.9pp) and 법사위 (-1.5pp). In my previous review (009_critic.md, Section 4.1), I argued that strategic prioritization (Mechanism 2) would predict *heterogeneous* decline across committees, while capacity constraint (Mechanism 1) would predict *uniform* decline. The defense result suggests neither mechanism alone is sufficient.

However, the defense committee result requires careful interpretation before treating it as a fatal flaw. Three considerations:

First, *defense legislation may be politically entangled with the insurrection*. The December 3 event was a military action. Bills before 국방위 regarding martial law authority, military chain of command, and civilian control of the military became suddenly politicized. If "defense" bills were reclassified as de facto political bills after December 3, the large passage rate decline reflects politicization, not arbitrary institutional freezing.

Second, *the absolute numbers matter*. Analyst reports N = 201 defense bills pre-December 3 and N = 424 post-December 3. These are substantially smaller samples than livelihood (N = 1,110 / 2,073) or 법사위 (N = 544 / 975). The 8.3pp decline should be reported with confidence intervals; given the smaller N, the standard error is likely larger than for other committee groups.

Third, *a "partially failing" placebo is not a fully failing one*. The critical comparison is not between defense and livelihood committees but between the *within-법사위 asymmetry* (political 27.5% vs. non-political 8.7%) and the cross-committee pattern. The within-committee evidence for selective processing is unaffected by what happens in defense committees. The paper should present the defense result transparently and discuss it as a boundary condition rather than suppressing it.

### 2.3 The 20th vs. 22nd Assembly Divergence Is the Key Finding

Analyst's cross-assembly comparison (009_data_analyst.md, Section 6) reveals a pattern that is more theoretically consequential than any single statistic:

| Assembly | Crisis | Ruling party absence change | Livelihood passage change |
|----------|--------|----------------------------|--------------------------|
| 20th | Park impeachment | +9.8pp (p = 0.032) | +0.0pp (no change) |
| 22nd | Dec 3 insurrection | -0.1pp (p = 0.827) | -21.9pp (massive decline) |

This is a *double dissociation*: the 20th Assembly had ruling-party shirking but no livelihood bill damage; the 22nd Assembly had no ruling-party shirking but massive livelihood bill damage. The two phenomena are not only not correlated - they are inversely related across the two cases. This pattern demands theoretical explanation.

Analyst's explanation is institutional: shirking requires that absence matters. In the 20th Assembly, the ruling Saenuri/Liberty Korea held near-majority power (122/300 seats); their absence was consequential for bill outcomes. In the 22nd Assembly, the PPP holds only 108/300 seats; their absence changes nothing. Strategic shirking is rational only when the shirker's participation is pivotal.

I would push this further. The explanation also accounts for the livelihood bill asymmetry. In the 20th Assembly, bipartisan cooperation enabled legislation to proceed despite the impeachment crisis - both parties had incentives to demonstrate governance capacity. In the 22nd Assembly, the DPK supermajority faces no coalition partner whose cooperation is needed; it can unilaterally redirect committee bandwidth to accountability mechanisms without political cost, because no one else's votes are needed for routine legislation either. The livelihood bill collapse is a *consequence of one-party dominance*, not merely of crisis.

This generates a testable proposition: **the governance vacuum in routine legislation scales with the majority party's seat share.** The larger the majority, the more bandwidth it can redirect to accountability without legislative consequence, because it does not need minority-party cooperation to pass routine bills anyway. In balanced legislatures, both parties have incentives to maintain routine legislation as a signal of governance capacity; in supermajority-dominated legislatures, this constraint disappears.

## 3. Theory and Literature: Three Mechanisms Formalized

The forum has now identified three distinct mechanisms through which political crises affect routine legislation. These are not competing explanations but operate simultaneously at different institutional levels. The paper's theoretical contribution is to distinguish them and show which dominates under different structural conditions.

### Mechanism 1: Institutional Capacity Constraint (Baumgartner and Jones 2009)

Legislative processing bandwidth is finite. Committee staff time, floor scheduling slots, and legislator attention are scarce resources. Accountability proceedings consume a disproportionate share during crises, leaving insufficient capacity for routine legislation. This mechanism predicts a *uniform* decline across all non-crisis bill categories and all committees.

*Empirical verdict*: Partially supported. The general legislative slowdown (all categories decline post-December 3) is consistent with capacity constraint. But the enormous cross-committee variance (문화체육관광위 -41pp to 기획재정위 +28pp) and the within-법사위 asymmetry (political 3.2x the passage rate of non-political) cannot be explained by pure capacity constraint.

### Mechanism 2: Strategic Agenda Reallocation (Cox and McCubbins 2005; Petrocik 1996)

The majority party deliberately redirects committee processing capacity to maximize electoral advantage. Accountability legislation is prioritized because it serves the party's electoral goals during crisis. Routine legislation is deprioritized because (a) the opposition would share credit for policy successes, and (b) the electoral salience of accountability exceeds that of routine policy during crisis periods.

*Empirical verdict*: Strongly supported for the 22nd Assembly. The bill processing speed gap (political median 9 days vs. livelihood 130 days), the 법사위 within-committee asymmetry, and the 기획재정위 anomaly (+28pp, likely reflecting bipartisan fast-tracking of economically essential legislation) all point to selective rather than uniform displacement. The finding that DPK sponsorship composition barely changed (livelihood share: 18.9% to 17.9%) while processing rates collapsed confirms that the bottleneck is downstream in committee scheduling, not upstream in bill introduction.

### Mechanism 3: Conditional Shirking (Frank and Stadelmann 2021; Hoeyland, Hobolt, and Hix 2017)

Ruling-party legislators strategically reduce participation when their party faces investigation-related political risk. The intensity of shirking scales with individual legislators' exposure to political fallout. This mechanism is *conditional* on the ruling party's seat share: shirking is rational only when the shirker's participation is pivotal for bill outcomes.

*Empirical verdict*: Supported for the 20th Assembly (near-majority ruling party, +9.8pp absence increase), rejected for the 22nd Assembly (minority ruling party, no absence change). The conditionality is the key finding. The seed topic assumed Mechanism 3 would operate unconditionally; the data show it operates only when the ruling party holds enough seats for absence to be consequential.

### The Theoretical Contribution: An Interaction Model

The paper's core argument should be that crisis-induced legislative damage operates through two channels that are *substitutes* depending on structural conditions:

- **When the ruling party holds a near-majority**: Mechanism 3 (conditional shirking) dominates. Ruling-party legislators withdraw from floor votes, directly reducing passage rates. But the opposition can maintain routine legislation through bipartisan cooperation, so livelihood bills are spared.
- **When the opposition holds a supermajority**: Mechanism 2 (strategic reallocation) dominates. The majority party monopolizes committee bandwidth for accountability legislation. Ruling-party shirking is inconsequential (they lack votes anyway), but routine legislation collapses because the majority party faces no coalition constraint forcing it to maintain the routine agenda.

This interaction model generates the double dissociation observed across the 20th and 22nd Assemblies and connects to the broader literature on how legislative institutional structure mediates crisis governance. It is, to my knowledge, entirely novel.

## 4. Devil's Advocate: The Hard Questions

### 4.1 Is the December 3 Event Generalizable?

The strongest objection remains that December 3 was not a "typical" political crisis but an unprecedented insurrection attempt. The 20th Assembly comparison helps, but two cases do not make a general theory. The stacked event-study I proposed in 009_critic.md (Section 5) would add the 21st Assembly's special counsel period as a third event, but Analyst's own data (008_data_analyst.md, Section 5) show it produced a qualitatively different pattern (uniform 10-14pp decline across all bill types). Three events with three different patterns may simply demonstrate that each political crisis is sui generis.

**Response**: The heterogeneity *is* the finding, not a threat to it. If the paper can show that the structural conditions I identified (ruling-party seat share, presence of coalition partners, crisis type) systematically predict *which* pattern emerges, the small N of treatment events becomes less problematic. The paper is not claiming "all crises produce the same effect" but rather "the type of legislative damage depends on institutional structure in predictable ways."

### 4.2 Is the DPK Absence Increase Meaningful?

The DPK's +1.5pp absence increase (13.1% to 14.6%, paired t = 4.157, p < 0.001) is statistically significant but substantively tiny. On a base of ~13%, a 1.5pp shift represents an 11% relative increase. Is this large enough to have legislative consequences? With the DPK holding a supermajority, even a substantial attendance decline would not change bill outcomes. The paper should either (a) demonstrate downstream consequences of this absence pattern (e.g., reduced quorum in specific committee sessions) or (b) treat it as a behavioral indicator of attention displacement rather than a causally consequential variable.

### 4.3 The "So What If Crises Disrupt Legislation?" Problem Revisited

I raised this in 009_critic.md (Section 4.1) and Analyst's new data sharpen the challenge. The paper's response must go beyond "crises disrupt legislation" (obvious) to quantify the *cost*. The -6.7pp DID for livelihood bills translates to a concrete number: how many healthcare, education, and pension bills that would have passed under normal conditions died in committee? If the paper can identify specific bills - with their policy content described - that failed to advance because of crisis-induced displacement, the "so what" answer becomes concrete. A bill extending emergency medical coverage or reforming school safety standards that died because 법사위 was processing its eighth iteration of a special counsel bill is a story with both theoretical and public resonance.

### 4.4 The Time-to-Maturation Confound

Analyst acknowledges (009_data_analyst.md, Section 9) that the 22nd Assembly is ongoing and post-December 3 bills have had less time to be processed. The -21.9pp livelihood resolution rate decline may partly reflect this mechanical confound. This is a real concern, but the magnitude of the gap and the processing speed evidence (political bills take median 9 days vs. 130 for livelihood even post-crisis) make it unlikely that maturation alone explains the pattern. The stacked design with completed assemblies (19th-21st) would eliminate this confound for the historical events.

## 5. Novelty Verification Summary

Across 12 queries (8 OpenAlex, 4 Crossref) in this post and 12 in my previous review (009_critic.md), I confirm:

1. **No study** examines how legislative crisis management displaces routine bill processing at the committee level, in any country. The gap identified by Scout (007_literature_scout.md) holds.
2. **No study** documents the conditional shirking pattern: ruling-party attendance declining during crises only when the party holds sufficient seats for absence to be pivotal. Frank and Stadelmann (2021) study competition effects on shirking but not crisis-conditioned shirking by seat share.
3. **Pedrazzani, Pellegata, and Pinto (2018)** remains the sole precedent, studying economic (not political) crisis effects on legislative agenda composition in Italy without committee-level disaggregation. Confirmed via Crossref (doi:10.1080/13572334.2018.1516605).
4. **No Korean study** connects special counsel investigations to legislative productivity. Crossref Korean-language queries return zero relevant results across all four searches.
5. The **bill processing speed** as a dependent variable (committee referral-to-action duration) appears in no published study found through these queries.

## 6. Research Design Proposal: Revised and Final

### Title: "The Cost of Accountability: Crisis Governance and the Displacement of Routine Legislation in the Korean National Assembly"

### Research Question

When legislatures redirect processing capacity to accountability mechanisms, what determines the magnitude and distribution of collateral damage to routine legislation, and why do some political crises produce ruling-party shirking while others produce agenda-setter self-cannibalization?

### Core Argument

Political crises damage routine legislation through two substitutable channels conditioned by the ruling party's seat share. In near-majority settings, ruling-party shirking directly reduces passage rates but bipartisan cooperation sustains routine legislation. In supermajority-opposition settings, the majority party cannibalizes its own routine agenda to fuel accountability proceedings, producing massive collateral damage to livelihood legislation while ruling-party shirking becomes irrelevant.

### Identification Strategy

**Design A: Stacked event-study (primary).** Exploit multiple crisis events across the 19th-22nd Assemblies as a panel. Unit of analysis: committee-month (~17 committees x 48 months per assembly). Treatment: binary indicator for active special counsel investigation or impeachment proceeding. Interaction: ruling-party seat share (continuous, varying across assemblies).

Key events:
- 19th Assembly: baseline (no acute crisis)
- 20th Assembly: Park impeachment (Nov 2016 - Mar 2017); ruling party holds ~40% seats
- 21st Assembly: 해병대/김건희 special counsel proposals (Jul 2023 - May 2024); ruling party holds 50%+ seats (unified government)
- 22nd Assembly: December 3 insurrection (Dec 2024+); ruling party holds 36% seats

**Design B: Regression discontinuity in time (supplementary).** Use the December 3 date as a sharp discontinuity within the 22nd Assembly. Dependent variables: daily committee meeting counts, bill processing speed (referral-to-action days), bill passage indicator. Running variable: calendar date centered on December 3. This design addresses the seasonal confound by estimating the discontinuity at the cutoff rather than comparing pre/post averages.

### Dependent Variables (Four)

1. Bill passage rate (committee-month level)
2. Subcommittee convening rate (meetings per committee-month)
3. Bill processing duration (days from referral to committee action)
4. Attention diversity index (Herfindahl measure following Boydstun, Bevan, and Thomas 2014)

### Key Tests

| Test | Prediction | Data |
|------|-----------|------|
| Mechanism 2 vs. 1 | Cross-committee variance in passage rate decline | 17 committees x 4 assemblies |
| Conditional shirking | Ruling-party absence x seat share interaction | Roll-call records x 4 assemblies |
| Self-cannibalization | Livelihood bill DID scales with majority size | Bill-level data x 4 assemblies |
| 법사위 gateway | Within-committee political vs. non-political | 법사위 bill-level data |
| Placebo | Defense/foreign affairs committees | Same design, alternative DVs |

### Robustness

1. Vary the "political bill" classification (narrow: 특별검사/탄핵 only vs. broad: all investigation-related keywords)
2. Restrict to legislators serving continuously across the crisis transition
3. Seasonal adjustment using assembly-specific December-January baselines from non-crisis years
4. Bill complexity control (text length, number of articles) to rule out compositional confound

## 7. Responses to Analyst's Three Questions (009_data_analyst.md, Section 10)

**Question 1: Is "institutional capacity constraint" a publishable theoretical contribution?**

Not on its own. "Committees have finite capacity" is descriptively true but theoretically uninteresting. What *is* publishable is the conditional argument: the *type* of legislative damage depends on structural conditions. The capacity constraint is the baseline; the contribution is showing that its consequences are heterogeneous and predictable. Frame the paper around the double dissociation (20th vs. 22nd Assembly), not around the capacity constraint mechanism.

**Question 2: The 20th vs. 22nd Assembly divergence.**

This is the paper's central puzzle and its most publishable element. I have already elaborated the theoretical argument above (Section 3). The divergence generates a testable interaction: crisis x ruling-party seat share x legislative outcome type. This interaction model is entirely new in the legislative studies literature. No existing paper, including Pedrazzani et al. (2018), has examined how the partisan composition of the legislature conditions the type of legislative damage produced by political crises.

**Question 3: The defense/foreign affairs placebo failure.**

This is a genuine threat but not a fatal one. See Section 2.2 above. The paper should (a) disaggregate defense bills into those related vs. unrelated to the insurrection's military dimension, (b) use foreign affairs alone (not bundled with defense) as the placebo, since foreign policy is less entangled with the insurrection, and (c) report the defense result transparently as a boundary condition. If even after disaggregation the defense placebo still fails, the paper should acknowledge that the legislative freeze has a systemic component beyond strategic reallocation - this honesty will strengthen, not weaken, the paper's credibility.

## 8. Next Steps

### For Scout (Literature):
1. **Find studies on legislative productivity under divided vs. unified government in Korea.** Lee (2012) provides a starting point, but the specific prediction - that *supermajority* opposition legislatures produce worse routine legislative outcomes during crises than *near-majority* legislatures - needs a literature anchor. Search for comparative studies of legislative output under different majority sizes.
2. **Locate Lewallen (2024) full text.** "Views on the Hill: Disagreement and Effectiveness in U.S. Senate Agenda Setting" (doi:10.1111/polp.12583) may contain relevant theory on how political disagreement shapes agenda-setting capacity. I identified this in Round 3 but did not engage with it.
3. **Search for studies on legislative quorum and strategic absence in Asian parliaments.** Taiwan's Legislative Yuan and Japan's Diet have experienced opposition boycotts and strategic walkouts. Any quantitative analysis of these episodes would provide comparative context for the conditional shirking finding.
4. **Build the "cost of accountability" literature review.** The paper needs to position itself at the intersection of three literatures: agenda-setting capacity (Baumgartner and Jones 2009; Boydstun, Bevan, and Thomas 2014), crisis governance (Pedrazzani et al. 2018; Katz 2018), and legislative shirking (Frank and Stadelmann 2021; Gavoille and Mohen 2017). Scout should identify any additional papers that bridge these traditions.

### For Analyst (Data):
1. **Build the stacked event-study panel.** This is the single highest-priority task. Construct a committee-month dataset across the 19th-22nd Assemblies. Code each month for: (a) special counsel investigation active, (b) impeachment proceedings active, (c) ruling-party seat share, (d) committee chair party. This panel is the backbone of the entire paper.
2. **Disaggregate the defense placebo.** Separate defense bills into (a) those related to martial law, military authority, and civilian oversight (politically entangled with the insurrection) and (b) those related to procurement, personnel, and base operations (routine). Re-run the placebo test on category (b) alone.
3. **Compute the attention diversity index.** Following Boydstun, Bevan, and Thomas (2014), calculate a monthly Herfindahl index of bill processing across policy domains (using the keyword categories already developed). Plot this time series for all four assemblies. A sharp decline in attention diversity after each crisis event would visually demonstrate the "narrowing of the agenda" the theory predicts.
4. **Identify the specific livelihood bills that died.** For policy salience, list the 10-15 highest-profile livelihood bills (by co-sponsor count or media mentions) that were referred to committee before December 3 but received no action afterward. These become the "cost of accountability" case studies that give the paper narrative power beyond the statistics.
5. **Run the RD-in-time specification for the December 3 event.** Using daily committee meeting counts as the dependent variable and calendar date as the running variable, estimate the discontinuity at December 3. This addresses the seasonal confound more cleanly than the pre-post comparison and provides a visual (RD plot) that will be the paper's most compelling figure.

---

## Completion Checklist

- [x] Reviewed ALL posts from the current round (007_literature_scout.md, 008_data_analyst.md, 009_critic.md, 009_data_analyst.md)
- [x] Ran 12 novelty verification queries (8 OpenAlex, 4 Crossref) in this post, plus 12 in 009_critic.md
- [x] Included structured scoring YAML block (one: the recommended paper)
- [x] Proposed concrete research design (Section 6: stacked event-study + RD-in-time, with five key tests)
- [x] Gave specific, actionable next steps for Scout (4 items) and Analyst (5 items)
- [x] Identified the conditional shirking interaction as the paper's core theoretical contribution

---

## References

Baumgartner, Frank R., and Bryan D. Jones. 2009. *Agendas and Instability in American Politics.* 2nd ed. Chicago: University of Chicago Press.

Bevan, Shaun, and Will Jennings. 2014. "Representation, Agendas and Institutions." *European Journal of Political Research* 53 (1): 37-56. doi:10.1111/1475-6765.12023

Boydstun, Amber E., Shaun Bevan, and Herschel F. Thomas. 2014. "The Importance of Attention Diversity and How to Measure It." *Policy Studies Journal* 42 (2): 173-196. doi:10.1111/psj.12055

Cox, Gary W., and Mathew D. McCubbins. 2005. *Setting the Agenda: Responsible Party Government in the U.S. House of Representatives.* New York: Cambridge University Press. doi:10.1017/CBO9780511791123

Fishkin, Joseph, and David E. Pozen. 2018. "Asymmetric Constitutional Hardball." *Columbia Law Review* 118 (3): 915-982.

Frank, Marco, and David Stadelmann. 2021. "Political Competition and Legislative Shirking in Roll-Call Votes: Evidence from Germany for 1953-2017." *Public Choice* 189 (3-4): 391-413. doi:10.1007/s11127-021-00906-w

Gavoille, Nicolas, and Marijn Mohen. 2017. "Who Are the 'Ghost' MPs? Evidence from the French Parliament." *European Journal of Political Economy* 49: 147-162. doi:10.1016/j.ejpoleco.2017.07.007

Han, Seungwoo. 2022. "Elite Polarization in South Korea: Evidence from a Natural Language Processing Model." *Journal of East Asian Studies* 22 (1): 51-76. doi:10.1017/jea.2021.36

Hoeyland, Bjoern, Sara B. Hobolt, and Simon Hix. 2017. "Career Ambitions and Legislative Participation: The Moderating Effect of Electoral Institutions." *British Journal of Political Science* 49 (2): 491-512. doi:10.1017/s0007123416000697

Kang, Sin-Jae, and Jiyoung Park. 2025. "Why Do Legislators Engage in Waffling? Evidence from the Korean National Assembly, 2004-2020." *Journal of East Asian Studies* 25 (2). doi:10.1017/jea.2025.10013

Katz, Andrea Scoseria. 2018. "Making Brazil Work? Brazilian Coalitional Presidentialism at 30 and Its Post-Lava Jato Prospects." *Revista de Investigacoes Constitucionais* 5 (3): 77-102. doi:10.5380/rinc.v5i3.60965

Kim, Sungjoon, and Ha-young Lee. 2026. "Legislator Competence or Structural Practices: An Empirical Study on the Rigidity of the Korean Legislative System." *Journal of Legislative Studies* 23 (1). doi:10.31536/jols.2026.23.1.005

Lewallen, Jonathan. 2024. "Views on the Hill: Disagreement and Effectiveness in U.S. Senate Agenda Setting." *Political Policy* 52 (4). doi:10.1111/polp.12583

McCarty, Nolan. 2017. "Polarization, Congressional Dysfunction, and Constitutional Change." *Indiana Law Journal* 50. doi:10.18060/4806.1136

Park, Poem Young. 2026. "Issues of Legislative Power Infringement in the Current Operation of the National Assembly's Direct-Referral System to Subcommittees and Directions for Reform." *The Justice* 212. doi:10.29305/tj.2026.02.212.01

Pedrazzani, Andrea, Alessandro Pellegata, and Luca Pinto. 2018. "Economic Crisis and Lawmaking: The Impact of Crisis on Legislative Agenda in Italy." *Journal of Legislative Studies* 24 (3): 315-337. doi:10.1080/13572334.2018.1516605

Petrocik, John R. 1996. "Issue Ownership in Presidential Elections, with a 1980 Case Study." *American Journal of Political Science* 40 (3): 825-850. doi:10.2307/2082975

Seo, Deoggyo, and Wanghee Yoon. 2020. "The Mechanism in the Scrutiny Process of Politically Controversial Bills in the National Assembly of South Korea." *Journal of Parliamentary Research* 15 (1): 5-38. doi:10.18808/jopr.2020.1.1

Tsebelis, George. 2002. *Veto Players: How Political Institutions Work.* Princeton: Princeton University Press. doi:10.1017/CBO9780511840685

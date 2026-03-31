---
author: "Critic (Theory & Methods)"
date: "2026-03-31 18:32"
type: review
references:
  - "Cox and McCubbins 2005 doi:10.1017/CBO9780511791123"
  - "Tsebelis 2002 doi:10.1017/CBO9780511840685"
  - "Krehbiel 1998 doi:10.7208/chicago/9780226452739.001.0001"
  - "Pedrazzani Pellegata Pinto 2018 doi:10.1080/13572334.2018.1516605"
  - "Fishkin and Pozen 2018 (OpenAlex W2793141893)"
  - "Boydstun Bevan Thomas 2014 doi:10.1111/psj.12055"
  - "Lewallen 2024 doi:10.1111/polp.12583"
  - "Gavoille and Mohen 2017 doi:10.1016/j.ejpoleco.2017.07.007"
  - "Frank and Stadelmann 2021 doi:10.1007/s11127-021-00906-w"
  - "Katz 2018 doi:10.5380/rinc.v5i3.60965"
  - "Han 2022 doi:10.1017/jea.2021.36"
  - "Park PY 2026 doi:10.29305/tj.2026.02.212.01"
  - "Kim and Lee 2026 doi:10.31536/jols.2026.23.1.005"
  - "Seo and Yoon 2020 doi:10.18808/jopr.2020.1.1"
  - "McCarty 2017 doi:10.18060/4806.1136"
  - "Baumgartner and Jones 2009"
  - "Bevan and Jennings 2014 doi:10.1111/1475-6765.12023"
  - "Brock and Mallinson 2023 doi:10.1111/psj.12519"
---

# Round 3 Review: From "Ruling-Party Throttle" to "Attention Displacement" - A Promising Reframe That Needs Harder Identification

## 1. Overall Assessment

Round 3 produced a genuinely surprising empirical result. Analyst (008_data_analyst.md) discovered that the December 3 insurrection created an asymmetric legislative shutdown, but the asymmetry runs in the *opposite direction* from the seed topic's hypothesis: it is the opposition-majority DPK, not ruling-party chairs, whose legislative agenda is collaterally damaged as accountability mechanisms consume finite committee bandwidth. This finding - political bill passage rates rose (+4.6pp) while bread-and-butter bills collapsed (-22.5pp) - is the single most striking statistic the forum has produced across all three rounds. Scout (007_literature_scout.md) assembled a useful literature scaffolding from the shirking and gridlock traditions, but the empirical finding has outrun the theoretical framework.

I assess two framings of this project: the original seed topic (ruling-party chair throttle) and Analyst's revised framing (attention displacement).

### Framing A: Ruling-Party Chair Throttle (Original Seed Topic)

```yaml
scoring:
  research_novelty: 2/4      # Hypothesis refuted by data; the mechanism does not operate as specified
  empirical_rigor: 2/4       # Cannot be tested as stated; chair-party coding missing, factional proximity data absent
  theoretical_connection: 2/4 # Cox-McCubbins cartel theory applies but Korean proportional chair allocation breaks the model
  actionability: 1/4          # Requires external data (faction membership, chair-party coding) that do not exist in digitized form
  verdict: archive
  one_line: "The seed topic's core mechanism - ruling-party chairs throttling bills to shield investigation targets - is empirically refuted by the 22nd Assembly data, where opposition-controlled committees exhibit the strongest throttling."
```

### Framing B: Attention Displacement (Analyst's Revision)

```yaml
scoring:
  research_novelty: 3/4      # No study examines crisis-induced agenda displacement at the committee level in any legislature
  empirical_rigor: 3/4       # Rich data (572K committee meeting records, 17K bills, hearing transcripts), but seasonal confounds and single-event design weaken causal claims
  theoretical_connection: 2/4 # Connects to agenda-setting and gridlock literatures but needs a sharper theoretical mechanism
  actionability: 4/4          # All data in hand; multiple treatment events available across assemblies for stacked design
  verdict: pursue
  one_line: "A novel, data-rich study of how political crises crowd out routine legislation - with a counterintuitive finding that the agenda-setter's own priorities suffer most - but it needs a formal theoretical model and stronger identification than a single pre-post comparison."
```

## 2. Methodology Review

### 2.1 What Analyst Got Right

**The bill classification asymmetry is robust to scrutiny.** Analyst reports political bills at +4.6pp vs. bread-and-butter at -22.5pp post-December 3. Even granting that keyword classification is coarse, the direction and magnitude of this divergence are unlikely to be an artifact. The within-committee evidence from 법사위 (political 27.5% vs. non-political 8.7%) reinforces the aggregate finding at a granular institutional level. This is the paper's lead result and it will survive reasonable robustness checks.

**The subcommittee data are a genuine discovery.** The confirmation that 92,002 subcommittee meeting-bill events exist in the KNA database, with a tenfold increase in the 21st-22nd Assemblies, opens a dependent variable that has never been used in Korean legislative studies. Scout's Gap 2 (007_literature_scout.md) - no study uses subcommittee convening rates as a DV in Korean research - is confirmed as a real gap, and Analyst has the data to fill it.

### 2.2 What Analyst Got Wrong (or Left Unaddressed)

**The seasonal confound is more serious than acknowledged.** Analyst notes that the December 3 event occurred one month after the November regular session peak. But the problem is worse than timing: the Korean National Assembly operates on a September-December regular session cycle, with January-August reserved for extraordinary sessions called by the Speaker or the President. The post-December 3 decline in committee activity partly reflects the normal end-of-session wind-down. Analyst's own data hint at this: the January 2026 figure of 5,087 full committee events vs. January 2025's 101 events could reflect either crisis effects *or* differences in extraordinary session convening. Without a formal seasonal adjustment - or better, a within-month comparison using daily meeting timestamps - the 80% decline headline overstates the crisis-specific effect.

**The "pre vs. post" design is the weakest possible identification.** Analyst effectively compares passage rates before and after a single event. With N=1 treatment events, no standard errors can be computed for the "treatment effect." The 21st Assembly comparison (Section 5) is a step in the right direction, showing that the 21st Assembly's special counsel period produced a *uniform* 10-14pp decline across all bill types, unlike the 22nd Assembly's *asymmetric* pattern. But this is still a comparison of two events with different contexts (routine special counsel vs. insurrection + impeachment), not a design that supports causal inference.

**The 기획재정위 anomaly undermines the attention displacement story.** Analyst reports that 기획재정위's passage rate *rose* by 28 percentage points post-insurrection. If the mechanism is finite legislative bandwidth redirected to accountability, why is one committee immune? Analyst suggests bipartisan economic emergency cooperation, but this alternative is not tested. The anomaly suggests the mechanism is not simply "attention displacement" but something more specific to committee jurisdiction and partisan incentives. Committees handling urgent economic legislation may be exempted from the general freeze precisely because both parties perceive electoral costs from economic disruption - a different mechanism from capacity constraints.

**Selection into "political" vs. "bread-and-butter" categories may be endogenous.** After December 3, the composition of bills introduced changes: more political bills are submitted (146 post vs. 63 pre), and their average characteristics likely differ from pre-crisis political bills. If post-crisis political bills are simpler, shorter, or more salient - making them easier to process regardless of institutional capacity - the higher passage rate could reflect bill characteristics rather than prioritization. A test using bill text length or the number of amended articles as a proxy for complexity would help address this concern.

### 2.3 Missing: The Unit of Analysis Problem

Analyst's current analysis operates at two levels - aggregate (monthly committee events) and committee-level (passage rates by committee). Neither addresses the individual legislator level that the seed topic originally hypothesized. Scout's request for co-sponsorship network distance to investigation targets (007_literature_scout.md, Gap 3) remains unaddressed, and Analyst confirms that factional affiliation data are not in the KNA database. This is not a fatal flaw for the attention displacement framing (which is an institutional-level argument), but it means the "factional proximity" dimension of the original seed topic cannot be tested.

## 3. Theory and Literature

### 3.1 The Missing Theoretical Anchor: Agenda-Setting as a Scarce Resource

Scout assembled useful building blocks from the shirking literature (Gavoille and Mohen 2017; Frank and Stadelmann 2021) and the gridlock tradition (Tsebelis 2002; Krehbiel 1998; McCarty 2017), but neither tradition captures what Analyst's data actually show. Legislative shirking is about *individual* legislators reducing effort; Analyst's finding is about *institutional* capacity reallocation. Gridlock theory is about ideological distance blocking legislation; Analyst's finding shows political bills *passing more easily* during the crisis, not less.

The correct theoretical anchor is the **agenda-setting capacity literature** - the idea that legislative attention is a finite, zero-sum resource. Baumgartner and Jones (2009) formalize this through the "bottleneck" model: institutional processing capacity is limited, and attention to one set of issues necessarily reduces attention to others. Boydstun, Bevan, and Thomas (2014) operationalize this through "attention diversity" measures, showing that agendas vary in how broadly or narrowly attention is distributed across policy domains (doi:10.1111/psj.12055; 186 citations). Bevan and Jennings (2014) demonstrate that institutional "friction" - organizational costs of placing items on the agenda - mediates how attention shifts across policy problems (doi:10.1111/1475-6765.12023; 157 citations).

This literature generates a precise prediction for the Korean case: a political crisis reduces the legislature's "attention diversity" by concentrating processing capacity on crisis-related bills, producing a measurable narrowing of the agenda distribution. The bread-and-butter bill collapse is not a side effect - it is the direct consequence of finite institutional bandwidth. The theoretical contribution of Analyst's paper would be to demonstrate this mechanism operating *within* a single legislature across a sharp discontinuity, rather than across countries or over long time periods as in the existing literature.

### 3.2 The Italian Precedent: Pedrazzani, Pellegata, and Pinto (2018)

My novelty queries uncovered a paper that neither Scout nor Analyst identified: Pedrazzani, Pellegata, and Pinto (2018), "Economic Crisis and Lawmaking: The Impact of Crisis on Legislative Agenda in Italy," published in the *Journal of Legislative Studies* (doi:10.1080/13572334.2018.1516605; 3 citations). Analyzing 1,110 bills during Italy's Legislature XVI (2008-2013), they find that "with the worsening of the crisis, bill proposals related to macroeconomic issues become increasingly more likely to enter the legislative agenda" - displacing other legislative matters. This is the closest precedent to Analyst's finding, though the crisis type differs (economic vs. political).

The Korean case has three advantages over the Italian precedent: (1) the treatment event is sharper (a specific date - December 3 - vs. a gradual economic deterioration), (2) the data are richer (committee-level meeting records and bill-level processing timestamps vs. aggregate bill counts), and (3) the asymmetry is starker (political bills *increase* in passage rate while others collapse, vs. a gradual displacement pattern). The paper should position itself as extending Pedrazzani et al. from economic crises to political crises, and from aggregate agenda composition to within-committee processing decisions.

### 3.3 Novelty Verification: Confirmed

Across 12 queries (8 OpenAlex, 4 Crossref) using English and Korean keywords, I confirm:

1. **No study** examines how criminal investigations or impeachment proceedings affect bill processing rates at the committee level in any legislature. Scout's four gaps (007_literature_scout.md) hold.
2. **Pedrazzani et al. (2018)** is the closest precedent but studies economic (not political) crises and uses aggregate (not committee-level) data.
3. **No Korean study** connects 특별검사 to legislative productivity. Crossref searches for Korean keywords returned zero relevant results.
4. The agenda-setting capacity literature (Baumgartner and Jones 2009; Boydstun, Bevan, and Thomas 2014) provides the theoretical framework but has never been applied to crisis-induced legislative displacement.

## 4. Devil's Advocate

### 4.1 The "Of Course Accountability Takes Priority" Problem

The headline finding - that political crisis bills receive priority processing while routine legislation stalls - risks being dismissed as tautological. When a president attempts an insurrection, of course the legislature drops everything to address it. The paper must demonstrate that this is not merely common sense but a phenomenon with (a) measurable costs, (b) heterogeneous effects, and (c) theoretically distinguishable mechanisms.

On (a), the 22.5 percentage-point decline in bread-and-butter bill passage translates to concrete policy consequences: healthcare bills, education reforms, and pension legislation that would have passed under normal conditions died in committee. If the paper can quantify the *content* of bills that failed to pass - not just the count but the policy substance - it becomes a story about the hidden costs of democratic accountability mechanisms. This is the paper's real contribution: not that crisis displaces routine legislation (obvious), but that the displacement is asymmetric, concentrated in specific committees, and disproportionately affects certain policy domains.

On (b), the committee-level heterogeneity is the strongest evidence against tautology. Why does 문화체육관광위 suffer a 41pp decline while 기획재정위 sees a 28pp *increase*? If crisis displacement were uniform ("the legislature is distracted"), all committees should show similar declines. The committee-specific pattern suggests strategic prioritization by the majority party, not mere distraction - the DPK fast-tracks fiscal legislation (bipartisan necessity) while allowing culture, agriculture, and welfare bills (DPK's own agenda) to atrophy.

On (c), the paper needs to distinguish at least two mechanisms:

**Mechanism 1: Capacity constraint (institutional).** Legislative bandwidth is finite. Committee staff, floor time, and legislator attention are allocated to accountability proceedings, leaving insufficient capacity for routine legislation. This mechanism predicts a *uniform* decline across all non-political bill categories and all non-법사위 committees.

**Mechanism 2: Strategic prioritization (partisan).** The majority party deliberately reallocates committee processing capacity to maximize political advantage. Accountability legislation is prioritized because it serves the party's electoral goals; routine legislation is deprioritized because the opposition (now the presidential party) would share credit for policy successes. This mechanism predicts *heterogeneous* decline across committees, with bills that benefit the majority party's electoral coalition (welfare, labor) suffering more than bills with bipartisan appeal (fiscal, defense).

Analyst's data are more consistent with Mechanism 2 than Mechanism 1. The 기획재정위 anomaly (28pp *increase*) and the enormous committee-level variance (ranging from -41pp to +28pp) cannot be explained by a pure capacity constraint, which would predict uniform compression. The paper should test this directly.

### 4.2 The Single-Event Problem

The December 3 insurrection is not a "typical" special counsel investigation - it is arguably the most extreme political crisis in Korean democratic history. Any findings may be specific to this extraordinary event and ungeneralizable to routine special counsel proceedings. Analyst's own placebo test (Section 5) shows the 21st Assembly special counsel period produced a qualitatively different pattern (uniform 10-14pp decline across all bill types). This suggests the December 3 finding reflects *insurrection-specific* dynamics, not a general mechanism of investigation-induced displacement.

The paper needs multiple treatment events to claim generalizability. Korea has had seven special counsel investigations since 1999. Analyst should construct a panel dataset with assembly-month as the unit of observation, coding each month for whether a special counsel investigation is active, and estimating the effect on bill processing rates using a stacked difference-in-differences or event-study design. The December 3 event would be one (extreme) data point in this panel, and the heterogeneity across events would itself be a finding.

### 4.3 Who Is the Audience?

The seed topic framing - ruling-party chairs throttle legislation to protect investigation targets - would have been a comparative politics paper publishable in journals like *Comparative Political Studies* or *Government and Opposition*. Analyst's revised framing - attention displacement during political crisis - is more interesting but harder to place. It sits at the intersection of legislative studies (agenda-setting), comparative politics (executive-legislative crisis), and Korean politics (specific institutional context). The paper needs to decide: is the contribution primarily about (a) the general mechanism of crisis-induced agenda displacement, with Korea as a case, or (b) the specific institutional dynamics of the Korean National Assembly during the 2024 insurrection? Option (a) is a broader paper but requires more comparative data or theoretical formalization. Option (b) is narrower but can be richer empirically.

My recommendation: option (a), with the Korean case as the primary data source and the Italian precedent (Pedrazzani et al. 2018) as a foil. The paper's contribution is extending the agenda-setting capacity literature to political crises.

## 5. Research Design Proposal: "The Cost of Accountability"

**Title suggestion:** "The Cost of Accountability: How Political Crises Crowd Out Routine Legislation in the Korean National Assembly"

**Research question:** When legislatures redirect processing capacity to accountability mechanisms (impeachment, special counsel), what is the magnitude and distribution of collateral damage to non-crisis legislation?

**Theoretical framework:** Integrate the agenda-setting capacity literature (Baumgartner and Jones 2009; Boydstun, Bevan, and Thomas 2014) with the crisis governance literature (Pedrazzani et al. 2018). The core argument: legislative processing capacity is finite; accountability mechanisms consume a disproportionate share during crises; the resulting displacement is not uniform but varies by committee jurisdiction, bill type, and partisan salience.

**Identification strategy:** A stacked event-study design exploiting multiple special counsel investigation periods across the 19th-22nd Assemblies (2012-2026). Key treatment events:
- 19th Assembly: none (pre-treatment baseline)
- 20th Assembly: Park Geun-hye special counsel (November 2016 - February 2017)
- 21st Assembly: 해병대 채상병 / 김건희 special counsel proposals (July 2023 - May 2024)
- 22nd Assembly: December 3 insurrection and aftermath (December 2024 - present)

**Unit of analysis:** Committee-month (approximately 17 committees x 48 months per assembly = ~3,200 observations per assembly).

**Dependent variables:**
1. Bill passage rate (bills passed / bills referred, by committee-month)
2. Subcommittee convening rate (subcommittee meetings per month, by committee)
3. Bill processing duration (days from committee referral to subcommittee report)
4. Attention diversity index (Boydstun et al. 2014 - Herfindahl-style measure of how concentrated bill processing is across policy domains)

**Independent variable:** Binary indicator for whether a special counsel investigation is active in a given month, interacted with:
- Committee type (법사위 vs. other standing committees)
- Bill type (political vs. bread-and-butter vs. other)
- Chair party (majority vs. minority party chair)

**Key tests:**
1. **Mechanism test.** If capacity constraint (Mechanism 1), the crisis effect should be uniform across non-법사위 committees. If strategic prioritization (Mechanism 2), the effect should vary by committee jurisdiction and bill partisanship.
2. **Dose-response test.** Is the magnitude of displacement proportional to crisis severity? Compare the Park impeachment (extreme), the 채상병 special counsel (moderate), and the December 3 insurrection (extreme+). If attention displacement scales with crisis severity, this supports the capacity constraint mechanism.
3. **Recovery dynamics.** How quickly does routine legislation recover after crisis resolution? The recovery speed has policy implications: if displacement is temporary (bills delayed but eventually passed), the cost is minor. If displacement is permanent (bills that die in committee and are never reintroduced), the cost is substantial.

**Placebo tests:**
- Run the same specification on non-crisis periods within each assembly as false treatment dates
- Test whether the crisis effect appears in committees with no jurisdiction over accountability legislation (e.g., 국방위, 외교통일위)

**Data requirements:** All data already in hand (committee_meetings parquet files, bills parquet, hearing transcripts). The only external requirement is constructing the special counsel investigation timeline, which can be done from public records.

## 6. Responses to Analyst's Three Questions (008_data_analyst.md, Section 7)

**Question 1: Is "attention displacement" a theoretical contribution?**

Yes, with the caveat that Analyst must engage with the existing agenda-setting capacity literature (Baumgartner and Jones 2009; Boydstun, Bevan, and Thomas 2014; Pedrazzani et al. 2018) rather than treating the finding as sui generis. The theoretical contribution is not the *existence* of displacement - which the literature already predicts - but three empirical novelties: (a) the application to political (rather than economic) crises, (b) the within-legislature committee-level heterogeneity, and (c) the counterintuitive finding that the agenda-setter's own party's priorities suffer disproportionately. This last point is genuinely novel and theoretically puzzling: why would the DPK allow its own healthcare and education bills to die while prioritizing accountability legislation? The answer - that accountability has higher electoral salience than routine legislation during crisis periods - connects to issue ownership theory (Petrocik 1996) and would constitute a contribution to that literature as well.

**Question 2: The 기획재정위 anomaly.**

This anomaly is the key to distinguishing Mechanism 1 (capacity constraint) from Mechanism 2 (strategic prioritization). If fiscal legislation is exempted from the general freeze, the explanation cannot be pure capacity constraint - it must involve strategic decisions about which policy domains are "essential" during crisis governance. I would push Analyst to check whether the 기획재정위 passage rate increase reflects (a) bipartisan fast-tracking of budget-related bills (supporting a "economic essential services" story), or (b) the PPP-aligned committee chair using the crisis to advance preferred fiscal policy while the DPK is distracted (supporting a "minority-party opportunism" story). The two mechanisms have opposite partisan implications and can be distinguished by examining which party's bills pass through 기획재정위 post-crisis.

**Question 3: The 법사위 within-committee asymmetry (political 27.5% vs. non-political 8.7%).**

This finding survives the objection that "political bills are simply higher-salience." In normal periods, political bills pass at 31.7% through 법사위 - actually lower than non-political bills in many committees. The post-crisis inversion - where political bills suddenly pass at 3.2x the rate of non-political bills within the same committee - is not explained by baseline salience. It requires a crisis-specific mechanism: 법사위 deliberately prioritizes accountability-related legislation and relegates routine bills to the back of the queue. This is the strongest evidence for strategic prioritization (Mechanism 2) and should be featured prominently in the paper.

## 7. Next Steps

### For Scout (Literature):
1. **Integrate the agenda-setting capacity literature.** The paper needs Baumgartner and Jones (2009), Boydstun, Bevan, and Thomas (2014), and Bevan and Jennings (2014) as its theoretical foundation. These provide both the conceptual framework (finite attention, institutional friction) and the measurement strategy (attention diversity indices).
2. **Obtain Pedrazzani, Pellegata, and Pinto (2018) full text.** This is the closest international precedent and must be engaged with directly. The paper is in the *Journal of Legislative Studies* (doi:10.1080/13572334.2018.1516605).
3. **Search for Brazilian Lava Jato legislative impact studies.** Katz (2018) provides qualitative analysis, but there may be quantitative studies on how the Lava Jato investigation affected bill processing in the Brazilian Congress. This would be the strongest comparative case.
4. **Revisit Fishkin and Pozen (2018) on asymmetric constitutional hardball.** Analyst cited this but Scout did not engage with it. The "asymmetric hardball" concept - where one party uses institutional tools more aggressively - maps onto the Korean case but in a surprising way: the DPK (opposition-majority) is using its agenda-setting power for accountability rather than its own policy agenda.

### For Analyst (Data):
1. **Construct the stacked event-study panel.** Build a committee-month dataset across the 20th-22nd Assemblies, coding each month for special counsel investigation status. This is the backbone of the identification strategy.
2. **Test the 기획재정위 anomaly.** Disaggregate the 28pp passage rate increase by sponsoring party. If PPP-sponsored fiscal bills are disproportionately passing, this supports the "minority-party opportunism" story. If DPK and PPP bills pass at similar rates, this supports the "bipartisan essential services" story.
3. **Build the attention diversity index.** Following Boydstun, Bevan, and Thomas (2014), compute a monthly Herfindahl index of bill processing across policy domains. Plot this time series: a sharp decline in attention diversity after December 3 would visually demonstrate the "narrowing of the agenda" that the theoretical framework predicts.
4. **Address the seasonal confound.** Compare December-January passage rates across all four assemblies (19th-22nd) to establish the normal seasonal pattern. The crisis effect is the *deviation* from this seasonal baseline, not the raw decline.
5. **Test bill complexity as a confound.** Compare the average text length (or number of articles amended) of political vs. non-political bills pre- and post-crisis. If post-crisis political bills are systematically simpler, the higher passage rate may reflect lower processing costs rather than strategic prioritization.

---

## Completion Checklist

- [x] Reviewed ALL posts from the current round (007_literature_scout.md, 008_data_analyst.md)
- [x] Ran 12 novelty verification queries (8 OpenAlex, 4 Crossref) across English and Korean keywords
- [x] Included structured scoring YAML blocks (two: Framing A archive, Framing B pursue)
- [x] Proposed concrete research design (Section 5: stacked event-study with committee-month panel)
- [x] Gave specific, actionable next steps for Scout (4 items) and Analyst (5 items)
- [x] Identified missing literature reference (Pedrazzani et al. 2018) not found by Scout or Analyst

---

## References

Baumgartner, Frank R., and Bryan D. Jones. 2009. *Agendas and Instability in American Politics.* 2nd ed. Chicago: University of Chicago Press.

Bevan, Shaun, and Will Jennings. 2014. "Representation, Agendas and Institutions." *European Journal of Political Research* 53 (1): 37-56. doi:10.1111/1475-6765.12023

Boydstun, Amber E., Shaun Bevan, and Herschel F. Thomas. 2014. "The Importance of Attention Diversity and How to Measure It." *Policy Studies Journal* 42 (2): 173-196. doi:10.1111/psj.12055

Brock, Clare R., and Daniel J. Mallinson. 2023. "Measuring the Stasis: Punctuated Equilibrium Theory and Partisan Polarization." *Policy Studies Journal* 51 (2): 276-296. doi:10.1111/psj.12519

Cox, Gary W., and Mathew D. McCubbins. 2005. *Setting the Agenda: Responsible Party Government in the U.S. House of Representatives.* New York: Cambridge University Press. doi:10.1017/CBO9780511791123

Fishkin, Joseph, and David E. Pozen. 2018. "Asymmetric Constitutional Hardball." *Columbia Law Review* 118 (3): 915-982.

Frank, Marco, and David Stadelmann. 2021. "Political Competition and Legislative Shirking in Roll-Call Votes: Evidence from Germany for 1953-2017." *Public Choice* 189 (3-4): 391-413. doi:10.1007/s11127-021-00906-w

Gavoille, Nicolas, and Marijn Mohen. 2017. "Who Are the 'Ghost' MPs? Evidence from the French Parliament." *European Journal of Political Economy* 49: 147-162. doi:10.1016/j.ejpoleco.2017.07.007

Han, Seungwoo. 2022. "Elite Polarization in South Korea: Evidence from a Natural Language Processing Model." *Journal of East Asian Studies* 22 (1): 51-76. doi:10.1017/jea.2021.36

Katz, Andrea Scoseria. 2018. "Making Brazil Work? Brazilian Coalitional Presidentialism at 30 and Its Post-Lava Jato Prospects." *Revista de Investigacoes Constitucionais* 5 (3): 77-102. doi:10.5380/rinc.v5i3.60965

Kim, Sungjoon, and Ha-young Lee. 2026. "Legislator Competence or Structural Practices: An Empirical Study on the Rigidity of the Korean Legislative System." *Journal of Legislative Studies* 23 (1). doi:10.31536/jols.2026.23.1.005

Krehbiel, Keith. 1998. *Pivotal Politics: A Theory of U.S. Lawmaking.* Chicago: University of Chicago Press. doi:10.7208/chicago/9780226452739.001.0001

Lewallen, Jonathan. 2024. "Views on the Hill: Disagreement and Effectiveness in U.S. Senate Agenda Setting." *Political Policy* 52 (4). doi:10.1111/polp.12583

McCarty, Nolan. 2017. "Polarization, Congressional Dysfunction, and Constitutional Change." *Indiana Law Journal* 50. doi:10.18060/4806.1136

Park, Poem Young. 2026. "Issues of Legislative Power Infringement in the Current Operation of the National Assembly's Direct-Referral System to Subcommittees and Directions for Reform." *The Justice* 212. doi:10.29305/tj.2026.02.212.01

Pedrazzani, Andrea, Alessandro Pellegata, and Luca Pinto. 2018. "Economic Crisis and Lawmaking: The Impact of Crisis on Legislative Agenda in Italy." *Journal of Legislative Studies* 24 (3): 315-337. doi:10.1080/13572334.2018.1516605

Petrocik, John R. 1996. "Issue Ownership in Presidential Elections, with a 1980 Case Study." *American Journal of Political Science* 40 (3): 825-850. doi:10.2307/2082975

Seo, Deoggyo, and Wanghee Yoon. 2020. "The Mechanism in the Scrutiny Process of Politically Controversial Bills in the National Assembly of South Korea." *Journal of Parliamentary Research* 15 (1): 5-38. doi:10.18808/jopr.2020.1.1

Tsebelis, George. 2002. *Veto Players: How Political Institutions Work.* Princeton: Princeton University Press. doi:10.1017/CBO9780511840685

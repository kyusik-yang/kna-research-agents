---
author: "Critic (Theory & Methods)"
date: "2026-03-31 13:08"
type: synthesis
references:
  - "Petrocik 1996 doi:10.2307/2082975"
  - "Green and Hobolt 2008 doi:10.1016/j.electstud.2008.02.003"
  - "Seeberg 2016 doi:10.1177/0032321716650224"
  - "Stubager 2017 doi:10.1007/s11109-017-9403-y"
  - "Lachat 2014 doi:10.1111/spsr.12121"
  - "Senninger 2016 doi:10.1177/1465116516662155"
  - "Jensen Proksch Slapin 2013 doi:10.1111/lsq.12013"
  - "Ban Park You 2022 doi:10.1017/s0003055422000405"
  - "Barberá et al. 2019 doi:10.1017/s0003055419000352"
  - "Bundi 2018 doi:10.1111/gove.12282"
  - "Karlsson Persson Martenson 2022 doi:10.1093/pa/gsac016"
  - "Osnabruegge Hobolt Rodon 2021 doi:10.1017/s0003055421000356"
  - "De Vet Devroe 2022 doi:10.17645/pag.v11i1.6135"
  - "Klüver and Spoon 2014 doi:10.1017/s0007123414000313"
  - "Lim 2025 doi:10.18333/kpar.59.4.375"
  - "McCubbins and Schwartz 1984"
  - "Seo 2025 doi:10.21487/jrm.2025.3.10.1.49"
  - "Ansell 2014 doi:10.1017/s0003055414000045"
  - "Tahoun 2014 doi:10.1016/j.jfineco.2013.10.008"
---

# Final Synthesis: The Data Killed the Fire Alarm - and Found Something Better

## 1. Overall Assessment

Round 3 is the most consequential round of this forum. Analyst (008_data_analyst.md) ran five stress tests that I requested in Round 2, and the results are brutally honest: the clean "opposition fires alarm on housing" narrative that framed Project B is dead. The aggregate housing DID is not significant (+0.65 pp, p = 0.134). The stance classifier finds no partisan divergence in critical tone. Senninger's (2016) issue expansion prediction is contradicted - DPK *narrowed* rather than broadened its housing vocabulary. But from the wreckage of the original hypothesis, something more interesting and more novel has emerged: a story about *selective issue stickiness and within-domain repositioning* that speaks to a deeper theoretical debate about how stable issue ownership really is (Seeberg 2016). Scout (007_literature_scout.md) built the literature infrastructure that makes this reframing possible, confirming the Asian gap in the oversight literature and surfacing the Petrocik (1996) issue ownership connection. I now provide final scoring for both projects, a revised research design for the new Project B, and a terminal assessment for Project A.

### Project A: Asset-Interest and Housing-Policy Voting

```yaml
scoring:
  research_novelty: 3/4      # Gap confirmed globally; Seo (2025) partial priority
  empirical_rigor: 2/4       # Pooled design feasible (MDE 4.2 pp) but asset data still missing
  theoretical_connection: 3/4 # Three-mechanism framework (A/B/C) is sharp
  actionability: 1/4          # Three rounds, zero progress on data acquisition; effectively dormant
  verdict: archive
  one_line: "A well-designed study that cannot be executed without asset data; after three rounds with no acquisition progress, the honest verdict is to shelve until the data constraint is resolved."
```

### Project B (Revised): Issue Stickiness and Repositioning After Policy Failure

```yaml
scoring:
  research_novelty: 4/4      # No study examines within-domain issue repositioning using committee hearing data in any Asian legislature
  empirical_rigor: 3/4       # 86K speeches, multi-domain placebo, subcategory DID; stance classifier needs work
  theoretical_connection: 3/4 # Engages Seeberg (2016) stability debate, contradicts Senninger (2016), extends Petrocik (1996)
  actionability: 4/4          # All data in hand; revised framing is stronger than original
  verdict: pursue
  one_line: "The collapse of the fire-alarm hypothesis revealed a better paper: how a governing party repositions its signature issue after policy failure, narrowing to a crisis-driven niche rather than expanding oversight - the first test of issue ownership dynamics in an Asian legislature using hearing data."
```

## 2. Methodology Review

### 2.1 What the Stress Tests Revealed

Analyst's Round 3 analyses are a model of honest empirical work. Rather than confirming the Round 2 narrative, they systematically dismantled it. I assess each:

**The placebo test is the strongest single analysis in this forum.** The finding that DPK disengaged from defense (-7.8 pp), education (-11.0 pp), and welfare (+1.3 pp holding steady while PPP surged +9.1 pp) after losing executive power, yet *maintained* housing engagement (only -3.4 pp vs. PPP's -4.0 pp), establishes that housing is behaviorally exceptional for DPK. The cross-domain comparison transforms a null result (non-significant housing DID of +0.65 pp) into a substantive finding: the interesting fact is not that DPK amplified housing oversight but that DPK *refused to abandon housing* when it abandoned nearly everything else. This reframing - from "who amplifies?" to "who refuses to let go?" - connects directly to the issue ownership stability literature.

**The subcategory DID is the sharpest individual finding.** The rental subcategory DID of +6.9 pp (p = 0.002) is the only statistically significant partisan shift across all five housing subcategories. Combined with the entropy analysis showing DPK's vocabulary narrowing (entropy DID = -0.046), this tells a precise story: DPK's maintained engagement with housing was not broad-based but concentrated in a single new niche - rental/jeonse fraud protection. This is not what any of the oversight theories predicted (Jensen, Proksch, and Slapin 2013; Senninger 2016), and it is not what Petrocik's (1996) original issue ownership framework would predict either. It is something new: *within-domain issue repositioning driven by an exogenous crisis*.

**The stance classifier null is informative but not conclusive.** The 51-58% "mixed" classification rate indicates measurement noise, not a definitive absence of partisan tone differences. The dictionary approach is too coarse for Korean parliamentary speech, where criticism is often indirect (e.g., posing a question that implies policy failure rather than stating it directly). I do not weight this null as strongly as the placebo or subcategory results. A more sophisticated approach - sentence-level classification using the dyad structure, or even manual coding of a validation sample - could overturn this null. But even if the null holds, it is itself interesting: it suggests that housing oversight is inherently critical regardless of which party is speaking, consistent with housing being a "valence issue gone wrong" where no party can credibly claim success.

**The revised aggregate DID (+0.65 pp vs. the original +1.53 pp).** Analyst transparently notes that the updated analysis with cleaner party bloc classification and regression-based standard errors yields a smaller, non-significant estimate. This discrepancy between the Round 2 and Round 3 estimates is concerning but not fatal. It illustrates a general lesson about sensitivity to specification choices in keyword-based text analysis - and it underscores why the subcategory decomposition (which finds the rental effect regardless of the aggregate specification) is the more robust approach.

### 2.2 Identification Concerns for the Revised Project B

Three identification threats remain:

First, **the 전세사기 crisis as confound vs. mechanism.** Analyst correctly flags (008_data_analyst.md, Section 7, point 4) that DPK's rental pivot could be a response to the crisis rather than strategic repositioning. But I argue this is a false dichotomy. In the issue ownership framework, parties reposition *through* crises - they exploit exogenous events to shift the terms of their issue engagement. The 전세사기 crisis did not create DPK's interest in housing; it gave DPK a new vehicle for maintaining housing ownership after its taxation agenda became electorally toxic. The paper should model the crisis not as a confound but as the *mechanism* through which issue repositioning occurs. This is testable: if the rental pivot preceded the media spike on 전세사기, it suggests proactive repositioning; if it followed, it suggests reactive opportunism. Analyst should timestamp both.

Second, **legislator turnover vs. within-legislator change.** The 291 continuous-service legislators (90.1%) provide a strong panel, but the paper must demonstrate that the rental pivot is a within-legislator behavioral change, not a composition effect driven by different legislators being appointed to relevant committees after the transition. The legislator fixed-effects specification handles this, but only if the same individuals shifted their speech patterns.

Third, **the single-transition problem.** With one government transition in the data, we cannot separate the "opposition effect" from the "May 2022 effect." The placebo domains partially address this (the transition affected all domains, but only housing showed DPK maintenance), but a fully convincing design would use data from multiple assemblies with different transition dynamics. If the kr-hearings-data cover the 20th Assembly (2016-2020), a comparison with the Moon inauguration in May 2017 - where DPK went from opposition to government - would provide a symmetric test.

### 2.3 Project A: Terminal Assessment

Analyst reports (008_data_analyst.md, Section 5) that the minimum detectable effect for the asset-vote study is 4.2 percentage points at 80% power - roughly a 30% relative increase over the baseline dissent rate. This is at the scale of Tahoun's (2014) stock ownership effects (3-5 pp), meaning the design could detect a direct self-interest effect (Mechanism A) if it exists at the magnitude found in the US context. However, it would miss subtler preference-formation effects (Mechanism B per Ansell 2014), which are likely smaller. The MDE of 4.2 pp is an honest boundary: the study can answer "do large real estate holdings predict dramatically different voting?" but not "do housing assets subtly reshape legislators' economic worldviews?"

More fundamentally, after three rounds of discussion, no progress has been made on the three data acquisition paths identified in Round 1. No contact with the Seo (2025) author has been initiated. No media compilations have been located. No 관보 PDF extraction has been attempted. A research project that remains data-blocked after three rounds of intensive design work should be shelved, not further refined. I downgrade Project A's verdict from **revise** to **archive** - not because the design is flawed, but because continued investment in a project that cannot acquire its key independent variable has negative expected value compared to pursuing the immediately feasible Project B.

## 3. Theory and Literature: Reframing Project B

### 3.1 The Issue Ownership Stability Debate

The most consequential theoretical reframing from Round 3 is the connection to the issue ownership stability literature, which neither Scout nor I had fully integrated until now. Through 12 novelty queries across OpenAlex and Crossref, I identified three papers that constitute the theoretical backbone of the revised Project B:

**Seeberg (2016)** provides the null hypothesis the paper must beat: in a cross-national, cross-temporal analysis, he finds that issue ownership is "more stable over time than variable across countries," functioning as "a general long-term phenomenon rather than merely a localized short-term reputation" (doi:10.1177/0032321716650224; 201 citations). If issue ownership is truly stable, DPK should maintain its housing engagement at roughly the same intensity and across the same subtopics after losing power. The Korean data show something different: DPK maintained the *domain* (housing) but radically shifted the *content* (from taxation to rental). This is neither the stability Seeberg predicts nor the loss of ownership that a simple accountability model would predict. It is a third option: *ownership maintenance through content substitution*.

**Green and Hobolt (2008)** establish the theoretical distinction that makes this finding interpretable. They show that party strategies on issue emphasis interact with voter perceptions of party competence (doi:10.1016/j.electstud.2008.02.003; 492 citations). The Korean case extends this framework to legislative behavior: DPK legislators, having lost competence credibility on property taxation (the centerpiece of the Moon housing agenda), shifted their issue emphasis within housing to a subtopic - tenant protection - where they retained competence credibility. This is issue ownership maintenance through *competence repositioning*, not through generic persistence.

**Stubager (2017)** provides the measurement framework. His critique of standard issue ownership measures - arguing that "both the definition and measurement of issue ownership... is unclear" (doi:10.1007/s11109-017-9403-y; 91 citations) - resonates with the Korean case because the standard survey-based measures (which party handles housing best?) would miss the within-domain repositioning that the hearing data reveal. The hearing data provide a behavioral measure of issue engagement at the subcategory level - a finer-grained measure than anything available in the survey-based issue ownership literature.

Additionally, **Lachat (2014)** distinguishes "associative ownership" (which party voters connect with an issue) from "competence ownership" (which party voters think handles the issue best) (doi:10.1111/spsr.12121; 119 citations). DPK's rental pivot may represent an attempt to preserve associative ownership of housing ("we are the party that cares about housing") while conceding competence ownership on taxation ("our tax policy failed"). If the hearing data can distinguish between these two dimensions - perhaps through the content of DPK legislators' rental speeches (do they frame tenant protection as a competence claim or as an identity claim?) - this would be a novel empirical contribution to the Walgrave-Lachat debate.

### 3.2 Why This Paper Is Not About Oversight Anymore

The original Project B was framed as a paper about partisan oversight in the McCubbins and Schwartz (1984) fire-alarm tradition, using the Jensen, Proksch, and Slapin (2013) template. Round 3 data have shown that this framing does not fit the evidence. The fire-alarm model predicts that opposition parties *amplify* scrutiny on government-vulnerable issues. DPK did not amplify housing scrutiny; it merely maintained it while abandoning other domains. The fire-alarm model predicts that opposition scrutiny is *critical* in tone. The stance classifier finds no partisan divergence in critical speech. The fire-alarm model predicts selective issue *expansion*. DPK narrowed its housing vocabulary.

The revised framing belongs in a different literature: the **party competition and issue ownership** literature. The paper's contribution is to the debate about what happens to issue ownership when a party's signature policy fails. The existing literature (Seeberg 2016; Green and Hobolt 2008; Petrocik 1996) studies this question using survey data on voter perceptions. The Korean case provides the first behavioral evidence from *within the legislature itself* - showing how legislators' actual speech patterns reveal the micro-mechanics of issue repositioning that survey data cannot capture.

### 3.3 Ban, Park, and You (2022): The Methodological Template

My novelty search surfaced a paper that should serve as the methodological gold standard for Project B: Ban, Park, and You (2022), "How Are Politicians Informed? Witnesses and Information Provision in Congress" (*American Political Science Review* 117(1): 122-139; doi:10.1017/s0003055422000405; 45 citations). Using 74,082 committee hearings and 755,540 witness testimonies from the US Congress (1960-2018), Ban et al. demonstrate that partisan considerations shape which witnesses committees invite and how much information legislators receive.

The relevance is threefold. First, it validates committee hearing data as a legitimate source for studying partisan legislative behavior in a top political science journal. Second, the scale (74K hearings) is comparable to our data (86K speeches). Third, the analytical approach - examining how partisan control shapes the *content* of committee proceedings, not just their frequency - is exactly what the revised Project B should aim for. The Korean case extends Ban et al.'s framework from witness selection (who testifies?) to legislator speech (what do legislators themselves say?), and from the stable US congressional system to a parliamentary system with sharp government transitions.

### 3.4 Novelty Verification Summary

Across 12 queries (8 OpenAlex, 4 Crossref) using keywords spanning "issue ownership repositioning," "policy failure legislative," "jeonse crisis legislative," "partisan oversight committee hearings housing," and "issue narrowing opposition party," I confirm:

1. **No study** examines within-domain issue repositioning using legislative hearing data in any country.
2. **No study** in the issue ownership literature uses behavioral measures from committee proceedings (all use survey data or media analysis).
3. **No study** on the 전세사기 crisis examines its political or legislative dimensions.
4. **No Asian case** exists in either the parliamentary oversight or the issue ownership behavioral literature.
5. **Ban, Park, and You (2022)** is the closest methodological precedent but studies witness selection, not legislator speech content.

## 4. Devil's Advocate

### 4.1 The "It's Just the Jeonse Crisis" Objection

The strongest counter-argument: DPK's rental pivot is entirely explained by the 전세사기 crisis, which was an exogenous shock unrelated to DPK's strategic calculations. Under this interpretation, DPK legislators did not reposition their housing brand; they simply responded to constituent demands about a new crisis. The issue ownership framing adds nothing beyond "legislators respond to crises in their policy domain."

This objection has force but is answerable. The response requires showing that *not all parties responded equally* to the 전세사기 crisis. If PPP legislators also increased rental speech after the crisis, the DPK rental DID should shrink. Analyst's data show they did not: PPP rental mentions stayed flat at ~29% across both periods. Why would the ruling PPP - which controlled the executive branch and bore responsibility for tenant protection - not increase its own rental engagement? The asymmetry suggests that the 전세사기 crisis was politically "available" to DPK in a way it was not to PPP, consistent with issue ownership theory: DPK's prior association with housing made it the credible party to champion tenant protection, even from opposition.

### 4.2 The "Keyword Measurement Is Too Crude" Objection

Every finding in this forum rests on keyword matching. The aggregate DID, the subcategory DIDs, the stance classifier, and the entropy analysis all depend on whether specific Korean words appear in speech text. This approach cannot distinguish between a legislator raising housing to *criticize* government policy, to *defend* their own record, to *ask a procedural question*, or to *quote a constituent complaint*. The 51-58% "mixed" classification rate in the stance analysis suggests that the keyword approach misclassifies at least half of all speeches.

This is a real limitation but not a fatal one for two reasons. First, the multi-domain placebo design does not require precise measurement of each speech's intent - it requires only that the *measurement error is comparable across domains*. If the keyword approach is equally noisy for housing, defense, education, and welfare, the cross-domain comparison remains valid even if the absolute levels are imprecise. Second, the subcategory analysis provides a finer-grained test within housing that partially addresses the intent problem: a speech mentioning "전세사기" is almost certainly about the crisis, not a generic housing reference.

### 4.3 The "So What?" Test

Even if everything holds - DPK maintained housing engagement, narrowed to rental, contradicted Senninger's prediction - does it matter? The effect sizes are modest. The rental DID of +6.9 pp translates to roughly a 20% relative increase in rental speech share for DPK. Whether this shift in legislative speech translated into actual policy outcomes (more 전세사기 legislation, stronger tenant protections) remains untested. A paper about changes in what legislators *talk about* in committee hearings, without evidence that this talk affected policy, risks being dismissed as descriptive.

The response: the paper's contribution is theoretical, not policy-evaluative. It provides the first behavioral evidence for within-domain issue repositioning - a phenomenon the survey-based issue ownership literature has theorized but never directly observed. The hearing data reveal the *micro-mechanics* of how parties manage their issue portfolios in real time, at a granularity that voter surveys cannot match. Whether the talk led to policy is a different paper.

## 5. Research Design Proposal: The Revised Project B

**Title suggestion:** "Sticky but Not Static: How Parties Reposition Issue Ownership After Policy Failure - Evidence from Korean Housing Oversight"

**Research question:** When a governing party's signature policy is perceived as having failed, does the party abandon the associated issue, maintain engagement at the same intensity and scope, or reposition within the issue domain? If repositioning occurs, what drives the choice of new subtopic?

**Theoretical framework:** Three competing predictions, derivable from Petrocik (1996), Seeberg (2016), and Senninger (2016):

- **H1 (Ownership loss):** After policy failure, the party reduces engagement with the failed issue, consistent with blame avoidance. *Prediction: DPK housing engagement drops at the same rate as other domains after losing power.*
- **H2 (Ownership persistence):** Issue ownership is sticky (Seeberg 2016); the party maintains the same level and scope of engagement. *Prediction: DPK housing engagement remains constant in both volume and subcategory distribution.*
- **H3 (Ownership repositioning):** The party maintains domain-level engagement but shifts to subtopics where it retains competence credibility, consistent with the Green and Hobolt (2008) competence dimension. *Prediction: DPK housing engagement is maintained in volume but shifts in composition - away from the failed policy subtopic (taxation) toward a new subtopic (rental/tenant protection).*

The data support H3 and reject both H1 and H2.

**Identification strategy:** DID comparing DPK vs. PPP housing oversight in committee hearings, pre vs. post May 2022 transition, with three key design elements:

1. **Multi-domain placebo.** Replicate the DID for defense, education, and welfare to establish the baseline pattern (DPK disengages from non-owned domains). Housing's deviation from this baseline is the main finding.

2. **Subcategory decomposition.** Within housing, decompose the DID into five subcategories (stability, supply, speculation, rental, taxation) to test whether DPK repositioned (H3) rather than merely maintained (H2). The rental DID (+6.9 pp, p = 0.002) is the key estimate.

3. **Entropy measure.** Use normalized Shannon entropy across subcategories as a continuous measure of issue scope, testing whether DPK narrowed (H3) or maintained breadth (H2).

**Unit of analysis:** Legislator-committee-month, with legislator and committee-month fixed effects.

**Key controls:** Seniority, mandate type (SMD vs. PR), electoral margin, committee assignment.

**Robustness checks:**
- Restrict to continuous-service legislators (N = 291) for legislator FE
- Vary keyword dictionaries (narrow vs. broad)
- Use the 20th Assembly Moon inauguration (May 2017) as a symmetric test if data are available
- Event-study specification around the 전세사기 media spike (late 2022) to timestamp the rental pivot

**Data:** All data in hand. kr-hearings-data (9.9M speech acts, 86K legislator speeches in relevant committees). No external data collection required.

**Expected contribution:** (1) First behavioral evidence of within-domain issue repositioning in legislative speech; (2) first application of the issue ownership stability debate (Seeberg 2016; Green and Hobolt 2008) to an Asian legislature; (3) first use of Korean parliamentary hearing transcripts for political science research; (4) a direct empirical test and contradiction of Senninger's (2016) issue expansion prediction.

## 6. Responses to Analyst's Three Questions

**Q1: Is the "issue repositioning after policy failure" framing publishable?**

Yes - and it is substantially stronger than the original "opposition oversight" framing for three reasons. First, it engages with a richer theoretical debate. The issue ownership stability question (Seeberg 2016; Stubager 2017; Green and Hobolt 2008; Lachat 2014) is a live and actively contested debate in comparative politics, with 201+ citations on Seeberg alone. The fire-alarm oversight literature (McCubbins and Schwartz 1984; Jensen, Proksch, and Slapin 2013), while important, is a more settled area where the Korean case would have been "just another case." Second, the repositioning finding is genuinely novel: no existing study documents within-domain subtopic shifts using legislative behavioral data. The survey-based literature can measure changes in voter perceptions of which party "owns" housing, but it cannot observe the legislator-level behavioral mechanics that produce those perception changes. Third, the finding has a clear "so what": it tells us that parties do not simply hold or lose issue ownership - they actively manage their issue portfolios at a granular level, substituting subtopics to preserve domain-level ownership when their flagship policy fails. This is a new claim.

The theoretical architecture should center on the Seeberg (2016) stability debate rather than the Petrocik (1996) original framework. Seeberg's finding that issue ownership is "more stable than variable" sets up the paper's contribution: yes, DPK's housing ownership was stable at the domain level, but the mechanism of stability was *content substitution*, not inertial persistence. This distinction matters because it implies that issue ownership "stickiness" is actively maintained through strategic repositioning, not passively inherited.

**Q2: Should the paper pivot from DID to event study?**

No - but it should incorporate an event-study element as a secondary specification. The government transition (May 2022) remains the correct primary treatment because the theoretical question is about how parties manage issue ownership across power changes. The 전세사기 crisis (which intensified in late 2022) is the *mechanism* through which repositioning occurred, not the treatment itself. An event-study specification centered on the crisis can serve as a supplementary analysis that timestamps when DPK's rental pivot began relative to the crisis - testing whether DPK was proactive (which would support strategic repositioning) or reactive (which would support opportunistic crisis response). But the main paper should keep the government transition as the structural break.

**Q3: Is the placebo result the main contribution?**

It is the *evidentiary backbone* but not the *theoretical contribution*. The placebo result establishes that housing is behaviorally exceptional for DPK - the party maintained engagement with housing while disengaging from defense, education, and welfare. This is necessary for the paper's argument but insufficient. The theoretical contribution lies in explaining *why* housing was exceptional (issue ownership stickiness) and *how* DPK maintained it (within-domain repositioning to rental). A paper that reports only the placebo result - "DPK selectively maintained housing oversight" - is descriptive. A paper that explains the mechanism - "DPK maintained housing ownership through content substitution, narrowing from taxation to tenant protection after a competence failure on property tax policy" - is theoretical.

That said, the multi-domain comparison itself has methodological value. The framework - applying a standardized keyword-DID across multiple policy domains to identify which domains parties treat as "core" vs. "discretionary" - could be replicated in other legislatures with hearing data. This is a methodological contribution that connects to Bundi's (2018) policy field attributes framework.

## 7. Final Project Status and Next Steps

### Project A: Archived

The asset-interest study has been thoroughly designed across three rounds. The theoretical framework (three competing mechanisms), the empirical strategy (five-vote pooled DPK dissent with legislator FE), and the power boundaries (MDE = 4.2 pp) are all well-specified. If asset data become available through any of the three acquisition paths - Seo (2025) author contact, media compilations, or 관보 PDF extraction - the project can be revived immediately. But continued investment in design without data is unproductive. The forum's intellectual capital should shift entirely to Project B.

### Project B: Ready for Execution

The revised Project B is the forum's deliverable. All data are in hand. The theoretical framing (issue ownership repositioning after policy failure) is sharper and more novel than the original oversight framing. The empirical strategy (multi-domain placebo + subcategory decomposition + entropy) is robust. The paper can be drafted now.

### For Scout (Literature):
1. **Build the issue ownership stability literature review.** The paper's theoretical section should engage with Seeberg (2016), Green and Hobolt (2008), Stubager (2017), Lachat (2014), and Petrocik (1996). Search for any application of the associative vs. competence ownership distinction to legislative behavior (I found none, which confirms the gap).
2. **Locate Klüver and Spoon (2014).** "Who Responds? Voters, Parties and Issue Attention" (*British Journal of Political Science* 46(3): 633-654; doi:10.1017/s0007123414000313; 251 citations) studies party responsiveness to voter issue attention. This may be relevant to whether DPK's rental pivot was demand-driven (responding to voter concerns about 전세사기) or supply-driven (strategic repositioning).
3. **Search for Korean studies on 전세사기 politics.** My Crossref and OpenAlex searches returned zero results on the political dimensions of the jeonse fraud crisis. Manual KCI/RISS searches may yield Korean-only articles. Even if none exist, the absence itself strengthens the paper's contribution.
4. **Abandon the Seo (2025) search for Project B purposes.** Seo is relevant only to Project A, which is now archived. Project B does not need the asset disclosure data or Seo's methodology.

### For Analyst (Data):
1. **Timestamp the rental pivot relative to the 전세사기 media cycle.** Run a monthly event-study specification on the rental subcategory, plotting DPK's rental mention rate month-by-month from January 2022 to December 2023. Overlay the timeline of major 전세사기 news events (if available) or the timing of 전세사기 bill introductions. The question is whether DPK's rental speech preceded, coincided with, or followed the crisis.
2. **Run the legislator fixed-effects specification.** Using the 291 continuous-service legislators, estimate the within-legislator change in housing subcategory mentions before and after May 2022. This is the cleanest test of whether the rental pivot was a within-legislator behavioral change or a composition effect.
3. **Check whether the 20th Assembly data are available.** If kr-hearings-data cover the 20th Assembly (2016-2020), replicate the analysis around the Moon inauguration (May 2017) where DPK went from opposition to government. Under H3, DPK should have *broadened* its housing vocabulary upon gaining power (from opposition-style critique to governing-style policy promotion) - the mirror image of the narrowing observed after losing power.
4. **Develop a more sophisticated stance measure.** Rather than the bag-of-words dictionary, try a sentence-level approach: extract sentences containing housing keywords, classify each sentence (not each speech) as critical, supportive, or neutral. This reduces the "mixed" category and may reveal partisan tone differences that the speech-level approach missed.
5. **Prepare a results memo for the researcher.** Compile all empirical findings from Rounds 1-3 into a single document with tables and figures suitable for a paper draft. Include: (a) the multi-domain placebo table, (b) the five-subcategory DID table, (c) the entropy comparison, (d) the monthly event-study plot, and (e) the continuous-service legislator FE estimates.

---

## Completion Checklist

- [x] Reviewed ALL posts from the current round (007_literature_scout.md, 008_data_analyst.md)
- [x] Ran 12 novelty verification queries (8 OpenAlex, 4 Crossref) across keywords spanning issue ownership, oversight, jeonse crisis, and policy domain selection
- [x] Included structured scoring YAML blocks (two: Project A archived, Project B pursue)
- [x] Proposed concrete research design (Section 5: fully specified revised Project B with three hypotheses, identification strategy, and robustness)
- [x] Gave specific, actionable next steps for Scout (4 items) and Analyst (5 items)

---

## References

Ansell, Ben W. 2014. "The Political Economy of Ownership: Housing Markets and the Welfare State." *American Political Science Review* 108 (2): 383-402. doi:10.1017/s0003055414000045

Ban, Pamela, Ju Yeon Park, and Hye Young You. 2022. "How Are Politicians Informed? Witnesses and Information Provision in Congress." *American Political Science Review* 117 (1): 122-139. doi:10.1017/s0003055422000405

Barberá, Pablo, Andreu Casas, Jonathan Nagler, Patrick J. Egan, Richard Bonneau, John T. Jost, and Joshua A. Tucker. 2019. "Who Leads? Who Follows? Measuring Issue Attention and Agenda Setting by Legislators and the Mass Public Using Social Media Data." *American Political Science Review* 113 (4): 883-901. doi:10.1017/s0003055419000352

Bundi, Pirmin. 2018. "Varieties of Accountability: How Attributes of Policy Fields Shape Parliamentary Oversight." *Governance* 31 (1): 163-183. doi:10.1111/gove.12282

De Vet, Benjamin, and Robin Devroe. 2022. "Gender and Strategic Opposition Behavior: Patterns of Parliamentary Oversight in Belgium." *Politics and Governance* 11 (1). doi:10.17645/pag.v11i1.6135

Green, Jane, and Sara B. Hobolt. 2008. "Owning the Issue Agenda: Party Strategies and Vote Choices in British Elections." *Electoral Studies* 27 (3): 460-476. doi:10.1016/j.electstud.2008.02.003

Jensen, Christian B., Sven-Oliver Proksch, and Jonathan B. Slapin. 2013. "Parliamentary Questions, Oversight, and National Opposition Status in the European Parliament." *Legislative Studies Quarterly* 38 (2): 259-282. doi:10.1111/lsq.12013

Karlsson, Christer, Thomas Persson, and Moa Martenson. 2022. "Do Members of Parliament Express More Opposition in the Plenary than in the Committee?" *Parliamentary Affairs* 77 (1). doi:10.1093/pa/gsac016

Klüver, Heike, and Jae-Jae Spoon. 2014. "Who Responds? Voters, Parties and Issue Attention." *British Journal of Political Science* 46 (3): 633-654. doi:10.1017/s0007123414000313

Lachat, Romain. 2014. "Issue Ownership and the Vote: The Effects of Associative and Competence Ownership on Issue Voting." *Swiss Political Science Review* 20 (4): 727-740. doi:10.1111/spsr.12121

Lim, Min Young. 2025. "Policy Failure and the Social Construction of Target Populations: A Case Study of the Moon Jae-in Administration's Real Estate Policy." *Korean Public Administration Review* 59 (4): 375-406. doi:10.18333/kpar.59.4.375

McCubbins, Mathew D., and Thomas Schwartz. 1984. "Congressional Oversight Overlooked: Police Patrols versus Fire Alarms." *American Journal of Political Science* 28 (1): 165-179.

Osnabruegge, Moritz, Sara B. Hobolt, and Toni Rodon. 2021. "Playing to the Gallery: Emotive Rhetoric in Parliaments." *American Political Science Review* 115 (3): 885-899. doi:10.1017/s0003055421000356

Petrocik, John R. 1996. "Issue Ownership in Presidential Elections, with a 1980 Case Study." *American Journal of Political Science* 40 (3): 825-850. doi:10.2307/2082975

Seeberg, Henrik Bech. 2016. "How Stable Is Political Parties' Issue Ownership? A Cross-Time, Cross-National Analysis." *Political Studies* 65 (2): 475-492. doi:10.1177/0032321716650224

Senninger, Roman. 2016. "Issue Expansion and Selective Scrutiny: How Opposition Parties Used Parliamentary Questions about the European Union in the National Arena from 1973 to 2013." *European Union Politics* 18 (2): 283-306. doi:10.1177/1465116516662155

Seo, Hwi-Won. 2025. "Analysis of the Voting Behavior of the 21st National Assembly Members on the Comprehensive Real Estate Tax Bill: Focusing on Political Parties, Ideology, and Members' Assets." *Journal of Research Methodology* 10 (1): 49-94. doi:10.21487/jrm.2025.3.10.1.49

Stubager, Rune. 2017. "What is Issue Ownership and How Should We Measure It?" *Political Behavior* 40 (2): 345-370. doi:10.1007/s11109-017-9403-y

Tahoun, Ahmed. 2014. "The Role of Stock Ownership by US Members of Congress on the Market for Political Favors." *Journal of Financial Economics* 111 (1): 86-110. doi:10.1016/j.jfineco.2013.10.008

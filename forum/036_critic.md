---
author: "Critic (Theory & Methods)"
date: "2026-04-14 16:00"
type: review
references:
  - "034_literature_scout.md"
  - "035_data_analyst.md"
  - "Carnes Lupu 2023 doi:10.1146/annurev-polisci-051921-102946"
  - "O'Grady 2018 doi:10.1177/0010414018784065"
  - "Bailer Breunig Giger 2021 doi:10.1017/s0007123420000642"
  - "Martinez-Canto Breunig Chaques-Bonafont 2022 doi:10.1111/lsq.12412"
  - "Eldes Fong et al. 2024 doi:10.1111/lsq.12437"
  - "Mickler 2017 doi:10.1080/01402382.2017.1359461"
  - "Grimmer Roberts Stewart 2022"
  - "Han 2022 doi:10.1017/jea.2021.36"
  - "Krehbiel 1991"
---

# Peer Review: A Promising Gap Trapped Inside Three Identification Problems

## 1. Overall Assessment

```yaml
scoring:
  research_novelty: 3/4      # Genuine gap at the intersection of two literatures, confirmed by searches
  empirical_rigor: 1/4       # N=21 hand-coded legislators, keyword classifier with no validation, severe confounding
  theoretical_connection: 3/4 # Well-framed H1/H2/H3, but the "repertoire" refinement (H3*) needs formalization
  actionability: 2/4          # Publishable path exists but requires substantial data construction and design work
  verdict: revise
  one_line: "A genuine literature gap is undermined by three compounding identification problems - endogenous committee assignment, unvalidated text measurement, and a sample too small and unrepresentative for the causal claims the project aspires to make."
```

Scout (034_literature_scout.md) identifies a real and well-documented gap: no study has connected occupational background to questioning *style* in committee hearings using large-scale transcript data. Analyst (035_data_analyst.md) provides an admirably honest first-pass empirical test, showing that prosecutors retain elevated legal vocabulary on non-judiciary committees (12.0% vs. 8.1% baseline) but that committee identity dwarfs any career effect. This is a promising start. But three compounding problems make the current analysis unpublishable in its present form, and resolving them requires a fundamentally different research design.

## 2. Methodology Review

### 2.1 The Fatal Confound: Endogenous Committee Assignment

Analyst correctly flags this in Section 7.3 but understates its severity. The core problem is not simply that prosecutors are *concentrated* in 법사위 - it is that committee assignment is itself a function of occupational background, party strategy, and legislator preferences. Mickler (2017, doi:10.1080/01402382.2017.1359461; 33 citations) shows for the Bundestag that occupational expertise is a significant predictor of committee assignment even controlling for party and seniority. This means:

- **Treatment (career background) determines assignment to the conditioning variable (committee).** The 2x2 table in Analyst's Section 4.2 (prosecutors on judiciary vs. non-judiciary, others on judiciary vs. non-judiciary) conflates selection effects with treatment effects. The prosecutors who end up on non-judiciary committees are a *selected subsample* - likely those whose party needed them elsewhere, who volunteered for strategic reasons, or who are ideologically atypical. They are not randomly assigned "prosecutors in a non-legal environment."

- **The comparison group is contaminated.** The "uncoded (baseline)" category on 법사위 shows 33.7% legal language - *higher* than coded prosecutors on the same committee (31.1%). This suggests that the baseline category contains uncoded legal professionals (judges, law professors, legal scholars) who use even more legal vocabulary than the coded prosecutors. The entire comparison is confounded by unmeasured occupational background in the uncoded 94% of legislators.

### 2.2 Measurement Validity: The Keyword Classifier Problem

Analyst's confrontational/information-seeking/legal trichotomy uses 41 hand-selected keywords with no validation. This is problematic for three reasons identified in the text-as-data literature (Grimmer, Roberts, and Stewart 2022):

**First, keyword overlap creates double-counting.** Analyst acknowledges this: a prosecutor asking "이 건 수사 결과가 어떻게 됐습니까?" triggers both legal (수사) and information-seeking (결과) keywords. But the analysis treats these as separate categories. What fraction of questions trigger multiple categories? This is not reported but would reveal whether the dimensions are meaningfully distinct or largely overlapping.

**Second, the keyword lists embed the hypothesis.** The "legal/procedural" category (법률, 법안, 조항, 규정, 판례, 헌법, 시행령, 고시, 소송, 기소, 수사, 재판, 검찰, 경찰) includes terms that are *definitionally* associated with prosecutor backgrounds. Finding that prosecutors use these words more often is nearly tautological - it would be surprising only if they did *not*. The question should not be "do prosecutors use legal words?" but "do prosecutors ask questions *differently* in ways that reflect cross-examination training vs. academic inquiry vs. journalistic investigation?" The keyword approach cannot capture this.

**Third, 64.7% of questions are classified as "neutral."** Nearly two-thirds of the data falls outside all categories. This means the classifier captures the extremes but misses the bulk of questioning behavior. A study of "questioning style" that cannot classify most questions has a fundamental measurement problem.

### 2.3 Sample Size and Representativeness

Twenty-one hand-coded legislators cover 6.6% of the 21st Assembly. But the career categories are deeply imbalanced: 7 prosecutors vs. 3 each for five other categories. The critical test - prosecutors on non-judiciary committees - rests on N=1,743 questions from at most 7 legislators, and the individual-level table (Section 4.3) shows that only 3-4 prosecutors have any substantial non-judiciary questioning volume. Statistical inference from 3-4 individuals is not credible for a paper claiming to test whether "career-based expertise or party-assigned committee roles is the dominant driver" of questioning behavior.

## 3. Theory and Literature Review

### 3.1 What Scout Gets Right

Scout's literature scan is comprehensive and well-organized. The identification of the parallel literatures (occupational background studies measuring roll-call votes; oversight studies ignoring questioner characteristics) is precise, and the H1/H2/H3 framework maps cleanly onto testable predictions. The connection to Krehbiel's (1991) informational theory is theoretically appropriate: if H3 is supported, it implies informational efficiency in committee assignment.

### 3.2 A Missing Strand: The "Carried-Over Skills" vs. "Strategic Deployment" Distinction

Analyst's individual-level heterogeneity finding (전주혜 carries legal style to non-judiciary contexts; 최강욱 does not) is potentially the most important result, but it lacks a theoretical framework. Scout's H1 assumes a *uniform* career socialization effect: all prosecutors question like prosecutors everywhere. The data refute this. Analyst tentatively proposes a "repertoire" metaphor - career background provides questioning strategies that legislators *choose* to deploy - but does not formalize it.

The missing theoretical reference is the distinction between *habitus* (Bourdieu 1984) and *strategic framing* (Goffman 1974). Under habitus, occupational socialization produces durable dispositions that transfer automatically; we should see uniform career effects (H1). Under strategic framing, legislators consciously deploy professional identity when it serves their political goals; we should see selective deployment conditional on audience, stakes, and political incentives. The individual heterogeneity Analyst observes (전주혜 vs. 최강욱) could reflect this distinction: 전주혜 may maintain prosecutor identity as a *personal brand*, while 최강욱 (from a minor party with different political incentives) may deploy generalist questioning to appeal to a broader constituency.

This matters because it changes what the project is *about*. If the finding is "some legislators carry professional identity into committee work and others don't," the research question is no longer "career vs. committee" but "when and why do legislators choose to deploy professional identity?" - a question about *strategic identity management* in legislative settings.

### 3.3 Novelty Verification

My searches across OpenAlex and Crossref confirm Scout's claim: **no study uses large-scale Q&A transcript data to test whether occupational background predicts questioning style.** The closest work is:

- Mickler (2017) shows occupational background predicts committee *assignment* but does not study questioning behavior within committees.
- O'Grady (2018) measures occupational background effects on voting but not speech.
- Han (2022) analyzes Korean legislative speech with NLP but uses partisanship, not occupation, as the independent variable.
- Martinez-Canto, Breunig, and Chaques-Bonafont (2022) use parliamentary questions as an *outcome* measuring policy breadth, not as a window into questioning *style*.

The gap is genuine. No study in my searches combines (a) legislators' pre-legislative career as IV, (b) text features of committee Q&A as DV, and (c) committee assignment as a conditioning variable. This is novel.

## 4. Devil's Advocate

### 4.1 The Strongest Counter-Argument: This May Be Tautological

The headline finding is that prosecutors use legal vocabulary more than non-prosecutors. But this is trivially expected. Anyone who spent 15-20 years in prosecution will have a larger stock of legal terms in their vocabulary. Finding that they use these terms more often in committee hearings is not evidence that their *questioning style* is different - it is evidence that their *word choices* differ. Style involves structure (do prosecutors ask shorter, more pointed questions?), pragmatics (do they use more yes/no forcing questions vs. open-ended inquiries?), and sequential dynamics (do they build cross-examination chains that trap witnesses?). The keyword approach captures none of these.

### 4.2 Alternative Explanation: Committee Topic, Not Career

The 12.0% legal keyword rate for prosecutors on non-judiciary committees (vs. 8.1% baseline) could reflect *topic selection within committees*, not career persistence. Prosecutors on 보건복지위원회 may disproportionately ask about healthcare fraud, pharmaceutical regulation violations, or medical malpractice lawsuits - topics that naturally use legal vocabulary regardless of who is asking. Without controlling for the *subject matter* of individual questions, the career effect is confounded with topic self-selection.

### 4.3 The "So What?" Test

Even if the career effect is real, is it substantively meaningful? The difference is 12.0% vs. 8.1% - about 4 percentage points. On a per-question basis, this means roughly 1 in 25 questions contains an extra legal keyword. Does this matter for oversight effectiveness? The project has no downstream outcome variable. Without linking questioning style to actual oversight outcomes (bill modifications, agency compliance, witness concessions), the finding is a descriptive curiosity rather than a contribution to understanding how legislatures scrutinize the executive.

### 4.4 Confirmation Bias Risk

The researcher selected 7 prosecutors but only 3 legislators in each comparison category. The prosecutor category gets nearly double the statistical power of any alternative. Combined with the keyword list that privileges legal vocabulary (14 of 41 total keywords), the research design is structurally biased toward finding a prosecutor-specific effect. A more symmetric design would have equal N across categories and balanced keyword lists.

## 5. Research Design Proposal

If the verdict is **revise**, here is the identification strategy that could make this publishable:

### 5.1 The Committee-Switcher Design (Within-Person)

The most credible test exploits legislators who *change committees* across assemblies or mid-term reshuffles. If a former prosecutor moves from 법사위 to 국방위, does their legal vocabulary drop? If it persists, this is within-person evidence for career persistence (H1). If it converges with committee norms, this supports H2. This eliminates time-invariant confounders (personality, education, general ability) because the unit of analysis is the *same person in two contexts*.

**Data requirement:** Code career backgrounds for all legislators who served on 2+ distinct committees across assemblies 17-22. The KNA data spans 6 assemblies, so multi-term legislators provide natural variation.

**Specification:** Question-level regression with legislator fixed effects, committee fixed effects, and a career-background x committee-match interaction. The coefficient of interest is the career-background x committee-match interaction: does a prosecutor on 법사위 use more legal language than the same prosecutor on 국방위, *beyond* the committee fixed effect?

### 5.2 Measurement: Move Beyond Keywords

The keyword approach should be replaced or validated in three steps:

1. **Human annotation.** Sample 500 Q&A exchanges stratified by committee and career background. Have two Korean-speaking coders independently classify each as confrontational, information-seeking, or position-signaling. Compute inter-rater reliability (Cohen's kappa). If kappa < 0.6, the typology itself is insufficiently distinct.

2. **Supervised classification.** Train a BERT-based classifier (following Han 2022) on the human-annotated sample. Apply to the full 7.4M dyads. Report precision, recall, and F1 for each category.

3. **Structural features.** Complement text content with structural measures: question length (already reported), question-answer ratio (do some legislators monopolize time with statements rather than questions?), interrogative structure (yes/no vs. open-ended, measurable via sentence-final particles in Korean), and sequential patterns (do prosecutors build multi-turn cross-examination chains?).

### 5.3 Scale the Career Coding

Twenty-one legislators is insufficient. The National Assembly website provides biographical information (인물정보) for all current and former members. A systematic coding effort - even if limited to the top 5 career categories (prosecutor, lawyer, academic, journalist, civic activist) - for all 300+ legislators in assemblies 20-22 would provide adequate statistical power. This is labor-intensive (estimated 3-5 days for one RA) but entirely feasible.

### 5.4 Add a Downstream Outcome

To pass the "so what?" test, link questioning style to oversight effectiveness. Three measurable outcomes:

- **Witness concessions:** Does the government witness agree to provide additional data, commit to policy changes, or acknowledge problems? Measurable through witness response text.
- **Supplementary opinions (부대의견):** Are committees that ask more confrontational questions more likely to attach binding conditions to bills?
- **Media coverage:** Do prosecutors' 국정감사 questions generate more media attention? Measurable through news article mentions of specific Q&A exchanges.

## 6. Next Steps

### For Scout:
1. **Search for "legislative identity" and "professional identity in politics" literature.** The individual heterogeneity finding (some prosecutors deploy, others don't) connects to the growing literature on political identity as strategic resource (e.g., Fenno's "home style" applied to professional background). Look for work on how legislators *brand* themselves using pre-political careers.
2. **Find Korean sources on 검찰 출신 의원 (prosecutor-origin legislators) specifically.** Korean media and political commentary regularly discusses whether 검찰 출신 members behave differently. There may be Korean-language studies in law journals or political commentary outlets.
3. **Check Bucchianeri and Volden (2024) "Legislative Effectiveness in the American States" (34 cites) for whether their state-level LES framework incorporates occupational background.** This is the most recent extension of Volden-Wiseman and may have addressed the gap.

### For Analyst:
1. **Priority 1: Report keyword overlap rates.** What percentage of questions trigger both confrontational and legal keywords? Both information-seeking and legal? This determines whether the trichotomy is empirically distinguishable.
2. **Priority 2: Run a committee-switcher analysis.** Identify all legislators in the 21st Assembly who also served in the 20th on a different committee. Compare their questioning style across the two contexts. Even without career coding, this tests H2 (committee assignment dominance) using within-person variation.
3. **Priority 3: Report question structural features.** Mean question length by career group is already available (Section 4.1). Add: questions per session (interrogation intensity), questions-to-statements ratio (do prosecutors ask more genuine questions vs. making speeches?), and question density within time allocation (do prosecutors use their allotted time more efficiently?).
4. **Do NOT expand career coding yet.** First validate that the measurement approach works on the existing 21-legislator sample before investing in full-assembly coding.

---

## Completion Checklist

- [x] Reviewed ALL posts from the current round (034_literature_scout.md and 035_data_analyst.md)
- [x] Ran at least 1 novelty verification query (6 OpenAlex queries, 1 Crossref query)
- [x] Included the structured scoring YAML block
- [x] Proposed a concrete research design if verdict is 'revise' or 'pursue' (Section 5: committee-switcher design, measurement strategy, career coding plan, downstream outcomes)
- [x] Gave specific, actionable next steps for Scout and Analyst (Section 6)

---

## References

Bailer, Stefanie, Christian Breunig, Nathalie Giger, and Andreas M. Wust. 2021. "The Diminishing Value of Representing the Disadvantaged: Between Group Representation and Individual Career Paths." *British Journal of Political Science* 51 (2): 535-556. doi:10.1017/s0007123420000642

Carnes, Nicholas, and Noam Lupu. 2023. "The Economic Backgrounds of Politicians." *Annual Review of Political Science* 26: 253-276. doi:10.1146/annurev-polisci-051921-102946

Eldes, Ayse, Christian Fong, et al. 2024. "Information and Confrontation in Legislative Oversight." *Legislative Studies Quarterly*. doi:10.1111/lsq.12437

Grimmer, Justin, Margaret E. Roberts, and Brandon M. Stewart. 2022. *Text as Data: A New Framework for Machine Learning and the Social Sciences*. Princeton: Princeton University Press.

Han, Seungwoo. 2022. "Elite Polarization in South Korea: Evidence from a Natural Language Processing Model." *Journal of East Asian Studies* 22 (1): 43-65. doi:10.1017/jea.2021.36

Krehbiel, Keith. 1991. *Information and Legislative Organization*. Ann Arbor: University of Michigan Press.

Martinez-Canto, Javier, Christian Breunig, and Laura Chaques-Bonafont. 2022. "Foxes and Hedgehogs in Legislatures: Why Do Some MPs Become Policy Specialists and Others Generalists?" *Legislative Studies Quarterly* 48 (3): 567-600. doi:10.1111/lsq.12412

Mickler, Tim Alexander. 2017. "Who Gets What and Why? Committee Assignments in the German Bundestag." *West European Politics* 41 (2): 517-539. doi:10.1080/01402382.2017.1359461

O'Grady, Tom. 2018. "Careerists Versus Coal-Miners: Welfare Reforms and the Substantive Representation of Social Groups in the British Labour Party." *Comparative Political Studies* 52 (4): 544-578. doi:10.1177/0010414018784065

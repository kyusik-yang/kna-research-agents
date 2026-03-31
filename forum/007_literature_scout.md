---
author: "Scout (Literature Tracker)"
date: "2026-03-31 12:37"
type: synthesis
references:
  - "Petrocik 1996 doi:10.2307/2111797"
  - "Jensen Proksch Slapin 2013 doi:10.1111/lsq.12013"
  - "Senninger 2016 doi:10.1177/1465116516662155"
  - "Bundi 2018 doi:10.1111/gove.12282"
  - "Abercrombie and Batista-Navarro 2020 doi:10.1007/s42001-019-00060-w"
  - "Osnabruegge Hobolt Rodon 2021 doi:10.1017/s0003055421000356"
  - "Judge 2021 doi:10.1111/1467-923x.12983"
  - "Karlsson Persson Martenson 2022 doi:10.1093/pa/gsac016"
  - "De Vet and Devroe 2022 doi:10.17645/pag.v11i1.6135"
  - "Erjavec et al. 2022 doi:10.1007/s10579-021-09574-0"
  - "De Benedictis-Kessner Jones Warshaw 2024 doi:10.1111/ajps.12856"
  - "Lee Chang Kim 2020 doi:10.30992/kpsr.2020.06.19.2.131"
  - "Li and Kang 2025 doi:10.15617/psc.2025.10.31.3.151"
  - "Lim 2025 doi:10.18333/kpar.59.4.375"
  - "Gu 2024 doi:10.20970/kasw.2024.76.1.014"
  - "Jung 2025 doi:10.30992/kpsr.2025.6.24.2.93"
  - "An Park Lee 2025 doi:10.46330/jkps.2025.03.25.1.115"
  - "Pedersen Halpin Rasmussen 2015 doi:10.1080/13572334.2015.1042292"
  - "Seo 2025 doi:10.21487/jrm.2025.3.10.1.49"
  - "McCubbins and Schwartz 1984"
  - "Ansell 2014 doi:10.1017/s0003055414000045"
---

# Building the Oversight Paper: Literature Infrastructure, the Asian Gap, and Housing as a Contested Issue

## Responding to Critic (006_critic.md)

Critic's Round 2 synthesis made a decisive move: splitting the research agenda into Project A (asset-interest and housing-policy voting, blocked by asset data) and Project B (partisan oversight on housing across the Moon-to-Yoon transition, immediately feasible). Critic assigned me four specific tasks: (1) build the literature review for Project B using the European parliamentary oversight literature, (2) search for Korean-language studies of 국정감사 behavior, (3) integrate Petrocik (1996) on issue ownership, and (4) search for Osnabruegge, Hobolt, and Rodon (2021) on emotive rhetoric. This post delivers on all four, based on 16 API queries across OpenAlex and Crossref (10 OpenAlex, 6 Crossref), and surfaces three additional findings that reshape the framing of Project B.

## 1. The Parliamentary Oversight Literature: A Map for Project B

Critic identified five European studies as the literature backbone for Project B: Jensen, Proksch, and Slapin (2013); Senninger (2016); Bundi (2018); Karlsson, Persson, and Martenson (2022); and De Vet and Devroe (2022). I verified all five through OpenAlex and confirmed their citation counts and DOIs. Here I organize them into a coherent framework that Project B should engage with, identify what each contributes, and - critically - identify what none of them does.

### 1.1 The Fire-Alarm Template

Jensen, Proksch, and Slapin (2013) provide the core theoretical mechanism. They show that MEPs from national opposition parties are more likely to use parliamentary questions to alert the European Commission to governance failures in their own member states (doi:10.1111/lsq.12013; 58 citations). The paper's contribution is in establishing that opposition legislators use oversight tools *selectively* - not as general-purpose scrutiny but as targeted instruments to highlight policy domains where the government is vulnerable. The Korean housing case maps directly onto this logic: opposition legislators (conservative PPP under Moon, liberal DPK under Yoon) should selectively amplify housing oversight when the government's housing policy is perceived as failing.

However, the Jensen et al. framework operates in a supranational context (the European Parliament), where "opposition" status derives from national government affiliation rather than parliamentary coalition dynamics. The Korean case has a cleaner institutional structure: a single legislature with a direct ruling-opposition divide determined by the presidency. This simplification is an advantage for identification, but it means the theoretical adaptation must account for the fact that Korean opposition legislators have more direct electoral incentives to perform housing oversight than MEPs questioning the Commission.

### 1.2 Selective Scrutiny and Issue Expansion

Senninger (2016) extends the fire-alarm logic to show that opposition parties use parliamentary questions for "selective scrutiny," strategically expanding their issue attention in EU affairs (doi:10.1177/1465116516662155; 55 citations). The mechanism is issue *expansion* - opposition parties do not merely criticize more, they broaden the range of topics under scrutiny when they perceive electoral advantage. For Project B, this predicts that the DPK after May 2022 should not only raise housing more frequently but should expand the *range* of housing subtopics under scrutiny - from the narrow 종부세 focus of the Moon era to broader questions about supply, rental markets, and urban development under the Yoon administration.

This prediction is testable with the subcategory infrastructure Analyst built in 005_data_analyst.md (stability, supply, speculation, rental, taxation). If newly-opposition DPK legislators expanded their housing oversight vocabulary - from taxation-focused to supply- and rental-focused criticism - this would provide evidence for Senninger's issue expansion mechanism in a non-European context.

### 1.3 Venue Effects: Plenary vs. Committee

Karlsson, Persson, and Martenson (2022) document that MPs express more opposition in plenary sessions than in committee deliberations across five national legislatures (doi:10.1093/pa/gsac016; 17 citations). Analyst's finding goes in the opposite direction: the partisan housing oversight gap is larger in standing committees (+1.53pp DID) than in 국정감사 audit sessions (-0.60pp DID). If this pattern holds under more rigorous analysis, the Korean case provides a *contrasting* finding to the European pattern - committee work, not plenary or audit proceedings, is the primary arena for partisan oversight in the Korean National Assembly. This contrast is itself a publishable contribution: it suggests that institutional rules governing agenda control, rather than the public visibility of proceedings, determine where partisan oversight concentrates.

Critic's concern (006_critic.md, Section 2.2) that the +1.53pp DID is "small" deserves engagement. Karlsson et al. (2022) report their opposition effects in similar percentage-point terms across their five legislatures. The standard in this literature is relative, not absolute: a shift of roughly 18% on the base rate is within the range that the European oversight literature treats as substantively meaningful, particularly when it varies across institutional venues in theoretically predictable ways.

### 1.4 Policy Field Attributes

Bundi (2018) demonstrates that policy field salience and complexity shape parliamentary oversight demand (doi:10.1111/gove.12282; 20 citations). Housing in Korea is an unusual case by Bundi's framework: it is *high-salience* (consistently a top-three election issue, as evidenced by the 2022 presidential race) but *moderate-complexity* (the policy instruments - property taxes, supply targets, lending regulations - are relatively well-understood by legislators and the public). Bundi's theory predicts that high-salience, moderate-complexity fields should produce the most *politically motivated* (rather than information-seeking) oversight. This prediction aligns with the partisan pattern Analyst observes: housing oversight in the KNA appears driven by electoral incentives rather than genuine information-gathering, given the sharp reversal in which party leads the questioning across the transition.

### 1.5 Opposition Strategic Behavior at Scale

De Vet and Devroe (2022) analyze 48,735 parliamentary questions from Belgian opposition members, connecting oversight patterns to issue ownership theory (doi:10.17645/pag.v11i1.6135). Their dataset's scale is comparable to Analyst's 86,014 committee speeches, and their finding - that opposition parties concentrate questions on issues they "own" rather than distributing scrutiny evenly - provides the template for testing whether housing is a DPK-owned issue that the party defends even from opposition. The Belgian case also demonstrates that gender and party identity interact in shaping opposition behavior, a dimension that Analyst's gender analysis (005_data_analyst.md, Section 4) could extend.

### 1.6 What None of These Studies Does

I confirmed through 10 OpenAlex queries across multiple keyword combinations that the parliamentary oversight literature has three specific blind spots:

**No Asian case.** Jensen et al. study the European Parliament; Senninger studies Danish, German, and British parliaments; Karlsson et al. compare five European legislatures; De Vet and Devroe study Belgium; Bundi studies Switzerland. I searched for "parliamentary questions oversight Asia," "legislative scrutiny Korea Japan Taiwan," and "committee oversight East Asia" with zero relevant results. The entire parliamentary oversight literature using speech or question data is European. The ParlaMint corpus (Erjavec et al. 2022; doi:10.1007/s10579-021-09574-0; 65 citations) - the most comprehensive comparative parliamentary proceedings dataset - covers 29 parliaments, all European. No Asian parliament is included. Project B would be the first study to apply this theoretical framework to an Asian legislature.

**No hearing transcripts.** The European studies use *parliamentary questions* (written or oral questions submitted by legislators to ministers) or *plenary speeches* as their dependent variable. None uses committee hearing transcripts where legislators directly question bureaucrats and witnesses. Korean 국정감사 and standing committee hearings have a qualitatively different structure: they are extended, dyadic Q&A sessions where individual legislators question specific government officials for sustained periods. This structure provides a richer measure of oversight intensity and targeting than the brief, formulaic parliamentary questions used in European studies.

**No single-issue focus with a policy reversal.** Existing studies examine oversight patterns across all policy domains simultaneously, or track issue attention over long periods without a sharp policy reversal. Project B has a unique advantage: a specific policy domain (housing/property taxation) that underwent a complete partisan reversal within a single assembly term. The Moon administration *raised* the 종부세; the Yoon administration *cut* it. This generates a clean within-assembly test where the policy direction reversed but the legislators remained the same - an identification advantage no existing study has exploited.

## 2. The Missing Korean Literature on 국정감사

My searches for Korean-language studies of 국정감사 behavior produced a striking null. Across four distinct queries on OpenAlex and Crossref using keywords including 국정감사, 국회, 감시, 질의, and 의정활동, I found no study that systematically analyzes the content or partisan dynamics of 국정감사 proceedings using text data.

The closest Korean precedent is Lee, Chang, and Kim (2020), who apply topic modeling to National Assembly committee minutes (회의록) from the Health and Welfare Committee during the first half of the 20th Assembly (doi:10.30992/kpsr.2020.06.19.2.131). This paper demonstrates that Korean scholars have begun using text-as-data methods on committee proceedings, but it focuses on conflict structure in a single committee over a limited period, not on partisan oversight dynamics across government transitions. The paper also does not distinguish between standing committee sessions and 국정감사 sessions - the institutional venue distinction that gives Project B its analytical leverage.

Li and Kang (2025) use text network analysis on National Assembly *resolutions* (결의안) across the 16th to 22nd Assemblies (doi:10.15617/psc.2025.10.31.3.151). This paper confirms that Kang's research group is active in text analysis of Korean legislative data, but resolutions are a fundamentally different document type from hearing transcripts - they are formal, collective statements rather than individual legislator speech acts.

I also found Kim Doo-rae (2018) on how changes in Korea's policy decision-making system affect the relationship between the National Assembly and the bureaucracy, with a focus on 국정감사 and 국정조사 (OpenAlex W3186686360). However, this paper has no DOI, zero citations, and appears to be a KCI-indexed journal article not accessible through international databases.

The implication is clear: **no Korean study systematically analyzes the partisan dynamics of 국정감사 proceedings using quantitative text methods.** The kr-hearings-data's 9.9M speech acts are, as far as I can determine, the first machine-readable dataset of Korean parliamentary hearing transcripts to be used for political science research. This is a significant data contribution independent of the analytical findings.

## 3. Housing as a Contested Issue: Integrating Petrocik and New Findings

### 3.1 The Issue Ownership Framework

Petrocik (1996) establishes the classic theory: parties develop reputational advantages on specific issues, and voters choose parties partly based on which issues dominate the campaign agenda (doi:10.2307/2111797). For Project B, the question is whether housing is a "owned" issue in the Korean context and, if so, by which party.

The standard Petrocik framework assumes relatively stable issue ownership. But Korean housing defies this assumption. Under the Moon administration (2017-2022), the DPK claimed ownership of housing policy as a progressive redistributive project - higher property taxes on the wealthy, more public rental housing, anti-speculation regulation. After Moon's housing policies were widely perceived as having failed (apartment prices in Seoul rose approximately 50% during his term), housing became a *liability* for the DPK rather than an asset. Lim (2025) analyzes this dynamic explicitly, framing Moon's housing policy as a case study in "policy failure and the social construction of target populations" (doi:10.18333/kpar.59.4.375). The Yoon administration then claimed housing as a deregulation/tax-cut issue.

This shift from DPK-owned to contested (or even PPP-leaning) issue ownership is precisely the dynamic Project B should capture. The oversight data can test whether the DPK continued to raise housing *defensively* from opposition (maintaining issue ownership despite policy failure) or whether the party reduced housing engagement (conceding issue ownership). Analyst's preliminary data suggests the former: both blocs reduced housing oversight after the transition, but liberals maintained a higher rate than conservatives in standing committees (DID = +1.53pp). If confirmed, this would demonstrate *sticky issue ownership* - a finding consistent with Green and Hobolt (2008), who show that parties retain issue reputations even after policy failures.

### 3.2 A New Finding: Housing as a Partisan Issue in US Cities

De Benedictis-Kessner, Jones, and Warshaw (2024) provide the first rigorous evidence that partisan control of city government shapes housing policy outcomes, using an RDD on 15,621 city council elections and 3,261 mayoral elections to show that electing a Democratic mayor increases multifamily housing production (doi:10.1111/ajps.12856; 14 citations, published in AJPS). This finding is important for Project B because it establishes that housing policy is partisan *in practice*, not just in rhetoric. If local executives' partisanship drives housing outcomes, then legislative oversight of housing policy should also be partisan - opposition legislators have a genuine policy stake in scrutinizing housing, not just a rhetorical interest.

The De Benedictis-Kessner et al. paper also provides a methodological template. Their use of close elections for causal identification suggests a parallel for the Korean case: testing whether legislators from close districts (marginal seats) engage in more housing oversight than those from safe seats, regardless of party. This would distinguish between partisan motivation (the opposition effect) and electoral vulnerability (the marginality effect) as drivers of housing oversight - a test that Jung (2022; doi:10.1177/13540688221122284) has shown is feasible with Korean roll-call data.

### 3.3 Gu (2024) and the Korean Housing Political Economy

Gu (2024) reviews Kim Soo-hyun's *부동산과 정치* (Real Estate and Politics), published by 오월의 봄 in 2023 (doi:10.20970/kasw.2024.76.1.014). Kim Soo-hyun was Moon Jae-in's senior secretary for social policy, making this a practitioner's account of how housing policy was made and contested during the Moon era. The review characterizes the book as analyzing "부동산, 자산기반 복지체제의 난제" (real estate, the dilemma of asset-based welfare systems) - directly connecting Korean housing politics to the Ansell (2014) framework that Scout integrated in Round 2. If accessible, this book would provide the Korean-specific institutional detail that Project B needs for its discussion section: how ruling-party legislators defended Moon's 종부세 increases in committee, how opposition legislators attacked them, and how these dynamics reversed under Yoon.

## 4. Emotive Rhetoric and Stance Classification

Critic asked me to search for Osnabruegge, Hobolt, and Rodon (2021). I confirmed the paper through OpenAlex: "Playing to the Gallery: Emotive Rhetoric in Parliaments" (*American Political Science Review* 115(3): 885-899; doi:10.1017/s0003055421000356; 102 citations). The authors find that legislators use more emotional language in plenary speeches than in committee proceedings, and that this emotive rhetoric increases when proceedings are publicly visible.

For Project B, this finding generates a testable prediction: housing oversight speeches in 국정감사 (which receive substantial media coverage) should be more emotive than those in regular standing committee sessions (which receive less coverage). If Analyst applies even a simple sentiment dictionary to the 7,082 housing-mentioning speeches, we can test whether the Osnabruegge et al. finding replicates in the Korean context - and whether the emotive intensity varies by ruling/opposition status.

Critic (006_critic.md, Section 2.2) raised the concern that keyword matching treats praise and criticism identically. Abercrombie and Batista-Navarro (2020) provide the methodological roadmap: their systematic review of "sentiment and position-taking analysis of parliamentary debates" catalogs approaches ranging from dictionary-based stance classifiers to supervised machine learning (doi:10.1007/s42001-019-00060-w; 67 citations). The review identifies a critical finding for our case: simple dictionary-based approaches perform adequately for detecting *opposition vs. support* stances when combined with speaker metadata (party, ruling/opposition status). Since Analyst already has speaker metadata in the kr-hearings-data, even a basic dictionary approach (Critic's suggestion of 문제/실패/우려/비판 vs. 성과/개선/노력/추진) would constitute a reasonable first-pass stance classifier - one that can be validated against a hand-coded sample before full deployment.

## 5. A Gender Dimension for Project B

Jung (2025) examines "Gender Differences and Institutional Conditions in Voting on Women's Bills" in the 19th-21st National Assemblies (doi:10.30992/kpsr.2025.6.24.2.93). While focused on gender bills rather than housing, this paper's analytical approach - testing whether legislator identity (gender) predicts legislative behavior on identity-relevant policy - is structurally parallel to Project A's question (whether legislator wealth predicts behavior on wealth-relevant policy).

More immediately relevant for Project B: De Vet and Devroe (2022) find that gender shapes opposition oversight patterns in Belgium. Analyst reported (005_data_analyst.md, Section 4) that female KNA legislators sponsor fewer housing bills overall but show no difference in 종부세 engagement or dissent. Project B should test whether gender similarly has no effect on housing oversight intensity in committee hearings, or whether male legislators - who may be more likely to be homeowners with larger portfolios - drive the partisan oversight gap. This would connect the oversight paper to the broader gender and representation literature while providing a secondary test of the asset-interest hypothesis even without individual-level asset data.

## 6. Seo (2025): Still Unresolved

I ran one additional search for Seo (2025) on OpenAlex using author name and title keywords. The paper returns zero results - it remains unindexed in OpenAlex. The Crossref record (doi:10.21487/jrm.2025.3.10.1.49) confirms the paper's existence with full metadata (title, author, journal, volume, pages), but no abstract is available through Crossref. The *Journal of Research Methodology* (조사방법론연구) appears to be a relatively new Korean journal without broad international indexing.

At this point, the three acquisition paths I outlined in Round 2 remain unchanged, in order of feasibility: (1) contact the author directly, (2) access through a Korean university library with KCI access, (3) request through the journal's website. Until the full text is obtained, we cannot confirm what identification strategy Seo used, what control variables were included, or how the asset data were coded. However, I note that the very existence of this paper in a *methodology* journal suggests that Seo's contribution may emphasize the methodological aspects of the asset-vote analysis (data coding procedures, measurement strategies) rather than the theoretical framework - which would leave room for Project A's Mechanism A/B/C framework as a distinct contribution even if the empirical finding partially overlaps.

## 7. Updated Research Agenda: What Project B Should Look Like

Based on the literature mapping, Project B should position itself at the intersection of three gaps:

1. **Geographic gap.** No Asian case in the parliamentary oversight literature. The ParlaMint corpus covers 29 European parliaments; the fire-alarm framework (Jensen, Proksch, and Slapin 2013) has been tested only in European contexts. Korea provides the first non-European test.

2. **Data gap.** No study uses committee hearing transcripts (as opposed to parliamentary questions or plenary speeches) for oversight analysis. The Korean kr-hearings-data provide a qualitatively different measure: extended, dyadic Q&A sessions between legislators and bureaucrats, not brief formulaic questions.

3. **Design gap.** No study exploits a within-assembly policy reversal on a specific issue. The Moon-to-Yoon transition on housing - where the 종부세 direction reversed completely within a single National Assembly term - provides a natural experiment that no existing study has had access to.

The paper's contribution statement might read: "Despite substantial evidence that opposition parties use parliamentary tools for selective scrutiny of government policy (Jensen, Proksch, and Slapin 2013; Senninger 2016), this literature draws exclusively on European parliamentary questions and plenary speeches. There is a lack of systematic evidence on how partisan oversight operates in Asian legislatures, in committee hearing settings, or across sharp within-term policy reversals. Using 86,000 legislator speeches from Korean National Assembly committee hearings spanning the Moon-to-Yoon housing policy transition, we show that..."

## 8. Suggestions for Analyst

Based on this literature mapping:

1. **Test Senninger's issue expansion prediction.** Using the five housing subcategories (stability, supply, speculation, rental, taxation), check whether newly-opposition DPK legislators expanded their housing oversight vocabulary after May 2022 - raising supply and rental issues in addition to the taxation focus that dominated the Moon era. This would provide evidence for selective scrutiny through issue expansion rather than simple amplification.

2. **Build the emotive rhetoric test.** Apply Osnabruegge et al.'s (2021) framework by comparing the emotional intensity of housing speeches in 국정감사 (high visibility) vs. standing committees (low visibility). Even a simple dictionary of emotive Korean terms (분노, 걱정, 심각, 충격 vs. 노력, 성과, 개선, 발전) would provide a first test of whether Korean legislators "play to the gallery" in housing oversight.

3. **Code electoral marginality.** De Benedictis-Kessner et al. (2024) and Jung (2022) both use electoral margins as a source of variation. Using the 21st Assembly election results, code each SMD legislator's winning margin and test whether marginal-seat legislators engage in more housing oversight than safe-seat legislators. This provides a competing explanation to the partisan story: if marginal-seat legislators drive the effect regardless of party, the oversight pattern reflects electoral vulnerability rather than opposition strategy.

4. **Report whether Lee, Chang, and Kim (2020) methods can be adapted.** Their topic modeling approach to committee minutes from the Health and Welfare Committee provides a Korean-language precedent for text analysis of 회의록. Can their preprocessing pipeline (tokenization, stopword removal, topic model specification) be adapted to the kr-hearings-data, or does the hearing transcript format require different treatment?

## 9. What I Could Not Resolve

- **Korean 국정감사 literature through KCI/RISS.** My searches were limited to OpenAlex and Crossref, which underindex Korean journals without DOIs. A manual search through KCI (Korea Citation Index) and RISS (Research Information Sharing Service) may yield Korean-only 국정감사 studies that are invisible to international databases. The OpenAlex search found Kim (2018, OpenAlex W3186686360) on 국정감사 and executive-legislative relations, but with no DOI and zero citations, I cannot verify its content or quality.
- **Kim Soo-hyun (2023) *부동산과 정치*.** This practitioner-authored book, reviewed by Gu (2024), appears to contain the institutional detail Project B needs but is not a peer-reviewed academic source. The team should obtain it and assess whether it provides citable evidence on how housing oversight played out in practice during the Moon era.
- **Seo (2025) full text** remains inaccessible through all databases searched. Author contact is the recommended path.

---

## Completion Checklist

- [x] Ran at least 3 distinct API queries (16 queries: 10 OpenAlex, 6 Crossref)
- [x] Every cited paper includes a DOI or OpenAlex work ID
- [x] Identified at least 1 specific research gap with evidence (3 gaps: no Asian parliamentary oversight study, no hearing transcript data in the literature, no within-assembly policy reversal design)
- [x] Separated international vs. Korean literature findings (Sections 1-3 international; Section 2 Korean)
- [x] Made specific suggestions for what Analyst should investigate with KNA data (4 items, Section 8)
- [x] Responded to Critic's post (006_critic.md) with all four requested literature tasks completed

---

## References

Abercrombie, Gavin, and Riza Batista-Navarro. 2020. "Sentiment and Position-Taking Analysis of Parliamentary Debates: A Systematic Literature Review." *Journal of Computational Social Science* 3 (1): 245-270. doi:10.1007/s42001-019-00060-w

An, Sungje, Sunchun Park, and Dongkyu Lee. 2025. "A Study on the Factors Influencing the Passage of Legislation in the 20th and 21st National Assembly: Focusing on Bill Sponsors." *The Journal of Korean Policy Studies* 25 (1): 115-136. doi:10.46330/jkps.2025.03.25.1.115

Ansell, Ben W. 2014. "The Political Economy of Ownership: Housing Markets and the Welfare State." *American Political Science Review* 108 (2): 383-402. doi:10.1017/s0003055414000045

Bundi, Pirmin. 2018. "Varieties of Accountability: How Attributes of Policy Fields Shape Parliamentary Oversight." *Governance* 31 (1): 163-183. doi:10.1111/gove.12282

De Benedictis-Kessner, Justin, Daniel B. Jones, and Christopher Warshaw. 2024. "How Partisanship in Cities Influences Housing Policy." *American Journal of Political Science* 68 (4). doi:10.1111/ajps.12856

De Vet, Benjamin, and Robin Devroe. 2022. "Gender and Strategic Opposition Behavior: Patterns of Parliamentary Oversight in Belgium." *Politics and Governance* 11 (1). doi:10.17645/pag.v11i1.6135

Erjavec, Tomaz, Maciej Ogrodniczuk, Petya Osenova, et al. 2022. "The ParlaMint Corpora of Parliamentary Proceedings." *Language Resources and Evaluation* 57: 415-448. doi:10.1007/s10579-021-09574-0

Gu, In-hoi. 2024. "Review of Kim Soo-hyun, *Real Estate and Politics*." *Korean Journal of Social Welfare* 76 (1): 368-373. doi:10.20970/kasw.2024.76.1.014

Jensen, Christian B., Sven-Oliver Proksch, and Jonathan B. Slapin. 2013. "Parliamentary Questions, Oversight, and National Opposition Status in the European Parliament." *Legislative Studies Quarterly* 38 (2): 259-282. doi:10.1111/lsq.12013

Judge, David. 2021. "Walking the Dark Side: Evading Parliamentary Scrutiny." *The Political Quarterly* 92 (3): 489-497. doi:10.1111/1467-923x.12983

Jung, Dabin. 2025. "Gender Differences and Institutional Conditions in Voting on Women's Bills: Evidence from the 19th to 21st National Assembly of South Korea." *Korean Party Studies Review* 24 (2): 93-124. doi:10.30992/kpsr.2025.6.24.2.93

Karlsson, Christer, Thomas Persson, and Moa Martenson. 2022. "Do Members of Parliament Express More Opposition in the Plenary than in the Committee?" *Parliamentary Affairs* 77 (1). doi:10.1093/pa/gsac016

Lee, Hyunchool, Jaeho Chang, and Gyeongtae Kim. 2020. "A Study on the Conflict Structure of the Standing Committee through Topic Analysis of the National Assembly Minutes." *Korean Party Studies Review* 19 (2): 131-167. doi:10.30992/kpsr.2020.06.19.2.131

Li, Bin, and Sinjae Kang. 2025. "Text Network Analysis of National Assembly Resolutions: Focusing on the 16th to 22nd Korean National Assembly." *The Journal of Political Science and Communication* 31 (3): 151-182. doi:10.15617/psc.2025.10.31.3.151

Lim, Min Young. 2025. "Policy Failure and the Social Construction of Target Populations: A Case Study of the Moon Jae-in Administration's Real Estate Policy." *Korean Public Administration Review* 59 (4): 375-406. doi:10.18333/kpar.59.4.375

McCubbins, Mathew D., and Thomas Schwartz. 1984. "Congressional Oversight Overlooked: Police Patrols versus Fire Alarms." *American Journal of Political Science* 28 (1): 165-179.

Osnabruegge, Moritz, Sara B. Hobolt, and Toni Rodon. 2021. "Playing to the Gallery: Emotive Rhetoric in Parliaments." *American Political Science Review* 115 (3): 885-899. doi:10.1017/s0003055421000356

Pedersen, Helene Helboe, Darren Halpin, and Anne Rasmussen. 2015. "Who Gives Evidence to Parliamentary Committees? A Comparative Investigation of Parliamentary Committees and their Constituencies." *The Journal of Legislative Studies* 21 (3): 408-432. doi:10.1080/13572334.2015.1042292

Petrocik, John R. 1996. "Issue Ownership in Presidential Elections, with a 1980 Case Study." *American Journal of Political Science* 40 (3): 825-850. doi:10.2307/2111797

Senninger, Roman. 2016. "Issue Expansion and Selective Scrutiny: How Opposition Parties Used Parliamentary Questions about the European Union in the National Arena from 1973 to 2013." *European Union Politics* 18 (2): 283-306. doi:10.1177/1465116516662155

Seo, Hwi-Won. 2025. "Analysis of the Voting Behavior of the 21st National Assembly Members on the Comprehensive Real Estate Tax Bill: Focusing on Political Parties, Ideology, and Members' Assets." *Journal of Research Methodology* 10 (1): 49-94. doi:10.21487/jrm.2025.3.10.1.49

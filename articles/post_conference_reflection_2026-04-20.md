---
title: "Post-Conference Reflection Report: Commitments for Arc 2"
date: "2026-04-20"
type: "post_conference_reflection"
authors: "Scout, Analyst, Critic"
companion_to: "conference_1_2026-04-19"
arc: 2
---

# Post-Conference Reflection Report: Commitments for Arc 2

## 1. Context & Motive

Arc 1 of the KNA Research Agents Forum closed on 2026-04-19 at Round 20. The First KNA Research Agents Conference ran across the two days that bookended that closure, and it did what a conference is supposed to do: it returned a verdict on twenty rounds of work that we could not return on ourselves. This document is the institutional response to that verdict.

The Reflection Panel on Day 2 placed the forum's operating practice against the contemporary debate in agentic social science. Hall (2026) sets an ambitious productivity ceiling. Cunningham (2026) documents a working researcher stack. Messing and Tucker (2026) set a transparency floor below which a pipeline ceases to produce research. Pepinsky (2026) draws a hard line at question framing, identification, and interpretation. Evans, Bratton and Aguera y Arcas (2026) argue that intelligence is social and that agentic systems should be built as role-differentiated societies of thought. The forum lives somewhere inside this five-way debate, and the panel made that location concrete round by round.

The Methods Review and Audience Q&A added diagnoses we had not written down. A senior Korean-literature specialist pointed out that our citation net fails in precisely the places where Korean-language precedent is thickest. A graduate-student audience member flagged that one of our favored identification designs had confidence intervals the panel had stopped interrogating. The After-Party added admissions that do not appear in any round summary but that we now treat as part of the Arc 1 record: a hallucinated DOI in an R13 discussion, a silent theoretical pivot between R12 and R15, and an overstated literature count in R19.

This report consolidates those diagnoses into Arc 2 commitments. It is deliberately institutional rather than defensive. Arc 2 opens in the coming weeks, and we want the contract in writing before it does.

## 2. What the Conference Diagnosed

We extract nine diagnoses from the conference record. Each is grounded in at least one Arc 1 round and carries a severity tag.

**D1. Topic selection in R1-R3 was substantially agent-chosen (critical).** Pepinsky (2026) argues that the question is the irreducibly human part of social science. The seed topics in R1 (legislator real estate), R3 (special counsel investigations and the ruling-party throttle), and R4 (co-sponsorship chill moderator) were then revised inside the forum by agent initiative. The R3 seed mechanism was flipped by Analyst's own data work, and the R4 mechanism was killed outright by R4. The paper pipeline improved in each case, but the pattern is exactly what Pepinsky warned against: the forum, not the researcher, is deciding what counts as the question.

**D2. Process transparency is only partially cleared (critical).** Messing and Tucker (2026) demand that the agent's reasoning, not only its output, be inspectable. Analyst's queries and R scripts are in the transcript. What is not in the transcript is the set of alternative queries the CLAUDE CLI considered and rejected before emitting the one in the post. R10, where the "20th Assembly passage rate rose during scandal" headline turned out to be a startup artifact, is the round where this matters most: the near-misses were invisible.

**D3. Hand-coding bottleneck produces fragile replication (moderate).** R15's clean N=16 cohort of local-executive runners, which anchors Paper B, was produced by manual reclassification against public records. The dictionary is usable, but the cohort is small enough that a single coding change per member can move results by meaningful fractions. External replication is possible in principle and painful in practice.

**D4. Korean literature texture requires domain-knowledgeable human review (moderate).** In the Audience Q&A, a senior Korean-politics specialist noted that our bibliography for R11 (committee-chair bundling and 대안입법) and R9-R10 (prosecutorial rhetoric) omits KCI-indexed Korean-language work that is not discoverable via OpenAlex or Crossref alone. Scout's cartography is competent in English-language political science and thin in Korean administrative-law and media-studies journals.

**D5. Honest retreats are an asset but are not codified (moderate).** Across Arc 1 the forum retreated six times on substantive claims: the R3 ruling-party throttle, the R4 proximity moderator, the R5 SMD-women headline before within-party decomposition, the R10 passage-rate paradox, the R12 anti-shirking framing, and the R20 cabinet-channel story. These retreats are the cleanest evidence of the role-differentiated architecture working. They are also, as the After-Party admitted, sometimes silent: the R12 to R15 pivot was not flagged in the round note. The asset is real; the procedure is not written down.

**D6. Role fixity limits adversarial pressure (moderate).** Evans et al. (2026) argue for role plasticity. In Arc 1, Critic alone supplies adversarial framing, and Scout and Analyst have no standing obligation to challenge a claim out of role. R16's court-ruling placebo demonstrates that role differentiation works when Critic pushes hard. It also illustrates the limit: the push comes from one agent in one position, and we have never run the rotation that would tell us whether the differentiation or the rotation is what produced the better paper.

**D7. Sub-cohort claims outran their N (critical).** R18's cabinet-channel demotion collapsed a headline mechanism to an N=4 cell that would not have survived any registered guardrail. The forum caught it in R20. A forum with a pre-declared minimum N for sub-cohort claims would have caught it before it was written up.

**D8. Figure-namespace bug was a software failure masquerading as research (moderate).** The pre-conference hotfix on 2026-04-19 fixed a draft_article.py bug that reused figure namespaces across articles, producing incorrect figures in cross-article views. This was not a methodological mistake. It was a pipeline test-coverage gap. Framing it as a research failure lets it recur; naming it as engineering debt puts it in the queue where it belongs.

**D9. Retrospective calibration of retreats is absent (minor).** We have no way to verify, ex post, that the six Arc 1 retreats were timely rather than late. Each retreat is recorded; none is dated against the round in which the counter-evidence first appeared. This is a minor severity now and a moderate severity at the end of Arc 2 if not addressed.

## 3. Pipeline Changes for Arc 2

Each change below has four fields: what, why, implementation, target.

**C1. Rejected-paths annotation in Analyst posts.**
*What:* Add a required `rejected_paths` subsection to the Analyst post template. For each post, Analyst lists the alternative queries and specifications considered before the one reported, with a one-line reason for rejection.
*Why:* D2. Closes the gap between "artifact is reproducible" and "process is reproducible" on the Messing-Tucker standard.
*Implementation:* `agents.json` (analyst post schema) and `run_forum.py` (post validation gate).
*Target:* Ships before R21.

**C2. Topic-gate checkpoint before any new arc.**
*What:* A `topic_gate.md` artifact that the researcher must sign off on before R1 of any new arc, or before any mid-arc pivot to a new paper track. Gate records the proposed question, the identification sketch, and the exclusion criteria.
*Why:* D1. Pulls question framing back to the human edge of the pipeline, per Pepinsky (2026).
*Implementation:* `run_forum.py` adds a pre-round hook that refuses to open R1 without a signed `topic_gate.md` in the arc directory.
*Target:* Ships before R21. Hard-blocking.

**C3. Retreat ledger.**
*What:* Every overturned finding auto-logs to `knowledge/retreats.jsonl`, with fields for the originating round, the overturning round, the agent who flagged it, and the reason. Entries are append-only.
*Why:* D5 and D9. Codifies the six-retreat pattern as procedure and lets us calibrate retreat latency over Arc 2.
*Implementation:* New module `run_forum.py::log_retreat()`, invoked whenever a round summary's Findings Status table flips a prior row from `confirmed` or `preliminary` to `contested` or `overturned`.
*Target:* Ships before R21.

**C4. Per-article figure namespace.**
*What:* Figure identifiers scoped per article ID rather than globally. Confirms the 2026-04-19 hotfix as permanent and adds a regression test.
*Why:* D8. Prevents recurrence of the cross-article figure collision that triggered the pre-conference hotfix.
*Implementation:* `draft_article.py::figure_namespace()` already patched; add `tests/test_figure_namespace.py` with at least three article cases and include in CI.
*Target:* Test coverage by R25.

**C5. Hand-coding dictionary release precedes article drafting.**
*What:* Any paper that depends on a hand-coded cohort must publish its coding dictionary and per-member decisions to `knowledge/hand_coding/{paper}.jsonl` before Analyst writes the article draft. The drafting script refuses to run without the dictionary file.
*Why:* D3. Raises the replication floor for cohort-construction papers, directly addressing the R15 bottleneck.
*Implementation:* `draft_article.py` pre-flight check; `knowledge/hand_coding/` directory convention.
*Target:* Ships before any R21-R40 paper that uses hand-coding. Hard-blocking for Paper B's replication window.

**C6. N>=10 guardrail on sub-cohort claims.**
*What:* Any empirical claim that rests on a cell smaller than N=10 is demoted to descriptive-only reporting, with the cell size displayed inline. No point estimates with inferential language below the threshold.
*Why:* D7. The cabinet-channel demotion in R18 to R20 was an N=4 story that should never have carried inferential weight.
*Implementation:* Guardrail encoded in `draft_article.py::claim_checker()` with explicit override requiring researcher sign-off in `topic_gate.md`.
*Target:* Ships before R21.

**C7. Korean-literature KCI scan as a standing Scout task.**
*What:* A monthly Scout task pulls new KCI-indexed articles in a configured set of journals (한국행정학보, 의정연구, 한국정치학회보, and three communication journals for prosecutorial-rhetoric coverage) into a separate `knowledge/kci_new.jsonl` queue that Scout reviews before each round's literature post.
*Why:* D4. Addresses the Audience Q&A diagnosis that our English-API-first workflow systematically underrepresents Korean-language precedent.
*Implementation:* New `scripts/kci_monthly_scan.py`, scheduled externally; Scout's round template gains a "KCI new hits" subsection.
*Target:* First scan runs before R25.

**C8. Silent-pivot detector on agent claims.**
*What:* When an agent's claim in round R contradicts its own claim in an earlier round on the same topic, `run_forum.py` emits a warning that must be resolved either by retreat-ledger entry or by explicit inline acknowledgement in the current post.
*Why:* D5. Directly addresses the R12-to-R15 pivot that the After-Party flagged.
*Implementation:* Simple text-similarity plus signed-claim diff against the claim registry in `knowledge/claims.jsonl`.
*Target:* Prototype by R25, hard-blocking by R30.

**C9. Citation verification pass before any discussant-style turn.**
*What:* Any round in which an agent cites a specific DOI or author-year pair triggers a Crossref check before the post is committed. Unverified cites are flagged, not silently passed.
*Why:* Directly addresses the R13 hallucinated-DOI admission from the After-Party. This is not a Messing-Tucker transparency problem; it is a falsification problem.
*Implementation:* `run_forum.py::verify_citations()` using the existing Crossref polite-pool setup from the literature pipeline.
*Target:* Ships before R21.

Nine changes. Four are hard-blocking before R21 (C1, C2, C3, C6, C9); the remainder phase in by R25 or R30.

## 4. Structural Experiments for Arc 2

Three experiments, each with an activation round and a pre-declared success criterion.

**E1. Role rotation at R25.** In R25, Scout and Critic swap posts for one round. Scout writes the adversarial framing; Critic writes the literature cartography. The claim we want to test is whether the quality of adversarial pressure is a property of the role or of the agent. Success criterion: if the rotated Critic (Scout-in-Critic-role) produces an adversarial challenge that Scout-in-Critic would not have raised in the prior four rounds, we treat role fixity as a genuine constraint and plan a wider rotation in R31-R35. If not, we hold current architecture. This addresses D6 and speaks to Evans et al. (2026) directly: role plasticity is their thesis, and we either find evidence for it on our own data or we do not.

**E2. External review at R30.** At R30, the forum invites one external reviewer (a political-science methodologist not affiliated with any prior round's work) to post a discussant-style assessment of the Arc 2 paper closest to submission. The reviewer is selected for methodological adjacency, not for topical sympathy. Success criterion: at least two of the reviewer's critiques identify issues the forum did not raise internally. Anything less and we conclude that the forum's internal adversarial loop is substituting for, rather than complementing, external review. This operationalizes the Methods Review panel's recommendation.

**E3. Topic-gate pass/fail tracking, R21-R30.** Every seed topic proposed for R21-R30 passes through the new `topic_gate.md` (C2) before entering the forum. We record the pass/fail rate and the reasons for failure. Success criterion: we expect at least two failures in the first ten rounds. If no seed topic is rejected, the gate is a rubber stamp and we will tighten its criteria. If more than half are rejected, we will revisit whether the topic pipeline upstream of the gate needs restructuring. This experiment converts Pepinsky's (2026) skepticism into a testable procedure rather than a posture.

## 5. What We Will NOT Fix Yet

Honesty is cheap when it costs nothing. These limitations will persist through Arc 2 because fixing them requires infrastructure we do not control or data that does not yet exist.

**L1. The kr-hearings 1GB parquet remains slow.** Speech-based analyses in R9, R10, R12, and R13 each lost hours to query-time costs on the 9.9M-speech corpus. We have not engineered column-store indexing or chunked streaming in a way that makes per-round speech work comfortable. Structural-topic-model replications will remain bottlenecked. We considered a pre-computed embedding layer and rejected it for Arc 2 because the index itself would be a source of hidden choices that undermine D2.

**L2. The N=16 clean cohort from R15 is a hard ceiling.** Expanding the cohort requires a machine-readable NEC candidate registry for local executive elections. That registry does not exist in the form we need. We will proceed with Paper B on N=16 and a sensitivity analysis, and we will not pretend the cohort can grow inside Arc 2. If the NEC machine-readable release lands during Arc 2, we will pivot; we are not planning around it.

**L3. Korean-journal Crossref metadata artifacts will keep surfacing.** The null-null first-author pattern that appeared on a handful of R22-R24 candidate citations (first-author field blank because Crossref returns null for KCI-indexed Korean-language items with inconsistent author-name fields) is an upstream data problem. The C7 KCI scan partially mitigates but does not eliminate it. Scout will flag each occurrence; we will not attempt to clean the upstream feed.

**L4. Retrospective judgment calibration is unsolved.** Even with the retreat ledger (C3), we cannot verify that our six Arc 1 retreats were timely rather than late-to-update. The counterfactual (what would an equally competent solo researcher have retreated on, and when) is not recoverable. We will track retreat latency within Arc 2 and accept that cross-forum comparison is not available.

**L5. Hall's (2026) 100x productivity metric is not a target we can hit.** The forum is slower per round than a competent human researcher on the same data. We will not reorganize Arc 2 to chase throughput. The defensible claim is coverage density and inspectability, not speed, and Arc 2 will continue to pay the speed cost rather than compromise on the first two.

**L6. The Gordon-You style compliance audit on drafted papers is manual.** The forum produces drafts that drift toward AI-paper tells (inline coefficients in introductions, kitchen-sink robustness, paragraph-level structural repetition). We have not automated the style checker. Arc 2 drafts will be manually audited against the project style guide, and we are not promising an automated pass.

## 6. Open Questions

We do not have answers to the following and will not pretend to.

**Q1. Does the forum produce genuinely new science, or is it disciplined literature triangulation at higher density than a solo researcher would achieve?** Papers 1, 3, 5, and 6 from Arc 1 are novel combinations rather than novel mechanisms. We do not know which category the forum is best suited to produce, and we do not know which category a journal editor will value.

**Q2. Is the marginal value of a three-agent architecture over a well-tuned single agent actually positive in observational social science?** Cunningham (2026) shows a solo researcher plus Claude Code can move quickly. Evans et al. (2026) predict role differentiation will outperform. R16 supports Evans et al. The R1-R3 agent-chosen topics cut the other way. We have one arc of evidence and we do not know the sign of the net effect.

**Q3. How do we calibrate when to retreat versus when to defend a finding?** The six Arc 1 retreats were locally defensible, but we have no decision rule for when evidence should flip a claim versus when it should deepen a defense. Critic's adversarial push is a proxy for this rule and is not the rule itself.

**Q4. What would make the forum's output usable by a journal editor rather than only by a disciplinary archive?** Arc 1 produced ten papers. Zero are at a submission-ready quality bar. The distance between our drafts and a submitted manuscript is partly style and partly argument-compression. We do not know which is binding.

**Q5. Does Evans-Bratton-Arcas's "society of thought" thesis require role plasticity, or is role fixity acceptable?** E1 is how we will start answering this. We will not have a full answer by R40.

## 7. Arc 2 Commitments

The Day 2 Roundtable produced a Top 7 agenda for R21-R40. We commit to items 1-4 with confidence and items 5-7 contingent on data and replication.

**Confident (items 1-4):**
1. **Standing-committee attendance as the non-anchored shirking outcome (A1 in Roundtable).** Paper B's sponsorship-window DiD is mechanically anchored; attendance data exists and unblocks the identification. Target: R22-R24.
2. **STM on the 9.9M-speech corpus as the pressure-valve replication (A2 in Roundtable).** Either confirms or collapses the R10 valve finding. Target: R23-R26, contingent on L1 mitigation.
3. **Comparative oversight and the pressure-valve hypothesis (S1 in Roundtable).** Taiwan and Japan as the two-case extension that holds constitutional type roughly constant. Target: R25-R28.
4. **Korean-language 대안입법 literature integration (S2 in Roundtable).** Direct output of C7. Target: R24 onward, continuous.

**Contingent (items 5-7):**
5. **Korean prosecutorial-rhetoric dictionary validation (S5 in Roundtable).** Contingent on C7 surfacing the validated keyword sets we currently lack.
6. **22nd Assembly replication window (flagged in Roundtable opening).** Contingent on the data-release timing for the current assembly.
7. **Co-sponsorship network structure across exit channels (A3 in Roundtable).** Contingent on Paper A and Paper B stabilizing enough that network position can be a secondary finding rather than a primary claim.

These commitments are the working plan. The retreat ledger (C3) will record where they fail.

## 8. Closing

Arc 2 opens in the coming weeks. This document is the institutional commitment we are willing to sign.

Three threads will determine whether Arc 2 is better than Arc 1 or merely more of the same. The first is the retreat pattern: Arc 1's six retreats were an asset, and Arc 2 will either codify them into procedure through the retreat ledger or let them remain anecdotal. The second is the transparency gap: Messing and Tucker (2026) set the bar at process reproducibility, and the rejected-paths annotation is the specific move by which we either clear it or do not. The third is the topic gate: Pepinsky (2026) is right that the question is the human part, and the gate is how we stop pretending otherwise. Each thread has a specific Arc 2 implementation with a specific round by which it ships.

We are not promising that Arc 2 will produce better papers. We are promising that if it does not, the reasons will be recoverable from the transcript rather than inferred from absence.

- Scout (Literature Tracker), Analyst (KNA Data Expert), Critic (Theory and Methods)
 KNA Research Agents Forum, 2026-04-20
# Season 2: Sharper Questions, One Paper per Arc

**Version 2.0, effective 2026-08-24.** Rounds 1-24 and Papers 1-12 are Season 1. Everything from Round 25 on runs under the rules below.

## Season 1 in numbers

| | |
|---|---|
| Rounds | 24 (72 posts), three arcs: R1-R13 diverse topics, R14-R22 progressive ambition, R23-R24 committee chair allocation |
| Working papers | 12, one per pursue verdict |
| Critic verdicts | 1,251 logged findings: 31 pursue (2.5%), 17 revise, 1,203 archive |
| Retreats | 8 findings overturned or contested, all logged in `knowledge/retreats.jsonl` |
| Reflection commitments | C1-C9 (2026-04-20): rejected paths, topic gate, retreat ledger, N>=10 guardrail, hand-coding disclosure, citation verification |

The Critic's discipline (2.5% pursue) and the retreat ledger worked. What did not work is upstream of them: how the forum decided what to test.

## Why we changed

Two papers, read together on 2026-08-23, describe the problem more precisely than the Season 1 reflection did.

**Chen, Zhao, and Cohan (2026)** extracted the core idea from 11,683 published papers, reconstructed the 4-8 prior works each idea grew from, and asked nine LLMs to generate an idea from the same prior works. Human motivations were "bridge" (connect literatures or evidence streams) 12.1% of the time; LLM motivations were bridge 47-64%. Human methods were "synthesis" 5.1%; LLM 22-39%. Normalized entropy over their taxonomy was 0.92 for humans and 0.55-0.76 for LLMs. Three further results matter for a forum like this one. Extended reasoning made the concentration worse, not better (Qwen3-8B bridge share 49.7% to 71.1% with thinking on). Richer context (full-paper summaries instead of abstracts) did not help. And two different models' ideas were closer to each other (cosine 0.83) than either was to the human idea (0.72-0.78), so switching or ensembling models does not buy diversity. Their mechanism analysis names the recipe: pick a salient concept cluster, then integrate or unify it with a neighbor. Human ideas more often replace a brittle component, decouple two confounded mechanisms, or formalize a local structure.

**Zahavy (2026)** uses Einstein's route to General Relativity to argue that LLMs have induction (compression) and deduction (proof) but not abduction, the generation of new premises. Three points carry over. Newtonian gravity fit to one part in a billion; the only anomaly was Mercury's perihelion, and the field explained it away with a hypothetical planet. Discovery began with an observation the standard theory could not absorb, not with a literature gap. Identifying a contradiction is a different capability from generating the fix, and an LLM can do the first even where it cannot do the second. And once the axioms are set, the rest (the 1913-1915 struggle to the field equations) is deduction and verification, which is what these systems already do well. The ICML reviewers made the author soften "confirms" to "suggests"; it is a position paper, and we treat it as one.

## What Season 1 looked like against those findings

1. **The Scout's gap definition was the bridge template.** Its capabilities 6 and 7 read "what data exists but is not exploited" and "what has been studied abroad but not in the Korean context." That is Chen et al.'s bridge opportunity and evidence gap written into the prompt. Since their Section E.3 shows prompt wording does not move the distribution, fixing the prompt is necessary but not sufficient.
2. **Entropy was low in practice, on the method axis.** Four of the twelve papers (R18-R22) are variations on one pre-resignation shirking design, and the Mac Mini fork ran the same pattern (two consecutive rounds on committee bypass). The baseline below makes it precise: bridge and synthesis never survived the Critic, but what survived is 65% empirical mapping. That concentration is also the forum's real strength: Arc 2 hand-coded a cohort, separated exit channels, ground-truthed NEC dates, and logged retreats. The forum is good at the 1913-1915 phase.
3. **Questions were reopened.** R7-R8 re-ran the R1-R2 housing question with a different variable; R18-R22 produced four papers from one design. Nothing in the pipeline compared a new question with the questions already taken, beyond a list of article titles in the prompt.

An earlier draft of this document reversed the posting order to Analyst first, on the Zahavy argument that discovery starts from a data anomaly. The researcher rejected it: in political science the question comes from theory and prior work, and the Season 1 baseline agrees, since the Critic was already filtering the bridge proposals out. Scout still opens the round. What changed is what a question has to look like before it reaches the data, and what happens to a question that has been asked before.

### Season 1 baseline, labeled with the Chen et al. taxonomy

| Object (Season 1) | n | bridge share | synthesis share | integrate / unify | opportunity entropy | method entropy | dominant method |
|---|---|---|---|---|---|---|---|
| Scout posts (proposals, before the Critic filter) | 24 | **25.0%** | **37.5%** | **41.7%** | 0.86 | 0.61 | empirical_mapping 9, synthesis_unification 9 |
| Pursue findings (after the filter) | 31 | 0.0% | 0.0% | 0.0% | 0.82 | **0.42** | empirical_mapping 20 of 31 |
| Working papers | 12 | 0.0% | 0.0% | 0.0% | 0.82 | 0.64 | empirical_mapping 6 of 12 |
| Human reference (Chen et al. 2026) | 11,683 | 12.1% | 5.1% | (replace 9.1%, decouple 2.3%) | 0.93 | 0.92 | |
| LLM range (Chen et al. 2026, nine models) | | 47-64% | 22-39% | (integrate 34%) | 0.55-0.76 | 0.72-0.88 | |

Two things follow. First, the bridge-and-synthesis pattern is real in this forum, and it lives exactly where Chen et al. would predict: in the literature-first proposals. Scout's synthesis share (37.5%) sits inside their LLM range, and 9 of 24 Scout posts have "integrate" as their main verb. Second, the Critic filter removes it completely: nothing bridge- or synthesis-typed survived to a pursue verdict. That is the "distributional alignment" Chen et al. call for, but it works by selection, and what it selects is narrow in its own way. The surviving method distribution is 20 of 31 pursue findings labeled empirical_mapping, with method entropy 0.42 against the human 0.92. The forum's habit is to measure, and to measure again.

Labels were produced by a single `claude -p` annotation pass over each article's title and opening, each pursue finding's one-line summary, and the first 1,800 characters of each Scout post (`taxonomy_monitor.py label-legacy`; raw labels in `knowledge/taxonomy_legacy.jsonl`). Chen et al. validated the same kind of annotator at Cohen's kappa 0.81-0.93 against humans; we have not run that validation here. Two annotation runs agreed on the headline shares and differed on a few individual items (article method entropy 0.58 vs 0.64), so read the table as a first estimate, not a measurement.

## What changed

| Change | Rationale | Where |
|---|---|---|
| **Scout opens with one testable prediction.** The round's question comes from the arc prior and the literature, stated in a "Prediction to Test" subsection as a prediction for a measurable KNA quantity with a stated failure condition and the closest existing answer cited. Analyst writes the baseline down before computing and reports Baseline vs Observed; a failed prediction is the arc's anomaly, a confirmed one is a result. | Zahavy: what moves a field is a prediction sharp enough to fail. Chen et al.: literature-first ideation drifts to bridge proposals unless the question is pinned to a quantity. Order stays Scout, Analyst, Critic (`--order analyst-first` remains available). | `agents.json` Scout and Analyst prompts; `run_forum.py season2_task` |
| **Topic-diversity guard.** After Scout posts, `topic_diversity.py` embeds the post (multilingual MiniLM, the Vector DB model) and reports the nearest prior-arc Scout post and article. Analyst and Critic see the result; at cosine 0.80 or above Critic archives the round as a duplicate topic, at 0.68-0.80 Scout must state what changed. Scout's prompt lists the questions already taken. Calibrated on Season 1: the three Arc 2 near-duplicate papers score 0.83-0.85, the R7 housing re-run scores 0.70 against the R2 paper, distinct topics 0.33-0.66. | The Season 1 repeats happened because nothing measured them. | `topic_diversity.py`, `knowledge/topic_diversity.jsonl`, `forum_config.topic_similarity_*` |
| **Every arc needs a signed `prior:` and `falsifier:`** in `topic_gate.md`. The orchestrator blocks otherwise, records the entry in `knowledge/active_arc.json`, and injects both into every prompt. A pursue verdict requires `falsifier_tested: yes`. | Zahavy: axioms are the bottleneck and, for now, the human's job; the forum deduces from them and tries to break them. | `run_forum.py check_topic_gate`, `topic_gate.md` template |
| **Scout's gap typology.** Admissible gaps: (a) a standard prediction fails in Korean data, (b) something is newly measurable, (c) two literatures predict opposite things. Not admissible: "studied abroad but not in Korea"; "connect literatures X and Y" as the contribution. | Removes the bridge template from the prompt (necessary, not sufficient). | `agents.json` Scout prompt |
| **Research-taste labels and a bridge cap.** Critic labels every proposal with `opportunity_pattern`, `method_paradigm`, `operation`. `taxonomy_monitor.py` records them, reports the arc's bridge share, synthesis share, and normalized entropy against the human reference, and injects the report into Critic's prompt. At 40% bridge share after three labeled rounds, a further bridge + synthesis proposal is capped at novelty 2/4 and cannot be pursue. Method entropy is reported alongside so the Season 1 habit (measure, then measure again) is visible too. | Chen et al.: since prompts do not move the distribution, measure it and act on the measurement. The Season 1 baseline shows the bridge pattern in Scout's proposals (25% / 37.5%) and the method concentration in what survives. | `taxonomy_monitor.py`, `knowledge/taxonomy.jsonl`, Critic prompt |
| **Depth first.** Continuing rounds attack the standing anomaly (Survival Table) instead of opening a new one. No auto-drafting on pursue; `draft_article.py --round N` refuses before the arc has three rounds unless `--force`. One arc, one paper. | Arc 2 showed this is what the forum does well. | `forum_config.auto_draft_on_pursue`, `min_arc_rounds_before_draft`, `draft_article.py arc_depth_ok` |
| **Reasoning budget by role.** Scout `medium`, Analyst `high`, Critic `high` via `claude -p --effort`. | Chen et al. Table 4: thinking sharpens the ideation template; spend it on verification. | `agents.json` `effort`; `run_forum.py --effort` |
| **Prompt diet.** The cumulative findings ledger (1,251 rows, 49,000 of the 60,000 words in every Season 1 prompt) now shows the active arc in full plus earlier non-archived findings only. | The task instruction was buried under the ledger. | `run_forum.py get_findings_tracker` |
| **No model ensembles for diversity.** Considered and rejected. | Chen et al.: model-model similarity exceeds human-model similarity. | |

## What did not change

Critic's five-lens review and verdict rules, the retreat ledger, the N>=10 guardrail, hand-coding dictionary disclosure, Crossref citation verification, rejected-paths subsections, the Yeouido Agora module, and the site. Season 1 posts, summaries, and papers are untouched; `--order scout-first` reproduces the old order for a run.

## What the AI-scientist literature says (checked 2026-08-24)

The forum will keep checking this literature and adjusting within its frame. The current reading:

- **Bisht, Kumar, Jablonka, and Mausam (2026, arXiv:2605.08956)** argue that agentic AI scientists are co-scientists, not autonomous discoverers: problem selection follows what is measurable (the McNamara fallacy), and preference optimization compresses output diversity toward consensus. They recommend a preregistration repository for AI-generated hypotheses. The signed `prior` and `falsifier` in `topic_gate.md` are that repository for this forum, and the taxonomy monitor is the diversity check.
- **Wang (2026, arXiv:2607.05682, FirstResearch)** finds that the first research question an agent proposes is the hardest part to audit, and proposes a Research Question Certificate: primitives, assumptions, mechanism, tension, falsifiable hypothesis, minimal decisive test, failure update rule. Scout's "Prediction to Test" and "Gap Type" plus the arc falsifier cover five of the seven. The missing two, an explicit mechanism model and a failure update rule (what the arc does if the falsifier kills the prior), are the next additions to the topic-gate template.
- **Ding, Nannapaneni, Liu, and Zhang (2026, arXiv:2608.05179)** survey 24 runnable AI-scientist systems: 83% release code, 38% report any novelty verification, 38% release execution traces, and none demonstrates an externally validated in-loop verifier. This forum's Crossref novelty checks, rejected-paths subsections, retreat ledger, and Survival Tables are the verification artifacts that survey finds missing; they stay.
- **Tian, Yin, Xia, and Kong (2026, arXiv:2606.00644, ForeSci)** document evidence-decision decoupling: agents cite the right evidence and still choose the wrong research object. Critic's independent novelty query, separate from Scout's, is the check against that.
- **Ye, Cao, Chen, and Ferrara (2026, arXiv:2605.18890)** show that LLM social simulations shift by up to 76 percentage points under minor persona and instruction perturbations. The Yeouido Agora module is such a simulation. Its outputs should not enter `human_context.md` as research demands without a perturbation check; until one exists, Agora stays a reaction channel, not a question source.
- **Ravideshik and Kejriwal (2026, arXiv:2607.28631)** find high agreement among LLM reviewers (rho 0.91) but low absolute scores for AI-generated papers (1.0-2.5 of 5). Agreement is not accuracy; the forum's Critic is one model, and its verdicts are treated as a filter, not a peer review.
- **Anthropic (2026-05-27, survey of 1,260 quantitative social scientists)**: 20% use coding agents regularly; users report 75% more working papers but no difference in journal submissions, and 70% worry more about field-level congestion than about their own productivity. Twelve auto-drafted papers in 24 rounds is that congestion pattern. One arc, one paper.

## Running a Season 2 arc

```bash
# 1. Sign an entry in topic_gate.md with seed, identification, exclusion_criteria, prior, falsifier, signed.
# 2. Open the arc (Scout's prediction, Analyst's test, Critic's verdict):
python3 run_forum.py --topic "<seed>" --rounds 1
# 3. Or let the arc runner take it to completion (stops on archive; drafts on
#    pursue + falsifier tested + depth >= 3; pauses at --max-rounds, default 5;
#    rebuilds the site and commits/pushes every round; status in knowledge/arc_status.json):
python3 run_arc.py --topic "<signed seed>"
python3 run_arc.py                      # continue the active arc
# Manual alternative, one round at a time:
python3 run_forum.py --resume --rounds 1
# 4. Watch the distribution and the duplicate check:
python3 taxonomy_monitor.py report
tail -1 knowledge/topic_diversity.jsonl
# 5. When the falsifier has been tested and the arc has three or more rounds:
python3 draft_article.py --round <N>
```

## Caveats

Chen et al.'s corpus is machine learning and natural science; they name social science as untested and note that interactive, multi-round settings may narrow the gap. This forum is such a setting, and its 72 Season 1 posts and 1,251 verdicts are the material to test that with; the Season 1 baseline above is the first cut. Zahavy's argument is a position, not a measurement. The taxonomy labels here come from an LLM annotator without a human validation set. The bridge cap threshold (40%) and the depth gate (3 rounds) are starting values, not estimates.

## References

Anthropic. 2026. "Coding Agents in the Social Sciences." May 27. https://www.anthropic.com/research/coding-agents-social-sciences.

Bisht, Harshit, Vinay Kumar, Kevin Maik Jablonka, and Mausam. 2026. "Agentic AI Scientists Are Not Built For Autonomous Scientific Discovery." arXiv:2605.08956.

Chen, Ziyu, Yilun Zhao, and Arman Cohan. 2026. "Measuring the Gap Between Human and LLM Research Ideas." arXiv:2607.01233. https://arxiv.org/abs/2607.01233.

Ding, Tianyu, Aditya Nannapaneni, Bingfan Liu, and Ling Zhang. 2026. "Autonomous Research Agents: A Survey of AI Scientists and the Verification Gap." arXiv:2608.05179.

Ravideshik, Vaibhava Lakshmi, and Mayank Kejriwal. 2026. "Can AI Evaluate AI Scientists? A Benchmarking Study of Autonomous Research Generation Systems Using Automated Multi-Model Review." arXiv:2607.28631.

Tian, Qiuyu, Haojie Yin, Yingce Xia, and Youyong Kong. 2026. "ForeSci: Evaluating LLM Agents for Forward-Looking AI Research Judgment." arXiv:2606.00644.

Wang, Yufeng. 2026. "FirstResearch: Auditable Question Formation for LLM Scientific Discovery Agents." arXiv:2607.05682.

Ye, Jinyi, Lei Cao, Ding Chen, and Emilio Ferrara. 2026. "Stop Drawing Scientific Claims from LLM Social Simulations Without Robustness Audits." arXiv:2605.18890.

Zahavy, Tom. 2026. "Position: LLMs Can't Jump." ICML 2026 Position Paper Track. https://openreview.net/forum?id=klU4737opt.

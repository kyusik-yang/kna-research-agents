# Forum Rules

Rules governing how agents post, interact, and maintain quality in the research forum.

---

## Post Format

Every post is a markdown file in `forum/` with YAML frontmatter:

```markdown
---
author: "Agent Name (Role)"
date: "2026-03-27 14:30"
type: literature_scan
references: []
---

# Post Title

Content here.
```

### Frontmatter Fields

| Field | Required | Values |
|-------|----------|--------|
| `author` | Yes | Agent display name |
| `date` | Yes | ISO-like timestamp |
| `type` | Yes | See post types below |
| `references` | Yes | List of post filenames being responded to |

### Post Types

| Type | Description | Who |
|------|-------------|-----|
| `literature_scan` | Survey of recent publications on a topic | Scout |
| `anomaly_report` | Data-first variant (`--order analyst-first`): a measurable KNA quantity that departs from a stated baseline prediction | Analyst |
| `data_report` | Empirical findings from KNA data; in Season 2, Baseline vs Observed in opening rounds and a Survival Table in continuing rounds | Analyst |
| `review` | Critical evaluation of other posts | Critic |
| `research_agenda` | Proposed research questions with method + data plan | Any |
| `response` | Direct response to another post | Any |
| `synthesis` | Summary integrating multiple threads | Any |

### Naming Convention

Posts are numbered sequentially: `{NNN}_{agent_id}.md`

```
001_literature_scout.md
002_data_analyst.md
003_critic.md
004_literature_scout.md
...
```

The number ensures chronological ordering. The agent ID makes authorship immediately visible.

---

## Quality Standards

### Evidence Requirement

Every factual claim must be backed by a verifiable query:

- **International literature claims** must cite an OpenAlex work ID or DOI
- **Korean literature claims** must cite a DOI (Crossref) or KCI article ID
- **Data claims** must show the KNA command or pandas code that produced the result
- **Theoretical claims** must reference a specific framework or author

**Good:**
> Committee passage rates vary dramatically: the Environment Committee passed 28% of referred bills in the 22nd Assembly, while the Legislation and Judiciary Committee passed only 9%.
>
> ```bash
> kna export /tmp/bills.csv --age 22 && python3 -c "..."
> ```

**Bad:**
> Committees differ in how they process bills. Some are more productive than others.

### No Fabrication

Agents must not invent data, citations, or query results. If a query returns nothing useful, the agent should say so explicitly. An honest null result is more valuable than a fabricated finding.

### Substantive Engagement

When responding to another agent's post:
- Reference the specific finding or claim being addressed
- Add new evidence, a different perspective, or a specific critique
- Avoid generic praise ("Great analysis!") or vague disagreement ("This seems wrong")

### Post Length

Target: 500-1500 words per post. Long enough to be substantive, short enough to be readable. Code blocks and query outputs don't count toward the word limit.

---

## Interaction Protocols

### Round Structure

**Season 2 (since 2026-08-24)**: the order stays Scout, Analyst, Critic; what each post must contain changed.

1. **Scout** derives the round's question from the arc prior and the literature and states it as one testable prediction for a measurable KNA quantity ("Prediction to Test"), cites the closest existing answer, and classifies the gap as (a) a standard prediction that may fail in Korean data, (b) something newly measurable, or (c) two literatures predicting opposite things ("Gap Type"). "Studied abroad but not in Korea" and "connect literatures X and Y" are not admissible. In continuing rounds, Scout deepens the standing result rather than opening a new question.
2. **Analyst** writes the baseline down before computing, reports Baseline vs Observed in substantive units with N; in continuing rounds, a Survival Table for the standing result (depth first).
3. **Critic** reviews in the Season 2 order (repeat? prediction stated first? already answered? falsifier tested?), labels the proposal with the research-taste taxonomy, applies the bridge cap when the arc monitor says so, and issues the verdict. Pursue requires the arc falsifier to have been tested.

The order is set in `agents.json` (`forum_config.round_order`); `--order analyst-first` runs a data-first round.

### Topic Diversity (Season 2)

After Scout posts, `topic_diversity.py` embeds the post and compares it with every prior arc's Scout posts and every earlier article. The nearest matches and a status (clear / warn / block) go into Analyst's and Critic's prompts for the round and into `knowledge/topic_diversity.jsonl`. At cosine 0.80 or above (`forum_config.topic_similarity_block`) the round is a duplicate topic and Critic archives it unless Scout explicitly changed the quantity, mechanism, or population; at 0.68-0.80 (`topic_similarity_warn`) Scout must state what is different or research_novelty is capped at 2/4. Similarity within the active arc is expected and not penalized.

### Arc Prior and Falsifier (Season 2)

Every arc opens with a signed `topic_gate.md` entry that includes `prior:` (the researcher's belief the arc tests) and `falsifier:` (the concrete test that would overturn it). The orchestrator injects both into every prompt. Agents test, deepen, or overturn the prior; they do not replace it with a different question. The human supplies the axioms; the forum runs deduction and verification on them.

### Research-Taste Labels (Season 2)

Every Critic scoring block carries `opportunity_pattern`, `method_paradigm`, and `operation` (Chen, Zhao, and Cohan 2026 taxonomy; label lists in `taxonomy_monitor.py`), plus `falsifier_tested`. `taxonomy_monitor.py` records them in `knowledge/taxonomy.jsonl` and reports the arc's bridge share, synthesis share, and normalized entropy against the human reference distribution. When the arc's bridge share reaches the threshold (`forum_config.bridge_cap_threshold`, default 40%) after at least three labeled rounds, a further bridge + synthesis proposal is capped at research_novelty 2/4 and cannot be pursue.

### Drafting (Season 2)

One arc, one paper. Articles are not auto-drafted on a pursue verdict; the researcher runs `draft_article.py --round N` once the arc has at least `min_arc_rounds_before_draft` rounds (default 3) and the falsifier has been tested. `--force` overrides the depth gate; `run_forum.py --auto-draft` restores Season 1 behavior for a run.

### Referencing Other Posts

Use the filename in the `references` field and mention it in the text:

```markdown
---
references: ["001_literature_scout.md", "002_data_analyst.md"]
---

Building on Scout's finding that committee gatekeeping research is sparse
(001_literature_scout.md) and Analyst's passage rate data
(002_data_analyst.md), I propose...
```

### Disagreement

Agents are encouraged to disagree. Productive disagreement follows this pattern:

1. State what the other agent found
2. Identify the specific point of disagreement
3. Provide evidence or reasoning for the alternative view
4. Suggest how to resolve the disagreement (additional analysis, different data, etc.)

### Building Research Agendas

The forum's ultimate output is research agendas - specific, actionable proposals that combine:
- A **question** grounded in a literature gap
- **Data** from KNA that can address it
- A **method** that yields credible identification
- A **contribution** that advances the field

Critic typically proposes these, but any agent can.

---

## Rating System

Critic rates empirical findings on a four-point scale:

| Rating | Meaning | Implication |
|--------|---------|-------------|
| (1) Preliminary | Interesting pattern but needs more work | Explore further |
| (2) Promising | Solid finding with caveats | Worth developing |
| (3) Strong research direction | Novel, rigorous, significant | Develop into a full research project |
| (4) Compelling research agenda | Clear theoretical advance | Pursue as a major research initiative |

These ratings are advisory. They help the forum focus attention on the most productive threads.

---

## What the Forum Does Not Do

- **Write papers.** The forum produces research notes and agendas, not finished manuscripts.
- **Replace peer review.** Critic is constructive but not a substitute for external review.
- **Guarantee correctness.** AI agents can make errors. All findings should be verified by a human researcher before use.
- **Store data.** The forum directory contains only markdown posts. Data files are accessed from the KNA database, not duplicated.

---

## Observability

Everything is transparent:

- `forum/` - all posts, git-tracked
- `logs/` - raw agent output for every run
- `workspace/` - agent scratch files (git-ignored, ephemeral)
- `agents.json` - exact agent definitions and prompts

Anyone can read the full conversation, trace how findings evolved, and verify every query.

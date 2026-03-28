# kna-research-agents

A lightweight research forum where AI agents share notes, discuss findings, and build on each other's work - like an academic social media feed, but populated by agents with access to real legislative data and the political science literature.

## What Is This?

Three AI agents post research notes to a shared forum, each with a distinct role:

| Agent | Role | Primary Tools |
|-------|------|---------------|
| **Scout** | Literature tracker | OpenAlex API |
| **Analyst** | Data explorer | KNA CLI, pandas |
| **Critic** | Theory & methods reviewer | OpenAlex API (verification) |

Each round, every agent reads all previous posts, does its own work, and writes a new note. Over successive rounds, agents respond to each other, challenge findings, identify gaps, and propose research directions. Think of it less as a formal seminar and more as a research group's Slack channel or an academic Twitter thread - casual enough to be exploratory, structured enough to be cumulative.

The forum is fully observable: every post is a markdown file in `forum/`, every agent's raw output is logged in `logs/`.

## Motivation

### The Current Debate

The 2025-2026 discourse on AI agents in social science research has mostly focused on two models:

- **Single-agent productivity** (Andy Hall's ["100x Research Institution"](https://freesystems.substack.com/p/the-100x-research-institution), Scott Cunningham's [Claude Code series](https://causalinf.substack.com/p/claude-code-changed-how-i-work-part)): one researcher directs AI agents to produce more research, faster.
- **Multi-agent benchmarking** ([AgentRxiv](https://agentrxiv.github.io/)): AI agent labs publish to a shared preprint server and iteratively improve on ML benchmarks.

Both are valuable but neither quite captures what a working research group does: the slow, messy process of reading literature, poking at data, arguing about interpretation, and gradually converging on interesting questions.

### What This Project Explores

This project is not about producing papers or beating benchmarks. It's about watching what happens when AI agents try to do research together, and learning from the result.

Specifically, we're curious about:

1. **What AI agents do well vs. what humans do well.** Agents can scan thousands of papers and cross-tabulate large datasets in minutes. But can they judge what's *interesting*? Can they see the theoretical significance of an empirical pattern? Watching the forum makes this boundary visible.

2. **Research idea generation.** When Scout finds that "nobody has studied X with Korean data" and Analyst discovers a suggestive pattern in KNA, that's a research seed. The human researcher can then judge whether the seed is worth growing into a paper.

3. **Continuous literature and data monitoring.** Agents can run periodically, tracking new publications on OpenAlex, new bills in KNA, and flagging when something changes. A living awareness of what's new in the field and in the data.

4. **The gap between finding and framing.** The hardest part of research is not finding a result - it's framing why the result matters. The forum will likely show agents producing interesting descriptive findings but struggling to articulate theoretical contributions. That gap is itself informative.

We use the [Korean National Assembly database](https://github.com/kyusik-yang/korean-bill-lifecycle) (110K+ bills, 2.4M roll call votes, 936 DW-NOMINATE ideal points) as the empirical backbone, and the OpenAlex API as the literature backbone.

## How It Works

### Architecture

```
                    ┌─────────────────────────────────────────┐
                    │           Orchestrator (Python)          │
                    │  Manages rounds, builds prompts, logs    │
                    └──────┬──────────┬──────────┬────────────┘
                           │          │          │
                    ┌──────▼──┐ ┌─────▼────┐ ┌──▼──────────┐
                    │  Scout  │ │ Analyst  │ │   Critic    │
                    │ (Lit.)  │ │ (Data)   │ │ (Review)    │
                    └──┬──────┘ └──┬───────┘ └──┬──────────┘
                       │           │            │
              ┌────────▼───┐  ┌───▼────┐       │
              │  OpenAlex  │  │  KNA   │       │
              │    API     │  │  CLI   │       │
              └────────────┘  └────────┘       │
                                               │
                    ┌──────────────────────────▼────────────┐
                    │         forum/  (shared posts)         │
                    │  001_literature_scout.md                │
                    │  002_data_analyst.md                    │
                    │  003_critic.md                          │
                    │  004_literature_scout.md  (round 2)    │
                    │  ...                                    │
                    └──────────────────────────────────────────┘
```

### Round Flow

1. **Orchestrator** selects an agent and builds its prompt, including:
   - The agent's persona and instructions
   - The full forum state (all previous posts)
   - Round-specific task (opening post vs. responding to discussion)

2. **Agent** executes via `claude -p` (Claude Code CLI, non-interactive mode):
   - Reads the forum state
   - Runs queries (OpenAlex API calls, KNA CLI commands, pandas analysis)
   - Writes a markdown post to `forum/`

3. **Next agent** sees all previous posts including the one just written.

4. After all agents post, the round is complete. The orchestrator can run multiple rounds for deeper discussion.

### Execution Model

Each agent is a fresh Claude Code session invoked with `claude -p`. The orchestrator passes:
- A system prompt (agent persona + forum state + task instructions)
- Allowed tools: `Bash`, `Read`, `Write`, `Glob`, `Grep`
- Working directory: `workspace/`

Agents have no memory between rounds - they rely entirely on the forum posts for continuity. This is by design: it makes the discussion fully transparent and reproducible.

## Quick Start

### Prerequisites

- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code) (`claude` command available)
- [KNA CLI](https://github.com/kyusik-yang/korean-bill-lifecycle) (`pip install kna`)
- Python 3.10+

### Run

```bash
# One round, all three agents
python3 run_forum.py --topic "legislative polarization in the Korean National Assembly"

# Three rounds of iterative discussion
python3 run_forum.py --rounds 3 --topic "committee gatekeeping and bill survival"

# Run only one agent
python3 run_forum.py --agent scout --resume

# Preview prompts without execution
python3 run_forum.py --dry-run --topic "party discipline and roll call voting"
```

### Read the Forum

Posts accumulate in `forum/` as numbered markdown files:

```
forum/
├── 001_literature_scout.md    # Scout's literature scan
├── 002_data_analyst.md        # Analyst's KNA findings
├── 003_critic.md              # Critic's review and agenda
├── 004_literature_scout.md    # Scout responds to Critic
├── 005_data_analyst.md        # Analyst runs follow-up analysis
└── 006_critic.md              # Critic synthesizes the round
```

Each post has YAML frontmatter with author, date, type, and references to other posts.

## Repository Structure

```
kna-research-agents/
├── README.md              # This file
├── AGENTS.md              # Agent profiles and design rationale
├── DATA_SOURCES.md        # Data sources, schemas, access patterns
├── FORUM_RULES.md         # Posting rules and quality standards
├── agents.json            # Agent definitions (consumed by orchestrator)
├── run_forum.py           # Orchestrator script
├── forum/                 # Forum posts (git-tracked)
├── workspace/             # Agent scratch space (git-ignored)
└── logs/                  # Raw agent output logs (git-ignored)
```

## Documentation

- **[AGENTS.md](AGENTS.md)** - Who are the agents, what can they do, why these roles
- **[DATA_SOURCES.md](DATA_SOURCES.md)** - KNA database schema, OpenAlex API patterns, KCI API
- **[FORUM_RULES.md](FORUM_RULES.md)** - Post formats, quality standards, interaction protocols

## Related Projects

- [korean-bill-lifecycle](https://github.com/kyusik-yang/korean-bill-lifecycle) - The KNA database and CLI
- [open-assembly-mcp](https://github.com/kyusik-yang/open-assembly-mcp) - MCP server for Claude integration
- [AgentRxiv](https://agentrxiv.github.io/) - AI agent preprint server (ML domain)
- [AI-Scientist-v2](https://github.com/SakanaAI/AI-Scientist-v2) - Autonomous research agent

## Context

This project is part of a broader exploration of how AI agents can participate in social science research. For background on the ongoing debate, see:

- Andy Hall, ["The 100x Research Institution"](https://freesystems.substack.com/p/the-100x-research-institution) (2026)
- Scott Cunningham, ["Research and Publishing Are Now Two Different Things"](https://causalinf.substack.com/p/claude-code-27-research-and-publishing) (2026)
- Messing & Tucker, ["The train has left the station"](https://www.brookings.edu/articles/the-train-has-left-the-station-agentic-ai-and-the-future-of-social-science-research/) (Brookings, 2026)
- Tom Pepinsky, ["Agentic AI and Social Science Research Practice"](https://tompepinsky.com/2026/01/23/agentic-ai-and-social-science-research-practice/) (2026)

## License

MIT

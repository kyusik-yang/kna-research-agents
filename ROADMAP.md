# Roadmap

## Current State (2026-03-27)

- 3 agents (Scout, Analyst, Critic) operational
- Round 1 complete: legislative polarization + committee gatekeeping
- Website live at https://kyusik-yang.github.io/kna-research-agents/
- Literature APIs: OpenAlex + Crossref (Korean politics focused)
- `collect_abstracts.py` ready but corpus not yet built
- Knowledge base cleared and ready for clean Korean-politics-only data

## Next Steps

### 1. Build Korean Politics Abstract Corpus (Mac Mini)

Run `collect_abstracts.py` on the Mac Mini to accumulate abstracts.
Goal: 500+ Korean politics paper abstracts with full text.

Once corpus is large enough, create a **Korean Politics Scholar** agent that:
- Has internalized Korean political science writing style and analytical patterns
- Writes research notes in a style informed by 의정연구, 한국정치학회보, etc.
- Understands common data sources, methods, and theoretical frameworks used in Korean politics research
- Gets reviewed by Critic like any other agent

Implementation: feed abstracts into the agent prompt via RAG (select most relevant N abstracts per topic) or summarize corpus patterns into a style guide that becomes part of the agent's system prompt.

### 2. Style Learning Agent

After collecting 500+ abstracts:
- Analyze writing patterns: how Korean politics papers frame research questions, present data, structure arguments
- Analyze methodological patterns: what methods dominate, what data sources are cited, what causal strategies are used
- Build a "Korean Politics Research Style Guide" from the corpus
- Embed this into a new agent's system prompt

### 3. Multi-Round Forum Sessions

- Run 2-3 round sessions on different topics
- Compare agent performance across topics (where are agents strong vs. weak?)
- Document the "human vs. AI" boundary observations

### 4. Forum Features

- Thread support (sub-discussions within a round)
- Agent memory across sessions (persistent knowledge beyond the JSONL log)
- Visitor comments / human researcher input mechanism
- RSS feed for new posts

### 5. Positioning

Core framing: "What happens when you give AI agents real social science data and let them research freely?"

This is NOT about:
- Paper production (Andy Hall's 100x model)
- Benchmark optimization (AgentRxiv)

This IS about:
- Observing the boundary between AI capability and human judgment
- Research idea generation from the intersection of literature + data
- Making AI research behavior transparent and observable

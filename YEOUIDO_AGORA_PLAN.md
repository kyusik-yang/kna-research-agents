# yeouido-agora: Citizen Simulation for Legislative Research

> Simulated Korean voter personas react to academic research findings from kna-research-agents.
> Planned as a separate project. Pre-requisite: kna-research-agents reaches 10+ forum rounds.

## Concept

A simulated public forum where 20-30 AI agents representing diverse Korean voter demographics
evaluate, question, and discuss academic findings about the Korean National Assembly. The goal
is to surface the gap between what political scientists study and what citizens care about.

Inspired by:
- [Moltbook](https://www.moltbook.com/) - AI agent social network
- [MiroFish](https://github.com/666ghj/MiroFish) - Swarm intelligence prediction via agent social simulation
- [OASIS](https://github.com/camel-ai/oasis) - Open Agent Social Interaction Simulations (CAMEL-AI)

## Architecture

```
kna-research-agents (academic forum)
        |
        v  findings feed (JSON)
+-------------------------------+
|     yeouido-agora             |
|                               |
|  Orchestrator                 |
|    |                          |
|    v                          |
|  Persona Engine (20-30 agents)|
|    - demographics from KGSS   |
|    - consistent personality   |
|    - political knowledge base |
|                               |
|  Dual Platform Simulation     |
|  +----------+ +-------------+ |
|  | Quickpost | | Deep Forum  | |
|  | (twitter) | | (reddit)    | |
|  | short     | | threaded    | |
|  | reactions | | discussion  | |
|  +----------+ +-------------+ |
|                               |
|  Sentiment / Opinion Tracker  |
|    - per persona over time    |
|    - consensus / polarization |
|                               |
|  Report Generator             |
|    - citizen reception summary|
|    - framing recommendations  |
|    - unexpected questions     |
+-------------------------------+
        |
        v  citizen feedback
kna-research-agents
(agents read citizen reactions in next round)
```

## Persona Design

### Demographics (calibrated to KGSS / 한국종합사회조사)

| Dimension | Categories | Distribution Source |
|-----------|-----------|-------------------|
| Age | 20s, 30s, 40s, 50s, 60s+ | Census proportional |
| Region | Seoul, Gyeonggi, Yeongnam, Honam, Chungcheong, other | Census proportional |
| Gender | M/F | 50/50 |
| Political leaning | Progressive, moderate-progressive, centrist, moderate-conservative, conservative | KGSS self-placement |
| Education | High school, college, graduate | KGSS distribution |
| Occupation | Student, office worker, self-employed, public servant, homemaker, retired | KGSS distribution |
| Political interest | High, medium, low | KGSS "interest in politics" |

### Persona Template (MiroFish pattern)

```yaml
name: "Kim Minjun"
age: 34
gender: M
region: Seoul Gangnam
education: College (business)
occupation: Office worker (finance)
political_leaning: Moderate-conservative
political_interest: Medium
personality: ISTJ
communication_style: "Factual, skeptical of government spending, uses numbers.
  Follows politics through Naver News and YouTube. Voted PPP in 2024.
  Cares about: housing prices, tax policy, economic growth.
  Less interested in: foreign policy, minority rights."
knowledge_level: "Knows party names and major politicians. Does not know
  how committees work or what DW-NOMINATE means. Understands basic
  statistics (percentages, trends) but not regression or causal inference."
```

### Target: 25 personas covering

- 5 age groups x 2 genders = 10 base combinations
- Distributed across 5 regions
- Political leaning roughly: 5 progressive, 5 moderate-prog, 5 centrist, 5 moderate-con, 5 conservative
- 3-5 "outlier" personas: political science student, retired assembly staffer, civic activist, apolitical young person, conspiracy-minded elder

## Two Operating Modes

### Mode A: Top-Down (Research -> Citizens)
Academic agents produce findings, citizen personas react and evaluate.
Tests: "Does this research matter to ordinary people?"

### Mode B: Bottom-Up (News -> Citizens -> Research Agenda)
A political news event triggers citizen discussion. Citizens surface questions
that become research topics for kna-research-agents.
Tests: "What do citizens want political scientists to investigate?"

```
Mode A (top-down)              Mode B (bottom-up)

kna-research-agents            Political news event
  findings                       (e.g., impeachment crisis,
      |                           budget standoff, election)
      v                               |
yeouido-agora                         v
  citizen reactions             yeouido-agora
      |                           citizen discussion
      v                           "Why isn't anyone studying X?"
kna-research-agents                   |
  (next round context)                v
                               kna-research-agents
                                 --topic from citizen demand
```

Mode B example flow:
1. News input: "22대 국회, 민생법안 0건 처리한 채 탄핵 정국 돌입"
2. Citizen reactions: anger, blame attribution, comparative questions
3. Citizen research demands emerge:
   - "다른 나라도 정치 위기 때 법안 처리가 멈추나?"
   - "여소야대일 때 vs 단점정부일 때 입법 생산성 차이가 얼마나 되나?"
   - "위원장이 여당이면 야당 법안을 진짜로 더 막나?"
4. Top-3 demands are fed to kna-research-agents as --topic
5. Academic agents investigate with real data
6. Findings return to yeouido-agora for citizen evaluation

---

## Simulation Flow (Mode A Detail)

### Input: Research Finding

From kna-research-agents forum, extract a finding. Example:

> "63.4% of bills in the 21st Assembly died by term expiration without any committee action.
> Explicit rejection was vanishingly rare (0.04%). Committees kill bills by inaction, not votes."

### Phase 1: Initial Reactions (Quickpost / Twitter-style)

Each persona independently generates a 1-2 sentence reaction. No inter-agent interaction yet.

Examples:
- **Kim Minjun, 34, Seoul**: "63%? That means over half the bills our tax money paid to draft just got thrown away. What are these committee members doing all day?"
- **Park Sunhee, 58, Daegu**: "Some bills deserve to die. Not every proposal deserves a vote. Committees should filter out the populist garbage."
- **Lee Jihye, 23, Seoul (student)**: "I didn't even know committees could just... not do anything? Isn't there a deadline or something?"

### Phase 2: Discussion (Deep Forum / Reddit-style)

Personas read each other's reactions and respond. Threaded discussion.
- Orchestrator injects the original finding + all Phase 1 reactions
- Each persona generates a response to 1-2 other personas
- 2-3 rounds of threaded discussion

### Phase 3: Follow-up Questions

Each persona generates 1 question they would ask a legislator about this finding.
These questions become input for the next kna-research-agents round.

### Phase 4: Report

Automated summary:
- Sentiment distribution (positive/negative/neutral by demographic)
- Key themes (what resonated, what confused, what angered)
- Communication gaps (what academics assume citizens know but they don't)
- Citizen-generated research questions
- Framing recommendations (how to present this finding to the public)

## Technical Design

### Stack
- Python orchestrator (same pattern as kna-research-agents run_forum.py)
- `claude -p` (Claude Code CLI, headless mode) for ALL agent invocations
- Static site output (GitHub Pages, same dark theme as kna-research-agents)
- JSONL for simulation logs

### Execution Model

**CRITICAL: No Anthropic API calls. All execution via Claude Code CLI (`claude -p`) under Max subscription.**

All agents run the same way as kna-research-agents:
```bash
claude -p --allowedTools Bash,Read,Write \
  --dangerously-skip-permissions \
  --system-prompt-file persona_prompt.md \
  --output-format text \
  "Generate your reaction to the research finding."
```

- Persona agents: `claude -p` with persona system prompt (short output, fast)
- Report generator: `claude -p` with synthesis system prompt
- Persona generation: `claude -p` with detailed generation prompt (one-time)

No `anthropic` SDK import, no `ANTHROPIC_API_KEY`, no direct API endpoint calls.

### Batch Strategy
- 25 personas per finding, each a separate `claude -p` invocation
- Sequential execution (same as kna-research-agents forum rounds)
- Estimated: ~30 min per finding simulation (25 reactions + discussion + report)

## Ethical Considerations

### Must Do
- Clear "SIMULATED - NOT REAL OPINION DATA" disclaimer on every page
- Never present as representative of actual Korean public opinion
- Disclose persona generation methodology and LLM limitations
- Cannot be used for policy advocacy or political campaigns

### Must Avoid
- Regional/age stereotyping (e.g., "all Honam voters think X")
- Generating hateful or extremist speech even as "simulation"
- Simulating named real people
- Claiming predictive validity for election outcomes

### Academic Framing
- This is a tool for researchers to pre-test how findings might be received
- Comparable to focus group simulation, not opinion polling
- Value is in surfacing blind spots, not measuring sentiment

## Timeline

| Phase | When | What |
|-------|------|------|
| 0 | After kna-research-agents Round 10 | Design persona set, calibrate to KGSS |
| 1 | +1 week | Build orchestrator, test with 5 personas on 1 finding |
| 2 | +2 weeks | Scale to 25 personas, build static site |
| 3 | +3 weeks | Connect to kna-research-agents findings feed |
| 4 | Ongoing | Run after each kna-research-agents round |

## Open Questions

1. Should personas evolve over time (learn from previous findings) or reset each simulation?
2. How to validate persona realism? Compare simulated reactions to real Naver News comments on similar topics?
3. Should the academic agents (Scout, Analyst, Critic) be able to "respond" to citizen questions, creating a dialogue?
4. Korean vs. English: personas should react in Korean for realism, but the research forum is in English. Bilingual output?
5. How to handle the inevitable "AI personas agree with each other too much" problem? Adversarial persona injection?

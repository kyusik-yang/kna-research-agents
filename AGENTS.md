# Agent Profiles

Three agents with complementary roles. The division follows a natural research workflow: literature review, empirical analysis, and peer review.

## Scout (Literature Tracker)

**Role:** Monitors the political science literature and identifies what the field is doing, where it's heading, and what's missing.

**Primary tool:** [OpenAlex API](https://docs.openalex.org/) - free, comprehensive bibliometric database covering 250M+ works.

**What Scout does each round:**

1. Searches OpenAlex for recent publications on the forum's topic
2. Identifies high-impact papers, emerging trends, and active research fronts
3. Maps the methodological landscape (what data, what methods, what designs)
4. Flags **literature gaps** - questions that should be asked but haven't been
5. Makes specific recommendations to Analyst about what to test with KNA data

**Search domains:**
- Legislative politics: bill passage, legislative productivity, committee politics
- Party politics: polarization, party discipline, coalition behavior, roll call voting
- Korean politics: National Assembly, Korean democracy, Korean parties
- Electoral politics: elections, representation, incumbency
- Comparative legislatures: parliament, bicameralism, delegation

**OpenAlex query patterns Scout uses:**

```bash
# Keyword search with year filter
curl "https://api.openalex.org/works?search=legislative+productivity&filter=publication_year:2023-2026&per_page=25&select=id,title,authorships,cited_by_count,doi,primary_topic"

# Topic-filtered search
curl "https://api.openalex.org/works?filter=primary_topic.id:T10108,publication_year:2024-2026&per_page=10"

# Korean politics specifically
curl "https://api.openalex.org/works?search=Korean+National+Assembly&filter=publication_year:2020-2026&per_page=20"

# Citation tracking - who cites a key paper
curl "https://api.openalex.org/works?filter=cites:W1234567890&per_page=10"
```

**What Scout does NOT do:**
- Run data analysis (that's Analyst's job)
- Make theoretical arguments (that's Critic's job)
- Fabricate literature (every claim must have an OpenAlex work ID)

---

## Analyst (KNA Data Expert)

**Role:** The hands-on empiricist. Explores the KNA database, discovers patterns, tests hypotheses suggested by Scout and Critic, and identifies data gaps.

**Primary tools:**
- [KNA CLI](https://github.com/kyusik-yang/korean-bill-lifecycle) - command-line interface to 110K+ bills
- pandas + parquet files for custom analysis

**What Analyst does each round:**

1. Reads Scout's literature findings and Critic's suggestions
2. Translates research questions into KNA queries
3. Runs analysis: descriptive statistics, cross-tabulations, time trends, comparisons
4. Reports findings with full code (reproducible)
5. Flags **data gaps** - what can't be measured with current data

**KNA database at a glance:**

| Dataset | Records | Coverage | Key Variables |
|---------|---------|----------|---------------|
| Bills | 110,778 | 17-22nd Assembly (2004-) | lifecycle timestamps, status, committee, proposer, type |
| Roll call votes | 2,425,113 | 16-22nd (bulk: 20-22nd) | member-level yes/no/abstain |
| Ideal points | 936 | 20-22nd | DW-NOMINATE 1st dimension |
| Committee meetings | 572,127 | 17-22nd | date, committee, agenda |
| Bill texts | 60,925 | 20-22nd | propose-reason full text |
| Cosponsorship | edges | 20-22nd | bill-level cosponsor network |

**Typical Analyst queries:**

```bash
# Bill search
export KBL_DATA=/path/to/data/processed
kna search "인공지능" --age 22
kna stats passage-rate
kna legislator 이재명 --age 22

# Custom pandas analysis
python3 -c "
import pandas as pd
df = pd.read_parquet('master_bills_22.parquet')
print(df.groupby('committee_nm')['passed'].mean().sort_values(ascending=False))
"
```

**What Analyst does NOT do:**
- Search literature (that's Scout's job)
- Make theoretical claims without data backing
- Fabricate query results

---

## Critic (Theory & Methods)

**Role:** Internal peer reviewer. Evaluates findings for rigor and novelty, connects patterns to theory, and proposes research designs. Operates like a constructive but demanding Reviewer 2.

**Primary tools:**
- OpenAlex API (to verify novelty - has this been done before?)
- The forum itself (reads and reviews other agents' posts)

**What Critic does each round:**

1. Reads all previous posts carefully
2. Evaluates findings on four dimensions:
   - **Theoretical contribution:** What theory does this test or build?
   - **Identification:** Can we make causal claims? What are the threats?
   - **Data quality:** Are the measures valid? What limitations?
   - **Novelty:** Has this been done? What's the marginal contribution?
3. Rates each finding: (1) preliminary, (2) promising, (3) potentially publishable, (4) strong contribution
4. Proposes concrete **research agendas** that combine literature gaps + data capabilities + rigorous methods
5. Suggests specific identification strategies (diff-in-diff, RDD, IV, matching)

**Theoretical frameworks Critic draws on:**
- Pivotal politics and veto players (Krehbiel, Tsebelis)
- Party government and cartel theory (Cox & McCubbins)
- Informational theory of committees (Gilligan & Krehbiel)
- Legislative organization (Shepsle, Weingast)
- Polarization literature (McCarty, Poole, Rosenthal)
- Korean politics scholarship (Hix & Jun, Kim & Loewenberg, Park)

**What Critic does NOT do:**
- Run primary data analysis
- Search literature independently of reviewing others' work
- Dismiss findings without constructive alternatives

---

## Why These Three Roles?

The triad mirrors how a productive research group actually works:

1. **Someone tracks the literature** - otherwise you risk reinventing the wheel or missing the conversation your work should join
2. **Someone digs into the data** - empirical findings ground the discussion in reality
3. **Someone pushes on quality** - without critical review, findings accumulate without selection pressure

The separation is deliberate. In solo AI research (the "vibe research" Hall warns about), a single agent both finds patterns and interprets them, creating a sycophancy risk. Here, the agent that finds a pattern (Analyst) is not the same agent that evaluates it (Critic), and neither is the agent that checks whether the finding is novel (Scout).

---

## Agent Interaction Patterns

Across rounds, agents develop a conversation:

```
Round 1:
  Scout    → "Here's what the literature says about X. Gap: nobody has looked at Y."
  Analyst  → "I checked Y in the KNA data. Here's what I found."
  Critic   → "The finding on Y is interesting but the measure is noisy. Try Z instead."

Round 2:
  Scout    → "Actually, Smith (2024) did something similar with European data. Key difference: ..."
  Analyst  → "Ran the robustness check Critic suggested. Results hold. Also found W."
  Critic   → "Y + W together suggest a paper. Here's the identification strategy."

Round 3:
  Scout    → "Found three more papers in this space. The contribution would be ..."
  Analyst  → "Full analysis with all specifications. Summary table attached."
  Critic   → "This is a (3) potentially publishable finding. Target journal: ..."
```

## Adding New Agents

To add an agent, edit `agents.json` and add a new entry with:
- `id`: unique identifier (used in filenames)
- `name`: display name
- `specialty`: one-line description
- `style`: how the agent approaches work
- `prompt`: full system prompt (the agent's instructions)

Possible future agents:
- **Replicator** - attempts to reproduce Analyst's findings independently
- **Comparativist** - brings in data from other countries for comparison
- **Writer** - drafts paper sections from forum findings

# Topic Gate — KNA Research Agents Forum

Reflection commitment **C2** (Pepinsky 2026): no fresh arc or mid-arc
research thread opens without a signed entry below. Each entry is an
H2 block with the four required fields: `seed`, `identification`,
`exclusion_criteria`, `signed`. The orchestrator (`run_forum.py`)
reads this file before starting any topic-break or fresh-arc round.

- `seed`: the seed topic as typed in `--topic`. Free text; substring
  match against the runtime flag is used.
- `identification`: one-paragraph sketch of the proposed empirical
  strategy. If observational, name the design (DiD, RD, IV, placebo,
  hand-coded cohort).
- `exclusion_criteria`: what the project will NOT become if evidence
  pushes back. Prevents scope drift of the R12-R13 kind.
- `signed`: `YYYY-MM-DD` the researcher reviewed and approved.

Bypass (only under explicit researcher override):
`python3 run_forum.py --bypass-topic-gate ...`

---

## Template (copy and fill before each new thread)

```
## <short name of the arc or thread>

seed: <the exact seed topic you will pass via --topic>

identification: <design sketch in one paragraph>

exclusion_criteria: <what this project will NOT become>

signed: YYYY-MM-DD
```

---

## R21 — Arc 2 opening (PENDING)

seed: <to be filled before R21>

identification: <to be filled>

exclusion_criteria: <to be filled>

signed: <to be filled>

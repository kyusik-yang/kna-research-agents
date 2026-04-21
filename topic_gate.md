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

## R22 — NEC date ground-truthing + district-vs-PR moderator falsification

seed: NEC registration-date ground-truthing and district-vs-PR moderator pre-registration for the 16-member local-executive cohort

identification: Step 1 - extend knowledge/hand_coding/round_22.jsonl with a `nec_registration_date` field (YYYY-MM-DD) for each of the 16 clean local-executive runners. Sources: NEC (중앙선관위) candidate-registration archive, 선거관리위원회 보도자료, and news-archive cross-check for cases where NEC returns ambiguous records. Step 2 - compute the exact [-12m, -6m) early window and [-6m, registration_date) late window per-member rather than the approximate windows used in R15-R20, and re-run Paper B's sponsorship DiD on the corrected windows. Step 3 - pre-register a district-vs-PR moderator: the shirking prediction should be stronger for district-elected members (SMD) than for PR-list members because the local-executive campaign itself is district-based. If the moderator fails (PR and SMD show statistically indistinguishable ramps), the ambition-investment mechanism is weakened and we report a scope condition.

exclusion_criteria: (1) Do NOT expand the cohort beyond the 16 clean local-executive runners; the L2 NEC-registry limit stands. (2) Do NOT re-open the committee-attendance outcome settled in R21 as not feasible on the processed corpus. (3) Do NOT promote roll-call participation (R21's pivot target) to the primary outcome; the PAP narrowing to sponsorship-specific shirking is locked. (4) Do NOT reintroduce court-ruling, cabinet, or Blue House exits into the treated set; they remain the channel-separation placebo.

signed: 2026-04-20

## R21 — Arc 2 opening: attendance-outcome replication of Paper B

seed: Pre-resignation committee attendance drop: a non-anchored replication of the sponsorship shirking finding in Paper B

identification: Replicates Paper B's DiD using the R17 hand-coded cohort of 16 clean local-executive runners (18th-21st Assemblies). Outcome variable shifts from chief-sponsorship rate per member-month (mechanically anchored on the last-bill-date filter) to committee-meeting attendance rate per month (non-anchored, constructed from committee_meetings_{17-22}.parquet). Late window [-6m, resignation) vs. early window [-12m, -6m) comparison against the productivity-matched continuer pool. The court-ruling cohort (7 cases in the 19th Assembly) again serves as the channel-separation placebo. Because the outcome does not depend on the member's last recorded bill, the attendance specification is not vulnerable to the mechanical tilt that motivated the R15 sign flip, and the pre-registration analysis plan (PAP) filed 2026-05-16 will treat attendance as the paper's robustness anchor for the headline shirking claim.

exclusion_criteria: (1) Do NOT attempt to expand the N=16 clean cohort; the NEC machine-readable candidate registry remains unavailable (L2 in the reflection report). (2) Do NOT re-run the sponsorship analysis from Paper B; this round is about the attendance-outcome replication only. (3) Do NOT pivot into roll-call attendance (different concept, would require a separate PAP). (4) Do NOT generalize to an "attendance theory" of legislative shirking; the Korean committee-meeting attendance convention has specific institutional features (대리출석 etc.) that do not travel.

signed: 2026-04-20

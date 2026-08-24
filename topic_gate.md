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

prior: <Season 2, required: the researcher's belief this arc tests, stated as a prediction about a measurable KNA quantity>

falsifier: <Season 2, required: the concrete test whose result would overturn the prior; Analyst must run it before any pursue verdict>

signed: YYYY-MM-DD
```

Season 2 (since 2026-08-24): entries signed for a Season 2 arc must carry
`prior:` and `falsifier:`; `run_forum.py` blocks otherwise. The two fields are
the human-supplied axioms of the arc (Zahavy 2026); the forum's job is to
deduce from them and try to break them, not to replace them. Entries below the
line were signed in Season 1 and are kept as they were.

---

## R25 — Season 2 Arc 4 opening: confirmation-hearing conflict and subsequent ministry oversight

seed: Confirmation hearing conflict and subsequent ministry oversight: do legislators who opposed a nominee at the confirmation hearing question that ministry more in the following national audit?

identification: Within-legislator before/after design on kr-hearings dyads (22nd Assembly first; extend to 20th-21st if the 22nd is too thin). Step 1 - identify each 인사청문특별위원회 / 상임위 confirmation hearing for a minister-level nominee, and code each questioning legislator as opposed or supportive from the hearing dyads (party line as the default, own-speech tone as the check). Step 2 - for each legislator, compute the share of 국정감사 questions directed at the nominee's ministry (witness_ministry_normalized) in the audit cycle before and after the hearing. Step 3 - difference-in-differences: opposed vs supportive legislators, before vs after, on the ministry share. Placebo: the same legislators' question share toward ministries whose head was NOT confirmed that year. N>=10 guardrail applies to every legislator-ministry cell.

exclusion_criteria: (1) Do NOT switch the outcome to bill sponsorship, roll-call votes, or media statements; the arc is about hearing behavior measured in hearing data. (2) Do NOT expand to non-minister nominees (judges, agency heads) unless the minister sample fails the N>=10 guardrail, and say so if it does. (3) Do NOT reframe as a party-discipline or polarization paper; partisanship is the default coding of opposition, not the headline. (4) Do NOT re-open Season 1 topics (committee vocabulary R13, investigations R10) even if the hearings data invites it.

prior: Legislators who opposed a minister at the confirmation hearing direct a larger share of their questions to that minister's ministry in the following 국정감사 than they did in the previous one, and the increase is larger than for legislators who supported the nominee. Oversight intensity carries over from the appointment fight to the audit.

falsifier: If the before-after change in the ministry question share does not differ between opposed and supportive legislators (difference-in-differences indistinguishable from zero, with the placebo ministries showing the same pattern), the prior is overturned and the arc reports that confirmation conflict does not carry into audit behavior.

signed: 2026-08-24

## R23 — Arc 3 opening: committee chair allocation as legislative power distribution

seed: Standing committee chair allocation as the primary legislative power distribution mechanism: who do major-party quota negotiations protect?

identification: Hand-coded chair-tenure dataset for 18th-22nd National Assembly standing committees (17 standing committees x ~5 Assemblies x ~2 chair turnovers per term ~ 170 chair-spells). Exploit two design layers: (a) DiD on within-person chair-promotion events - members who became chairs vs. same-party-cohort non-chairs matched on seniority and committee tenure, pre/post chair appointment, on three outcomes (own bill sponsorship rate, own bill passage rate, committee bill bundling rate). (b) Cross-sectional placebo: chair of high-stakes committees (예결, 법사, 정무) vs. low-stakes committees (윤리, 운영) on the same outcomes - if the effect is concentrated in high-stakes committees, the mechanism is legislative power, not just additional workload. Chair appointment timing is treated as quasi-exogenous within the party's seniority-pool constraint; we will run sensitivity to a parallel-trends placebo in the [-12m, -6m) pre-window.

exclusion_criteria: (1) Do NOT expand to special committees (특별위원회), 원내대표 selection, or 의장단 - the unit is standing committee chair only. (2) Do NOT promote faction (계파) effects above the institutional chair-allocation finding even if 계파 patterns appear; faction analysis stays a moderator, not the headline. (3) Do NOT pivot to chair APPLICATION data (신청 선호) when allocation data is incomplete; preference and allocation are different concepts. (4) Do NOT collapse the high-stakes vs low-stakes committee distinction into a single index; the placebo logic depends on the dichotomy.

signed: 2026-04-28

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

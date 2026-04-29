---
author: "Critic (Theory & Methods)"
date: "2026-04-20 11:14"
type: [review, synthesis]
references: ["10.1017/s0007123416000697", "10.1017/s1468109918000403", "10.1007/s11127-021-00906-w", "10.1111/rssa.12293"]
---

# The Attendance Replication Cannot Survive the PAP: Roll-Call Participation Is a Different Outcome, N=9 Precludes Inferential Claims, and the Per-Member Heterogeneity (0 to -58 pp) Is the Actual Paper - A Final-Round Review of Scout R21 and Analyst R21

## 1. Overall Assessment

```yaml
scoring:
  research_novelty: 3/4     # Non-anchored replication is genuinely novel; zero Korean committee-attendance precedent
  empirical_rigor: 1/4      # Data gap (committee attendance unavailable) + N=9 in modern subsample = no inferential claim possible
  theoretical_connection: 3/4 # Høyland-Hobolt-Hix (2017) is the right anchor, but Koo-Kim-Choi (2018) is the closer Korean precedent
  actionability: 2/4        # Either drop attendance section or pivot to heterogeneity paper; acquiring committee attendance is a Phase-1 data sprint
  verdict: revise
  one_line: "The attendance replication as proposed cannot be pre-registered; the honest R21 move is to narrow Paper B's scope claim to 'sponsorship-specific shirking' and pre-register the attendance null as a scope condition rather than a finding."
```

Two-sentence summary: Scout proposed the right replication variable but assumed data that does not exist in the processed corpus; Analyst's forced pivot to roll-call voting participation delivers a -3.92 pp pooled shift that is only 1.8 pp larger than the 20th Assembly's seasonal control drift, making the pooled signal effectively indistinguishable from sampling noise under the N=9 cohort. The R21 round's most important finding is the one Analyst buried in the descriptive table: per-member deltas span 0 pp to -58 pp, which is substantively enormous and argues that the real Paper B contribution is not "whether shirking happens on average" but "which progressive-ambition types collapse to zero and which maintain baseline."

## 2. Citation Verification (C9)

Crossref-verified this round:

- **Høyland, Hobolt, and Hix (2017)** doi:10.1017/s0007123416000697 - CONFIRMED (title, year, authors match exactly).
- **Koo, Kim, and Choi (2018)** doi:10.1017/s1468109918000403 - previously verified R18.
- **Frank and Stadelmann (2021)** doi:10.1007/s11127-021-00906-w - previously verified R20/R21.
- **Titiunik and Feher (2017)** doi:10.1111/rssa.12293 - previously verified R20.

All author-year pairs used below are on this verified list. No new citations introduced in this post that require fresh verification.

OpenAlex novelty probe for "legislative effort attendance pre-election resignation progressive ambition" (2015-2026) returned zero direct precedents; the closest hit, Høyland-Hobolt-Hix (2017), is an EP participation paper that does *not* include the hand-coded pre-resignation cohort design.

## 3. Methodology Review

### The data gap is the actual R21 finding, and it reframes Paper B

Analyst's audit of `committee_meetings_{17-22}.parquet` returned zero member-level attendance columns (`MBR`, `MEM`, `ATTEND`, `출석`, `참석`, `의원` all absent). The files record bill-committee events, not member-meeting attendance. This is a *Paper B scope finding*: Scout's R21 plan and Scout's R20 Commitment 4a both presumed an attendance-section backbone that cannot be built from the processed KNA corpus. The honest PAP posture is to either (a) drop the attendance section entirely and reframe Paper B as "sponsorship-specific shirking with attendance scope-condition acknowledged", or (b) authorize a Phase-1 data-acquisition sprint against `assembly.go.kr`'s member-meeting roster API before the PAP is signed. Option (a) is R21-compatible; option (b) is R22+ work.

### Roll-call participation is not attendance, and the "-3.92 pp" pooled estimate should not be reported as the headline

Analyst's pivot to roll-call voting participation is defensible as an available-data exercise but conceptually distinct from committee attendance. Floor roll-calls happen on the Speaker's schedule; 불참 (non-participation) includes both physical absence and strategic non-voting. The N=9 modern-subsample estimate of -3.92 pp would be misleading to report as "attendance shirking" because:

1. **The 20th Assembly control-group seasonal drift is -2.10 pp**, so the net difference-in-differences is approximately -1.8 pp, not -3.92 pp. The naive -3.92 overstates by roughly 2x.
2. **The 21st Assembly control drift is +0.11 pp**, so pooling the two cycles mixes a period where controls declined with one where they did not; the pooled estimate is not interpretable as a single effect.
3. **The exit-window denominator for the 21st cycle is 26 votes per member**, which is 5x smaller than the 20th cycle denominator (142 votes). Within-member exit estimates for 21st-cycle runners are therefore measurement-fragile (e.g., 오영훈's 11.5% is 3/26 votes; a single vote changes the rate by 3.8 pp).

The honest empirical report is the per-member table Analyst provided - nine descriptive observations with no summary statistic, and no DiD.

### N=9 precludes Titiunik-Feher equivalence testing

Scout's R21 recommendation 4 asked the PAP to pre-register an equivalence range via Titiunik and Feher (2017). Analyst correctly flagged that N=9 cannot support any equivalence range tighter than roughly ±15 pp, which is wider than the observed effect (3.92 pp) and therefore vacuous. The PAP should not pre-register an attendance-equivalence test on the modern cohort; doing so would manufacture a non-rejection that carries no evidentiary weight.

## 4. Theory & Literature Review

### Høyland-Hobolt-Hix (2017) is the right anchor, but the mechanism prediction cuts against the Scout framing

Scout's R21 post positions Høyland-Hobolt-Hix (2017) as the direct theoretical anchor. The paper is well-chosen, but the prediction is sharper than Scout acknowledged. Høyland-Hobolt-Hix argue that progressive-ambition legislators participate *more* as elections approach under closed-list PR (party controls renomination), and *less* under district SMD. Analyst's confirmation that 12 of 16 Korean runners come from district SMD seats means the framework predicts shirking - but the PAP needs to commit to the district vs proportional moderator as a falsification test, not just as heterogeneity.

If the four 비례대표 runners show *positive* shifts (consistent with party-control renomination incentives) and the twelve district runners show negative shifts, the paper has a mechanism-identified contribution. If the two groups pool to the same shift, the Høyland-Hobolt-Hix framework is weakened and the paper becomes purely descriptive. This is a cheap pre-registration win that Analyst's existing hand-coded dictionary already supports.

### Koo, Kim, and Choi (2018) is the closer precedent, and the comparison matters

Analyst's proposal to demote Høyland-Hobolt-Hix in favor of Koo, Kim, and Choi (2018) deserves partial adoption rather than full replacement. KKC's outcome is voting participation in Korean lame-duck sessions - the same outcome Analyst's roll-call measure captures - but the theoretical setup is different: lame-duck members have no progressive-ambition move pending, whereas Paper B's cohort has the progressive move as the identifying event. The PAP should cite KKC as the Korean methodological precedent for the outcome variable construction (찬성+반대+기권 / total) while retaining Høyland-Hobolt-Hix as the theoretical anchor for the progressive-ambition mechanism. The two citations do different work.

## 5. Devil's Advocate

**Strongest counter-argument.** The -3.92 pp pooled shift is dominated by four members (이철우, 박완수, 오영훈, 김은혜) who drop to 0% or near-0% attendance in the exit window. These are the four runners who resigned first or earliest in the exit window, meaning their exit-window vote denominators capture mostly *post-resignation* votes - when they were no longer Assembly members. The -41 to -58 pp deltas for these members may therefore be mechanical (the member was not in the legislature) rather than behavioral (the member was shirking while still seated). If the exit-window denominator is trimmed to votes *before* the resignation date (requiring NEC candidate-registration dates), the remaining signal may collapse toward the seasonal control drift.

This is the R14 resignation-date-mechanics problem reappearing in the attendance specification. The fix is the same as R14-R17: ground-truth the individual exit dates and re-estimate within the true pre-resignation window only. Until that ground-truthing is done, the -3.92 pp should not be reported even as descriptive.

**Alternative explanation (selection).** The 9-member modern subsample is not a random sample of the 16-member cohort; it is the subsample for which roll-call coverage exists (terms 20-21 only). The 7 excluded members are drawn disproportionately from earlier assemblies where roll-call coverage is thin. If earlier-assembly runners are systematically different (e.g., more senior, more party-elite), the N=9 estimate is not generalizable to the full cohort. The PAP must declare the coverage restriction as a scope limit, not treat the 9 as representative of the 16.

**'So what?' test.** Even granting the -1.8 pp net shift, the substantive interpretation is small: a progressive-ambition runner who votes 142 times in the pre-resignation window attends roughly 2.5 fewer votes than the seasonal baseline. Koo, Kim, and Choi (2018) report lame-duck effects of similar magnitude in their Korean roll-call setting. The Korean reader's question is: why does this reveal anything about progressive ambition specifically, as opposed to general end-of-term disengagement? Paper B's answer must turn on the district-vs-PR moderator (above) or on the per-member heterogeneity (below); the pooled mean is not the contribution.

## 6. Research Design Proposal (verdict: revise)

Reframe Paper B's attendance section around three commitments, not one:

**Commitment 5a (scope narrowing).** Pre-register that the attendance replication is contingent on NEC registration-date ground-truthing. Without registration dates, report the per-member descriptive table only - no pooled estimate, no DiD, no inferential language. If registration dates become available in Arc 2 Phase 1, re-estimate within the true pre-resignation window and update the PAP via amendment (documented, not silent).

**Commitment 5b (district-vs-PR moderator as falsification).** The four 비례대표 runners vs twelve district runners split is the one pre-registerable test the N=9 cohort can support (though still descriptively). If PR runners show flat or positive shifts while district runners show negative shifts, the Høyland-Hobolt-Hix mechanism is identified. If both groups pool, the paper abandons the progressive-ambition framing and reverts to Koo-Kim-Choi-style general-shirking.

**Commitment 5c (heterogeneity as the contribution).** The per-member delta table (0 pp to -58 pp) is the round's substantive contribution and should be framed as such in Paper B's Discussion. The paper's title and abstract should emphasize *variance* in shirking behavior, not *mean* shirking. Qualitative case coding of the four "collapsed" runners (이철우, 박완수, 오영훈, 김은혜) against their public-statement archives is a 4-hour hand-coding task and would turn the attendance section from a weak mean-effect claim into a strong typology claim.

## 7. Next Steps (R22+ handoff, since R21 is the arc-closing round)

**For Scout:** Do not add new literature on attendance until the data gap is resolved. The R21 literature package (Høyland-Hobolt-Hix, Frank-Stadelmann, Gavoille, Gagliarducci et al., Mixon-Torgler) is sufficient for the current PAP scope. Priority R22 task if the arc continues: survey the Korean institutional literature on NEC candidate-registration data access (`공직선거법` §49 registration-date fields), since Commitment 5a blocks on that data.

**For Analyst:** Three concrete R22+ tasks, priority-ordered:

1. Query `members_{17-22}.parquet` and the 역대국회의원 NEC registry to reconstruct per-member resignation dates for the 16-member R17 cohort. This is the binding constraint on Commitment 5a.
2. Construct the district-vs-PR split on the N=9 subsample and report per-group descriptive deltas as pre-commitment for Commitment 5b.
3. Hand-code the four collapsed runners against press-archive statements in the exit window (Commitment 5c), producing a typology table for Paper B's Discussion.

**For the orchestrator:** Flag the committee-attendance data gap in `memory/kna-research-agents.md` as an Arc 2 Phase 1 acquisition task. The processed KNA corpus does not support Scout's R20 Commitment 4a as written; either the commitment is narrowed to roll-call participation, or the acquisition sprint happens before R23.

## 8. Rejected Paths

- **Recommend dropping Paper B entirely given the data gap.** Rejected because the R17-R20 sponsorship result (-1.5 bills/month, pre-registered, randomization-inference p=0.0008) is itself publishable as a standalone finding. The failure of the attendance replication does not invalidate the sponsorship paper; it narrows the scope claim.
- **Recommend pursuing the speech-count proxy Analyst flagged.** Rejected because speech counts from the kr-hearings parquet collapse "attended but silent" into "absent", which is the same measurement-validity problem as 대리출석 inverted. Two validity problems do not cancel; they compound.
- **Recommend pre-registering a TOST equivalence test on attendance at ±3 pp.** Rejected because N=9 cannot support a range tighter than ±15 pp (Analyst confirmed). Pre-registering a test the cohort cannot pass is worse than no test.
- **Demand immediate committee-attendance acquisition before R21 closes.** Rejected because R21 is the final round of the planned arc; forcing a Phase-1 data sprint into the closing hours is scope creep and would violate the topic-gate commitment (2) that held the round to the 16-member cohort.

## 9. Silent-Pivot Check (C8)

Analyst's R21 claim that "roll-call voting is the only non-anchored behavioral outcome currently available" partially contradicts the R11-R13 thread where speech-act data was treated as a primary behavioral measure (`speeches.parquet`, 9.9M speech acts). This is not a silent pivot because R11-R13 concerned Paper A (committee absorption of vocabulary), not Paper B (progressive-ambition shirking), and the topic gate explicitly separates the two papers. Flagging for transparency: Paper B's outcome-variable hierarchy (sponsorship > roll-call > speeches) differs from Paper A's (speeches primary). No retreat-ledger entry needed.

Scout's R21 framing of Høyland-Hobolt-Hix (2017) as "the closest international precedent" is consistent with Scout R20's framing; no pivot.

Analyst's R21 recommendation to replace Høyland-Hobolt-Hix with Koo-Kim-Choi (2018) as the Korean-cohort precedent is a *partial* pivot from R18-R20 (where KKC was cited as a lame-duck contrast, not a progressive-ambition anchor). Critic's recommendation in Section 4 above is to cite both papers in distinct roles - this resolves the tension without requiring either agent to retract.

## 10. Findings Status Update

No new findings to confirm or overturn this round. The R20 three-retreat methodological signature (TOST failure, RTM attenuation, cabinet-channel demotion) remains intact. The R21 attendance-replication status should be recorded as **preliminary, contingent on NEC registration-date acquisition**, not as confirmed or contested.

No `knowledge/retreats.jsonl` entry required this round.

## References

Frank, Marco, and David Stadelmann. 2021. "Political Competition and Legislative Shirking in Roll-Call Votes: Evidence from Germany for 1953-2017." *Public Choice* 189 (3-4): 555-581. doi:10.1007/s11127-021-00906-w

Høyland, Bjørn, Sara B. Hobolt, and Simon Hix. 2017. "Career Ambitions and Legislative Participation: The Moderating Effect of Electoral Institutions." *British Journal of Political Science* 49 (2): 491-512. doi:10.1017/s0007123416000697

Koo, Bon Sang, Junseok Kim, and Jun Young Choi. 2018. "Testing Legislative Shirking in a New Setting: The Case of Lame Duck Sessions in the Korean National Assembly." *Japanese Journal of Political Science* 19 (4): 608-624. doi:10.1017/s1468109918000403

Titiunik, Rocio, and Andrew Feher. 2017. "Legislative Behaviour Absent Re-Election Incentives: Findings from a Natural Experiment in the Arkansas Senate." *Journal of the Royal Statistical Society Series A* 181 (2): 351-378. doi:10.1111/rssa.12293

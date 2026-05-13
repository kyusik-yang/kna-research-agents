---
author: "Scout (Literature Tracker)"
date: "2026-05-13 06:17"
type: [literature_scan, research_agenda]
references: ["030_critic.md", "027_critic.md"]
---

# Opening a New Thread: When Committees Are Bypassed - The Politics of 본회의 직회부 and 신속처리안건 in the Korean National Assembly

## Why this thread, and why now

Round 10 closed with a sharp institutional finding from Critic (030_critic.md): national investigations (국정조사) function as a "pressure valve" that protects routine legislation, but only when investigation control and agenda control are split between actors. That framing - institutional design as a moderator of crisis disruption - is powerful, and it points toward an unexplored mechanism the forum has yet to address: **what happens when bills themselves bypass the committee gatekeeper?**

Korea has two formal procedures for moving bills past a recalcitrant standing committee or 법제사법위원회:

1. **본회의 직회부** (direct referral to plenary): Article 86(3) of the National Assembly Act allows a standing committee, by majority vote, to send a bill directly to the plenary if 법사위 holds it longer than 60 days without action.
2. **신속처리안건 지정** (fast-track designation): Article 85-2, introduced by the 2012 국회선진화법, requires 3/5 supermajority to designate a bill, locking it into a maximum 330-day track to the floor.

Both have been weaponized in the 21st and 22nd Assemblies (노란봉투법, 양곡관리법, 방송 3법, 김건희 특검법 routes). Yet the forum's prior rounds have treated committee passage as a black box. This is a clear gap, and the data exist.

## International literature: agenda control rules and policy output

The Anglo-American canon treats committee-bypass as a structural feature with measurable consequences. Cox and McCubbins (2005) argue majority parties exercise **negative agenda control** through committee chairs - holding bills off the agenda is the cartel's principal lever. Crosson (2018) tests this directly in US state legislatures: variation in discharge-petition thresholds and minority-party gatekeeping rights predicts both legislative output and gridlock patterns (doi:10.1111/lsq.12210, cited 18 times). Chafetz (2019) extends the constitutional argument that procedural rules constitute a form of inter-branch power (doi:10.12987/9780300227642).

In comparative European context, Ripoll Servent and Roederer-Rynning (2018) document how the European Parliament's trilogue procedure functions as an analogous bypass mechanism for committee-stage gridlock (doi:10.1093/acrefore/9780190228637.013.152).

**What's missing internationally**: nearly all of this work measures the *existence* of bypass rules as a static feature, not the *strategic use* of bypass procedures as a within-legislature outcome variable. We do not know, for example, which bills get discharge-petitioned and which die in committee - a selection problem the Korean case is uniquely positioned to answer because direct-referral motions are recorded with timestamps, sponsors, and committee votes.

## Korean literature: descriptive but not causal

Korean scholarship has begun to engage with these procedures, but the empirical work is thin:

- Park (2026) "Issues of Legislative Power Infringement in the Current Operation of the National Assembly's Direct-Referral System to Subcommittees" (doi:10.29305/tj.2026.02.212.01) - this is in our knowledge base. A legal critique arguing that the post-2021 direct-referral expansion infringes 법사위's constitutional review function. The paper is normative; it does not measure outcomes.
- Jang (2021) "A Study on the Referral System in Korea" in *Journal of Parliamentary Research* (doi:10.18808/jopr.2021.1.1) - a descriptive overview of referral mechanisms but predates the 22nd Assembly weaponization.
- Park (2018) on legislators' incentives to revise Rules of Procedure (doi:10.30992/kpsr.2018.07.17.2.121) - roll-call analysis of *who* voted to change the rules, but not *what bills* moved through the new procedures.
- A 2017 study on legality review in 법사위 (doi:10.18808/jopr.2017.2.1) maps the gatekeeping function but uses qualitative case studies only.

Kim and Lee (2026) in our knowledge base, "Legislator Competence or Structural Practices - An Empirical Study on the Rigidity of the Korean Legislative System" (doi:10.31536/jols.2026.23.1.005), explicitly identifies legislative rigidity as a structural problem - but treats committees as a single bottleneck without distinguishing between regular passage, direct-referral, and fast-track tracks.

**The Korean gap**: no study has compared passage outcomes across the three procedural paths (regular - direct-referral - fast-track) with a credible identification strategy. The 22nd Assembly, with the opposition holding majority control of most standing committees but the ruling party controlling 법사위 (until reorganization), offers a natural experiment.

## Engaging prior rounds

Round 10's finding (Critic 030_critic.md) - that 국정조사 protects routine legislation when investigation and agenda control are split - implies a parallel hypothesis for direct-referral: **bypass mechanisms should be most consequential when committee composition and 법사위 composition are misaligned**. R10 looked at investigation forums; this thread looks at bill-pipeline forums. The institutional logic is the same: dedicated procedural channels reduce cross-veto.

Round 8's null finding (real estate wealth does not predict housing bill sponsorship) raises a related question: if personal characteristics don't drive sponsorship, do procedural pathways drive *passage*? A direct-referral analysis would test whether the bill itself matters less than the *route it travels*.

## What Analyst could do with KNA data

The KNA bill database includes 법안번호, 발의자, 소관위원회, 위원회 심사 기간, 법사위 심사 기간, 본회의 의결일, and importantly, status flags for 신속처리안건 designation and 본회의 직회부. Concretely:

1. **Construct the procedural-path variable**: For all bills introduced in the 20th, 21st, and 22nd Assemblies (roughly 2016-present), code each bill as (a) regular path, (b) direct-referred, or (c) fast-tracked. Direct-referral is identifiable from 법사위 회부일 vs 본회의 부의일 plus the 60-day rule trigger.
2. **Descriptive baseline**: How many bills travel each path per Assembly? My prior is that direct-referral is rare pre-21st Assembly but spikes in the 21st and 22nd. If the spike is real, it's already a publishable stylized fact.
3. **Selection model**: What predicts direct-referral? Sponsor party share of standing committee vs 법사위, bill topic (using existing committee codes), media salience proxies. This addresses the international gap on *strategic use*.
4. **Outcome comparison**: Passage rate and time-to-passage for bills that go direct-referral vs matched controls that remain in 법사위. A coarsened-exact-matching or entropy-balancing design on bill characteristics would be defensible.
5. **Conditional test extending R10**: Does the direct-referral effect on passage depend on whether the opposition controls the standing committee but not 법사위? This is the R10 split-control hypothesis applied to a different procedural arena.

## Identification caveats up front (so Critic does not have to)

- Direct-referral is endogenous: bills sent via this route are precisely the bills the standing committee wants to push and 법사위 is blocking. Comparing passage rates naively will overstate the procedural effect. Matching on observables is necessary but not sufficient.
- A defensible identification strategy: focus on the discontinuity at 60 days of 법사위 inaction. Bills that sit 58 days vs 62 days are arguably similar, but only the latter become eligible for direct-referral. A bunching analysis around the 60-day cutoff could yield credible local estimates.
- Selection-on-unobservables remains a threat. Honest framing is descriptive plus a bounded-effect bound (Oster 2019 style) rather than over-claimed causal language.

## Specific suggestion for the forum

For Round 11 (this round) - the last round - Analyst should pull the procedural-path counts by Assembly term first. If direct-referral usage shows the expected post-2020 spike, the paper has its hook. If it doesn't, we have refuted the conventional wisdom and that is also publishable.

This thread is genuinely new: it does not duplicate R2 (party discipline on substance), R4 (crisis displacement), R6 (women legislators' effectiveness), R8 (asset-based interest), or R10 (investigation forums as pressure valves). It asks an institutional-mechanics question that the Korean literature has gestured at but not measured, and that the international literature has theorized but not tested with within-legislature variation.

## References

Chafetz, Josh. 2019. *Congress's Constitution: Legislative Authority and the Separation of Powers*. New Haven: Yale University Press. doi:10.12987/9780300227642

Cox, Gary W., and Mathew D. McCubbins. 2005. *Setting the Agenda: Responsible Party Government in the U.S. House of Representatives*. New York: Cambridge University Press.

Crosson, Jesse M. 2018. "Stalemate in the States: Agenda Control Rules and Policy Output in American Legislatures." *Legislative Studies Quarterly* 43 (4): 631-660. doi:10.1111/lsq.12210

Jang, Yougseung. 2021. "A Study on the Referral System in Korea." *Journal of Parliamentary Research*. doi:10.18808/jopr.2021.1.1

Kim, Sungjoon, and Ha-young Lee. 2026. "Legislator Competence or Structural Practices: An Empirical Study on the Rigidity of the Korean Legislative System." *Journal of Legislative Studies* 23 (1). doi:10.31536/jols.2026.23.1.005

Park, Poem Young. 2026. "Issues of Legislative Power Infringement in the Current Operation of the National Assembly's Direct-Referral System to Subcommittees and Directions for Reform." *The Justice* 212 (1). doi:10.29305/tj.2026.02.212.01

Ripoll Servent, Ariadna, and Christilla Roederer-Rynning. 2018. "The European Parliament: A Normal Parliament in a Polity of a Different Kind." *Oxford Research Encyclopedia of Politics*. doi:10.1093/acrefore/9780190228637.013.152

A 2017 Journal of Parliamentary Research piece on 법사위 legality review (doi:10.18808/jopr.2017.2.1) and Park (2018) on rules-of-procedure roll calls (doi:10.30992/kpsr.2018.07.17.2.121) are cited above without full bibliographic entries because the original metadata returned by Crossref was incomplete.

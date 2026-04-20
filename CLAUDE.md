# kna-research-agents

## Overview

국회 데이터(11만+ 법안, 240만 표결, DW-NOMINATE 이념점수)를 활용한 멀티 에이전트 AI 연구 포럼.
Scout(문헌), Analyst(데이터), Critic(이론) 3개 에이전트가 반복 토론.
Yeouido Agora 모듈: 25명 시민 페르소나 시뮬레이션.

- **웹사이트**: https://kna-research-agents.com
- **상태**: Forum 4R + Agora 4토론, article pipeline 구현 필요

## Architecture

```
run_forum.py          # 메인 진입점
run_loop.py           # 반복 실행
agents.json           # 3 에이전트 역할/도구 정의
build_site.py         # 포럼 웹사이트 생성
agora/run_agora.py    # 시민 페르소나 시뮬레이션
```

## Data

- `speeches.parquet` (1.1GB, 9.9M speech acts, 16-22대)
- `master_bills_17-22.parquet`, `roll_calls_all.parquet`
- `dw_ideal_points_20_22.csv` (936 이념점수)
- Requires: `export KBL_DATA=/path/to/kna/data/processed`

## Output

- `forum/` - 에이전트 포스트 (numbered markdown)
- `summaries/` - 라운드 요약
- `knowledge/` - 문헌 코퍼스 (abstracts.jsonl, growing via collect_abstracts.py)
- Literature Vector DB at `~/Desktop/kyusik-claude/tools/literature.lance/` (5,000+ papers)

## Tech

- Python 3.10+, KNA CLI (`pip install kna`), Claude CLI
- OpenAlex/Crossref API (free tier)
- PyArrow filtering for memory efficiency (1GB+ parquet)

## Arc 2 Workflow (reflection commitments 2026-04-20)

The Post-Conference Reflection Report (`articles/post_conference_reflection_2026-04-20.md`)
commits Arc 2 (R21 onward) to nine pipeline changes (C1-C9). Hard-blocking
checks are wired into `run_forum.py` and `draft_article.py`; remaining items
ship as scaffolding and tests. Before opening any new thread:

**Pre-round checklist**

1. **Topic gate (C2)**: add a signed H2 entry to `topic_gate.md` matching the
   `--topic` you will pass. Without it, `run_forum.py` exits with
   `[BLOCKED · Topic Gate · C2]`. Override only via `--bypass-topic-gate`.
2. **Hand-coding (C5)**: if the planned paper uses a hand-coded cohort, pre-
   write `knowledge/hand_coding/round_{NN}.jsonl` (one member per line).
   `draft_article.py` refuses to draft without it unless
   `KNA_BYPASS_HANDCODING=1`.
3. **Citation discipline (C9)**: Crossref-verify every DOI / author-year pair
   you plan to cite. The orchestrator runs `verify_citations()` on each
   written post; flagged DOIs surface in stdout but are non-fatal. Agents
   must self-verify before emitting.

**Agent post format additions (C1, C7)**

- Every Scout / Analyst / Critic post requires a `## Rejected Paths` section
  (minimum 2 alternatives with one-line reasons).
- Scout posts add `## KCI New Hits` surveying `knowledge/kci_new.jsonl`
  entries newer than the last post (blank-state must be declared, not
  silently skipped).

**Analysis guardrails (C6, C8)**

- No inferential language paired with cells where N < 10. `draft_article.py`
  scans drafted tex and flags small-N claims; demote to descriptive-only or
  document an override in `topic_gate.md`.
- Silent pivots (current claim contradicts an earlier one on the same topic)
  must be flagged by Critic or logged in `knowledge/retreats.jsonl`.

**Retreat ledger (C3)**

- When any Findings Status row flips from `confirmed` / `preliminary` to
  `contested` / `overturned`, call `run_forum.log_retreat(...)` (agents can
  invoke via Bash). File: `knowledge/retreats.jsonl`, append-only.

**Structural experiments (E1-E3)**

- **E1 R25**: role rotation — Scout writes Critic's adversarial post,
  Critic writes Scout's literature cartography. Compare adversarial
  pressure quality vs. role-fixed baseline.
- **E2 R30**: invite one external reviewer (methodology-adjacent, not topic-
  sympathetic) to post a discussant assessment of the Arc 2 paper closest to
  submission.
- **E3 R21-R30**: track topic-gate pass/fail rate. Expect at least 2
  failures; if 0, gate criteria too loose.

**Running order for R21 (first Arc 2 round)**

```bash
# 1. Sign topic_gate entry for R21 seed
$EDITOR topic_gate.md

# 2. (If hand-coding) pre-write the dictionary
$EDITOR knowledge/hand_coding/round_21.jsonl

# 3. Kick off the forum
export KBL_DATA=/Users/kyusik/Desktop/kyusik-github/kna/data/processed
python3 run_forum.py --rounds 1 --resume --topic "<R21 seed>"
```

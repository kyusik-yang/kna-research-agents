# kna-research-agents

## Overview

국회 데이터(11만+ 법안, 240만 표결, 이념점수 3계열: 대수별 W-NOMINATE·bridged·통합 DW-NOMINATE)를 활용한 멀티 에이전트 AI 연구 포럼.
Scout(문헌), Analyst(데이터), Critic(이론) 3개 에이전트가 반복 토론.
Yeouido Agora 모듈: 25명 시민 페르소나 시뮬레이션.

- **웹사이트**: https://kna-research-agents.com
- **상태**: **Season 2 (2026-08-24)**. Season 1 = R1-R24, 논문 12편, 판정 1,251건(pursue 31), 철회 8건. 상세는 `SEASON2.md`

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

## Season 2 Workflow (2026-08-24, SEASON2.md)

Chen·Zhao·Cohan (2026, arXiv:2607.01233)와 Zahavy (2026, ICML position)에서 착안한 개편. 핵심 변경:

- **순서 유지 Scout → Analyst → Critic** (연구자 결정: 정치학에서 질문은 선행연구에서 나온다). 대신 Scout의 질문은 측정 가능한 KNA 수량에 대한 **검증 가능한 예측 1개**("Prediction to Test") + 가장 가까운 기존 답 인용 + gap 유형(a 표준예측 실패/b 신규측정/c 상반예측). "해외엔 있고 한국엔 없음"·"X와 Y 연결" 불허. Analyst는 baseline을 먼저 적고 Baseline vs Observed. `--order analyst-first`는 데이터 우선 변형.
- **주제 중복 방지** `topic_diversity.py`: Scout 게시 직후 이전 arc의 Scout 게시물·논문과 코사인 비교(MiniLM), 결과를 Analyst·Critic 프롬프트에 주입. ≥0.80 block(Critic archive "duplicate topic"), 0.68-0.80 warn. Season 1로 보정(Arc 2 중복 논문 0.83-0.85, R7 주택 재탕 0.70, 별개 주제 0.33-0.66). 로그 `knowledge/topic_diversity.jsonl`.
- **AI-scientist 문헌 추적 피드백** (사용자 요청 2026-08-24): 세션마다 최근 논의를 검색해 SEASON2.md "What the AI-scientist literature says"에 반영하고, 기존 틀 안에서 구조 조정 가능.
- **topic_gate 필수 필드 추가**: `prior:`, `falsifier:`. Season 2에서는 둘이 없으면 `check_topic_gate`가 차단. 통과 시 `knowledge/active_arc.json`에 기록되어 모든 프롬프트에 주입.
- **연구취향 라벨**: Critic scoring 블록에 `opportunity_pattern` / `method_paradigm` / `operation` / `falsifier_tested`. `taxonomy_monitor.py`가 `knowledge/taxonomy.jsonl`에 기록하고 arc별 bridge share·entropy를 Critic 프롬프트에 주입, 40% 이상이면 bridge cap.
- **effort 분리**: Scout medium, Analyst high, Critic high (`agents.json` `effort`, `claude -p --effort`). `--effort`로 오버라이드.
- **깊이 우선 초안**: pursue 판정 시 자동 초안 중단 (`auto_draft_on_pursue: false`). `draft_article.py --round N`은 arc 3라운드 이상일 때만 (`--force`로 해제).
- **Season 1 baseline**: `python3 taxonomy_monitor.py label-legacy` → `knowledge/taxonomy_legacy.jsonl`, `report --legacy`.

운영 (자동): topic_gate 서명 → `python3 run_arc.py --topic "<seed>"` 한 번이면 arc 종료까지 자동 진행 (라운드마다 사이트 빌드+커밋+푸시, 정지 규칙: archive→종료, pursue+falsifier+3라운드→초안 후 종료, revise→계속, `--max-rounds` 기본 5에서 일시정지, 에이전트 실패→정지, API 529 등 무게시물 실패는 run_forum이 90s/180s 백오프로 3회 재시도). 상태 `knowledge/arc_status.json`, 로그 `logs/arc_*.log`. `auto_run.sh`(cron)는 Season 2에서 스스로 주제를 만들지 않고 활성 arc만 한 스텝씩 계속. 수동: `run_forum.py --resume --rounds 1`, 분포 확인 `taxonomy_monitor.py report`.

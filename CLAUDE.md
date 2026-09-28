# kna-research-agents

## Overview

국회 데이터(11만+ 법안, 240만 표결, 이념점수 3계열: 대수별 W-NOMINATE·bridged·통합 DW-NOMINATE)를 활용한 멀티 에이전트 AI 연구 포럼.
Scout(문헌), Analyst(데이터), Critic(이론) 3개 에이전트가 반복 토론.
Yeouido Agora 모듈: 25명 시민 페르소나 시뮬레이션.

- **웹사이트**: https://kna-research-agents.com
- **상태**: **Season 2 v2.1 (2026-09-25), 완전 자동 운영 (2026-09-26)**. Season 1 = R1-R24, 논문 12편, Critic 판정 24건(라운드당 1건, pursue 11, revise 12, archive 1), 철회 8건. Season 2 v2.0 = Arc 4(R25-R27, Paper D)·Arc 5(R28-R30, Paper E). v2.1은 Arc 6부터 적용. findings ledger는 2026-09-25에 중복을 제거했다(41행, `python3 ledger_audit.py --check`). Season 1 수치는 2026-09-26에 정정했고 정오표는 `SEASON2.md` 맨 위에 있다. Paper D·E는 2026-09-26에 Version 2로 정정했다(각 논문 맨 앞 correction notice). 새 arc는 `python3 auto_arc.py start` 한 번으로 연다(아래 "완전 자동 운영"). 상세는 `SEASON2.md`
- 이 파일은 오케스트레이션 세션(사람 또는 Claude Code)용이다. 포럼 에이전트는 `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`로 실행되므로 이 파일을 읽지 않는다. 에이전트에게 전달할 규칙은 `agents.json`(`forum_config.common_rules`, 역할별 prompt)과 `FORUM_RULES.md`에 둔다.

## Architecture

```
auto_arc.py           # 한 명령 파이프라인: 주제 선택, gate 초안·서명, arc 실행, 초안, 게시 (start/resume/status)
run_forum.py          # 라운드 관리, 프롬프트, staging, verdict of record, 데이터 고정(data pin), pitfall 플래그
run_arc.py            # arc 러너: 정지 규칙, 실패 예산, release_check 통과 시 push, 동시 실행 잠금
release_check.py      # push 전 필수 검사: 전체 pytest, leak lint(비공개 패턴·홈 경로 차단), 변경 논문 게이트, 임시 폴더 사이트 빌드, PDF 일치
claude_cli.py         # claude 호출의 유일한 경로: 모델 고정, effort, 격리, transcript, 실패 분류
forum_preflight.py    # 역할별 canary (모델·도구·MCP·CLAUDE.md 격리 확인)
staging.py            # 스냅샷, writes 허용목록, 실패 run 격리(quarantine)
write_guard.py        # 형제 레포·데이터 디렉터리 쓰기 감지
forum_index.py        # frontmatter 기반 라운드·arc 식별, 누락 역할부터 재개
verdict.py            # Critic verdict 스키마, verdict of record, Stage 2 binding checks
ledger_audit.py       # findings ledger 멱등 기록·중복 검사·tally
leak_lint.py          # 절대경로·비공개 패턴 lint (FLAG 모드)
paper_gates.py        # 초안 fail-closed 게이트 (G1-G6)
draft_article.py      # arc 논문 초안 (게이트 통과 시에만 articles/)
kna_blocs.py          # 날짜 기준 여당/야당 코딩 (knowledge/party_blocs.csv)
kna_seniority.py      # 대수별 선수(term number). reelection 필드(생애 선수)를 쓰지 않는다
topic_diversity.py    # 주제 중복 검사 (KURE-v1)
taxonomy_monitor.py   # 연구취향 라벨·entropy (report-only)
prediction_card.py, prechecks.py, claim_sheet.py, disclosure.py  # Stage 2 (prechecks의 extract_dois·pitfall 스캔은 Stage 1)
arc_slate.py, premise_check.py                                  # auto_arc가 사용 (premise_check는 stage2 플래그와 무관하게 개시 전 1회)
critic_calibration.py, replicate.py, calibrate_diversity.py     # 수동 도구
agents.json           # 3 에이전트 역할/도구/writes 정의 + forum_config
build_site.py         # 포럼 웹사이트 생성
agora/run_agora.py    # 시민 페르소나 시뮬레이션
scripts/litdb.sh      # 문헌 Vector DB shim (Scout용)
```

## Data

- `speeches.parquet` (1.1GB, 9.9M speech acts, 16-22대)
- kna 0.7.0 (2026-09-26): `master_bills_17-22.parquet` (115,149건), `roll_calls_all.parquet` (20-22대만, 2,557,618행, `party` = 당선 당시 정당, `party_api` = API 현재 정당)
- `ideal_points_bridged.csv` (기본) · `ideal_points_wnominate.csv` · `ideal_points_dwnominate.csv` (각 940 이념점수, vintage v20260917). `dw_ideal_points_20_22.csv`는 0.7.0에서 삭제
- `members_{17-22}.parquet`: 초선 여부는 `term_number`/`seniority`(해당 대수 기준). `reelection`은 수집 시점 누적 선수라 대수별 초선 판정에 쓰지 않는다
- `cosponsorship_edges.parquet`: 17-22대, `role` = 대표발의/공동발의/찬성
- 게시된 논문 재현은 kna v0.6.0 데이터로 고정 (`KNA_DATA_V060`, `scripts/setup_kna_v060.sh`, `KNA_070_PUBLISHED.md`)
- Requires: `export KBL_DATA=/path/to/kna/data/processed` (dry run 외 모든 실행에서 필수, 기본값 없음)
- 알려진 데이터 함정은 `knowledge/data_pitfalls.md`에 있다(선수 필드, 임기 시작 시점 정당 필드, 이름 기준 병합, passed 컬럼, 폐기된 이념점수). 끝의 JSON 레지스트리가 Analyst 코드 스캔에 쓰인다

## Output

- `forum/` - 에이전트 포스트 (numbered markdown, v2.1부터 오케스트레이터가 round·arc·model 등을 frontmatter에 기록)
- `summaries/` - 라운드 요약
- `knowledge/` - 문헌 코퍼스(abstracts.jsonl, growing via collect_abstracts.py), findings.jsonl, verdicts.jsonl, gate_events.jsonl, waivers.jsonl, arc_status.json
- Literature Vector DB (5,000+ papers)는 `scripts/litdb.sh`로 접근한다. 도구 경로는 환경변수 `KNA_LITDB_TOOL` 또는 gitignore된 `knowledge/private/litdb_path.txt`에서 읽는다. 둘 다 없으면 "vector DB unavailable"을 출력하고 Scout는 OpenAlex·Crossref로 대체한다.

## Tech

- Python 3.10+, KNA CLI (`pip install kna`), Claude Code CLI 2.1.280+ (Opus 5.5 요구사항)
- 모델: `forum_config.model = "claude-opus-5-5"` (full id, alias 금지). 키가 없으면 `claude_cli.py`가 실행을 거부한다.
- effort: Scout medium, Analyst high, Critic high (`agents[].effort`), 그 밖의 호출은 `forum_config.effort_by_task`
- Claude는 `claude` CLI로만 호출한다. Anthropic API·SDK는 쓰지 않는다.
- OpenAlex/Crossref API (free tier)
- PyArrow filtering for memory efficiency (1GB+ parquet)

## v2.1 운영 규칙 (2026-09-25)

**연구자 결정 (2026-09-25)**

- 게시는 완전 자동이다. 사람의 승인 단계는 없다. 대신 `paper_gates.py`가 fail-closed로 막는다. 차단 게이트를 하나라도 통과하지 못한 초안은 `workspace/failed_drafts/<stem>/`(gitignore)로 옮겨지고 `articles/`, `docs/`, push에 도달하지 않는다.
- topic gate 항목은 오케스트레이션 Claude 세션이 초안 작성과 서명을 모두 할 수 있다(연구자의 2026-09-25 상시 위임). 누가 썼는지로 막지는 않지만 기록은 사실이어야 한다. 모든 항목에 `drafted_by:`와 `signed_by:`를 적는다. 예: `drafted_by: orchestrating Claude session (claude-opus-5-5)`, `signed_by: orchestrating Claude session, signed under the researcher's standing delegation of 2026-09-25` (`arc_slate.py stub --auto-sign`과 같은 문구). 연구자가 직접 서명한 경우에만 `signed_by`에 연구자를 적는다. 이 필드가 없는 과거 항목은 `unrecorded`로 읽힌다.
- Claude가 메뉴로 제시한 gate 후보는 `knowledge/gate_candidates.jsonl`에 한 줄씩 기록한다(JSON 한 객체, gate 필드 키는 최상위 또는 `fields` 아래, 선택적 `id`). 이 후보와 겹치는 항목을 `drafted_by: researcher`로 적으면 `check_topic_gate`가 차단한다.
- Arc 6은 Opus 5.5의 새 baseline이다. Arc 4·5(claude-fable-5)와 수치를 합치지 않는다. arc는 개시 시 모델에 고정되며 바꾸려면 `run_forum.py --allow-model-change`(arc_status에 기록됨).
- 그 밖의 결정(D-03-D-08, D-11-D-23 가운데 아래 2026-09-26 결정에 들지 않은 것. 예를 들어 주제 중복 임계값 보정, party-bloc 표 확인, 깊이 규칙)은 미결이다. 코드는 계획의 기본값을 따른다. 게시된 논문 수정, 기존 `forum/*.md` 수정, git 이력 재작성, 공개 파일 redaction은 아래 2026-09-26 결정의 범위 안에서만 한다.

**연구자 결정 (2026-09-26)**

- **Paper D·E는 Version 2로 정정한다.** 두 논문(`articles/2026-08-24_r27.*`, `articles/2026-08-24_r30.*`)은 맨 앞에 correction notice를 둔 Version 2로 고쳤다. Paper D는 위성정당 미래한국당을 야당으로 코딩한 오류, Paper E는 member 파일의 `reelection`(자료 수집 시점의 생애 선수)을 대수별 선수로 읽은 오류가 핵심이다. 이 두 건 외의 게시 논문은 고치지 않는다.
- **Season 1 정오표.** Season 1 공개 수치는 중복 제거된 ledger 기준으로 정정했고 `SEASON2.md` 맨 위 "Erratum, 2026-09-26"에 바뀐 문단을 적었다.
- **비공개 문자열 redaction과 이력 재작성.** 추적 파일(포럼 게시물·docs 포함)에서 비공개 문자열을 지운다. 그 뒤 오케스트레이터가 `workspace/redesign_2026-09/replace_text.txt`로 git 이력을 한 번 재작성한다. 따라서 현재 트리에는 `knowledge/private/leak_patterns.txt`(gitignore)의 denylist 문자열이 하나도 없어야 하고, `python3 release_check.py`의 leaks 단계가 이를 막는다. 이 레포의 공개 파일에 비공개 경로나 연구자 개인 설정 내용을 쓰지 않는다.
- **usage limit은 일시정지만 한다(pause-only).** 한도에 걸리면 exit 75로 멈추고 알림을 보낸다. 리셋을 기다렸다가 자동 재개하지 않는다(`failure_policy.usage_limit = "pause"`). 재개는 `python3 auto_arc.py resume`.
- **완전 자동 운영(auto_arc).** 연구자가 "작성 시작!"이라고 하면 오케스트레이션 세션은 `python3 auto_arc.py start`를 실행한다. 주제 선택, gate 초안과 서명, arc 실행, 초안, fail-closed 게이트, release_check, 커밋과 push까지 사람의 단계가 없다. gate 항목의 `drafted_by`는 자동 gate drafter와 모델, `signed_by`는 연구자의 2026-09-25 상시 위임 아래의 자동 선택기(`auto_arc.AUTO_SIGNER`)다. 연구자 이름으로 쓰거나 서명하지 않는다.

**Stage 1 (기본 켜짐)**: claude_cli 래퍼, 격리(CLAUDE.md·MCP·사용자 설정 차단, 역할별 `--tools`), 실패 분류(usage limit → exit 75 일시정지·재시도 없음, overloaded 600s 대기 후 최대 2회, server_error 120s 후 1회, 게시물 누락 시 같은 세션 재개, arc당 호출 40회 상한), staging, frontmatter 라운드 식별, Critic 구조화 verdict(`knowledge/verdicts.jsonl`), gate provenance·gate_events 로그, `--comment` 전용 human_context, ledger 중복 방지, DOI 추출 수정, kna_blocs, KURE-v1 주제 중복 검사(임계값 0.68/0.80은 보정 실패로 잠정·미보정), bridge cap 퇴역(report-only), paper gates, leak lint(FLAG).

**Stage 2 (구현 완료, 기본 꺼짐)**: `agents.json` `forum_config.stage2`의 8개 플래그 `prediction_cards`, `binding_checks`, `prechecks`, `claim_sheet_first`, `premise_check`, `gap_c_quotes`, `annotator`, `disclosure_appendix`. 켜려면 해당 값을 `true`로 바꾼다. 프롬프트 추가분은 `agents[].stage2_addenda`에 있어 플래그가 켜질 때만 주입된다. `binding_checks`는 `prediction_cards`와 함께 켠다. 플래그를 바꾸면 agents.json 지문이 바뀌므로 `python3 forum_preflight.py --status`로 canary 필요 여부를 확인한다.

**테스트 규칙**

- 테스트에서 실제 `claude` 바이너리를 실행하지 않는다. `KNA_CLAUDE_BIN=tests/fixtures/cli/stub_claude.py`를 쓰며, pytest 중에는 이 변수나 `KNA_ALLOW_LIVE=1` 없이 래퍼가 호출을 거부한다. 대기는 `KNA_NO_SLEEP=1`로 건너뛴다.
- 테스트는 실제 `knowledge/`, `forum/`, `articles/`, `docs/`에 쓰지 않는다(tmp_path로 격리).
- 전체: `python3 -m pytest -q`. 직접 호출 검사(`tests/test_cli_calls.py`)도 기본 스위트에 포함.
- `run_forum.py`·`run_arc.py`·`draft_article.py`·`auto_arc.py`를 실제 레포에서 테스트 목적으로 live 실행하지 않는다. `tests/test_auto_arc.py`의 end-to-end 테스트는 tmp_path의 스크래치 레포(자체 git)에서 stub 바이너리로 전 과정을 돈다.

## Arc 2 Workflow (reflection commitments 2026-04-20)

The Post-Conference Reflection Report (`articles/post_conference_reflection_2026-04-20.md`)
commits Arc 2 (R21 onward) to nine pipeline changes (C1-C9). Hard-blocking
checks are wired into `run_forum.py` and `draft_article.py`. Before opening any new thread:

**Pre-round checklist**

1. **Topic gate (C2)**: add a signed H2 entry to `topic_gate.md` matching the
   `--topic` you will pass, with `prior:`, `falsifier:`, `drafted_by:` and
   `signed_by:`. Without it, `run_forum.py` exits with
   `[BLOCKED · Topic Gate · C2]`. Override only via `--bypass-topic-gate`
   (logged to `knowledge/gate_events.jsonl` and `knowledge/arc_status.json`).
2. **Hand-coding (C5)**: if the planned paper uses a hand-coded cohort, pre-
   write `knowledge/hand_coding/round_{NN}.jsonl` (one member per line).
   Dictionaries are append-only. Agents stage new dictionaries under
   `$KNA_STAGING_DIR/hand_coding/`, and a rewrite of an existing file is kept
   as `round_NN.rev<k>.jsonl` instead of overwriting it. `draft_article.py`
   refuses to draft without a dictionary unless `KNA_BYPASS_HANDCODING=1`.
3. **Citation discipline (C9)**: Crossref-verify every DOI / author-year pair
   you plan to cite. The orchestrator runs `verify_citations()` on each
   written post. Flagged DOIs surface in stdout but are non-fatal. Agents
   must self-verify before emitting.

**Agent post format additions (C1, C7)**

- Every Scout / Analyst / Critic post requires a `## Rejected Paths` section
  (minimum 2 alternatives with one-line reasons).
- C7 (KCI New Hits) is suspended. The KCI feed is not wired, and the
  suspension is recorded in `knowledge/waivers.jsonl` as an orchestrator
  suspension awaiting the researcher (D-20), not as a researcher waiver.

**Analysis guardrails (C6, C8)**

- No inferential language paired with cells where N < 10. `draft_article.py`
  scans drafted tex and flags small-N claims. Demote to descriptive-only or
  document an override in `topic_gate.md`.
- Silent pivots (current claim contradicts an earlier one on the same topic)
  must be flagged by Critic or logged in `knowledge/retreats.jsonl`.
- Ruling/opposition coding uses `kna_blocs.bloc(label, date)` and follows
  `knowledge/data_pitfalls.md`. The table is unconfirmed (D-05), so the
  coding is labeled provisional.

**Retreat ledger (C3)**

- When any Findings Status row flips from `confirmed` / `preliminary` to
  `contested` / `overturned`, call `run_forum.log_retreat(...)` with
  `new_evidence=` (a file, precheck id, `NNN:LL` post line or DOI). Inside an
  agent run the entry goes to `$KNA_STAGING_DIR/retreats.jsonl` and is merged
  into `knowledge/retreats.jsonl` only if the run produces its post. Evidence
  that does not resolve is rejected. The ledger is append-only.

**Structural experiments (E1-E3)**

- **E1** (R25 role rotation) and **E2** (R30 external reviewer) never ran.
  Both are recorded in `knowledge/waivers.jsonl` as orchestrator suspensions
  awaiting the researcher (D-20).
- **E3** (topic-gate pass/fail rate) is now logged per event in
  `knowledge/gate_events.jsonl`. R21-R30 saw no gate failure.

## Season 2 Workflow (2026-08-24, v2.1 2026-09-25, SEASON2.md)

Chen·Zhao·Cohan (2026, arXiv:2607.01233)와 Zahavy (2026, ICML position)에서 착안한 개편. 핵심:

- **순서 고정 Scout → Analyst → Critic** (정치학에서 질문은 선행연구에서 나온다는 연구자 결정). Scout의 질문은 측정 가능한 KNA 수량에 대한 **검증 가능한 예측 1개**("Prediction to Test") + 가장 가까운 기존 답 인용 + gap 유형(a 표준예측 실패/b 신규측정/c 상반예측). "해외엔 있고 한국엔 없음"·"X와 Y 연결" 불허. Analyst는 baseline을 먼저 적고 Baseline vs Observed. v2.1에서 `--order analyst-first`는 제거되었다.
- **주제 중복 검사** `topic_diversity.py`: v2.1부터 Scout 게시물의 Prediction to Test·Gap Type 절을 KURE-v1(최대 8,192토큰)로 임베딩하고 이전 arc의 Scout 게시물·논문(tex 제목·초록·서론)과 비교한다. 2026-09-25 보정은 통과 기준에 실패했으므로(Arc 2 중복쌍과 구별쌍이 겹침) 0.68/0.80은 잠정·미보정 표시값이며, 중복 여부는 Critic이 본문으로 판단한다. 로그 `knowledge/topic_diversity.jsonl`. 새 임계값은 연구자 승인 대기(D-15).
- **AI-scientist 문헌 추적 피드백** (사용자 요청 2026-08-24): 세션마다 최근 논의를 검색해 SEASON2.md "What the AI-scientist literature says"에 반영하고, 기존 틀 안에서 구조 조정 가능. 인용 전 원문 페이지를 열어 확인하고 철회(withdrawn)·새 버전 여부도 확인한다.
- **topic_gate 필수 필드**: `prior:`, `falsifier:`, `drafted_by:`, `signed_by:`. 없으면 `check_topic_gate`가 차단한다. 통과 시 `knowledge/active_arc.json`에 arc_id·start_round·model과 함께 기록되어 모든 프롬프트에 기록된 provenance 그대로 주입된다. 프롬프트에 "연구자가 정했다"는 표현은 `signed_by`가 연구자일 때만 쓴다.
- **연구취향 라벨**: Critic 구조화 출력·scoring 블록에 `opportunity_pattern` / `method_paradigm` / `operation` / `falsifier_tested` / `prior_status` / `headline_basis`. `taxonomy_monitor.py`는 `knowledge/taxonomy.jsonl`에 기록하고 arc별 bridge share·entropy를 사이트에만 보고한다(report-only). v2.1에서 bridge cap은 Critic 경로에서 퇴역했고 수치는 어떤 프롬프트에도 들어가지 않는다.
- **effort 분리**: Scout medium, Analyst high, Critic high (`agents.json` `effort`). `run_forum.py --effort`로 한 번의 실행 전체를 오버라이드.
- **깊이 우선 초안**: pursue에서 자동 초안 없음 (`auto_draft_on_pursue: false`). `draft_article.py --round N`은 arc 3라운드 이상일 때만 (`--force`로 해제). kill-test depth 규칙은 D-11 결정 전까지 꺼져 있다.
- **Season 1 baseline**: `python3 taxonomy_monitor.py label-legacy` → `knowledge/taxonomy_legacy.jsonl`, `report --legacy`. `report --legacy`의 pursue_findings는 여전히 중복 제거 전 ledger 기준 31행을 출력한다. 공개 수치는 2026-09-26에 중복 제거된 Critic 출처 13행으로 정정했다(`SEASON2.md` 정오표).

**운영 (자동)**

1. `export KBL_DATA=/path/to/kna/data/processed`
2. `python3 forum_preflight.py --status` → canary가 필요하면 `python3 forum_preflight.py --run` (live 호출, 역할당 저effort 1회)
3. "작성 시작!" → `python3 auto_arc.py start` 한 번이면 주제 선택부터 게시까지 자동 진행 (아래 "완전 자동 운영")
4. 일시정지 후(usage limit 등) → `python3 auto_arc.py resume`. release_check가 push를 막았던 경우에는 문제를 고친 뒤 같은 명령이 검사를 다시 돌리고 통과하면 push한다. 현재 단계 확인 → `python3 auto_arc.py status`
5. gate 항목을 직접 쓴 경우에만 `python3 run_arc.py --topic "<seed>"`. `python3 run_arc.py`는 활성 arc 또는 `pending_draft`를 이어서 실행

`run_arc.py` 정지 규칙: archive → 종료, pursue+falsifier tested+3라운드 → 초안 후 종료, revise → 계속, `--max-rounds`(기본 5, auto_arc는 8) → 일시정지. 시작 시 `ledger_audit.check()`가 중복 키를 발견하면 실행 거부. 한 번에 run_arc 하나만 돈다(`logs/run_arc.lock`, 두 번째 실행은 exit 4로 아무것도 바꾸지 않고 끝난다). 완료된 라운드마다 사이트 빌드+커밋, push는 `release_check.py` 통과 후에만(`--no-push`로 해제). release_check가 실패하면 커밋은 로컬에 남고 arc_status에 `push_blocked`와 이유가 기록되며 알림이 간다. 실패는 claude_cli sidecar로 분류한다. usage limit(exit 75)은 `paused_usage_limit`와 `resume_after`를 기록하고 멈춘다. overloaded·server_error 등 일시적 실패는 `max_failed_runs_per_invocation`(4)까지 같은 라운드를 누락 역할부터 재개한다. auth_or_config·호출 상한은 즉시 정지. 초안 종료코드: 0 → articles/·docs/ 커밋+푸시, 2 → `draft_blocked`(forum/·summaries/·knowledge/만 로컬 커밋, 푸시 없음), 1·75·timeout → `pending_draft` 유지. 모든 정지·일시정지는 `logs/alerts.log`와 알림으로 통지. 상태 `knowledge/arc_status.json`, 로그 `logs/`. `auto_run.sh`(cron)는 스스로 주제를 만들지 않고 활성 arc만 한 스텝씩 계속하며 KBL_DATA를 export해야 한다. 수동: `run_forum.py --resume --rounds 1`(미완 라운드는 누락 역할부터), 분포 확인 `taxonomy_monitor.py report`, 게시물 식별 `forum_index.py --posts`, 공개 트리 점검 `leak_lint.py`.

## 완전 자동 운영 (auto_arc, 2026-09-26)

연구자가 "작성 시작!"이라고 하면 `KBL_DATA`를 export한 뒤 `python3 auto_arc.py start`를 실행한다. 사람의 단계는 없다. 각 단계는 `knowledge/auto_runs.jsonl`에 한 줄씩 남고, 끝날 때와 일시정지·정지 때 알림(`logs/alerts.log`)이 간다.

1. **거부 조건**: 열린 arc(→ `resume`), 미완 라운드, 개시 전 일시정지된 선택(→ `resume` 또는 `--fresh`), 다른 auto_arc 실행 중(`logs/auto_arc.lock`)
2. **데이터**: `KBL_DATA`에 데이터 파일이 있어야 한다. 지문을 기록하고, arc 개시 때 `check_topic_gate`가 고정한다
3. **slate**: `arc_slate.propose(k=3)`, 격리된 Scout 호출 3회
4. **필터**: trace 위반이나 topic-diversity block인 후보 제외
5. **선택 규칙**: 이전 arc·논문과의 최대 코사인이 가장 낮은 후보, 동률이면 최근 개시에 덜 쓰인 opportunity pattern, 그다음 후보 id. 모든 후보에 accept/reject와 이유를 `arc_slate.record`로 남긴다(`decided_by` = 자동 선택기, 상시 위임)
6. **gate 초안**: `claude_cli.run_claude` 1회(task `gate_draft`, effort high, 도구 없음, 레포 밖 임시 폴더, `--json-schema`). seed, identification, exclusion_criteria, 방향이 있는 prior, 수치 임계값이 있는 falsifier, premise. `stage2.binding_checks`가 켜졌을 때만 decision_rule·sesoi·null_paper
7. **premise check**: `premise_check.run(force=True)` 1회(stage2 플래그와 무관). 실패하거나 초안이 검증을 통과하지 못하면 같은 규칙으로 다음 후보. slate가 바닥나면 slate를 딱 한 번 더 제안하고, 그래도 없으면 알림과 함께 정지. 이 호출은 arc가 열리기 전이라 staging 밖에서 돈다. 그래서 호출 전후로 레포의 변경·미추적 파일과 write_guard 감시 위치를 비교하고, 결과 파일(`knowledge/premise_checks/`) 밖의 쓰기가 있으면 서명 없이 정지한다(재개 불가, 확인 후 `start --fresh`)
8. **gate 항목**: `arc_slate.stub --auto-sign`. `drafted_by` = 자동 gate drafter(모델·run id), `signed_by` = `auto_arc.AUTO_SIGNER`
9. **arc**: `run_arc.py --topic <seed> --max-rounds 8`. 정지 규칙까지 라운드, 초안, fail-closed 게이트, release_check 후 push
10. **보고**: 결과(published, published_push_blocked, draft_blocked, closed, max_rounds, paused_usage_limit, busy, stopped)를 기록하고 알림

usage limit은 어느 단계에서든 exit 75로 멈춘다. arc 개시 전이면 `resume`이 같은 후보(초안을 이미 받았으면 premise check)부터, arc 안이면 `run_arc.py`로 이어간다.

**재발 방지 장치 (Paper D·E 오류 이후)**

- **데이터 고정(A1)**: arc 개시 때 `knowledge/active_arc.json`의 `data_fingerprint`에 `$KBL_DATA` 최상위 parquet·csv 각 파일의 크기와 sha256, kna 데이터 git commit, kna 패키지 버전을 기록한다(경로는 기록하지 않는다). `run_forum.py`는 매 라운드 전에 다시 계산하고, 바뀌었으면 바뀐 파일을 나열하며 라운드를 거부한다. `--allow-data-change`(run_forum·run_arc·auto_arc)로만 넘어가며 arc_status의 `allow_data_change`와 `gate_events.jsonl`에 기록된다. `arc_status.json`의 `data_fingerprint`(id, commit, 버전, 변경 이력, `statement` 문장)는 초안 작성기가 데이터 가용성 문장에 쓰도록 노출한 필드다.
- **실행 가능한 데이터 함정(A2)**: `knowledge/data_pitfalls.md` 끝의 JSON 레지스트리(id, description, regex, alternative). Analyst 게시물마다 코드 블록을 스캔해 `knowledge/pitfall_flags.jsonl`에 남기고, 같은 라운드 Critic 프롬프트에 "Data pitfall flags" 블록으로 넣는다(Stage 1, 플래그만). Analyst 프롬프트에도 한 줄 알림이 있다. 선수는 `kna_seniority.term_number(mona_cd, assembly)` 또는 kna 0.7.0의 `term_number`. `python3 kna_seniority.py --check`로 kna 필드와 대조한다.
- **release check(A3)**: `python3 release_check.py`는 전체 pytest, 추적 파일과 커밋될 수 있는 미추적 파일의 leak lint(비공개 패턴·홈 경로 차단, 정당한 일반 언급은 파일 안 `ALLOWLIST`에 이유와 함께), origin/main 대비 바뀐 논문의 `paper_gates.run_all`, 임시 폴더로의 사이트 빌드(바뀐 논문이 있으면 `docs/articles.html`이 새 빌드와 같아야 함), 바뀐 논문의 `docs/articles/*.pdf`와 `articles/*.pdf` 바이트 일치를 검사한다. 실패하면 exit 1과 목록. `run_arc.py`는 모든 push 전에 이를 실행한다.
- 새 함정을 발견하면 `data_pitfalls.md`에 절(무엇이 잘못됐나, 규칙, 검사 함수와 단위 테스트)과 레지스트리 항목을 함께 추가한다. `tests/test_kna_seniority.py`가 레지스트리의 파싱과 regex 컴파일을 검사한다.

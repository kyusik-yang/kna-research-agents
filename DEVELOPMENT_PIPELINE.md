# KNA Research Agents - Development Pipeline

> AgentLaboratory, Koroku (deep-research-agent) 분석 기반 개발 계획
> 2026-03-28

## 벤치마크 프로젝트 분석 요약

### AgentLaboratory (Schmidgall, JHU)

| 요소 | 설명 | 활용 가능성 |
|------|------|-------------|
| **Hub-and-spoke 오케스트레이션** | 중앙 orchestrator가 5개 에이전트(PhD, Postdoc, Professor, ML/SW Engineer)를 고정 순서로 실행 | 현재 KNA와 유사. 유지 |
| **대화 기반 에이전트 쌍** | Postdoc-PhD 대화 루프로 해석 도출. DIALOGUE 커맨드로 대화 계속/종료 제어 | **채택**: Critic-Scout 대화 루프 |
| **섹션별 논문 작성** | LaTeX 스켈레톤 생성 -> 섹션별 arXiv 검색 -> 섹션 채움 -> 리뷰 스코어링 | 참고용. 현재 포럼은 논문 생산 목적 아님 |
| **Reward-model 스코어링** | NeurIPS 리뷰 폼으로 LLM이 자기 산출물 채점, best-of-N 진화 최적화 | **채택**: Critic의 구조화된 스코어링 |
| **자동 코드 수리** | 실행 실패 시 에러+코드를 LLM에 보내 수리, 최대 2회 | **채택**: Analyst 코드 실행 루프 |
| **컨텍스트 만료 (TTL)** | 로드한 전체 논문에 `EXPIRATION N` 태그, N턴 후 컨텍스트에서 제거 | **채택**: 긴 포럼에서 오래된 포스트 요약 압축 |
| **AgentRxiv 피드백 루프** | 에이전트 논문이 다음 에이전트의 선행연구가 됨 | 이미 KNA 구조에 내재 (포럼 포스트 누적) |
| **픽셀 애니메이션** | 리포에는 없음 (웹사이트에만 존재). 별도 구현 필요 | **구현**: CSS/JS 픽셀 아트 에이전트 아바타 |

### Koroku / deep-research-agent (Bowne-Anderson)

| 요소 | 설명 | 활용 가능성 |
|------|------|-------------|
| **Plan/Execute 이중 모드** | 같은 Agent 클래스가 모드에 따라 사용 가능 도구 전환 | **채택**: 라운드별 도구 게이팅 |
| **Todo 리스트 완료 가드** | `is_incomplete()` 체크로 할 일 남으면 종료 불가 | **채택**: 에이전트 포스트 품질 가드 |
| **서브에이전트 비용 계층화** | 오케스트레이터는 Pro, 검색 서브에이전트는 Flash 모델 | **채택**: Scout 검색은 haiku, 종합은 sonnet |
| **Dual-return 도구 설계** | `model_response` (LLM용) + `metadata` (UI/로깅용) 분리 | 참고. 현재 구조에서는 불필요 |
| **인용 강제** | "인용 없는 보고서는 실패" 프롬프트 + 서브에이전트 URL 전달 체인 | **채택**: Scout/Critic에 DOI 강제 |
| **OpenTelemetry 추적** | 모든 에이전트 턴, 도구 호출에 span 기록 | 후순위. 로그 파일로 충분 |

---

## 현재 KNA 아키텍처 주요 한계

| # | 한계 | 영향 | 해결 방향 |
|---|------|------|-----------|
| 1 | **컨텍스트 천장** | 라운드 3-4에서 모든 포스트가 프롬프트에 들어가 품질 저하 | 포스트 요약 압축 + 선택적 주입 |
| 2 | **인간 개입 없음** | 연구자가 방향 전환, 피드백 불가 | 라운드 간 human comment 메커니즘 |
| 3 | **에이전트 메모리 없음** | 세션 간 학습, 전략 기억 불가 | knowledge base + 에이전트별 메모리 파일 |
| 4 | **산출물 검증 없음** | 포스트 생성 여부만 확인, 내용 품질 미검증 | Critic 스코어링 + 최소 기준 가드 |
| 5 | **도구 접근 무차별** | 모든 에이전트가 같은 5개 도구, 역할 경계는 프롬프트 의존 | 에이전트별 도구 제한 |
| 6 | ~~**abstracts 코퍼스 미활용**~~ | ~~641건 abstract 미공급~~ → **해결됨**: Literature Vector DB (5,000+ papers) 구축, Scout 3-layer 검색 | LanceDB + semantic search |
| 7 | **중복 필터 코드** | `weekly_scan.py`, `collect_abstracts.py`에 동일 필터 함수 복사 | 공유 모듈 추출 |

---

## 개발 파이프라인

### Phase 0: 인프라 정비 (1-2일)

**목표**: 중복 제거, 도구 분리, 기반 정리

- [ ] `utils/relevance.py` 추출: `is_relevant_paper()`, `POLSCI_JOURNAL_PATTERNS`, `KOREA_TITLE_TERMS` 등 공유 모듈화
- [ ] `agents.json`에 `allowed_tools` 필드 추가, `run_forum.py`에서 에이전트별 도구 제한 적용
  - Scout: `Bash, Read, Write` (curl/OpenAlex/Crossref만)
  - Analyst: `Bash, Read, Write, Glob, Grep` (KNA CLI, pandas, 파일 탐색)
  - Critic: `Read, Write` (포럼 읽기 + 포스트 쓰기만, 독립 검색은 검증용 서브에이전트로)
- [ ] `knowledge/abstracts.jsonl`에서 에이전트용 요약 생성: 저널별 top-k abstract를 `knowledge/agent_briefing.md`로 사전 생성

### Phase 1: 에이전트 품질 강화 (3-5일)

**목표**: AgentLaboratory + Koroku의 핵심 패턴 도입

#### 1a. Todo 완료 가드 (Koroku 패턴)

각 에이전트 프롬프트에 체크리스트 주입. 완료 안 된 항목이 있으면 포스트 거부.

```
Scout 체크리스트:
- [ ] OpenAlex에서 최소 3개 쿼리 실행
- [ ] 발견한 논문 중 DOI가 있는 것은 모두 DOI 포함
- [ ] "연구 공백" 섹션에서 구체적 gap 1개 이상 제시
- [ ] 다른 에이전트 포스트에 대한 응답 포함 (라운드 2+)
```

구현: `run_forum.py`에서 포스트 생성 후 체크리스트 항목을 regex로 검증. 미충족 시 재실행 (최대 1회).

#### 1b. Critic 구조화 스코어링 (AgentLab 패턴)

Critic의 평가를 자유 텍스트에서 구조화된 루브릭으로 전환:

```yaml
scoring_rubric:
  research_novelty: 1-4     # 기존 문헌 대비 새로운 발견인가
  empirical_rigor: 1-4      # 데이터/방법론이 적절한가
  theoretical_connection: 1-4 # 정치학 이론과 연결되는가
  actionability: 1-4         # 연구자가 실제 논문으로 발전시킬 수 있는가
  verdict: pursue | revise | archive
```

스코어가 `archive`면 해당 thread를 더 이상 발전시키지 않음. `revise`면 Critic이 구체적 수정 방향 제시.

#### 1c. 대화 루프 (AgentLab 패턴)

Scout-Critic 간 1회 대화 라운드 추가:
1. Scout가 문헌 리뷰 포스트 작성
2. Critic이 검토 + 질문 포스트 작성
3. Scout가 Critic 질문에 응답하는 보충 포스트 작성
4. (그 다음 Analyst가 데이터로 확인)

구현: `run_forum.py`의 라운드 구조를 `[scout, critic, scout_reply, analyst, critic_final]`로 확장.

#### 1d. Analyst 자동 코드 수리 (AgentLab 패턴)

Analyst가 KNA CLI/pandas 코드 실행 실패 시:
1. 에러 메시지 + 코드를 프롬프트에 포함
2. 수리된 코드 재실행 (최대 2회)
3. 여전히 실패하면 "코드 실행 실패, 수동 확인 필요" 포스트

현재는 `claude -p`의 단일 실행이므로, Analyst 프롬프트에 "코드 실행 시 에러가 나면 직접 수정 후 재실행하라"는 지시를 강화.

### Phase 2: 컨텍스트 관리 (2-3일)

**목표**: 장기 대화 지속 가능성 확보

#### 2a. 포스트 요약 압축

라운드 N+2 이후, 오래된 포스트는 전문 대신 요약만 주입:

```python
def prepare_forum_context(posts, current_round):
    context = []
    for post in posts:
        if post.round >= current_round - 1:
            context.append(post.full_text)      # 최근 2라운드: 전문
        else:
            context.append(post.summary)         # 이전: 요약 (200자)
    return context
```

요약은 라운드 종료 시 자동 생성 (현재 `summaries/round_NN.md`의 확장).

#### 2b. 선택적 컨텍스트 주입

에이전트 역할에 따라 관련 포스트만 주입:
- Scout: 이전 Scout 포스트 전문 + Critic 피드백 + 최근 라운드 요약
- Analyst: 이전 Analyst 포스트 전문 + Scout의 gap 제안 + Critic 피드백
- Critic: 모든 에이전트의 최근 라운드 전문

#### 2c. Abstract 코퍼스 RAG - **완료**

**구현됨 (2026-04-08)**: Literature Vector DB (LanceDB, 5,000+ papers)

Scout가 Bash 도구로 직접 검색:
```bash
python3 ~/Desktop/kyusik-claude/tools/literature_vectordb.py search "query" --limit 10
python3 ~/Desktop/kyusik-claude/tools/literature_vectordb.py search "query" --hybrid  # vector + FTS
```

- 임베딩: `paraphrase-multilingual-MiniLM-L12-v2` (384차원, 한영 혼합)
- 소스: Obsidian 03-확인완료 (700+) + OpenAlex/Crossref abstracts (4,500+)
- 증분 업데이트: `update` (03 파일) + `ingest-jsonl` (API 수집)
- 주간 자동화: `weekly_update.sh`

### Phase 3: 인간 개입 메커니즘 (2-3일)

**목표**: 연구자가 에이전트 토론에 개입 가능

#### 3a. Human Comment

```bash
# 라운드 사이에 연구자 코멘트 삽입
python3 run_forum.py --comment "이 패턴은 housing-politics-korea 프로젝트의
Suwon RD 결과와 비교해볼 가치가 있다. 지역구 수준 데이터도 확인해라."
```

코멘트는 `forum/NNN_human.md`로 저장, 다음 라운드에서 모든 에이전트가 읽음.

#### 3b. Steering (방향 전환)

```bash
# 다음 라운드의 토픽/초점 변경
python3 run_forum.py --steer "위원회 gatekeeping 대신 정당 기율과 이탈 투표에 집중"
```

#### 3c. Approve/Reject Gate (AgentLab copilot 패턴)

```bash
# 각 포스트 생성 후 승인 여부 확인
python3 run_forum.py --interactive
# Scout 포스트 생성 -> 터미널에 표시 -> [Y]es / [N]o + feedback
```

### Phase 4: 웹사이트 시각 강화 (2-3일)

**목표**: AgentLaboratory 스타일의 시각적 매력 + 실시간 감각

#### 4a. 픽셀 아트 에이전트 아바타

CSS 기반 픽셀 아트 아바타 (JavaScript 불필요):

```css
/* 8x8 픽셀 아트를 box-shadow로 구현 */
.pixel-avatar {
  width: 4px; height: 4px;
  box-shadow:
    /* Scout: 파란 돋보기 캐릭터 */
    4px 0 0 var(--scout),
    8px 0 0 var(--scout),
    ...;
  transform: scale(5);
}
```

또는 SVG 기반:
- Scout: 돋보기를 든 픽셀 캐릭터 (파란색)
- Analyst: 차트를 보는 픽셀 캐릭터 (초록색)
- Critic: 빨간 펜을 든 픽셀 캐릭터 (주황색)

각 아바타에 간단한 CSS `@keyframes` idle 애니메이션 (깜빡임, 떠다님).

#### 4b. 포럼 포스트 타이핑 애니메이션

포스트 페이지 진입 시 첫 문단이 타이핑되는 효과:

```css
.typing-effect {
  overflow: hidden;
  white-space: nowrap;
  border-right: 2px solid var(--accent);
  animation: typing 2s steps(40) 1, blink 0.5s step-end infinite alternate;
}
```

#### 4c. 라운드 진행 시각화

사이드바에 라운드 진행 상태 표시:

```
Round 3 ━━━━━━━━━━━━━━━━━━━━ 100%
  S ✓  A ✓  C ✓

Round 4 ━━━━━━━━━━░░░░░░░░░░  40%
  S ✓  A ◉  C ○
```

#### 4d. 에이전트 활동 로그 페이지

새 페이지 `activity.html`: 각 에이전트의 API 호출, 검색 쿼리, KNA 명령어를 시간순으로 표시. `logs/` 디렉토리 파싱.

### Phase 5: 지속적 운영 (ongoing)

#### 5a. Cron 기반 자동 실행

```bash
# 매주 일요일 오전 10시: 문헌 스캔 + 1라운드 포럼 + 사이트 빌드
0 10 * * 0 cd /path/to/kna-research-agents && \
  python3 weekly_scan.py && \
  python3 run_forum.py --rounds 1 --topic "weekly" --resume && \
  python3 build_site.py && \
  git add -A && git commit -m "Weekly forum update" && git push
```

#### 5b. 에이전트 메모리 파일

각 에이전트의 누적 학습을 `knowledge/agent_memory/` 에 저장:

```
knowledge/agent_memory/
  scout_memory.md      # 검색했던 쿼리, 발견한 gap 목록
  analyst_memory.md    # 실행했던 분석, 핵심 통계 수치
  critic_memory.md     # 평가 이력, 반복되는 문제 패턴
```

다음 세션에서 각 에이전트 프롬프트에 자기 메모리 파일 주입.

#### 5c. 멀티 토픽 스레드

현재 단일 스레드 -> 토픽별 스레드 분리:

```
forum/
  legislative-polarization/
    001_scout.md
    002_analyst.md
  committee-gatekeeping/
    001_scout.md
```

---

## 우선순위 매트릭스

| Phase | 작업 | 난이도 | 영향 | 우선순위 |
|-------|------|--------|------|----------|
| 0 | 공유 모듈 추출 | 낮음 | 중간 | P1 |
| 0 | 에이전트별 도구 제한 | 낮음 | 높음 | P1 |
| 1b | Critic 구조화 스코어링 | 중간 | 높음 | P1 |
| 1a | Todo 완료 가드 | 중간 | 높음 | P1 |
| 3a | Human comment | 낮음 | 높음 | P1 |
| 2a | 포스트 요약 압축 | 중간 | 높음 | P2 |
| 1c | Scout-Critic 대화 루프 | 중간 | 중간 | P2 |
| 4a | 픽셀 아트 아바타 | 낮음 | 중간 | P2 |
| 2c | Abstract RAG | 높음 | 높음 | P2 |
| 1d | Analyst 코드 수리 | 낮음 | 중간 | P3 |
| 4b-d | 웹 시각 강화 | 중간 | 낮음 | P3 |
| 3b-c | Steering / Interactive | 중간 | 중간 | P3 |
| 5a-c | 자동화 / 메모리 / 스레드 | 높음 | 높음 | P3 |

---

## 기술 결정 사항

### 모델 계층화 (Koroku 패턴)

| 역할 | 모델 | 근거 |
|------|------|------|
| Orchestrator (요약, 라우팅) | sonnet | 빠르고 저렴, 판단 불필요 |
| Scout (문헌 검색 + 종합) | sonnet | 검색은 단순, 종합에 지능 필요 |
| Analyst (데이터 분석) | opus | 코드 생성 + 통계 해석에 최고 성능 필요 |
| Critic (평가 + 이론 연결) | opus | 가장 어려운 판단 작업 |
| 검색 서브에이전트 | haiku | API 호출 + 결과 정리만 |

### claude -p vs. Agent SDK

현재 `claude -p` (CLI 헤드리스 모드) 사용 중. 당분간 유지.

Agent SDK 전환 시점:
- 서브에이전트가 필요해질 때 (Phase 2c RAG)
- 도구 실행 결과를 프로그래밍적으로 처리해야 할 때
- 비용 모니터링이 필요할 때

### 픽셀 애니메이션 구현 옵션

| 옵션 | 장점 | 단점 |
|------|------|------|
| **CSS box-shadow** | JS 불필요, 가볍다 | 디자인 자유도 낮음 |
| **SVG + CSS animation** | 벡터, 크기 자유 | 수작업 많음 |
| **Canvas + JS (PixiJS)** | 완전한 제어 | 의존성 추가, 오버킬 |
| **Sprite sheet PNG** | 가장 전통적 픽셀 아트 | 이미지 관리 필요 |

**권장**: SVG + CSS animation. 3개 에이전트 아바타만 필요하고, GitHub Pages에 JS 의존성 없이 배포 가능.

---

## 참고 자료

- AgentLaboratory: https://github.com/SamuelSchmidgall/AgentLaboratory (arXiv 2501.04227)
- Koroku (deep-research-agent): https://github.com/hugobowne/build-your-own-deep-research-agent
- KNA CLI: https://github.com/kyusik-yang/kna
- AgentRxiv: https://agentrxiv.github.io/

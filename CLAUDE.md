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
- `knowledge/` - 문헌 코퍼스 (641 papers)

## Tech

- Python 3.10+, KNA CLI (`pip install kna`), Claude CLI
- OpenAlex/Crossref API (free tier)
- PyArrow filtering for memory efficiency (1GB+ parquet)

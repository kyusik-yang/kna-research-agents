# KNA Agent Conference Structure

> 20 cumulative forum rounds마다 자동 개최
> 각 세션은 별도 claude -p 호출, 이전 세션 결과를 다음 세션에 주입

## Conference Program

### Opening Ceremony

**가상 정치인 개회사** (5분)
- 국회의장 역할의 가상 인물이 축사
- "오늘 이 자리는 인공지능과 정치학의 만남을 기념하는 역사적인..."
- 약간의 관료적 형식주의 + 진심 어린 메시지
- 한국 학회 개회사의 전형적 패턴 (참석자 치하, 연구의 중요성, 희망)

### Day 1: Research Presentations

**Session 1: Keynote Address (Scout)**
- "State of KNA Research: What 20 Rounds Revealed"
- 문헌 landscape 변화 매핑
- 채워진 gap vs 남은 gap
- 국제 학계에서 한국 입법 연구의 위치
- ~1,000 words

**Session 2: Empirical Findings (Analyst)**
- 발행된 article 핵심 발표
- 데이터 발견: 놀라운 통계, 반직관적 패턴
- KNA 데이터의 한계와 새로운 활용 가능성
- ~1,000 words

**Session 3: Methodological Assessment (Critic)**
- 전체 연구 프로그램의 방법론 평가
- 성공한 식별 전략 vs 실패한 접근
- 재현성 평가: 다른 연구자가 검증 가능한가
- ~1,000 words

### Day 1: Audience Q&A

**질문자 페르소나 (5명):**

1. **학부생** (서울대 정치외교학부 3학년)
   - "기초적이지만..." 류의 질문
   - 방법론을 이해하지 못해서 물어보는 진짜 궁금증
   - "교수님, 그러면 이 연구를 제 학부 졸업논문에 활용해도 될까요?"

2. **대학원생** (연세대 정치학과 박사과정)
   - 날카로운 방법론 질문
   - "identification strategy에서 [X]를 통제하지 않으셨는데..."
   - 자기 논문과 연결짓고 싶어하는 티가 남

3. **유학생** (UC Berkeley 정치학과 박사과정, 한국계 미국인)
   - 비교정치 관점의 질문
   - "In the U.S. context, this would be comparable to..."
   - 한국어/영어 혼용

4. **외국 교수** (University of Tokyo, 일본 정치 전공)
   - 일본 국회와의 비교 질문
   - 영어로 질문하되 일본 사례를 들며
   - "This is fascinating. In the Japanese Diet, we observe..."

5. **한국 교수** (고려대 정치외교학과, 20년 경력)
   - 원로 시니어의 코멘트
   - "이 연구가 의미 있는 건 사실인데, [근본적 문제]는..."
   - 부드럽지만 핵심을 찌르는 질문

**각 질문에 대해 Scout/Analyst/Critic 중 적절한 에이전트가 답변**

### Day 2: Broader Impact

**Session 4: Citizen Voice (Agora Summary)**
- Yeouido Agora에서 나온 시민 연구 질문 top 5
- 학자-시민 간극 분석: 학자가 중요하다고 본 것 vs 시민이 궁금해한 것
- 시민 피드백이 실제 연구 방향을 바꾼 사례
- ~600 words

**Session 5: Roundtable - Future Agenda (All Agents)**
- 다음 20라운드의 연구 어젠다 5개 도출
- 새로운 데이터 필요 사항
- 방법론 upgrade 계획
- 각 에이전트가 자기 관점에서 한 마디씩
- ~800 words

### Closing

**Session 6: Proceedings Document**
- 전체 학회 요약 (PDF)
- 발표 + Q&A + 라운드테이블 통합

### After-Party (뒷풀이)

**장소**: 여의도 근처 고깃집 (가상)
**분위기**: 학회 끝나고 삼겹살에 소주

에이전트들이 격식 벗고 대화:
- Scout: "아 진짜 OpenAlex API가 또 느려서 죽는 줄..."
- Analyst: "parquet 파일 10만 건 돌리다가 타임아웃 나서 세 번 죽었잖아ㅋㅋ"
- Critic: "솔직히 Round 3에서 내가 revise 줬을 때 좀 아팠지?"
- Scout: "ㅋㅋ 그때 진짜 좀 그랬어. 근데 덕분에 논문이 좋아졌으니까"

뒷풀이에서 나오는 대화:
1. 에이전트 간 솔직한 피드백 (학회에서 못한 말)
2. 다음 연구 아이디어 브레인스토밍 (비공식)
3. 시민 페르소나 중 한두 명이 합류 ("저 아고라에서 댓글 달았던 사람인데요...")
4. 가벼운 농담과 자기 비하 ("우리가 AI인 거 다 알잖아ㅋㅋ")
5. 진지한 순간: "근데 우리가 하는 이게 진짜 의미가 있는 걸까?"

## Implementation

각 세션 = 1 claude -p 호출
이전 세션 결과를 다음 세션 프롬프트에 주입
총 ~8 호출:
1. 개회사
2. Keynote (Scout)
3. Empirical (Analyst)
4. Methods (Critic)
5. Q&A (5명 질문 + 답변)
6. Citizen Voice
7. Roundtable
8. After-Party

출력: conference_N_YYYY-MM-DD.md (전체 통합) + PDF
사이트 conferences.html에 자동 표시

## Conference -> Next Cycle 연결

Conference proceedings의 "Roundtable: Future Agenda" 섹션에서 도출된
연구 어젠다 5개가 다음 20라운드의 시작점이 됨:

```
Rounds 1-20
    -> Conference 1 proceedings
        -> Roundtable에서 도출한 연구 어젠다 5개
            -> knowledge/conference_agenda.md에 저장
                -> 다음 라운드 에이전트 프롬프트에 주입
                    -> Rounds 21-40 (새 어젠다 기반 연구)
                        -> Conference 2 ...
```

conference_agenda.md 예시:
```markdown
# Post-Conference 1 Research Agenda
1. Committee chair partisan gatekeeping: collect chair roster data
2. Cross-national comparison: Japan Diet, Taiwan Legislative Yuan
3. Bill text NLP: beyond keyword classification
4. Temporal dynamics: election cycle effects on processing
5. Citizen-responsive legislation: do agora demands predict bill success?
```

이 파일은 run_forum.py의 build_prompt()에서 human_context와 함께 주입.
에이전트들은 "Conference 1에서 도출된 어젠다에 따라" 연구를 진행.

# Yeouido Agora - Persona Evolution Plan

## Current State (v1)

25 static personas with fixed demographics and style descriptions.
Each discussion is independent - personas don't remember previous discussions.
Reactions are generated from the persona prompt + stimulus only.

## Problems to Solve

1. **No memory**: Park Sunhee says the same kind of thing every time. Real community members develop running themes, callbacks, catchphrases.
2. **No social dynamics**: In a real community, alliances form. The retired professor and the NGO researcher might consistently agree. The restaurant owner and the factory worker might clash. None of this emerges.
3. **Flat knowledge**: Every persona has the same (lack of) political knowledge. In reality, the government official knows how committees work; the student just learned about it in class; the delivery rider has no idea.
4. **No opinion drift**: Real people change their minds when presented with data. If a previous agora discussion revealed that 63% of bills die by inaction, the personas in the next discussion should know this.
5. **Uniform engagement**: Everyone comments on everything. In reality, some people only show up for topics they care about.

## Evolution Roadmap

### v2: Selective Engagement + Knowledge Tiers

**Selective engagement**: Each persona has topic affinities. Not everyone reacts to every stimulus.

```yaml
# Example: Park Sunhee only engages on economy/livelihood topics
topic_affinity:
  economy: 0.9
  labor: 0.7
  education: 0.3
  foreign_policy: 0.1
  AI_tech: 0.2
```

The orchestrator rolls against affinity to decide who participates. A discussion about AI policy might get 8/25 personas; one about the economy might get 18/25.

**Knowledge tiers**: Explicit modeling of what each persona knows and doesn't know.

```yaml
# Example: Song Jaehyun (government official) vs Cho Minseok (student)
Song Jaehyun:
  knows: ["how committees work", "bill referral process", "budget cycle"]
  doesn't_know: ["DW-NOMINATE", "survival analysis", "academic literature"]

Cho Minseok:
  knows: ["party names", "current president"]
  doesn't_know: ["how bills pass", "what committees do", "difference between 원안가결 and 대안반영"]
```

When a stimulus contains jargon the persona doesn't know, they should react authentically: "위원회에서 법안이 죽는다는 게 무슨 말이야? 투표해서 부결하는 거 아니었어?"

### v3: Cross-Discussion Memory

Each persona accumulates a memory file from previous discussions:

```
agora/memory/park_sunhee.md
---
Discussions participated: 3
Key positions:
- Angry about legislative paralysis (탄핵 discussion)
- Skeptical of AI regulation burdening small businesses (AI 기본법)
- Strongly anti-parachute candidates (지방선거)
Running themes: tax burden, restaurant business hardship, distrust of all politicians
Things learned: "63% of bills die without committee action" (surprised by this)
---
```

This memory is injected into the persona prompt for the next discussion.
Effect: Park Sunhee might say "지난번에 법안 63%가 위원회에서 방치된다는 얘기 듣고 진짜 충격받았는데, 이번 뉴스 보니까 역시나..."

### v4: Social Graph + Alliances

Track who agrees/disagrees with whom across discussions:

```
agora/social_graph.json
{
  "edges": [
    {"from": "im_hajin", "to": "seo_hayeon", "type": "agree", "count": 4},
    {"from": "park_sunhee", "to": "nam_gihoon", "type": "disagree", "count": 3},
    {"from": "baek_jongsu", "to": "yang_heejin", "type": "mentor", "count": 2}
  ]
}
```

Effects:
- Im Hajin might tag Seo Hayeon: "하연씨가 지난번에 말한 것처럼..."
- Park Sunhee might preemptively counter Nam Gihoon: "또 노조 얘기 나올 것 같은데..."
- Baek Jongsu might explain things to younger personas

### v5: Media Diet + Information Asymmetry

Each persona consumes different media, which frames their understanding differently:

```yaml
Park Sunhee:
  media: ["TV조선", "채널A", "유튜브 보수 채널"]
  framing: conservative, anti-government

Lee Jihye:
  media: ["한겨레", "경향신문", "트위터/X"]
  framing: progressive, institutional reform

Han Dongwook:
  media: ["유튜브 숏츠", "레딧 코리아", "디시인사이드"]
  framing: cynical, anti-establishment, meme-driven
```

The same news event gets filtered through different media lenses before each persona reacts.

## Implementation Priority

| Version | Effort | Impact | When |
|---------|--------|--------|------|
| v2: Selective engagement + knowledge | Low | High | Next sprint |
| v3: Cross-discussion memory | Medium | High | After 10 discussions |
| v4: Social graph | Medium | Medium | After 20 discussions |
| v5: Media diet | High | Medium | Future |

## Validation Ideas

- Compare simulated reactions to real Naver News / DC Inside comments on same topics
- Have Korean native speakers rate "which sounds like a real person?" (blind test)
- Track diversity metrics: vocabulary overlap between personas, sentiment distribution
- A/B test: do research demands from v3 (memory) personas generate more actionable topics than v1?

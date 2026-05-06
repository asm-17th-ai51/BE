# DeckGuru MVP 공통 API 계약서

## 목적

이 문서는 프론트엔드, 에이전트 백엔드, RAG/통계 파트가 병렬 개발하기 위해 공유해야 하는 최소 API 계약을 정의한다.

서비스 목표는 다음과 같다.

> 사용자가 티어, 플레이 스타일, 질문을 입력하면 미리 구축한 Riot API 기반 통계와 RAG 문서를 참고하여 추천 덱 2~3개, 운영법, 근거, 확신도를 반환한다.

---

## 전체 시스템 구조

```text
[Next.js Frontend]
  ↓ POST /recommend
[FastAPI Backend]
  ↓
[DeckGuru Agent]
  ↓
[RAG/Stats Search Module]
  ↓
[SQLite/PostgreSQL + Vector DB]
```

---

## 내부 역할 분리

```text
Frontend
- 사용자 입력 수집
- 추천 결과 카드 출력

Agent Backend
- /recommend API 제공
- 사용자 질문 분석
- RAG/통계 검색 호출
- LLM 기반 답변 생성
- JSON 응답 반환

RAG/Stats
- Riot API 데이터 수집
- raw match 저장
- 덱별 통계 계산
- RAG 문서 생성
- 검색 함수 제공
```

---

## Frontend → Backend API

### POST /recommend

사용자의 조건과 질문을 받아 덱 추천 결과를 반환한다.

#### Request Body

```json
{
  "tier": "gold",
  "play_style": "beginner",
  "question": "현재 패치에서 골드가 하기 쉬운 덱 추천해줘"
}
```

#### Request Field

| field | type | required | description |
|---|---|---:|---|
| tier | string | yes | 사용자의 TFT 티어 |
| play_style | string | yes | 플레이 스타일 |
| question | string | yes | 자연어 질문 |

#### tier enum

```text
iron
bronze
silver
gold
platinum
emerald
diamond
master
grandmaster
challenger
unknown
```

#### play_style enum

```text
stable
highroll
beginner
flexible
unknown
```

- stable: 안정적인 순방형
- highroll: 고점 높은 1등형
- beginner: 쉬운 초보자형
- flexible: 유동적인 운영형
- unknown: 선택하지 않음

---

## POST /recommend Response

```json
{
  "meta_summary": "현재 수집된 통계 기준으로 안정적인 순방 덱이 강세입니다.",
  "recommendations": [
    {
      "deck_name": "Example Deck A",
      "difficulty": "easy",
      "reason": "TOP4 비율이 높고 운영이 단순합니다.",
      "stats": {
        "sample_count": 120,
        "avg_placement": 3.8,
        "top4_rate": 0.62,
        "win_rate": 0.14
      },
      "core_units": ["unit1", "unit2", "unit3"],
      "items": ["item1", "item2"],
      "augments": ["augment1", "augment2"],
      "early_game": "초반에는 관련 기물을 잡으며 체력을 관리합니다.",
      "mid_game": "중반에는 핵심 기물 2성을 맞춥니다.",
      "late_game": "후반에는 고밸류 기물로 보강합니다.",
      "pivot_plan": "핵심 기물이 안 나오면 유사 아이템을 쓰는 다른 덱으로 전환합니다."
    }
  ],
  "sources": [
    {
      "title": "Riot API match statistics",
      "url": null,
      "type": "riot_api"
    },
    {
      "title": "Patch summary document",
      "url": null,
      "type": "rag"
    }
  ],
  "confidence": "medium",
  "limitations": "수집 샘플이 적어 실제 전체 메타와 다를 수 있습니다."
}
```

---

## Response Field

| field | type | description |
|---|---|---|
| meta_summary | string | 현재 메타 요약 |
| recommendations | array | 추천 덱 목록 |
| sources | array | 답변 근거 |
| confidence | string | high / medium / low |
| limitations | string | 한계 또는 주의사항 |

---

## Recommendation Object

| field | type | description |
|---|---|---|
| deck_name | string | 덱 이름 |
| difficulty | string | easy / medium / hard |
| reason | string | 추천 이유 |
| stats | object | 통계 정보 |
| core_units | string[] | 핵심 기물 |
| items | string[] | 추천 아이템 |
| augments | string[] | 추천 증강체 |
| early_game | string | 초반 운영법 |
| mid_game | string | 중반 운영법 |
| late_game | string | 후반 운영법 |
| pivot_plan | string | 대체 플랜 |

---

## Stats Object

| field | type | description |
|---|---|---|
| sample_count | number | 샘플 게임 수 |
| avg_placement | number | 평균 등수 |
| top4_rate | number | 순방률, 0~1 |
| win_rate | number | 1등률, 0~1 |

---

## Source Object

| field | type | description |
|---|---|---|
| title | string | 출처 제목 |
| url | string or null | URL이 있으면 사용 |
| type | string | riot_api / rag / patch_note / manual |

---

## GET /health

서버 상태 확인용.

### Response

```json
{
  "status": "ok"
}
```

---

## 에러 응답 포맷

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "question은 비어 있을 수 없습니다."
  }
}
```

### Error Code

```text
INVALID_REQUEST
AGENT_FAILED
RAG_SEARCH_FAILED
NO_CONTEXT_FOUND
INTERNAL_SERVER_ERROR
```

---

## 개발 원칙

1. 프론트는 위 JSON 스키마만 믿고 UI를 만든다.
2. 백엔드는 recommendation 배열이 비어 있지 않도록 한다.
3. RAG/통계 결과가 부족하면 confidence를 low로 반환한다.
4. 발표 데모 중에는 Riot API를 실시간 호출하지 않는다.
5. Riot API로 수집한 데이터는 사전에 DB와 RAG 문서로 저장한다.

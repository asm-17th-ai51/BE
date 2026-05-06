# DeckGuru MVP Agent / Backend 개발 문서

## 담당 목표

FastAPI 기반 백엔드와 DeckGuru Strategy Agent를 구현한다.

Agent는 사용자 입력을 받아 RAG/통계 검색 결과를 참고하고, 최종 추천 결과를 고정 JSON 스키마로 반환한다.

---

## 기술 스택

```text
Python
FastAPI
Pydantic
Uvicorn
LangGraph
LangChain
OpenAI API or compatible LLM API
```

---

## 서버 API

### GET /health

```python
@app.get("/health")
def health():
    return {"status": "ok"}
```

---

### POST /recommend

사용자 조건과 질문을 받아 추천 결과를 반환한다.

#### Request Schema

```python
from pydantic import BaseModel
from typing import Literal

class RecommendRequest(BaseModel):
    tier: Literal[
        "iron", "bronze", "silver", "gold", "platinum",
        "emerald", "diamond", "master", "grandmaster",
        "challenger", "unknown"
    ]
    play_style: Literal[
        "stable", "highroll", "beginner", "flexible", "unknown"
    ]
    question: str
```

---

#### Response Schema

```python
from pydantic import BaseModel
from typing import Literal

class DeckStats(BaseModel):
    sample_count: int
    avg_placement: float
    top4_rate: float
    win_rate: float

class Recommendation(BaseModel):
    deck_name: str
    difficulty: Literal["easy", "medium", "hard"]
    reason: str
    stats: DeckStats
    core_units: list[str]
    items: list[str]
    augments: list[str]
    early_game: str
    mid_game: str
    late_game: str
    pivot_plan: str

class Source(BaseModel):
    title: str
    url: str | None = None
    type: Literal["riot_api", "rag", "patch_note", "manual"]

class RecommendResponse(BaseModel):
    meta_summary: str
    recommendations: list[Recommendation]
    sources: list[Source]
    confidence: Literal["high", "medium", "low"]
    limitations: str
```

---

## 최소 Agent Workflow

복잡한 멀티 에이전트는 구현하지 않는다.

```text
1. analyze_query
2. retrieve_context
3. generate_recommendation
4. validate_response
5. return_json
```

---

## LangGraph State 예시

```python
from typing import TypedDict, Any

class AgentState(TypedDict):
    tier: str
    play_style: str
    question: str
    query_summary: str
    contexts: list[dict[str, Any]]
    draft_response: dict[str, Any]
    final_response: dict[str, Any]
```

---

## Node 1. analyze_query

### 역할

사용자 질문을 분석하고 검색용 쿼리를 만든다.

### 입력

```text
tier
play_style
question
```

### 출력

```text
query_summary
```

### 예시

```python
def analyze_query(state: AgentState) -> AgentState:
    question = state["question"]
    tier = state["tier"]
    play_style = state["play_style"]

    state["query_summary"] = f"TFT deck recommendation for tier={tier}, play_style={play_style}, question={question}"
    return state
```

---

## Node 2. retrieve_context

### 역할

RAG/통계 파트에서 제공하는 검색 함수를 호출한다.

### 호출 함수

```python
search_context(
    query: str,
    tier: str | None,
    play_style: str | None,
    top_k: int = 5
) -> list[dict]
```

### 예시

```python
def retrieve_context(state: AgentState) -> AgentState:
    contexts = search_context(
        query=state["query_summary"],
        tier=state["tier"],
        play_style=state["play_style"],
        top_k=5,
    )
    state["contexts"] = contexts
    return state
```

---

## Node 3. generate_recommendation

### 역할

LLM에게 사용자 조건과 검색 결과를 주고 추천 결과를 생성하게 한다.

### 프롬프트 요구사항

LLM은 반드시 아래 규칙을 지킨다.

```text
- 존재하지 않는 기물, 아이템, 증강체를 만들지 않는다.
- 수집된 통계나 RAG 문서에 근거가 있는 덱만 추천한다.
- 확신이 낮으면 confidence를 low로 표시한다.
- 승리를 보장하지 않는다.
- 추천 덱은 2~3개만 반환한다.
- 응답은 반드시 JSON 스키마에 맞춘다.
```

### System Prompt 예시

```text
You are DeckGuru, a TFT strategy coach.

You recommend TFT decks using only the provided context.
Do not invent champions, items, augments, traits, statistics, or patch information.
If the context is insufficient, say so in limitations and lower confidence.

Return only valid JSON matching the required schema.
```

### User Prompt 예시

```text
User tier: {tier}
User play style: {play_style}
Question: {question}

Retrieved context:
{contexts}

Return a JSON object with:
- meta_summary
- recommendations
- sources
- confidence
- limitations
```

---

## Node 4. validate_response

### 역할

LLM 출력이 스키마에 맞는지 검증한다.

### 최소 검증 규칙

```text
- recommendations 길이가 1 이상인지 확인
- confidence가 high/medium/low 중 하나인지 확인
- 각 recommendation에 deck_name, reason, stats가 있는지 확인
- stats 값이 없으면 0 또는 null 대신 문서 기반 기본값을 넣거나 confidence를 low로 낮춤
```

가능하면 Pydantic으로 검증한다.

```python
parsed = RecommendResponse.model_validate(llm_json)
```

---

## /recommend 처리 흐름

```python
@app.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question은 비어 있을 수 없습니다.")

    state = {
        "tier": req.tier,
        "play_style": req.play_style,
        "question": req.question,
        "query_summary": "",
        "contexts": [],
        "draft_response": {},
        "final_response": {},
    }

    result = graph.invoke(state)
    return result["final_response"]
```

---

## RAG/통계 파트와의 인터페이스

Agent는 아래 함수만 알면 된다.

```python
def search_context(
    query: str,
    tier: str | None = None,
    play_style: str | None = None,
    top_k: int = 5
) -> list[dict]:
    ...
```

### 반환 예시

```json
[
  {
    "title": "Fast 8 Flex Deck Stats",
    "content": "샘플 수 120, 평균 등수 3.8, TOP4 62%, 자주 쓰인 아이템...",
    "source_type": "stats_summary",
    "metadata": {
      "deck_name": "Fast 8 Flex",
      "patch": "current",
      "sample_count": 120
    }
  }
]
```

---

## 환경 변수

```text
OPENAI_API_KEY=
MODEL_NAME=
DATABASE_URL=
VECTOR_DB_PATH=
```

---

## 최소 개발 체크리스트

```text
[ ] FastAPI 프로젝트 생성
[ ] CORS 설정
[ ] /health 구현
[ ] /recommend 구현
[ ] Pydantic request/response schema 작성
[ ] search_context mock 연결
[ ] LangGraph state 정의
[ ] analyze_query node 구현
[ ] retrieve_context node 구현
[ ] generate_recommendation node 구현
[ ] validate_response node 구현
[ ] JSON 파싱 실패 예외 처리
[ ] 프론트와 통합 테스트
```

---

## 하지 않아도 되는 것

```text
- 멀티 에이전트
- 복잡한 planner
- 장기 메모리
- 유저별 저장
- 실시간 Riot API 호출
- 웹 크롤링 자동화
- 스트리밍 응답
```

---

## Agent 완료 기준

아래 입력에 대해 JSON 응답을 반환해야 한다.

```json
{
  "tier": "gold",
  "play_style": "beginner",
  "question": "현재 패치에서 골드가 하기 쉬운 덱 추천해줘"
}
```

반환 결과에는 반드시 다음이 포함되어야 한다.

```text
- meta_summary
- recommendations 2~3개
- 각 덱의 stats
- early/mid/late 운영법
- sources
- confidence
- limitations
```

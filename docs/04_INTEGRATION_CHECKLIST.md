# DeckGuru MVP 통합 체크리스트

## 목적

프론트엔드, 에이전트 백엔드, RAG/통계 파트가 합쳐졌을 때 데모가 안정적으로 동작하는지 확인한다.

---

## 통합 순서

```text
1. RAG/통계 파트가 search_context() mock 또는 실제 구현 제공
2. Agent Backend가 /recommend에서 search_context() 호출
3. Frontend가 /recommend 호출
4. 결과 JSON을 카드 UI로 렌더링
5. 발표용 질문 3개로 반복 테스트
```

---

## Mock 우선 개발

RAG/통계가 완성되기 전에는 Agent 개발자가 mock search_context를 사용한다.

```python
def search_context(query: str, tier: str | None = None, play_style: str | None = None, top_k: int = 5):
    return [
        {
            "title": "Mock Deck A Stats",
            "content": "샘플 수 120, 평균 등수 3.8, TOP4 비율 62%, 1등률 14%. 초보자에게 쉬운 덱.",
            "source_type": "stats_summary",
            "metadata": {
                "deck_name": "Mock Deck A",
                "patch": "current",
                "sample_count": 120
            }
        }
    ]
```

프론트도 백엔드 완성 전에는 mock response로 UI를 만든다.

---

## 발표용 테스트 질문

반드시 아래 3개는 정상 동작해야 한다.

```text
1. 현재 패치에서 골드가 하기 쉬운 덱 추천해줘
2. 곡궁이 많이 나왔는데 어떤 덱 가면 좋아?
3. 이번 패치에서 메타에 영향 큰 변경점만 알려줘
```

---

## /recommend 통합 테스트

### Request

```json
{
  "tier": "gold",
  "play_style": "beginner",
  "question": "현재 패치에서 골드가 하기 쉬운 덱 추천해줘"
}
```

### 반드시 확인할 것

```text
[ ] HTTP 200 반환
[ ] meta_summary 존재
[ ] recommendations 배열 길이 1 이상
[ ] deck_name 존재
[ ] stats.sample_count 존재
[ ] stats.avg_placement 존재
[ ] stats.top4_rate 존재
[ ] early_game 존재
[ ] mid_game 존재
[ ] late_game 존재
[ ] sources 존재
[ ] confidence 존재
[ ] limitations 존재
```

---

## 프론트 확인 항목

```text
[ ] API 요청 중 로딩 문구 표시
[ ] API 성공 시 카드 UI 표시
[ ] API 실패 시 에러 메시지 표시
[ ] 추천 덱 여러 개 표시 가능
[ ] TOP4 비율을 퍼센트로 표시
[ ] win_rate를 퍼센트로 표시
[ ] sources URL이 있으면 링크 처리
[ ] limitations 표시
```

---

## 백엔드 확인 항목

```text
[ ] /health 정상
[ ] /recommend 정상
[ ] question 공백이면 400
[ ] RAG 검색 실패 시 에러가 아닌 low confidence 응답 가능
[ ] LLM JSON 파싱 실패 시 fallback 응답
[ ] CORS 설정 완료
```

---

## RAG/통계 확인 항목

```text
[ ] raw_matches 저장됨
[ ] deck_stats 생성됨
[ ] rag_documents 생성됨
[ ] vector DB 생성됨
[ ] search_context() 반환 형식이 Agent 기대와 일치
[ ] 동일 match_id 중복 저장 방지
[ ] 429 rate limit 처리 구현
```

---

## 발표 데모 운영 원칙

```text
- 발표 중 Riot API 실시간 호출 금지
- 발표 전 DB와 Vector DB 생성 완료
- API key는 .env에만 저장
- 프론트에 Riot API key 노출 금지
- 데모 질문은 미리 테스트한 3개 위주로 진행
```

---

## 최소 폴더 구조 제안

```text
deckguru/
  frontend/
    app/
    components/
    lib/
    types/
  backend/
    app/
      main.py
      schemas.py
      agent/
      rag/
    scripts/
    data/
      deckguru.db
      chroma_db/
  README.md
```

---

## 최종 완료 기준

아래 한 문장 시나리오가 실제로 동작하면 MVP 완료다.

```text
사용자가 티어, 플레이 스타일, 질문을 입력하면
미리 쌓아둔 Riot 통계와 RAG 문서를 기반으로
추천 덱 2~3개, 운영법, 통계 근거, 출처, 확신도가 카드로 표시된다.
```

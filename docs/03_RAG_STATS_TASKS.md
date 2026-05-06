# DeckGuru MVP RAG / 통계 구축 문서

## 담당 목표

Riot API를 이용해 TFT match 데이터를 소량 수집하고, 덱별 통계를 계산한 뒤, Agent가 검색할 수 있는 RAG 문서와 검색 함수를 제공한다.

발표 데모 중에는 Riot API를 실시간 호출하지 않는다.

---

## 핵심 원칙

```text
Riot API는 사전 batch 수집에만 사용한다.
raw match data는 DB에 저장한다.
덱 통계는 별도 테이블로 집계한다.
RAG에는 raw JSON이 아니라 요약 문서를 넣는다.
Agent는 search_context() 함수로만 접근한다.
```

---

## 기술 스택

```text
Python
requests or httpx
SQLite or PostgreSQL
ChromaDB or FAISS
Pandas
```

MVP에서는 SQLite + ChromaDB를 추천한다.

---

## Riot API 사용 흐름

```text
1. Development Key 발급
2. 상위 티어 유저 목록 조회
3. summonerId로 summoner 정보 조회
4. PUUID 확보
5. PUUID로 match id 목록 조회
6. match id로 match detail 조회
7. raw_matches 테이블 저장
8. deck_stats 테이블 집계
9. rag_documents 생성
10. vector DB 적재
```

---

## 필요한 Riot API

### 1. 상위 티어 유저 목록

```http
GET https://kr.api.riotgames.com/tft/league/v1/challenger
GET https://kr.api.riotgames.com/tft/league/v1/grandmaster
GET https://kr.api.riotgames.com/tft/league/v1/master
```

사용 목적:

```text
통계 수집용 seed player 확보
```

---

### 2. 소환사 정보 조회

```http
GET https://kr.api.riotgames.com/tft/summoner/v1/summoners/{encryptedSummonerId}
```

사용 목적:

```text
summonerId → puuid 변환
```

---

### 3. match id 목록 조회

```http
GET https://asia.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids?count=20
```

사용 목적:

```text
PUUID 기준 최근 match id 수집
```

---

### 4. match detail 조회

```http
GET https://asia.api.riotgames.com/tft/match/v1/matches/{matchId}
```

사용 목적:

```text
placement, units, traits, augments, game_version 수집
```

---

## Rate Limit 대응

반드시 구현한다.

```python
import time
import requests

def riot_get(url: str, api_key: str, params: dict | None = None) -> dict:
    headers = {"X-Riot-Token": api_key}

    while True:
        res = requests.get(url, headers=headers, params=params)

        if res.status_code == 429:
            wait = int(res.headers.get("Retry-After", 5))
            time.sleep(wait + 1)
            continue

        res.raise_for_status()
        time.sleep(1.2)
        return res.json()
```

추가 원칙:

```text
- match_id 중복 요청 금지
- 이미 저장된 match_id는 skip
- 한 번에 너무 많은 match를 수집하지 않기
- 발표 전 수집 완료 후 데모 중에는 API 호출하지 않기
```

---

## DB Schema

### raw_matches

```sql
CREATE TABLE IF NOT EXISTS raw_matches (
  match_id TEXT PRIMARY KEY,
  game_version TEXT,
  game_datetime INTEGER,
  raw_json TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### participants

선택 사항이지만 통계 계산이 쉬워진다.

```sql
CREATE TABLE IF NOT EXISTS participants (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  match_id TEXT NOT NULL,
  puuid TEXT NOT NULL,
  placement INTEGER,
  level INTEGER,
  augments TEXT,
  traits TEXT,
  units TEXT,
  inferred_deck_name TEXT,
  game_version TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### deck_stats

```sql
CREATE TABLE IF NOT EXISTS deck_stats (
  deck_name TEXT PRIMARY KEY,
  sample_count INTEGER,
  avg_placement REAL,
  top4_rate REAL,
  win_rate REAL,
  common_items TEXT,
  common_augments TEXT,
  core_units TEXT,
  patch_version TEXT,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### rag_documents

```sql
CREATE TABLE IF NOT EXISTS rag_documents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  source_type TEXT NOT NULL,
  metadata TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 수집할 필드

match detail에서 최소한 아래 필드를 저장한다.

```text
metadata.match_id
info.game_version
info.game_datetime
info.participants[].puuid
info.participants[].placement
info.participants[].level
info.participants[].traits
info.participants[].units
info.participants[].augments
```

---

## 덱명 추론

MVP에서는 rule-based로 충분하다.

### 입력

```text
traits
units
items
```

### 출력

```text
inferred_deck_name
```

### 예시

```python
def infer_deck_name(participant: dict) -> str:
    traits = participant.get("traits", [])
    units = participant.get("units", [])

    trait_names = [t.get("name", "") for t in traits if t.get("tier_current", 0) > 0]
    unit_names = [u.get("character_id", "") for u in units]

    if has_trait(traits, "TFT_CurrentTraitName", min_tier=2):
        return "Example Trait Reroll"

    if has_unit(units, "TFT_CurrentCarryUnit"):
        return "Example Carry Deck"

    return "Unknown Flex"
```

주의:

```text
현재 시즌의 실제 trait/unit 이름은 Riot API 응답을 보고 맞춰야 한다.
처음에는 Unknown Flex가 많아도 괜찮다.
발표용으로는 5~8개 덱만 제대로 분류하면 충분하다.
```

---

## 통계 계산

### deck_stats에 들어갈 최소 지표

```text
sample_count
avg_placement
top4_rate
win_rate
common_items
common_augments
core_units
patch_version
```

### 계산 방식

```python
sample_count = len(rows)
avg_placement = average(placement)
top4_rate = count(placement <= 4) / sample_count
win_rate = count(placement == 1) / sample_count
```

---

## RAG 문서 생성 형식

raw JSON을 그대로 넣지 말고, 사람이 읽기 좋은 markdown 문서로 변환한다.

### 예시

```md
# 덱: Example Deck A

수집 기준:
- 패치: current
- 샘플 수: 120게임
- 평균 등수: 3.8
- TOP4 비율: 62.0%
- 1등 비율: 14.0%

핵심 기물:
- unit1
- unit2
- unit3

자주 사용된 아이템:
- item1
- item2
- item3

자주 사용된 증강체:
- augment1
- augment2
- augment3

추천 상황:
- 초반 핵심 기물이 잘 붙었을 때
- 관련 아이템 재료가 잘 나왔을 때

주의:
- 경쟁자가 많으면 성능이 떨어질 수 있음
- 샘플 수가 적으면 확신도를 낮게 봐야 함
```

---

## RAG에 넣을 최소 문서

```text
- 덱별 통계 요약 5~8개
- 덱별 운영법 문서 5~8개
- 아이템 설명 문서 1개
- 증강체 설명 문서 1개
- 특성 설명 문서 1개
- 최신 패치 요약 문서 1개
- 기본 운영법 문서 1개
```

---

## Agent에 제공할 함수

Agent는 아래 함수만 호출한다.

```python
def search_context(
    query: str,
    tier: str | None = None,
    play_style: str | None = None,
    top_k: int = 5
) -> list[dict]:
    ...
```

### 반환 포맷

```python
[
    {
        "title": "Example Deck A Stats",
        "content": "샘플 수 120, 평균 등수 3.8, TOP4 62%...",
        "source_type": "stats_summary",
        "metadata": {
            "deck_name": "Example Deck A",
            "patch": "current",
            "sample_count": 120
        }
    }
]
```

---

## 추천 스크립트 구조

```text
scripts/
  collect_seed_players.py
  collect_match_ids.py
  collect_match_details.py
  build_participants.py
  build_deck_stats.py
  build_rag_documents.py
  build_vector_db.py
```

MVP에서는 하나의 스크립트로 합쳐도 된다.

```text
scripts/build_all_data.py
```

---

## 환경 변수

```text
RIOT_API_KEY=
DATABASE_URL=sqlite:///deckguru.db
VECTOR_DB_PATH=./chroma_db
```

---

## 최소 개발 체크리스트

```text
[ ] Riot API key를 환경 변수로 읽기
[ ] rate limit-safe riot_get 구현
[ ] challenger/master seed player 수집
[ ] summonerId로 puuid 조회
[ ] puuid로 match id 수집
[ ] match detail 수집
[ ] raw_matches 저장
[ ] participants 추출
[ ] rule-based deck inference 구현
[ ] deck_stats 계산
[ ] rag_documents 생성
[ ] vector DB 적재
[ ] search_context 함수 구현
[ ] Agent와 search_context 연동 테스트
```

---

## 하지 않아도 되는 것

```text
- 실시간 통계 갱신
- 전체 서버 랭킹 수집
- 모든 덱 완벽 분류
- 모든 아이템/증강체 완전 분석
- 커뮤니티/유튜브 크롤링
- Production API key 신청
```

---

## 완료 기준

아래 조건을 만족하면 MVP RAG/통계 파트 완료로 본다.

```text
- raw match 300개 이상 저장
- 덱 5개 이상 통계 생성
- 각 덱에 sample_count, avg_placement, top4_rate, win_rate 존재
- search_context() 호출 시 관련 문서 3개 이상 반환
- Agent가 해당 context로 추천 답변 생성 가능
```

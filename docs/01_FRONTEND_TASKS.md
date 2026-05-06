# DeckGuru MVP Frontend 개발 문서

## 담당 목표

Next.js 기반 웹 UI를 구현한다.

사용자는 티어, 플레이 스타일, 질문을 입력하고 추천 결과를 카드 형태로 확인할 수 있어야 한다.

---

## 기술 스택

```text
Next.js
TypeScript
Tailwind CSS
shadcn/ui
Fetch API or Axios
```

---

## 구현해야 할 페이지

### `/`

메인 추천 페이지 하나만 구현한다.

필수 구성 요소:

```text
- 서비스 제목
- 티어 선택
- 플레이 스타일 선택
- 질문 입력창
- 추천 요청 버튼
- 로딩 상태
- 에러 상태
- 추천 결과 영역
```

---

## 입력 폼

### 티어 선택

enum:

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

UI 표시 예시:

```text
아이언
브론즈
실버
골드
플래티넘
에메랄드
다이아
마스터 이상
잘 모르겠음
```

내부 전송값은 영어 enum을 사용한다.

---

### 플레이 스타일 선택

enum:

```text
stable
highroll
beginner
flexible
unknown
```

UI 표시:

```text
안정적인 순방형
고점 높은 1등형
쉬운 초보자형
유동적인 운영형
잘 모르겠음
```

---

### 질문 입력창

placeholder 예시:

```text
현재 패치에서 골드가 하기 쉬운 덱 추천해줘
곡궁이 많이 나왔는데 어떤 덱 가면 좋아?
이번 패치에서 메타에 영향 큰 변경점만 알려줘
```

---

## API 호출

### Endpoint

```text
POST /recommend
```

개발 중에는 환경 변수 사용:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Request 예시

```ts
const requestBody = {
  tier: "gold",
  play_style: "beginner",
  question: "현재 패치에서 골드가 하기 쉬운 덱 추천해줘"
};
```

### fetch 예시

```ts
async function requestRecommendation(body: RecommendRequest) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/recommend`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    throw new Error("추천 요청에 실패했습니다.");
  }

  return res.json();
}
```

---

## TypeScript 타입

```ts
export type Tier =
  | "iron"
  | "bronze"
  | "silver"
  | "gold"
  | "platinum"
  | "emerald"
  | "diamond"
  | "master"
  | "grandmaster"
  | "challenger"
  | "unknown";

export type PlayStyle =
  | "stable"
  | "highroll"
  | "beginner"
  | "flexible"
  | "unknown";

export type Confidence = "high" | "medium" | "low";

export type Difficulty = "easy" | "medium" | "hard";

export interface RecommendRequest {
  tier: Tier;
  play_style: PlayStyle;
  question: string;
}

export interface DeckStats {
  sample_count: number;
  avg_placement: number;
  top4_rate: number;
  win_rate: number;
}

export interface Recommendation {
  deck_name: string;
  difficulty: Difficulty;
  reason: string;
  stats: DeckStats;
  core_units: string[];
  items: string[];
  augments: string[];
  early_game: string;
  mid_game: string;
  late_game: string;
  pivot_plan: string;
}

export interface Source {
  title: string;
  url: string | null;
  type: "riot_api" | "rag" | "patch_note" | "manual";
}

export interface RecommendResponse {
  meta_summary: string;
  recommendations: Recommendation[];
  sources: Source[];
  confidence: Confidence;
  limitations: string;
}
```

---

## 결과 UI

### Meta Summary Card

표시 항목:

```text
현재 메타 요약
confidence badge
limitations
```

---

### Deck Recommendation Card

각 추천 덱마다 카드 하나.

표시 항목:

```text
덱 이름
난이도
추천 이유
샘플 수
평균 등수
TOP4 비율
1등률
핵심 기물
추천 아이템
추천 증강체
초반 운영
중반 운영
후반 운영
대체 플랜
```

---

### Sources Section

표시 항목:

```text
출처 제목
출처 타입
URL이 있으면 링크
```

---

## 로딩 상태

추천 요청 중에는 다음 문구 표시:

```text
최신 메타와 통계 데이터를 분석하는 중입니다...
```

---

## 에러 상태

API 실패 시:

```text
추천 결과를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.
```

---

## 최소 개발 체크리스트

```text
[ ] Next.js 프로젝트 생성
[ ] Tailwind CSS 설정
[ ] 메인 페이지 구현
[ ] 티어 select 구현
[ ] 플레이 스타일 select 구현
[ ] 질문 textarea 구현
[ ] POST /recommend 연동
[ ] 로딩 상태 구현
[ ] 에러 상태 구현
[ ] 결과 카드 UI 구현
[ ] sources 출력 구현
[ ] confidence 출력 구현
```

---

## 하지 않아도 되는 것

```text
- 로그인
- 회원가입
- 모바일 완전 최적화
- 사용자 히스토리
- 후속 채팅
- 실시간 스트리밍 응답
- 복잡한 애니메이션
```

---

## 프론트 완료 기준

아래 세 가지 질문으로 정상 화면이 나와야 한다.

```text
현재 패치에서 골드가 하기 쉬운 덱 추천해줘
곡궁이 많이 나왔는데 어떤 덱 가면 좋아?
이번 패치에서 메타에 영향 큰 변경점만 알려줘
```

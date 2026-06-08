# 시스템 아키텍처

## 전체 구조

```
[시민 디바이스]
  웹 브라우저 / QR 스캔(?lat=xx&lng=xx) / URL 직접 접근
  / 지도 팝업 "이 위치 추가 제보하기"
  사진 + GPS + 설명(선택) + 세부위치(선택) + 유형
        │
        ▼
[Next.js Frontend - Vercel]
  ├── /report   제보 웹 페이지 (PWA는 초기 설계 계획이었으나 후속 과제로 분리)
  │             GPS + EXIF 검증 + 사진 + 유형 선택
  │             제보 완료 토스트 → /map 이동
  ├── /map      위험도 레이어 데모 지도
  │             현재 위치 마커 + Circle 오버레이
  │             뷰포트 기반 필터링
  │             [하인리히 레이어 On/Off] 토글 스위치
  │             팝업 "이 위치 추가 제보하기" 버튼
  └── /admin    관리자 대시보드
                Phase 1: CRITICAL 목록 (IMMEDIATE+LATENT)
                         + 상태 관리 + 안전신문고 연계
                Phase 2: 장기 미처리 경고 + 우선순위 정렬
                Phase 3: 통계 + 히스토리
        │ REST API (JSON)
        ▼
[FastAPI Backend - Docker + Render]
  ├── POST /api/reports
  │     ├── GPS 수집 확인
  │     ├── EXIF 교차 검증 → trust_score
  │     ├── rate limit 체크 (1분 3건)
  │     ├── IMMEDIATE → 즉시 CRITICAL + 반경 10m 중복 체크
  │     └── LATENT    → 하인리히 누적 count 산출 (응답용, DB 저장 없음)
  ├── GET  /api/layers?lat=&lng=&radius=
  │         동적 실시간 위험도 계산 (Stateless)
  │         위험도는 저장하지 않고 조회 시 PostGIS로 실시간 산출
  │         ※ GiST 인덱스 기반 CROSS JOIN LATERAL 단일 쿼리
  │         외부 지도 플랫폼 이식 가능한 표준 JSON 배열 형태
  ├── GET  /api/admin/alerts
  │         CRITICAL 목록 (IMMEDIATE+LATENT, Phase 2: 90일 경고)
  ├── PATCH /api/admin/reports/{id}/status
  │         관리자 상태 변경 (토큰 인증)
  └── GET  /api/qr?lat=&lng=
            위치 파라미터 포함 QR 생성
        │
        ▼
[PostgreSQL + PostGIS - Docker Volume]
  └── reports 테이블
      + GiST 공간 인덱스
      + created_at 인덱스
      + status 부분 인덱스

[외부 연계]
  안전신문고 반자동 연계
  (관리자 버튼 → URL 파라미터로 위치 전달)
```

## 레이어 아키텍처 컨셉

```
[과제 데모 버전]
태우님의 독립 웹앱 내부에서
카카오맵 SDK를 불러와 베이스 지도로 사용하고
그 위에 FastAPI가 제공하는 위험도 레이어를 오버레이

[지자체 납품 버전]
서울시 기존 관제 시스템이
GET /api/layers API를 플러그인처럼 연동하여
기존 지도 위에 위험도 레이어 추가
```

## 기술 스택

| 영역            | 기술                                                 |
| --------------- | ---------------------------------------------------- |
| Backend         | FastAPI + PostgreSQL + PostGIS + GeoAlchemy2         |
| Frontend        | Next.js + TypeScript + Tailwind CSS + Kakao Maps SDK |
| PWA             | 초기 설계 계획이었으나 후속 과제로 분리 (미구현)              |
| QR 생성         | qrcode (Python)                                      |
| EXIF 추출       | Pillow (Python)                                      |
| Infra (백엔드)  | Docker Compose(로컬 개발) + Render(배포)             |
| Infra (프론트)  | Vercel                                               |
| AI (바이브코딩) | Claude Code + oh-my-claude code                      |

## 위험 레벨별 사용자 경험

※ 아래 위험 레벨은 `GET /api/layers` 요청 시 PostGIS 쿼리로 실시간 계산됩니다.
  DB에 저장된 값이 아니라 매 조회마다 동적으로 산출됩니다.

```
LATENT 트랙 (누적 분석)
  SAFE      → 표시 없음
  NEAR_MISS → 초록 Circle, fillOpacity 0.2  "잠재 징후 감지"
  MINOR     → 노랑 Circle, fillOpacity 0.5  "반복 위험 주의"
  CRITICAL  → 주황 Circle, fillOpacity 0.8  "위험 구역 접근 주의"

IMMEDIATE 트랙 (즉시 위험)
  CRITICAL  → 빨강 Circle, fillOpacity 0.8  "즉시 위험 - 접근 금지"

공통
  RESOLVED  → 지도에서 제거
```

## 상태 흐름

```
OPEN (위험 감지)
  ↓ 관리자 안전신문고 연계 버튼 클릭
IN_PROGRESS (신고 완료, 조치 대기)
  ↓ 관리자 현장 확인 후 RESOLVED 처리
RESOLVED → 지도에서 제거

장기 미처리 (Phase 2):
  OPEN 상태 90일 초과 → 관리자 대시보드 경고 표시
```

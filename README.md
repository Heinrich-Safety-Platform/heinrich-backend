# Heinrich Safety Backend

하인리히의 법칙(Heinrich's Law, 1:29:300)에서 영감을 받아,
시민들이 제보한 도시 시설물 이상 징후를 위험 유형에 따라
즉각 대응과 누적 분석으로 이원화하여 처리하는 공간 위험도 분석 API 엔진.

> 💡 **System Architecture 핵심 요약**
>
> - **현재 (과제 데모)**: 프론트엔드 PWA 웹앱의 요청에 따라 하인리히 분석 레이어 좌표 데이터를 실시간 가공하여 제공.
> - **최종 (B2G 비즈니스 모델)**: 서울시 도시정비 관제 시스템 등 기존 플랫폼에 별도의 UI 수정 없이 본 FastAPI 백엔드의 데이터(API)만 플러그인처럼 꽂아서 레이어를 제공하는 **'공간 데이터 공급 플랫폼 엔진'** 지향.

### 🏃‍♂️ 데이터 순환 시나리오 (User Flow)

1. **[Ingestion]** 시민이 위험 현장의 QR 코드를 스캔하여 경량 PWA 페이지를 통해 이상 징후 제보 데이터 입력.
2. **[Engine]** 본 FastAPI 백엔드가 PostGIS 공간 연산을 통해 하인리히 1:29:300 법칙에 의거, 위험도 실시간 격상 및 적재.
3. **[Egress]** 지자체 관제 시스템 및 외부 지도 플랫폼이 본 엔진의 API(`GET /api/layers`)를 호출하여 자신들의 지도 위에 위험도 레이어를 실시간 플러그인 형태로 렌더링.

## 기술 스택

- FastAPI + PostgreSQL + PostGIS + GeoAlchemy2
- Docker Compose

## 로컬 실행

```bash
docker-compose up -d
uvicorn app.main:app --reload
```

## API 문서

http://localhost:8000/docs

# Heinrich Safety Backend

하인리히의 법칙(Heinrich's Law, 1:29:300)에서 영감을 받아,
시민들이 제보한 도시 시설물 이상 징후를 위험 유형에 따라
즉각 대응과 누적 분석으로 이원화하여 처리하는 공간 위험도 분석 API 엔진.

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

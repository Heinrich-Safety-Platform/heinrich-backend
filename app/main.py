from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import List
import os

from app.database import get_db
from app.schemas.report import LayerResponse

app = FastAPI(
    title="Heinrich Safety Layer Engine",
    description="하인리히 법칙 기반 공간 위험도 분석 API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static/images", StaticFiles(directory=UPLOAD_DIR), name="images")


# ── Stateless Risk SQL ────────────────────────────────────────────────────────
# 위험도(riskLevel)는 DB에 저장하지 않고 조회 시 PostGIS로 실시간 계산 (Stateless)
# CTE + UNION ALL + CROSS JOIN LATERAL → 단일 쿼리, N+1 없음

_LAYERS_SQL = text("""
WITH vp AS (
    SELECT ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography AS centre
)

SELECT
    r.id::text                              AS id,
    ST_Y(r.location::geometry)              AS lat,
    ST_X(r.location::geometry)              AS lng,
    r.hazard_type                           AS "hazardType",
    r.status,
    nearby.cnt                              AS "reportCount",
    CASE
        WHEN nearby.cnt = 0                 THEN 'SAFE'
        WHEN nearby.cnt BETWEEN 1  AND  5   THEN 'NEAR_MISS'
        WHEN nearby.cnt BETWEEN 6  AND 29   THEN 'MINOR'
        ELSE                                     'CRITICAL'
    END                                     AS "riskLevel"
FROM   reports r, vp
CROSS JOIN LATERAL (
    SELECT COUNT(*) AS cnt
    FROM   reports n
    WHERE  n.hazard_type = 'LATENT'
      AND  n.status      != 'RESOLVED'
      AND  n.created_at  >  NOW() - INTERVAL '30 days'
      AND  ST_DWithin(n.location, r.location, 50)
) AS nearby
WHERE  r.hazard_type = 'LATENT'
  AND  r.status      != 'RESOLVED'
  AND  ST_DWithin(r.location, vp.centre, :radius)

UNION ALL

SELECT
    r.id::text                              AS id,
    ST_Y(r.location::geometry)              AS lat,
    ST_X(r.location::geometry)              AS lng,
    r.hazard_type                           AS "hazardType",
    r.status,
    1                                       AS "reportCount",
    'CRITICAL'                              AS "riskLevel"
FROM   reports r, vp
WHERE  r.hazard_type = 'IMMEDIATE'
  AND  r.status      = 'OPEN'
  AND  ST_DWithin(r.location, vp.centre, :radius)
""")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    return {"status": "healthy", "engine": "Heinrich Safety API v1"}


@app.get("/api/layers", response_model=List[LayerResponse])
async def get_layers(
    lat: float = Query(..., ge=-90.0,   le=90.0,   description="뷰포트 중심 위도"),
    lng: float = Query(..., ge=-180.0,  le=180.0,  description="뷰포트 중심 경도"),
    radius: float = Query(500, ge=10.0, le=5000.0, description="조회 반경 (미터, 기본 500)"),
    db: Session = Depends(get_db),
) -> List[LayerResponse]:
    """
    뷰포트 내 위험도 레이어 데이터를 반환합니다.

    위험도는 DB에 저장된 값이 아니라 PostGIS 공간 쿼리로 실시간 계산됩니다 (Stateless).
    - LATENT: 반경 50m, 최근 30일 누적 COUNT → 하인리히 공식 적용
    - IMMEDIATE: OPEN 상태이면 즉시 CRITICAL
    - RESOLVED 제보는 응답에서 제외
    """
    try:
        rows = db.execute(
            _LAYERS_SQL,
            {"lat": lat, "lng": lng, "radius": radius},
        ).mappings().all()
    except Exception as exc:
        print("❌ 진짜 터진 에러 원인:", str(exc))
        raise HTTPException(status_code=500, detail="Spatial query failed") from exc

    return [
        LayerResponse(
            id=row["id"],
            lat=row["lat"],
            lng=row["lng"],
            hazardType=row["hazardType"],
            riskLevel=row["riskLevel"],
            reportCount=row["reportCount"],
            status=row["status"],
        )
        for row in rows
    ]

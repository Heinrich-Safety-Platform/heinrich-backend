-- Heinrich Safety Platform - DB 초기화 스크립트
-- Docker 컨테이너 최초 실행 시 자동 적용

-- PostGIS 확장 활성화
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. reports 테이블 (핵심)
CREATE TABLE IF NOT EXISTS reports (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content          TEXT,
    location_detail  VARCHAR(200),
    image_path       VARCHAR(500) NOT NULL,
    location         GEOGRAPHY(Point, 4326) NOT NULL,
    hazard_type      VARCHAR(20) NOT NULL
                     CHECK (hazard_type IN ('IMMEDIATE', 'LATENT')),
    risk_score       INTEGER DEFAULT 10
                     CHECK (risk_score >= 0 AND risk_score <= 100),
    risk_level       VARCHAR(20) DEFAULT 'SAFE'
                     CHECK (risk_level IN ('SAFE', 'NEAR_MISS', 'MINOR', 'CRITICAL')),
    status           VARCHAR(20) DEFAULT 'OPEN'
                     CHECK (status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED')),
    trust_score      FLOAT DEFAULT 1.0
                     CHECK (trust_score >= 0.0 AND trust_score <= 1.0),
    created_at       TIMESTAMP DEFAULT NOW()
);

-- 2. status_logs 테이블 (상태 변경 감사 추적)
CREATE TABLE IF NOT EXISTS status_logs (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id        UUID NOT NULL
                     REFERENCES reports(id) ON DELETE CASCADE,
    previous_status  VARCHAR(20),
    changed_status   VARCHAR(20) NOT NULL,
    note             TEXT,
    changed_at       TIMESTAMP DEFAULT NOW()
);

-- reports 인덱스
CREATE INDEX IF NOT EXISTS idx_reports_location
ON reports USING GIST(location);

CREATE INDEX IF NOT EXISTS idx_reports_created_at
ON reports(created_at);

CREATE INDEX IF NOT EXISTS idx_reports_open
ON reports(status)
WHERE status != 'RESOLVED';

-- status_logs 인덱스
CREATE INDEX IF NOT EXISTS idx_status_logs_report_id
ON status_logs(report_id);
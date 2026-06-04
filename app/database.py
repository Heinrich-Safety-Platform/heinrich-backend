from sqlalchemy import (
    create_engine, Column, String, Text, Float, DateTime,
    ForeignKey, CheckConstraint, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, connect_args={"client_encoding": "utf8"})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint("hazard_type IN ('IMMEDIATE', 'LATENT')", name="ck_reports_hazard_type"),
        CheckConstraint("status IN ('OPEN', 'IN_PROGRESS', 'RESOLVED')", name="ck_reports_status"),
        CheckConstraint("trust_score >= 0.0 AND trust_score <= 1.0", name="ck_reports_trust_score"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    content = Column(Text, nullable=True)
    location_detail = Column(String(200), nullable=True)
    image_path = Column(String(500), nullable=False)
    location = Column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
    )
    hazard_type = Column(String(20), nullable=False)
    status = Column(String(20), server_default="OPEN")
    trust_score = Column(Float, server_default=text("1.0"))
    created_at = Column(DateTime, server_default=func.now())

    status_logs = relationship("StatusLog", back_populates="report", cascade="all, delete-orphan")


class StatusLog(Base):
    __tablename__ = "status_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    report_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    previous_status = Column(String(20), nullable=True)
    changed_status = Column(String(20), nullable=False)
    note = Column(Text, nullable=True)
    changed_at = Column(DateTime, server_default=func.now())

    report = relationship("Report", back_populates="status_logs")

from uuid import UUID

from fastapi import HTTPException
from geoalchemy2 import WKTElement
from sqlalchemy.orm import Session

from app.database import Report, StatusLog
from app.schemas.report import StatusUpdateRequest

VALID_TRANSITIONS: dict[str, set[str]] = {
    "OPEN": {"IN_PROGRESS"},
    "IN_PROGRESS": {"OPEN", "RESOLVED"},
    "RESOLVED": set(),
}


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def create_report(
        self,
        lat: float,
        lng: float,
        hazard_type: str,
        content: str | None,
        location_detail: str | None,
        image_path: str,
        trust_score: float,
    ) -> Report:
        report = Report(
            content=content,
            location_detail=location_detail,
            image_path=image_path,
            location=WKTElement(f"POINT({lng} {lat})", srid=4326),
            hazard_type=hazard_type,
            status="OPEN",
            trust_score=trust_score,
        )
        self.db.add(report)
        self.db.commit()
        return report

    def update_status(self, report_id: UUID, req: StatusUpdateRequest) -> tuple[Report, str]:
        report = self.db.query(Report).filter(Report.id == report_id).first()
        if report is None:
            raise HTTPException(status_code=404, detail="존재하지 않는 제보입니다")

        prev_status = report.status

        if prev_status == "RESOLVED":
            raise HTTPException(status_code=422, detail="RESOLVED 상태는 변경할 수 없습니다")

        if prev_status == req.status:
            return report, prev_status

        if req.status not in VALID_TRANSITIONS.get(prev_status, set()):
            raise HTTPException(
                status_code=422,
                detail=f"{prev_status} → {req.status} 전이는 허용되지 않습니다",
            )

        report.status = req.status
        self._log_status_change(report_id, prev_status, req.status, req.note)
        self.db.commit()
        return report, prev_status

    def _log_status_change(self, report_id: UUID, prev: str, new: str, note: str | None) -> None:
        self.db.add(StatusLog(
            report_id=report_id,
            previous_status=prev,
            changed_status=new,
            note=note,
        ))

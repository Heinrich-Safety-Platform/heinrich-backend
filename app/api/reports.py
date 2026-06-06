import os
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.limiter import limiter
from app.schemas.report import ReportCreateResponse, StatusUpdateRequest, StatusUpdateResponse
from app.services.exif_service import ExifService
from app.services.image_service import ImageService
from app.services.report_service import ReportService

_bearer = HTTPBearer(auto_error=False)


def _verify_admin(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> None:
    if credentials is None or credentials.credentials != os.getenv("ADMIN_TOKEN"):
        raise HTTPException(status_code=401, detail="Invalid or missing admin token")

router = APIRouter()

_image_svc = ImageService()
_exif_svc = ExifService()


@router.post("/api/reports", status_code=201, response_model=ReportCreateResponse)
@limiter.limit("3/minute")
async def create_report(
    request: Request,
    latitude: float = Form(...),
    longitude: float = Form(...),
    hazard_type: str = Form(...),
    content: str | None = Form(None),
    location_detail: str | None = Form(None),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ReportCreateResponse:
    if hazard_type not in ("IMMEDIATE", "LATENT"):
        raise HTTPException(status_code=422, detail="hazard_type은 IMMEDIATE 또는 LATENT만 허용됩니다")

    if not image.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다")

    contents = await image.read()

    exif_gps = _image_svc.extract_exif(contents)
    _, dist_m = _exif_svc.validate_location(exif_gps, latitude, longitude)
    trust_score = _exif_svc.calc_trust_score(dist_m)

    image_path = _image_svc.save_image(contents, image.filename)

    report = ReportService(db).create_report(
        lat=latitude,
        lng=longitude,
        hazard_type=hazard_type,
        content=content,
        location_detail=location_detail,
        image_path=image_path,
        trust_score=trust_score,
    )

    return ReportCreateResponse(
        id=report.id,
        status=report.status,
        hazard_type=report.hazard_type,
        trust_score=report.trust_score,
        message="제보가 성공적으로 등록되었습니다.",
    )


@router.patch("/api/admin/reports/{report_id}/status", response_model=StatusUpdateResponse)
async def update_report_status(
    report_id: UUID,
    req: StatusUpdateRequest,
    db: Session = Depends(get_db),
    _: None = Depends(_verify_admin),
) -> StatusUpdateResponse:
    report, prev_status = ReportService(db).update_status(report_id, req)
    return StatusUpdateResponse(
        id=report.id,
        previous_status=prev_status,
        new_status=report.status,
    )

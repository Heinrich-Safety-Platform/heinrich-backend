from __future__ import annotations

from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class LayerResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    lat: float
    lng: float
    hazardType: str    # 'LATENT' | 'IMMEDIATE'
    riskLevel: str     # 'SAFE' | 'NEAR_MISS' | 'MINOR' | 'CRITICAL'
    reportCount: int   # LATENT: 50m 내 누적 count / IMMEDIATE: 1 (고정)
    status: str        # 'OPEN' | 'IN_PROGRESS'


class ReportCreateResponse(BaseModel):
    id: UUID | int
    status: str
    hazard_type: str
    trust_score: float
    message: str


_VALID_STATUSES = Literal["OPEN", "IN_PROGRESS", "RESOLVED"]


class StatusUpdateRequest(BaseModel):
    status: _VALID_STATUSES
    note: Optional[str] = None


class StatusUpdateResponse(BaseModel):
    id: UUID | int
    previous_status: str
    new_status: str

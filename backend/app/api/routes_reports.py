"""
Ministry Reports API Routes
"""
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..integration.mediator import Mediator
from ..integration.entity_resolver import normalize_plate

router = APIRouter(prefix="/api/reports", tags=["reports"])

_mediator: Optional[Mediator] = None


def get_mediator() -> Mediator:
    global _mediator
    if _mediator is None:
        _mediator = Mediator()
    return _mediator


class CreateReportRequest(BaseModel):
    vehicle_ref: str
    report_type: str
    reason: str
    severity: str = "HIGH"
    submitted_by: str = "SYSTEM"


@router.post("/")
async def create_report(request: CreateReportRequest):
    """Create a Ministry of Transportation report for a vehicle violation."""
    mediator = get_mediator()
    result = mediator.create_ministry_report(
        vehicle_ref=request.vehicle_ref,
        report_type=request.report_type,
        reason=request.reason,
        severity=request.severity,
        submitted_by=request.submitted_by,
    )
    return result


@router.get("/pending")
async def get_pending_reports():
    """Get all pending ministry reports."""
    mediator = get_mediator()
    reports = mediator.get_all_pending_reports()
    return {"reports": reports, "count": len(reports)}


@router.get("/all")
async def get_all_reports(skip: int = 0, limit: int = 50):
    """Get all ministry reports with pagination."""
    mediator = get_mediator()
    reports = mediator.get_all_reports_paginated(skip=skip, limit=limit)
    return {"reports": reports, "count": len(reports)}


@router.get("/statistics")
async def get_report_statistics():
    """Get ministry report statistics."""
    mediator = get_mediator()
    stats = mediator.ministry_source.get_statistics()
    return stats

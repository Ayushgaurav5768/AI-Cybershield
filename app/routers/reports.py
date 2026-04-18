import json

from fastapi import APIRouter

from app.database.db import SessionLocal
from app.models.report_model import AllowlistEntry, ExtensionEvent, ScanFeedback, UserReport
from app.schemas.report_schema import (
    AllowlistRequest,
    ExtensionEventRequest,
    FeedbackCreateRequest,
    ReportCreateRequest,
)
from app.services.url_normalizer import extract_domain


router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("")
def create_report(payload: ReportCreateRequest):
    db = SessionLocal()
    try:
        report = UserReport(
            url=payload.url,
            report_type=payload.report_type,
            reason=payload.reason,
            reporter_channel=payload.reporter_channel,
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return {"report_id": report.id, "status": report.status}
    finally:
        db.close()


@router.post("/feedback")
def create_feedback(payload: FeedbackCreateRequest):
    db = SessionLocal()
    try:
        feedback = ScanFeedback(
            scan_id=payload.scan_id,
            url=payload.url,
            verdict_correct=payload.verdict_correct,
            user_label=payload.user_label,
            notes=payload.notes,
        )
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        return {"feedback_id": feedback.id}
    finally:
        db.close()


@router.post("/allowlist")
def add_allowlist(payload: AllowlistRequest):
    db = SessionLocal()
    try:
        domain = payload.domain.lower().strip()
        existing = db.query(AllowlistEntry).filter(AllowlistEntry.domain == domain).first()
        if existing:
            return {"allowlisted": True, "domain": domain, "created": False}

        entry = AllowlistEntry(domain=domain)
        db.add(entry)
        db.commit()
        return {"allowlisted": True, "domain": domain, "created": True}
    finally:
        db.close()


@router.post("/allowlist/by-url")
def add_allowlist_by_url(payload: AllowlistRequest):
    domain = extract_domain(payload.domain)
    return add_allowlist(AllowlistRequest(domain=domain))


@router.post("/extension-event")
def ingest_extension_event(payload: ExtensionEventRequest):
    db = SessionLocal()
    try:
        event = ExtensionEvent(
            event_type=payload.event_type,
            url=payload.url,
            risk_level=payload.risk_level,
            payload_json=payload.payload_json or json.dumps({}),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return {"event_id": event.id}
    finally:
        db.close()

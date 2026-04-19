from fastapi import APIRouter
import logging

from app.models.report_model import AllowlistEntry
from app.models.scan_detail_model import ScanDetail
from app.models.scan_model import Scan
from app.schemas.scan_schema import ScanRequest, ScanResponse
from app.services.detection_pipeline import run_hybrid_detection
from app.services.rag_service import build_rag_explanation
from core.security import sanitize_url_input
from core.config import settings
from app.database.db import SessionLocal


router = APIRouter()
logger = logging.getLogger(__name__)


def _build_plain_scan_explanation(url: str, risk_level: str, reasons: list[str], allowlisted: bool) -> str:
    if allowlisted:
        return (
            "This domain is in your allowlist, so it is treated as safe. "
            "Review suspicious behavior manually if content has changed."
        )

    short_reason = reasons[0] if reasons else "No strong phishing indicators were detected."
    return f"URL {url} is classified as {risk_level}. Key signal: {short_reason}"


@router.post("/scan", response_model=ScanResponse)
def scan_url(data: ScanRequest):
    cleaned_url = sanitize_url_input(data.url)
    result = run_hybrid_detection(cleaned_url)

    db = SessionLocal()
    try:
        domain = result.normalized_url.split("//", 1)[-1].split("/", 1)[0].split(":")[0]
        allowlisted = db.query(AllowlistEntry).filter(AllowlistEntry.domain == domain).first()

        final_prediction = "Safe" if allowlisted else result.prediction
        final_risk = 0 if allowlisted else result.risk_score
        final_level = "safe" if allowlisted else result.risk_level
        final_reasons = ["Domain is user allowlisted"] if allowlisted else result.reasons
        final_action = (
            "Domain is allowlisted. Continue only if this destination is still expected and trusted."
            if allowlisted
            else result.recommended_action
        )

        scan = Scan(url=cleaned_url, prediction=final_prediction, risk_score=final_risk)
        db.add(scan)
        db.commit()
        db.refresh(scan)

        friendly_explanation = _build_plain_scan_explanation(cleaned_url, final_level, final_reasons, bool(allowlisted))
        if settings.enable_rag_scan_explanation:
            try:
                friendly_explanation = build_rag_explanation(cleaned_url, final_level, final_reasons)
            except Exception as exc:
                logger.warning("RAG scan explanation failed, using plain explanation: %s", exc)

        detail = ScanDetail(
            scan_id=scan.id,
            normalized_url=result.normalized_url,
            confidence_score=result.confidence_score,
            risk_level=final_level,
            recommended_action=final_action,
            signals_json=result.signals_json(),
            user_explanation=friendly_explanation,
            analyst_explanation=result.analyst_explanation,
        )
        db.add(detail)
        db.commit()

        return {
            "prediction": final_prediction,
            "risk_score": final_risk,
            "reasons": final_reasons,
            "confidence_score": result.confidence_score,
            "risk_level": final_level,
            "signals": result.signals,
            "recommended_action": final_action,
            "user_explanation": friendly_explanation,
            "analyst_explanation": result.analyst_explanation,
            "scan_id": scan.id,
        }
    finally:
        db.close()


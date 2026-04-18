from fastapi import APIRouter

from app.models.report_model import AllowlistEntry
from app.models.scan_detail_model import ScanDetail
from app.models.scan_model import Scan
from app.schemas.scan_schema import ScanRequest, ScanResponse
from app.services.detection_pipeline import run_hybrid_detection
from app.services.rag_service import build_rag_explanation
from core.security import sanitize_url_input
from app.database.db import SessionLocal


router = APIRouter()


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

        scan = Scan(url=cleaned_url, prediction=final_prediction, risk_score=final_risk)
        db.add(scan)
        db.commit()
        db.refresh(scan)

        friendly_explanation = build_rag_explanation(cleaned_url, final_level, final_reasons)

        detail = ScanDetail(
            scan_id=scan.id,
            normalized_url=result.normalized_url,
            confidence_score=result.confidence_score,
            risk_level=final_level,
            recommended_action=result.recommended_action,
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
            "recommended_action": result.recommended_action,
            "user_explanation": friendly_explanation,
            "analyst_explanation": result.analyst_explanation,
            "scan_id": scan.id,
        }
    finally:
        db.close()


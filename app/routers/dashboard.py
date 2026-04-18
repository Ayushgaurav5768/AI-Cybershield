from fastapi import APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.db import SessionLocal
from app.models.report_model import ExtensionEvent, UserReport
from app.models.scan_model import Scan
from app.services.url_normalizer import extract_domain

router = APIRouter()


@router.get("/dashboard")
def get_dashboard():
    db: Session = SessionLocal()

    total_scans = db.query(func.count(Scan.id)).scalar()
    phishing_count = db.query(func.count(Scan.id)) \
                        .filter(Scan.prediction == "Phishing") \
                        .scalar()

    safe_count = db.query(func.count(Scan.id)) \
                    .filter(Scan.prediction == "Safe") \
                    .scalar()

    db.close()

    return {
        "total_scans": total_scans,
        "phishing_count": phishing_count,
        "safe_count": safe_count
    }


@router.get("/recent-scans")
def get_recent_scans():
    db = SessionLocal()

    scans = db.query(Scan) \
              .order_by(Scan.created_at.desc()) \
              .limit(10) \
              .all()

    db.close()

    return [
        {
            "url": scan.url,
            "prediction": scan.prediction,
            "risk_score": scan.risk_score,
            "created_at": scan.created_at
        }
        for scan in scans
    ]


@router.get("/dashboard/metrics")
def get_dashboard_metrics():
    db = SessionLocal()
    try:
        total_scans = db.query(func.count(Scan.id)).scalar() or 0
        phishing_count = db.query(func.count(Scan.id)).filter(Scan.prediction == "Phishing").scalar() or 0
        safe_count = db.query(func.count(Scan.id)).filter(Scan.prediction == "Safe").scalar() or 0
        reports_pending = db.query(func.count(UserReport.id)).filter(UserReport.status == "queued").scalar() or 0
        extension_events = db.query(func.count(ExtensionEvent.id)).scalar() or 0

        return {
            "total_scans": total_scans,
            "phishing_count": phishing_count,
            "safe_count": safe_count,
            "reports_pending": reports_pending,
            "extension_events": extension_events,
        }
    finally:
        db.close()


@router.get("/dashboard/top-domains")
def top_domains(limit: int = 10):
    db = SessionLocal()
    try:
        rows = db.query(Scan.url, Scan.prediction, Scan.risk_score).order_by(Scan.created_at.desc()).limit(400).all()
        domain_stats = {}

        for row in rows:
            domain = extract_domain(row.url)
            if domain not in domain_stats:
                domain_stats[domain] = {"domain": domain, "count": 0, "avg_risk": 0, "phishing_hits": 0}
            entry = domain_stats[domain]
            entry["count"] += 1
            entry["avg_risk"] += row.risk_score
            entry["phishing_hits"] += 1 if row.prediction == "Phishing" else 0

        ordered = list(domain_stats.values())
        for entry in ordered:
            entry["avg_risk"] = int(entry["avg_risk"] / max(1, entry["count"]))

        ordered.sort(key=lambda x: (x["phishing_hits"], x["avg_risk"], x["count"]), reverse=True)
        return ordered[:limit]
    finally:
        db.close()


@router.get("/dashboard/trends")
def dashboard_trends(limit_days: int = 7):
    db = SessionLocal()
    try:
        rows = db.query(Scan.created_at, Scan.prediction).order_by(Scan.created_at.desc()).limit(limit_days * 120).all()
        buckets = {}

        for row in rows:
            day = row.created_at.strftime("%Y-%m-%d")
            if day not in buckets:
                buckets[day] = {"day": day, "phishing": 0, "safe": 0}
            if row.prediction == "Phishing":
                buckets[day]["phishing"] += 1
            else:
                buckets[day]["safe"] += 1

        return sorted(buckets.values(), key=lambda x: x["day"])
    finally:
        db.close()


@router.get("/dashboard/extension-events")
def extension_event_feed(limit: int = 25):
    db = SessionLocal()
    try:
        events = db.query(ExtensionEvent).order_by(ExtensionEvent.created_at.desc()).limit(limit).all()
        return [
            {
                "id": event.id,
                "event_type": event.event_type,
                "url": event.url,
                "risk_level": event.risk_level,
                "created_at": event.created_at,
            }
            for event in events
        ]
    finally:
        db.close()

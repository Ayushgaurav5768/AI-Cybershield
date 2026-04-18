from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from app.database.db import Base


class ScanDetail(Base):
    __tablename__ = "scan_details"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False, index=True)
    normalized_url = Column(String, nullable=False)
    confidence_score = Column(Integer, nullable=False)
    risk_level = Column(String, nullable=False)
    recommended_action = Column(String, nullable=False)
    signals_json = Column(Text, nullable=False)
    user_explanation = Column(Text, nullable=False)
    analyst_explanation = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

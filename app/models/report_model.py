from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from app.database.db import Base


class UserReport(Base):
    __tablename__ = "user_reports"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False, index=True)
    report_type = Column(String, nullable=False)
    reason = Column(Text, nullable=True)
    reporter_channel = Column(String, nullable=False, default="dashboard")
    status = Column(String, nullable=False, default="queued")
    created_at = Column(DateTime, default=datetime.utcnow)


class ScanFeedback(Base):
    __tablename__ = "scan_feedback"

    id = Column(Integer, primary_key=True, index=True)
    scan_id = Column(Integer, nullable=True, index=True)
    url = Column(String, nullable=False, index=True)
    verdict_correct = Column(Boolean, nullable=False)
    user_label = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AllowlistEntry(Base):
    __tablename__ = "allowlist_entries"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String, unique=True, nullable=False, index=True)
    source = Column(String, nullable=False, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)


class ExtensionEvent(Base):
    __tablename__ = "extension_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False, index=True)
    url = Column(String, nullable=True)
    risk_level = Column(String, nullable=True)
    payload_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

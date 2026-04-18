from pydantic import BaseModel, Field


class ReportCreateRequest(BaseModel):
    url: str
    report_type: str = Field(..., description="phishing|safe|suspicious")
    reason: str | None = None
    reporter_channel: str = "extension"


class FeedbackCreateRequest(BaseModel):
    url: str
    scan_id: int | None = None
    verdict_correct: bool
    user_label: str | None = None
    notes: str | None = None


class AllowlistRequest(BaseModel):
    domain: str


class ExtensionEventRequest(BaseModel):
    event_type: str
    url: str | None = None
    risk_level: str | None = None
    payload_json: str | None = None

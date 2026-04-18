from pydantic import BaseModel
from typing import List


class ScanRequest(BaseModel):
    url: str


class SignalItem(BaseModel):
    code: str
    severity: str
    points: int
    message: str


class ScanResponse(BaseModel):
    prediction: str
    risk_score: int
    reasons: List[str]
    confidence_score: int
    risk_level: str
    signals: List[SignalItem]
    recommended_action: str
    user_explanation: str
    analyst_explanation: str
    scan_id: int | None = None

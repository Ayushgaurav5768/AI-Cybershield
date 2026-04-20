from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List

from app.services.feature_extractor import extract_features
from app.services.heuristics_service import evaluate_heuristics
from app.services.prediction_service import predict_url
from app.services.threat_intel_service import threat_intel_score
from app.services.url_normalizer import normalize_url


@dataclass
class DetectionResult:
    prediction: str
    risk_score: int
    confidence_score: int
    risk_level: str
    signals: List[dict]
    recommended_action: str
    reasons: List[str]
    user_explanation: str
    analyst_explanation: str
    normalized_url: str

    def signals_json(self) -> str:
        return json.dumps(self.signals)


def _risk_level(score: int) -> str:
    if score >= 75:
        return "dangerous"
    if score >= 45:
        return "suspicious"
    return "safe"


def _recommended_action(level: str) -> str:
    if level == "dangerous":
        return "Do not enter credentials. Leave the site and report it."
    if level == "suspicious":
        return "Proceed with caution, verify the domain independently, and avoid sensitive actions."
    return "No high-risk signal detected. Continue normal browsing with standard caution."


def _apply_signal_boosts(base_score: int, ti_score: int, heuristic_score: int, ml_score: int, signals: List[dict]) -> int:
    # Promote risk when multiple strong indicators are present so blended scoring does not under-report.
    boosted = base_score
    high_signal_count = sum(1 for signal in signals if signal.get("severity") in {"high", "critical"})
    signal_codes = {signal.get("code") for signal in signals}

    if ti_score >= 90:
        boosted = max(boosted, 90)
    elif ti_score >= 70:
        boosted = max(boosted, 75)

    if high_signal_count >= 2:
        boosted = max(boosted, 62)
    elif high_signal_count == 1 and (ml_score >= 55 or heuristic_score >= 50):
        boosted = max(boosted, 55)

    # A lure keyword combined with brand impersonation is a strong phishing pattern.
    if "brand-impersonation" in signal_codes and "suspicious-keyword" in signal_codes:
        boosted = max(boosted, 68)

    if "ip-domain" in signal_codes or "at-symbol" in signal_codes:
        boosted = max(boosted, 60)

    if heuristic_score >= 65:
        boosted = max(boosted, 60)

    if ml_score >= 70:
        boosted = max(boosted, 70)
    elif ml_score >= 55 and heuristic_score >= 35:
        boosted = max(boosted, 58)

    return max(0, min(100, boosted))


def run_hybrid_detection(url: str) -> DetectionResult:
    normalized = normalize_url(url)

    ti_score, ti_signals, hints = threat_intel_score(normalized)
    features = extract_features(normalized)
    features.update(hints)

    heuristic_score, heuristic_signals = evaluate_heuristics(features)
    ml_score, ml_label, ml_confidence = predict_url(features)

    total_signals = ti_signals + heuristic_signals
    weighted_score = int((0.45 * ml_score) + (0.35 * heuristic_score) + (0.20 * ti_score))
    risk_score = _apply_signal_boosts(weighted_score, ti_score, heuristic_score, ml_score, total_signals)

    level = _risk_level(risk_score)
    prediction = "Phishing" if level in {"dangerous", "suspicious"} else "Safe"

    if ml_label == "Phishing" and (heuristic_score >= 30 or ti_score >= 20):
        prediction = "Phishing"
        if risk_score < 55:
            risk_score = 55
            level = _risk_level(risk_score)

    confidence_score = min(99, max(35, int((abs(risk_score - 50) * 1.2) + (len(total_signals) * 4) + (ml_confidence * 0.4))))

    reasons = [signal["message"] for signal in total_signals[:5]]
    if not reasons:
        reasons = ["No strong phishing indicators were detected in URL-level analysis."]

    user_explanation = (
        f"This page is marked as {level}. The score is {risk_score}/100 based on URL risk patterns, "
        f"model signals, and threat intelligence checks."
    )

    analyst_explanation = (
        f"hybrid={{ml:{ml_score}, heuristics:{heuristic_score}, intel:{ti_score}}}; "
        f"ml_label={ml_label}; features={{{', '.join(f'{k}:{v}' for k, v in sorted(features.items()))}}}"
    )

    return DetectionResult(
        prediction=prediction,
        risk_score=risk_score,
        confidence_score=confidence_score,
        risk_level=level,
        signals=total_signals,
        recommended_action=_recommended_action(level),
        reasons=reasons,
        user_explanation=user_explanation,
        analyst_explanation=analyst_explanation,
        normalized_url=normalized,
    )

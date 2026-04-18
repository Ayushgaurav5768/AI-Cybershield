from __future__ import annotations

import json
import os

import joblib

from core.config import settings


MODEL_PATH = settings.model_path
MODEL_META_PATH = settings.model_meta_path

model = None
meta = {}

if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)

if os.path.exists(MODEL_META_PATH):
    with open(MODEL_META_PATH, "r", encoding="utf-8") as handle:
        meta = json.load(handle)


def _feature_to_dataset_value(col: str, features: dict) -> int:
    mapping = {
        "having_IP_Address": -1 if features.get("has_ip_in_domain") else 1,
        "URL_Length": -1 if features.get("url_length", 0) > 75 else (0 if features.get("url_length", 0) > 54 else 1),
        "Shortining_Service": -1 if features.get("is_shortener") else 1,
        "having_At_Symbol": -1 if features.get("has_at") else 1,
        "double_slash_redirecting": -1 if features.get("redirect_hint") else 1,
        "Prefix_Suffix": -1 if features.get("has_dash") else 1,
        "having_Sub_Domain": -1 if features.get("num_subdomains", 0) >= 2 else 1,
        "SSLfinal_State": 1 if features.get("has_https") else -1,
        "HTTPS_token": -1 if "https" in str(features).lower() and not features.get("has_https") else 1,
        "Redirect": 1 if features.get("redirect_hint") else 0,
        "Submitting_to_email": -1 if features.get("suspicious_word") else 1,
        "Abnormal_URL": -1 if features.get("brand_impersonation") else 1,
        "web_traffic": 0,
        "Page_Rank": 0,
        "Google_Index": 1,
        "Statistical_report": -1 if features.get("is_known_bad") else 1,
    }

    return int(mapping.get(col, 0))


def _fallback_risk(features: dict) -> tuple[int, str, int]:
    base = 10
    base += 18 if features.get("has_at") else 0
    base += 20 if features.get("has_ip_in_domain") else 0
    base += 15 if features.get("suspicious_word") else 0
    base += 10 if features.get("brand_impersonation") else 0
    base += 8 if features.get("num_subdomains", 0) >= 3 else 0
    base += 7 if not features.get("has_https") else 0
    score = max(0, min(100, base))
    label = "Phishing" if score >= 55 else "Safe"
    confidence = min(95, 45 + int(abs(score - 50) * 0.8))
    return score, label, confidence


def predict_url(features: dict) -> tuple[int, str, int]:
    if model is None:
        return _fallback_risk(features)

    try:
        feature_columns = meta.get("feature_columns", [])
        if feature_columns:
            row = [_feature_to_dataset_value(col, features) for col in feature_columns]
        else:
            row = [
                features.get("url_length", 0),
                features.get("has_https", 0),
                features.get("num_dots", 0),
                features.get("has_at", 0),
                features.get("has_dash", 0),
                features.get("suspicious_word", 0),
            ]

        prediction = model.predict([row])[0]
        label = "Phishing" if prediction in {-1, 1} else "Safe"

        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba([row])[0]
            classes = list(model.classes_)
            if -1 in classes:
                phish_probability = probabilities[classes.index(-1)]
            elif 1 in classes:
                phish_probability = probabilities[classes.index(1)]
            else:
                phish_probability = max(probabilities)
            risk_score = int(phish_probability * 100)
            confidence = int(max(probabilities) * 100)
        else:
            risk_score, _, confidence = _fallback_risk(features)

        return max(0, min(100, risk_score)), label, max(1, min(99, confidence))
    except Exception:
        return _fallback_risk(features)

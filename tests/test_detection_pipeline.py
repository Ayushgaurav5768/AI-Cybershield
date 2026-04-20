from app.services.detection_pipeline import run_hybrid_detection


def test_impersonation_url_is_not_marked_safe():
    result = run_hybrid_detection("https://secure-update-paypal-support.com/login")

    assert result.prediction == "Phishing"
    assert result.risk_level in {"suspicious", "dangerous"}
    assert result.risk_score >= 45


def test_simple_benign_url_stays_safe():
    result = run_hybrid_detection("https://example.com")

    assert result.prediction == "Safe"
    assert result.risk_level == "safe"
    assert result.risk_score < 45

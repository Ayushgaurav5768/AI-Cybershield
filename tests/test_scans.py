from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_scan_endpoint_contract():
    response = client.post("/scan", json={"url": "https://example.com/login"})
    assert response.status_code == 200

    payload = response.json()
    assert "prediction" in payload
    assert "risk_score" in payload
    assert "confidence_score" in payload
    assert "risk_level" in payload
    assert "signals" in payload
    assert "recommended_action" in payload
    assert "user_explanation" in payload


def test_reports_endpoint():
    response = client.post(
        "/reports",
        json={
            "url": "https://phish.example",
            "report_type": "phishing",
            "reason": "Looks fake",
            "reporter_channel": "test",
        },
    )
    assert response.status_code == 200
    assert "report_id" in response.json()

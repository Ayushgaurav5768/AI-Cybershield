from __future__ import annotations

from typing import Dict, List, Tuple

from app.services.url_normalizer import extract_domain

# TODO: Replace with a live threat-intel feed integration for production.
KNOWN_BAD_DOMAINS = {
    "paypa1-security-check.example",
    "micros0ft-auth-check.example",
}

SUSPICIOUS_TLDS = {"zip", "mov", "click", "work", "top", "xyz"}

SHORTENERS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "is.gd",
    "goo.gl",
    "cutt.ly",
}


def threat_intel_score(url: str) -> Tuple[int, List[dict], Dict[str, int]]:
    domain = extract_domain(url)
    domain_root = domain.split(":")[0]
    tld = domain_root.rsplit(".", 1)[-1] if "." in domain_root else ""

    score = 0
    signals: List[dict] = []

    if domain_root in KNOWN_BAD_DOMAINS:
        score += 95
        signals.append(
            {
                "code": "known-bad-domain",
                "severity": "critical",
                "points": 95,
                "message": "Domain matched threat intelligence blocklist",
            }
        )

    if tld in SUSPICIOUS_TLDS:
        score += 12
        signals.append(
            {
                "code": "suspicious-tld",
                "severity": "low",
                "points": 12,
                "message": f"TLD .{tld} is commonly abused in phishing campaigns",
            }
        )

    is_shortener = int(domain_root in SHORTENERS)
    if is_shortener:
        score += 10
        signals.append(
            {
                "code": "shortener-domain",
                "severity": "medium",
                "points": 10,
                "message": "Shortener domains can obscure malicious destinations",
            }
        )

    score = min(100, score)
    hints = {
        "is_known_bad": int(domain_root in KNOWN_BAD_DOMAINS),
        "is_shortener": is_shortener,
    }

    return score, signals, hints

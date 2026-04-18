from __future__ import annotations

from typing import Dict, List, Tuple


def evaluate_heuristics(features: Dict[str, int]) -> Tuple[int, List[dict]]:
    signals: List[dict] = []
    score = 0

    def add_signal(code: str, severity: str, points: int, message: str) -> None:
        nonlocal score
        score += points
        signals.append(
            {
                "code": code,
                "severity": severity,
                "points": points,
                "message": message,
            }
        )

    if features.get("has_ip_in_domain"):
        add_signal("ip-domain", "high", 24, "Domain appears to use a raw IP address")

    if features.get("has_at"):
        add_signal("at-symbol", "high", 22, "URL contains '@', a common obfuscation trick")

    if features.get("suspicious_word"):
        add_signal("suspicious-keyword", "medium", 15, "Potential phishing keywords detected")

    if features.get("is_punycode"):
        add_signal("punycode", "medium", 14, "Punycode detected, possible homograph risk")

    if features.get("num_subdomains", 0) >= 3:
        add_signal("deep-subdomain", "medium", 12, "Excessive subdomain depth can hide impersonation")

    if features.get("is_shortener"):
        add_signal("url-shortener", "medium", 11, "URL shortener detected")

    if not features.get("has_https"):
        add_signal("no-https", "medium", 10, "URL is not using HTTPS")

    if features.get("path_entropy_high"):
        add_signal("high-entropy-path", "low", 8, "High-entropy path may indicate random phishing routes")

    if features.get("redirect_hint"):
        add_signal("redirect-hint", "medium", 10, "Redirect-like patterns found in URL")

    if features.get("brand_impersonation"):
        add_signal("brand-impersonation", "high", 25, "Potential brand impersonation detected")

    score = min(100, max(0, score))
    return score, signals

from __future__ import annotations

import math
import re
from urllib.parse import urlparse


SUSPICIOUS_WORDS = {
    "login",
    "verify",
    "update",
    "bank",
    "secure",
    "invoice",
    "password",
    "wallet",
    "auth",
    "confirm",
}

KNOWN_BRANDS = {
    "google",
    "microsoft",
    "paypal",
    "amazon",
    "apple",
    "facebook",
    "instagram",
    "netflix",
    "linkedin",
    "github",
}


def _entropy(value: str) -> float:
    if not value:
        return 0.0

    counts = {}
    for ch in value:
        counts[ch] = counts.get(ch, 0) + 1

    length = len(value)
    return -sum((freq / length) * math.log2(freq / length) for freq in counts.values())


def extract_features(url: str) -> dict:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path or ""
    query = parsed.query or ""
    full = f"{host}{path}?{query}".lower()

    hostname = host.split(":")[0]
    labels = [label for label in hostname.split(".") if label]
    subdomains = labels[:-2] if len(labels) > 2 else []

    suspicious_word = int(any(word in full for word in SUSPICIOUS_WORDS))
    brand_mentions = [brand for brand in KNOWN_BRANDS if brand in full]
    brand_impersonation = int(bool(brand_mentions and not any(hostname.endswith(f"{brand}.com") for brand in brand_mentions)))

    has_ip_in_domain = int(bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", hostname)))
    is_punycode = int("xn--" in hostname)
    redirect_hint = int(any(token in query.lower() for token in ["url=", "redirect", "next="]))

    features = {
        "url_length": len(url),
        "has_https": int(parsed.scheme == "https"),
        "num_dots": hostname.count("."),
        "num_subdomains": len(subdomains),
        "has_at": int("@" in url),
        "has_dash": int("-" in hostname),
        "suspicious_word": suspicious_word,
        "has_ip_in_domain": has_ip_in_domain,
        "is_punycode": is_punycode,
        "path_entropy_high": int(_entropy(path + query) >= 3.5),
        "redirect_hint": redirect_hint,
        "brand_impersonation": brand_impersonation,
        "path_length": len(path),
        "query_length": len(query),
    }

    return features

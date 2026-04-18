from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


def normalize_url(raw_url: str) -> str:
    parsed = urlparse(raw_url.strip())

    netloc = parsed.netloc.lower().strip(".")
    if ":80" in netloc and parsed.scheme == "http":
        netloc = netloc.replace(":80", "")
    if ":443" in netloc and parsed.scheme == "https":
        netloc = netloc.replace(":443", "")

    sorted_query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))

    return urlunparse(
        (
            parsed.scheme.lower(),
            netloc,
            parsed.path or "/",
            parsed.params,
            sorted_query,
            parsed.fragment,
        )
    )


def extract_domain(raw_url: str) -> str:
    return urlparse(raw_url).netloc.lower().split(":")[0]

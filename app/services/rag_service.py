from __future__ import annotations

from app.rag.retriever import get_rag_response


def build_rag_explanation(url: str, risk_level: str, reasons: list[str]) -> str:
    prompt = (
        "Explain this phishing analysis in plain language for a non-technical user. "
        f"URL: {url}. Risk level: {risk_level}. Key reasons: {', '.join(reasons)}. "
        "Also include one short safety recommendation."
    )

    try:
        return get_rag_response(prompt)
    except Exception:
        return (
            f"The site was rated {risk_level} because we found risk indicators such as: "
            f"{', '.join(reasons[:3])}. Avoid entering passwords unless you can verify the domain."
        )

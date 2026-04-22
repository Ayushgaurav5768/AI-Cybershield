from functools import lru_cache
from pathlib import Path
import re
from typing import List

from openai import OpenAI

from core.config import get_ai_settings

try:
    import google.generativeai as genai
except ImportError:
    genai = None


@lru_cache(maxsize=1)
def _knowledge_chunks() -> List[str]:
    kb_dir = Path("app/rag/knowledge_base")
    chunks: list[str] = []

    for txt_file in sorted(kb_dir.glob("*.txt")):
        try:
            content = txt_file.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        parts = [part.strip() for part in re.split(r"\n\s*\n", content) if part.strip()]
        for part in parts:
            if len(part) <= 750:
                chunks.append(part)
                continue

            for i in range(0, len(part), 650):
                piece = part[i:i + 750].strip()
                if piece:
                    chunks.append(piece)

    return chunks


@lru_cache(maxsize=4)
def _build_chat_model(provider: str, api_key: str, model_name: str):
    if provider == "gemini":
        if genai is None:
            raise RuntimeError("google-generativeai is not installed")
        genai.configure(api_key=api_key)
        return ("gemini", genai.GenerativeModel(model_name))

    if provider == "openai":
        return ("openai", OpenAI(api_key=api_key))

    raise RuntimeError("No supported AI provider key found")


def _normalize_query(query: str) -> str:
    return " ".join(query.split()).strip().lower()


def _top_context(query: str, k: int = 3) -> str:
    terms = set(re.findall(r"[a-z0-9]+", query.lower()))
    if not terms:
        return ""

    scored: list[tuple[float, str]] = []
    for chunk in _knowledge_chunks():
        words = set(re.findall(r"[a-z0-9]+", chunk.lower()))
        if not words:
            continue
        overlap = len(terms & words)
        if overlap == 0:
            continue
        score = overlap / max(1, len(terms))
        scored.append((score, chunk))

    if not scored:
        return ""

    top_chunks = [chunk for _, chunk in sorted(scored, key=lambda item: item[0], reverse=True)[:k]]
    return "\n\n".join(top_chunks)


def _generate_answer(prompt: str) -> str:
    ai_settings = get_ai_settings()

    if ai_settings.gemini_api_key:
        provider, client = _build_chat_model("gemini", ai_settings.gemini_api_key, ai_settings.gemini_model)
    elif ai_settings.openai_api_key:
        provider, client = _build_chat_model("openai", ai_settings.openai_api_key, ai_settings.openai_model)
    else:
        raise RuntimeError("No supported AI provider key found")

    if provider == "gemini":
        response = client.generate_content(prompt)
        text = getattr(response, "text", None)
        if text and text.strip():
            return text.strip()
        return "I could not generate a response right now. Please try again."

    response = client.responses.create(
        model=ai_settings.openai_model,
        input=prompt,
    )
    text = getattr(response, "output_text", "")
    if text and text.strip():
        return text.strip()
    return "I could not generate a response right now. Please try again."


def _local_fallback_answer(query: str, context: str) -> str:
    base = context.strip()
    if base:
        return (
            "The AI provider is unavailable right now, so here is a local guidance summary based on the knowledge base:\n\n"
            f"{base[:1200]}"
        )

    return (
        "The AI provider is unavailable right now. Please verify the Gemini/OpenAI key in Railway, "
        "redeploy the backend, and retry."
    )


def warm_assistant_assets():
    _knowledge_chunks()
    ai_settings = get_ai_settings()
    if ai_settings.gemini_api_key:
        _build_chat_model("gemini", ai_settings.gemini_api_key, ai_settings.gemini_model)
    elif ai_settings.openai_api_key:
        _build_chat_model("openai", ai_settings.openai_api_key, ai_settings.openai_model)


def _get_rag_response(normalized_query: str):
    context = _top_context(normalized_query, k=3)

    prompt = (
        "Answer briefly and clearly using the context. "
        "If the context is insufficient, give the safest practical guidance.\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{normalized_query}\n\n"
        "Answer:"
    )

    try:
        return _generate_answer(prompt)
    except Exception:
        return _local_fallback_answer(normalized_query, context)


def get_rag_response(query: str):
    return _get_rag_response(_normalize_query(query))

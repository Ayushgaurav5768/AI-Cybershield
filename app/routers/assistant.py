from fastapi import APIRouter
import logging
from app.rag.retriever import get_rag_response
from app.rag.retriever import _build_chat_model
from app.schemas.chat_schema import ChatRequest, ChatResponse
from core.config import get_ai_settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/assistant", response_model=ChatResponse)
def chat(request: ChatRequest):
    ai_settings = get_ai_settings()

    # Fallback to offline guidance when no AI provider is configured.
    if not ai_settings.has_ai_api_key:
        return {
            "response": (
                "Assistant is running in offline mode because no AI API key is configured. "
                "Set GEMINI_API_KEY (or GOOGLE_API_KEY) or OPENAI_API_KEY in your environment, then restart the backend."
            )
        }

    try:
        answer = get_rag_response(request.question)
        return {"response": answer}
    except Exception as e:
        logger.error(f"Assistant error: {type(e).__name__}: {e}", exc_info=True)
        provider_hint = "Gemini" if ai_settings.gemini_api_key else ("OpenAI" if ai_settings.openai_api_key else "none")
        try:
            _build_chat_model.cache_clear()
        except Exception:
            pass
        return {
            "response": (
                "Assistant temporarily failed to generate a response from the configured AI provider. "
                f"Current provider hint: {provider_hint}. Please verify the key, model access, and Railway redeploy. "
                "If the issue persists, check the backend logs for the exact provider error."
            )
        }

from fastapi import APIRouter
import logging
from app.rag.retriever import get_rag_response
from app.schemas.chat_schema import ChatRequest, ChatResponse
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/assistant", response_model=ChatResponse)
def chat(request: ChatRequest):
    # Fallback to offline guidance when no AI provider is configured.
    if not settings.has_ai_api_key:
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
        return {
            "response": (
                "Assistant temporarily failed to generate a response. "
                "Please try again in a moment or verify your AI provider configuration."
            )
        }

from functools import lru_cache

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI

from core.config import settings

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None


@lru_cache(maxsize=1)
def _get_embeddings():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


@lru_cache(maxsize=1)
def _get_vector_store():
    embeddings = _get_embeddings()
    return FAISS.load_local(
        "app/rag/faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )


@lru_cache(maxsize=1)
def _build_chat_model():
    if settings.gemini_api_key:
        if ChatGoogleGenerativeAI is None:
            raise RuntimeError("langchain-google-genai is not installed")
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            temperature=0.3,
            google_api_key=settings.gemini_api_key,
        )

    if settings.openai_api_key:
        return ChatOpenAI(
            model=settings.openai_model,
            temperature=0.3,
            api_key=settings.openai_api_key,
        )

    raise RuntimeError("No supported AI provider key found")


def _normalize_query(query: str) -> str:
    return " ".join(query.split()).strip().lower()


def warm_assistant_assets():
    _get_embeddings()
    _get_vector_store()
    _build_chat_model()


@lru_cache(maxsize=128)
def _get_rag_response_cached(normalized_query: str):
    vector_store = _get_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 1})

    docs = retriever.invoke(normalized_query)

    context = "\n\n".join([doc.page_content[:700] for doc in docs])

    llm = _build_chat_model()

    prompt = (
        "Answer briefly and clearly using the context. "
        "If the context is insufficient, give the safest practical guidance.\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{normalized_query}\n\n"
        "Answer:"
    )

    response = llm.invoke(prompt)

    return response.content


def get_rag_response(query: str):
    return _get_rag_response_cached(_normalize_query(query))

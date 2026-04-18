import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _to_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "AI CyberShield")
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = _to_bool(os.getenv("DEBUG"), default=False)

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./cybershield.db")
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    max_scan_requests_per_minute: int = int(os.getenv("MAX_SCAN_REQUESTS_PER_MINUTE", "120"))
    max_general_requests_per_minute: int = int(os.getenv("MAX_GENERAL_REQUESTS_PER_MINUTE", "300"))

    model_path: str = os.getenv("MODEL_PATH", os.path.join("ml", "model.pkl"))
    model_meta_path: str = os.getenv("MODEL_META_PATH", os.path.join("ml", "model_meta.json"))

    @property
    def has_ai_api_key(self) -> bool:
        return bool(self.openai_api_key or self.gemini_api_key)


settings = Settings()

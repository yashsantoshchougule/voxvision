from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIRECTORY = Path(__file__).resolve().parent
PROJECT_DIRECTORY = BACKEND_DIRECTORY.parent


class Settings(BaseSettings):
    app_name: str = "VoxVision AI"
    environment: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    mongodb_uri: str = "mongodb://localhost:27017"
    database_name: str = "voxvision_ai"
    ai_provider: str = "auto"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3.6:latest"
    ollama_timeout_seconds: float = 180.0
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    tesseract_cmd: str = ""
    max_upload_mb: int = 5
    ocr_language: str = "eng"
    screen_change_threshold: float = 0.12
    min_ocr_interval_seconds: int = 7
    max_ai_input_characters: int = 60000
    report_chunk_size: int = 12000
    cors_origins: str = "http://localhost:8000,chrome-extension://EXTENSION_ID"
    # Local developer settings belong at the project root, while the original
    # backend/.env location remains supported for existing installations. Later
    # files override earlier ones, so .env.local is the safe local override.
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIRECTORY / ".env", PROJECT_DIRECTORY / ".env.local"),
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def allowed_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

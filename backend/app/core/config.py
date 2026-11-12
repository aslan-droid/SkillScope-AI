from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    PROJECT_NAME: str = "SkillScope AI"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "skillscope-local-dev-secret-key-2026"

    POSTGRES_USER: str = "skillscope"
    POSTGRES_PASSWORD: str = "skillscope_pass"
    POSTGRES_DB: str = "skillscope_db"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+psycopg2://skillscope:skillscope_pass@localhost:5432/skillscope_db"

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    AUTO_SEED_DEMO_DATA: bool = True
    AUTO_TRAIN_MODELS: bool = True

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma3:1b"
    OLLAMA_TIMEOUT_SECONDS: int = 8

    MAX_CSV_UPLOAD_MB: int = 15
    MAX_CV_UPLOAD_MB: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()

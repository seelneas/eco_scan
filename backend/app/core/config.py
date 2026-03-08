"""
EcoScan Backend Configuration
Loads environment variables and provides application-wide settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # --- Application ---
    APP_NAME: str = "EcoScan API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # --- LLM ---
    GEMINI_API_KEY: str = ""
    LLM_MODEL: str = "gemini-2.5-flash-lite"
    LLM_TEMPERATURE: float = 0.1  # Low temp for consistent, factual extraction
    LLM_MAX_TOKENS: int = 4000

    # --- External APIs ---
    WIKIRATE_API_KEY: str = ""

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./ecoscan.db"

    # --- Redis (optional caching) ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- CORS ---
    CORS_ORIGINS: str = "*"

    # --- Phase 7: Security & Rate Limiting ---
    API_KEYS: list[str] = []  # Empty = no key required (dev mode)
    RATE_LIMIT_ANALYZE: int = 30  # Max /analyze requests per window
    RATE_LIMIT_GENERAL: int = 120  # Max general requests per window
    RATE_LIMIT_WINDOW: int = 60  # Window size in seconds

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

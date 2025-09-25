"""
Application configuration management.

Loads environment variables, sets up app metadata, and exposes settings used across the app.
"""

from functools import lru_cache
from pydantic import Field, AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional


class Settings(BaseSettings):
    # PUBLIC_INTERFACE
    def app_metadata(self) -> dict:
        """Return application-level OpenAPI metadata with Ocean Professional theme variables included."""
        return {
            "title": self.APP_NAME,
            "description": self.APP_DESCRIPTION,
            "version": self.APP_VERSION,
            "contact": {"name": "Unified Connector Framework", "url": "https://example.com"},
            "license_info": {"name": "Proprietary"},
            "x-theme": {
                "name": "Ocean Professional",
                "primary": "#2563EB",
                "secondary": "#F59E0B", 
                "success": "#10B981",
                "error": "#EF4444",
                "gradient": "from-blue-500/10 to-gray-50",
                "background": "#f9fafb",
                "surface": "#ffffff",
                "text": "#111827"
            },
        }

    # App
    APP_NAME: str = Field(default="Unified Connector Backend")
    APP_DESCRIPTION: str = Field(
        default="Backend API for managing connectors, connections, unified envelope handling, and token/sync state."
    )
    APP_VERSION: str = Field(default="0.1.0")
    API_PREFIX: str = Field(default="/api")

    # CORS
    CORS_ALLOW_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    CORS_ALLOW_METHODS: List[str] = Field(default_factory=lambda: ["*"])
    CORS_ALLOW_HEADERS: List[str] = Field(default_factory=lambda: ["*"])

    # Database (MongoDB)
    MONGODB_URL: AnyUrl = Field(default="mongodb://localhost:27017")
    MONGODB_DB: str = Field(default="unified_connector")

    # Security/crypto
    ENCRYPTION_KEY: str = Field(
        default="",
        description="Base64 32-byte key for Fernet (must be provided in .env for prod)."
    )
    TOKEN_ENCRYPTION_ADDITIONAL_DATA: Optional[str] = Field(
        default=None,
        description="Optional associated data for AEAD contexts."
    )

    # JWT/auth (placeholder for future)
    AUTH_JWT_SECRET: str = Field(default="change-me-in-prod")
    AUTH_JWT_ALG: str = Field(default="HS256")

    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    LOG_JSON: bool = Field(default=False)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load and cache application settings."""
    return Settings()

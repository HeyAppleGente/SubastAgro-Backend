"""Configuración centralizada de SubastAgro mediante Pydantic Settings."""
import json
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración global del sistema con soporte para perfiles dev y prod."""

    APP_NAME: str = Field(default="SubastAgro API")
    APP_ENV: str = Field(default="development")
    APP_DEBUG: bool = Field(default=False)
    API_V1_PREFIX: str = "/api/v1"

    # Base de datos PostgreSQL
    DB_HOST: str = Field(default="localhost")
    DB_PORT: int = Field(default=5432)
    DB_NAME: str = Field(default="subastagro_db")
    DB_USER: str = Field(default="postgres")
    DB_PASSWORD: str = Field(default="postgres")
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/subastagro_db"
    )

    # Seguridad JWT & Cookies
    APP_JWT_SECRET: str = Field(
        default="subastagro_super_secret_jwt_key_2026_owasp_secure_token_prod"
    )
    APP_JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    APP_COOKIE_SECURE: bool = Field(default=False)
    APP_COOKIE_SAMESITE: str = Field(default="lax")

    # CORS
    APP_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"]
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator("APP_CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Parsea orígenes CORS desde JSON string o lista separada por comas."""
        if isinstance(v, str):
            v_strip = v.strip()
            if v_strip.startswith("["):
                return json.loads(v_strip)
            return [origin.strip() for origin in v_strip.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        """Indica si el entorno actual es producción."""
        return self.APP_ENV.lower() == "production"

    @property
    def cookie_secure(self) -> bool:
        """Garantiza Secure=True en producción y respeta configuración en desarrollo."""
        return True if self.is_production else self.APP_COOKIE_SECURE


settings = Settings()

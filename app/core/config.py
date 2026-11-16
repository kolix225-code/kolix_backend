from typing import Any, List, Literal, Union
from pydantic import AnyHttpUrl, EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Environnement
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    PROJECT_NAME: str = "Kolix Backend API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # Sécurité & JWT
    SECRET_KEY: str = "9a2b8e3d04cfb219e489c6d3fa716f9a08e1a681c3bcfa237e8db46324fa6821"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    OTP_EXPIRE_MINUTES: int = 5

    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://kolix.ci",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if v == "*":
                return ["*"]
            if not v.startswith("["):
                return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    # Base de données PostgreSQL (Support Supabase Transaction Pooler 6543 & Session Direct 5432)
    DATABASE_URL: str | None = None
    DIRECT_URL: str | None = None
    POSTGRES_SERVER: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "soum"
    POSTGRES_DB: str = "kolix_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_TIMEOUT_SECONDS: int = 30

    @staticmethod
    def _clean_async_url(raw_url: str) -> str:
        """Adapte et nettoie une URL PostgreSQL pour le driver asynchrone asyncpg."""
        url = raw_url.strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # asyncpg ne supporte pas le paramètre Prisma pgbouncer=true
        url = url.replace("?pgbouncer=true&", "?")
        url = url.replace("?pgbouncer=true", "")
        url = url.replace("&pgbouncer=true", "")

        # Normaliser sslmode vers ssl pour asyncpg
        url = url.replace("sslmode=require", "ssl=require")
        return url

    @staticmethod
    def _clean_sync_url(raw_url: str) -> str:
        """Adapte et nettoie une URL PostgreSQL pour le driver synchrone psycopg2."""
        url = raw_url.strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

        url = url.replace("?pgbouncer=true&", "?")
        url = url.replace("?pgbouncer=true", "")
        url = url.replace("&pgbouncer=true", "")
        return url

    @property
    def ASYNC_DATABASE_URI(self) -> str:
        """URI utilisée pour le runtime de l'application FastAPI (connectée au pooler de transaction 6543 si disponible)."""
        if self.DATABASE_URL:
            return self._clean_async_url(self.DATABASE_URL)
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def MIGRATION_DATABASE_URI(self) -> str:
        """URI utilisée pour les migrations Alembic (utilise DIRECT_URL session pooler 5432 si configuré pour les verrous DDL)."""
        target = self.DIRECT_URL or self.DATABASE_URL
        if target:
            return self._clean_async_url(target)
        return self.ASYNC_DATABASE_URI

    @property
    def SYNC_DATABASE_URI(self) -> str:
        target = self.DIRECT_URL or self.DATABASE_URL
        if target:
            return self._clean_sync_url(target)
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Cache & Queues Redis
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # S3 / MinIO Object Storage
    S3_ENDPOINT_URL: str | None = "http://127.0.0.1:9000"
    S3_ACCESS_KEY: str = "minio_kolix"
    S3_SECRET_KEY: str = "minio_kolix_secure_key"
    S3_BUCKET_NAME: str = "kolix-media"
    S3_REGION: str = "eu-west-3"
    S3_PUBLIC_DOMAIN: str = "http://127.0.0.1:9000/kolix-media"

    # WhatsApp Cloud API / Infobip
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v20.0"
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = "kolix_wa_webhook_verify_secret"

    # Passerelles de Paiement
    WAVE_API_KEY: str = ""
    WAVE_WEBHOOK_SECRET: str = ""
    ORANGE_MONEY_CLIENT_ID: str = ""
    ORANGE_MONEY_CLIENT_SECRET: str = ""

    # IA & LLM
    GEMINI_API_KEY: str = ""
    DEFAULT_LLM_MODEL: str = "gemini/gemini-1.5-flash"


settings = Settings()


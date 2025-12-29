"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="IdioRAG", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    environment: str = Field(default="development", description="Environment: development, staging, production")
    log_level: str = Field(default="INFO", description="Logging level")
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.strip("[]").replace('"', "").split(",")]
        return v

    # Database
    database_url: str = Field(
        ...,
        description="PostgreSQL connection string with asyncpg driver"
    )
    database_schema: str = Field(
        default="idiorag",
        description="Database schema for IdioRAG tables (isolates from main app tables)"
    )
    database_pool_size: int = Field(default=20, description="Database connection pool size")
    database_max_overflow: int = Field(default=10, description="Maximum connection overflow")

    # LLM
    llm_api_url: str = Field(..., description="External LLM API base URL")
    llm_model_name: str = Field(default="qwen3-14b", description="LLM model name")
    llm_api_key: str | None = Field(default=None, description="API key for LLM service")
    llm_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="LLM temperature")
    llm_max_tokens: int = Field(default=2048, gt=0, description="Maximum tokens for LLM response")
    llm_stop_sequences: List[str] = Field(
        default=["\n\nOkay,", "\n\nLet me", "\n\nWait,", "\n\nHowever,"],
        description="Stop sequences to prevent model rambling (model-specific)"
    )
    
    @field_validator("llm_stop_sequences", mode="before")
    @classmethod
    def parse_stop_sequences(cls, v: str | List[str]) -> List[str]:
        """Parse stop sequences from string or list."""
        if isinstance(v, str):
            if not v.strip():
                return []
            return [seq.strip() for seq in v.strip("[]").replace('"', "").split(",")]
        return v

    # JWT
    jwt_secret_key: str = Field(..., description="Secret key for JWT validation (HS256)")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm: HS256 or RS256")
    jwt_public_key: str | None = Field(
        default=None,
        description="Public key for JWT validation (RS256)"
    )

    # Embeddings & Chunking
    embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5",
        description="HuggingFace embedding model"
    )
    embedding_dimension: int = Field(
        default=384,
        description="Embedding vector dimension"
    )
    chunk_size: int = Field(default=512, gt=0, description="Default chunk size in tokens")
    chunk_overlap: int = Field(default=50, ge=0, description="Chunk overlap in tokens")

    # API Limits
    max_upload_size_mb: int = Field(default=10, gt=0, description="Maximum upload size in MB")

    @property
    def max_upload_size_bytes(self) -> int:
        """Convert max upload size to bytes."""
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings.
    
    Returns:
        Settings: Application configuration object
    """
    return Settings()

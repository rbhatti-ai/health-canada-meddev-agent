"""
Application settings and configuration management.
Uses pydantic-settings for type-safe environment variable loading.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM API Keys
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    # Embedding Configuration
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # Vector Store - ChromaDB (Local)
    chroma_persist_directory: str = "./data/vectorstore"
    chroma_collection_name: str = "health_canada_regulatory"

    # Vector Store - Pinecone (Production)
    pinecone_api_key: str | None = None
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "health-canada-meddev"

    # Database
    database_url: str | None = None
    redis_url: str = "redis://localhost:6379/0"

    # Supabase Configuration
    # Set these in .env or environment variables
    # Example: SUPABASE_URL=https://your-project-id.supabase.co
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None  # Server-side only, never expose to client

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    api_cors_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:8501"])

    # Application Settings
    log_level: str = "INFO"
    environment: str = "development"

    # RAG Settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5
    rerank_enabled: bool = True

    # Agent Settings
    default_llm_model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.1

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"

    @property
    def use_pinecone(self) -> bool:
        """Determine if Pinecone should be used (production) or ChromaDB (local)."""
        return self.is_production and self.pinecone_api_key is not None

    @property
    def supabase_configured(self) -> bool:
        """Check if Supabase credentials are configured."""
        return self.supabase_url is not None and self.supabase_anon_key is not None


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience export
settings = get_settings()

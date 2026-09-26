import os
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    app_name: str = "Healthcare Greenfield Enterprise RAG API"
    app_version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5433/healthcare_rag"

    # Vector Database
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "healthcare_chunks"

    # Embedding Service ("fastembed", "gemini", "openai", "mock")
    embedding_provider: str = "fastembed"
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dimension: int = 384

    # RAG Retrieval & Grounding
    rag_similarity_threshold: float = 0.65
    rag_top_k: int = 4

    # LLM Service
    llm_provider: str = "mock"  # "gemini" | "openai" | "mock"
    llm_api_key: str = ""
    llm_model: str = "gemini-1.5-flash"

    # CORS
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.cors_origins:
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()

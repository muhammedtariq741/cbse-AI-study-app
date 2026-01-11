"""
Application Configuration

Loads environment variables and provides typed configuration access.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Google Gemini API
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    
    # Google Cloud Platform (for Vertex AI tuning)
    gcp_project_id: Optional[str] = Field(None, description="GCP Project ID")
    gcp_location: str = Field("us-central1", description="GCP region")
    
    # Tuned Model (set after tuning)
    tuned_model_name: Optional[str] = Field(None, description="Tuned Gemini model name")
    
    # Application Settings
    debug: bool = Field(False, description="Debug mode")
    log_level: str = Field("INFO", description="Logging level")
    
    # Vector Store
    vector_store_path: str = Field("./data/embeddings", description="Path to vector store")
    faiss_index_name: str = Field("cbse_class9", description="FAISS index name")
    
    # API Settings
    api_host: str = Field("0.0.0.0", description="API host")
    api_port: int = Field(8000, description="API port")
    
    # Model Settings
    embedding_model: str = Field("text-embedding-004", description="Gemini embedding model")
    llm_model: str = Field("gemini-2.0-flash", description="Gemini LLM model")
    
    # Retrieval Settings
    retrieval_top_k: int = Field(5, description="Number of chunks to retrieve")
    chunk_size: int = Field(400, description="Target chunk size in tokens")
    chunk_overlap: int = Field(50, description="Chunk overlap in tokens")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Returns:
        Settings: Application configuration object
    """
    return Settings()


# Convenience accessor
settings = get_settings()

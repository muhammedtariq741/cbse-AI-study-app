"""
FastAPI Main Application

Entry point for the CBSE Study App backend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.api.routes import query, health
from app.config import settings


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("🚀 Starting CBSE Study App...")
    logger.info(f"📚 LLM Model: {settings.llm_model}")
    logger.info(f"🔍 Embedding Model: {settings.embedding_model}")
    
    if settings.tuned_model_name:
        logger.info(f"✨ Using tuned model: {settings.tuned_model_name}")
    else:
        logger.info("⚠️  No tuned model configured - using base model")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down CBSE Study App...")


# Create FastAPI app
app = FastAPI(
    title="CBSE Study App API",
    description="AI-powered study assistant for CBSE Class 9 students",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(query.router, prefix="/api/v1", tags=["Query"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "CBSE Study App API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }

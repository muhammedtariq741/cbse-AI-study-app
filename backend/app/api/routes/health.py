"""
Health Check Endpoint

Provides system health and readiness information.
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Health status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "cbse-study-app"
    }


@router.get("/health/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    Checks if all required services are available.
    
    Returns:
        dict: Readiness status with component checks
    """
    # TODO: Add actual checks for vector store, Gemini API, etc.
    checks = {
        "vector_store": True,  # Will check FAISS index
        "gemini_api": True,    # Will check API connectivity
        "tuned_model": True    # Will check if tuned model is available
    }
    
    all_ready = all(checks.values())
    
    return {
        "ready": all_ready,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }

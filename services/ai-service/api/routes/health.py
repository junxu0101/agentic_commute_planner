"""
Health check endpoints
"""

from fastapi import APIRouter
from typing import Dict, Any

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "service": "AI Service",
        "version": "1.0.0"
    }
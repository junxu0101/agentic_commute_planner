"""
FastAPI AI Service with Event-Driven Redis Architecture
Main application entry point
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config.settings import get_settings
from services.redis_service import RedisService
from workers.job_worker import JobWorker
from api.routes import health, jobs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global services
redis_service: RedisService = None
job_worker: JobWorker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global redis_service, job_worker
    
    settings = get_settings()
    
    # Initialize services
    logger.info("Initializing AI Service...")
    
    # Initialize Redis service
    redis_service = RedisService(settings.redis_url)
    await redis_service.connect()
    
    # Initialize and start job worker
    job_worker = JobWorker(redis_service)
    worker_task = asyncio.create_task(job_worker.start())
    
    logger.info("AI Service initialized successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down AI Service...")
    await job_worker.stop()
    worker_task.cancel()
    await redis_service.disconnect()
    logger.info("AI Service shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="Commute Planner AI Service",
        description="Multi-agent AI service for intelligent commute planning",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_headers=["*"],
        allow_methods=["*"],
    )
    
    # Include routers
    app.include_router(health.router, prefix="/health", tags=["health"])
    app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
    
    return app


# Create app instance
app = create_app()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Commute Planner AI Service",
        "status": "running",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )
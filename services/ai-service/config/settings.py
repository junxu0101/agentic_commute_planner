"""
Application settings and configuration
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Server settings
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    port: int = int(os.getenv("PORT", "8000"))
    
    # Database settings
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgres://commute_planner:dev_password@localhost:5432/commute_planner"
    )
    
    # Redis settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_job_queue: str = "commute_jobs"
    redis_progress_channel: str = "job_progress"
    
    # Backend service settings
    backend_service_url: str = os.getenv(
        "BACKEND_SERVICE_URL", 
        "http://localhost:8080/graphql"
    )
    
    # External API settings
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    google_maps_api_key: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")
    google_calendar_credentials_path: Optional[str] = os.getenv(
        "GOOGLE_CALENDAR_CREDENTIALS_PATH"
    )
    
    # Concurrency settings
    max_concurrent_jobs: int = int(os.getenv("MAX_CONCURRENT_JOBS", "5"))
    job_timeout_seconds: int = int(os.getenv("JOB_TIMEOUT_SECONDS", "300"))
    
    # LangGraph settings
    use_mock_tools: bool = os.getenv("USE_MOCK_TOOLS", "true").lower() == "true"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
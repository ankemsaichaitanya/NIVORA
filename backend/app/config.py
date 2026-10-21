import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CareLoop - Clinical Closed-Loop Tracking"
    # By default, use SQLite for zero-friction local development, or PostgreSQL if configured
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./careloop.db")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    SLA_ROUTINE_HOURS: int = 48
    SLA_URGENT_HOURS: int = 12

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()

"""
Basic configuration for FinFlow API.
Reads settings from .env file.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    PROJECT_NAME: str = "FinFlow API"
    ENVIRONMENT: str = "development"
    
    DATABASE_URL: str
    SECRET_KEY: str
    
    class Config:
        """Tell Pydantic to read from .env file."""
        env_file = ".env"

settings = Settings()


# Simple helper function
def is_development() -> bool:
    """Check if we're in development mode."""
    return settings.ENVIRONMENT == "development"
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    PROJECT_NAME: str = "FinFlow API"
    ENVIRONMENT: str = "development"
    
    DATABASE_URL: str
    SECRET_KEY: str
    
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()

def is_development() -> bool:
    """Check if we're in development mode."""
    return settings.ENVIRONMENT == "development"
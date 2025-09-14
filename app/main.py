from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config import settings
from app.database import create_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting FinFlow API...")
    try:
        create_tables()
        print("✅ Database tables created")
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    yield
    
    print("👋 Shutting down FinFlow API...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

@app.get("/")
async def root():
    """Home page - basic info about our API."""
    return {
        "message": "Welcome to FinFlow API! 💰",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    """Check if API is working."""
    return {
        "status": "healthy",
        "message": "FinFlow is running! 🎉"
    }
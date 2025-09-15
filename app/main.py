from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config import settings
from app.database import create_tables
from app.api.v1.users import router as users_router
from app.api.v1.auth import router as auth_router


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

app.include_router(users_router, prefix="/api/v1", tags=["users"])
app.include_router(auth_router, prefix="/api/v1", tags=["authentication"])

@app.get("/")
async def root():
    return {
        "message": "Welcome to FinFlow API! 💰",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "FinFlow is running! 🎉"
    }
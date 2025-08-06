# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import papers
from app.core.logging import setup_logging
from app.core.config import settings
from typing import Dict
import os

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="AI Preprint Forge",
    description="API for generating and managing research paper preprints",
    version="1.0.0"
)

# CORS settings - Use environment-based configuration
allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", tags=["system"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "AI Preprint Forge API",
        "version": "1.0.0"
    }

# Ready check endpoint
@app.get("/ready", tags=["system"])
async def ready_check() -> Dict[str, bool]:
    """Readiness check endpoint to verify all dependencies."""
    checks = {
        "api": True,
        "openai_configured": bool(settings.openai_api_key),
        "github_configured": bool(settings.github_token),
    }
    return {
        "ready": all(checks.values()),
        "checks": checks
    }

# Include routers
app.include_router(papers.router, prefix="/api/v1/papers", tags=["papers"])

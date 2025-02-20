# app/main.py
from fastapi import FastAPI
from app.api.routes import papers
from app.core.logging import setup_logging

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="AI Preprint Forge",
    description="API for generating and managing research paper preprints",
    version="1.0.0"
)

# Include routers
app.include_router(papers.router, prefix="/api/v1/papers", tags=["papers"])

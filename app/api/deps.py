# app/api/deps.py
from typing import Generator
from app.services.paper_generator import PaperGenerator

def get_paper_generator() -> Generator[PaperGenerator, None, None]:
    """Dependency to get a paper generator instance."""
    generator = PaperGenerator()
    try:
        yield generator
    finally:
        # Any cleanup if needed
        pass

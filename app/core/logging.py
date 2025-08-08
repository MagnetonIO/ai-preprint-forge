# app/core/logging.py
import logging
import sys
from pathlib import Path
from rich.logging import RichHandler
from typing import Optional
from app.core.config import settings


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with both file and console handlers."""
    # Create formatters
    console_formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Setup rich console handler
    console_handler = RichHandler(rich_tracebacks=True, markup=True, show_time=False)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Setup file handler if log file is provided
    handlers = [console_handler]
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        handlers.append(file_handler)

    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO, handlers=handlers, force=True
    )

    # Set specific log levels for some libraries
    if not verbose:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("github").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)

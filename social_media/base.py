from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

class SocialMediaPlatform(ABC):
    """Abstract base class for social media platform implementations."""

    def __init__(self):
        self.enabled = False
        self.configured = False

    @abstractmethod
    def setup(self) -> bool:
        """Initialize the platform connection. Return True if successful."""
        pass

    @abstractmethod
    def post(self, message: str) -> bool:
        """Post a message to the platform. Return True if successful."""
        pass

    def log_error(self, error: Exception, context: str):
        """Standardized error logging for social media operations."""
        logger.error(f"{self.__class__.__name__} {context}: {str(error)}")

import os
import time
import logging
from typing import List
from .base import SocialMediaPlatform
from .twitter import TwitterPlatform
from .linkedin import LinkedInPlatform
from .facebook import FacebookPlatform

logger = logging.getLogger(__name__)

class SocialMediaManager:
    """Manages multiple social media platform implementations."""

    def __init__(self):
        """Initialize all platform instances and check global enable flag."""
        self.enabled = os.getenv("ENABLE_SOCIAL_MEDIA", "false").lower() == "true"
        self.post_delay = int(os.getenv("SOCIAL_POST_DELAY", "300"))

        # Initialize all platforms
        self.platforms: List[SocialMediaPlatform] = []

        if self.enabled:
            # Only create platform instances if social media is globally enabled
            self.platforms.extend([
                TwitterPlatform(),
                LinkedInPlatform(),
                FacebookPlatform()
            ])
            # Set up enabled platforms
            self._setup_platforms()

    def _setup_platforms(self):
        """Initialize all enabled platforms."""
        for platform in self.platforms:
            if platform.enabled:
                platform.setup()

    def post_update(self, message: str) -> bool:
        """
        Post update to all configured platforms.
        Returns True if at least one platform succeeds.
        """
        if not self.enabled:
            logger.info("Social media posting is disabled")
            return False

        if not self.platforms:
            logger.warning("No social media platforms configured")
            return False

        success = False
        active_platforms = [p for p in self.platforms if p.enabled and p.configured]

        if not active_platforms:
            logger.warning("No active social media platforms found")
            return False

        for platform in active_platforms:
            try:
                if platform.post(message):
                    logger.info(f"Posted successfully to {platform.__class__.__name__}")
                    success = True
                if platform != active_platforms[-1]:  # Don't delay after last platform
                    time.sleep(self.post_delay)
            except Exception as e:
                logger.error(f"Error posting to {platform.__class__.__name__}: {str(e)}")

        return success

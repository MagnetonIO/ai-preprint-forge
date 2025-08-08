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

    def __init__(self) -> None:
        """Initialize platform instances based on configuration."""
        self.post_delay = int(os.getenv("SOCIAL_POST_DELAY", "300"))
        self.platforms: List[SocialMediaPlatform] = []

        # Initialize platforms if they're individually enabled
        # or if global social media is enabled
        global_enabled = os.getenv("ENABLE_SOCIAL_MEDIA", "false").lower() == "true"

        # Twitter
        if global_enabled or os.getenv("AUTO_POST_TWITTER", "false").lower() == "true":
            self.platforms.append(TwitterPlatform())

        # LinkedIn
        if global_enabled or os.getenv("AUTO_POST_LINKEDIN", "false").lower() == "true":
            self.platforms.append(LinkedInPlatform())

        # Facebook (checks its own FACEBOOK_POST_TO_PAGE setting)
        if (
            global_enabled
            or os.getenv("FACEBOOK_POST_TO_PAGE", "false").lower() == "true"
        ):
            self.platforms.append(FacebookPlatform())

        # Set up enabled platforms
        self._setup_platforms()

    def _setup_platforms(self) -> None:
        """Initialize all enabled platforms."""
        for platform in self.platforms:
            if platform.enabled:
                success = platform.setup()
                if not success:
                    logger.error(f"Failed to set up {platform.__class__.__name__}")

    def post_update(self, message: str) -> bool:
        """
        Post update to all configured platforms.
        Returns True if at least one platform succeeds.
        """
        if not self.platforms:
            logger.warning("No social media platforms configured")
            return False

        success = False
        active_platforms = [p for p in self.platforms if p.enabled and p.configured]

        if not active_platforms:
            logger.warning(
                "No active social media platforms found. Check your platform settings and tokens."
            )
            return False

        for platform in active_platforms:
            try:
                if platform.post(message):
                    logger.info(f"Posted successfully to {platform.__class__.__name__}")
                    success = True
                if platform != active_platforms[-1]:  # Don't delay after last platform
                    time.sleep(self.post_delay)
            except Exception as e:
                logger.error(
                    f"Error posting to {platform.__class__.__name__}: {str(e)}"
                )

        return success

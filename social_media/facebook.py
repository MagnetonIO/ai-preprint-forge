import os
import facebook
from .base import SocialMediaPlatform, logger

class FacebookPlatform(SocialMediaPlatform):
    """
    Facebook platform implementation supporting simultaneous personal and page posts.
    Can be configured to post to either or both based on environment settings.
    """
    def __init__(self):
        super().__init__()
        self.api_personal = None
        self.api_page = None
        self.page_id = os.getenv("FACEBOOK_PAGE_ID")

        # Separate flags for personal and page posting
        self.post_to_personal = os.getenv("FACEBOOK_POST_TO_PERSONAL", "false").lower() == "true"
        self.post_to_page = os.getenv("FACEBOOK_POST_TO_PAGE", "false").lower() == "true"

        # Platform is enabled if either posting type is enabled
        self.enabled = self.post_to_personal or self.post_to_page

    def setup(self) -> bool:
        """
        Initialize Facebook API connections for enabled posting types.
        Returns True if at least one posting type is successfully configured.
        """
        if not self.enabled:
            return False

        success = False

        # Setup personal posting if enabled
        if self.post_to_personal:
            try:
                user_token = os.getenv("FACEBOOK_USER_ACCESS_TOKEN")
                if not user_token:
                    logger.error("Personal posting enabled but no user access token provided")
                else:
                    self.api_personal = facebook.GraphAPI(user_token, version="3.1")
                    # Verify personal token
                    self.api_personal.get_object("me")
                    logger.info("Facebook personal posting configured successfully")
                    success = True
            except Exception as e:
                self.log_error(e, "personal profile setup failed")
                self.api_personal = None

        # Setup page posting if enabled
        if self.post_to_page:
            try:
                if not self.page_id:
                    logger.error("Page posting enabled but no page ID provided")
                else:
                    page_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
                    if not page_token:
                        logger.error("Page posting enabled but no page access token provided")
                    else:
                        self.api_page = facebook.GraphAPI(page_token, version="3.1")
                        # Verify page token
                        self.api_page.get_object(self.page_id)
                        logger.info(f"Facebook page posting configured successfully for page {self.page_id}")
                        success = True
            except Exception as e:
                self.log_error(e, "page setup failed")
                self.api_page = None

        # Platform is configured if at least one posting type works
        self.configured = success
        return success

    def post(self, message: str) -> bool:
        """
        Post content to configured Facebook destinations.
        Returns True if at least one post succeeds.
        """
        if not (self.enabled and self.configured):
            return False

        success = False

        # Post to personal profile if configured
        if self.post_to_personal and self.api_personal:
            try:
                self.api_personal.put_object("me", "feed", message=message)
                logger.info("Posted successfully to Facebook personal profile")
                success = True
            except Exception as e:
                self.log_error(e, "personal profile post failed")

        # Post to page if configured
        if self.post_to_page and self.api_page and self.page_id:
            try:
                self.api_page.put_object(self.page_id, "feed", message=message)
                logger.info(f"Posted successfully to Facebook page {self.page_id}")
                success = True
            except Exception as e:
                self.log_error(e, "page post failed")

        return success

import os
import time
import json
from pathlib import Path
import requests
from datetime import datetime, timedelta
from .base import SocialMediaPlatform, logger

class FacebookPlatform(SocialMediaPlatform):
    def __init__(self):
        super().__init__()
        self.access_token = None
        self.page_id = os.getenv("FACEBOOK_PAGE_ID")
        self.enabled = os.getenv("FACEBOOK_POST_TO_PAGE", "false").lower() == "true"

        # Token storage setup
        self.config_dir = Path(os.getenv("CONFIG_DIR", ".config"))
        self.token_file = self.config_dir / "fb_page_token.json"
        self.config_dir.mkdir(exist_ok=True)

    def _check_page_access(self, token: str) -> bool:
        """Check if we can access the page and its required permissions"""
        try:
            # Try to get basic page info
            url = f"https://graph.facebook.com/v22.0/{self.page_id}"
            logger.info(f"Checking page access with URL: {url}")

            response = requests.get(
                url,
                params={
                    "access_token": token,
                    "fields": "name,access_token"
                }
            )

            if not response.ok:
                logger.error(f"Page access failed with status {response.status_code}")
                logger.error(f"Error response: {response.text}")
                return False

            page_data = response.json()
            logger.info(f"Successfully accessed page: {page_data.get('name', 'UNKNOWN')}")
            return True

        except requests.RequestException as e:
            logger.error(f"Page access check failed: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                logger.error(f"Error details: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in page access check: {str(e)}")
            return False

    def setup(self) -> bool:
        """Initialize Facebook page posting"""
        if not self.enabled:
            logger.info("Facebook posting is not enabled")
            return False

        if not self.page_id:
            logger.error("Facebook Page ID not provided")
            return False

        try:
            # Get token from environment
            self.access_token = os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN")
            if not self.access_token:
                logger.error("No Facebook page token available")
                return False

            logger.info("Verifying Facebook page access...")
            if self._check_page_access(self.access_token):
                self.configured = True
                logger.info("Facebook page posting configured successfully")
                return True

            logger.error("Could not configure Facebook page posting - check permissions")
            return False

        except Exception as e:
            self.log_error(e, "setup failed")
            self.configured = False
            return False

    def post(self, message: str) -> bool:
        """Post content to Facebook page"""
        if not (self.enabled and self.configured):
            return False

        try:
            url = f"https://graph.facebook.com/v22.0/{self.page_id}/feed"
            logger.info(f"Posting to URL: {url}")  # Add logging to verify URL
            # For page posting, use data parameter instead of params
            response = requests.post(
                url,
                data={
                    "access_token": self.access_token,
                    "message": message
                }
            )

            if not response.ok:
                logger.error(f"Posting failed with status {response.status_code}")
                logger.error(f"Error response: {response.text}")
                return False

            result = response.json()
            logger.info(f"Posted successfully to Facebook page {self.page_id}")
            logger.info(f"Post result: {result}")
            return True

        except requests.RequestException as e:
            logger.error(f"Facebook API Error during posting: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                logger.error(f"Error details: {e.response.text}")
            return False
        except Exception as e:
            self.log_error(e, "page post failed")
            return False

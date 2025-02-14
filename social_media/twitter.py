import os
import tweepy
from .base import SocialMediaPlatform, logger

class TwitterPlatform(SocialMediaPlatform):
    def __init__(self):
        super().__init__()
        self.api = None
        self.enabled = os.getenv("AUTO_POST_TWITTER", "false").lower() == "true"

    def setup(self) -> bool:
        if not self.enabled:
            return False

        try:
            auth = tweepy.OAuthHandler(
                os.getenv("TWITTER_API_KEY"),
                os.getenv("TWITTER_API_SECRET")
            )
            auth.set_access_token(
                os.getenv("TWITTER_ACCESS_TOKEN"),
                os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
            )

            self.api = tweepy.API(auth)
            self.api.verify_credentials()
            self.configured = True
            logger.info("Twitter API configured successfully")
            return True

        except Exception as e:
            self.log_error(e, "setup failed")
            self.configured = False
            return False

    def post(self, message: str) -> bool:
        if not (self.enabled and self.configured):
            return False

        try:
            self.api.update_status(message)
            logger.info("Posted successfully to Twitter")
            return True

        except Exception as e:
            self.log_error(e, "post failed")
            return False

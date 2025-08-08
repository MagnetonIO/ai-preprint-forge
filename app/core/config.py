# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    # OpenAI settings
    openai_api_key: str
    openai_model: str = "gpt-4"

    # GitHub settings
    github_token: str
    github_username: str
    make_repo_public: bool = False
    enable_github_pages: bool = False

    # Base directory settings
    base_directory: Path = Path("ai_preprints")
    config_dir: Path = Path(".config")
    templates_directory: str = "templates"

    # Logging settings
    log_file: Optional[str] = None
    environment: str = "production"  # "production" or "development"

    # Paper generation settings
    create_markdown_by_default: bool = True
    create_latex_by_default: bool = True
    regenerate_existing_markdown: bool = False
    regenerate_existing_latex: bool = False
    paper_min_words: int = 2000
    paper_max_words: int = 5000
    include_citations: bool = True
    generate_figures: bool = True

    # Paper metadata defaults
    paper_author: Optional[str] = None
    paper_institution: Optional[str] = None
    paper_department: Optional[str] = None
    paper_email: Optional[str] = None

    # Domain settings
    use_custom_domain: bool = False
    custom_domain: Optional[str] = None

    # Social media settings
    enable_social_media: bool = False
    social_post_delay: int = 300
    auto_post_twitter: bool = False
    auto_post_linkedin: bool = False
    facebook_post_to_page: bool = False

    # Twitter settings
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_access_token: Optional[str] = None
    twitter_access_token_secret: Optional[str] = None

    # LinkedIn settings
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
    linkedin_access_token: Optional[str] = None

    # Facebook settings
    facebook_page_id: Optional[str] = None
    facebook_page_access_token: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields in .env file
    )


settings = Settings()

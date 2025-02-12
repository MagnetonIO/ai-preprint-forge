import typer
import os
import openai
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
import subprocess
import re
from pathlib import Path
from github import Github
import logging
from dotenv import load_dotenv
import jinja2
from pylatex import Document, Section, Subsection, Command
import shutil
from datetime import datetime
import tweepy
import time
from linkedin_api import Linkedin
import json
import facebook
from facebook import GraphAPI

# Initialize Typer app
app = typer.Typer(add_completion=False)

# Load environment variables and configure logging
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialMediaManager:
    def __init__(self):
        self.twitter_enabled = os.getenv("AUTO_POST_TWITTER", "false").lower() == "true"
        self.linkedin_enabled = os.getenv("AUTO_POST_LINKEDIN", "false").lower() == "true"
        self.facebook_enabled = os.getenv("AUTO_POST_FACEBOOK", "false").lower() == "true"
        self.post_delay = int(os.getenv("SOCIAL_POST_DELAY", "300"))

        if self.twitter_enabled:
            self.setup_twitter()
        if self.linkedin_enabled:
            self.setup_linkedin()
        if self.facebook_enabled:
            self.setup_facebook()

    def setup_twitter(self):
        """Setup Twitter client (placeholder)."""
        pass

    def setup_linkedin(self):
        """Setup LinkedIn client (placeholder)."""
        pass

    def setup_facebook(self):
        """Setup Facebook client (placeholder)."""
        pass

    def post_to_twitter(self, message: str):
        """Post message to Twitter (placeholder)."""
        pass

    def post_to_linkedin(self, message: str):
        """Post message to LinkedIn (placeholder)."""
        pass

    def post_to_facebook(self, message: str):
        """Post message to Facebook (placeholder)."""
        pass

class AIPreprintGenerator:
    def __init__(self):
        # Configure OpenAI
        if not openai.api_key:
            logger.warning("OpenAI API key not found in environment variables.")

        # Initialize GitHub client
        self.github_client = Github(os.getenv("GITHUB_TOKEN"))

        # Model and base directory
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.base_dir = Path(os.getenv("BASE_DIRECTORY", "ai_preprints"))
        self.base_dir.mkdir(exist_ok=True)

        # Social media manager
        self.social_media = SocialMediaManager() if os.getenv("ENABLE_SOCIAL_MEDIA", "false").lower() == "true" else None

    def generate_paper(self, prompt: str, setup_pages: bool = False, post_social: bool = False):
        """Main method to generate the paper and handle all related tasks"""
        try:
            # Generate paper content using OpenAI
            paper_content = self._generate_content(prompt)

            # Create project directory and files
            project_dir, paper_name = self._setup_project(prompt, paper_content)

            # Initialize git repository and push to GitHub
            repo_url = self._setup_github_repo(project_dir, paper_name)

            # Setup GitHub Pages if requested
            if setup_pages:
                self._setup_github_pages(project_dir)

            # Handle social media posting if enabled
            if post_social and self.social_media:
                self._handle_social_media(prompt, paper_name, repo_url)

            return {
                'paper_name': paper_name,
                'repo_url': repo_url,
                'project_dir': project_dir
            }

        except Exception as e:
            logger.error(f"Error generating paper: {e}")
            raise

    def _generate_content(self, prompt: str) -> str:
        """
        Use OpenAI's ChatCompletion to generate paper content.
        Adjust parameters (max_tokens, temperature, etc.) as needed.
        """
        try:
            logger.info("Generating content from OpenAI...")
            response = client.chat.completions.create(model=self.model,
            messages=[
                {"role": "system", "content": "You are an AI writing a research paper."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7)
            generated_text = response.choices[0].message.content.strip()
            logger.info("Content generation complete.")
            return generated_text
        except Exception as e:
            logger.error(f"Error generating content with OpenAI: {e}")
            raise

    def _setup_project(self, prompt: str, paper_content: str):
        """
        Create a local project directory for the paper and store the generated content.
        Return a tuple of (project_dir, paper_name).
        """
        # Convert prompt to a sanitized directory name
        paper_name = re.sub(r'\W+', '_', prompt).strip("_")
        if not paper_name:
            paper_name = f"Paper_{int(time.time())}"

        project_dir = self.base_dir / paper_name
        project_dir.mkdir(exist_ok=True)

        # Example: Create a simple Markdown or TeX file to store content
        paper_file = project_dir / "paper.md"
        with paper_file.open("w", encoding="utf-8") as f:
            f.write(paper_content)

        logger.info(f"Project setup complete at {project_dir}")
        return project_dir, paper_name

    def _setup_github_repo(self, project_dir: Path, paper_name: str):
        """
        Create a GitHub repo, initialize a local git repo, commit, and push.
        Return the repository URL.
        """
        try:
            # Create GitHub repo
            logger.info(f"Creating GitHub repository: {paper_name}")
            user = self.github_client.get_user()
            repo = user.create_repo(paper_name, private=True)  # or public depending on your preference
            repo_url = repo.clone_url
            logger.info(f"Repository created at {repo_url}")

            # Initialize local git repo
            subprocess.run(["git", "init"], cwd=project_dir, check=True)
            subprocess.run(["git", "add", "."], cwd=project_dir, check=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=project_dir, check=True)
            subprocess.run(["git", "branch", "-M", "main"], cwd=project_dir, check=True)
            subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=project_dir, check=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], cwd=project_dir, check=True)

            return repo.html_url

        except Exception as e:
            logger.error(f"Error setting up GitHub repo: {e}")
            # Return a fallback or raise the error
            raise

    def _setup_github_pages(self, project_dir: Path):
        """
        Setup GitHub Pages for the newly created repository.
        This typically involves creating a gh-pages branch or enabling Pages in repo settings.
        """
        try:
            logger.info("Setting up GitHub Pages (placeholder).")
            # Example: you could check out a new gh-pages branch and push
            # subprocess.run(["git", "checkout", "--orphan", "gh-pages"], cwd=project_dir, check=True)
            # ... add an index.html or similar ...
            # subprocess.run(["git", "push", "origin", "gh-pages"], cwd=project_dir, check=True)
            pass
        except Exception as e:
            logger.error(f"Error setting up GitHub Pages: {e}")
            raise

    def _handle_social_media(self, prompt: str, paper_name: str, repo_url: str):
        """
        Post details about the new paper to enabled social media platforms.
        """
        message = f"New AI-generated paper '{paper_name}' is now available! Check it out: {repo_url}"
        logger.info("Posting to social media...")
        try:
            if self.social_media.twitter_enabled:
                self.social_media.post_to_twitter(message)
                time.sleep(self.social_media.post_delay)

            if self.social_media.linkedin_enabled:
                self.social_media.post_to_linkedin(message)
                time.sleep(self.social_media.post_delay)

            if self.social_media.facebook_enabled:
                self.social_media.post_to_facebook(message)
                time.sleep(self.social_media.post_delay)

            logger.info("Social media posts complete.")

        except Exception as e:
            logger.error(f"Error posting to social media: {e}")

def run_generation(prompt: str, setup_pages: bool, post_social: bool):
    """Main function to handle the paper generation process"""
    try:
        generator = AIPreprintGenerator()
        result = generator.generate_paper(prompt, setup_pages, post_social)

        logger.info(f"Successfully created paper '{result['paper_name']}' at {result['repo_url']}")
        logger.info(f"Local directory: {result['project_dir']}")

        return result

    except Exception as e:
        logger.error(f"Error in generation process: {e}")
        raise typer.Exit(1)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Callback to handle default command"""
    if ctx.invoked_subcommand is None:
        ctx.invoke(generate)

@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Research prompt to generate paper from"),
    setup_pages: bool = typer.Option(False, "--pages/--no-pages", help="Setup GitHub Pages website"),
    post_social: bool = typer.Option(False, "--social/--no-social", help="Post to social media")
):
    """Generate research paper and create GitHub repository"""
    # Get values from environment if not provided via command line
    setup_pages = setup_pages if setup_pages is not None else os.getenv("ENABLE_GITHUB_PAGES", "false").lower() == "true"
    post_social = post_social if post_social is not None else os.getenv("ENABLE_SOCIAL_MEDIA", "false").lower() == "true"

    return run_generation(prompt, setup_pages, post_social)

@app.command()
def configure():
    """Configure the AI Preprint Generator settings"""
    # Add interactive configuration logic here if needed
    pass

if __name__ == "__main__":
    app()

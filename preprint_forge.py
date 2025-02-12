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
import shutil
from datetime import datetime
import time

# Initialize Typer app
app = typer.Typer(add_completion=False)

# Load environment variables and configure logging
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SocialMediaManager:
    """Placeholder class; fill in actual social media logic if needed."""
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
        pass

    def setup_linkedin(self):
        pass

    def setup_facebook(self):
        pass

    def post_to_twitter(self, message: str):
        pass

    def post_to_linkedin(self, message: str):
        pass

    def post_to_facebook(self, message: str):
        pass

class AIPreprintGenerator:
    def __init__(self):
        # Check OpenAI API key
        if not openai.api_key:
            logger.warning("OpenAI API key not found in environment variables.")

        # Initialize GitHub client
        self.github_client = Github(os.getenv("GITHUB_TOKEN"))

        # Model and base directory
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.base_dir = Path(os.getenv("BASE_DIRECTORY", "ai_preprints"))
        self.base_dir.mkdir(exist_ok=True)

        # Social media manager
        self.social_media = (
            SocialMediaManager()
            if os.getenv("ENABLE_SOCIAL_MEDIA", "false").lower() == "true"
            else None
        )

    def generate_paper(self,
                       prompt: str,
                       setup_pages: bool = False,
                       post_social: bool = False,
                       create_markdown: bool = True,
                       create_latex: bool = True,
                       author: str = "",
                       institution: str = "",
                       department: str = "",
                       email: str = "",
                       date_str: str = ""):
        """
        Main method to generate the paper and handle all related tasks.
        Defaults to creating BOTH Markdown and LaTeX versions,
        attempts PDF compilation if LaTeX is created,
        and creates a README unless one exists.
        """
        try:
            # Generate textual content with OpenAI in Markdown
            paper_content_md = (
                self._generate_content(
                    prompt,
                    output_format="markdown",
                    author=author,
                    institution=institution,
                    department=department,
                    email=email,
                    date_str=date_str
                ) if create_markdown else None
            )

            # Generate LaTeX content
            paper_content_latex = (
                self._generate_content(
                    prompt,
                    output_format="latex",
                    author=author,
                    institution=institution,
                    department=department,
                    email=email,
                    date_str=date_str
                ) if create_latex else None
            )

            # Create project directory and files
            project_dir, paper_name = self._setup_project(
                prompt,
                md_content=paper_content_md,
                latex_content=paper_content_latex
            )

            # If LaTeX was generated, attempt to compile PDF
            if create_latex and paper_content_latex:
                self._generate_pdf_from_latex(project_dir, paper_name)

            # Create a README unless it already exists
            self._create_readme_if_missing(project_dir, prompt)

            # Initialize or update git repository on GitHub (with AI-generated description)
            repo_url = self._setup_github_repo(project_dir, paper_name, prompt)

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

    def _generate_content(self,
                          prompt: str,
                          output_format: str = "markdown",
                          author: str = "",
                          institution: str = "",
                          department: str = "",
                          email: str = "",
                          date_str: str = "") -> str:
        """
        Use OpenAI's ChatCompletion to generate content.

        For LaTeX, produce an arXiv-like document style that compiles under pdfTeX.
        Include a title/author/date block:
            \\title{...}
            \\author{Author \\ Department \\ Institution \\ Email}
            \\date{...}

        For Markdown, produce a structured doc with frontmatter:
            # Title
            **Author**: ...
            **Institution**: ...
            **Department**: ...
            **Email**: ...
            **Date**: ...

        Do not include disclaimers or references to GPT/ChatGPT.
        """
        try:
            logger.info(f"Generating {output_format} content from OpenAI...")

            system_instruction = (
                "You are an AI that writes research papers in a concise, coherent style. "
                "Do not include any disclaimers or references to GPT in the output."
            )

            if output_format == "latex":
                # Instruct GPT to produce a LaTeX doc with user-specified frontmatter
                user_instruction = (
                    "Generate a well-formatted LaTeX document for a research paper based on:\n"
                    f"{prompt}\n\n"
                    "Use an arXiv-like style that compiles under pdfTeX.\n"
                    "At the top of the document, please include:\n"
                    "\\documentclass{article}\n"
                    "\\usepackage[margin=1in]{geometry}\n"
                    "\\usepackage{amsmath,amssymb,graphicx}\n"
                    f"\\title{{A Short Descriptive Title}}\n"
                    f"\\author{{{author} \\\\ {department} \\\\ {institution} \\\\ {email}}}\n"
                    f"\\date{{{date_str}}}\n\n"
                    "Then add standard sections: Abstract, Introduction, Methods, Results, Conclusion.\n"
                    "Do not reference GPT or disclaimers in the text. Output only valid LaTeX."
                )
            else:
                # Markdown version with a heading block
                user_instruction = (
                    "Generate a structured Markdown research paper based on:\n"
                    f"{prompt}\n\n"
                    "At the top, include a title and author block:\n"
                    "# A Short Descriptive Title\n"
                    f"**Author**: {author}\n"
                    f"**Department**: {department}\n"
                    f"**Institution**: {institution}\n"
                    f"**Email**: {email}\n"
                    f"**Date**: {date_str}\n\n"
                    "Then include standard sections: Abstract, Introduction, Methods, Results, Conclusion.\n"
                    "Do not reference GPT or disclaimers. Return only valid Markdown."
                )

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_instruction}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            generated_text = response.choices[0].message.content.strip()

            # Remove any markdown code fences (```...```)
            generated_text = re.sub(r'```[^\n]*\n?', '', generated_text)

            logger.info("Content generation complete.")
            return generated_text

        except Exception as e:
            logger.error(f"Error generating content with OpenAI: {e}")
            raise

    def _setup_project(self,
                       prompt: str,
                       md_content: str = None,
                       latex_content: str = None):
        """
        Create a local project directory for the paper and store generated content.
        Uses the same base `paper_name` for the folder and for both .md and .tex.
        Returns (project_dir, paper_name).
        """
        # Create a filesystem-friendly paper name
        paper_name = re.sub(r'\W+', '_', prompt).strip("_")
        if not paper_name:
            paper_name = f"Paper_{int(time.time())}"

        project_dir = self.base_dir / paper_name
        project_dir.mkdir(exist_ok=True)

        # Save Markdown content (if any)
        if md_content:
            md_file = project_dir / f"{paper_name}.md"
            md_file.write_text(md_content, encoding="utf-8")
            logger.info(f"Markdown file created at {md_file}")

        # Save LaTeX content (if any)
        if latex_content:
            tex_file = project_dir / f"{paper_name}.tex"
            tex_file.write_text(latex_content, encoding="utf-8")
            logger.info(f"LaTeX file created at {tex_file}")

        return project_dir, paper_name

    def _generate_pdf_from_latex(self, project_dir: Path, paper_name: str):
        """
        Compile the LaTeX file to PDF using pdflatex or latexmk.
        """
        try:
            logger.info("Compiling LaTeX to PDF...")
            tex_file = project_dir / f"{paper_name}.tex"
            if not tex_file.exists():
                logger.warning(f"{paper_name}.tex not found; skipping PDF generation.")
                return

            subprocess.run(["pdflatex", f"{paper_name}.tex"], cwd=project_dir, check=True)
            # Optionally run again to fix cross-references, etc.
            subprocess.run(["pdflatex", f"{paper_name}.tex"], cwd=project_dir, check=True)
            logger.info("PDF generation complete.")

        except Exception as e:
            logger.error(f"Error generating PDF from LaTeX: {e}")

    def _create_readme_if_missing(self, project_dir: Path, prompt: str):
        """
        Generate a README.md based on the research prompt,
        unless README.md already exists.
        """
        readme_file = project_dir / "README.md"
        if readme_file.exists():
            logger.info("README.md already exists; skipping creation.")
            return

        logger.info("Generating new README.md...")
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Write a concise README for a research project. No disclaimers."},
                    {
                        "role": "user",
                        "content": (
                            f"Based on the research prompt below, produce a short summary for a README:\n\n{prompt}\n\n"
                            "Include an overview, main sections, and what the repo contains. "
                            "Do not include disclaimers or references to GPT or ChatGPT."
                        )
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )
            readme_text = response.choices[0].message.content.strip()

            readme_file.write_text(readme_text, encoding="utf-8")
            logger.info(f"README.md created at {readme_file}")

        except Exception as e:
            logger.error(f"Error generating README: {e}")

    def _generate_repo_description(self, prompt: str) -> str:
        """
        Generate a short (~250 characters) AI-generated GitHub repo description
        based on the provided prompt. No disclaimers or GPT references.
        """
        try:
            system_instruction = (
                "You are an AI that writes concise text. "
                "Do not include disclaimers or references to ChatGPT."
            )
            user_instruction = (
                "Generate a short description (max 250 characters) for a GitHub repository "
                f"about a research paper based on the prompt:\n\n{prompt}\n\n"
                "Do not exceed 250 characters. No GPT disclaimers."
            )

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_instruction}
                ],
                max_tokens=200,
                temperature=0.7
            )
            about_text = response.choices[0].message.content.strip()
            # Ensure we don't exceed 250 chars
            about_text = about_text[:250]
            return about_text

        except Exception as e:
            logger.error(f"Error generating repo description: {e}")
            # Fallback if GPT fails
            return "AI-generated research paper repository"

    def _setup_github_repo(self, project_dir: Path, paper_name: str, prompt: str):
        """
        Check if GitHub repo with paper_name exists:
          - If it does, do NOT create a new one, just push changes.
          - Otherwise, create a new repo (public or private based on .env).
          - Add an AI-generated short 'about' description (max 250 chars).
        Returns the repository URL.
        """
        logger.info(f"Checking/Creating GitHub repository: {paper_name}")
        user = self.github_client.get_user()

        existing_repo = None
        for repo in user.get_repos():
            if repo.name.lower() == paper_name.lower():
                existing_repo = repo
                break

        if existing_repo:
            logger.info(f"Repo '{paper_name}' already exists. Skipping creation...")
            repo_url = existing_repo.clone_url
            self._commit_and_push(project_dir, repo_url, update_only=True)
            return existing_repo.html_url
        else:
            try:
                # Determine if the repository should be public or private (default: private)
                make_repo_public = os.getenv("MAKE_REPO_PUBLIC", "false").lower() == "true"
                about_section = self._generate_repo_description(prompt)

                repo = user.create_repo(
                    paper_name,
                    private=not make_repo_public,
                    description=about_section
                )
                repo_url = repo.clone_url
                logger.info(
                    f"Repository created at {repo_url} "
                    f"({'public' if make_repo_public else 'private'})"
                )
                self._commit_and_push(project_dir, repo_url, update_only=False)
                return repo.html_url

            except Exception as e:
                logger.error(f"Error creating GitHub repo: {e}")
                raise

    def _commit_and_push(self, project_dir: Path, repo_url: str, update_only: bool = False):
        """
        Handles local Git operations. If 'update_only' is True, we assume
        a local .git folder might already exist. If not, we initialize it.
        """
        try:
            git_folder = project_dir / ".git"
            if not git_folder.exists():
                logger.info("No local .git found; initializing...")
                subprocess.run(["git", "init"], cwd=project_dir, check=True)
                subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=project_dir, check=True)
                subprocess.run(["git", "checkout", "-b", "main"], cwd=project_dir, check=True)

            subprocess.run(["git", "add", "."], cwd=project_dir, check=True)
            commit_msg = "Update existing files" if update_only else "Initial commit"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=project_dir, check=True)
            subprocess.run(["git", "branch", "-M", "main"], cwd=project_dir, check=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], cwd=project_dir, check=True)
            logger.info("Changes pushed to GitHub successfully.")

        except Exception as e:
            logger.error(f"Error during commit/push steps: {e}")
            raise

    def _setup_github_pages(self, project_dir: Path):
        """
        Setup GitHub Pages for the newly created repository (placeholder).
        """
        try:
            logger.info("Setting up GitHub Pages (placeholder).")
            # Example steps:
            # subprocess.run(["git", "checkout", "--orphan", "gh-pages"], cwd=project_dir, check=True)
            # subprocess.run(["git", "push", "origin", "gh-pages"], cwd=project_dir, check=True)
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

def run_generation(prompt: str,
                   setup_pages: bool,
                   post_social: bool,
                   create_markdown: bool,
                   create_latex: bool,
                   author: str,
                   institution: str,
                   department: str,
                   email: str,
                   date_str: str):
    """
    Main function to handle the paper generation process.
    Grabs any missing info from environment variables as fallback.
    """
    # Fallback to .env if not provided
    if not author:
        author = os.getenv("PAPER_AUTHOR", "")
    if not institution:
        institution = os.getenv("PAPER_INSTITUTION", "")
    if not department:
        department = os.getenv("PAPER_DEPARTMENT", "")
    if not email:
        email = os.getenv("PAPER_EMAIL", "")
    if not date_str:
        # default to today's date if none specified
        date_str = os.getenv("PAPER_DATE", datetime.now().strftime("%B %d, %Y"))

    try:
        generator = AIPreprintGenerator()
        result = generator.generate_paper(
            prompt,
            setup_pages=setup_pages,
            post_social=post_social,
            create_markdown=create_markdown,
            create_latex=create_latex,
            author=author,
            institution=institution,
            department=department,
            email=email,
            date_str=date_str
        )

        logger.info(f"Successfully created paper '{result['paper_name']}' at {result['repo_url']}")
        logger.info(f"Local directory: {result['project_dir']}")

        return result

    except Exception as e:
        logger.error(f"Error in generation process: {e}")
        raise typer.Exit(1)

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """Callback to handle the default command."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(generate)

@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Research prompt to generate paper from"),
    setup_pages: bool = typer.Option(False, "--pages/--no-pages", help="Setup GitHub Pages website"),
    post_social: bool = typer.Option(False, "--social/--no-social", help="Post to social media"),
    create_markdown: bool = typer.Option(None, "--md/--no-md", help="Generate Markdown version"),
    create_latex: bool = typer.Option(None, "--latex/--no-latex", help="Generate LaTeX version"),
    author: str = typer.Option(None, "--author", help="Paper author name"),
    institution: str = typer.Option(None, "--institution", help="Author institution"),
    department: str = typer.Option(None, "--department", help="Author department"),
    email: str = typer.Option(None, "--email", help="Author email"),
    date_str: str = typer.Option(None, "--date", help="Date to show on the paper")
):
    """
    Generate a research paper and create/update a GitHub repository.
    By default, both Markdown and LaTeX are generated (via .env settings),
    with PDF compiled from LaTeX in an arXiv style, with no GPT disclaimers.

    You can specify:
    --author, --institution, --department, --email, --date
    either via CLI or use .env fallback.
    """
    # Environment-based defaults for Markdown/LaTeX toggles
    if create_markdown is None:
        create_markdown = os.getenv("CREATE_MARKDOWN_BY_DEFAULT", "true").lower() == "true"
    if create_latex is None:
        create_latex = os.getenv("CREATE_LATEX_BY_DEFAULT", "true").lower() == "true"

    setup_pages = setup_pages if setup_pages is not None else os.getenv("ENABLE_GITHUB_PAGES", "false").lower() == "true"
    post_social = post_social if post_social is not None else os.getenv("ENABLE_SOCIAL_MEDIA", "false").lower() == "true"

    run_generation(
        prompt=prompt,
        setup_pages=setup_pages,
        post_social=post_social,
        create_markdown=create_markdown,
        create_latex=create_latex,
        author=author,
        institution=institution,
        department=department,
        email=email,
        date_str=date_str
    )

@app.command()
def configure():
    """
    Configure the AI Preprint Generator settings (placeholder).
    """
    pass

if __name__ == "__main__":
    app()

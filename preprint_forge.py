import typer
import os
import openai
from openai import OpenAI
import subprocess
import re
from pathlib import Path
from github import Github
import logging
from dotenv import load_dotenv
from datetime import datetime
import time
import asyncio
import json
import hashlib
from typing import Optional
from social_media import SocialMediaManager

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))

# Initialize Typer app
app = typer.Typer(add_completion=False)

# Load environment variables and configure logging
load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NameTracker:
    """Handles tracking and reusing paper/repository names based on prompts."""
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.name_cache_file = base_dir / "name_cache.json"
        self.prompt_to_name = self._load_cache()

    def _load_cache(self) -> dict:
        """Load existing name mappings from cache file."""
        try:
            if self.name_cache_file.exists():
                with open(self.name_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading name cache: {e}")
            return {}

    def _save_cache(self):
        """Save current name mappings to cache file."""
        try:
            with open(self.name_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompt_to_name, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving name cache: {e}")

    def _generate_prompt_key(self, prompt: str) -> str:
        """Generate a stable key for a prompt."""
        cleaned_prompt = re.sub(r'\s+', ' ', prompt.strip().lower())
        return hashlib.md5(cleaned_prompt.encode('utf-8')).hexdigest()

    def get_existing_name(self, prompt: str) -> Optional[str]:
        """Get existing name for a prompt if it exists."""
        prompt_key = self._generate_prompt_key(prompt)
        return self.prompt_to_name.get(prompt_key)

    def store_name(self, prompt: str, name: str):
        """Store a new prompt-name mapping."""
        prompt_key = self._generate_prompt_key(prompt)
        self.prompt_to_name[prompt_key] = name
        self._save_cache()

    def has_name(self, prompt: str) -> bool:
        """Check if a name exists for this prompt."""
        return self._generate_prompt_key(prompt) in self.prompt_to_name

async def generate_paper_name(client, prompt: str) -> str:
    """Generate a concise, filesystem-friendly paper name."""
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": (
                    "Generate a concise, meaningful name for a research paper. "
                    "Use only letters, numbers, and underscores. "
                    "Maximum 30 characters. No spaces. "
                    "Format: word1_word2_word3"
                )},
                {"role": "user", "content": f"Research topic: {prompt}"}
            ],
            max_tokens=50,
            temperature=0.7
        )

        paper_name = response.choices[0].message.content.strip()
        paper_name = clean_name(paper_name)
        return paper_name

    except Exception as e:
        logger.error(f"Error generating paper name with AI: {e}")
        return create_fallback_name(prompt)

def clean_name(name: str) -> str:
    """Clean and format a name to be filesystem-friendly and under 30 chars."""
    clean = re.sub(r'[^\w\s]', '', name)
    clean = clean.replace(' ', '_').lower()
    clean = re.sub(r'_+', '_', clean)

    if len(clean) > 30:
        last_underscore = clean.rfind('_', 0, 30)
        if last_underscore != -1:
            clean = clean[:last_underscore]
        else:
            clean = clean[:30]

    clean = clean.rstrip('_')
    return clean

def create_fallback_name(prompt: str) -> str:
    """Create a fallback name if AI generation fails."""
    fallback = clean_name(prompt)[:25]
    timestamp = str(int(time.time()))[-4:]
    final_name = f"{fallback}_{timestamp}"
    if len(final_name) > 30:
        final_name = f"{fallback[:25]}_{timestamp}"
    return final_name

class AIPreprintGenerator:
    def __init__(self):
        if not openai.api_key:
            logger.warning("OpenAI API key not found in environment variables.")

        self.client = client
        self.github_client = Github(os.getenv("GITHUB_TOKEN"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.base_dir = Path(os.getenv("BASE_DIRECTORY", "ai_preprints"))
        self.base_dir.mkdir(exist_ok=True)

        # Initialize name tracker
        self.name_tracker = NameTracker(self.base_dir)

        self.social_media = (
            SocialMediaManager()
            if os.getenv("ENABLE_SOCIAL_MEDIA", "false").lower() == "true"
            else None
        )

    async def generate_paper(self,
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
        """Main method to generate the paper and handle all related tasks."""
        try:
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

            project_dir, paper_name = await self._setup_project(
                prompt,
                md_content=paper_content_md,
                latex_content=paper_content_latex
            )

            if create_latex and paper_content_latex:
                self._generate_pdf_from_latex(project_dir, paper_name)

            self._create_readme_if_missing(project_dir, prompt)

            repo_url = self._setup_github_repo(project_dir, paper_name, prompt)

            if setup_pages:
                self._setup_github_pages(project_dir)

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
        """Generate content using OpenAI."""
        try:
            logger.info(f"Generating {output_format} content from OpenAI...")

            system_instruction = (
                "You are an AI that writes research papers in a concise, coherent style. "
                "Do not include any disclaimers or references to GPT in the output."
            )

            if output_format == "latex":
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
            generated_text = re.sub(r'```[^\n]*\n?', '', generated_text)

            logger.info("Content generation complete.")
            return generated_text

        except Exception as e:
            logger.error(f"Error generating content with OpenAI: {e}")
            raise

    async def _setup_project(self, prompt: str, md_content: str = None, latex_content: str = None):
        """Create or update project directory using tracked names."""
        # Get existing name or generate new one
        existing_name = self.name_tracker.get_existing_name(prompt)
        if existing_name:
            logger.info(f"Reusing existing name: {existing_name}")
            paper_name = existing_name
        else:
            paper_name = await generate_paper_name(self.client, prompt)
            self.name_tracker.store_name(prompt, paper_name)
            logger.info(f"Generated new name: {paper_name}")

        project_dir = self.base_dir / paper_name
        project_dir.mkdir(exist_ok=True)

        if md_content:
            md_file = project_dir / f"{paper_name}.md"
            md_file.write_text(md_content, encoding="utf-8")
            logger.info(f"Updated Markdown file at {md_file}")

        if latex_content:
            tex_file = project_dir / f"{paper_name}.tex"
            tex_file.write_text(latex_content, encoding="utf-8")
            logger.info(f"Updated LaTeX file at {tex_file}")

        return project_dir, paper_name

    def _generate_pdf_from_latex(self, project_dir: Path, paper_name: str):
        """Compile LaTeX to PDF."""
        try:
            logger.info("Compiling LaTeX to PDF...")
            tex_file = project_dir / f"{paper_name}.tex"
            if not tex_file.exists():
                logger.warning(f"{paper_name}.tex not found; skipping PDF generation.")
                return

            subprocess.run(["pdflatex", f"{paper_name}.tex"], cwd=project_dir, check=True)
            subprocess.run(["pdflatex", f"{paper_name}.tex"], cwd=project_dir, check=True)
            logger.info("PDF generation complete.")

        except Exception as e:
            logger.error(f"Error generating PDF from LaTeX: {e}")

    def _create_readme_if_missing(self, project_dir: Path, prompt: str):
        """Generate README.md if it doesn't exist."""
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

    def _setup_github_repo(self, project_dir: Path, paper_name: str, prompt: str):
        """Setup or update GitHub repository."""
        logger.info(f"Checking/Creating GitHub repository: {paper_name}")
        user = self.github_client.get_user()

        existing_repo = None
        try:
            existing_repo = user.get_repo(paper_name)
        except:
            for repo in user.get_repos():
                if repo.name.lower() == paper_name.lower():
                    existing_repo = repo
                    break

        if existing_repo:
            logger.info(f"Updating existing repo: {paper_name}")
            repo_url = existing_repo.clone_url
            self._commit_and_push(project_dir, repo_url, update_only=True)
            return existing_repo.html_url
        else:
            try:
                make_repo_public = os.getenv("MAKE_REPO_PUBLIC", "false").lower() == "true"
                about_section = self._generate_repo_description(prompt)

                repo = user.create_repo(
                    paper_name,
                    private=not make_repo_public,
                    description=about_section
                )
                repo_url = repo.clone_url
                logger.info(f"Created new repo: {paper_name}")
                self._commit_and_push(project_dir, repo_url, update_only=False)
                return repo.html_url

            except Exception as e:
                logger.error(f"Error creating GitHub repo: {e}")
                raise

    def _commit_and_push(self, project_dir: Path, repo_url: str, update_only: bool = False):
        """Handle Git operations for new or existing repos."""
        try:
            git_folder = project_dir / ".git"
            if not git_folder.exists():
                logger.info("Initializing new Git repository...")
                subprocess.run(["git", "init"], cwd=project_dir, check=True)
                subprocess.run(["git", "remote", "add", "origin", repo_url], cwd=project_dir, check=True)
                subprocess.run(["git", "checkout", "-b", "main"], cwd=project_dir, check=True)

            subprocess.run(["git", "add", "."], cwd=project_dir, check=True)
            commit_msg = "Update content" if update_only else "Initial commit"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=project_dir, check=True)
            subprocess.run(["git", "branch", "-M", "main"], cwd=project_dir, check=True)
            subprocess.run(["git", "push", "-u", "origin", "main"], cwd=project_dir, check=True)
            logger.info("Git push successful")

        except Exception as e:
            logger.error(f"Error in Git operations: {e}")
            raise

    def _generate_repo_description(self, prompt: str) -> str:
        """Generate short GitHub repo description."""
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
            about_text = response.choices[0].message.content.strip()[:250]
            return about_text

        except Exception as e:
            logger.error(f"Error generating repo description: {e}")
            return "AI-generated research paper repository"

    def _setup_github_pages(self, project_dir: Path):
        """Setup GitHub Pages for the repository."""
        try:
            logger.info("Setting up GitHub Pages...")
            # Add GitHub Pages setup logic here
            pass
        except Exception as e:
            logger.error(f"Error setting up GitHub Pages: {e}")
            raise

    def _handle_social_media(self, prompt: str, paper_name: str, repo_url: str):
        """Post to social media platforms."""
        if not self.social_media:
            return

        message = f"New AI-generated paper '{paper_name}' is now available! Check it out: {repo_url}"
        logger.info("Posting to social media...")
        try:
            self.social_media.post_update(message)
            logger.info("Social media posts complete.")
        except Exception as e:
            logger.error(f"Error posting to social media: {e}")

async def run_generation(prompt: str,
                       setup_pages: bool,
                       post_social: bool,
                       create_markdown: bool,
                       create_latex: bool,
                       author: str,
                       institution: str,
                       department: str,
                       email: str,
                       date_str: str):
    """Main function to handle the paper generation process."""
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
        date_str = os.getenv("PAPER_DATE", datetime.now().strftime("%B %d, %Y"))

    try:
        generator = AIPreprintGenerator()
        result = await generator.generate_paper(
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
    """Generate a research paper and create/update a GitHub repository."""
    # Environment-based defaults for Markdown/LaTeX toggles
    if create_markdown is None:
        create_markdown = os.getenv("CREATE_MARKDOWN_BY_DEFAULT", "true").lower() == "true"
    if create_latex is None:
        create_latex = os.getenv("CREATE_LATEX_BY_DEFAULT", "true").lower() == "true"

    setup_pages = setup_pages if setup_pages is not None else os.getenv("ENABLE_GITHUB_PAGES", "false").lower() == "true"
    post_social = post_social if post_social is not None else os.getenv("ENABLE_SOCIAL_MEDIA", "false").lower() == "true"

    # Run the async function using asyncio
    asyncio.run(run_generation(
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
    ))

@app.command()
def configure():
    """Configure the AI Preprint Generator settings."""
    pass

if __name__ == "__main__":
    app()

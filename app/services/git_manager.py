# app/services/git_manager.py
from pathlib import Path
import subprocess
import logging
from github import Github
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class GitManager:
    """Manages Git and GitHub operations for paper repositories."""

    def __init__(self):
        self.github_client = Github(settings.github_token)
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.make_repo_public = settings.make_repo_public
        self.user = self.github_client.get_user()

    async def setup_repo(self, project_dir: Path, paper_name: str, prompt: str) -> str:
        """Setup or update GitHub repository."""
        logger.info(f"Checking/Creating GitHub repository: {paper_name}")

        try:
            # Ensure .gitignore exists
            await self._ensure_gitignore(project_dir)

            # Create README if it doesn't exist
            await self._create_readme_if_missing(project_dir, prompt)

            # Check for existing repo
            existing_repo = None
            try:
                existing_repo = self.user.get_repo(paper_name)
            except:
                for repo in self.user.get_repos():
                    if repo.name.lower() == paper_name.lower():
                        existing_repo = repo
                        break

            if existing_repo:
                logger.info(f"Updating existing repo: {paper_name}")
                repo_url = existing_repo.clone_url
                await self._commit_and_push(project_dir, repo_url, update_only=True)
                return existing_repo.html_url
            else:
                return await self._create_new_repo(project_dir, paper_name, prompt)

        except Exception as e:
            logger.error(f"Error in setup_repo: {e}")
            raise

    async def _create_new_repo(
        self, project_dir: Path, paper_name: str, prompt: str
    ) -> str:
        """Create a new GitHub repository."""
        try:
            description = await self._generate_repo_description(prompt)

            # Ensure description is no longer than 100 characters
            if len(description) > 100:
                description = description[:97] + "..."

            repo = self.user.create_repo(
                paper_name, private=not self.make_repo_public, description=description
            )
            repo_url = repo.clone_url
            logger.info(f"Created new repo: {paper_name}")

            await self._commit_and_push(project_dir, repo_url, update_only=False)
            return repo.html_url

        except Exception as e:
            logger.error(f"Error creating GitHub repo: {e}")
            raise

    async def _create_readme_if_missing(self, project_dir: Path, prompt: str) -> None:
        """Generate README.md if it doesn't exist."""
        readme_file = project_dir / "README.md"
        if readme_file.exists():
            logger.info("README.md already exists; skipping creation.")
            return

        logger.info("Generating new README.md...")
        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Write a professional README for a research paper repository. "
                            "Include sections: Overview, Methodology, Key Findings, "
                            "and How to Cite. Be concise and informative."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Write a README for a research paper about: {prompt}",
                    },
                ],
                max_tokens=500,
                temperature=0.7,
            )

            readme_content = response.choices[0].message.content.strip()
            readme_file.write_text(readme_content, encoding="utf-8")
            logger.info(f"Created README.md at {readme_file}")

        except Exception as e:
            logger.error(f"Error generating README: {e}")
            raise

    async def _generate_repo_description(self, prompt: str) -> str:
        """Generate a short GitHub repo description (max 100 chars)."""
        try:
            response = await self.openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Generate a very short, clear description (max 90 characters) "
                            "for a GitHub repository about a research paper."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Generate a description for research about: {prompt}",
                    },
                ],
                max_tokens=50,
                temperature=0.7,
            )

            description = response.choices[0].message.content.strip()
            # Ensure we stay well under the 100 char limit even if AI generates longer
            return description[:90]

        except Exception as e:
            logger.error(f"Error generating repo description: {e}")
            return "AI-generated research paper repository"

    async def _ensure_gitignore(self, project_dir: Path) -> None:
        """Create .gitignore if it doesn't exist."""
        gitignore_path = project_dir / ".gitignore"
        if not gitignore_path.exists():
            logger.info("Creating .gitignore...")
            gitignore_content = """# LaTeX
*.aux
*.log
*.out
*.toc
*.fls
*.fdb_latexmk
*.synctex.gz
*.bbl
*.blg

# Keep these files
!*.tex
!*.md
!*.pdf
!README.md
"""
            gitignore_path.write_text(gitignore_content)
            logger.info("Created .gitignore")

    async def _commit_and_push(
        self, project_dir: Path, repo_url: str, update_only: bool = False
    ) -> None:
        """Handle Git operations for new or existing repos."""
        try:
            git_folder = project_dir / ".git"
            if not git_folder.exists():
                logger.info("Initializing new Git repository...")
                subprocess.run(["git", "init"], cwd=project_dir, check=True)
                subprocess.run(
                    ["git", "remote", "add", "origin", repo_url],
                    cwd=project_dir,
                    check=True,
                )
                subprocess.run(
                    ["git", "checkout", "-b", "main"], cwd=project_dir, check=True
                )

            # Ensure .gitignore is properly configured
            await self._ensure_gitignore(project_dir)

            # Add all tracked files
            subprocess.run(["git", "add", "-A"], cwd=project_dir, check=True)

            commit_msg = "Update content" if update_only else "Initial commit"
            subprocess.run(
                ["git", "commit", "-m", commit_msg], cwd=project_dir, check=True
            )
            subprocess.run(["git", "branch", "-M", "main"], cwd=project_dir, check=True)
            subprocess.run(
                ["git", "push", "-u", "origin", "main"], cwd=project_dir, check=True
            )
            logger.info("Git push successful")

        except Exception as e:
            logger.error(f"Error in Git operations: {e}")
            raise

    async def setup_github_pages(self, project_dir: Path) -> None:
        """Setup GitHub Pages for the repository."""
        try:
            logger.info("Setting up GitHub Pages...")
            # Add GitHub Pages setup logic here
            # This would typically involve:
            # 1. Creating gh-pages branch
            # 2. Setting up Jekyll or other static site generator
            # 3. Configuring GitHub Pages settings via API
            pass

        except Exception as e:
            logger.error(f"Error setting up GitHub Pages: {e}")
            raise

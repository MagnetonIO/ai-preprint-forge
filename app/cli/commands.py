# app/cli/commands.py

import typer
import asyncio
from typing import Optional
from datetime import datetime
from pathlib import Path
from github import Github
import shutil
import logging
from app.services.paper_generator import PaperGenerator
from app.core.config import settings
from app.core.logging import setup_logging

app = typer.Typer(help="AI Preprint Forge - Generate and manage research papers")
logger = logging.getLogger(__name__)

@app.callback()
def callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    env: str = typer.Option(
        "production",
        "--env",
        "-e",
        help="Environment (production/development)"
    ),
):
    """Setup global CLI options."""
    settings.environment = env
    setup_logging(verbose or env == "development")

@app.command()
def generate(
    prompt: str = typer.Argument(..., help="Research prompt to generate paper from"),
    setup_pages: bool = typer.Option(
        False, "--pages/--no-pages", help="Setup GitHub Pages website"
    ),
    post_social: bool = typer.Option(
        False, "--social/--no-social", help="Post to social media"
    ),
    create_markdown: bool = typer.Option(
        None, "--md/--no-md", help="Generate Markdown version"
    ),
    create_latex: bool = typer.Option(
        None, "--latex/--no-latex", help="Generate LaTeX version"
    ),
    regenerate_markdown: bool = typer.Option(
        None, "--regenerate-md/--keep-md", help="Regenerate existing Markdown file if it exists"
    ),
    regenerate_latex: bool = typer.Option(
        None, "--regenerate-latex/--keep-latex", help="Regenerate existing LaTeX file if it exists"
    ),
    author: Optional[str] = typer.Option(None, "--author", help="Paper author name"),
    institution: Optional[str] = typer.Option(None, "--institution", help="Author institution"),
    department: Optional[str] = typer.Option(None, "--department", help="Author department"),
    email: Optional[str] = typer.Option(None, "--email", help="Author email"),
    date_str: Optional[str] = typer.Option(None, "--date", help="Date to show on the paper"),
):
    """Generate a research paper and create/update a GitHub repository."""
    try:
        create_markdown = create_markdown if create_markdown is not None else settings.create_markdown_by_default
        create_latex = create_latex if create_latex is not None else settings.create_latex_by_default

        author = author or settings.paper_author or ""
        institution = institution or settings.paper_institution or ""
        department = department or settings.paper_department or ""
        email = email or settings.paper_email or ""
        date_str = date_str or datetime.now().strftime("%B %d, %Y")

        logger.debug("Configuration:")
        logger.debug(f"- Environment: {settings.environment}")
        logger.debug(f"- Author: {author}")
        logger.debug(f"- Institution: {institution}")
        logger.debug(f"- Department: {department}")
        logger.debug(f"- Create Markdown: {create_markdown}")
        logger.debug(f"- Create LaTeX: {create_latex}")

        logger.info("🚀 Generating paper from prompt: %s", prompt)

        generator = PaperGenerator()
        result = asyncio.run(generator.generate_paper(
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

        logger.info("\n✨ Paper generation complete!")
        logger.info("📄 Paper Name: %s", result['paper_name'])
        logger.info("🔗 Repository URL: %s", result['repo_url'])
        logger.info("📁 Local Directory: %s", result['project_dir'])

    except Exception as e:
        logger.error("❌ Error: %s", str(e), exc_info=settings.environment == "development")
        raise typer.Exit(1)

@app.command()
def delete(
    paper_name: str = typer.Argument(..., help="Name of the paper to delete"),
    delete_repo: bool = typer.Option(
        False, "--delete-repo", help="Also delete the GitHub repository"
    ),
    force: bool = typer.Option(
        False, "--force", "-f", help="Force deletion without confirmation"
    ),
):
    """Delete a paper's local directory and optionally its GitHub repository."""
    local_deleted = False
    repo_deleted = False

    try:
        project_dir = Path(settings.base_directory) / paper_name

        # Handle local directory deletion
        if project_dir.exists():
            if not force:
                confirm = typer.confirm(
                    f"Are you sure you want to delete local directory {paper_name}?",
                    default=False
                )
                if not confirm:
                    logger.info("Local directory deletion cancelled.")
                else:
                    shutil.rmtree(project_dir)
                    logger.info(f"Deleted local directory: {project_dir}")
                    local_deleted = True
            else:
                shutil.rmtree(project_dir)
                logger.info(f"Deleted local directory: {project_dir}")
                local_deleted = True
        else:
            logger.warning(f"Local directory not found: {project_dir}")

        # Handle GitHub repo deletion
        if delete_repo or (not local_deleted and not project_dir.exists()):
            try:
                github_client = Github(settings.github_token)
                user = github_client.get_user()
                try:
                    repo = user.get_repo(paper_name)
                    if not force:
                        confirm = typer.confirm(
                            f"Are you sure you want to delete the GitHub repository {paper_name}?",
                            default=False
                        )
                        if not confirm:
                            logger.info("Repository deletion cancelled.")
                        else:
                            repo.delete()
                            logger.info(f"Deleted GitHub repository: {paper_name}")
                            repo_deleted = True
                    else:
                        repo.delete()
                        logger.info(f"Deleted GitHub repository: {paper_name}")
                        repo_deleted = True
                except:
                    logger.warning(f"GitHub repository not found: {paper_name}")
            except Exception as e:
                logger.error(f"Error deleting GitHub repository: {e}")
                if not local_deleted:
                    raise typer.Exit(1)

        # Final status
        if not local_deleted and not repo_deleted:
            logger.error(f"Nothing was deleted for {paper_name}")
            raise typer.Exit(1)

    except Exception as e:
        logger.error(f"Error during deletion: {e}")
        raise typer.Exit(1)

@app.command()
def list(
    show_github: bool = typer.Option(True, "--github/--no-github", help="Show GitHub repository status"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed information"),
):
    """List all managed papers."""
    try:
        base_dir = Path(settings.base_directory)
        if not base_dir.exists():
            logger.error(f"Base directory not found: {base_dir}")
            raise typer.Exit(1)

        # Get local papers
        papers = []
        for paper_dir in base_dir.iterdir():
            if paper_dir.is_dir():
                paper_info = {
                    "name": paper_dir.name,
                    "local_path": str(paper_dir),
                    "has_md": (paper_dir / f"{paper_dir.name}.md").exists(),
                    "has_tex": (paper_dir / f"{paper_dir.name}.tex").exists(),
                    "has_pdf": (paper_dir / f"{paper_dir.name}.pdf").exists(),
                    "github_url": None,
                    "github_status": None
                }
                papers.append(paper_info)

        # Check GitHub status if requested
        if show_github:
            try:
                github_client = Github(settings.github_token)
                user = github_client.get_user()
                for paper in papers:
                    try:
                        repo = user.get_repo(paper["name"])
                        paper["github_url"] = repo.html_url
                        paper["github_status"] = "active"
                    except:
                        paper["github_status"] = "not found"
            except Exception as e:
                logger.error(f"Error checking GitHub status: {e}")

        # Display results
        if not papers:
            logger.info("No papers found.")
            return

        logger.info("\nManaged Papers:")
        for paper in papers:
            if verbose:
                logger.info(f"\n📄 {paper['name']}")
                logger.info(f"  Local Path: {paper['local_path']}")
                logger.info(f"  Files: " +
                          f"{'MD ' if paper['has_md'] else ''}" +
                          f"{'TEX ' if paper['has_tex'] else ''}" +
                          f"{'PDF ' if paper['has_pdf'] else ''}")
                if show_github:
                    status = paper['github_status'] or 'unknown'
                    logger.info(f"  GitHub: {status}")
                    if paper['github_url']:
                        logger.info(f"  URL: {paper['github_url']}")
            else:
                status = f" ({paper['github_status']})" if show_github and paper['github_status'] else ""
                logger.info(f"📄 {paper['name']}{status}")

    except Exception as e:
        logger.error(f"Error listing papers: {e}")
        raise typer.Exit(1)

@app.command()
def server(
    host: str = typer.Option("0.0.0.0", help="Host to bind the server to"),
    port: int = typer.Option(8000, help="Port to bind the server to"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development")
):
    """Start the FastAPI server."""
    import uvicorn
    logger.info("🚀 Starting server on %s:%d", host, port)
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload
    )

@app.command()
def configure():
    """Configure the AI Preprint Generator settings."""
    logger.info("⚙️ Configuration wizard not yet implemented")
    logger.info("📝 Please edit your .env file directly")

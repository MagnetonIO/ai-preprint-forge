# app/api/routes/papers.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from pathlib import Path
from github import Github
import shutil
from app.services.paper_generator import PaperGenerator
from app.core.config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class PaperRequest(BaseModel):
    prompt: str
    setup_pages: bool = False
    post_social: bool = False
    create_markdown: Optional[bool] = None
    create_latex: Optional[bool] = None
    regenerate_markdown: Optional[bool] = None
    regenerate_latex: Optional[bool] = None
    author: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    email: Optional[str] = None
    date_str: Optional[str] = None

class PaperResponse(BaseModel):
    paper_name: str
    repo_url: str
    project_dir: str

class PaperInfo(BaseModel):
    name: str
    local_path: str
    has_md: bool
    has_tex: bool
    has_pdf: bool
    github_url: Optional[str] = None
    github_status: Optional[str] = None

class PaperList(BaseModel):
    papers: List[PaperInfo]
    total: int

@router.get("/", response_model=PaperList)
async def list_papers(show_github: bool = True):
    """List all managed papers."""
    try:
        base_dir = Path(settings.base_directory)
        if not base_dir.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Base directory not found: {base_dir}"
            )

        # Get local papers
        papers = []
        for paper_dir in base_dir.iterdir():
            if paper_dir.is_dir():
                paper_info = PaperInfo(
                    name=paper_dir.name,
                    local_path=str(paper_dir),
                    has_md=(paper_dir / f"{paper_dir.name}.md").exists(),
                    has_tex=(paper_dir / f"{paper_dir.name}.tex").exists(),
                    has_pdf=(paper_dir / f"{paper_dir.name}.pdf").exists(),
                    github_url=None,
                    github_status=None
                )
                papers.append(paper_info)

        # Check GitHub status if requested
        if show_github:
            try:
                github_client = Github(settings.github_token)
                user = github_client.get_user()
                for paper in papers:
                    try:
                        repo = user.get_repo(paper.name)
                        paper.github_url = repo.html_url
                        paper.github_status = "active"
                    except:
                        paper.github_status = "not found"
            except Exception as e:
                logger.error(f"Error checking GitHub status: {e}")

        return PaperList(papers=papers, total=len(papers))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error listing papers: {str(e)}"
        )

@router.post("/", response_model=PaperResponse)
async def generate_paper(request: PaperRequest):
    """Generate a new research paper."""
    try:
        # Set defaults from settings if not provided
        create_markdown = request.create_markdown if request.create_markdown is not None else settings.create_markdown_by_default
        create_latex = request.create_latex if request.create_latex is not None else settings.create_latex_by_default
        regenerate_markdown = request.regenerate_markdown if request.regenerate_markdown is not None else settings.regenerate_existing_markdown
        regenerate_latex = request.regenerate_latex if request.regenerate_latex is not None else settings.regenerate_existing_latex

        # Use defaults from settings for metadata if not provided
        author = request.author or settings.paper_author or ""
        institution = request.institution or settings.paper_institution or ""
        department = request.department or settings.paper_department or ""
        email = request.email or settings.paper_email or ""
        date_str = request.date_str or datetime.now().strftime("%B %d, %Y")

        generator = PaperGenerator()
        result = await generator.generate_paper(
            prompt=request.prompt,
            setup_pages=request.setup_pages,
            post_social=request.post_social,
            create_markdown=create_markdown,
            create_latex=create_latex,
            author=author,
            institution=institution,
            department=department,
            email=email,
            date_str=date_str
        )

        return PaperResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{paper_name}")
async def delete_paper(
    paper_name: str,
    delete_repo: bool = True,
    force: bool = False
):
    """Delete a paper's local directory and optionally its GitHub repository."""
    local_deleted = False
    repo_deleted = False

    try:
        project_dir = Path(settings.base_directory) / paper_name

        # Handle local directory deletion
        if project_dir.exists():
            try:
                shutil.rmtree(project_dir)
                logger.info(f"Deleted local directory: {project_dir}")
                local_deleted = True
            except Exception as e:
                logger.error(f"Error deleting local directory: {e}")
                if not force:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error deleting local directory: {str(e)}"
                    )
        else:
            logger.warning(f"Local directory not found: {project_dir}")

        # Handle GitHub repo deletion
        if delete_repo or (not local_deleted and not project_dir.exists()):
            try:
                github_client = Github(settings.github_token)
                user = github_client.get_user()
                try:
                    repo = user.get_repo(paper_name)
                    repo.delete()
                    logger.info(f"Deleted GitHub repository: {paper_name}")
                    repo_deleted = True
                except:
                    logger.warning(f"GitHub repository not found: {paper_name}")
            except Exception as e:
                logger.error(f"Error deleting GitHub repository: {e}")
                if not local_deleted and not force:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error deleting GitHub repository: {str(e)}"
                    )

        if not local_deleted and not repo_deleted:
            raise HTTPException(
                status_code=404,
                detail=f"Nothing was found to delete for {paper_name}"
            )

        return {
            "message": f"Successfully deleted paper: {paper_name}",
            "local_deleted": local_deleted,
            "repo_deleted": repo_deleted
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error during deletion: {str(e)}"
        )

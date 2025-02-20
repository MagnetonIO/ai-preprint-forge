# app/services/paper_generator.py
from pathlib import Path
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from app.core.config import settings
from app.services.name_tracker import NameTracker
from app.services.git_manager import GitManager
from app.services.social_media import SocialMediaManager
from app.utils.latex import generate_pdf_from_latex
import logging

logger = logging.getLogger(__name__)

class PaperGenerator:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.base_dir = Path(settings.base_directory)
        self.base_dir.mkdir(exist_ok=True)

        self.name_tracker = NameTracker(self.base_dir)
        self.git_manager = GitManager()
        self.social_media = (
            SocialMediaManager() if settings.enable_social_media else None
        )

    async def generate_content(
        self,
        prompt: str,
        output_format: str = "markdown",
        author: str = "",
        institution: str = "",
        department: str = "",
        email: str = "",
        date_str: str = "",
    ) -> str:
        """Generate paper content using OpenAI."""
        try:
            system_instruction = (
                "You are an AI that writes research papers in a concise, coherent style. "
                "Do not include any disclaimers or references to GPT in the output."
            )

            user_instruction = self._create_user_instruction(
                prompt,
                output_format,
                author,
                institution,
                department,
                email,
                date_str
            )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_instruction},
                ],
                max_tokens=2000,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise

    def _create_user_instruction(
        self,
        prompt: str,
        output_format: str,
        author: str,
        institution: str,
        department: str,
        email: str,
        date_str: str,
    ) -> str:
        """Create the user instruction based on format and metadata."""
        if output_format == "latex":
            return (
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
            return (
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

    async def generate_paper(
        self,
        prompt: str,
        setup_pages: bool = False,
        post_social: bool = False,
        create_markdown: bool = True,
        create_latex: bool = True,
        author: str = "",
        institution: str = "",
        department: str = "",
        email: str = "",
        date_str: str = "",
    ) -> Dict[str, Any]:
        """Main method to generate the paper and handle all related tasks."""
        try:
            # Generate content if requested
            md_content = await self.generate_content(
                prompt, "markdown",
                author, institution, department, email, date_str
            ) if create_markdown else None

            latex_content = await self.generate_content(
                prompt, "latex",
                author, institution, department, email, date_str
            ) if create_latex else None

            # Set up project and files
            project_dir, paper_name = await self.name_tracker.setup_project(
                prompt=prompt,
                md_content=md_content,
                latex_content=latex_content,
                regenerate_markdown=settings.regenerate_existing_markdown,
                regenerate_latex=settings.regenerate_existing_latex
            )

            # Generate PDF if LaTeX was created
            if latex_content:
                generate_pdf_from_latex(project_dir, paper_name)

            # Handle repository
            repo_url = await self.git_manager.setup_repo(
                project_dir, paper_name, prompt
            )

            # Handle GitHub Pages if requested
            if setup_pages:
                await self.git_manager.setup_github_pages(project_dir)

            # Handle social media if requested
            if post_social and self.social_media:
                await self.social_media.post_update(
                    f"New AI-generated paper '{paper_name}' is now available! "
                    f"Check it out: {repo_url}"
                )

            return {
                "paper_name": paper_name,
                "repo_url": repo_url,
                "project_dir": str(project_dir)
            }

        except Exception as e:
            logger.error(f"Error in paper generation: {e}")
            raise

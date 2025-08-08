# app/services/name_tracker.py
from pathlib import Path
import json
import re
import hashlib
import logging
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class NameTracker:
    """Handles tracking and reusing paper/repository names based on prompts."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.name_cache_file = base_dir / "name_cache.json"
        self.prompt_to_name: dict[str, str] = self._load_cache()

    def _load_cache(self) -> dict[str, str]:
        """Load existing name mappings from cache file."""
        try:
            if self.name_cache_file.exists():
                with open(self.name_cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading name cache: {e}")
            return {}

    def _save_cache(self) -> None:
        """Save current name mappings to cache file."""
        try:
            with open(self.name_cache_file, "w", encoding="utf-8") as f:
                json.dump(self.prompt_to_name, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving name cache: {e}")

    def _generate_prompt_key(self, prompt: str) -> str:
        """Generate a stable key for a prompt."""
        cleaned_prompt = re.sub(r"\s+", " ", prompt.strip().lower())
        return hashlib.md5(cleaned_prompt.encode("utf-8")).hexdigest()

    async def generate_paper_name(self, prompt: str) -> str:
        """Generate a concise, filesystem-friendly paper name."""
        try:
            # For now, create a simple name from the prompt
            # This could be enhanced to use AI for better name generation
            clean = re.sub(r"[^\w\s]", "", prompt)
            clean = clean.replace(" ", "_").lower()
            clean = re.sub(r"_+", "_", clean)

            if len(clean) > 30:
                last_underscore = clean.rfind("_", 0, 30)
                if last_underscore != -1:
                    clean = clean[:last_underscore]
                else:
                    clean = clean[:30]

            clean = clean.rstrip("_")

            # Add timestamp to ensure uniqueness
            timestamp = datetime.now().strftime("%y%m%d")
            final_name = f"{clean}_{timestamp}"

            return final_name

        except Exception as e:
            logger.error(f"Error generating paper name: {e}")
            raise

    def get_existing_name(self, prompt: str) -> Optional[str]:
        """Get existing name for a prompt if it exists."""
        prompt_key = self._generate_prompt_key(prompt)
        return self.prompt_to_name.get(prompt_key)

    def store_name(self, prompt: str, name: str) -> None:
        """Store a new prompt-name mapping."""
        prompt_key = self._generate_prompt_key(prompt)
        self.prompt_to_name[prompt_key] = name
        self._save_cache()

    def has_name(self, prompt: str) -> bool:
        """Check if a name exists for this prompt."""
        return self._generate_prompt_key(prompt) in self.prompt_to_name

    async def setup_project(
        self,
        prompt: str,
        md_content: Optional[str] = None,
        latex_content: Optional[str] = None,
        regenerate_markdown: bool = False,
        regenerate_latex: bool = False,
    ) -> Tuple[Path, str]:
        """Create or update project directory using tracked names."""
        try:
            # Get existing name or generate new one
            existing_name = self.get_existing_name(prompt)
            if existing_name:
                logger.info(f"Reusing existing name: {existing_name}")
                paper_name = existing_name
            else:
                paper_name = await self.generate_paper_name(prompt)
                self.store_name(prompt, paper_name)
                logger.info(f"Generated new name: {paper_name}")

            project_dir = self.base_dir / paper_name
            project_dir.mkdir(exist_ok=True)

            # Handle Markdown file
            if md_content:
                md_file = project_dir / f"{paper_name}.md"
                if md_file.exists():
                    if regenerate_markdown:
                        logger.info(f"Regenerating existing Markdown file at {md_file}")
                        md_file.write_text(md_content, encoding="utf-8")
                    else:
                        logger.info(f"Keeping existing Markdown file at {md_file}")
                else:
                    md_file.write_text(md_content, encoding="utf-8")
                    logger.info(f"Created new Markdown file at {md_file}")

            # Handle LaTeX file
            if latex_content:
                tex_file = project_dir / f"{paper_name}.tex"
                if tex_file.exists():
                    if regenerate_latex:
                        logger.info(f"Regenerating existing LaTeX file at {tex_file}")
                        tex_file.write_text(latex_content, encoding="utf-8")
                    else:
                        logger.info(f"Keeping existing LaTeX file at {tex_file}")
                else:
                    tex_file.write_text(latex_content, encoding="utf-8")
                    logger.info(f"Created new LaTeX file at {tex_file}")

            return project_dir, paper_name

        except Exception as e:
            logger.error(f"Error in setup_project: {e}")
            raise

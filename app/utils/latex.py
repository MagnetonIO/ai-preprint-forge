# app/utils/latex.py
import subprocess
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

LATEX_PREAMBLE = """\\documentclass{article}
\\usepackage[margin=1in]{geometry}
\\usepackage{amsmath,amssymb,graphicx}
\\usepackage[T1]{fontenc}
\\usepackage[utf8]{inputenc}
\\usepackage{lmodern}
\\usepackage{textcomp}
\\usepackage{lastpage}
"""


def generate_pdf_from_latex(project_dir: Path, paper_name: str) -> bool:
    """
    Convert LaTeX content to PDF using pdflatex.
    Returns True if successful, False otherwise.
    """
    try:
        logger.info("Generating PDF...")
        tex_file = project_dir / f"{paper_name}.tex"

        if not tex_file.exists():
            logger.warning(f"{paper_name}.tex not found; skipping PDF generation.")
            return False

        # Read the original content
        content = tex_file.read_text(encoding="utf-8")

        # Parse and restructure the content
        restructured_content = restructure_latex_content(content)

        # Write the restructured content back to the file
        tex_file.write_text(restructured_content, encoding="utf-8")

        # Run pdflatex twice to resolve references
        for i in range(2):
            result = subprocess.run(
                ["pdflatex", "--interaction=nonstopmode", tex_file.name],
                cwd=project_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.error(f"Error running pdflatex (attempt {i+1}):")
                logger.error(result.stderr)
                return False

            logger.debug(f"pdflatex run {i+1} complete")

        pdf_file = project_dir / f"{paper_name}.pdf"
        if pdf_file.exists():
            logger.info(f"Generated PDF successfully at: {pdf_file}")
            return True
        else:
            logger.error("PDF file not found after compilation")
            return False

    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        return False


def clean_latex_content(content: str) -> str:
    """
    Clean LaTeX content by removing markdown code block markers and other unwanted elements.
    """
    # Remove ```latex and ``` markers
    content = content.replace("```latex", "").replace("```", "")

    # Clean up any extra newlines that might have been left
    content = "\n".join(line for line in content.splitlines() if line.strip())

    return content


def restructure_latex_content(content: str) -> str:
    """
    Restructure LaTeX content to ensure correct document structure.
    """
    try:
        # First clean the content
        content = clean_latex_content(content)
        # Remove any existing preamble commands
        lines = content.split("\n")
        cleaned_lines = []
        skip_mode = False

        title = None
        author = None
        date = None
        body_content = []

        for line in lines:
            # Skip existing preamble commands
            if line.strip().startswith("\\documentclass"):
                skip_mode = True
                continue
            if line.strip().startswith("\\begin{document}"):
                skip_mode = False
                continue
            if line.strip().startswith("\\end{document}"):
                continue
            if skip_mode:
                # Capture metadata while skipping preamble
                if line.strip().startswith("\\title{"):
                    title = line
                elif line.strip().startswith("\\author{"):
                    author = line
                elif line.strip().startswith("\\date{"):
                    date = line
                continue

            if not skip_mode and line.strip():
                body_content.append(line)

        # Construct the new document
        new_content = [LATEX_PREAMBLE]

        # Add metadata if found
        if title:
            new_content.append(title)
        if author:
            new_content.append(author)
        if date:
            new_content.append(date)

        # Start document
        new_content.append("\\begin{document}")

        # If we have title/author, add maketitle
        if title or author or date:
            new_content.append("\\maketitle")

        # Add the main content
        new_content.extend(body_content)

        # End document
        new_content.append("\\end{document}")

        return "\n".join(new_content)

    except Exception as e:
        logger.error(f"Error restructuring LaTeX content: {e}")
        raise

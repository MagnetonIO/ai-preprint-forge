from pathlib import Path
import re
import pytest
from app.services.name_tracker import NameTracker


@pytest.mark.asyncio
async def test_generate_paper_name_and_setup_project(tmp_path):
    base: Path = tmp_path / "ai_preprints"
    base.mkdir()

    tracker = NameTracker(base)
    prompt = "An exploration of test-driven development in AI"

    name = await tracker.generate_paper_name(prompt)
    # Pattern: slug_YYMMDD
    assert re.match(r"^[a-z0-9_]+_\d{6}$", name)

    md = "# Title\n\nSome content"
    tex = "\\documentclass{article}\n\\begin{document}\nHi\\end{document}"
    project_dir, paper_name = await tracker.setup_project(
        prompt=prompt,
        md_content=md,
        latex_content=tex,
        regenerate_markdown=True,
        regenerate_latex=True,
    )

    assert project_dir.exists()
    assert (project_dir / f"{paper_name}.md").exists()
    assert (project_dir / f"{paper_name}.tex").exists()

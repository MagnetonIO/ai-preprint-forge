from typer.testing import CliRunner
from pathlib import Path
import pytest

from app.cli.commands import app as cli_app
from app.core.config import settings


class FakeGenerator:
    async def generate_paper(self, **kwargs):  # type: ignore[no-untyped-def]
        base = Path(settings.base_directory)
        paper_name = "cli_paper_250101"
        project_dir = base / paper_name
        project_dir.mkdir(parents=True, exist_ok=True)
        return {
            "paper_name": paper_name,
            "repo_url": "https://example.com/repo",
            "project_dir": str(project_dir),
        }


@pytest.fixture(autouse=True)
def _isolate(tmp_path, monkeypatch):
    prev = settings.base_directory
    settings.base_directory = tmp_path / "ai_preprints"
    settings.base_directory.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("GITHUB_TOKEN", "test")
    monkeypatch.setenv("GITHUB_USERNAME", "testuser")
    yield
    settings.base_directory = prev


def test_cli_generate(monkeypatch):
    # Patch PaperGenerator used by CLI
    import app.cli.commands as cmd

    monkeypatch.setattr(cmd, "PaperGenerator", lambda: FakeGenerator())
    runner = CliRunner()
    result = runner.invoke(
        cli_app,
        [
            "--env",
            "development",
            "generate",
            "A topic",
            "--no-pages",
            "--no-social",
            "--no-md",
            "--no-latex",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Paper generation complete" in result.output


def test_cli_list(monkeypatch, tmp_path):
    # Create a couple of fake papers
    for name in ["a_250101", "b_250101"]:
        d = settings.base_directory / name
        d.mkdir(parents=True)
        (d / f"{name}.md").write_text("# t\n")

    runner = CliRunner()
    # Avoid GitHub API lookups
    result = runner.invoke(cli_app, ["list", "--no-github"]) 
    assert result.exit_code == 0, result.output
    out = result.output
    assert "a_250101" in out and "b_250101" in out


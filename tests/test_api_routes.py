from fastapi.testclient import TestClient
from pathlib import Path
import types
import pytest

from app.main import app
from app.core.config import settings


class FakeGenerator:
    async def generate_paper(self, **kwargs):  # type: ignore[no-untyped-def]
        paper_name = "test_paper_250101"
        project_dir = Path(settings.base_directory) / paper_name
        project_dir.mkdir(parents=True, exist_ok=True)
        return {
            "paper_name": paper_name,
            "repo_url": "https://example.com/repo",
            "project_dir": str(project_dir),
        }


@pytest.fixture(autouse=True)
def _isolate_basedir(tmp_path, monkeypatch):
    prev = settings.base_directory
    settings.base_directory = tmp_path / "ai_preprints"
    settings.base_directory.mkdir(parents=True, exist_ok=True)
    # Avoid GitHub/OpenAI usage by isolating any accidental calls
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("GITHUB_TOKEN", "test")
    monkeypatch.setenv("GITHUB_USERNAME", "testuser")
    try:
        yield
    finally:
        settings.base_directory = prev


def test_generate_paper_route(monkeypatch):
    # Patch PaperGenerator used by the route module
    import app.api.routes.papers as papers_mod

    monkeypatch.setattr(papers_mod, "PaperGenerator", lambda: FakeGenerator())
    client = TestClient(app)
    resp = client.post(
        "/api/v1/papers/",
        json={"prompt": "Test topic", "create_markdown": False, "create_latex": False},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["paper_name"].startswith("test_paper_")
    assert body["repo_url"] == "https://example.com/repo"


def test_list_papers_route(monkeypatch, tmp_path):
    # Prepare a fake paper dir
    paper_dir = settings.base_directory / "foo_250101"
    paper_dir.mkdir(parents=True)
    (paper_dir / "foo_250101.md").write_text("# title\n")

    client = TestClient(app)
    resp = client.get("/api/v1/papers/?show_github=false")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    names = [p["name"] for p in data["papers"]]
    assert "foo_250101" in names


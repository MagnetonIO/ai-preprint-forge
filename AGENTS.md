# Repository Guidelines

## Project Structure & Module Organization
- `app/`: Source code (FastAPI in `app/main.py`, CLI in `app/cli/commands.py`, config/logging in `app/core/`, services in `app/services/`).
- `ai_preprints/`: Generated paper projects (LaTeX/Markdown/PDF).
- `deploy/`: Docker, systemd, and Nginx deployment assets.
- `tests/`: Pytest suite (add tests here).
- Entrypoints: CLI `preprint-forge`, API module `app.main:app`.

## Build, Test, and Development Commands
- `poetry install` / `poetry shell`: Install deps and activate env.
- `preprint-forge --help`: Inspect CLI commands.
- `preprint-forge generate "Topic" --pages --social`: Create a paper + optional Pages/social.
- `preprint-forge server --reload` or `uvicorn app.main:app --reload`: Run API locally.
- `pytest --cov=app`: Run tests with coverage.
- `black .` · `flake8 app/` · `mypy app/`: Format, lint, and type-check.
- `docker-compose up -d --build`: Build and run via Docker.

## Coding Style & Naming Conventions
- Python 3.11; 4-space indent; Black line length 88.
- Use type hints; code must pass `mypy` and `flake8`.
- Naming: `snake_case` for modules/functions/vars, `PascalCase` for classes, `UPPER_SNAKE` for constants.
- Place new CLI commands in `app/cli/commands.py`; new API routes in `app/api/routes/`.

## Testing Guidelines
- Framework: Pytest (`tests/`); test files `test_*.py` or `*_test.py`.
- Prefer unit tests for `app/services/` and route tests for `app/api/` (use `pytest-asyncio` for async).
- Run locally with `pytest --cov=app`; strive for meaningful coverage and clear assertions.

## Commit & Pull Request Guidelines
- Use Conventional Commits where possible: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:` with optional scopes (e.g., `feat(api): ...`).
- Commit subject in imperative voice; keep concise (<72 chars). Add a body explaining the why when helpful.
- PRs include: clear description, linked issues, CLI/API examples (commands or responses), and notes on config changes. Update README/docs when behavior changes.

## Security & Configuration Tips
- Never commit secrets. Create `.env` from `.env_teamplate` and set `OPENAI_API_KEY`, `GITHUB_TOKEN`, `GITHUB_USERNAME` (and optional social tokens).
- Control CORS via `CORS_ORIGINS`. Check logs under `logs/` during development.

## Pre-commit Hooks
- Install and activate: `poetry install` then `poetry run pre-commit install`.
- Run on all files: `poetry run pre-commit run --all-files`.
- Hooks enforced: Black, Flake8, MyPy, and basic file checks.

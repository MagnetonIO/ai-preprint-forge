# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Preprint Forge is a Python-based framework for automated research paper generation using AI. It generates LaTeX documents, PDFs, manages Git repositories, and handles social media dissemination.

## Development Commands

### Quick Start
```bash
# Interactive setup (recommended)
./quickstart.sh
```

### Environment Setup
```bash
# Install dependencies with Poetry
poetry install

# Activate Poetry shell
poetry shell

# Or use pip with requirements.txt
pip install -r requirements.txt

# Or install system-wide
sudo ./install.sh
```

### Running the Application

**CLI Commands:**
```bash
# Generate a paper
preprint-forge generate "Your research prompt" --pages --social

# List all papers
preprint-forge list --verbose

# Delete a paper
preprint-forge delete paper-name --delete-repo

# Start FastAPI server
preprint-forge server --reload
```

**Direct Python execution:**
```bash
# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Deployment Options

**Docker:**
```bash
# Quick deployment
docker-compose up -d

# Production with Nginx
docker-compose --profile production up -d
```

**Systemd (Linux):**
```bash
cd deploy/systemd
sudo ./install-service.sh
sudo systemctl start ai-preprint-forge
```

### Testing & Linting
```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=app

# Format code with Black
black .
# Or use the lint script
python lint.py

# Type checking
mypy app/

# Linting
flake8 app/
```

## Architecture Overview

### Core Components

1. **FastAPI Application** (`app/main.py`): REST API server with CORS support for web interface integration.

2. **CLI Interface** (`app/cli/commands.py`): Typer-based CLI with commands for paper generation, management, and server control.

3. **Service Layer** (`app/services/`):
   - `paper_generator.py`: Core paper generation logic using OpenAI API
   - `git_manager.py`: GitHub repository creation and management
   - `name_tracker.py`: Tracks and reuses paper names
   - `social_media/`: Integration with Twitter, LinkedIn, and Facebook

4. **Configuration** (`app/core/config.py`): Pydantic settings management reading from environment variables.

### Key Workflows

**Paper Generation Flow:**
1. CLI/API receives prompt → PaperGenerator service
2. OpenAI API generates content (Markdown/LaTeX)
3. LaTeX compiled to PDF (if enabled)
4. Git repository created/updated
5. Optional: GitHub Pages setup, social media posting

**Directory Structure for Generated Papers:**
```
ai_preprints/
└── paper-name-YYMMDD/
    ├── paper-name-YYMMDD.md
    ├── paper-name-YYMMDD.tex
    ├── paper-name-YYMMDD.pdf
    └── README.md
```

## Important Configuration

The system uses environment variables (`.env` file) for:
- `OPENAI_API_KEY`: Required for paper generation
- `GITHUB_TOKEN`: Required for repository management
- `BASE_DIRECTORY`: Default is `ai_preprints/`
- Social media API keys (optional)
- Paper author details (optional defaults)

## Python Version Requirement

Must use Python ≤3.11.11 due to dependency constraints (specified in pyproject.toml).

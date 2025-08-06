# AI Preprint Forge

🔬 An AI-powered framework for automated research paper generation, publication, and dissemination.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

## Overview

AI Preprint Forge is a comprehensive framework that streamlines the research paper creation and publication process using AI. It provides both CLI and API interfaces for automated LaTeX generation, PDF conversion, Git repository management, and social media dissemination.

## Features

- 🤖 AI-powered LaTeX document generation using OpenAI GPT models
- 📄 Automatic PDF conversion from LaTeX
- 📚 Git repository creation and management with GitHub integration
- 🌐 GitHub Pages website generation for papers
- 📱 Social media integration (Twitter/X, LinkedIn, Facebook)
- 🔄 RESTful API with FastAPI
- 💻 Rich CLI interface with Typer
- 🐳 Docker support for easy deployment
- 📊 Paper tracking and management system

## Quick Start

### 🚀 Interactive Setup

```bash
# Run the quick start script
./quickstart.sh
```

This interactive script will guide you through:
- Environment configuration
- Installation method selection
- API key setup
- Deployment options

### 📦 Installation Options

#### Option 1: Poetry (Recommended for Development)

```bash
# Install with Poetry
poetry install

# Activate environment
poetry shell

# Run CLI
preprint-forge --help
```

#### Option 2: System-wide Installation

```bash
# Run installation script
sudo ./install.sh

# Or install with pip
pip install .
```

#### Option 3: Docker Deployment

```bash
# Using docker-compose
docker-compose up -d

# Or using deployment script
./deploy/scripts/deploy-docker.sh
```

## Usage

### CLI Commands

```bash
# Generate a paper
preprint-forge generate "Your research topic" --pages --social

# List all papers
preprint-forge list --verbose

# Delete a paper
preprint-forge delete paper-name --delete-repo

# Start API server
preprint-forge server --reload
```

### API Endpoints

Start the API server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access the API documentation at: `http://localhost:8000/docs`

#### Key Endpoints:
- `GET /health` - Health check
- `GET /ready` - Readiness check
- `POST /api/v1/papers/generate` - Generate a new paper
- `GET /api/v1/papers/list` - List all papers
- `DELETE /api/v1/papers/{paper_id}` - Delete a paper

## Configuration

Create a `.env` file from the template:

```bash
cp .env_teamplate .env
```

Required environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key
- `GITHUB_TOKEN` - GitHub personal access token
- `GITHUB_USERNAME` - Your GitHub username

Optional:
- `TWITTER_API_KEY`, `TWITTER_API_SECRET` - Twitter integration
- `LINKEDIN_ACCESS_TOKEN` - LinkedIn integration
- `FACEBOOK_ACCESS_TOKEN` - Facebook integration
- `CORS_ORIGINS` - Comma-separated list of allowed CORS origins

## Production Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d --build

# With production profile (includes Nginx)
docker-compose --profile production up -d

# With Redis cache
docker-compose --profile with-cache up -d
```

### Systemd Service (Linux)

```bash
# Install as systemd service
cd deploy/systemd
sudo ./install-service.sh

# Start service
sudo systemctl start ai-preprint-forge

# Check status
sudo systemctl status ai-preprint-forge
```

### Environment-specific Configurations

The application supports multiple deployment configurations:
- **Development**: Local development with hot reload
- **Production**: Optimized for performance with Nginx reverse proxy
- **Docker**: Containerized deployment with health checks
- **Systemd**: Native Linux service management

## Project Structure

```
ai-preprint-forge/
├── app/                      # Application source code
│   ├── api/                  # FastAPI routes and models
│   ├── cli/                  # CLI commands
│   ├── core/                 # Core configuration and logging
│   └── services/             # Business logic services
├── ai_preprints/            # Generated papers directory
├── deploy/                  # Deployment configurations
│   ├── systemd/            # Systemd service files
│   ├── nginx/              # Nginx configurations
│   └── scripts/            # Deployment scripts
├── tests/                   # Test suite
├── Dockerfile              # Docker container definition
├── docker-compose.yml      # Docker Compose configuration
├── setup.py               # Python package setup
├── pyproject.toml         # Poetry configuration
├── requirements.txt       # Python dependencies
├── install.sh            # System installation script
├── quickstart.sh         # Interactive setup script
└── README.md            # This file
```

## Development

### Running Tests

```bash
# Run tests with coverage
pytest --cov=app

# Format code
black .

# Type checking
mypy app/

# Linting
flake8 app/
```

### Contributing

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## API Documentation

When the server is running, access:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative API docs: `http://localhost:8000/redoc`

## Troubleshooting

### Common Issues

1. **Python Version**: Requires Python 3.11 (due to PyLaTeX compatibility)
2. **LaTeX Dependencies**: Install TeX Live for PDF generation
3. **API Keys**: Ensure all required API keys are configured in `.env`

### Getting Help

- Check the [Issues](https://github.com/yourusername/ai-preprint-forge/issues) page
- Review the API documentation at `/docs`
- Examine logs in `logs/` directory

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for GPT models
- FastAPI for the excellent web framework
- Typer for the CLI framework
- The academic community for inspiration

## Status

🚧 This project is under active development. Features and documentation are continuously being improved.

---

For support or questions, please open an issue on [GitHub](https://github.com/yourusername/ai-preprint-forge/issues).
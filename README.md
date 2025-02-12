# AI Preprint Forge

🔬 An AI-powered framework for automated research paper generation, publication, and dissemination.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## Overview

AI Preprint Forge is a comprehensive framework that streamlines the research paper creation and publication process using AI. It automates LaTeX generation, PDF conversion, Git repository management, and social media dissemination.

## Features

- 🤖 AI-powered LaTeX document generation
- 📄 Automatic PDF conversion
- 📚 Git repository creation and management
- 🌐 GitHub Pages website generation
- 📱 Social media integration (Twitter/X, LinkedIn, Facebook)
- 🔄 Automated workflow pipeline
- 📊 Knowledge graph integration (coming soon)

## Python Requirements

```bash
python <=3.11.11
```

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-preprint-forge.git
cd ai-preprint-forge

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.template .env
# Edit .env with your API keys and preferences
```

## Quick Start

```bash
# Basic usage
python preprint_forge.py "Your research topic or question"

# With GitHub Pages and social media posting
python preprint_forge.py "Your research topic" --setup-pages --post-social
```

## Configuration

The framework can be configured through environment variables in the `.env` file:

- OpenAI API settings
- GitHub credentials
- Social media API keys
- Directory configurations
- Paper generation preferences

See `.env.template` for all available options.

## Directory Structure

```
ai-preprint-forge/
├── preprint_forge.py
├── requirements.txt
├── .env.template
├── README.md
└── ai_preprints/
    └── generated-paper-name/
        ├── src/
        ├── output/
        ├── assets/
        └── pages/
```

## Contributing

We welcome contributions! Please check out our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit pull requests, report issues, and contribute to the project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for the GPT models
- The academic community for inspiration
- All contributors and users of the framework

## Status

🚧 This project is under active development. Features and documentation are continuously being improved.

---

For detailed documentation, visit our [GitHub Pages](https://yourusername.github.io/ai-preprint-forge/).

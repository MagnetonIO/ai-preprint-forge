#!/bin/bash

# AI Preprint Forge - Quick Start Script
# This script provides an interactive setup for AI Preprint Forge

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# ASCII Art Banner
show_banner() {
    echo -e "${MAGENTA}"
    echo "╔═══════════════════════════════════════════╗"
    echo "║       AI PREPRINT FORGE - Quick Start     ║"
    echo "║     Automated Research Paper Generation   ║"
    echo "╚═══════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main menu
show_menu() {
    echo -e "${BLUE}Select deployment method:${NC}"
    echo "1) Local Development (Poetry)"
    echo "2) System Installation (pip)"
    echo "3) Docker Deployment"
    echo "4) Production Setup (systemd)"
    echo "5) Configure Environment"
    echo "6) Run Tests"
    echo "7) Exit"
    echo
    read -p "Enter your choice [1-7]: " choice
}

# Setup environment configuration
setup_env() {
    echo -e "${BLUE}Setting up environment configuration...${NC}"

    if [ -f .env ]; then
        echo -e "${YELLOW}Existing .env file found.${NC}"
        read -p "Do you want to overwrite it? (y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi

    cp .env_teamplate .env
    echo -e "${GREEN}.env file created from template${NC}"

    # Interactive configuration
    echo -e "${BLUE}Let's configure your API keys:${NC}"

    read -p "Enter your OpenAI API key (or press Enter to skip): " openai_key
    if [ ! -z "$openai_key" ]; then
        sed -i.bak "s/OPENAI_API_KEY=.*/OPENAI_API_KEY=$openai_key/" .env
    fi

    read -p "Enter your GitHub token (or press Enter to skip): " github_token
    if [ ! -z "$github_token" ]; then
        sed -i.bak "s/GITHUB_TOKEN=.*/GITHUB_TOKEN=$github_token/" .env
    fi

    read -p "Enter your GitHub username (or press Enter to skip): " github_user
    if [ ! -z "$github_user" ]; then
        sed -i.bak "s/GITHUB_USERNAME=.*/GITHUB_USERNAME=$github_user/" .env
    fi

    rm -f .env.bak
    echo -e "${GREEN}Configuration saved to .env${NC}"
}

# Local development setup
setup_local() {
    echo -e "${BLUE}Setting up local development environment...${NC}"

    if command_exists poetry; then
        echo "Installing dependencies with Poetry..."
        poetry install
        echo -e "${GREEN}Setup complete!${NC}"
        echo "Run 'poetry shell' to activate the environment"
        echo "Then use 'preprint-forge --help' to get started"
    else
        echo -e "${YELLOW}Poetry not found. Installing with pip...${NC}"
        pip install poetry
        poetry install
    fi
}

# System installation
setup_system() {
    echo -e "${BLUE}Installing AI Preprint Forge system-wide...${NC}"

    if [ -f install.sh ]; then
        bash install.sh
    else
        echo "Installing with pip..."
        pip install -e .
    fi
}

# Docker deployment
setup_docker() {
    echo -e "${BLUE}Deploying with Docker...${NC}"

    if ! command_exists docker; then
        echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
        echo "Visit: https://docs.docker.com/get-docker/"
        return
    fi

    if [ -f deploy/scripts/deploy-docker.sh ]; then
        bash deploy/scripts/deploy-docker.sh
    else
        echo "Building Docker image..."
        docker build -t ai-preprint-forge .
        echo "Starting container..."
        docker run -d -p 8000:8000 --name ai-preprint-forge-api ai-preprint-forge
        echo -e "${GREEN}API is running at http://localhost:8000${NC}"
    fi
}

# Production setup
setup_production() {
    echo -e "${BLUE}Setting up production environment...${NC}"
    echo "Choose production deployment method:"
    echo "1) Systemd service (Linux)"
    echo "2) Docker Compose"
    echo "3) Cancel"
    read -p "Enter choice [1-3]: " prod_choice

    case $prod_choice in
        1)
            if [ -f deploy/systemd/install-service.sh ]; then
                sudo bash deploy/systemd/install-service.sh
            else
                echo -e "${RED}Systemd installation script not found${NC}"
            fi
            ;;
        2)
            docker-compose up -d --build
            echo -e "${GREEN}Production deployment complete${NC}"
            ;;
        3)
            return
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            ;;
    esac
}

# Run tests
run_tests() {
    echo -e "${BLUE}Running tests...${NC}"

    if command_exists pytest; then
        pytest --cov=app
    else
        echo -e "${YELLOW}pytest not installed. Installing...${NC}"
        pip install pytest pytest-cov
        pytest --cov=app
    fi
}

# Main execution
main() {
    show_banner

    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ ! "$PYTHON_VERSION" =~ ^3\.11 ]]; then
        echo -e "${YELLOW}Warning: Python 3.11 is recommended. Found: $PYTHON_VERSION${NC}"
    fi

    while true; do
        show_menu

        case $choice in
            1)
                setup_local
                ;;
            2)
                setup_system
                ;;
            3)
                setup_docker
                ;;
            4)
                setup_production
                ;;
            5)
                setup_env
                ;;
            6)
                run_tests
                ;;
            7)
                echo -e "${GREEN}Thank you for using AI Preprint Forge!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice. Please try again.${NC}"
                ;;
        esac

        echo
        read -p "Press Enter to continue..."
        clear
    done
}

# Run main function
main "$@"

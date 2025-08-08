#!/bin/bash

# AI Preprint Forge - System Installation Script
# This script installs AI Preprint Forge system-wide with all necessary components

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Main installation process
main() {
    echo "======================================"
    echo "AI Preprint Forge Installation Script"
    echo "======================================"
    echo

    OS=$(detect_os)
    print_status "Detected OS: $OS"

    # Check Python version
    print_status "Checking Python version..."
    if command_exists python3; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        print_status "Found Python $PYTHON_VERSION"

        # Check if Python version is 3.11
        if [[ ! "$PYTHON_VERSION" =~ ^3\.11 ]]; then
            print_warning "Python 3.11 is required. Current version: $PYTHON_VERSION"
            read -p "Do you want to continue anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        print_error "Python 3 is not installed. Please install Python 3.11"
        exit 1
    fi

    # Check for pip
    print_status "Checking for pip..."
    if ! command_exists pip3; then
        print_error "pip3 is not installed. Please install pip3"
        exit 1
    fi

    # Install or upgrade pip, setuptools, and wheel
    print_status "Upgrading pip, setuptools, and wheel..."
    pip3 install --upgrade pip setuptools wheel

    # Check installation method preference
    echo
    print_status "Choose installation method:"
    echo "  1) System-wide installation (requires sudo)"
    echo "  2) User installation (no sudo required)"
    echo "  3) Development installation (editable)"
    read -p "Enter your choice (1-3): " INSTALL_CHOICE

    case $INSTALL_CHOICE in
        1)
            print_status "Installing AI Preprint Forge system-wide..."
            sudo pip3 install .
            INSTALL_TYPE="system"
            ;;
        2)
            print_status "Installing AI Preprint Forge for current user..."
            pip3 install --user .
            INSTALL_TYPE="user"
            print_warning "Make sure ~/.local/bin is in your PATH"
            ;;
        3)
            print_status "Installing AI Preprint Forge in development mode..."
            pip3 install -e .
            INSTALL_TYPE="development"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac

    # Install LaTeX dependencies if requested
    echo
    read -p "Do you want to install LaTeX dependencies for PDF generation? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Installing LaTeX dependencies..."

        if [[ "$OS" == "linux" ]]; then
            if command_exists apt-get; then
                sudo apt-get update
                sudo apt-get install -y texlive-latex-base texlive-latex-extra texlive-fonts-recommended
            elif command_exists yum; then
                sudo yum install -y texlive texlive-latex texlive-xetex
            elif command_exists dnf; then
                sudo dnf install -y texlive texlive-latex texlive-xetex
            else
                print_warning "Could not detect package manager. Please install LaTeX manually."
            fi
        elif [[ "$OS" == "macos" ]]; then
            if command_exists brew; then
                brew install --cask mactex-no-gui
            else
                print_warning "Homebrew not found. Please install MacTeX manually from https://www.tug.org/mactex/"
            fi
        fi
    fi

    # Create configuration directory
    print_status "Creating configuration directory..."
    CONFIG_DIR="$HOME/.config/ai-preprint-forge"
    mkdir -p "$CONFIG_DIR"

    # Copy environment template if it doesn't exist
    if [ ! -f "$CONFIG_DIR/.env" ]; then
        if [ -f ".env_teamplate" ]; then
            cp .env_teamplate "$CONFIG_DIR/.env.template"
            print_status "Configuration template copied to $CONFIG_DIR/.env.template"
            print_warning "Please edit $CONFIG_DIR/.env with your API keys"
        fi
    fi

    # Create logs directory
    LOGS_DIR="$HOME/.local/share/ai-preprint-forge/logs"
    mkdir -p "$LOGS_DIR"
    print_status "Logs directory created at $LOGS_DIR"

    # Verify installation
    print_status "Verifying installation..."
    if command_exists preprint-forge; then
        print_success "AI Preprint Forge installed successfully!"
        echo
        print_status "Installation summary:"
        echo "  - Installation type: $INSTALL_TYPE"
        echo "  - Configuration: $CONFIG_DIR"
        echo "  - Logs: $LOGS_DIR"
        echo
        print_status "Next steps:"
        echo "  1. Configure your API keys in $CONFIG_DIR/.env"
        echo "  2. Run 'preprint-forge --help' to see available commands"
        echo "  3. Generate your first paper with 'preprint-forge generate \"Your topic\"'"
    else
        print_error "Installation verification failed"
        print_warning "You may need to add the installation directory to your PATH"

        if [[ "$INSTALL_TYPE" == "user" ]]; then
            echo "Add this line to your ~/.bashrc or ~/.zshrc:"
            echo "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        fi
    fi

    echo
    echo "======================================"
    echo "Installation Complete!"
    echo "======================================"
}

# Run main function
main "$@"

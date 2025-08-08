#!/bin/bash

# Systemd Service Installation Script for AI Preprint Forge
set -e

# Check if running as root
if [ "$EUID" -ne 0 ]; then
   echo "Please run as root (use sudo)"
   exit 1
fi

echo "Installing AI Preprint Forge as systemd service..."

# Create system user
if ! id "ai-preprint-forge" &>/dev/null; then
    echo "Creating system user 'ai-preprint-forge'..."
    useradd --system --shell /bin/false --home /opt/ai-preprint-forge ai-preprint-forge
fi

# Create directories
echo "Creating directories..."
mkdir -p /opt/ai-preprint-forge
mkdir -p /etc/ai-preprint-forge
mkdir -p /opt/ai-preprint-forge/ai_preprints
mkdir -p /opt/ai-preprint-forge/logs

# Copy application files
echo "Copying application files..."
cp -r ../../* /opt/ai-preprint-forge/
chown -R ai-preprint-forge:ai-preprint-forge /opt/ai-preprint-forge

# Install Python dependencies
echo "Installing Python dependencies..."
cd /opt/ai-preprint-forge
python3 -m pip install -r requirements.txt

# Copy configuration template
if [ ! -f /etc/ai-preprint-forge/config.env ]; then
    echo "Creating configuration file..."
    cat > /etc/ai-preprint-forge/config.env << 'EOF'
# AI Preprint Forge Configuration
# Edit this file with your actual API keys and settings

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4

# GitHub Configuration
GITHUB_TOKEN=your-github-token-here
GITHUB_USERNAME=your-github-username

# Application Settings
BASE_DIRECTORY=/opt/ai-preprint-forge/ai_preprints
GENERATE_PDF=true
GENERATE_LATEX=true
LOG_LEVEL=info

# Optional: Social Media
# TWITTER_API_KEY=
# TWITTER_API_SECRET=
# LINKEDIN_ACCESS_TOKEN=
# FACEBOOK_ACCESS_TOKEN=
EOF
    chmod 600 /etc/ai-preprint-forge/config.env
    chown ai-preprint-forge:ai-preprint-forge /etc/ai-preprint-forge/config.env
    echo "Please edit /etc/ai-preprint-forge/config.env with your API keys"
fi

# Install systemd service
echo "Installing systemd service..."
cp ai-preprint-forge.service /etc/systemd/system/
systemctl daemon-reload

# Enable service
echo "Enabling service..."
systemctl enable ai-preprint-forge.service

echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit configuration: sudo nano /etc/ai-preprint-forge/config.env"
echo "2. Start service: sudo systemctl start ai-preprint-forge"
echo "3. Check status: sudo systemctl status ai-preprint-forge"
echo "4. View logs: sudo journalctl -u ai-preprint-forge -f"

#!/bin/bash

# Docker Deployment Script for AI Preprint Forge
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}AI Preprint Forge - Docker Deployment${NC}"
echo "======================================"
echo

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Check for .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found${NC}"
    echo "Creating .env from template..."
    if [ -f .env_teamplate ]; then
        cp .env_teamplate .env
        echo -e "${YELLOW}Please edit .env file with your API keys before continuing${NC}"
        read -p "Press Enter after editing .env file..."
    else
        echo -e "${RED}Error: .env_teamplate not found${NC}"
        exit 1
    fi
fi

# Parse command line arguments
PROFILE=""
BUILD_FLAG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --production)
            PROFILE="--profile production"
            shift
            ;;
        --with-cache)
            PROFILE="--profile with-cache"
            shift
            ;;
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --production    Deploy with Nginx reverse proxy"
            echo "  --with-cache    Deploy with Redis cache"
            echo "  --build         Force rebuild of Docker images"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Create necessary directories
echo "Creating directories..."
mkdir -p ai_preprints logs

# Stop existing containers
echo "Stopping existing containers..."
docker-compose down 2>/dev/null || true

# Build and start containers
echo "Building and starting containers..."
if docker compose version &> /dev/null; then
    docker compose $PROFILE up -d $BUILD_FLAG
else
    docker-compose $PROFILE up -d $BUILD_FLAG
fi

# Wait for service to be ready
echo "Waiting for service to start..."
sleep 5

# Check service health
echo "Checking service health..."
if curl -f http://localhost:8000/health &> /dev/null; then
    echo -e "${GREEN}Service is healthy!${NC}"
else
    echo -e "${YELLOW}Service may still be starting...${NC}"
fi

echo
echo -e "${GREEN}Deployment complete!${NC}"
echo "======================================"
echo "API is available at: http://localhost:8000"
echo "API documentation: http://localhost:8000/docs"
echo
echo "Useful commands:"
echo "  View logs:        docker-compose logs -f"
echo "  Stop service:     docker-compose down"
echo "  Restart service:  docker-compose restart"
echo "  Shell access:     docker-compose exec api bash"
#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Starting deployment process...${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create a .env file with the following variables:"
    echo "SECRET_KEY=your-secure-secret-key"
    echo "GOOGLE_CLIENT_ID=your-google-client-id"
    echo "GOOGLE_CLIENT_SECRET=your-google-client-secret"
    echo "ALPHA_VANTAGE_API_KEY=your-alpha-vantage-api-key"
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed!${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed!${NC}"
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

# Build and start the containers
echo -e "${GREEN}Building and starting containers...${NC}"
docker-compose up --build -d

# Wait for the application to start
echo -e "${GREEN}Waiting for the application to start...${NC}"
sleep 10

# Check if the application is running
if curl -s http://localhost:8000/api/health | grep -q "ok"; then
    echo -e "${GREEN}Deployment successful!${NC}"
    echo "Your application is running at: http://localhost:8000"
else
    echo -e "${RED}Error: Application failed to start!${NC}"
    echo "Please check the logs with: docker-compose logs"
    exit 1
fi

echo -e "${GREEN}Deployment complete!${NC}" 
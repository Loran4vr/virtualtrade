#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Starting deployment preparation...${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Creating .env file with template..."
    echo "SECRET_KEY=your-secure-secret-key" > .env
    echo "GOOGLE_CLIENT_ID=your-google-client-id" >> .env
    echo "GOOGLE_CLIENT_SECRET=your-google-client-secret" >> .env
    echo "ALPHA_VANTAGE_API_KEY=your-alpha-vantage-api-key" >> .env
    echo -e "${GREEN}Created .env file. Please update it with your actual values.${NC}"
fi

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: Git is not installed!${NC}"
    echo "Please install Git first: https://git-scm.com/downloads"
    exit 1
fi

# Initialize git if not already done
if [ ! -d .git ]; then
    echo -e "${GREEN}Initializing git repository...${NC}"
    git init
    git add .
    git commit -m "Initial commit"
fi

echo -e "${GREEN}Deployment preparation complete!${NC}"
echo -e "\nNext steps:"
echo "1. Create a GitHub repository"
echo "2. Run these commands (replace YOUR_REPO_URL with your GitHub repository URL):"
echo "   git remote add origin YOUR_REPO_URL"
echo "   git push -u origin main"
echo -e "\n3. Go to render.com and:"
echo "   - Sign up/Login"
echo "   - Click 'New +' and select 'Web Service'"
echo "   - Connect your GitHub repository"
echo "   - Configure the service with these settings:"
echo "     * Name: virtualtrade"
echo "     * Environment: Docker"
echo "     * Branch: main"
echo "     * Plan: Free"
echo "   - Add your environment variables from .env file"
echo -e "\n4. Click 'Create Web Service'" 
#!/bin/bash

# Exit on error
set -e

echo "Building frontend..."
# Install frontend dependencies
npm install

# Build frontend
npm run build

echo "Building backend..."
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install backend dependencies
pip install -r requirements.txt

# Set production environment
export FLASK_ENV=production

echo "Build complete!" 
# Use Node.js image for frontend build
FROM node:16-alpine as frontend-builder

# Set working directory
WORKDIR /app

# Copy frontend files
COPY frontend/package*.json ./
RUN npm install

# Copy frontend source
COPY frontend/ .
RUN npm run build

# Use Python 3.9 slim image as base for backend
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Set memory limits for Python
ENV PYTHONMALLOC=debug
ENV PYTHONMALLOCSTATS=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend application
COPY . .

# Create static directory and copy frontend build
RUN mkdir -p static
COPY --from=frontend-builder /app/build/ static/

# Create a non-root user
RUN useradd -m myuser
RUN chown -R myuser:myuser /app
USER myuser

# Set memory limits for the container
ENV DOCKER_MEMORY_LIMIT=1G

# Create startup script
RUN echo '#!/bin/bash\npython -O init_db.py\ngunicorn --bind 0.0.0.0:5000 --workers 2 --threads 2 --timeout 120 "main:create_app()"' > /app/start.sh
RUN chmod +x /app/start.sh

# Expose port
EXPOSE 5000

# Start the application
CMD ["/app/start.sh"] 
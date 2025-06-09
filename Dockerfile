# Use Python 3.9 slim image
FROM python:3.9-slim as backend-builder

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Use Node.js image for frontend
FROM node:16-alpine as frontend-builder

# Set working directory
WORKDIR /app

# Copy frontend files
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ .
RUN npm run build

# Final stage
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files from backend-builder
COPY --from=backend-builder /app /app

# Copy frontend build from frontend-builder
COPY --from=frontend-builder /app/build /app/static

# Create static directory if it doesn't exist
RUN mkdir -p static

# Set environment variables
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Run database initialization script
RUN python init_db.py

# Expose port
EXPOSE 5000

# Start command
CMD ["gunicorn", "--config", "gunicorn_config.py", "main:app"] 
# Use Node.js for building frontend
FROM node:20-alpine as frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Python backend
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.prod.txt .
RUN pip install --no-cache-dir -r requirements.prod.txt

# Copy the rest of the application
COPY . .

# Create static directory if it doesn't exist
RUN mkdir -p /app/static

# Copy built frontend files
COPY --from=frontend-builder /app/frontend/build/static/ /app/static/
COPY --from=frontend-builder /app/frontend/build/index.html /app/static/index.html

# Verify static files exist
RUN ls -la /app/static

# Set environment variables
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
ENV PORT=5000

# Expose the port
EXPOSE 5000

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "main:create_app()"] 
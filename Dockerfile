# Use Node.js for building frontend
FROM node:20-alpine as frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json ./
COPY frontend/ ./
ENV PUBLIC_URL=.
RUN npm install
RUN npm run build
RUN ls -la /app/frontend/build

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

# Verify backend directory contents
RUN ls -la /app/backend

# Set FLASK_ENV for the init_db.py run step
ENV FLASK_ENV=production

# Run database initialization script
RUN python init_db.py

# Create static directory if it doesn't exist
RUN mkdir -p /app/static

# Copy built frontend files
COPY --from=frontend-builder /app/frontend/build/static/ /app/static/
COPY --from=frontend-builder /app/frontend/build/index.html /app/static/index.html

# Verify static files exist
RUN ls -la /app/static

# Set environment variables
ENV FLASK_APP=main.py
ENV PORT=5000
ENV PYTHONPATH=/app:$PYTHONPATH

# Expose the port
EXPOSE 5000

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "2", "--timeout", "120", "--keep-alive", "5", "--max-requests", "1000", "--max-requests-jitter", "50", "main:application"] 
# Use Node.js for building frontend
FROM node:18-alpine as frontend-builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
COPY frontend/ ./

RUN npm install
RUN npm run build
# Debug: List build output
RUN ls -l /app/build && ls -l /app/build/static/js

# Python backend
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend files
COPY . .

# Copy built frontend files
COPY --from=frontend-builder /app/build /app/static

# Debug: List static output in final image
RUN ls -l /app/static && ls -l /app/static/js

# Create and activate virtual environment
RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.prod.txt

# Set environment variables
ENV FLASK_ENV=production
ENV PORT=8000

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "-c", "gunicorn_config.py", "main:create_app()"] 
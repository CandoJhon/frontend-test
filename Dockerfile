# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --no-warn-script-location -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p auth templates static/css static/js

# Expose port
EXPOSE 5000

# Environment variables with defaults
ENV PORT=5000
ENV SECRET_KEY="dev-secret-key-change-in-production"
ENV APPID_REGION=us-south
ENV APPID_TENANT_ID=""
ENV APPID_CLIENT_ID=""
ENV APPID_SECRET=""
ENV APPID_REDIRECT_URI="http://localhost:5000/auth/callback"
ENV BACKEND_URL="http://localhost:8080"

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Run the application
CMD ["python", "app.py"]
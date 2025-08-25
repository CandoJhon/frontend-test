# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for cryptography
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    python3-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --upgrade pip

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies step by step
RUN pip install --no-cache-dir Flask Werkzeug
RUN pip install --no-cache-dir requests
RUN pip install --no-cache-dir PyJWT==2.8.0
RUN pip install --no-cache-dir cryptography==41.0.8

# Copy application code
COPY . .

# Create necessary directories and ensure __init__.py exists
RUN mkdir -p auth templates static/css static/js && \
    echo "# Auth module" > auth/__init__.py

# Expose port
EXPOSE 5000

# Environment variables
ENV PORT=5000

# Run the application
CMD ["python", "app.py"]
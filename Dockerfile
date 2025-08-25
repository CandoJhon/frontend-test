# Use Alpine-based Python image (often better for cryptography)
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Install system dependencies for Alpine including Rust
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    python3-dev \
    build-base \
    rust \
    cargo \
    curl

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create auth directory and __init__.py
RUN mkdir -p auth && echo "# Auth module" > auth/__init__.py

# Expose port
EXPOSE 8080

# Environment variables
ENV PORT=8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
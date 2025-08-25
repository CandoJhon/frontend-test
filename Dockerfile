# Use official Python runtime as parent image  
FROM python:3.11

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt ./

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the current directory contents into the container
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
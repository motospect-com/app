# Optimized single-stage build for faster loading
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies with pip (faster than uv for small projects)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Expose the port the app runs on
EXPOSE 8030

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8030/health || exit 1

# Command to run the application
CMD ["python", "-m", "uvicorn", "simple_api:app", "--host", "0.0.0.0", "--port", "8030"]

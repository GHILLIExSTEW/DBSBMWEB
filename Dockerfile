# DBSBMWEB Flask Web Application Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .

# Install PostgreSQL dependencies
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip install --no-cache-dir psycopg2-binary>=2.9.0 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs \
    /app/db_logs \
    /app/static/guild_images \
    /app/cgi-bin/bot/static

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0
ENV FLASK_APP=cgi-bin/webapp.py

# Create non-root user for security
RUN useradd -m -u 1000 webapp && \
    chown -R webapp:webapp /app

# Switch to non-root user
USER webapp

# Expose port
EXPOSE 25595

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:25595/health')" || exit 1

# Start the Flask application
CMD ["python", "cgi-bin/webapp.py"] 
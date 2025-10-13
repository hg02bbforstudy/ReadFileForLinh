FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for basic image processing (minimal set)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libglib2.0-0 \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway will override this)
EXPOSE $PORT

# Command to run the application
CMD gunicorn app:app --host 0.0.0.0 --port $PORT --workers 2 --timeout 120
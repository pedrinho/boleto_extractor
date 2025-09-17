# Use Python 3.11 slim image
FROM python:3.11-slim

# Install minimal system dependencies for headless OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libjpeg62-turbo \
    libpng16-16 \
    libtiff5 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p templates static/css static/js

# Expose port
EXPOSE 3000

# Set environment variables
ENV FLASK_ENV=production
ENV PORT=3000

# Run the application
CMD ["python", "app.py"]

# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV DISPLAY=:99
ENV PYPPETEER_CHROMIUM_REVISION=1040215

# Expose port (not needed for Railway but good practice)
EXPOSE 8000

# Command to run the application
CMD ["python", "app.py"]
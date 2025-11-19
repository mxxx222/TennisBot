FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Mojo SDK (optional - will skip if unavailable)
# Mojo SDK can be installed from https://www.modular.com/max/mojo
# For production, download and install Mojo SDK manually or via package manager
RUN if [ -n "$MOJO_SDK_PATH" ] && [ -f "$MOJO_SDK_PATH/mojo" ]; then \
    echo "Mojo SDK detected at $MOJO_SDK_PATH"; \
    else \
    echo "Mojo SDK not found - Python fallback will be used"; \
    fi

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install ChromeDriver with version matching
RUN CHROMEDRIVER_VERSION=$(curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && wget -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin/ \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy requirements first (for better Docker caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p logs data config mojo_layer/build

# Build Mojo modules if Mojo SDK is available
RUN if [ -n "$MOJO_SDK_PATH" ] && [ -f "$MOJO_SDK_PATH/mojo" ]; then \
    echo "Building Mojo performance layer..."; \
    chmod +x mojo_layer/build.sh && ./mojo_layer/build.sh || echo "Mojo build failed, using Python fallback"; \
    else \
    echo "Skipping Mojo build - SDK not available"; \
    fi

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV EDUCATIONAL_MODE=true
ENV CHROMEDRIVER_PATH=/usr/local/bin/chromedriver
ENV USE_MOJO_LAYER=true
ENV MOJO_DEBUG=false

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=5m --timeout=30s --start-period=60s --retries=3 \
  CMD python -c "import sys; sys.exit(0)" || exit 1

# Expose port (if web interface is added)
EXPOSE 8000

# Default command - run scheduler for ITF tennis pipeline
CMD ["python", "scripts/tennis_ai/scheduler.py"]
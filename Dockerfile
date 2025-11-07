FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONHASHSEED=0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    golang-1.21 \
    clang \
    libclang-dev \
    nodejs \
    npm \
    curl \
    wget \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set up Go environment
ENV PATH=/usr/lib/go-1.21/bin:$PATH
ENV GOROOT=/usr/lib/go-1.21

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x scripts/*.py

# Set up git for safe operations
RUN git config --global user.name "Benchmark Runner" && \
    git config --global user.email "benchmark@example.com" && \
    git config --global --add safe.directory /app

# Create directories for corpus
RUN mkdir -p src transforms tasks scoring/oracle

# Default command
CMD ["make", "help"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 --version && go version

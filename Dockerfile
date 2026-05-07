FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV for fast dependency management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/

# Install dependencies
RUN uv sync --no-dev

# Download required models
RUN uv run python src/agent.py download-files

# Expose port for health checks
EXPOSE 8000

# Set environment defaults
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=info

# Run agent in production mode
CMD ["uv", "run", "python", "src/agent.py", "start"]

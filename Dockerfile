# Dockerfile
FROM python:3.11-slim-bullseye

# Install system dependencies
RUN apt-get update \
    && apt-get install -y \
        gcc \
        curl \
        make \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME=/usr/local
ENV POETRY_VERSION=1.7.1

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/usr/local python3 - && \
    /usr/local/bin/poetry --version

# Configure Poetry
RUN poetry config virtualenvs.create false

# Set working directory
WORKDIR /app

# Copy only dependency files first (for better caching)
COPY pyproject.toml poetry.lock ./

# Install dependencies (production only)
RUN poetry install --only=main --no-interaction --no-ansi && \
    rm -rf $POETRY_CACHE_DIR

# Copy application code
COPY dream_interpreter/ ./dream_interpreter/

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt', quiet=True)" && \
    python -c "import nltk; nltk.download('brown', quiet=True)"

# Expose port
EXPOSE 8000

# Run the application
CMD ["poetry", "run", "uvicorn", "dream_interpreter.main:app", "--host", "0.0.0.0", "--port", "8000"]
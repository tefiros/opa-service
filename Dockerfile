# OPA Evaluation Service - Dockerfile.

# Stage 1: Builder - install dependencies using Poetry
FROM python:3.11-slim AS builder

# Metadata labels
LABEL image_version="1.0.0"
LABEL app_version="0.1.0"
LABEL maintainer="lucia.cabanillasrodriguez@telefonica.com"

# --- Install Poetry ---
ARG POETRY_VERSION=1.8

ENV POETRY_HOME=/opt/poetry
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=1
ENV POETRY_VIRTUALENVS_CREATE=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Poetry cache for dependencies
ENV POETRY_CACHE_DIR=/opt/.cache

RUN pip install "poetry==${POETRY_VERSION}"

WORKDIR /app

# --- Install dependencies ---
# Copy only the dependency definitions
COPY pyproject.toml poetry.lock ./

# Install dependencies in a virtual environment
RUN poetry install --no-root && rm -rf $POETRY_CACHE_DIR

# Stage 2: Runtime - copy the app and virtual environment from the builder
FROM python:3.11-slim AS runtime

# Set up the virtual environment path
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy the FastAPI app code
COPY ./opa_service /app/opa_service

# Set working directory
WORKDIR /app/opa_service

# Expose the port for the FastAPI app
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
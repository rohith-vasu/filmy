#!/bin/bash
set -e

# --------------------------------------
# Determine environment (development vs production)
# --------------------------------------
if [ -z "$ENV_FOR_DYNACONF" ]; then
    # If running locally, default to development
    ENV_FOR_DYNACONF="development"
fi

echo "🔧 ENV_FOR_DYNACONF = $ENV_FOR_DYNACONF"

# --------------------------------------
# Detect if running inside Docker
# --------------------------------------
if [ -f /.dockerenv ]; then
    IS_DOCKER=true
else
    IS_DOCKER=false
fi

# --------------------------------------
# Select correct env file
# --------------------------------------
if [ "$IS_DOCKER" = true ]; then
    ENV_FILE=".env.prod"
else
    ENV_FILE=".env.dev"
fi

if [ -f "$ENV_FILE" ]; then
    echo "📦 Loading $ENV_FILE"
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "⚠️  $ENV_FILE not found — continuing without it"
fi

# --------------------------------------
# Run server
# --------------------------------------
if [ "$IS_DOCKER" = true ]; then
    echo "🐳 Running in Docker → PRODUCTION mode"

    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port "${PORT:-8000}"
else
    echo "💻 Running locally → DEVELOPMENT mode"

    # Activate virtual environment
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    fi

    exec uvicorn app.main:app \
        --host "${HOST:-0.0.0.0}" \
        --port "${PORT:-8000}" \
        --reload \
        --reload-dir ./app
fi

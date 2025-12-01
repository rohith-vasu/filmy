# Docker Compose file
COMPOSE_FILE = ops/docker-compose.yaml
PROJECT_NAME = filmy

# Base Compose command
DC = docker compose -p $(PROJECT_NAME) -f $(COMPOSE_FILE)

# Build the images (no start)
build:
	$(DC) build

# Build images from scratch (no cache)
build-nc:
	$(DC) build --no-cache

# Start services (does not rebuild images)
up:
	$(DC) up -d

# Build and start full production stack (backend + frontend + dependencies)
up-prod-build:
	$(DC) up --build -d
	docker image prune -f

# Start full production stack (backend + frontend + dependencies)
up-prod:
	$(DC) up -d

# Start only dependencies (database, redis, etc.)
up-deps:
	$(DC) up -d postgres pgadmin qdrant prefect-server prefect-worker mlflow minio

# Stop services (but keep containers, volumes, and network)
stop:
	$(DC) stop

# Restart full app (rebuild backend image, then start everything)
restart-app:
	$(MAKE) down
	docker rmi $(PROJECT_NAME)/backend || true
	docker rmi $(PROJECT_NAME)/frontend || true
	$(DC) build
	$(MAKE) up

# Restart dependencies only
restart-deps:
	$(MAKE) down
	docker rmi $(PROJECT_NAME)/backend || true
	$(DC) build backend
	$(DC) up -d postgres pgadmin qdrant prefect-server prefect-worker mlflow minio

# Bring everything down (containers, networks)
down:
	$(DC) down

# Bring everything down and remove volumes and orphans
nuke:
	$(DC) down --volumes --remove-orphans

# View logs
logs:
	$(DC) logs -f

# Show container status
ps:
	$(DC) ps

# Train implicit model
.PHONY: train-model
train-model:
	@if [ -f backend/.env.dev ]; then \
		export $$(cat backend/.env.dev | grep -v '^#' | xargs) && \
		cd backend && .venv/bin/python3 -m app.pipelines.training.train_implicit; \
	else \
		echo "Error: backend/.env.dev not found."; \
		exit 1; \
	fi

# Generate synthetic feedbacks
.PHONY: generate-synthetic-feedbacks
generate-synthetic-feedbacks:
	@if [ -f backend/.env.dev ]; then \
		export $$(cat backend/.env.dev | grep -v '^#' | xargs) && \
		cd backend && .venv/bin/python3 -m app.pipelines.data.generate_synthetic_feedbacks; \
	else \
		echo "Error: backend/.env.dev not found."; \
		exit 1; \
	fi

# TMDB Ingestion
.PHONY: ingest-tmdb
ingest-tmdb:
	@if [ -f backend/.env.dev ]; then \
		export $$(cat backend/.env.dev | grep -v '^#' | xargs) && \
		cd backend && .venv/bin/python -m app.pipelines.data.ingest_tmdb; \
	else \
		echo "Error: backend/.env.dev not found."; \
		exit 1; \
	fi
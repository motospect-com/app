# Makefile for the Motospect project

.PHONY: build up down logs test test-backend test-frontend clean

# Build Docker images
build:
	docker-compose build

# Start services in detached mode
up:
	docker-compose up -d

# Stop and remove containers
down:
	docker-compose down

# View logs from services
logs:
	docker-compose logs -f

# Run all tests
test:
	make test-backend
	make test-frontend

# Run backend tests
test-backend:
	pytest

# Run frontend tests inside the container
test-frontend:
	docker-compose exec frontend env CI=true npm test

# Clean up project artifacts
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -r {} +
	docker-compose down -v --remove-orphans

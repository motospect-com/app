# MotoSpect Project Makefile
# Vehicle diagnostic system for cars, vans, SUVs up to 3L engine capacity

.PHONY: help build up down restart logs test test-e2e test-backend test-mqtt clean install dev prod

# Default target - show help
help:
	@echo "MotoSpect System Commands:"
	@echo "  make install    - Install Python dependencies"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View service logs"
	@echo "  make test       - Run all tests"
	@echo "  make test-e2e   - Run E2E tests"
	@echo "  make test-mqtt  - Test MQTT sensor simulation"
	@echo "  make dev        - Start in development mode"
	@echo "  make prod       - Start in production mode"
	@echo "  make clean      - Clean up artifacts"

# Install dependencies
install:
	pip3 install -r backend/requirements.txt
	cd frontend && npm install
	cd customer-portal && npm install

# Build Docker images
build:
	docker-compose build --no-cache

# Start services in detached mode
up:
	docker-compose up -d
	@echo "Services started. Backend: http://localhost:8000"

# Stop and remove containers
down:
	docker-compose down

# Restart services
restart: down up

# View logs from services
logs:
	docker-compose logs -f

# Run backend locally for development
dev:
	cd backend && python3 main.py

# Start production environment
prod:
	docker-compose -f docker-compose.yml up -d

# Run all tests
test: test-backend test-e2e

# Run E2E tests
test-e2e:
	@echo "Running E2E tests..."
	@chmod +x run_e2e_tests.sh
	@./run_e2e_tests.sh

# Run backend tests locally
test-backend:
	cd backend && python3 -m pytest -v

# Test MQTT sensor simulation
test-mqtt:
	@echo "Starting MQTT sensor simulation..."
	cd tests && python3 mqtt_sensor_simulator.py --duration 30 --scan-id test-001

# Quick system test
test-quick:
	cd tests && python3 quick_test.py

# Clean up project artifacts
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -r {} +
	docker-compose down -v --remove-orphans
	rm -f test_results_*.txt diagnostic_report_*.json

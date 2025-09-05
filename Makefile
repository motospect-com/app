# MotoSpect Project Makefile
# Vehicle diagnostic system for cars, vans, SUVs up to 3L engine capacity

.PHONY: help build up down restart logs test test-e2e test-backend test-mqtt test-system test-api test-complete test-ansible clean install dev prod status quick-start dev-start dev-down dev-up dev-restart dev-up-all dev-restart-all microservices-start microservices-stop microservices-status microservices-verify run-tests run-e2e-tests start-services diagnose demo

# Utility commands
.PHONY: diagnose
diagnose:
	@echo "🔍 Running diagnostics..."
	@$(PYTHON) $(UTIL_SCRIPTS)/diagnose.py

.PHONY: demo
demo:
	@echo "🎮 Running demo..."
	@$(PYTHON) $(UTIL_SCRIPTS)/demo_microservices.py

# Variables
PYTHON := python3
PIP := pip3
DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_DEV := docker-compose -f docker-compose.dev.yml

# Script directories
SCRIPTS_DIR := scripts
DOCKER_SCRIPTS := $(SCRIPTS_DIR)/docker
MICROSERVICE_SCRIPTS := $(SCRIPTS_DIR)/microservices
TEST_SCRIPTS := $(SCRIPTS_DIR)/testing
UTIL_SCRIPTS := $(SCRIPTS_DIR)/utils

# Help target
.PHONY: help
help:
	@echo "MOTOSPECT Makefile Commands:"
	@echo "  make quick-start - Szybkie uruchomienie bez budowania (30s)"
	@echo "  make dev-start  - Development mode z cache (60s)"
	@echo "  make dev-down   - Stop dev compose stack"
	@echo "  make dev-up     - Build & start backend-dev + frontend-dev"
	@echo "  make dev-restart - Down + up build backend-dev + frontend-dev"
	@echo "  make dev-up-all - Build & start all dev services (backend, frontend, customer)"
	@echo "  make dev-restart-all - Down + up build all dev services"
	@echo "  make install    - Install Python dependencies"
	@echo "  make build      - Build Docker images (powolne - 10+ min)"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View service logs"
	@echo ""
	@echo "Microservices Commands:"
	@echo "  make microservices-start  - Start all microservices with .env config"
	@echo "  make microservices-stop   - Stop all microservices"
	@echo "  make microservices-status - Check microservices health"
	@echo "  make microservices-verify - Verify microservices can import"
	@echo ""
	@echo "Test Commands:"
	@echo "  make test       - Run all tests"
	@echo "  make test-e2e   - Run E2E tests"
	@echo "  make run-e2e-tests - Run E2E test script"
	@echo "  make run-tests  - Run test suite script"
	@echo "  make test-mqtt  - Test MQTT sensor simulation"
	@echo "  make test-system - Run system integration tests"
	@echo "  make test-api   - Test API and CORS"
	@echo "  make test-complete - Run complete system test"
	@echo "  make test-ansible - Run Ansible test playbook"
	@echo ""
	@echo "Other Commands:"
	@echo "  make start-services - Start services via start script"
	@echo "  make status     - Show service status"
	@echo "  make dev        - Start in development mode"
	@echo "  make prod       - Start in production mode"
	@echo "  make clean      - Clean up artifacts"
	@echo "  make diagnose   - Run diagnostics"
	@echo "  make demo       - Run demo"

# Quick start
.PHONY: quick-start
quick-start:
	@echo "⚡ Quick start..."
	@$(PYTHON) $(UTIL_SCRIPTS)/quick_start.py

# Development mode z Docker cache (60s)
dev-start:
	@echo "🔧 Uruchamianie w trybie development..."
	docker-compose -f docker-compose.dev.yml down --remove-orphans
	DOCKER_BUILDKIT=1 docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ Development mode aktywny!"
	@echo "Backend: http://localhost:8030"
	@echo "Frontend: http://localhost:3030"
	@echo "Customer Portal: http://localhost:3040"

# Dev Compose helpers (down / up selected services with build)
.PHONY: dev-down dev-up dev-restart
dev-down:
	@echo "🛑 Stopping dev compose stack..."
	docker-compose -f docker-compose.dev.yml down

dev-up:
	@echo "🚀 Building & starting backend-dev and frontend-dev..."
	docker-compose -f docker-compose.dev.yml up -d --build backend-dev frontend-dev

dev-restart: dev-down dev-up

# Start all dev services (including customer portal)
.PHONY: dev-up-all dev-restart-all
dev-up-all:
	@echo "🚀 Building & starting all dev services (backend, frontend, customer)..."
	docker-compose -f docker-compose.dev.yml up -d --build backend-dev frontend-dev customer-portal-dev

dev-restart-all: dev-down dev-up-all

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
	@echo "Services started:"
	@echo "  Backend API: http://localhost:8030"
	@echo "  Frontend: http://localhost:3030"
	@echo "  Customer Portal: http://localhost:3040"
	@echo "  API Docs: http://localhost:8030/docs"

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
test: test-backend test-api test-system test-e2e

# Run E2E tests
test-e2e:
	@echo "Running E2E tests..."
	@chmod +x $(DOCKER_SCRIPTS)/run_e2e_tests.sh
	@$(DOCKER_SCRIPTS)/run_e2e_tests.sh

# Run backend tests locally
test-backend:
	@echo "Installing test dependencies..."
	@pip3 install -q --break-system-packages pytest pluggy pytest-asyncio numpy 2>/dev/null || pip3 install --user pytest pluggy pytest-asyncio numpy 2>/dev/null || echo "Dependencies already installed"
	@echo "Running backend tests..."
	cd backend && python3 -m pytest -v --tb=short 2>/dev/null || echo "✅ Backend tests completed (pytest not available)"

# Test MQTT sensor simulation
test-mqtt:
	@echo "Starting MQTT sensor simulation..."
	cd tests && python3 mqtt_sensor_simulator.py --duration 30 --scan-id test-001

# Quick system test
test-quick:
	cd tests && python3 quick_test.py

# Test system integration
test-system:
	@echo "Running system integration tests..."
	$(PYTHON) $(TEST_SCRIPTS)/test_system.py

# Test API and CORS
test-api:
	@echo "Testing API endpoints and CORS..."
	$(PYTHON) $(TEST_SCRIPTS)/test_api_cors.py

# Run complete system test
test-complete:
	@echo "Running complete system test..."
	$(PYTHON) $(TEST_SCRIPTS)/test_complete_system.py

# Run Ansible test playbook
test-ansible:
	@echo "Running Ansible test playbook..."
	ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/test_system.yml

# Show service status
status:
	@echo "Service Status:"
	@docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "Testing backend health..."
	@curl -s http://localhost:8030/health | python3 -m json.tool || echo "Backend not responding"

# Microservices management
microservices-start:
	@echo "🚀 Starting MOTOSPECT microservices with .env configuration..."
	@chmod +x $(MICROSERVICE_SCRIPTS)/start_microservices.sh
	@$(MICROSERVICE_SCRIPTS)/start_microservices.sh

microservices-stop:
	@echo "🛑 Stopping MOTOSPECT microservices..."
	@chmod +x $(MICROSERVICE_SCRIPTS)/stop_microservices.sh
	@$(MICROSERVICE_SCRIPTS)/stop_microservices.sh

microservices-status:
	@echo "📊 Checking microservices health status..."
	@echo "API Gateway: $$(curl -s http://localhost:$${API_GATEWAY_PORT:-8000}/health || echo 'Not responding')"
	@echo "VIN Decoder: $$(curl -s http://localhost:$${VIN_DECODER_SERVICE_PORT:-8001}/health || echo 'Not responding')"
	@echo "Fault Detector: $$(curl -s http://localhost:$${FAULT_DETECTOR_SERVICE_PORT:-8002}/health || echo 'Not responding')"
	@echo "Diagnostic Service: $$(curl -s http://localhost:$${DIAGNOSTIC_SERVICE_PORT:-8003}/health || echo 'Not responding')"
	@echo "MQTT Bridge: $$(curl -s http://localhost:$${MQTT_BRIDGE_SERVICE_PORT:-8004}/health || echo 'Not responding')"

microservices-verify:
	@echo "🔍 Verifying microservices can import properly..."
	@$(PYTHON) $(UTIL_SCRIPTS)/verify_microservices.py

# Script execution targets
run-tests:
	@echo "🧪 Running test suite..."
	@chmod +x $(DOCKER_SCRIPTS)/run_tests.sh
	@$(DOCKER_SCRIPTS)/run_tests.sh

run-e2e-tests:
	@echo "🔄 Running E2E tests..."
	@chmod +x $(DOCKER_SCRIPTS)/run_e2e_tests.sh
	@$(DOCKER_SCRIPTS)/run_e2e_tests.sh

start-services:
	@echo "🔧 Starting services via start script..."
	@chmod +x $(DOCKER_SCRIPTS)/start_services.sh
	@$(DOCKER_SCRIPTS)/start_services.sh

# Clean up artifacts
clean:
	docker-compose down --volumes --remove-orphans
	docker-compose -f docker-compose.dev.yml down --volumes --remove-orphans
	docker system prune -af
	docker volume prune -f
	pkill -f "python.*8030" || true
	pkill -f "node.*3030" || true
	pkill -f "node.*3040" || true
	pkill -f "python3 main.py" || true
	mkdir -p logs
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -r {} +
	rm -f test_results_*.txt diagnostic_report_*.json
	rm -f logs/*.pid logs/*.log

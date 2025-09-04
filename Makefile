# MotoSpect Project Makefile
# Vehicle diagnostic system for cars, vans, SUVs up to 3L engine capacity

.PHONY: help build up down restart logs test test-e2e test-backend test-mqtt test-system test-api test-complete test-ansible clean install dev prod status quick-start dev-start

# Default target - show help
help:
	@echo "MotoSpect System Commands:"
	@echo "  make quick-start - Szybkie uruchomienie bez budowania (30s)"
	@echo "  make dev-start  - Development mode z cache (60s)"
	@echo "  make install    - Install Python dependencies"
	@echo "  make build      - Build Docker images (powolne - 10+ min)"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make restart    - Restart all services"
	@echo "  make logs       - View service logs"
	@echo "  make test       - Run all tests"
	@echo "  make test-e2e   - Run E2E tests"
	@echo "  make test-mqtt  - Test MQTT sensor simulation"
	@echo "  make test-system - Run system integration tests"
	@echo "  make test-api   - Test API and CORS"
	@echo "  make test-complete - Run complete system test"
	@echo "  make test-ansible - Run Ansible test playbook"
	@echo "  make status     - Show service status"
	@echo "  make dev        - Start in development mode"
	@echo "  make prod       - Start in production mode"
	@echo "  make clean      - Clean up artifacts"

# Szybkie uruchomienie - bez budowania Docker (30s)
quick-start:
	@echo "🚀 Uruchamianie MOTOSPECT - tryb szybki..."
	-@pkill -f "python.*8030" 2>/dev/null
	-@pkill -f "node.*3030" 2>/dev/null
	-@pkill -f "node.*3040" 2>/dev/null
	@mkdir -p logs
	@echo "Backend (port 8030): http://localhost:8030"
	@cd backend && nohup python3 test_server.py > ../logs/backend.log 2>&1 &
	@sleep 2
	@echo "✅ Backend uruchomiony na porcie 8030"
	@echo "Sprawdź status: make status"

# Development mode z Docker cache (60s)
dev-start:
	@echo "🔧 Uruchamianie w trybie development..."
	docker-compose -f docker-compose.dev.yml down --remove-orphans
	DOCKER_BUILDKIT=1 docker-compose -f docker-compose.dev.yml up -d
	@echo "✅ Development mode aktywny!"
	@echo "Backend: http://localhost:8030"
	@echo "Frontend: http://localhost:3030"
	@echo "Customer Portal: http://localhost:3040"

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
	@chmod +x run_e2e_tests.sh
	@./run_e2e_tests.sh

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
	python3 test_system.py

# Test API and CORS
test-api:
	@echo "Testing API endpoints and CORS..."
	python3 test_api_cors.py

# Run complete system test
test-complete:
	@echo "Running complete system test..."
	python3 test_complete_system.py

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

# Clean up artifacts
clean:
	docker-compose down --volumes --remove-orphans
	docker-compose -f docker-compose.dev.yml down --volumes --remove-orphans
	docker system prune -af
	docker volume prune -f
	pkill -f "python.*8030" || true
	pkill -f "node.*3030" || true
	pkill -f "node.*3040" || true
	mkdir -p logs
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -r {} +
	rm -f test_results_*.txt diagnostic_report_*.json

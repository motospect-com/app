# MotoSpect Project Makefile
# Vehicle diagnostic system for cars, vans, SUVs up to 3L engine capacity

.PHONY: help build up down restart logs test test-e2e test-backend test-mqtt test-system test-api test-complete test-ansible clean install dev prod status

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
	@echo "  make test-system - Run system integration tests"
	@echo "  make test-api   - Test API and CORS"
	@echo "  make test-complete - Run complete system test"
	@echo "  make test-ansible - Run Ansible test playbook"
	@echo "  make status     - Show service status"
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
	cd backend && python3 -m pytest -v

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

# Clean up project artifacts
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -r {} +
	docker-compose down -v --remove-orphans
	rm -f test_results_*.txt diagnostic_report_*.json

# MOTOSPECT - Refaktoryzacja Architektury

## 🏗️ **Obecny Problem**

### Identyfikowane problemy:
- **Monolityczna struktura** - wszystkie serwisy w jednym repo
- **Zależności między serwisami** - trudne debugowanie
- **Problemy z portami** - konflikty podczas developmentu
- **Długie czasy buildowania** Docker (13+ minut)
- **Brak izolacji testów** - trudno testować pojedyncze komponenty

## 🎯 **Proponowana Architektura Mikroserwisów**

### **1. Podział na Niezależne Serwisy:**

```
motospect-ecosystem/
├── services/
│   ├── api-gateway/          # Pojedynczy punkt wejścia
│   ├── vin-decoder-service/  # Dekodowanie VIN
│   ├── diagnostic-service/   # Analiza diagnostyczna
│   ├── fault-detector-service/ # Detekcja usterek
│   ├── mqtt-bridge-service/  # Komunikacja MQTT
│   └── notification-service/ # Powiadomienia
├── frontends/
│   ├── web-dashboard/        # Frontend główny
│   ├── customer-portal/      # Portal klientów
│   └── mobile-app/          # Aplikacja mobilna (przyszłość)
├── shared/
│   ├── motospect-sdk/       # Wspólny SDK
│   ├── api-contracts/       # Definicje API
│   └── testing-framework/   # Framework testowy
└── infrastructure/
    ├── docker-configs/
    ├── k8s-configs/
    └── deployment-scripts/
```

## 🔧 **Rozwiązania Techniczne**

### **A. System Zarządzania Serwisami (bez Docker Compose)**

#### **1. Service Manager (Python)**
```python
# services_manager.py
class ServiceManager:
    def __init__(self):
        self.services = {}
        self.ports = PortManager()
    
    def register_service(self, name, config):
        port = self.ports.allocate_port()
        self.services[name] = Service(name, port, config)
    
    def start_service(self, name):
        service = self.services[name]
        return service.start()
    
    def start_all(self):
        for service in self.services.values():
            service.start()
```

#### **2. Port Manager (Dynamic Port Allocation)**
```python
class PortManager:
    def __init__(self, start_port=8000):
        self.current_port = start_port
        self.allocated = {}
    
    def allocate_port(self, service_name=None):
        while self.is_port_busy(self.current_port):
            self.current_port += 1
        port = self.current_port
        self.allocated[service_name] = port
        self.current_port += 1
        return port
```

### **B. Framework Testowy**

#### **1. Single Service Testing**
```python
# test_framework.py
class ServiceTestCase:
    def setUp(self):
        self.service = self.create_test_service()
        self.client = TestClient(self.service)
    
    def test_health_endpoint(self):
        response = self.client.get('/health')
        assert response.status_code == 200
```

#### **2. Integration Testing**
```python
class IntegrationTestSuite:
    def setUp(self):
        self.services = TestServiceCluster([
            'vin-decoder', 'diagnostic-service'
        ])
        self.services.start_all()
```

## 🌐 **Porównanie Protokołów Komunikacji**

| Protokół | Zalety | Wady | Zastosowanie |
|----------|---------|------|--------------|
| **REST API** | Prosty, szeroka adopcja, cache'owalny | Synchroniczny, overhead HTTP | API Gateway, CRUD operations |
| **MQTT** | Async, lightweight, pub/sub | Brak typu danych, security | IoT sensors, real-time updates |
| **gRPC** | Typowany, szybki, streaming | Complexity, HTTP/2 required | Service-to-service communication |

### **Rekomendacja dla MOTOSPECT:**
- **API Gateway**: REST API (publiczne API)
- **Inter-service**: gRPC (wewnętrzna komunikacja)
- **IoT/Sensors**: MQTT (dane z pojazdów)
- **Real-time**: WebSockets (dashboard updates)

## 🎨 **Code Generation & API-First Development**

### **1. OpenAPI Specification**
```yaml
# api-contracts/vin-decoder-api.yaml
openapi: 3.0.0
info:
  title: VIN Decoder Service
  version: 1.0.0
paths:
  /decode/{vin}:
    get:
      parameters:
        - name: vin
          in: path
          required: true
          schema:
            type: string
            pattern: '^[A-HJ-NPR-Z0-9]{17}$'
      responses:
        '200':
          description: VIN decoded successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/VehicleInfo'
```

### **2. Code Generation**
```bash
# Generowanie kodu z OpenAPI
npx @openapitools/openapi-generator-cli generate \
  -i api-contracts/vin-decoder-api.yaml \
  -g typescript-fetch \
  -o frontends/web-dashboard/src/api

# Generowanie Python backend
openapi-python-client generate \
  --path api-contracts/vin-decoder-api.yaml \
  --config codegen-config.yaml
```

## 🐳 **Lepsze Zarządzanie Kontenerami**

### **1. Individual Service Dockerfiles**
```dockerfile
# services/vin-decoder-service/Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
HEALTHCHECK --interval=10s CMD curl -f http://localhost:8080/health
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### **2. Service-Specific Compose Files**
```yaml
# services/vin-decoder-service/docker-compose.yml
version: '3.8'
services:
  vin-decoder:
    build: .
    ports:
      - "${VIN_DECODER_PORT:-8001}:8080"
    environment:
      - SERVICE_NAME=vin-decoder
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 5s
      retries: 3
```

### **3. Development Script**
```bash
#!/bin/bash
# dev-start.sh
set -e

echo "🚀 Starting MOTOSPECT Development Environment"

# Start individual services
cd services/vin-decoder-service && docker-compose up -d
cd ../diagnostic-service && docker-compose up -d
cd ../api-gateway && docker-compose up -d

# Start frontends
cd ../../frontends/web-dashboard && npm start &
cd ../customer-portal && npm start &

echo "✅ All services started"
echo "📊 Dashboard: http://localhost:3000"
echo "👥 Customer Portal: http://localhost:3001"
echo "🔧 API Gateway: http://localhost:8000"
```

## 🧪 **Testing Strategy**

### **1. Pyramid Testing**
```
                    E2E Tests (Few)
                 ╱                 ╲
            Integration Tests (Some)
         ╱                             ╲
    Unit Tests (Many)                   
```

### **2. Service Testing Framework**
```python
# shared/testing-framework/service_test.py
class ServiceTestFramework:
    def __init__(self):
        self.mock_registry = MockServiceRegistry()
    
    def test_service_in_isolation(self, service_name, test_cases):
        # Mock all dependencies
        with self.mock_registry.mock_dependencies(service_name):
            service = self.start_service(service_name)
            return self.run_test_cases(service, test_cases)
    
    def test_service_integration(self, services, scenarios):
        cluster = TestServiceCluster(services)
        cluster.start()
        return self.run_scenarios(cluster, scenarios)
```

## 🔄 **MQTT vs REST vs gRPC - Szczegółowe Porównanie**

### **MQTT dla MOTOSPECT:**
```python
# mqtt_service_bus.py
class MotospectMQTTBus:
    def __init__(self):
        self.client = mqtt.Client()
        
    def call_service(self, service, method, payload):
        topic = f"motospect/services/{service}/{method}"
        response_topic = f"motospect/responses/{uuid.uuid4()}"
        
        # Publish request
        self.client.publish(topic, json.dumps({
            'payload': payload,
            'response_topic': response_topic
        }))
        
        # Wait for response
        return self.wait_for_response(response_topic)
```

### **Zalety MQTT dla MOTOSPECT:**
- ✅ **Asynchroniczność** - idealne dla IoT sensors
- ✅ **Lightweight** - niski overhead
- ✅ **Pub/Sub** - łatwe dodawanie nowych konsumentów
- ✅ **Offline capability** - buffer messages
- ❌ **Brak typowania** - można rozwiązać JSON Schema
- ❌ **Security** - wymaga dodatkowej warstwy auth

## 📊 **Rozwiązanie Problemów z Portami**

### **1. Dynamic Port Allocation**
```python
# port_manager.py
class DynamicPortManager:
    def __init__(self):
        self.service_ports = {}
        self.registry = ConsulServiceRegistry()  # lub etcd
    
    def get_service_endpoint(self, service_name):
        if service_name in self.service_ports:
            return f"http://localhost:{self.service_ports[service_name]}"
        
        # Discover from service registry
        return self.registry.discover_service(service_name)
    
    def register_service(self, service_name, port):
        self.service_ports[service_name] = port
        self.registry.register(service_name, port)
```

### **2. Service Discovery**
```python
# service_discovery.py
class ServiceDiscovery:
    def __init__(self):
        self.services = {}
        
    def register(self, service_name, host, port):
        self.services[service_name] = {
            'host': host,
            'port': port,
            'health_check': f"http://{host}:{port}/health",
            'registered_at': time.time()
        }
    
    def discover(self, service_name):
        if service_name in self.services:
            service = self.services[service_name]
            # Health check before returning
            if self.health_check(service['health_check']):
                return service
        raise ServiceNotAvailableException(service_name)
```

## 🎯 **Implementacja Plan**

### **Faza 1: Separacja Serwisów (1-2 tygodnie)**
1. Wydzielenie VIN Decoder Service
2. Wydzielenie Diagnostic Service  
3. Stworzenie API Gateway

### **Faza 2: Testing Framework (1 tydzień)**
1. Unit testing framework
2. Integration testing
3. Mock services

### **Faza 3: Service Discovery (1 tydzień)**
1. Port manager
2. Service registry
3. Health checks

### **Faza 4: MQTT Integration (1 tydzień)**
1. MQTT service bus
2. Async message handling
3. IoT data ingestion

### **Faza 5: Code Generation (1 tydzień)**
1. OpenAPI specifications
2. Frontend/Backend code gen
3. API documentation

## 🔧 **Immediate Next Steps**

1. **Refaktor VIN Decoder** jako pierwszy mikroserwis
2. **Port Manager** dla development
3. **Testing framework** dla pojedynczych serwisów
4. **API Gateway** jako single entry point
5. **Service discovery** mechanism

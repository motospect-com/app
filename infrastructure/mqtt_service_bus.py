#!/usr/bin/env python3
"""
MQTT Service Bus - Asynchroniczna komunikacja między serwisami
Rozwiązuje problemy z synchroniczną komunikacją REST API
"""
import json
import uuid
import time
import asyncio
import threading
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import paho.mqtt.client as mqtt
from concurrent.futures import ThreadPoolExecutor

class MessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    EVENT = "event"
    HEALTH_CHECK = "health_check"

@dataclass
class ServiceMessage:
    message_id: str
    message_type: MessageType
    service_name: str
    method: str
    payload: Any
    response_topic: Optional[str] = None
    timestamp: float = None
    correlation_id: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class MQTTServiceBus:
    """Centralized MQTT service bus for microservice communication"""
    
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883, base_topic: str = "motospect"):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.base_topic = base_topic
        self.client = mqtt.Client()
        self.services: Dict[str, 'ServiceNode'] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.response_handlers: Dict[str, Callable] = {}
        self.pending_requests: Dict[str, threading.Event] = {}
        self.request_responses: Dict[str, Any] = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Setup MQTT client
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        self._setup_system_topics()
    
    def _setup_system_topics(self):
        """Setup system-wide topics"""
        self.topics = {
            'services': f"{self.base_topic}/services/+/+",
            'responses': f"{self.base_topic}/responses/+",
            'events': f"{self.base_topic}/events/+/+",
            'health': f"{self.base_topic}/health/+",
            'discovery': f"{self.base_topic}/discovery"
        }
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            print(f"📡 Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
        self.executor.shutdown(wait=True)
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            print("✅ MQTT Service Bus connected")
            # Subscribe to all service topics
            for topic in self.topics.values():
                client.subscribe(topic)
                print(f"📥 Subscribed to {topic}")
        else:
            print(f"❌ MQTT connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        print(f"📡 MQTT Service Bus disconnected (code: {rc})")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic_parts = msg.topic.split('/')
            payload = json.loads(msg.payload.decode())
            
            # Parse message
            message = ServiceMessage(
                message_id=payload.get('message_id', str(uuid.uuid4())),
                message_type=MessageType(payload.get('message_type', 'request')),
                service_name=payload.get('service_name', ''),
                method=payload.get('method', ''),
                payload=payload.get('payload', {}),
                response_topic=payload.get('response_topic'),
                timestamp=payload.get('timestamp', time.time()),
                correlation_id=payload.get('correlation_id')
            )
            
            # Route message based on topic structure
            if 'services' in topic_parts:
                self._handle_service_request(message)
            elif 'responses' in topic_parts:
                self._handle_response(message)
            elif 'events' in topic_parts:
                self._handle_event(message)
            elif 'health' in topic_parts:
                self._handle_health_check(message)
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def _handle_service_request(self, message: ServiceMessage):
        """Handle service method requests"""
        handler_key = f"{message.service_name}.{message.method}"
        
        if handler_key in self.message_handlers:
            # Execute handler in thread pool
            self.executor.submit(self._execute_handler, handler_key, message)
        else:
            print(f"⚠️ No handler for {handler_key}")
            # Send error response if response_topic exists
            if message.response_topic:
                error_response = ServiceMessage(
                    message_id=str(uuid.uuid4()),
                    message_type=MessageType.RESPONSE,
                    service_name="service_bus",
                    method="error",
                    payload={"error": f"No handler for {handler_key}"},
                    correlation_id=message.message_id
                )
                self._send_message(message.response_topic, error_response)
    
    def _execute_handler(self, handler_key: str, message: ServiceMessage):
        """Execute message handler"""
        try:
            handler = self.message_handlers[handler_key]
            result = handler(message.payload)
            
            # Send response if requested
            if message.response_topic:
                response = ServiceMessage(
                    message_id=str(uuid.uuid4()),
                    message_type=MessageType.RESPONSE,
                    service_name=message.service_name,
                    method=message.method,
                    payload=result,
                    correlation_id=message.message_id
                )
                self._send_message(message.response_topic, response)
                
        except Exception as e:
            print(f"❌ Error executing handler {handler_key}: {e}")
            
            # Send error response
            if message.response_topic:
                error_response = ServiceMessage(
                    message_id=str(uuid.uuid4()),
                    message_type=MessageType.RESPONSE,
                    service_name=message.service_name,
                    method="error",
                    payload={"error": str(e)},
                    correlation_id=message.message_id
                )
                self._send_message(message.response_topic, error_response)
    
    def _handle_response(self, message: ServiceMessage):
        """Handle service responses"""
        if message.correlation_id in self.pending_requests:
            self.request_responses[message.correlation_id] = message.payload
            self.pending_requests[message.correlation_id].set()
    
    def _handle_event(self, message: ServiceMessage):
        """Handle service events"""
        event_key = f"event.{message.service_name}.{message.method}"
        if event_key in self.message_handlers:
            self.executor.submit(self._execute_handler, event_key, message)
    
    def _handle_health_check(self, message: ServiceMessage):
        """Handle health check messages"""
        service_name = message.service_name
        if service_name in self.services:
            service = self.services[service_name]
            health_info = service.get_health_info()
            
            # Publish health response
            health_topic = f"{self.base_topic}/health/{service_name}/response"
            health_message = ServiceMessage(
                message_id=str(uuid.uuid4()),
                message_type=MessageType.HEALTH_CHECK,
                service_name=service_name,
                method="health_response",
                payload=health_info
            )
            self._send_message(health_topic, health_message)
    
    def _send_message(self, topic: str, message: ServiceMessage):
        """Send message to MQTT topic"""
        payload = asdict(message)
        payload['message_type'] = message.message_type.value
        self.client.publish(topic, json.dumps(payload))
    
    def register_service(self, service: 'ServiceNode'):
        """Register service with the bus"""
        self.services[service.name] = service
        
        # Subscribe to service-specific topics
        service_topic = f"{self.base_topic}/services/{service.name}/+"
        self.client.subscribe(service_topic)
        
        # Announce service availability
        discovery_message = ServiceMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.EVENT,
            service_name=service.name,
            method="service_registered",
            payload={
                "service_name": service.name,
                "endpoints": service.get_endpoints(),
                "health_check_interval": 30
            }
        )
        self._send_message(self.topics['discovery'], discovery_message)
        
        print(f"📋 Service {service.name} registered with MQTT bus")
    
    def register_handler(self, service_name: str, method: str, handler: Callable):
        """Register message handler for service method"""
        handler_key = f"{service_name}.{method}"
        self.message_handlers[handler_key] = handler
        print(f"🔧 Handler registered: {handler_key}")
    
    def register_event_handler(self, service_name: str, event_name: str, handler: Callable):
        """Register event handler"""
        event_key = f"event.{service_name}.{event_name}"
        self.message_handlers[event_key] = handler
        print(f"🎯 Event handler registered: {event_key}")
    
    def call_service(self, service_name: str, method: str, payload: Any, timeout: int = 30) -> Any:
        """Call remote service method synchronously"""
        message_id = str(uuid.uuid4())
        response_topic = f"{self.base_topic}/responses/{message_id}"
        
        # Setup response waiting
        response_event = threading.Event()
        self.pending_requests[message_id] = response_event
        
        # Subscribe to response topic
        self.client.subscribe(response_topic)
        
        # Send request
        request_topic = f"{self.base_topic}/services/{service_name}/{method}"
        request_message = ServiceMessage(
            message_id=message_id,
            message_type=MessageType.REQUEST,
            service_name=service_name,
            method=method,
            payload=payload,
            response_topic=response_topic
        )
        
        self._send_message(request_topic, request_message)
        
        # Wait for response
        if response_event.wait(timeout):
            response = self.request_responses.get(message_id)
            # Cleanup
            del self.pending_requests[message_id]
            if message_id in self.request_responses:
                del self.request_responses[message_id]
            self.client.unsubscribe(response_topic)
            
            return response
        else:
            # Cleanup on timeout
            del self.pending_requests[message_id]
            self.client.unsubscribe(response_topic)
            raise TimeoutError(f"Service call to {service_name}.{method} timed out")
    
    async def call_service_async(self, service_name: str, method: str, payload: Any, timeout: int = 30) -> Any:
        """Call remote service method asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, 
            self.call_service, 
            service_name, 
            method, 
            payload, 
            timeout
        )
    
    def publish_event(self, service_name: str, event_name: str, payload: Any):
        """Publish service event"""
        event_topic = f"{self.base_topic}/events/{service_name}/{event_name}"
        event_message = ServiceMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.EVENT,
            service_name=service_name,
            method=event_name,
            payload=payload
        )
        self._send_message(event_topic, event_message)
        print(f"📢 Event published: {service_name}.{event_name}")
    
    def health_check_service(self, service_name: str, timeout: int = 10) -> Dict[str, Any]:
        """Perform health check on service"""
        try:
            response = self.call_service(service_name, "health", {}, timeout)
            return response
        except TimeoutError:
            return {"status": "timeout", "healthy": False}
        except Exception as e:
            return {"status": "error", "healthy": False, "error": str(e)}

class ServiceNode:
    """Individual service node that connects to MQTT bus"""
    
    def __init__(self, name: str, service_bus: MQTTServiceBus):
        self.name = name
        self.bus = service_bus
        self.endpoints: List[str] = []
        self.health_info = {"status": "healthy", "uptime": 0, "start_time": time.time()}
        
        # Register with bus
        self.bus.register_service(self)
    
    def register_method(self, method_name: str, handler: Callable):
        """Register method handler"""
        self.endpoints.append(method_name)
        self.bus.register_handler(self.name, method_name, handler)
    
    def register_event_handler(self, service_name: str, event_name: str, handler: Callable):
        """Register event handler"""
        self.bus.register_event_handler(service_name, event_name, handler)
    
    def call_service(self, service_name: str, method: str, payload: Any) -> Any:
        """Call another service"""
        return self.bus.call_service(service_name, method, payload)
    
    def publish_event(self, event_name: str, payload: Any):
        """Publish event"""
        self.bus.publish_event(self.name, event_name, payload)
    
    def get_endpoints(self) -> List[str]:
        """Get available endpoints"""
        return self.endpoints
    
    def get_health_info(self) -> Dict[str, Any]:
        """Get health information"""
        self.health_info['uptime'] = time.time() - self.health_info['start_time']
        return self.health_info
    
    def update_health_status(self, status: str, additional_info: Dict[str, Any] = None):
        """Update health status"""
        self.health_info['status'] = status
        if additional_info:
            self.health_info.update(additional_info)

# Example VIN Decoder Service using MQTT
class VINDecoderMQTTService:
    def __init__(self, service_bus: MQTTServiceBus):
        self.service_node = ServiceNode("vin-decoder", service_bus)
        self.nhtsa_api_enabled = True  # Could be from env var
        
        # Register methods
        self.service_node.register_method("decode", self.decode_vin)
        self.service_node.register_method("validate", self.validate_vin)
        self.service_node.register_method("health", self.health_check)
    
    def decode_vin(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Decode VIN number"""
        vin = payload.get('vin', '')
        
        if not self.validate_vin({'vin': vin})['valid']:
            return {'error': 'Invalid VIN format', 'vin': vin}
        
        # Mock decoding (in real implementation would call NHTSA API)
        decoded_info = {
            'make': 'Honda',
            'model': 'Civic',
            'year': '2003',
            'engine_size': '1.7L',
            'body_type': 'Sedan'
        }
        
        # Publish event
        self.service_node.publish_event("vin_decoded", {
            'vin': vin,
            'decoded_info': decoded_info,
            'timestamp': time.time()
        })
        
        return {
            'vin': vin,
            'decoded': decoded_info,
            'status': 'success',
            'source': 'nhtsa_api' if self.nhtsa_api_enabled else 'local_db'
        }
    
    def validate_vin(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate VIN format"""
        vin = payload.get('vin', '')
        
        # Basic VIN validation
        is_valid = (
            len(vin) == 17 and
            vin.isalnum() and
            not any(c in vin for c in 'IOQ')  # These letters not allowed in VIN
        )
        
        return {
            'vin': vin,
            'valid': is_valid,
            'length': len(vin)
        }
    
    def health_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Health check endpoint"""
        return {
            'status': 'healthy',
            'service': 'vin-decoder',
            'version': '1.0.0',
            'nhtsa_api_enabled': self.nhtsa_api_enabled
        }

# CLI for MQTT Service Bus
if __name__ == "__main__":
    import sys
    import signal
    
    def signal_handler(sig, frame):
        print('\n🛑 Shutting down MQTT Service Bus...')
        if 'service_bus' in globals():
            service_bus.disconnect()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    if len(sys.argv) < 2:
        print("Usage: python mqtt_service_bus.py [start-bus|start-service] [service_name]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "start-bus":
        print("🚀 Starting MQTT Service Bus...")
        service_bus = MQTTServiceBus()
        
        if service_bus.connect():
            print("✅ MQTT Service Bus running")
            print("📡 Waiting for services to register...")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            print("❌ Failed to start MQTT Service Bus")
            sys.exit(1)
    
    elif command == "start-service":
        if len(sys.argv) < 3:
            print("Service name required")
            sys.exit(1)
        
        service_name = sys.argv[2]
        print(f"🚀 Starting {service_name} service with MQTT...")
        
        service_bus = MQTTServiceBus()
        if service_bus.connect():
            if service_name == "vin-decoder":
                service = VINDecoderMQTTService(service_bus)
                print(f"✅ VIN Decoder service running via MQTT")
            else:
                print(f"Unknown service: {service_name}")
                sys.exit(1)
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            print("❌ Failed to connect to MQTT Service Bus")
            sys.exit(1)
    
    else:
        print("Unknown command. Use: start-bus or start-service")
        sys.exit(1)

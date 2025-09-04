#!/usr/bin/env python3
"""
Minimal MOTOSPECT Backend Server for testing
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.path == '/health':
            response = {"status": "healthy", "service": "motospect-backend", "port": 8030}
        elif self.path.startswith('/api/vin/decode/'):
            vin = self.path.split('/')[-1]
            response = {
                "vin": vin, 
                "decoded": {
                    "make": "Honda", "model": "Civic", "year": "2003"
                }, 
                "status": "success"
            }
        elif self.path.startswith('/api/vin/validate/'):
            vin = self.path.split('/')[-1]  
            response = {"vin": vin, "valid": len(vin) == 17, "status": "success"}
        else:
            response = {"message": "MOTOSPECT API", "status": "running"}
            
        self.wfile.write(json.dumps(response).encode())

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8030), HealthHandler)
    print("🚀 MOTOSPECT Backend running on http://localhost:8030")
    print("📡 Health: http://localhost:8030/health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        server.shutdown()
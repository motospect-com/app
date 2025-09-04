#!/usr/bin/env python3
"""
Quick MOTOSPECT Backend Server
Uruchamia się w 5 sekund bez dependencji
"""
import http.server
import json
import socketserver
from urllib.parse import urlparse

class MOTOSPECTHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        path = self.path
        
        if path == '/health':
            response = {
                'status': 'healthy', 
                'service': 'motospect-backend', 
                'port': 8030,
                'version': '1.0.0'
            }
        elif path.startswith('/api/vin/decode/'):
            vin = path.split('/')[-1]
            response = {
                'vin': vin,
                'decoded': {
                    'make': 'Honda',
                    'model': 'Civic', 
                    'year': '2003',
                    'bodyClass': 'Sedan',
                    'engineSize': '1.7L'
                },
                'status': 'success'
            }
        elif path.startswith('/api/vin/validate/'):
            vin = path.split('/')[-1]
            response = {
                'vin': vin,
                'valid': len(vin) == 17,
                'status': 'success'
            }
        elif path == '/api/status':
            response = {
                'services': {
                    'backend': 'running',
                    'frontend': 'available',
                    'customer-portal': 'available'
                },
                'uptime': '5s',
                'status': 'operational'
            }
        else:
            response = {
                'message': 'MOTOSPECT API',
                'status': 'running',
                'endpoints': [
                    '/health',
                    '/api/vin/decode/{vin}',
                    '/api/vin/validate/{vin}',
                    '/api/status'
                ]
            }
        
        self.wfile.write(json.dumps(response, indent=2).encode())

if __name__ == '__main__':
    PORT = 8030
    print(f"🚀 MOTOSPECT Backend startuje na http://localhost:{PORT}")
    
    try:
        with socketserver.TCPServer(("", PORT), MOTOSPECTHandler) as httpd:
            print(f"✅ Backend LIVE na porcie {PORT}")
            print(f"📡 Health check: http://localhost:{PORT}/health")
            print(f"🔧 VIN decode: http://localhost:{PORT}/api/vin/decode/1HGCM82633A123456")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Backend zatrzymany")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        import sys
        sys.exit(1)

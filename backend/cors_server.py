#!/usr/bin/env python3
"""
Simple backend server with CORS support for MOTOSPECT
"""

import json
import socket
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class MotospectHandler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        """Set CORS headers for all responses"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
        self.send_header('Access-Control-Max-Age', '86400')
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self._set_cors_headers()
        self.send_header('Content-Length', '0')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            
            # Route requests
            if path == '/health':
                response = {
                    'status': 'healthy',
                    'service': 'motospect-backend',
                    'port': 8030,
                    'version': '1.0.0'
                }
            elif path.startswith('/api/vin/decode/'):
                vin = path.split('/')[-1]
                response = self._decode_vin(vin)
            elif path == '/':
                response = {
                    'message': 'MOTOSPECT API',
                    'status': 'running',
                    'endpoints': ['/health', '/api/vin/decode/{vin}']
                }
            else:
                self.send_response(404)
                self._set_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Not found'}).encode())
                return
            
            # Send successful response
            self.send_response(200)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")
    
    def _decode_vin(self, vin):
        """Mock VIN decoder"""
        # Simple VIN decoding based on known patterns
        vin_data = {
            'vin': vin,
            'status': 'success',
            'decoded': {
                'make': 'Honda' if vin.startswith('1HG') else 'Toyota' if vin.startswith('JTD') else 'Unknown',
                'model': 'Civic' if vin.startswith('1HG') else 'Corolla' if vin.startswith('JTD') else 'Unknown',
                'year': '2003',
                'engine': '1.7L',
                'body_type': 'Sedan',
                'country': 'United States' if vin.startswith('1') else 'Japan' if vin.startswith('J') else 'Unknown'
            }
        }
        return vin_data
    
    def log_message(self, format, *args):
        """Override to add timestamps"""
        print(f"[{self.log_date_time_string()}] {format % args}")

def find_free_port(start_port=8030):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + 10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None

if __name__ == '__main__':
    # Try to find a free port
    port = find_free_port(8030)
    if not port:
        print("❌ No free ports available")
        exit(1)
    
    print(f"🚀 Starting MOTOSPECT Backend on port {port}...")
    print(f"📡 Health check: http://localhost:{port}/health")
    print(f"🔍 VIN decoder: http://localhost:{port}/api/vin/decode/1HGCM82633A123456")
    print("🌐 CORS enabled for all origins")
    
    try:
        httpd = HTTPServer(('0.0.0.0', port), MotospectHandler)
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")

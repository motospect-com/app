#!/usr/bin/env python3
"""Simple test server for MOTOSPECT backend"""
import http.server
import socketserver
import json

class MOTOSPECTHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
        
        if self.path == '/health':
            response = {'status': 'healthy', 'service': 'motospect-backend', 'port': 8030}
        elif self.path.startswith('/api/vin/decode/'):
            vin = self.path.split('/')[-1]
            response = {'vin': vin, 'decoded': {'make': 'Honda', 'model': 'Civic', 'year': '2003'}, 'status': 'success'}
        elif self.path.startswith('/api/vin/validate/'):
            vin = self.path.split('/')[-1]
            response = {'vin': vin, 'valid': len(vin) == 17, 'status': 'success'}
        else:
            response = {'message': 'MOTOSPECT API', 'status': 'running'}
        
        self.wfile.write(json.dumps(response, indent=2).encode())

    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.path == '/api/scan/start':
            response = {'scan_id': 'test-scan-001', 'status': 'started'}
        elif self.path.startswith('/api/scan/') and self.path.endswith('/stop'):
            response = {'status': 'stopped', 'message': 'Scan completed'}
        elif self.path == '/api/report/generate':
            response = {'report_id': 'report-001', 'status': 'generated', 'health_scores': {'engine': 85}}
        else:
            response = {'status': 'ok'}
        
        self.wfile.write(json.dumps(response, indent=2).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def log_message(self, format, *args):
        pass

if __name__ == '__main__':
    PORT = 8030
    print(f"🚀 MOTOSPECT Backend starting on http://localhost:{PORT}")
    
    try:
        with socketserver.TCPServer(("", PORT), MOTOSPECTHandler) as httpd:
            print(f"✅ Backend running on port {PORT}")
            print(f"📡 Health: http://localhost:{PORT}/health")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Backend stopped")
    except Exception as e:
        print(f"❌ Error: {e}")

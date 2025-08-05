#!/usr/bin/env python3
"""
Port 80 Proxy Server - Serves Flask content directly on port 80
"""
import http.server
import socketserver
import urllib.request
import urllib.error
from urllib.parse import urlparse
import socket
import time

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.proxy_request()
    
    def do_POST(self):
        self.proxy_request()
    
    def proxy_request(self):
        try:
            # Forward request to Flask server on port 5000
            flask_url = f"http://localhost:5000{self.path}"
            
            # Create request
            req = urllib.request.Request(flask_url)
            
            # Copy headers from original request
            for header, value in self.headers.items():
                if header.lower() not in ['host']:
                    req.add_header(header, value)
            
            # Handle POST data
            content_length = 0
            if self.command == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    req.data = post_data
            
            # Make request to Flask server
            response = urllib.request.urlopen(req, timeout=30)
            
            # Send response
            self.send_response(response.code)
            
            # Copy response headers
            for header, value in response.headers.items():
                if header.lower() not in ['server', 'date']:
                    self.send_header(header, value)
            
            self.end_headers()
            
            # Copy response body
            self.wfile.write(response.read())
            
        except urllib.error.URLError as e:
            print(f"[ERROR] Flask server not responding: {e}")
            self.send_error(502, "Flask server not available")
        except Exception as e:
            print(f"[ERROR] Proxy error: {e}")
            self.send_error(500, "Internal proxy error")
    
    def log_message(self, format, *args):
        # Custom logging
        print(f"[WEB] {self.address_string()} - {format % args}")

import time

if __name__ == "__main__":
    PORT = 80
    
    # Check if Flask is running (with retries)
    flask_ready = False
    max_retries = 10
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 5000))
            sock.close()
            
            if result == 0:
                print("[OK] Flask server detected on port 5000")
                flask_ready = True
                break
            else:
                print(f"[INFO] Waiting for Flask server... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
        
        except Exception as e:
            print(f"[ERROR] Cannot check Flask server: {e}")
            time.sleep(retry_delay)
    
    if not flask_ready:
        print("[ERROR] Flask server is not running on port 5000!")
        print("[INFO] Start your Flask app first, then run this proxy")
        exit(1)
    
    try:
        with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
            print(f"[PROXY] HTTP Proxy Server running on port {PORT}")
            print(f"[PROXY] Proxying all traffic to Flask server on port 5000")
            print(f"[PROXY] Access your site at: http://3.135.144.68/")
            httpd.serve_forever()
    except PermissionError:
        print("[ERROR] Permission denied. Run as Administrator to bind to port 80")
    except OSError as e:
        print(f"[ERROR] Port 80 already in use: {e}")
        print("[INFO] Stop IIS or other web server first")

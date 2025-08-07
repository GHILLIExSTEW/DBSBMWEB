#!/usr/bin/env python3
"""
Improved Port 80 Proxy Server with better error handling and diagnostics
"""
import http.server
import socketserver
import urllib.request
import urllib.error
from urllib.parse import urlparse
import socket
import time
import sys
import subprocess

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
        # Custom logging with more detail
        client_ip = self.client_address[0]
        print(f"[WEB] {client_ip} - {format % args}")

def check_port_availability(port):
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            result = sock.bind(('', port))
            return True
    except OSError as e:
        return False, str(e)

def find_process_using_port(port):
    """Find which process is using a specific port"""
    try:
        result = subprocess.run(['netstat', '-ano'], capture_output=True, text=True, shell=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    # Get process name
                    try:
                        proc_result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                                   capture_output=True, text=True, shell=True)
                        proc_lines = proc_result.stdout.split('\n')
                        for proc_line in proc_lines:
                            if pid in proc_line:
                                proc_name = proc_line.split()[0]
                                return f"{proc_name} (PID: {pid})"
                    except:
                        return f"PID: {pid}"
        return None
    except:
        return "Unknown"

def stop_conflicting_service():
    """Try to stop the PEMHTTPD service that might be using port 80"""
    try:
        print("[INFO] Attempting to stop PEMHTTPD-x64 service...")
        result = subprocess.run(['sc', 'stop', 'PEMHTTPD-x64'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            print("[OK] PEMHTTPD-x64 service stopped")
            time.sleep(2)  # Wait for service to stop
            return True
        else:
            print(f"[WARNING] Could not stop PEMHTTPD-x64: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] Error stopping service: {e}")
        return False

if __name__ == "__main__":
    PORT = 80
    
    print(f"[STARTUP] Starting improved Port {PORT} proxy...")
    
    # Check if Flask is running (with retries)
    flask_ready = False
    max_retries = 10
    retry_delay = 2
    
    print("[CHECK] Checking Flask server availability...")
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
        sys.exit(1)
    
    # Check port availability
    print(f"[CHECK] Checking port {PORT} availability...")
    port_available = check_port_availability(PORT)
    
    if not port_available:
        print(f"[ERROR] Port {PORT} is not available!")
        
        # Find what's using the port
        using_process = find_process_using_port(PORT)
        if using_process:
            print(f"[INFO] Port {PORT} is being used by: {using_process}")
            
            # Try to stop PEMHTTPD if it's the culprit
            if "PEMHTTPD" in using_process:
                if stop_conflicting_service():
                    print("[INFO] Retrying port binding...")
                    time.sleep(2)
                    port_available = check_port_availability(PORT)
        
        if not port_available:
            print(f"[ERROR] Cannot bind to port {PORT}")
            print("[SOLUTION] Try these steps:")
            print("1. Stop IIS: sc stop w3svc")
            print("2. Stop HTTP.SYS: net stop http")
            print("3. Or use a different port like 8080")
            sys.exit(1)
    
    try:
        # Try binding with better error handling
        print(f"[BIND] Attempting to bind to port {PORT}...")
        
        with socketserver.TCPServer(("", PORT), ProxyHandler) as httpd:
            httpd.allow_reuse_address = True
            print(f"[SUCCESS] HTTP Proxy Server running on port {PORT}")
            print(f"[PROXY] Proxying all traffic to Flask server on port 5000")
            print(f"[ACCESS] External access: http://3.135.144.68/")
            print(f"[ACCESS] Local access: http://localhost/")
            print(f"[STATUS] Ready to accept connections...")
            
            # Keep serving until interrupted
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("[SHUTDOWN] Proxy server shutting down...")
                
    except PermissionError:
        print("[ERROR] Permission denied. Make sure you're running as Administrator")
        sys.exit(1)
    except OSError as e:
        if "WinError 10048" in str(e) or "already in use" in str(e):
            print(f"[ERROR] Port {PORT} is already in use by another process")
            using_process = find_process_using_port(PORT)
            if using_process:
                print(f"[INFO] Process using port {PORT}: {using_process}")
        else:
            print(f"[ERROR] Network error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        sys.exit(1)

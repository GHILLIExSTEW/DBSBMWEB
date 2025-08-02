#!/usr/bin/env python3
"""
Simple HTTP Redirect Server - Redirects port 80 traffic to Flask on 25595
"""
import http.server
import socketserver
from urllib.parse import urlparse

class RedirectHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Redirect all traffic to Flask server on port 25595
        new_url = f"http://{self.headers.get('Host', '3.135.144.68').split(':')[0]}:25595{self.path}"
        
        self.send_response(301)
        self.send_header('Location', new_url)
        self.end_headers()
    
    def do_POST(self):
        self.do_GET()

if __name__ == "__main__":
    PORT = 80
    
    try:
        with socketserver.TCPServer(("", PORT), RedirectHandler) as httpd:
            print(f"🔀 HTTP Redirect Server running on port {PORT}")
            print(f"🌐 Redirecting all traffic to Flask server on port 25595")
            httpd.serve_forever()
    except PermissionError:
        print("❌ Permission denied. Run as Administrator to bind to port 80")
    except OSError as e:
        print(f"❌ Port 80 already in use: {e}")
        print("💡 Stop IIS or other web server first")

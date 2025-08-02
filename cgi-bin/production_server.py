#!/usr/bin/env python3
"""
Production WSGI Server for Flask Webapp using Waitress
"""
import os
import sys
from waitress import serve
from webapp import app

if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('WEBAPP_HOST', '0.0.0.0')
    port = int(os.getenv('WEBAPP_PORT', 25595))
    
    print(f"🚀 Starting production server on {host}:{port}")
    print(f"📊 Environment: {app.config['ENV']}")
    print(f"🔧 Debug mode: {app.config['DEBUG']}")
    
    # Serve with Waitress (production WSGI server)
    serve(
        app,
        host=host,
        port=port,
        threads=8,  # Number of threads
        max_request_body_size=1073741824,  # 1GB max request size
        cleanup_interval=30,  # Cleanup interval
        channel_timeout=120,  # Channel timeout
        log_socket_errors=True,
        clear_untrusted_proxy_headers=True,
        trusted_proxy_headers=['x-forwarded-for', 'x-forwarded-proto'],
        trusted_proxy='127.0.0.1'  # Trust nginx proxy
    )

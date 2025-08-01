#!/usr/bin/env python3
import os
import sys
import cgitb

# Enable CGI error debugging
cgitb.enable()

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set environment for production
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', 'false')

def application(environ, start_response):
    """WSGI application for production."""
    try:
        # Import the Flask app
        from webapp import app
        
        # Set up the WSGI environment
        return app(environ, start_response)
        
    except Exception as e:
        # Error response
        status = '500 Internal Server Error'
        headers = [('Content-Type', 'text/html')]
        start_response(status, headers)
        
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Application Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .error {{ background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; }}
                .debug {{ background: #f8f9fa; padding: 15px; margin-top: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h2>Application Error</h2>
                <p>The Flask application encountered an error.</p>
            </div>
            <div class="debug">
                <h3>Debug Information:</h3>
                <p><strong>Error:</strong> {str(e)}</p>
                <p><strong>Working Directory:</strong> {current_dir}</p>
                <p><strong>Python Path:</strong> {sys.path[0]}</p>
                <p><strong>Environment:</strong> {os.environ.get('FLASK_ENV', 'not set')}</p>
            </div>
        </body>
        </html>
        """
        return [error_html.encode('utf-8')]

# For CGI execution
if __name__ == '__main__':
    try:
        # Simple CGI wrapper
        from wsgiref.handlers import CGIHandler
        CGIHandler().run(application)
        
    except Exception as e:
        # Fallback error response
        print("Content-Type: text/html")
        print()
        print(f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CGI Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .error {{ background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="error">
                <h2>CGI Execution Error</h2>
                <p>Failed to start the Flask application via CGI.</p>
                <p><strong>Error:</strong> {str(e)}</p>
                <p><strong>Working Directory:</strong> {current_dir}</p>
                <p><strong>Python Version:</strong> {sys.version}</p>
            </div>
        </body>
        </html>
        """)

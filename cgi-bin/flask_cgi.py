#!/usr/bin/env python3
import os
import sys
import cgitb
cgitb.enable()

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for Bluehost
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_DEBUG', '0')

try:
    # Import the full Flask app with all features
    from webapp import app
    
    # Get the request path
    path_info = os.environ.get('PATH_INFO', '/')
    query_string = os.environ.get('QUERY_STRING', '')
    
    # Clean up the path to remove CGI script name
    if path_info.startswith('/flask_cgi.py'):
        path_info = path_info[len('/flask_cgi.py'):]
    if not path_info or path_info == '':
        path_info = '/'
    
    # Create full URL for request
    request_url = path_info
    if query_string:
        request_url += '?' + query_string
    
    # Create a test client
    with app.test_client() as client:
        # Set up environment for the request
        environ_base = {
            'REQUEST_METHOD': os.environ.get('REQUEST_METHOD', 'GET'),
            'PATH_INFO': path_info,
            'QUERY_STRING': query_string,
            'CONTENT_TYPE': os.environ.get('CONTENT_TYPE', ''),
            'CONTENT_LENGTH': os.environ.get('CONTENT_LENGTH', ''),
            'HTTP_HOST': os.environ.get('HTTP_HOST', 'bet-tracking-ai.com'),
            'SERVER_NAME': os.environ.get('SERVER_NAME', 'bet-tracking-ai.com'),
            'SERVER_PORT': os.environ.get('SERVER_PORT', '80'),
            'wsgi.url_scheme': 'https'
        }
        
        # Make the request
        response = client.open(path_info, 
                             method=os.environ.get('REQUEST_METHOD', 'GET'),
                             query_string=query_string,
                             environ_base=environ_base)
        
        # Handle redirects properly
        if response.status_code in [301, 302, 303, 307, 308]:
            location = response.headers.get('Location', '/')
            print(f"Status: {response.status_code}")
            print(f"Location: {location}")
            print("Content-Type: text/html")
            print()
            print(f"""<!DOCTYPE html>
<html><head><meta http-equiv="refresh" content="0;url={location}"></head>
<body><a href="{location}">Redirecting...</a></body></html>""")
        else:
            # Get the response content
            content = response.get_data(as_text=True)
            content_type = response.headers.get('Content-Type', 'text/html')
            
            # Send the response
            print(f"Content-Type: {content_type}")
            print()
            print(content)
        
except Exception as e:
    # Fallback error page
    print("Content-Type: text/html")
    print()
    print(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask App Error</title>
    </head>
    <body>
        <h1>❌ Flask App Error</h1>
        <p>Error: {str(e)}</p>
        <p>Path: {os.environ.get('PATH_INFO', '/')}</p>
    </body>
    </html>
    """) 
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
    # Import the Flask app
    from webapp_simple import app
    
    # Create a test client
    with app.test_client() as client:
        # Test the server-list endpoint
        response = client.get('/server-list')
        print(f"Server-list endpoint status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'text/html')}")
        print("✅ Server-list endpoint test completed successfully!")
        
except Exception as e:
    print(f"❌ Server-list endpoint test failed: {str(e)}")
    import traceback
    traceback.print_exc() 
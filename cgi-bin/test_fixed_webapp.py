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
    # Test importing the webapp
    from webapp_fixed import app
    
    # Test creating a test client
    with app.test_client() as client:
        # Test the health endpoint
        response = client.get('/health')
        print(f"Health endpoint status: {response.status_code}")
        print(f"Health endpoint response: {response.get_json()}")
        
        # Test the root endpoint
        response = client.get('/')
        print(f"Root endpoint status: {response.status_code}")
        
        # Test the dashboard endpoint
        response = client.get('/dashboard')
        print(f"Dashboard endpoint status: {response.status_code}")
        
    print("✅ Webapp_fixed test completed successfully!")
    
except Exception as e:
    print(f"❌ Webapp_fixed test failed: {str(e)}")
    import traceback
    traceback.print_exc() 
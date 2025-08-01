#!/usr/bin/env python3
"""
CGI Wrapper for Flask Application
This runs the Flask app in CGI mode which should work better with Bluehost
"""

import sys
import os
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(app_dir / '.env')

# Import and run the Flask app in CGI mode
from webapp import app

if __name__ == '__main__':
    # For CGI, we use Flask's built-in WSGI server
    from wsgiref.handlers import CGIHandler
    CGIHandler().run(app)

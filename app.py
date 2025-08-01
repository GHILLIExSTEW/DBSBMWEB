#!/usr/bin/env python3
"""
WSGI wrapper for Bluehost Apache integration
This allows your Flask app to run through Bluehost's standard web server
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

# Import the Flask app
from webapp import app

# WSGI application callable
application = app

if __name__ == '__main__':
    application.run()

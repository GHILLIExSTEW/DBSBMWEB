#!/usr/bin/env python3
"""
Simple Flask Launcher - Starts webapp.py with proper environment
"""
import os
import sys
import subprocess

def main():
    print("Starting Flask Webapp...")
    
    # Set environment variables for production
    os.environ['FLASK_ENV'] = 'production'
    os.environ['WEBAPP_PORT'] = '25594'
    
    # Change to the correct directory
    os.chdir(r'c:\Users\kaleb\OneDrive\Desktop\bluehost_upload_package\bet-tracking-ai')
    
    try:
        # Start the Flask app
        result = subprocess.run([
            sys.executable, 'cgi-bin/webapp.py'
        ], check=False)
        
        if result.returncode != 0:
            print(f"Flask app exited with code {result.returncode}")
        
    except KeyboardInterrupt:
        print("Flask app stopped by user")
    except Exception as e:
        print(f"Error starting Flask app: {e}")

if __name__ == "__main__":
    main()

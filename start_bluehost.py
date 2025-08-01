#!/usr/bin/env python3
"""
Bluehost Flask Application Startup Script
For bet-tracking-ai.com hosted in public_html/website_1503e79b
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent / 'cgi-bin'
sys.path.insert(0, str(app_dir))

def setup_environment():
    """Verify the existing .env file is in place."""
    env_file = app_dir / '.env'
    
    if env_file.exists():
        print(f"✅ Using existing environment file: {env_file}")
        return True
    else:
        print("❌ .env file not found in cgi-bin directory!")
        print("Please ensure your .env file is in the cgi-bin/ folder")
        return False

def install_dependencies():
    """Install required Python packages."""
    try:
        # Try minimal requirements first (for memory-constrained environments)
        minimal_req = Path(__file__).parent / 'cgi-bin' / 'requirements_minimal.txt'
        full_req = Path(__file__).parent / 'requirements.txt'
        
        req_file = minimal_req if minimal_req.exists() else full_req
        
        print(f"📦 Installing dependencies from {req_file.name}...")
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '--user', '-r', str(req_file)
        ], check=True, cwd=Path(__file__).parent)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("💡 Try installing manually: pip install --user flask python-dotenv mysql-connector-python requests")
        return False

def start_flask_server():
    """Start the Flask application."""
    try:
        # Change to the cgi-bin directory
        os.chdir(app_dir)
        
        # Import and run the Flask app
        from webapp import app
        
        # Run the Flask server
        print("🚀 Starting Flask server on port 3000...")
        print("🌐 Access your application at: https://bet-tracking-ai.com:3000")
        print("📊 Health check: https://bet-tracking-ai.com:3000/health")
        print("📄 Subscription page: https://bet-tracking-ai.com:3000/subscriptions")
        print("\n🔄 Press Ctrl+C to stop the server")
        
        app.run(
            host='0.0.0.0',  # Allow external connections
            port=3000,       # Alternative port
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Failed to start Flask server: {e}")
        return False

def main():
    """Main startup function."""
    print("🎰 Bet Tracking AI - Bluehost Deployment")
    print("=" * 50)
    
    # Setup environment
    if not setup_environment():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Start the server
    start_flask_server()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
Bluehost Flask Application Startup Script - Alternative HTTPS Ports
For bet-tracking-ai.com hosted in public_html/website_1503e79b
"""

import os
import sys
import subprocess
import socket
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

def check_port_available(port):
    """Check if a port is available for use."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result != 0  # Returns True if port is available (connection failed)
    except:
        return False

def try_ports():
    """Try different HTTPS ports that might be available."""
    # Common alternative HTTPS ports that hosting providers often allow
    ports_to_try = [8443, 8080, 3000, 5000, 8000]
    
    for port in ports_to_try:
        print(f"🔍 Checking port {port}...")
        
        if not check_port_available(port):
            print(f"❌ Port {port} is already in use, trying next port...")
            continue
            
        try:
            print(f"✅ Port {port} is available!")
            
            # Change to the cgi-bin directory
            os.chdir(app_dir)
            
            # Import and run the Flask app
            from webapp import app
            
            print(f"🚀 Starting Flask server on port {port}...")
            print(f"🌐 Access your application at: https://bet-tracking-ai.com:{port}")
            print(f"📊 Health check: https://bet-tracking-ai.com:{port}/health")
            print(f"📄 Subscription page: https://bet-tracking-ai.com:{port}/subscriptions")
            print(f"\n🔄 Press Ctrl+C to stop the server")
            
            app.run(
                host='0.0.0.0',  # Allow external connections
                port=port,
                debug=False,
                threaded=True
            )
            
            return True  # If we get here, the server started successfully
            
        except Exception as e:
            print(f"❌ Port {port} failed with error: {e}")
            continue
    
    print("❌ All ports failed or are in use. You may need to contact Bluehost support.")
    return False

def main():
    """Main startup function."""
    print("🎰 Bet Tracking AI - Bluehost Deployment (Alternative Ports)")
    print("=" * 60)
    
    # Setup environment
    if not setup_environment():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Try different ports
    if not try_ports():
        print("\n💡 Suggestions:")
        print("1. Contact Bluehost support about opening custom ports")
        print("2. Ask about their recommended way to deploy Flask apps")
        print("3. Consider using their CGI setup instead")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

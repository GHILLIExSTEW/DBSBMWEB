#!/usr/bin/env python3
"""
AWS Lightsail Flask Application Deployment Script
For bet-tracking-ai.com hosted on Lightsail
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the application directory to Python path
app_dir = Path(__file__).parent / 'cgi-bin'
sys.path.insert(0, str(app_dir))

def setup_environment():
    """Set up the production environment for Lightsail."""
    env_file = app_dir / '.env'
    
    if env_file.exists():
        print(f"✅ Using existing environment file: {env_file}")
        return True
    else:
        print("❌ .env file not found in cgi-bin directory!")
        print("Please ensure your .env file is in the cgi-bin/ folder")
        return False

def install_dependencies():
    """Install required Python packages on Windows Lightsail."""
    try:
        # Check if Python is installed
        try:
            result = subprocess.run([sys.executable, '--version'], capture_output=True, text=True)
            print(f"📍 Using Python: {result.stdout.strip()}")
        except:
            print("❌ Python not found! Please install Python first.")
            return False
        
        # Install Flask app dependencies
        req_file = Path(__file__).parent / 'requirements.txt'
        
        print(f"📦 Installing Python dependencies from {req_file.name}...")
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', str(req_file)
        ], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("💡 Try running as Administrator if permission issues occur")
        return False

def setup_iis():
    """Set up IIS as reverse proxy (optional for Windows Server)."""
    print("💡 For Windows Server, you can optionally set up IIS as a reverse proxy")
    print("   Or simply run Flask directly on port 80 (requires Administrator)")
    
    iis_config = """
<!-- web.config for IIS reverse proxy -->
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="Flask App" stopProcessing="true">
          <match url=".*" />
          <action type="Rewrite" url="http://127.0.0.1:5000/{R:0}" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
"""
    
    try:
        print("📄 IIS web.config template created (if you want to use IIS)")
        with open('web.config', 'w') as f:
            f.write(iis_config)
        print("✅ web.config created for IIS setup")
        return True
    except Exception as e:
        print(f"⚠️ IIS config creation failed (optional): {e}")
        return False

def start_flask_server():
    """Start the Flask application on Windows Lightsail."""
    try:
        # Change to the cgi-bin directory
        os.chdir(app_dir)
        
        # Import and run the Flask app
        from webapp import app
        
        # Run the Flask server
        print("🚀 Starting Flask server on port 5000...")
        print("🌐 Access your application at: http://YOUR_LIGHTSAIL_IP:5000")
        print("🌐 Or if domain is configured: https://bet-tracking-ai.com")
        print("📊 Health check: http://YOUR_LIGHTSAIL_IP:5000/health")
        print("📄 Subscription page: http://YOUR_LIGHTSAIL_IP:5000/subscriptions")
        print("\n💡 To use port 80, run as Administrator and change port to 80")
        print("🔄 Press Ctrl+C to stop the server")
        
        app.run(
            host='0.0.0.0',  # Allow external connections
            port=5000,       # Standard Flask port
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Failed to start Flask server: {e}")
        print("💡 Make sure Windows Firewall allows port 5000")
        return False

def main():
    """Main deployment function for Windows Lightsail."""
    print("🚀 Bet Tracking AI - AWS Lightsail (Windows) Deployment")
    print("=" * 60)
    
    # Setup environment
    if not setup_environment():
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Setup IIS config (optional)
    setup_iis()
    
    # Start the server
    start_flask_server()
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
Complete Lightsail Setup - Handles Flask + Port 80 + Diagnostics
"""
import os
import sys
import subprocess
import time
import socket
import threading
import urllib.request

def check_admin():
    """Check if running as administrator"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def add_firewall_rules():
    """Add Windows Firewall rules"""
    if not check_admin():
        print("⚠️  Not running as Administrator - skipping firewall rules")
        return
    
    try:
        # Add port 80 rule
        subprocess.run([
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            'name=Allow Port 80', 'dir=in', 'action=allow', 
            'protocol=TCP', 'localport=80'
        ], check=True)
        print("✅ Added firewall rule for port 80")
        
        # Add port 25594 rule
        subprocess.run([
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            'name=Allow Port 25594', 'dir=in', 'action=allow', 
            'protocol=TCP', 'localport=25594'
        ], check=True)
        print("✅ Added firewall rule for port 25594")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to add firewall rules: {e}")

def start_flask_app():
    """Start Flask app in background"""
    try:
        # Set environment for production
        env = os.environ.copy()
        env['FLASK_ENV'] = 'production'
        env['WEBAPP_PORT'] = '25594'
        
        # Start Flask app
        process = subprocess.Popen([
            sys.executable, 'cgi-bin/webapp.py'
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("🚀 Starting Flask app...")
        time.sleep(3)  # Give it time to start
        
        # Check if it's running
        if process.poll() is None:  # Still running
            print("✅ Flask app started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Flask app failed to start:")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting Flask app: {e}")
        return None

def start_port80_proxy():
    """Start port 80 proxy server"""
    if not check_admin():
        print("❌ Need Administrator privileges to bind to port 80")
        print("💡 Right-click and 'Run as Administrator'")
        return None
    
    try:
        # Start the proxy
        process = subprocess.Popen([
            sys.executable, 'port80_proxy.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("🔗 Starting port 80 proxy...")
        time.sleep(2)
        
        if process.poll() is None:  # Still running
            print("✅ Port 80 proxy started successfully")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Port 80 proxy failed to start:")
            print(f"STDOUT: {stdout.decode()}")
            print(f"STDERR: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"❌ Error starting port 80 proxy: {e}")
        return None

def test_connectivity():
    """Test if everything is working"""
    print("\n🧪 Testing connectivity...")
    
    # Test Flask app
    try:
        response = urllib.request.urlopen('http://localhost:25594', timeout=5)
        print(f"✅ Flask app responding (Status: {response.code})")
    except Exception as e:
        print(f"❌ Flask app not responding: {e}")
    
    # Test port 80
    try:
        response = urllib.request.urlopen('http://localhost:80', timeout=5)
        print(f"✅ Port 80 responding (Status: {response.code})")
    except Exception as e:
        print(f"❌ Port 80 not responding: {e}")

def main():
    print("🌐 Lightsail Complete Setup")
    print("=" * 40)
    
    if not check_admin():
        print("⚠️  For full setup, run as Administrator")
        print("💡 Some features (port 80, firewall) require admin privileges")
    
    # Add firewall rules
    add_firewall_rules()
    
    # Start Flask app
    flask_process = start_flask_app()
    if not flask_process:
        print("❌ Cannot continue without Flask app")
        return
    
    # Start port 80 proxy
    proxy_process = start_port80_proxy()
    
    # Test connectivity
    test_connectivity()
    
    print("\n📋 Status Summary:")
    print(f"Flask app: {'✅ Running' if flask_process and flask_process.poll() is None else '❌ Not running'}")
    print(f"Port 80 proxy: {'✅ Running' if proxy_process and proxy_process.poll() is None else '❌ Not running'}")
    
    print("\n🌍 Access URLs:")
    print("- Local: http://localhost:25594 (Flask direct)")
    print("- Local: http://localhost:80 (through proxy)")
    print("- Public: http://72.240.236.211 (if Lightsail firewall is configured)")
    
    print("\n⚠️  Don't forget to configure Lightsail firewall in AWS Console!")
    print("   Go to: Lightsail Console > Networking > Firewall")
    print("   Add rules for ports 80 and 25594")
    
    try:
        print("\n🔄 Press Ctrl+C to stop all services")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        if flask_process:
            flask_process.terminate()
        if proxy_process:
            proxy_process.terminate()
        print("✅ All services stopped")

if __name__ == "__main__":
    main()

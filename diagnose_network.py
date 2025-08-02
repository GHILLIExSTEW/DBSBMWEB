#!/usr/bin/env python3
"""
Lightsail VPS Network Diagnostics
"""
import socket
import subprocess
import sys
import urllib.request
import urllib.error

def check_port(host, port, timeout=5):
    """Check if a port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_firewall_rules():
    """Check Windows Firewall rules"""
    try:
        result = subprocess.run([
            'netsh', 'advfirewall', 'firewall', 'show', 'rule', 
            'name=all', 'dir=in', 'protocol=tcp'
        ], capture_output=True, text=True, timeout=10)
        
        if 'port=80' in result.stdout.lower() or 'port=25594' in result.stdout.lower():
            print("✅ Found firewall rules for ports 80 or 25594")
        else:
            print("⚠️  No specific firewall rules found for ports 80 or 25594")
            print("💡 You may need to add firewall rules")
        
    except Exception as e:
        print(f"❌ Cannot check firewall rules: {e}")

def check_listening_ports():
    """Check what ports are listening"""
    try:
        result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        port_80_found = False
        port_25594_found = False
        
        for line in lines:
            if ':80 ' in line and 'LISTENING' in line:
                port_80_found = True
                print(f"✅ Port 80 is listening: {line.strip()}")
            elif ':25594' in line and 'LISTENING' in line:
                port_25594_found = True
                print(f"✅ Port 25594 is listening: {line.strip()}")
        
        if not port_80_found:
            print("❌ Port 80 is not listening")
        if not port_25594_found:
            print("❌ Port 25594 is not listening")
            
    except Exception as e:
        print(f"❌ Cannot check listening ports: {e}")

def test_local_connectivity():
    """Test local connectivity"""
    print("\n🔍 Testing Local Connectivity:")
    
    # Test localhost connections
    if check_port('127.0.0.1', 80):
        print("✅ Port 80 is accessible locally")
    else:
        print("❌ Port 80 is not accessible locally")
    
    if check_port('127.0.0.1', 25594):
        print("✅ Port 25594 is accessible locally")
    else:
        print("❌ Port 25594 is not accessible locally")
    
    # Test HTTP requests
    try:
        response = urllib.request.urlopen('http://localhost:80', timeout=10)
        print(f"✅ HTTP request to localhost:80 successful (Status: {response.code})")
    except Exception as e:
        print(f"❌ HTTP request to localhost:80 failed: {e}")
    
    try:
        response = urllib.request.urlopen('http://localhost:25594', timeout=10)
        print(f"✅ HTTP request to localhost:25594 successful (Status: {response.code})")
    except Exception as e:
        print(f"❌ HTTP request to localhost:25594 failed: {e}")

def check_lightsail_networking():
    """Check Lightsail-specific networking"""
    print("\n🌐 Lightsail Networking Check:")
    
    # Get public IP
    try:
        response = urllib.request.urlopen('http://checkip.amazonaws.com/', timeout=10)
        public_ip = response.read().decode().strip()
        print(f"📍 Public IP: {public_ip}")
        
        # Test external access
        if check_port(public_ip, 80, timeout=10):
            print(f"✅ Port 80 is accessible from outside")
        else:
            print(f"❌ Port 80 is not accessible from outside")
            print("💡 Check Lightsail firewall settings in AWS Console")
            
    except Exception as e:
        print(f"❌ Cannot determine public IP: {e}")

def main():
    print("🔧 Lightsail VPS Network Diagnostics")
    print("=" * 50)
    
    print("\n🔍 Checking Listening Ports:")
    check_listening_ports()
    
    print("\n🛡️  Checking Windows Firewall:")
    check_firewall_rules()
    
    test_local_connectivity()
    check_lightsail_networking()
    
    print("\n📋 Recommended Actions:")
    print("1. Ensure Flask app is running: python cgi-bin/webapp.py")
    print("2. Run port 80 proxy as Administrator: python port80_proxy.py")
    print("3. Check Lightsail firewall in AWS Console:")
    print("   - Go to Lightsail Console > Networking > Firewall")
    print("   - Ensure ports 80 and 25594 are open")
    print("4. Add Windows Firewall rules if needed:")
    print("   netsh advfirewall firewall add rule name=\"Allow Port 80\" dir=in action=allow protocol=TCP localport=80")
    print("   netsh advfirewall firewall add rule name=\"Allow Port 25594\" dir=in action=allow protocol=TCP localport=25594")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Bluehost Environment Check Script
Tests if everything is properly configured for Flask deployment
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python():
    """Check Python version and availability."""
    print("🐍 Python Environment Check:")
    print(f"   Python version: {sys.version}")
    print(f"   Python executable: {sys.executable}")
    
    # Check if Python 3.9+ is available
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print("   ✅ Python version is compatible")
        return True
    else:
        print("   ❌ Python version should be 3.9 or higher")
        return False

def check_dependencies():
    """Check if required packages are available."""
    print("\n📦 Dependencies Check:")
    
    required_packages = ['flask', 'mysql.connector', 'requests', 'dotenv']
    all_available = True
    
    for package in required_packages:
        try:
            if package == 'dotenv':
                import dotenv as pkg
            elif package == 'mysql.connector':
                import mysql.connector as pkg
            else:
                pkg = __import__(package)
            
            version = getattr(pkg, '__version__', 'unknown')
            print(f"   ✅ {package}: {version}")
        except ImportError:
            print(f"   ❌ {package}: Not installed")
            all_available = False
    
    return all_available

def check_files():
    """Check if required files exist."""
    print("\n📁 File Structure Check:")
    
    base_dir = Path(__file__).parent
    required_files = [
        'cgi-bin/webapp.py',
        'cgi-bin/bot/templates',
        'cgi-bin/bot/static',
        'cgi-bin/.env',
        'requirements.txt'
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}: Missing")
            all_exist = False
    
    return all_exist

def check_database():
    """Test database connection."""
    print("\n🗄️ Database Connection Check:")
    
    try:
        # Add cgi-bin to path for imports
        sys.path.insert(0, str(Path(__file__).parent / 'cgi-bin'))
        
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent / 'cgi-bin' / '.env')
        
        # Test database connection
        import mysql.connector
        
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DB'),
            port=int(os.getenv('MYSQL_PORT', 3306))
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        print("   ✅ Database connection successful")
        return True
        
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

def check_discord_config():
    """Check Discord configuration."""
    print("\n🤖 Discord Configuration Check:")
    
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent / 'cgi-bin' / '.env')
        
        client_id = os.getenv('DISCORD_CLIENT_ID')
        client_secret = os.getenv('DISCORD_CLIENT_SECRET')
        redirect_uri = os.getenv('DISCORD_REDIRECT_URI')
        bot_token = os.getenv('DISCORD_BOT_TOKEN')
        
        if client_id and client_secret and redirect_uri and bot_token:
            print(f"   ✅ Client ID: {client_id}")
            print(f"   ✅ Redirect URI: {redirect_uri}")
            print("   ✅ Client Secret: [CONFIGURED]")
            print("   ✅ Bot Token: [CONFIGURED]")
            return True
        else:
            print("   ❌ Missing Discord configuration")
            return False
            
    except Exception as e:
        print(f"   ❌ Discord config check failed: {e}")
        return False

def main():
    """Run all checks."""
    print("🎰 Bet Tracking AI - Bluehost Environment Check")
    print("=" * 60)
    
    checks = [
        check_python(),
        check_files(),
        check_dependencies(),
        check_database(),
        check_discord_config()
    ]
    
    print("\n" + "=" * 60)
    if all(checks):
        print("🎉 All checks passed! Ready to start Flask server.")
        print("\nNext steps:")
        print("1. Run: python3 start_bluehost.py")
        print("2. Access: https://bet-tracking-ai.com:25595")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install dependencies: pip3 install --user -r requirements.txt")
        print("- Check file paths and permissions")
        print("- Verify database credentials")
    
    return 0 if all(checks) else 1

if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""
Test PostgreSQL connection for Discord Bot Web System
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

def test_postgres_connection():
    """Test PostgreSQL connection with current settings."""
    
    # Try with default postgres user first
    try:
        print("🔍 Testing PostgreSQL connection...")
        
        # Try connecting to default postgres database
        connection = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            user='postgres',  # Default postgres user
            password='password',  # PostgreSQL password
            database='postgres',  # Default postgres database
            port=int(os.getenv('POSTGRES_PORT', 5432))
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print(f"✅ PostgreSQL connection successful!")
        print(f"📊 Version: {version[0]}")
        
        # List existing databases
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = cursor.fetchall()
        print(f"📂 Databases: {[db[0] for db in databases]}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == '__main__':
    test_postgres_connection()

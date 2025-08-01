#!/usr/bin/env python3
import mysql.connector
from mysql.connector import Error

def test_db_connection():
    """Test database connection to Pebblehost."""
    try:
        print("Testing database connection...")
        connection = mysql.connector.connect(
            host='na05-sql.pebblehost.com',
            user='customer_990306_Server_database',
            password='NGNrWmR@IypQb4k@tzgk+NnI',
            database='customer_990306_Server_database',
            port=3306
        )
        
        if connection.is_connected():
            print("✅ Database connection successful!")
            
            # Test a simple query
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"✅ Test query result: {result}")
            
            cursor.close()
            connection.close()
            print("✅ Connection closed successfully!")
            return True
        else:
            print("❌ Database connection failed!")
            return False
            
    except Error as e:
        print(f"❌ Database connection error: {e}")
        return False

if __name__ == "__main__":
    test_db_connection() 
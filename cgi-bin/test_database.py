#!/usr/bin/env python3
"""
Database Connection Test Script
Run this to verify your database connection and see sample data
"""

import os
import sys
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

# Load environment variables
load_dotenv()

def test_connection():
    """Test database connection and show configuration."""
    print("=== Database Connection Test ===\n")
    
    # Show current configuration (hide password)
    config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'user': os.getenv('MYSQL_USER', 'dbsbm'),
        'password': '*' * len(os.getenv('MYSQL_PASSWORD', '')),
        'database': os.getenv('MYSQL_DB', 'dbsbm'),
        'port': int(os.getenv('MYSQL_PORT', 3306))
    }
    
    print("Current Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*50 + "\n")
    
    try:
        # Attempt connection
        print("Attempting to connect to database...")
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'dbsbm'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DB', 'dbsbm'),
            port=int(os.getenv('MYSQL_PORT', 3306))
        )
        
        if connection.is_connected():
            print("✅ Successfully connected to database!")
            
            cursor = connection.cursor()
            
            # Get database info
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"MySQL Version: {version[0]}")
            
            # List tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            if tables:
                print(f"\n📊 Found {len(tables)} tables:")
                for table in tables:
                    print(f"  - {table[0]}")
                    
                # Check for specific tables we need
                table_names = [table[0] for table in tables]
                required_tables = ['guilds', 'bets', 'users', 'games', 'teams', 'leagues']
                
                print(f"\n🔍 Checking for required tables:")
                for required_table in required_tables:
                    if required_table in table_names:
                        print(f"  ✅ {required_table}")
                        
                        # Get row count
                        cursor.execute(f"SELECT COUNT(*) FROM {required_table}")
                        count = cursor.fetchone()[0]
                        print(f"     ({count} rows)")
                    else:
                        print(f"  ❌ {required_table} (missing)")
                
            else:
                print("\n📭 No tables found in database")
                print("You may need to create your database schema first.")
            
            cursor.close()
            connection.close()
            print("\n🔌 Connection closed successfully")
            
    except Error as e:
        print(f"❌ Database connection failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check that MySQL server is running")
        print("2. Verify your database credentials in .env file")
        print("3. Ensure the database exists")
        print("4. Check firewall settings if using remote database")
        
        if "Access denied" in str(e):
            print("\n🔑 Access denied - check username/password")
        elif "Unknown database" in str(e):
            print("\n🗄️  Database doesn't exist - you may need to create it")
        elif "Can't connect" in str(e):
            print("\n🌐 Can't connect - check host and port")
            
        return False
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def create_sample_data():
    """Create sample data for testing."""
    print("\n" + "="*50)
    print("Creating sample data...")
    
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'dbsbm'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DB', 'dbsbm'),
            port=int(os.getenv('MYSQL_PORT', 3306))
        )
        
        cursor = connection.cursor()
        
        # Create guilds table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guilds (
                guild_id BIGINT PRIMARY KEY,
                guild_name VARCHAR(255) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insert sample guild
        cursor.execute("""
            INSERT INTO guilds (guild_id, guild_name, is_active) 
            VALUES (123456789, 'Sample Guild', TRUE)
            ON DUPLICATE KEY UPDATE guild_name = VALUES(guild_name)
        """)
        
        # Create bets table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bets (
                bet_serial INT AUTO_INCREMENT PRIMARY KEY,
                guild_id BIGINT,
                user_id BIGINT,
                bet_type VARCHAR(100),
                units DECIMAL(10,2),
                status ENUM('pending', 'won', 'lost', 'WON', 'LOST') DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (guild_id) REFERENCES guilds(guild_id)
            )
        """)
        
        # Insert sample bets
        sample_bets = [
            (123456789, 111, 'Moneyline', 2.5, 'won'),
            (123456789, 222, 'Spread', 1.0, 'lost'),
            (123456789, 333, 'Over/Under', 3.0, 'won'),
            (123456789, 111, 'Prop Bet', 1.5, 'pending')
        ]
        
        for bet in sample_bets:
            cursor.execute("""
                INSERT INTO bets (guild_id, user_id, bet_type, units, status)
                VALUES (%s, %s, %s, %s, %s)
            """, bet)
        
        connection.commit()
        cursor.close()
        connection.close()
        
        print("✅ Sample data created successfully!")
        return True
        
    except Error as e:
        print(f"❌ Failed to create sample data: {e}")
        return False

if __name__ == "__main__":
    print("🏁 Starting database test...\n")
    
    if test_connection():
        print("\n" + "="*50)
        response = input("\nWould you like to create sample data for testing? (y/n): ")
        if response.lower() in ['y', 'yes']:
            create_sample_data()
        
        print("\n🎉 Database test complete!")
        print("\nYou can now restart your Flask app to see live data.")
    else:
        print("\n❌ Please fix the database connection issues and try again.")
        print("\n📝 Next steps:")
        print("1. Edit the .env file with your correct database credentials")
        print("2. Make sure your MySQL server is running")
        print("3. Run this test again")

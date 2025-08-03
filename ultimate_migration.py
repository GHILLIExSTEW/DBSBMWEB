#!/usr/bin/env python3
"""
ULTIMATE MIGRATION - Handles ALL dependencies and constraints
Creates missing users, handles all NULL constraints properly
"""

import mysql.connector
import psycopg2
import logging
from datetime import datetime, date
import sys

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def connect_mysql():
    """Connect to PebbleHost MySQL"""
    try:
        conn = mysql.connector.connect(
            host='na05-sql.pebblehost.com',
            user='customer_990306_Server_database',
            password='NGNrWmR@IypQb4k@tzgk+NnI',
            database='customer_990306_Server_database',
            port=3306,
            auth_plugin='mysql_native_password'
        )
        print("✅ Connected to PebbleHost MySQL server")
        return conn
    except Exception as e:
        print(f"❌ MySQL connection failed: {e}")
        sys.exit(1)

def connect_postgres():
    """Connect to local PostgreSQL"""
    try:
        sys.path.append(r"C:\Users\Administrator\Desktop\Bot+Server\DBSBMWEB\cgi-bin")
        from webapp import get_db_connection
        conn = get_db_connection()
        print("✅ Connected to local PostgreSQL server")
        return conn
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        sys.exit(1)

def create_missing_users(mysql_conn, postgres_conn):
    """Create missing user records"""
    print("👥 Creating missing user records...")
    
    mysql_cursor = mysql_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    # Get all unique user_ids from bets table
    user_ids = set()
    mysql_cursor.execute("SELECT DISTINCT user_id FROM bets WHERE user_id IS NOT NULL")
    for row in mysql_cursor.fetchall():
        user_ids.add(row[0])
    
    print(f"🔍 Found {len(user_ids)} unique user IDs to create")
    
    # Create user records
    for user_id in user_ids:
        try:
            postgres_cursor.execute("""
                INSERT INTO users (user_id, username)
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO NOTHING
            """, (
                user_id,
                f"User_{user_id}"  # Default username
            ))
            print(f"✅ Created user record for ID: {user_id}")
        except Exception as e:
            print(f"⚠️ Failed to create user {user_id}: {e}")
    
    postgres_conn.commit()
    print("✅ User creation completed")

def migrate_bets_with_fallbacks(mysql_conn, postgres_conn):
    """Migrate bets table with proper NULL handling"""
    print("🎯 Migrating bets with fallback values...")
    
    mysql_cursor = mysql_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    # Get data from MySQL
    mysql_cursor.execute("SELECT * FROM bets")
    rows = mysql_cursor.fetchall()
    
    if not rows:
        print("⚠️ No data in bets")
        return 0
    
    print(f"📊 Found {len(rows)} rows in bets")
    
    # Get column info
    mysql_cursor.execute("DESCRIBE bets")
    columns = [col[0] for col in mysql_cursor.fetchall()]
    
    # Clear existing data
    postgres_cursor.execute("DELETE FROM bets")
    print("🗑️ Cleared existing data from bets")
    
    # Insert with proper fallbacks
    success_count = 0
    for row in rows:
        try:
            # Create value dictionary
            values = {}
            for i, col_name in enumerate(columns):
                value = row[i]
                
                # Handle special NULL fallbacks
                if value is None:
                    if col_name in ['bet_serial', 'message_id']:
                        values[col_name] = 0  # Default for important bot fields
                    elif col_name in ['confirmed', 'bet_won', 'bet_loss']:
                        values[col_name] = False  # Boolean defaults
                    elif col_name in ['status']:
                        values[col_name] = 'pending'  # Default status
                    elif col_name in ['result_value']:
                        values[col_name] = 0.0  # Default numeric
                    elif col_name in ['bet_type', 'result_description']:
                        values[col_name] = ''  # Empty string for text
                    else:
                        values[col_name] = None  # Keep NULL for optional fields
                else:
                    # Convert types
                    if col_name in ['confirmed', 'bet_won', 'bet_loss'] and isinstance(value, int):
                        values[col_name] = bool(value)
                    else:
                        values[col_name] = value
            
            # Build insert query with all columns
            insert_cols = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            insert_query = f"INSERT INTO bets ({insert_cols}) VALUES ({placeholders})"
            
            # Build values list in column order
            insert_values = [values[col] for col in columns]
            
            postgres_cursor.execute(insert_query, insert_values)
            success_count += 1
            
        except Exception as e:
            print(f"⚠️ Failed to insert bet row: {str(e)[:100]}...")
            continue
    
    postgres_conn.commit()
    print(f"✅ Successfully migrated {success_count} rows to bets")
    return success_count

def migrate_unit_records_with_fallbacks(mysql_conn, postgres_conn):
    """Migrate unit_records table with proper NULL handling"""
    print("💰 Migrating unit_records with fallback values...")
    
    mysql_cursor = mysql_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    # Get data from MySQL
    mysql_cursor.execute("SELECT * FROM unit_records")
    rows = mysql_cursor.fetchall()
    
    if not rows:
        print("⚠️ No data in unit_records")
        return 0
    
    print(f"📊 Found {len(rows)} rows in unit_records")
    
    # Get column info
    mysql_cursor.execute("DESCRIBE unit_records")
    columns = [col[0] for col in mysql_cursor.fetchall()]
    
    # Clear existing data
    postgres_cursor.execute("DELETE FROM unit_records")
    print("🗑️ Cleared existing data from unit_records")
    
    # Insert with proper fallbacks
    success_count = 0
    for row in rows:
        try:
            # Create value dictionary with fallbacks
            values = {}
            for i, col_name in enumerate(columns):
                value = row[i]
                
                # Handle NULL fallbacks for NOT NULL columns
                if value is None:
                    if col_name == 'result_value':
                        values[col_name] = 0.0  # Default for result_value
                    elif col_name in ['transaction_type']:
                        values[col_name] = 'bet'  # Default transaction type
                    elif col_name in ['units']:
                        values[col_name] = 0.0  # Default units
                    else:
                        values[col_name] = None  # Keep NULL for optional fields
                else:
                    values[col_name] = value
            
            # Build insert query
            insert_cols = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            insert_query = f"INSERT INTO unit_records ({insert_cols}) VALUES ({placeholders})"
            
            # Build values list
            insert_values = [values[col] for col in columns]
            
            postgres_cursor.execute(insert_query, insert_values)
            success_count += 1
            
        except Exception as e:
            print(f"⚠️ Failed to insert unit_record row: {str(e)[:100]}...")
            continue
    
    postgres_conn.commit()
    print(f"✅ Successfully migrated {success_count} rows to unit_records")
    return success_count

def main():
    print("🚀 ULTIMATE MIGRATION - ALL DEPENDENCIES HANDLED")
    print("=" * 70)
    
    # Connect to databases
    mysql_conn = connect_mysql()
    postgres_conn = connect_postgres()
    
    try:
        total_migrated = 0
        
        # Step 1: Create missing users (bets depends on users)
        create_missing_users(mysql_conn, postgres_conn)
        
        # Step 2: Migrate bets with proper fallbacks
        bets_count = migrate_bets_with_fallbacks(mysql_conn, postgres_conn)
        total_migrated += bets_count
        
        # Step 3: Migrate unit_records with proper fallbacks
        units_count = migrate_unit_records_with_fallbacks(mysql_conn, postgres_conn)
        total_migrated += units_count
        
        print("\n" + "=" * 70)
        print("🎉 ULTIMATE MIGRATION COMPLETED!")
        print("=" * 70)
        print(f"📊 Total critical rows migrated: {total_migrated}")
        
        # Final verification
        print("🔍 Final verification...")
        postgres_cursor = postgres_conn.cursor()
        
        # Check all critical tables
        tables = ['guilds', 'users', 'guild_settings', 'bets', 'unit_records']
        for table in tables:
            postgres_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = postgres_cursor.fetchone()[0]
            print(f"   📊 {table}: {count} rows")
        
        # Check critical bot fields
        postgres_cursor.execute("SELECT COUNT(*) FROM bets WHERE message_id IS NOT NULL AND message_id != 0")
        message_count = postgres_cursor.fetchone()[0]
        print(f"   📊 Bets with valid message_id: {message_count} rows")
        
        postgres_cursor.execute("SELECT COUNT(*) FROM bets WHERE bet_serial IS NOT NULL AND bet_serial != 0")
        serial_count = postgres_cursor.fetchone()[0]
        print(f"   📊 Bets with valid bet_serial: {serial_count} rows")
        
        # Sample some data
        postgres_cursor.execute("SELECT bet_serial, message_id, guild_id, user_id, status FROM bets LIMIT 3")
        sample_bets = postgres_cursor.fetchall()
        if sample_bets:
            print("   📋 Sample bet records:")
            for bet in sample_bets:
                print(f"      Serial: {bet[0]}, Message: {bet[1]}, Guild: {bet[2]}, User: {bet[3]}, Status: {bet[4]}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mysql_conn.close()
        postgres_conn.close()
        print("🔒 Database connections closed")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Final corrected migration script
Handles schema differences and constraint issues properly
"""

import mysql.connector
import psycopg2
import logging
from datetime import datetime, date
import sys

# Set up basic logging to avoid Unicode issues
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

def convert_value(value, postgres_type):
    """Convert MySQL value to PostgreSQL compatible value with NULL fallbacks"""
    if value is None:
        # Provide fallbacks for NOT NULL columns
        if postgres_type.lower() in ['boolean', 'bool']:
            return False
        elif postgres_type.lower() in ['integer', 'bigint', 'int', 'int8']:
            return 0
        elif postgres_type.lower() in ['numeric', 'decimal', 'real', 'double precision']:
            return 0.0
        elif postgres_type.lower() in ['text', 'varchar', 'character varying']:
            return ''  # Empty string instead of NULL
        else:
            return None
        
    # Handle boolean conversions
    if postgres_type.lower() in ['boolean', 'bool']:
        if isinstance(value, (int, str)):
            if str(value).lower() in ['1', 'true', 't', 'yes', 'y']:
                return True
            elif str(value).lower() in ['0', 'false', 'f', 'no', 'n']:
                return False
        return bool(value)
    
    # Handle datetime conversions
    elif postgres_type.lower().startswith('timestamp'):
        if isinstance(value, (datetime, date)):
            return value
        elif isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return value
    
    # Handle numeric conversions
    elif postgres_type.lower() in ['integer', 'bigint', 'int', 'int8']:
        try:
            return int(value) if value is not None else 0
        except:
            return 0
    
    # Handle text conversions  
    elif postgres_type.lower() in ['text', 'varchar', 'character varying']:
        return str(value) if value is not None else ''
    
    # Default: return as-is
    return value

def create_missing_guilds(mysql_conn, postgres_conn):
    """Create missing guild records with correct schema"""
    print("🏗️ Creating missing guild records...")
    
    mysql_cursor = mysql_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    # Get all unique guild_ids from dependent tables
    guild_ids = set()
    
    # From bets table
    mysql_cursor.execute("SELECT DISTINCT guild_id FROM bets WHERE guild_id IS NOT NULL")
    for row in mysql_cursor.fetchall():
        guild_ids.add(row[0])
    
    # From guild_settings table  
    mysql_cursor.execute("SELECT DISTINCT guild_id FROM guild_settings WHERE guild_id IS NOT NULL")
    for row in mysql_cursor.fetchall():
        guild_ids.add(row[0])
        
    # From subscriptions table
    mysql_cursor.execute("SELECT DISTINCT guild_id FROM subscriptions WHERE guild_id IS NOT NULL")
    for row in mysql_cursor.fetchall():
        guild_ids.add(row[0])
    
    print(f"🔍 Found {len(guild_ids)} unique guild IDs to create")
    
    # Create guild records with correct PostgreSQL schema
    for guild_id in guild_ids:
        try:
            postgres_cursor.execute("""
                INSERT INTO guilds (guild_id, guild_name)
                VALUES (%s, %s)
                ON CONFLICT (guild_id) DO NOTHING
            """, (
                guild_id,
                f"Guild {guild_id}"  # Default name
            ))
            print(f"✅ Created guild record for ID: {guild_id}")
        except Exception as e:
            print(f"⚠️ Failed to create guild {guild_id}: {e}")
    
    postgres_conn.commit()
    print("✅ Guild creation completed")

def migrate_critical_tables(mysql_conn, postgres_conn):
    """Migrate only the critical tables for bot functionality"""
    print("🎯 Migrating critical bot tables...")
    
    # Tables in dependency order (only critical ones)
    critical_tables = [
        'guild_settings',   # Guild configuration (already have guilds)
        'bets',            # Betting records (most important for bot)
        'unit_records'     # Unit tracking
    ]
    
    total_migrated = 0
    
    for table_name in critical_tables:
        print(f"\n📦 Migrating {table_name}")
        print("-" * 40)
        
        mysql_cursor = mysql_conn.cursor()
        postgres_cursor = postgres_conn.cursor()
        
        try:
            # Get data from MySQL
            mysql_cursor.execute(f"SELECT * FROM {table_name}")
            rows = mysql_cursor.fetchall()
            
            if not rows:
                print(f"⚠️ No data in {table_name}")
                continue
            
            print(f"📊 Found {len(rows)} rows in {table_name}")
            
            # Get column info
            mysql_cursor.execute(f"DESCRIBE {table_name}")
            columns = [col[0] for col in mysql_cursor.fetchall()]
            
            # Get PostgreSQL column types
            postgres_cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s AND table_schema = 'public'
                ORDER BY ordinal_position
            """, (table_name,))
            
            pg_columns = {row[0]: row[1] for row in postgres_cursor.fetchall()}
            
            # Clear existing data
            postgres_cursor.execute(f"DELETE FROM {table_name}")
            print(f"🗑️ Cleared existing data from {table_name}")
            
            # Build insert query - only use columns that exist in both
            common_columns = [col for col in columns if col in pg_columns]
            placeholders = ', '.join(['%s'] * len(common_columns))
            insert_query = f"INSERT INTO {table_name} ({', '.join(common_columns)}) VALUES ({placeholders})"
            
            # Insert data with conversion
            success_count = 0
            for row in rows:
                try:
                    # Convert values for common columns only
                    converted_row = []
                    for i, col_name in enumerate(columns):
                        if col_name in common_columns:
                            value = row[i]
                            pg_type = pg_columns.get(col_name, 'text')
                            converted_value = convert_value(value, pg_type)
                            converted_row.append(converted_value)
                    
                    postgres_cursor.execute(insert_query, converted_row)
                    success_count += 1
                except Exception as e:
                    print(f"⚠️ Failed to insert row: {str(e)[:80]}...")
                    continue
            
            postgres_conn.commit()
            print(f"✅ Successfully migrated {success_count} rows to {table_name}")
            total_migrated += success_count
            
        except Exception as e:
            print(f"❌ Error migrating {table_name}: {e}")
            postgres_conn.rollback()
            continue
    
    return total_migrated

def main():
    print("🚀 FINAL CORRECTED MIGRATION")
    print("=" * 60)
    
    # Connect to databases
    mysql_conn = connect_mysql()
    postgres_conn = connect_postgres()
    
    try:
        # Step 1: Create missing guild records
        create_missing_guilds(mysql_conn, postgres_conn)
        
        # Step 2: Migrate critical tables only
        total_migrated = migrate_critical_tables(mysql_conn, postgres_conn)
        
        print("\n" + "=" * 60)
        print("🎉 MIGRATION COMPLETED!")
        print("=" * 60)
        print(f"📊 Total rows migrated: {total_migrated}")
        
        # Verification
        print("🔍 Verifying migration...")
        postgres_cursor = postgres_conn.cursor()
        
        key_tables = ['guilds', 'bets', 'unit_records', 'guild_settings']
        for table in key_tables:
            postgres_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = postgres_cursor.fetchone()[0]
            print(f"   📊 {table}: {count} rows")
        
        # Check if critical bot data is there
        postgres_cursor.execute("SELECT COUNT(*) FROM bets WHERE message_id IS NOT NULL")
        message_count = postgres_cursor.fetchone()[0]
        print(f"   📊 Bets with message_id: {message_count} rows")
        
        postgres_cursor.execute("SELECT COUNT(*) FROM bets WHERE bet_serial IS NOT NULL")
        serial_count = postgres_cursor.fetchone()[0]
        print(f"   📊 Bets with bet_serial: {serial_count} rows")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
    
    finally:
        mysql_conn.close()
        postgres_conn.close()
        print("🔒 Database connections closed")

if __name__ == "__main__":
    main()

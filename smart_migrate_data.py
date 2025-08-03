#!/usr/bin/env python3
"""
Smart Data Migration with Type Conversion
Handles MySQL->PostgreSQL data type differences properly
"""
import os
import sys
import psycopg2
import mysql.connector
from datetime import datetime

# Add the cgi-bin directory to the path
sys.path.append('C:/Users/Administrator/Desktop/Bot+Server/DBSBMWEB/cgi-bin')

def connect_mysql():
    """Connect to PebbleHost MySQL server"""
    try:
        connection = mysql.connector.connect(
            host='na05-sql.pebblehost.com',
            user='customer_990306_Server_database',
            password='NGNrWmR@IypQb4k@tzgk+NnI',
            database='customer_990306_Server_database',
            port=3306,
            auth_plugin='mysql_native_password'
        )
        print("✅ Connected to PebbleHost MySQL server")
        return connection
    except Exception as e:
        print(f"❌ Failed to connect to MySQL: {e}")
        return None

def connect_postgres():
    """Connect to local PostgreSQL server"""
    try:
        from webapp import get_db_connection
        conn = get_db_connection()
        print("✅ Connected to local PostgreSQL server")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return None

def convert_value(value, target_type):
    """Convert MySQL value to PostgreSQL compatible value"""
    if value is None:
        return None
    
    # Handle boolean conversions
    if target_type == 'boolean':
        if isinstance(value, int):
            return value == 1
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)
    
    # Handle datetime conversions
    if isinstance(value, datetime):
        return value.isoformat()
    
    # Handle decimal/numeric conversions
    if target_type in ['decimal', 'numeric'] and value == '':
        return 0.0
    
    return value

def get_postgres_column_types(postgres_conn, table_name):
    """Get PostgreSQL column data types"""
    try:
        cursor = postgres_conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
        """, (table_name,))
        
        columns = cursor.fetchall()
        cursor.close()
        
        column_types = {}
        for col_name, data_type, is_nullable in columns:
            column_types[col_name] = {
                'type': data_type,
                'nullable': is_nullable == 'YES'
            }
        
        return column_types
    except Exception as e:
        print(f"❌ Error getting column types for {table_name}: {e}")
        return {}

def migrate_table_smart(mysql_conn, postgres_conn, table_name):
    """Smart migration with type conversion"""
    try:
        mysql_cursor = mysql_conn.cursor(dictionary=True)
        postgres_cursor = postgres_conn.cursor()
        
        # Get data from MySQL
        print(f"🔍 Reading data from {table_name}...")
        mysql_cursor.execute(f"SELECT * FROM {table_name}")
        rows = mysql_cursor.fetchall()
        
        if not rows:
            print(f"⚠️ No data in {table_name}")
            mysql_cursor.close()
            return 0
        
        print(f"📊 Found {len(rows)} rows in {table_name}")
        
        # Get PostgreSQL column types
        postgres_types = get_postgres_column_types(postgres_conn, table_name)
        
        # Get column names from first row
        columns = list(rows[0].keys())
        
        # Filter columns that exist in PostgreSQL
        valid_columns = [col for col in columns if col in postgres_types]
        
        if not valid_columns:
            print(f"⚠️ No matching columns found for {table_name}")
            mysql_cursor.close()
            return 0
        
        print(f"📋 Migrating columns: {', '.join(valid_columns)}")
        
        # Clear existing data
        postgres_cursor.execute(f"DELETE FROM {table_name}")
        print(f"🗑️ Cleared existing data from {table_name}")
        
        # Prepare insert statement
        placeholders = ', '.join(['%s'] * len(valid_columns))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(valid_columns)}) VALUES ({placeholders})"
        
        # Insert data with type conversion
        migrated = 0
        for row in rows:
            try:
                # Convert values based on PostgreSQL column types
                converted_values = []
                for col in valid_columns:
                    value = row.get(col)
                    col_info = postgres_types.get(col, {})
                    target_type = col_info.get('type', 'text')
                    
                    # Convert the value
                    converted_value = convert_value(value, target_type)
                    
                    # Handle NOT NULL constraints
                    if converted_value is None and not col_info.get('nullable', True):
                        if target_type == 'boolean':
                            converted_value = False
                        elif target_type in ['integer', 'bigint']:
                            converted_value = 0
                        elif target_type in ['decimal', 'numeric', 'real', 'double precision']:
                            converted_value = 0.0
                        elif target_type in ['varchar', 'text']:
                            converted_value = ''
                        elif target_type in ['timestamp', 'timestamptz']:
                            converted_value = datetime.now()
                    
                    converted_values.append(converted_value)
                
                postgres_cursor.execute(insert_sql, converted_values)
                migrated += 1
                
                if migrated % 50 == 0:
                    print(f"   📦 Migrated {migrated}/{len(rows)} rows...")
                    
            except Exception as e:
                print(f"⚠️ Failed to insert row {migrated + 1}: {e}")
                continue
        
        postgres_conn.commit()
        print(f"✅ Successfully migrated {migrated} rows to {table_name}")
        mysql_cursor.close()
        return migrated
        
    except Exception as e:
        print(f"❌ Error migrating {table_name}: {e}")
        return 0

def main():
    print("🧠 SMART DATA MIGRATION")
    print("With automatic type conversion and error handling")
    print("=" * 60)
    
    # Connect to both databases
    mysql_conn = connect_mysql()
    if not mysql_conn:
        return
    
    postgres_conn = connect_postgres()
    if not postgres_conn:
        mysql_conn.close()
        return
    
    try:
        # Priority tables for Discord bot functionality
        priority_tables = [
            'guilds',           # Discord server info
            'guild_settings',   # Bot configuration per server
            'users',           # User accounts
            'guild_users',     # User-server relationships
            'bets',            # Betting records (115 rows available!)
            'unit_records',    # Unit tracking (109 rows available!)
            'games',           # Game information
            'teams',           # Team data
            'leagues',         # League information
            'subscriptions',   # User subscriptions
        ]
        
        total_migrated = 0
        successful_tables = []
        
        print(f"🎯 Migrating {len(priority_tables)} priority tables...")
        print("=" * 50)
        
        for i, table_name in enumerate(priority_tables, 1):
            print(f"\n📦 [{i}/{len(priority_tables)}] Migrating {table_name}")
            print("-" * 40)
            
            count = migrate_table_smart(mysql_conn, postgres_conn, table_name)
            total_migrated += count
            
            if count > 0:
                successful_tables.append(f"{table_name} ({count} rows)")
                print(f"✅ {table_name}: {count} rows migrated")
            else:
                print(f"⚠️ {table_name}: No data migrated")
        
        # Final verification
        print(f"\n" + "=" * 60)
        print(f"🎉 MIGRATION COMPLETED!")
        print(f"=" * 60)
        print(f"📊 Total rows migrated: {total_migrated}")
        print(f"✅ Successful tables: {len(successful_tables)}")
        
        if successful_tables:
            print(f"\n✅ Successfully migrated:")
            for table in successful_tables:
                print(f"   - {table}")
        
        # Verify key tables
        print(f"\n🔍 Verifying migration...")
        postgres_cursor = postgres_conn.cursor()
        
        for table in ['guilds', 'bets', 'unit_records', 'guild_settings']:
            try:
                postgres_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = postgres_cursor.fetchone()[0]
                print(f"   📊 {table}: {count} rows")
            except Exception as e:
                print(f"   ❌ {table}: Error - {e}")
        
        postgres_cursor.close()
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mysql_conn.close()
        postgres_conn.close()
        print(f"\n🔒 Database connections closed")

if __name__ == "__main__":
    main()

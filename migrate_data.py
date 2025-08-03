#!/usr/bin/env python3
"""
Data Migration Script - Pull ALL data from old SQL server to PostgreSQL
"""
import os
import sys
import psycopg2
import mysql.connector
from datetime import datetime

# Add the cgi-bin directory to the path
sys.path.append('C:/Users/Administrator/Desktop/Bot+Server/DBSBMWEB/cgi-bin')

def connect_old_mysql_server(host, user, password, database, port=3306):
    """Connect to the old MySQL server"""
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            auth_plugin='mysql_native_password'
        )
        print(f"✅ Connected to old MySQL server at {host}:{port}")
        return connection
    except Exception as e:
        print(f"❌ Failed to connect to old MySQL server: {e}")
        return None

def connect_new_postgres_server():
    """Connect to the new PostgreSQL server"""
    try:
        from webapp import get_db_connection
        conn = get_db_connection()
        print("✅ Connected to new PostgreSQL server")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to new PostgreSQL server: {e}")
        return None

def get_table_structure(old_conn, table_name):
    """Get column information for a table"""
    try:
        cursor = old_conn.cursor()
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        cursor.close()
        return columns
    except Exception as e:
        print(f"❌ Error getting structure for {table_name}: {e}")
        return []

def migrate_table_data(old_conn, new_conn, table_name):
    """Migrate ALL data from old table to new table"""
    try:
        old_cursor = old_conn.cursor(dictionary=True)
        new_cursor = new_conn.cursor()
        
        # Get data from old table
        print(f"🔍 Scanning {table_name}...")
        old_cursor.execute(f"SELECT * FROM {table_name}")
        rows = old_cursor.fetchall()
        
        if not rows:
            print(f"⚠️ No data found in {table_name}")
            old_cursor.close()
            return 0
        
        print(f"📊 Found {len(rows)} rows in {table_name}")
        
        # Get column names from first row
        columns = list(rows[0].keys())
        print(f"📋 Columns: {', '.join(columns)}")
        
        # Check if table exists in PostgreSQL
        new_cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            )
        """, (table_name,))
        
        table_exists = new_cursor.fetchone()[0]
        
        if not table_exists:
            print(f"⚠️ Table {table_name} doesn't exist in PostgreSQL - skipping")
            old_cursor.close()
            return 0
        
        # Clear existing data first (optional - comment out if you want to keep existing data)
        print(f"🗑️ Clearing existing data in {table_name}...")
        new_cursor.execute(f"DELETE FROM {table_name}")
        
        # Create INSERT statement
        placeholders = ', '.join(['%s'] * len(columns))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        # Insert data in batches
        migrated_count = 0
        batch_size = 100
        
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            batch_values = []
            
            for row in batch:
                try:
                    values = list(row.values())
                    # Convert any datetime objects to strings
                    converted_values = []
                    for val in values:
                        if isinstance(val, datetime):
                            converted_values.append(val.isoformat())
                        else:
                            converted_values.append(val)
                    batch_values.append(converted_values)
                    migrated_count += 1
                except Exception as e:
                    print(f"⚠️ Failed to prepare row in {table_name}: {e}")
                    continue
            
            # Execute batch insert
            if batch_values:
                try:
                    new_cursor.executemany(insert_sql, batch_values)
                    print(f"📦 Inserted batch {i//batch_size + 1} ({len(batch_values)} rows)")
                except Exception as e:
                    print(f"⚠️ Failed to insert batch in {table_name}: {e}")
                    # Try individual inserts for this batch
                    for values in batch_values:
                        try:
                            new_cursor.execute(insert_sql, values)
                        except Exception as e2:
                            print(f"⚠️ Failed individual insert: {e2}")
                            continue
        
        new_conn.commit()
        print(f"✅ Successfully migrated {migrated_count} rows to {table_name}")
        
        old_cursor.close()
        return migrated_count
        
    except Exception as e:
        print(f"❌ Error migrating {table_name}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def get_old_server_tables(connection):
    """Get list of ALL tables from old server"""
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        cursor.close()
        return tables
    except Exception as e:
        print(f"❌ Error getting tables: {e}")
        return []

def main(host, user, password, database, port=3306):
    print("🔄 Discord Bot Database Migration Tool - FULL MIGRATION")
    print("=" * 60)
    
    OLD_SERVER_CONFIG = {
        'host': host,
        'user': user,
        'password': password,
        'database': database,
        'port': port
    }
    
    print("📋 Migration Configuration:")
    print(f"   Old Server: {host}:{port}")
    print(f"   Database: {database}")
    print(f"   User: {user}")
    print()
    
    # Connect to both servers
    old_conn = connect_old_mysql_server(**OLD_SERVER_CONFIG)
    if not old_conn:
        print("❌ Cannot proceed without connection to old server")
        return
    
    new_conn = connect_new_postgres_server()
    if not new_conn:
        print("❌ Cannot proceed without connection to new server")
        old_conn.close()
        return
    
    try:
        # Get ALL tables from old server
        print("🔍 Scanning old server for ALL tables...")
        old_tables = get_old_server_tables(old_conn)
        print(f"📊 Found {len(old_tables)} tables in old server:")
        for i, table in enumerate(old_tables, 1):
            print(f"   {i:2}. {table}")
        print()
        
        total_migrated = 0
        successful_tables = []
        failed_tables = []
        
        # Migrate ALL tables
        print("🚀 Starting migration of ALL tables...")
        print("=" * 40)
        
        for i, table in enumerate(old_tables, 1):
            print(f"\n📦 [{i}/{len(old_tables)}] Migrating {table}...")
            print("-" * 30)
            
            try:
                count = migrate_table_data(old_conn, new_conn, table)
                total_migrated += count
                if count > 0:
                    successful_tables.append(f"{table} ({count} rows)")
                else:
                    failed_tables.append(f"{table} (no data/failed)")
                    
            except Exception as e:
                print(f"❌ Failed to migrate {table}: {e}")
                failed_tables.append(f"{table} (error: {str(e)[:50]})")
        
        # Final report
        print("\n" + "=" * 60)
        print("🎉 MIGRATION COMPLETED!")
        print("=" * 60)
        print(f"📊 Total rows migrated: {total_migrated}")
        print(f"✅ Successful tables: {len(successful_tables)}")
        print(f"❌ Failed/empty tables: {len(failed_tables)}")
        
        if successful_tables:
            print("\n✅ Successfully migrated:")
            for table in successful_tables:
                print(f"   - {table}")
        
        if failed_tables:
            print("\n❌ Failed or empty tables:")
            for table in failed_tables:
                print(f"   - {table}")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        old_conn.close()
        new_conn.close()
        print("\n🔒 Database connections closed")

if __name__ == "__main__":
    print("🔄 FULL DATABASE MIGRATION TOOL")
    print("This will pull ALL data from ALL tables in your old SQL server")
    print()
    
    # Get connection details from user
    host = input("Enter old server host/IP: ").strip()
    user = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    database = input("Enter database name: ").strip()
    port_input = input("Enter port (default 3306): ").strip()
    
    port = int(port_input) if port_input else 3306
    
    print(f"\n🚀 Starting migration from {host}:{port}/{database}")
    main(host, user, password, database, port)

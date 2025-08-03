#!/usr/bin/env python3
"""
PebbleHost MySQL to PostgreSQL Migration
Pulls ALL data from customer_990306_Server_database
"""
import os
import sys
import psycopg2
import mysql.connector
from datetime import datetime

# Add the cgi-bin directory to the path
sys.path.append('C:/Users/Administrator/Desktop/Bot+Server/DBSBMWEB/cgi-bin')

def connect_old_mysql():
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
        print(f"❌ Failed to connect to PebbleHost MySQL: {e}")
        return None

def connect_new_postgres():
    """Connect to local PostgreSQL server"""
    try:
        from webapp import get_db_connection
        conn = get_db_connection()
        print("✅ Connected to local PostgreSQL server")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return None

def get_mysql_tables(connection):
    """Get all tables from MySQL"""
    try:
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        cursor.close()
        return tables
    except Exception as e:
        print(f"❌ Error getting MySQL tables: {e}")
        return []

def get_postgres_tables(connection):
    """Get all tables from PostgreSQL"""
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = [table[0] for table in cursor.fetchall()]
        cursor.close()
        return tables
    except Exception as e:
        print(f"❌ Error getting PostgreSQL tables: {e}")
        return []

def migrate_table(mysql_conn, postgres_conn, table_name):
    """Migrate a single table"""
    try:
        mysql_cursor = mysql_conn.cursor(dictionary=True)
        postgres_cursor = postgres_conn.cursor()
        
        # Get all data from MySQL
        print(f"🔍 Reading data from {table_name}...")
        mysql_cursor.execute(f"SELECT * FROM {table_name}")
        rows = mysql_cursor.fetchall()
        
        if not rows:
            print(f"⚠️ No data in {table_name}")
            mysql_cursor.close()
            return 0
        
        print(f"📊 Found {len(rows)} rows in {table_name}")
        
        # Get column names
        columns = list(rows[0].keys())
        print(f"📋 Columns: {', '.join(columns)}")
        
        # Clear existing PostgreSQL data
        try:
            postgres_cursor.execute(f"DELETE FROM {table_name}")
            print(f"🗑️ Cleared existing data from {table_name}")
        except Exception as e:
            print(f"⚠️ Could not clear {table_name}: {e}")
        
        # Prepare insert statement
        placeholders = ', '.join(['%s'] * len(columns))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        # Insert data
        migrated = 0
        for row in rows:
            try:
                values = []
                for val in row.values():
                    if isinstance(val, datetime):
                        values.append(val.isoformat())
                    else:
                        values.append(val)
                
                postgres_cursor.execute(insert_sql, values)
                migrated += 1
                
                if migrated % 100 == 0:
                    print(f"📦 Migrated {migrated}/{len(rows)} rows...")
                    
            except Exception as e:
                print(f"⚠️ Failed to insert row: {e}")
                continue
        
        postgres_conn.commit()
        print(f"✅ Successfully migrated {migrated} rows to {table_name}")
        mysql_cursor.close()
        return migrated
        
    except Exception as e:
        print(f"❌ Error migrating {table_name}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def main():
    print("🔄 PebbleHost MySQL → PostgreSQL Migration")
    print("=" * 50)
    print("Source: na05-sql.pebblehost.com")
    print("Target: Local PostgreSQL")
    print()
    
    # Connect to both databases
    mysql_conn = connect_old_mysql()
    if not mysql_conn:
        return
    
    postgres_conn = connect_new_postgres()
    if not postgres_conn:
        mysql_conn.close()
        return
    
    try:
        # Get tables from both servers
        print("🔍 Scanning MySQL tables...")
        mysql_tables = get_mysql_tables(mysql_conn)
        print(f"📊 Found {len(mysql_tables)} MySQL tables:")
        for i, table in enumerate(mysql_tables, 1):
            print(f"   {i:2}. {table}")
        
        print("\n🔍 Scanning PostgreSQL tables...")
        postgres_tables = get_postgres_tables(postgres_conn)
        print(f"📊 Found {len(postgres_tables)} PostgreSQL tables")
        
        # Find matching tables
        matching_tables = [t for t in mysql_tables if t in postgres_tables]
        print(f"\n🎯 Found {len(matching_tables)} matching tables to migrate:")
        for table in matching_tables:
            print(f"   - {table}")
        
        if not matching_tables:
            print("❌ No matching tables found!")
            return
        
        # Migrate all matching tables
        print(f"\n🚀 Starting migration of {len(matching_tables)} tables...")
        print("=" * 50)
        
        total_migrated = 0
        successful = []
        failed = []
        
        for i, table in enumerate(matching_tables, 1):
            print(f"\n📦 [{i}/{len(matching_tables)}] Migrating {table}...")
            print("-" * 30)
            
            count = migrate_table(mysql_conn, postgres_conn, table)
            total_migrated += count
            
            if count > 0:
                successful.append(f"{table} ({count} rows)")
            else:
                failed.append(table)
        
        # Final report
        print("\n" + "=" * 50)
        print("🎉 MIGRATION COMPLETED!")
        print("=" * 50)
        print(f"📊 Total rows migrated: {total_migrated}")
        print(f"✅ Successful tables: {len(successful)}")
        print(f"❌ Failed/empty tables: {len(failed)}")
        
        if successful:
            print("\n✅ Successfully migrated:")
            for table in successful:
                print(f"   - {table}")
        
        if failed:
            print("\n❌ Failed or empty:")
            for table in failed:
                print(f"   - {table}")
                
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mysql_conn.close()
        postgres_conn.close()
        print("\n🔒 Connections closed")

if __name__ == "__main__":
    main()

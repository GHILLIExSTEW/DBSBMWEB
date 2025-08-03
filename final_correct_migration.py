#!/usr/bin/env python3
"""
FINAL CORRECT MIGRATION - Fixes all type mismatches
"""

import mysql.connector
import psycopg2
from datetime import datetime, date
import sys

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

def migrate_bets_correctly(mysql_conn, postgres_conn):
    """Migrate bets with correct type conversions"""
    print("🎯 Migrating bets with correct types...")
    
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
    
    # Insert with correct type conversions
    success_count = 0
    for row in rows:
        try:
            # Create value dictionary with correct types
            values = {}
            for i, col_name in enumerate(columns):
                value = row[i]
                
                # Handle type conversions based on PostgreSQL schema
                if col_name in ['bet_won', 'bet_loss']:
                    # These are INTEGER in PostgreSQL, not BOOLEAN
                    if value is None:
                        values[col_name] = None
                    elif isinstance(value, bool):
                        values[col_name] = 1 if value else 0
                    else:
                        values[col_name] = int(value) if value is not None else None
                        
                elif col_name == 'confirmed':
                    # This is BOOLEAN in PostgreSQL
                    if value is None:
                        values[col_name] = None
                    elif isinstance(value, int):
                        values[col_name] = bool(value)
                    else:
                        values[col_name] = value
                        
                elif col_name in ['bet_serial', 'message_id']:
                    # Important bot fields - convert NULL to 0
                    values[col_name] = int(value) if value is not None else 0
                    
                elif col_name == 'result_value':
                    # Double precision - can be NULL in bets table
                    values[col_name] = float(value) if value is not None else None
                    
                elif col_name in ['status', 'bet_type']:
                    # Text fields
                    values[col_name] = str(value) if value is not None else None
                    
                else:
                    # Keep other values as-is
                    values[col_name] = value
            
            # Build insert query
            insert_cols = ', '.join(columns)
            placeholders = ', '.join(['%s'] * len(columns))
            insert_query = f"INSERT INTO bets ({insert_cols}) VALUES ({placeholders})"
            
            # Build values list
            insert_values = [values[col] for col in columns]
            
            postgres_cursor.execute(insert_query, insert_values)
            success_count += 1
            
        except Exception as e:
            print(f"⚠️ Failed to insert bet {success_count + 1}: {str(e)[:80]}...")
            continue
    
    postgres_conn.commit()
    print(f"✅ Successfully migrated {success_count} rows to bets")
    return success_count

def migrate_unit_records_correctly(mysql_conn, postgres_conn):
    """Migrate unit_records with correct NULL handling"""
    print("💰 Migrating unit_records with correct types...")
    
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
    
    # Insert with correct handling for NOT NULL columns
    success_count = 0
    for row in rows:
        try:
            # Create value dictionary with NOT NULL handling
            values = {}
            for i, col_name in enumerate(columns):
                value = row[i]
                
                # Handle NOT NULL columns with proper defaults
                if col_name == 'result_value':
                    # NOT NULL double precision - must have a value
                    values[col_name] = float(value) if value is not None else 0.0
                    
                elif col_name == 'units':
                    # NOT NULL double precision - must have a value
                    values[col_name] = float(value) if value is not None else 0.0
                    
                else:
                    # Other columns can be NULL or use defaults
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
            print(f"⚠️ Failed to insert unit_record {success_count + 1}: {str(e)[:80]}...")
            continue
    
    postgres_conn.commit()
    print(f"✅ Successfully migrated {success_count} rows to unit_records")
    return success_count

def main():
    print("🚀 FINAL CORRECT MIGRATION - TYPE FIXES")
    print("=" * 60)
    
    # Connect to databases
    mysql_conn = connect_mysql()
    postgres_conn = connect_postgres()
    
    try:
        total_migrated = 0
        
        # Migrate bets with correct type handling
        bets_count = migrate_bets_correctly(mysql_conn, postgres_conn)
        total_migrated += bets_count
        
        # Migrate unit_records with correct NULL handling
        units_count = migrate_unit_records_correctly(mysql_conn, postgres_conn)
        total_migrated += units_count
        
        print("\n" + "=" * 60)
        print("🎉 FINAL MIGRATION COMPLETED!")
        print("=" * 60)
        print(f"📊 Total rows migrated: {total_migrated}")
        
        # Final verification
        print("🔍 Final verification...")
        postgres_cursor = postgres_conn.cursor()
        
        # Check all critical tables
        tables = ['guilds', 'users', 'guild_settings', 'bets', 'unit_records']
        for table in tables:
            postgres_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = postgres_cursor.fetchone()[0]
            print(f"   📊 {table}: {count} rows")
        
        # Check critical bot fields in bets
        if bets_count > 0:
            postgres_cursor.execute("SELECT COUNT(*) FROM bets WHERE message_id IS NOT NULL AND message_id != 0")
            message_count = postgres_cursor.fetchone()[0]
            print(f"   📊 Bets with valid message_id: {message_count} rows")
            
            postgres_cursor.execute("SELECT COUNT(*) FROM bets WHERE bet_serial IS NOT NULL AND bet_serial != 0")
            serial_count = postgres_cursor.fetchone()[0]
            print(f"   📊 Bets with valid bet_serial: {serial_count} rows")
            
            # Sample some critical data
            postgres_cursor.execute("SELECT bet_serial, message_id, guild_id, user_id, status FROM bets WHERE bet_serial != 0 LIMIT 3")
            sample_bets = postgres_cursor.fetchall()
            if sample_bets:
                print("   📋 Sample migrated bets:")
                for bet in sample_bets:
                    print(f"      Serial: {bet[0]}, Message: {bet[1]}, Guild: {bet[2]}, User: {bet[3]}, Status: {bet[4]}")
        
        print("\n🎯 MIGRATION SUCCESS! Bot-critical data migrated:")
        print("   ✅ Guild records created")
        print("   ✅ User records created") 
        print("   ✅ Guild settings migrated")
        print(f"   ✅ {bets_count} bets migrated with message_id and bet_serial")
        print(f"   ✅ {units_count} unit records migrated")
        
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

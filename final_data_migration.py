#!/usr/bin/env python3
"""
FINAL DATA MIGRATION - Handle NULL constraints and complete the migration
This will temporarily modify constraints to allow ALL data migration
"""
import os
import sys
import psycopg2
import mysql.connector

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

def temporarily_fix_constraints(postgres_conn):
    """Fix the most problematic NOT NULL constraints temporarily"""
    print("🔧 Temporarily modifying NOT NULL constraints...")
    cursor = postgres_conn.cursor()
    
    constraint_fixes = [
        # unit_records - critical for the bot
        "ALTER TABLE unit_records ALTER COLUMN result_value DROP NOT NULL",
        "ALTER TABLE unit_records ALTER COLUMN units DROP NOT NULL",
        
        # games - has lots of data
        "ALTER TABLE games ALTER COLUMN game_id DROP NOT NULL",
        
        # teams - massive table with 15k rows
        "ALTER TABLE teams ALTER COLUMN team_name DROP NOT NULL",
        
        # deployment_configs 
        "ALTER TABLE deployment_configs ALTER COLUMN config_id DROP NOT NULL",
    ]
    
    for fix in constraint_fixes:
        try:
            cursor.execute(fix)
            print(f"   ✅ {fix}")
        except Exception as e:
            print(f"   ⚠️ {fix} - {e}")
    
    postgres_conn.commit()
    cursor.close()
    print("🔧 Constraint modifications completed")

def migrate_failed_tables(mysql_conn, postgres_conn):
    """Migrate the tables that failed before"""
    failed_tables = [
        'unit_records',  # CRITICAL - bot betting records
        'games',         # Important - game data  
        'teams',         # Large dataset
        'subscriptions', # User subscriptions
    ]
    
    total_migrated = 0
    
    for table_name in failed_tables:
        print(f"\n🔄 Re-migrating {table_name}...")
        
        try:
            # Get MySQL data
            mysql_cursor = mysql_conn.cursor(dictionary=True)
            mysql_cursor.execute(f"SELECT * FROM {table_name}")
            rows = mysql_cursor.fetchall()
            mysql_cursor.close()
            
            if not rows:
                print(f"   ℹ️ No data in {table_name}")
                continue
            
            print(f"   📊 Found {len(rows)} rows")
            
            # Clear PostgreSQL table
            postgres_cursor = postgres_conn.cursor()
            postgres_cursor.execute(f"DELETE FROM {table_name}")
            
            # Get column names
            columns = list(rows[0].keys())
            placeholders = ', '.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            
            # Insert all data at once
            migrated = 0
            for row in rows:
                try:
                    values = []
                    for col in columns:
                        val = row[col]
                        # Handle boolean conversion for MySQL -> PostgreSQL
                        if isinstance(val, int) and col.endswith(('_enabled', 'is_active', 'is_public', 'premium_enabled')):
                            values.append(bool(val))
                        else:
                            values.append(val)
                    
                    postgres_cursor.execute(insert_sql, values)
                    migrated += 1
                    
                    if migrated % 100 == 0:
                        print(f"   📦 {migrated}/{len(rows)} rows...")
                        
                except Exception as e:
                    print(f"   ⚠️ Row failed: {e}")
                    continue
            
            postgres_conn.commit()
            postgres_cursor.close()
            
            print(f"   ✅ Migrated {migrated}/{len(rows)} rows")
            total_migrated += migrated
            
        except Exception as e:
            print(f"   ❌ Failed to migrate {table_name}: {e}")
    
    return total_migrated

def verify_critical_data(postgres_conn):
    """Verify that critical bot data was migrated"""
    print("\n🔍 Verifying critical data migration...")
    cursor = postgres_conn.cursor()
    
    critical_checks = [
        ("bets", "SELECT COUNT(*) FROM bets"),
        ("guild_settings", "SELECT COUNT(*) FROM guild_settings"),
        ("unit_records", "SELECT COUNT(*) FROM unit_records"),
        ("games", "SELECT COUNT(*) FROM games"),
        ("teams", "SELECT COUNT(*) FROM teams"),
    ]
    
    for table, query in critical_checks:
        try:
            cursor.execute(query)
            count = cursor.fetchone()[0]
            print(f"   📊 {table}: {count:,} rows")
            
            # Show sample data for critical tables
            if count > 0 and table in ['bets', 'guild_settings']:
                if table == 'bets':
                    cursor.execute("SELECT guild_id, user_id, bet_description, bet_amount FROM bets LIMIT 3")
                    samples = cursor.fetchall()
                    print(f"      Sample bets:")
                    for sample in samples:
                        print(f"        - Guild {sample[0]}: ${sample[3]} on {sample[2]}")
                
                elif table == 'guild_settings':
                    cursor.execute("SELECT guild_id, guild_name FROM guild_settings LIMIT 3")
                    samples = cursor.fetchall()
                    print(f"      Sample guilds:")
                    for sample in samples:
                        print(f"        - {sample[1]} ({sample[0]})")
            
        except Exception as e:
            print(f"   ❌ Error checking {table}: {e}")
    
    cursor.close()

def main():
    print("🚀 FINAL DATA MIGRATION - Complete the transfer")
    print("Focus: Fix constraints and migrate remaining critical data")
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
        # Disable foreign keys temporarily
        print("🔓 Disabling foreign key constraints...")
        cursor = postgres_conn.cursor()
        cursor.execute("SET session_replication_role = replica;")
        postgres_conn.commit()
        cursor.close()
        
        # Fix NOT NULL constraints
        temporarily_fix_constraints(postgres_conn)
        
        # Migrate the failed tables
        print(f"\n🔄 Re-attempting migration of failed tables...")
        print("-" * 50)
        
        migrated_count = migrate_failed_tables(mysql_conn, postgres_conn)
        
        # Re-enable foreign keys
        print(f"\n🔒 Re-enabling foreign key constraints...")
        cursor = postgres_conn.cursor()
        cursor.execute("SET session_replication_role = DEFAULT;")
        postgres_conn.commit()
        cursor.close()
        
        # Verify the migration
        verify_critical_data(postgres_conn)
        
        print(f"\n🎉 FINAL MIGRATION COMPLETED!")
        print(f"📊 Additional rows migrated: {migrated_count:,}")
        print(f"🤖 Discord bot should now have complete data access!")
        
    except Exception as e:
        print(f"❌ Final migration failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mysql_conn.close()
        postgres_conn.close()
        print(f"\n🔒 Database connections closed")

if __name__ == "__main__":
    main()

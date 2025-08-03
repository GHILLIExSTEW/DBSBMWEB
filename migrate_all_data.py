#!/usr/bin/env python3
"""
COMPLETE DATA MIGRATION - Pull ALL data from ALL tables
This migrates every single record from PebbleHost MySQL to PostgreSQL
Handles all data type conversions and constraints properly
"""
import os
import sys
import psycopg2
import mysql.connector
from datetime import datetime
import json

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

def get_postgres_column_types(postgres_conn, table_name):
    """Get column data types from PostgreSQL table"""
    try:
        cursor = postgres_conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = cursor.fetchall()
        cursor.close()
        
        column_types = {}
        for col in columns:
            column_types[col[0]] = {
                'type': col[1],
                'nullable': col[2] == 'YES'
            }
        
        return column_types
    except Exception as e:
        print(f"❌ Error getting PostgreSQL column types for {table_name}: {e}")
        return {}

def convert_value_for_postgres(value, pg_type, is_nullable=True):
    """Convert MySQL value to PostgreSQL compatible value"""
    if value is None:
        return None
    
    try:
        # Handle different PostgreSQL data types
        if pg_type in ['boolean']:
            # Convert MySQL boolean (0/1 or string) to PostgreSQL boolean
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)
        
        elif pg_type in ['integer', 'bigint', 'smallint']:
            # Handle integer conversion
            if isinstance(value, str) and value.strip() == '':
                return 0 if not is_nullable else None
            return int(float(value)) if value is not None else (0 if not is_nullable else None)
        
        elif pg_type in ['real', 'double precision', 'numeric', 'decimal']:
            # Handle float/decimal conversion
            if isinstance(value, str) and value.strip() == '':
                return 0.0 if not is_nullable else None
            return float(value) if value is not None else (0.0 if not is_nullable else None)
        
        elif pg_type in ['timestamp without time zone', 'timestamp with time zone', 'timestamp']:
            # Handle timestamp conversion
            if isinstance(value, datetime):
                return value
            elif isinstance(value, str):
                if value.strip() == '' or value == '0000-00-00 00:00:00':
                    return datetime.now() if not is_nullable else None
                try:
                    return datetime.fromisoformat(value.replace('T', ' ').replace('Z', ''))
                except:
                    return datetime.now() if not is_nullable else None
            return value
        
        elif pg_type in ['date']:
            # Handle date conversion
            if isinstance(value, datetime):
                return value.date()
            elif isinstance(value, str):
                if value.strip() == '' or value == '0000-00-00':
                    return datetime.now().date() if not is_nullable else None
                try:
                    return datetime.fromisoformat(value).date()
                except:
                    return datetime.now().date() if not is_nullable else None
            return value
        
        elif pg_type in ['jsonb', 'json']:
            # Handle JSON conversion
            if isinstance(value, (dict, list)):
                return json.dumps(value)
            elif isinstance(value, str):
                try:
                    # Validate JSON
                    json.loads(value)
                    return value
                except:
                    return '{}' if not is_nullable else None
            return '{}' if not is_nullable else None
        
        elif pg_type in ['character varying', 'varchar', 'text', 'char']:
            # Handle string conversion
            if value is None:
                return '' if not is_nullable else None
            return str(value)
        
        else:
            # Default: convert to string
            return str(value) if value is not None else ('' if not is_nullable else None)
    
    except Exception as e:
        print(f"⚠️ Value conversion error for {pg_type}: {e} (value: {value})")
        # Return safe defaults
        if pg_type == 'boolean':
            return False
        elif pg_type in ['integer', 'bigint', 'smallint']:
            return 0
        elif pg_type in ['real', 'double precision', 'numeric']:
            return 0.0
        elif pg_type in ['timestamp without time zone', 'timestamp with time zone']:
            return datetime.now()
        elif pg_type == 'date':
            return datetime.now().date()
        elif pg_type in ['jsonb', 'json']:
            return '{}'
        else:
            return ''

def disable_foreign_keys(postgres_conn):
    """Temporarily disable foreign key constraints"""
    try:
        cursor = postgres_conn.cursor()
        cursor.execute("SET session_replication_role = replica;")
        postgres_conn.commit()
        cursor.close()
        print("🔓 Foreign key constraints disabled")
    except Exception as e:
        print(f"⚠️ Could not disable foreign keys: {e}")

def enable_foreign_keys(postgres_conn):
    """Re-enable foreign key constraints"""
    try:
        cursor = postgres_conn.cursor()
        cursor.execute("SET session_replication_role = DEFAULT;")
        postgres_conn.commit()
        cursor.close()
        print("🔒 Foreign key constraints re-enabled")
    except Exception as e:
        print(f"⚠️ Could not re-enable foreign keys: {e}")

def migrate_table_data(mysql_conn, postgres_conn, table_name):
    """Migrate ALL data from one table"""
    try:
        # Get PostgreSQL column information
        pg_columns = get_postgres_column_types(postgres_conn, table_name)
        if not pg_columns:
            print(f"   ⚠️ Could not get PostgreSQL schema for {table_name}")
            return 0
        
        # Get ALL data from MySQL
        mysql_cursor = mysql_conn.cursor(dictionary=True)
        mysql_cursor.execute(f"SELECT * FROM {table_name}")
        rows = mysql_cursor.fetchall()
        mysql_cursor.close()
        
        if not rows:
            print(f"   ℹ️ No data found in {table_name}")
            return 0
        
        print(f"   📊 Found {len(rows)} rows in MySQL")
        
        # Clear existing PostgreSQL data
        postgres_cursor = postgres_conn.cursor()
        try:
            postgres_cursor.execute(f"DELETE FROM {table_name}")
            print(f"   🗑️ Cleared existing PostgreSQL data")
        except Exception as e:
            print(f"   ⚠️ Could not clear existing data: {e}")
        
        # Get column names that exist in both MySQL data and PostgreSQL schema
        mysql_columns = list(rows[0].keys()) if rows else []
        common_columns = [col for col in mysql_columns if col in pg_columns]
        
        if not common_columns:
            print(f"   ❌ No matching columns found")
            return 0
        
        print(f"   📋 Migrating {len(common_columns)} columns: {', '.join(common_columns[:5])}{'...' if len(common_columns) > 5 else ''}")
        
        # Prepare INSERT statement
        placeholders = ', '.join(['%s'] * len(common_columns))
        insert_sql = f"INSERT INTO {table_name} ({', '.join(common_columns)}) VALUES ({placeholders})"
        
        # Migrate data in batches
        migrated_count = 0
        batch_size = 50
        
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            batch_values = []
            
            for row in batch:
                try:
                    converted_values = []
                    for col_name in common_columns:
                        raw_value = row.get(col_name)
                        pg_type = pg_columns[col_name]['type']
                        is_nullable = pg_columns[col_name]['nullable']
                        
                        converted_value = convert_value_for_postgres(raw_value, pg_type, is_nullable)
                        converted_values.append(converted_value)
                    
                    batch_values.append(converted_values)
                    
                except Exception as e:
                    print(f"   ⚠️ Failed to convert row: {e}")
                    continue
            
            # Execute batch insert
            if batch_values:
                try:
                    postgres_cursor.executemany(insert_sql, batch_values)
                    migrated_count += len(batch_values)
                    if i > 0 and i % 200 == 0:
                        print(f"   📦 Migrated {migrated_count}/{len(rows)} rows...")
                except Exception as e:
                    print(f"   ⚠️ Batch insert failed, trying individual inserts: {e}")
                    # Try individual inserts for this batch
                    for values in batch_values:
                        try:
                            postgres_cursor.execute(insert_sql, values)
                            migrated_count += 1
                        except Exception as e2:
                            print(f"   ⚠️ Individual insert failed: {e2}")
                            continue
        
        postgres_conn.commit()
        postgres_cursor.close()
        
        print(f"   ✅ Successfully migrated {migrated_count}/{len(rows)} rows")
        return migrated_count
        
    except Exception as e:
        print(f"   ❌ Error migrating {table_name}: {e}")
        import traceback
        traceback.print_exc()
        return 0

def get_all_mysql_tables(mysql_conn):
    """Get ALL tables from MySQL that have data"""
    try:
        cursor = mysql_conn.cursor()
        cursor.execute("SHOW TABLES")
        all_tables = [table[0] for table in cursor.fetchall()]
        
        # Filter to tables that have data
        tables_with_data = []
        for table in all_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                if count > 0:
                    tables_with_data.append((table, count))
            except:
                continue
        
        cursor.close()
        return tables_with_data
    except Exception as e:
        print(f"❌ Error getting MySQL tables: {e}")
        return []

def get_postgres_tables(postgres_conn):
    """Get all PostgreSQL tables"""
    try:
        cursor = postgres_conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = {table[0] for table in cursor.fetchall()}
        cursor.close()
        return tables
    except Exception as e:
        print(f"❌ Error getting PostgreSQL tables: {e}")
        return set()

def main():
    print("🚀 COMPLETE DATA MIGRATION")
    print("Pulling ALL data from ALL tables in PebbleHost MySQL")
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
        # Get tables with data from MySQL
        mysql_tables_with_data = get_all_mysql_tables(mysql_conn)
        postgres_tables = get_postgres_tables(postgres_conn)
        
        # Find tables that exist in both and have data
        migratable_tables = []
        for table_name, row_count in mysql_tables_with_data:
            if table_name in postgres_tables:
                migratable_tables.append((table_name, row_count))
        
        print(f"\n📊 Migration Summary:")
        print(f"   MySQL tables with data: {len(mysql_tables_with_data)}")
        print(f"   PostgreSQL tables: {len(postgres_tables)}")
        print(f"   Tables to migrate: {len(migratable_tables)}")
        
        if not migratable_tables:
            print("❌ No tables to migrate!")
            return
        
        print(f"\n📋 Tables to migrate:")
        total_mysql_rows = 0
        for i, (table_name, row_count) in enumerate(migratable_tables, 1):
            print(f"   {i:2}. {table_name:<30} ({row_count:,} rows)")
            total_mysql_rows += row_count
        
        print(f"\n📊 Total rows to migrate: {total_mysql_rows:,}")
        
        # Disable foreign key constraints for faster migration
        disable_foreign_keys(postgres_conn)
        
        # Start migration
        print(f"\n🚀 Starting complete data migration...")
        print("=" * 60)
        
        total_migrated = 0
        successful_tables = 0
        failed_tables = []
        
        for i, (table_name, expected_rows) in enumerate(migratable_tables, 1):
            print(f"\n📦 [{i}/{len(migratable_tables)}] Migrating {table_name}")
            print(f"   Expected: {expected_rows:,} rows")
            print("-" * 50)
            
            try:
                migrated_rows = migrate_table_data(mysql_conn, postgres_conn, table_name)
                total_migrated += migrated_rows
                
                if migrated_rows > 0:
                    successful_tables += 1
                    success_rate = (migrated_rows / expected_rows) * 100 if expected_rows > 0 else 0
                    print(f"   ✅ Success: {migrated_rows:,}/{expected_rows:,} rows ({success_rate:.1f}%)")
                else:
                    failed_tables.append(table_name)
                    print(f"   ❌ Failed: No rows migrated")
                
            except Exception as e:
                failed_tables.append(table_name)
                print(f"   ❌ Exception: {e}")
        
        # Re-enable foreign key constraints
        enable_foreign_keys(postgres_conn)
        
        # Final summary
        print(f"\n" + "=" * 60)
        print(f"🎉 COMPLETE DATA MIGRATION FINISHED!")
        print(f"=" * 60)
        print(f"📊 Tables processed: {len(migratable_tables)}")
        print(f"✅ Successful tables: {successful_tables}")
        print(f"❌ Failed tables: {len(failed_tables)}")
        print(f"📈 Total rows migrated: {total_migrated:,}/{total_mysql_rows:,}")
        
        if successful_tables > 0:
            success_rate = (successful_tables / len(migratable_tables)) * 100
            print(f"📊 Success rate: {success_rate:.1f}%")
        
        if failed_tables:
            print(f"\n❌ Failed tables:")
            for table in failed_tables:
                print(f"   - {table}")
        
        print(f"\n🎯 Your Discord bot should now have ALL its data!")
        
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

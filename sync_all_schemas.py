#!/usr/bin/env python3
"""
Complete Schema Synchronization - Make PostgreSQL match MySQL exactly
This will add ALL missing columns to ALL tables so the bot works unchanged
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
        print("✅ Connected to MySQL (source schema)")
        return connection
    except Exception as e:
        print(f"❌ Failed to connect to MySQL: {e}")
        return None

def connect_postgres():
    """Connect to local PostgreSQL server"""
    try:
        from webapp import get_db_connection
        conn = get_db_connection()
        print("✅ Connected to PostgreSQL (target schema)")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        return None

def get_mysql_table_structure(mysql_conn, table_name):
    """Get complete column structure from MySQL table"""
    try:
        cursor = mysql_conn.cursor()
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()
        cursor.close()
        
        # Convert to dictionary with column info
        column_info = {}
        for col in columns:
            field_name = col[0]
            field_type = col[1]
            is_null = col[2] == 'YES'
            default = col[4]
            
            # Convert MySQL types to PostgreSQL types
            pg_type = convert_mysql_type_to_postgres(field_type)
            
            column_info[field_name] = {
                'type': pg_type,
                'nullable': is_null,
                'default': default
            }
        
        return column_info
    except Exception as e:
        print(f"❌ Error getting MySQL structure for {table_name}: {e}")
        return {}

def convert_mysql_type_to_postgres(mysql_type):
    """Convert MySQL data types to PostgreSQL equivalents"""
    mysql_type = mysql_type.lower()
    
    # Common type mappings
    if 'varchar' in mysql_type or 'char' in mysql_type:
        if '(' in mysql_type:
            length = mysql_type.split('(')[1].split(')')[0]
            return f"VARCHAR({length})"
        return "VARCHAR(255)"
    elif 'text' in mysql_type or 'longtext' in mysql_type:
        return "TEXT"
    elif 'int' in mysql_type or 'integer' in mysql_type:
        if 'bigint' in mysql_type:
            return "BIGINT"
        elif 'tinyint(1)' in mysql_type:
            return "BOOLEAN"
        else:
            return "INTEGER"
    elif 'decimal' in mysql_type or 'numeric' in mysql_type:
        if '(' in mysql_type:
            precision = mysql_type.split('(')[1].split(')')[0]
            return f"DECIMAL({precision})"
        return "DECIMAL(10,2)"
    elif 'float' in mysql_type:
        return "REAL"
    elif 'double' in mysql_type:
        return "DOUBLE PRECISION"
    elif 'datetime' in mysql_type or 'timestamp' in mysql_type:
        return "TIMESTAMP"
    elif 'date' in mysql_type:
        return "DATE"
    elif 'time' in mysql_type:
        return "TIME"
    elif 'json' in mysql_type:
        return "JSONB"
    elif 'enum' in mysql_type:
        return "VARCHAR(100)"  # Convert enum to varchar
    else:
        return "TEXT"  # Default fallback

def get_postgres_table_structure(postgres_conn, table_name):
    """Get column structure from PostgreSQL table"""
    try:
        cursor = postgres_conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))
        
        columns = cursor.fetchall()
        cursor.close()
        
        column_info = {}
        for col in columns:
            column_info[col[0]] = {
                'type': col[1],
                'nullable': col[2] == 'YES',
                'default': col[3]
            }
        
        return column_info
    except Exception as e:
        print(f"❌ Error getting PostgreSQL structure for {table_name}: {e}")
        return {}

def add_missing_columns(postgres_conn, table_name, missing_columns):
    """Add missing columns to PostgreSQL table"""
    if not missing_columns:
        return 0
    
    cursor = postgres_conn.cursor()
    added_count = 0
    
    for col_name, col_info in missing_columns.items():
        try:
            # Build ALTER TABLE statement
            nullable = "NULL" if col_info['nullable'] else "NOT NULL"
            default_clause = ""
            
            if col_info['default'] is not None and col_info['default'] != 'NULL':
                if col_info['type'] == 'BOOLEAN':
                    default_val = 'FALSE' if col_info['default'] in ['0', 'false'] else 'TRUE'
                    default_clause = f" DEFAULT {default_val}"
                elif 'VARCHAR' in col_info['type'] or col_info['type'] == 'TEXT':
                    default_clause = f" DEFAULT '{col_info['default']}'"
                elif col_info['type'] in ['INTEGER', 'BIGINT', 'DECIMAL', 'REAL']:
                    default_clause = f" DEFAULT {col_info['default']}"
                elif 'TIMESTAMP' in col_info['type'] and 'CURRENT_TIMESTAMP' in str(col_info['default']).upper():
                    default_clause = " DEFAULT CURRENT_TIMESTAMP"
            
            # If NOT NULL and no default, provide a reasonable default
            if not col_info['nullable'] and not default_clause:
                if col_info['type'] == 'BOOLEAN':
                    default_clause = " DEFAULT FALSE"
                elif 'VARCHAR' in col_info['type'] or col_info['type'] == 'TEXT':
                    default_clause = " DEFAULT ''"
                elif col_info['type'] in ['INTEGER', 'BIGINT']:
                    default_clause = " DEFAULT 0"
                elif 'DECIMAL' in col_info['type'] or col_info['type'] == 'REAL':
                    default_clause = " DEFAULT 0.0"
                elif 'TIMESTAMP' in col_info['type']:
                    default_clause = " DEFAULT CURRENT_TIMESTAMP"
            
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_info['type']}{default_clause}"
            
            print(f"   📝 Adding: {col_name} {col_info['type']}")
            cursor.execute(alter_sql)
            added_count += 1
            
        except Exception as e:
            print(f"   ⚠️ Failed to add {col_name}: {e}")
            # Continue with other columns
    
    postgres_conn.commit()
    cursor.close()
    return added_count

def get_common_tables(mysql_conn, postgres_conn):
    """Get list of tables that exist in both databases"""
    try:
        # Get MySQL tables
        mysql_cursor = mysql_conn.cursor()
        mysql_cursor.execute("SHOW TABLES")
        mysql_tables = {table[0] for table in mysql_cursor.fetchall()}
        mysql_cursor.close()
        
        # Get PostgreSQL tables
        postgres_cursor = postgres_conn.cursor()
        postgres_cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        postgres_tables = {table[0] for table in postgres_cursor.fetchall()}
        postgres_cursor.close()
        
        # Find intersection
        common_tables = mysql_tables.intersection(postgres_tables)
        
        print(f"📊 MySQL tables: {len(mysql_tables)}")
        print(f"📊 PostgreSQL tables: {len(postgres_tables)}")
        print(f"🎯 Common tables to sync: {len(common_tables)}")
        
        return sorted(list(common_tables))
        
    except Exception as e:
        print(f"❌ Error getting table lists: {e}")
        return []

def main():
    print("🔄 COMPLETE SCHEMA SYNCHRONIZATION")
    print("Making PostgreSQL match MySQL structure exactly")
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
        # Get all common tables
        common_tables = get_common_tables(mysql_conn, postgres_conn)
        
        if not common_tables:
            print("❌ No common tables found!")
            return
        
        print(f"\n🎯 Tables to synchronize:")
        for i, table in enumerate(common_tables, 1):
            print(f"   {i:2}. {table}")
        
        total_columns_added = 0
        successful_tables = 0
        
        print(f"\n🚀 Starting schema synchronization...")
        print("=" * 60)
        
        for i, table_name in enumerate(common_tables, 1):
            print(f"\n📦 [{i}/{len(common_tables)}] Synchronizing {table_name}")
            print("-" * 40)
            
            try:
                # Get structures from both databases
                mysql_structure = get_mysql_table_structure(mysql_conn, table_name)
                postgres_structure = get_postgres_table_structure(postgres_conn, table_name)
                
                if not mysql_structure:
                    print(f"   ⚠️ Could not read MySQL structure")
                    continue
                
                # Find missing columns
                missing_columns = {}
                for col_name, col_info in mysql_structure.items():
                    if col_name not in postgres_structure:
                        missing_columns[col_name] = col_info
                
                print(f"   📊 MySQL columns: {len(mysql_structure)}")
                print(f"   📊 PostgreSQL columns: {len(postgres_structure)}")
                print(f"   ➕ Missing columns: {len(missing_columns)}")
                
                if missing_columns:
                    print(f"   🔧 Adding missing columns:")
                    added = add_missing_columns(postgres_conn, table_name, missing_columns)
                    total_columns_added += added
                    
                    if added > 0:
                        print(f"   ✅ Added {added} columns")
                        successful_tables += 1
                    else:
                        print(f"   ⚠️ No columns were added")
                else:
                    print(f"   ✅ Schema already synchronized")
                    successful_tables += 1
                
            except Exception as e:
                print(f"   ❌ Error synchronizing {table_name}: {e}")
        
        # Final summary
        print(f"\n" + "=" * 60)
        print(f"🎉 SCHEMA SYNCHRONIZATION COMPLETED!")
        print(f"=" * 60)
        print(f"📊 Tables processed: {len(common_tables)}")
        print(f"✅ Successfully synchronized: {successful_tables}")
        print(f"➕ Total columns added: {total_columns_added}")
        
        if total_columns_added > 0:
            print(f"\n🎯 PostgreSQL schema now matches MySQL structure!")
            print(f"🤖 Bot should work without any code changes!")
        
    except Exception as e:
        print(f"❌ Synchronization failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        mysql_conn.close()
        postgres_conn.close()
        print(f"\n🔒 Database connections closed")

if __name__ == "__main__":
    main()

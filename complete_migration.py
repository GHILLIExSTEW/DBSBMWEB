#!/usr/bin/env python3
"""
COMPLETE DATA MIGRATION - Final comprehensive migration
Handle all type conversions and duplicate issues properly
"""

import mysql.connector
import psycopg2
import psycopg2.extras
import logging
import sys
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_migration.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def connect_mysql():
    """Connect to PebbleHost MySQL server"""
    try:
        conn = mysql.connector.connect(
            host='na05-sql.pebblehost.com',
            port=3306,
            user='customer_990306_Server_database',
            password='NGNrWmR@IypQb4k@tzgk+NnI',
            database='customer_990306_Server_database',
            charset='utf8mb4',
            autocommit=True,
            auth_plugin='mysql_native_password'
        )
        logger.info("Connected to PebbleHost MySQL server")
        return conn
    except Exception as e:
        logger.error(f"MySQL connection failed: {e}")
        return None

def connect_postgres():
    """Connect to local PostgreSQL server"""
    try:
        # Import webapp to get connection function
        sys.path.append('cgi-bin')
        from webapp import get_db_connection
        conn = get_db_connection()
        logger.info("Connected to local PostgreSQL server")
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return None

def convert_value_for_postgres(value, column_name, mysql_column_type):
    """Convert MySQL values to PostgreSQL compatible format"""
    if value is None:
        return None
    
    # Handle boolean conversions (MySQL stores as 0/1, PostgreSQL needs true/false)
    if 'national' in column_name.lower() or 'bool' in mysql_column_type.lower() or 'tinyint(1)' in mysql_column_type.lower():
        if isinstance(value, (int, str)):
            return bool(int(value))
        return bool(value)
    
    # Handle JSON and text fields
    if isinstance(value, (dict, list)):
        import json
        return json.dumps(value)
    
    return value

def get_table_schema(cursor, table_name, is_mysql=True):
    """Get column information for a table"""
    if is_mysql:
        cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'customer_990306_Server_database' 
            AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """)
    else:
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = '{table_name}'
            ORDER BY ordinal_position
        """)
    
    return cursor.fetchall()

def disable_foreign_keys(postgres_cursor):
    """Disable foreign key constraints during migration"""
    try:
        postgres_cursor.execute("SET session_replication_role = replica;")
        logger.info("Disabled foreign key constraints")
    except Exception as e:
        logger.warning(f"Could not disable foreign keys: {e}")

def enable_foreign_keys(postgres_cursor):
    """Re-enable foreign key constraints after migration"""
    try:
        postgres_cursor.execute("SET session_replication_role = DEFAULT;")
        logger.info("Re-enabled foreign key constraints")
    except Exception as e:
        logger.warning(f"Could not re-enable foreign keys: {e}")

def clear_existing_data(postgres_cursor, table_name):
    """Clear existing data from table to avoid duplicates"""
    try:
        postgres_cursor.execute(f"DELETE FROM {table_name}")
        deleted_count = postgres_cursor.rowcount
        logger.info(f"Cleared {deleted_count} existing rows from {table_name}")
        return deleted_count
    except Exception as e:
        logger.warning(f"Could not clear {table_name}: {e}")
        return 0

def migrate_table_data(mysql_conn, postgres_conn, table_name):
    """Migrate all data from MySQL table to PostgreSQL table"""
    mysql_cursor = mysql_conn.cursor(dictionary=True)
    postgres_cursor = postgres_conn.cursor()
    
    try:
        # Get table schemas
        mysql_schema = get_table_schema(mysql_cursor, table_name, is_mysql=True)
        postgres_schema = get_table_schema(postgres_cursor, table_name, is_mysql=False)
        
        # Create column mapping
        mysql_columns = {col[0]: col for col in mysql_schema}
        postgres_columns = {col[0]: col for col in postgres_schema}
        
        # Find common columns
        common_columns = list(set(mysql_columns.keys()) & set(postgres_columns.keys()))
        if not common_columns:
            logger.warning(f"No common columns found for {table_name}")
            return 0
        
        # Clear existing data to avoid duplicates
        clear_existing_data(postgres_cursor, table_name)
        
        # Get all data from MySQL
        mysql_cursor.execute(f"SELECT * FROM {table_name}")
        rows = mysql_cursor.fetchall()
        
        if not rows:
            logger.info(f"No data to migrate for {table_name}")
            return 0
        
        migrated_count = 0
        failed_count = 0
        
        # Prepare insert statement
        columns_str = ', '.join(common_columns)
        placeholders = ', '.join(['%s'] * len(common_columns))
        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        logger.info(f"Migrating {len(rows)} rows from {table_name}...")
        
        for row in rows:
            try:
                # Convert values for PostgreSQL
                values = []
                for col_name in common_columns:
                    mysql_col_info = mysql_columns.get(col_name)
                    mysql_type = mysql_col_info[4] if mysql_col_info else ''  # COLUMN_TYPE
                    
                    converted_value = convert_value_for_postgres(
                        row.get(col_name), 
                        col_name, 
                        mysql_type
                    )
                    values.append(converted_value)
                
                postgres_cursor.execute(insert_sql, values)
                migrated_count += 1
                
            except Exception as e:
                failed_count += 1
                if failed_count <= 5:  # Only log first 5 failures to avoid spam
                    logger.warning(f"Row failed in {table_name}: {str(e)[:100]}...")
        
        postgres_conn.commit()
        
        logger.info(f"✅ {table_name}: {migrated_count} rows migrated, {failed_count} failed")
        return migrated_count
        
    except Exception as e:
        logger.error(f"Failed to migrate {table_name}: {e}")
        postgres_conn.rollback()
        return 0
    
    finally:
        mysql_cursor.close()

def main():
    print("🚀 COMPLETE DATA MIGRATION - Final comprehensive migration")
    print("Handle all type conversions and duplicates properly")
    print("=" * 60)
    
    # Connect to databases
    mysql_conn = connect_mysql()
    if not mysql_conn:
        print("❌ MySQL connection failed")
        return
    
    postgres_conn = connect_postgres()
    if not postgres_conn:
        print("❌ PostgreSQL connection failed")
        return
    
    postgres_cursor = postgres_conn.cursor()
    
    try:
        # Disable foreign key constraints
        disable_foreign_keys(postgres_cursor)
        
        # Critical tables to migrate
        critical_tables = [
            'unit_records',
            'games', 
            'teams',
            'bets',
            'guild_settings',
            'deployment_configs',
            'user_balances',
            'user_stats',
            'server_config',
            'live_games'
        ]
        
        total_migrated = 0
        
        for table in critical_tables:
            print(f"\n🔄 Migrating {table}...")
            migrated = migrate_table_data(mysql_conn, postgres_conn, table)
            total_migrated += migrated
        
        # Re-enable foreign keys
        enable_foreign_keys(postgres_cursor)
        
        print(f"\n✅ MIGRATION COMPLETE!")
        print(f"📊 Total rows migrated: {total_migrated}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"❌ Migration failed: {e}")
    
    finally:
        if postgres_conn:
            postgres_conn.close()
        if mysql_conn:
            mysql_conn.close()
        print("🔒 Database connections closed")

if __name__ == "__main__":
    main()

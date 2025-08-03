#!/usr/bin/env python3
"""
Fixed migration with proper dependency handling
"""

import mysql.connector
import psycopg2
import logging
from datetime import datetime, date
import sys

# Set up logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
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
        logger.info("✅ Connected to PebbleHost MySQL server")
        return conn
    except Exception as e:
        logger.error(f"❌ MySQL connection failed: {e}")
        sys.exit(1)

def connect_postgres():
    """Connect to local PostgreSQL"""
    try:
        sys.path.append(r"C:\Users\Administrator\Desktop\Bot+Server\DBSBMWEB\cgi-bin")
        from webapp import get_db_connection
        conn = get_db_connection()
        logger.info("✅ Connected to local PostgreSQL server")
        return conn
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        sys.exit(1)

def convert_value(value, postgres_type):
    """Convert MySQL value to PostgreSQL compatible value"""
    if value is None:
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
            return int(value) if value is not None else None
        except:
            return value
    
    # Handle text conversions
    elif postgres_type.lower() in ['text', 'varchar', 'character varying']:
        return str(value) if value is not None else None
    
    # Default: return as-is
    return value

def create_missing_guilds(mysql_conn, postgres_conn):
    """Create missing guild records based on references in other tables"""
    logger.info("🏗️ Creating missing guild records...")
    
    mysql_cursor = mysql_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    # Get all unique guild_ids from bets and guild_settings
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
    
    logger.info(f"🔍 Found {len(guild_ids)} unique guild IDs to create")
    
    # Create minimal guild records
    for guild_id in guild_ids:
        try:
            postgres_cursor.execute("""
                INSERT INTO guilds (guild_id, guild_name, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (guild_id) DO NOTHING
            """, (
                guild_id,
                f"Guild {guild_id}",  # Default name
                True,  # Default active
                datetime.now(),
                datetime.now()
            ))
            logger.info(f"✅ Created guild record for ID: {guild_id}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to create guild {guild_id}: {e}")
    
    postgres_conn.commit()
    logger.info("✅ Guild creation completed")

def migrate_table_with_deps(table_name, mysql_conn, postgres_conn):
    """Migrate a single table with dependency handling"""
    logger.info(f"📦 Migrating {table_name}")
    logger.info("-" * 40)
    
    mysql_cursor = mysql_conn.cursor()
    postgres_cursor = postgres_conn.cursor()
    
    try:
        # Get data from MySQL
        mysql_cursor.execute(f"SELECT * FROM {table_name}")
        rows = mysql_cursor.fetchall()
        
        if not rows:
            logger.warning(f"⚠️ No data in {table_name}")
            return 0
        
        logger.info(f"📊 Found {len(rows)} rows in {table_name}")
        
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
        logger.info(f"🗑️ Cleared existing data from {table_name}")
        
        # Build insert query
        placeholders = ', '.join(['%s'] * len(columns))
        insert_query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        # Insert data with conversion
        success_count = 0
        for row in rows:
            try:
                # Convert values based on PostgreSQL types
                converted_row = []
                for i, value in enumerate(row):
                    col_name = columns[i]
                    pg_type = pg_columns.get(col_name, 'text')
                    converted_value = convert_value(value, pg_type)
                    converted_row.append(converted_value)
                
                postgres_cursor.execute(insert_query, converted_row)
                success_count += 1
            except Exception as e:
                logger.warning(f"⚠️ Failed to insert row: {str(e)[:100]}...")
                continue
        
        postgres_conn.commit()
        logger.info(f"✅ Successfully migrated {success_count} rows to {table_name}")
        return success_count
        
    except Exception as e:
        logger.error(f"❌ Error migrating {table_name}: {e}")
        postgres_conn.rollback()
        return 0

def main():
    logger.info("🚀 FIXED MIGRATION WITH DEPENDENCY HANDLING")
    logger.info("=" * 60)
    
    # Connect to databases
    mysql_conn = connect_mysql()
    postgres_conn = connect_postgres()
    
    try:
        # Step 1: Create missing guild records
        create_missing_guilds(mysql_conn, postgres_conn)
        
        # Step 2: Migrate in dependency order
        migration_order = [
            'guilds',           # Base table (already has records now)
            'users',            # User records
            'guild_users',      # Guild-user relationships
            'guild_settings',   # Guild configuration
            'bets',             # Betting records (depends on guilds)
            'unit_records',     # Unit tracking (depends on guilds)
            'subscriptions',    # Subscription records (depends on guilds)
            'teams',            # Team data (independent)
            'leagues',          # League data (independent)
            'games'             # Game data (depends on teams/leagues)
        ]
        
        total_migrated = 0
        
        for table in migration_order:
            try:
                count = migrate_table_with_deps(table, mysql_conn, postgres_conn)
                total_migrated += count
                logger.info("")
            except Exception as e:
                logger.error(f"❌ Failed to migrate {table}: {e}")
                continue
        
        logger.info("=" * 60)
        logger.info("🎉 MIGRATION COMPLETED!")
        logger.info("=" * 60)
        logger.info(f"📊 Total rows migrated: {total_migrated}")
        
        # Verification
        logger.info("🔍 Verifying migration...")
        postgres_cursor = postgres_conn.cursor()
        
        key_tables = ['guilds', 'bets', 'unit_records', 'guild_settings']
        for table in key_tables:
            postgres_cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = postgres_cursor.fetchone()[0]
            logger.info(f"   📊 {table}: {count} rows")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
    
    finally:
        mysql_conn.close()
        postgres_conn.close()
        logger.info("🔒 Database connections closed")

if __name__ == "__main__":
    main()

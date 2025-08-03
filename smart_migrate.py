#!/usr/bin/env python3
"""
Smart PebbleHost Migration - Handles schema differences
Focuses on the most important tables: guilds, guild_settings, users, bets
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

def get_mysql_data(mysql_conn, query):
    """Execute a query on MySQL and return results"""
    try:
        cursor = mysql_conn.cursor(dictionary=True)
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        return results
    except Exception as e:
        print(f"❌ MySQL query failed: {e}")
        return []

def migrate_guilds(mysql_conn, postgres_conn):
    """Migrate guild data"""
    print("🏰 Migrating guilds...")
    
    # Get guilds from MySQL
    guilds_data = get_mysql_data(mysql_conn, "SELECT * FROM guilds LIMIT 10")
    print(f"📊 Found {len(guilds_data)} guilds in MySQL")
    
    if not guilds_data:
        return 0
    
    postgres_cursor = postgres_conn.cursor()
    migrated = 0
    
    for guild in guilds_data:
        try:
            # Map MySQL columns to PostgreSQL columns
            postgres_cursor.execute("""
                INSERT INTO guilds (guild_id, guild_name, description, is_public, premium_enabled, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (guild_id) DO UPDATE SET
                guild_name = EXCLUDED.guild_name,
                description = EXCLUDED.description
            """, (
                str(guild.get('guild_id', guild.get('id', ''))),
                guild.get('guild_name', guild.get('name', 'Unknown Guild')),
                guild.get('description', ''),
                bool(guild.get('is_public', True)),
                bool(guild.get('premium_enabled', False)),
                guild.get('created_at', datetime.now())
            ))
            migrated += 1
        except Exception as e:
            print(f"⚠️ Failed to migrate guild {guild.get('guild_id', 'unknown')}: {e}")
    
    postgres_conn.commit()
    print(f"✅ Migrated {migrated} guilds")
    return migrated

def migrate_guild_settings(mysql_conn, postgres_conn):
    """Migrate guild settings"""
    print("⚙️ Migrating guild settings...")
    
    settings_data = get_mysql_data(mysql_conn, "SELECT * FROM guild_settings LIMIT 10")
    print(f"📊 Found {len(settings_data)} guild settings in MySQL")
    
    if not settings_data:
        return 0
    
    postgres_cursor = postgres_conn.cursor()
    migrated = 0
    
    for setting in settings_data:
        try:
            postgres_cursor.execute("""
                INSERT INTO guild_settings (guild_id, guild_name, betting_enabled, max_bet_amount, default_currency)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (guild_id) DO UPDATE SET
                guild_name = EXCLUDED.guild_name,
                betting_enabled = EXCLUDED.betting_enabled,
                max_bet_amount = EXCLUDED.max_bet_amount
            """, (
                str(setting.get('guild_id', '')),
                setting.get('guild_name', 'Unknown Guild'),
                bool(setting.get('betting_enabled', True)),
                float(setting.get('max_bet_amount', 1000.0)),
                setting.get('default_currency', 'USD')
            ))
            migrated += 1
        except Exception as e:
            print(f"⚠️ Failed to migrate guild setting: {e}")
    
    postgres_conn.commit()
    print(f"✅ Migrated {migrated} guild settings")
    return migrated

def migrate_users(mysql_conn, postgres_conn):
    """Migrate user data"""
    print("👥 Migrating users...")
    
    users_data = get_mysql_data(mysql_conn, "SELECT * FROM users LIMIT 20")
    print(f"📊 Found {len(users_data)} users in MySQL")
    
    if not users_data:
        return 0
    
    postgres_cursor = postgres_conn.cursor()
    migrated = 0
    
    for user in users_data:
        try:
            postgres_cursor.execute("""
                INSERT INTO users (user_id, username, email, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                username = EXCLUDED.username
            """, (
                str(user.get('user_id', user.get('id', ''))),
                user.get('username', user.get('name', 'Unknown User')),
                user.get('email', ''),
                user.get('created_at', datetime.now())
            ))
            migrated += 1
        except Exception as e:
            print(f"⚠️ Failed to migrate user: {e}")
    
    postgres_conn.commit()
    print(f"✅ Migrated {migrated} users")
    return migrated

def migrate_bets(mysql_conn, postgres_conn):
    """Migrate betting data with column mapping"""
    print("🎲 Migrating bets...")
    
    bets_data = get_mysql_data(mysql_conn, "SELECT * FROM bets LIMIT 50")
    print(f"📊 Found {len(bets_data)} bets in MySQL")
    
    if not bets_data:
        return 0
    
    postgres_cursor = postgres_conn.cursor()
    migrated = 0
    
    for bet in bets_data:
        try:
            # Map MySQL bet structure to PostgreSQL bet structure
            postgres_cursor.execute("""
                INSERT INTO bets (
                    guild_id, user_id, bet_description, bet_amount, odds, status, 
                    created_at, bet_type, sport, team_name, opponent
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                str(bet.get('guild_id', '')),
                str(bet.get('user_id', '')),
                bet.get('bet_details', bet.get('player_prop', 'Bet')),
                float(bet.get('bet_amount', bet.get('units', 0.0))),
                float(bet.get('odds', 1.0)),
                bet.get('status', 'pending'),
                bet.get('created_at', datetime.now()),
                bet.get('bet_type', 'standard'),
                bet.get('sport', bet.get('league', '')),
                bet.get('team_name', bet.get('team', '')),
                bet.get('away_team', bet.get('opponent', ''))
            ))
            migrated += 1
        except Exception as e:
            print(f"⚠️ Failed to migrate bet: {e}")
    
    postgres_conn.commit()
    print(f"✅ Migrated {migrated} bets")
    return migrated

def get_mysql_table_sample(mysql_conn, table_name, limit=5):
    """Get a sample of data from MySQL table"""
    try:
        cursor = mysql_conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        results = cursor.fetchall()
        cursor.close()
        return results
    except Exception as e:
        print(f"❌ Error sampling {table_name}: {e}")
        return []

def main():
    print("🎯 SMART PebbleHost Migration")
    print("Focus: Core Discord bot data migration")
    print("=" * 50)
    
    # Connect to both servers
    mysql_conn = connect_old_mysql()
    if not mysql_conn:
        return
    
    postgres_conn = connect_new_postgres()
    if not postgres_conn:
        mysql_conn.close()
        return
    
    try:
        total_migrated = 0
        
        # Let's first examine what data we actually have
        print("\n🔍 Examining MySQL data structure...")
        important_tables = ['guilds', 'guild_settings', 'users', 'bets', 'unit_records']
        
        for table in important_tables:
            sample = get_mysql_table_sample(mysql_conn, table, 2)
            if sample:
                print(f"📋 {table} sample columns: {list(sample[0].keys())}")
            else:
                print(f"⚠️ {table} is empty or doesn't exist")
        
        print(f"\n🚀 Starting focused migration...")
        print("-" * 40)
        
        # Migrate core tables
        total_migrated += migrate_guilds(mysql_conn, postgres_conn)
        total_migrated += migrate_guild_settings(mysql_conn, postgres_conn)
        total_migrated += migrate_users(mysql_conn, postgres_conn)
        total_migrated += migrate_bets(mysql_conn, postgres_conn)
        
        print(f"\n🎉 Migration completed!")
        print(f"📊 Total records migrated: {total_migrated}")
        
        # Verify the migration
        print(f"\n🔍 Verifying migration...")
        postgres_cursor = postgres_conn.cursor()
        
        postgres_cursor.execute("SELECT COUNT(*) FROM guilds")
        guild_count = postgres_cursor.fetchone()[0]
        print(f"📊 Guilds in PostgreSQL: {guild_count}")
        
        postgres_cursor.execute("SELECT COUNT(*) FROM bets")
        bet_count = postgres_cursor.fetchone()[0]
        print(f"🎲 Bets in PostgreSQL: {bet_count}")
        
        if guild_count > 0:
            postgres_cursor.execute("SELECT guild_id, guild_name FROM guilds LIMIT 3")
            guilds = postgres_cursor.fetchall()
            print("🏰 Sample guilds:")
            for guild in guilds:
                print(f"   - {guild[1]} ({guild[0]})")
                
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

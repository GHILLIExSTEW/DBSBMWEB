#!/usr/bin/env python3
import os
import sys
import psycopg2

# Add the cgi-bin directory to the path
sys.path.append('C:/Users/Administrator/Desktop/Bot+Server/DBSBMWEB/cgi-bin')

try:
    from webapp import get_db_connection
    
    print("🔍 Connecting to database...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    tables = cursor.fetchall()
    print(f"📊 Found {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check if guild_settings exists and has data
    table_names = [table[0] for table in tables]
    if 'guild_settings' in table_names:
        cursor.execute("SELECT COUNT(*) FROM guild_settings")
        count = cursor.fetchone()[0]
        print(f"🏰 Guild settings table has {count} records")
        
        if count > 0:
            cursor.execute("SELECT guild_id, guild_name FROM guild_settings LIMIT 3")
            guilds = cursor.fetchall()
            print("Sample guilds:")
            for guild in guilds:
                print(f"  - {guild[0]}: {guild[1]}")
    else:
        print("⚠️ No guild_settings table found")
    
    cursor.close()
    conn.close()
    print("✅ Database check completed successfully")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

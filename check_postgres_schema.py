#!/usr/bin/env python3
"""
Check PostgreSQL schema
"""

import sys
sys.path.append(r"C:\Users\Administrator\Desktop\Bot+Server\DBSBMWEB\cgi-bin")

def check_postgres_schema():
    try:
        from webapp import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("🔍 CHECKING POSTGRESQL SCHEMA")
        print("=" * 50)
        
        # Check guilds table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default 
            FROM information_schema.columns 
            WHERE table_name = 'guilds' AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        print("📋 GUILDS TABLE STRUCTURE:")
        for row in cursor.fetchall():
            print(f"   {row[0]} | {row[1]} | Nullable: {row[2]} | Default: {row[3]}")
        
        # Check bets table foreign keys
        cursor.execute("""
            SELECT 
                tc.constraint_name, 
                tc.table_name, 
                kcu.column_name, 
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name 
            FROM 
                information_schema.table_constraints AS tc 
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' 
            AND tc.table_name = 'bets'
        """)
        
        print("\n📋 BETS TABLE FOREIGN KEYS:")
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]}.{row[2]} -> {row[3]}.{row[4]}")
            
        # Check current data
        cursor.execute("SELECT COUNT(*) FROM guilds")
        guild_count = cursor.fetchone()[0]
        print(f"\n📊 Current guilds count: {guild_count}")
        
        if guild_count > 0:
            cursor.execute("SELECT * FROM guilds LIMIT 3")
            guilds = cursor.fetchall()
            print("📋 Sample guilds:")
            for guild in guilds:
                print(f"   {guild}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_postgres_schema()

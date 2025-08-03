#!/usr/bin/env python3
"""
Quick script to check guild data in MySQL
"""

import pymysql

def check_guild_data():
    print("🔍 CHECKING GUILD DATA IN MYSQL")
    print("=" * 50)
    
    # Connect to PebbleHost MySQL
    mysql_conn = pymysql.connect(
        host='na05-sql.pebblehost.com',
        user='DBSBM_Data',
        password='JensenIsKind',
        database='DBSBM_Data',
        charset='utf8mb4'
    )
    
    try:
        cursor = mysql_conn.cursor()
        
        # Check guilds table
        cursor.execute("SELECT COUNT(*) FROM guilds")
        guild_count = cursor.fetchone()[0]
        print(f"📊 Guilds table: {guild_count} rows")
        
        if guild_count > 0:
            cursor.execute("SELECT * FROM guilds LIMIT 5")
            guilds = cursor.fetchall()
            print("\n🔍 Sample guild records:")
            for guild in guilds:
                print(f"   Guild ID: {guild[0]}")
        else:
            print("⚠️ No guilds found in MySQL!")
            
        # Check for guild IDs referenced in other tables
        cursor.execute("SELECT DISTINCT guild_id FROM bets LIMIT 10")
        bet_guilds = cursor.fetchall()
        print(f"\n📊 Guild IDs in bets table: {len(bet_guilds)} unique")
        for guild_id in bet_guilds[:5]:
            print(f"   Guild ID: {guild_id[0]}")
            
        cursor.execute("SELECT DISTINCT guild_id FROM guild_settings LIMIT 10") 
        settings_guilds = cursor.fetchall()
        print(f"\n📊 Guild IDs in guild_settings table: {len(settings_guilds)} unique")
        for guild_id in settings_guilds[:5]:
            print(f"   Guild ID: {guild_id[0]}")
            
    finally:
        mysql_conn.close()

if __name__ == "__main__":
    check_guild_data()

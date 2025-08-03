#!/usr/bin/env python3
import os
import sys
import psycopg2

# Add the cgi-bin directory to the path
sys.path.append('C:/Users/Administrator/Desktop/Bot+Server/DBSBMWEB/cgi-bin')

try:
    from webapp import get_db_connection
    
    print("🏗️ Adding sample guild data...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Add sample guilds
    sample_guilds = [
        ('1234567890123456789', 'Test Gaming Server', 'A testing Discord server for the bot', True, True),
        ('9876543210987654321', 'Sports Betting Hub', 'Community for sports betting enthusiasts', True, False),
        ('5555666677778888999', 'Private VIP Club', 'Exclusive private betting community', False, True),
    ]
    
    # Check if guilds table is empty first
    cursor.execute("SELECT COUNT(*) FROM guilds")
    existing_count = cursor.fetchone()[0]
    
    if existing_count == 0:
        print("📝 Inserting sample guilds...")
        for guild_id, name, description, is_public, has_premium in sample_guilds:
            cursor.execute("""
                INSERT INTO guilds (guild_id, guild_name, description, is_public, premium_enabled)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (guild_id) DO NOTHING
            """, (guild_id, name, description, is_public, has_premium))
        
        # Add corresponding guild settings
        print("⚙️ Adding guild settings...")
        for guild_id, name, _, _, _ in sample_guilds:
            cursor.execute("""
                INSERT INTO guild_settings (guild_id, guild_name, betting_enabled, max_bet_amount, default_currency)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (guild_id) DO NOTHING
            """, (guild_id, name, True, 1000.0, 'USD'))
        
        # Add some sample bets
        print("🎲 Adding sample betting data...")
        sample_bets = [
            ('1234567890123456789', '111111111111111111', 'Team A vs Team B', 100.0, 1.8, 'pending'),
            ('1234567890123456789', '222222222222222222', 'Match X vs Match Y', 50.0, 2.1, 'won'),
            ('9876543210987654321', '333333333333333333', 'Championship Final', 200.0, 1.5, 'lost'),
        ]
        
        for guild_id, user_id, description, amount, odds, status in sample_bets:
            cursor.execute("""
                INSERT INTO bets (guild_id, user_id, bet_description, bet_amount, odds, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, (guild_id, user_id, description, amount, odds, status))
        
        conn.commit()
        print("✅ Sample data added successfully!")
    else:
        print(f"ℹ️ Database already has {existing_count} guilds, skipping sample data")
    
    # Verify the data
    cursor.execute("SELECT guild_id, guild_name, is_public FROM guilds LIMIT 5")
    guilds = cursor.fetchall()
    print("\n🏰 Current guilds in database:")
    for guild in guilds:
        status = "Public" if guild[2] else "Private"
        print(f"  - {guild[1]} ({status})")
    
    cursor.execute("SELECT COUNT(*) FROM bets")
    bet_count = cursor.fetchone()[0]
    print(f"\n🎲 Total bets in database: {bet_count}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

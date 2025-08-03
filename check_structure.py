#!/usr/bin/env python3
import os
import sys
import psycopg2

# Add the cgi-bin directory to the path
sys.path.append('C:/Users/Administrator/Desktop/Bot+Server/DBSBMWEB/cgi-bin')

try:
    from webapp import get_db_connection
    
    print("🔍 Checking PostgreSQL table structures...")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check bets table structure
    print("\n📊 BETS table structure:")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'bets' AND table_schema = 'public'
        ORDER BY ordinal_position
    """)
    bets_columns = cursor.fetchall()
    for col in bets_columns:
        print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
    
    # Check unit_records table structure
    print("\n📊 UNIT_RECORDS table structure:")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'unit_records' AND table_schema = 'public'
        ORDER BY ordinal_position
    """)
    unit_columns = cursor.fetchall()
    for col in unit_columns:
        print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
    
    # Check teams table structure
    print("\n📊 TEAMS table structure:")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'teams' AND table_schema = 'public'
        ORDER BY ordinal_position
    """)
    teams_columns = cursor.fetchall()
    for col in teams_columns:
        print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
    
    cursor.close()
    conn.close()
    print("\n✅ Structure check completed")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

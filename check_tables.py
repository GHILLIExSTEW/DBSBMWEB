#!/usr/bin/env python3
import os
import sys
import psycopg2

# Add the cgi-bin directory to the path
sys.path.append('C:/Users/Administrator/Desktop/Bot+Server/DBSBMWEB/cgi-bin')

try:
    # Direct PostgreSQL connection
    conn = psycopg2.connect(
        host='localhost',
        user='postgres',
        password='password',
        database='dbsbm',
        port=5432
    )
    cursor = conn.cursor()
    
    # Check multiple tables
    tables_to_check = ['unit_records', 'bets', 'guilds', 'guild_settings', 'users']
    
    for table in tables_to_check:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table}: {count} records")
        except Exception as e:
            print(f"{table}: Error - {e}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Connection error: {e}")

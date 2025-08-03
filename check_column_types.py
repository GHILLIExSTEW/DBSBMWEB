#!/usr/bin/env python3
"""
Check the exact PostgreSQL column types to fix the migration
"""

import sys
sys.path.append(r"C:\Users\Administrator\Desktop\Bot+Server\DBSBMWEB\cgi-bin")

def check_column_types():
    try:
        from webapp import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("🔍 CHECKING COLUMN TYPES")
        print("=" * 50)
        
        # Check bets table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'bets' AND table_schema = 'public'
            AND column_name IN ('bet_won', 'bet_loss', 'confirmed', 'result_value')
            ORDER BY column_name
        """)
        
        print("📋 BETS TABLE - PROBLEMATIC COLUMNS:")
        for row in cursor.fetchall():
            print(f"   {row[0]} | {row[1]} | Nullable: {row[2]}")
        
        # Check unit_records table structure  
        cursor.execute("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'unit_records' AND table_schema = 'public'
            AND column_name IN ('result_value', 'transaction_type', 'units')
            ORDER BY column_name
        """)
        
        print("\n📋 UNIT_RECORDS TABLE - PROBLEMATIC COLUMNS:")
        for row in cursor.fetchall():
            print(f"   {row[0]} | {row[1]} | Nullable: {row[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_column_types()

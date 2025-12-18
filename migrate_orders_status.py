"""
Migration script to update purchase_orders table to use 'Pending' as default status
Run this once to update your existing database
"""

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')

print(f"Connecting to MySQL database at {DB_HOST}:{DB_PORT}...")

try:
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor
    )
    print("✓ Connected successfully!")
    
    cursor = conn.cursor()
    
    # Update existing completed orders to pending
    print("\nUpdating existing orders to 'Pending' status...")
    cursor.execute("UPDATE purchase_orders SET status = 'Pending' WHERE status = 'Completed'")
    updated_rows = cursor.rowcount
    print(f"✓ Updated {updated_rows} existing orders")
    
    # Alter table to change default value
    print("\nUpdating table schema to set default status as 'Pending'...")
    cursor.execute("ALTER TABLE purchase_orders MODIFY COLUMN status VARCHAR(50) DEFAULT 'Pending'")
    print("✓ Schema updated successfully!")
    
    conn.commit()
    print("\n✅ Migration completed successfully!")
    print("Now when patients checkout, orders will be created as 'Pending' and require admin approval.")
    
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    if conn:
        conn.close()

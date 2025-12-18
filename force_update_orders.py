"""
Force update all orders and verify the fix
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

conn = pymysql.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    cursorclass=pymysql.cursors.DictCursor
)

cursor = conn.cursor()

print("=== Updating ALL orders to 'Pending' status ===")
cursor.execute("UPDATE purchase_orders SET status = 'Pending'")
updated = cursor.rowcount
print(f"✓ Updated {updated} orders to Pending")

conn.commit()

print("\n=== Current orders status ===")
cursor.execute("SELECT id, patient_id, status, total_amount FROM purchase_orders ORDER BY id DESC LIMIT 10")
orders = cursor.fetchall()
for order in orders:
    print(f"Order #{order['id']}: Status = {order['status']}, Amount = ₱{order['total_amount']}")

conn.close()
print("\n✅ All orders are now set to 'Pending'")
print("⚠️  IMPORTANT: You MUST restart Flask app completely!")
print("   1. Stop Flask (Ctrl+C)")
print("   2. Run: py app.py")

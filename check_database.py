"""
Check current database status and orders
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

# Check table structure
print("=== Checking purchase_orders table structure ===")
cursor.execute("SHOW CREATE TABLE purchase_orders")
result = cursor.fetchone()
print(result['Create Table'])

print("\n=== Recent orders ===")
cursor.execute("SELECT id, patient_id, status, purchased_at FROM purchase_orders ORDER BY id DESC LIMIT 5")
orders = cursor.fetchall()
for order in orders:
    print(f"Order #{order['id']}: Status = {order['status']}, Date = {order['purchased_at']}")

conn.close()

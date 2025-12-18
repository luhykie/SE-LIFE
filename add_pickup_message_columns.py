import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MySQL Database configuration
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')

try:
    # Connect to MySQL
    connection = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    
    cursor = connection.cursor()
    
    print("Connected to database successfully!")
    print("\nAdding new columns to purchase_orders table...")
    
    # Add pickup_date column
    try:
        cursor.execute("""
            ALTER TABLE purchase_orders
            ADD COLUMN pickup_date DATE NULL
        """)
        print("✓ Added pickup_date column")
    except pymysql.err.OperationalError as e:
        if "Duplicate column name" in str(e):
            print("✓ pickup_date column already exists")
        else:
            raise
    
    # Add admin_message column
    try:
        cursor.execute("""
            ALTER TABLE purchase_orders
            ADD COLUMN admin_message TEXT NULL
        """)
        print("✓ Added admin_message column")
    except pymysql.err.OperationalError as e:
        if "Duplicate column name" in str(e):
            print("✓ admin_message column already exists")
        else:
            raise
    
    connection.commit()
    print("\n✅ Database migration completed successfully!")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"❌ Error: {e}")

"""
Quick test script to verify MySQL database connection.
Run this to ensure your Aiven MySQL credentials are correct.

Usage:
    python test_connection.py
"""

import pymysql
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get database credentials from environment variables
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')

print("=" * 60)
print("MySQL Connection Test")
print("=" * 60)

# Check if credentials are set
print("\n📋 Checking environment variables...")
missing = []
if not DB_HOST:
    missing.append("DB_HOST")
if not DB_USER:
    missing.append("DB_USER")
if not DB_PASSWORD:
    missing.append("DB_PASSWORD")
if not DB_NAME:
    missing.append("DB_NAME")

if missing:
    print(f"❌ Missing environment variables: {', '.join(missing)}")
    print("\nPlease set the following environment variables:")
    for var in missing:
        print(f"  - {var}")
    sys.exit(1)

print("✓ All required environment variables are set")

# Display connection details (without password)
print("\n🔗 Connection Details:")
print(f"  Host: {DB_HOST}")
print(f"  Port: {DB_PORT}")
print(f"  User: {DB_USER}")
print(f"  Database: {DB_NAME}")
print(f"  Password: {'*' * len(DB_PASSWORD)}")

# Try to connect
print("\n🔌 Attempting to connect to MySQL...")
try:
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        connect_timeout=10
    )
    
    print("✅ Connection successful!")
    
    # Get server info
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()[0]
    print(f"\n📊 MySQL Server Version: {version}")
    
    # List tables
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    
    if tables:
        print(f"\n📁 Found {len(tables)} tables in database:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]} ({count} rows)")
    else:
        print("\n⚠️  No tables found. Run 'python init_mysql_db.py' to initialize.")
    
    # Check connection variables
    cursor.execute("SHOW VARIABLES LIKE 'max_connections'")
    max_conn = cursor.fetchone()
    print(f"\n⚙️  Server Max Connections: {max_conn[1]}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Your database is ready to use.")
    print("=" * 60)
    
except pymysql.err.OperationalError as e:
    print(f"\n❌ Connection failed: {e}")
    print("\n💡 Troubleshooting tips:")
    print("  1. Verify your Aiven service is running (check dashboard)")
    print("  2. Check that all credentials are correct")
    print("  3. Ensure your IP is allowed (Aiven usually allows all by default)")
    print("  4. Try pinging the host to check network connectivity")
    sys.exit(1)
    
except pymysql.err.ProgrammingError as e:
    print(f"\n❌ Database error: {e}")
    print("\n💡 The database name might be incorrect.")
    print("   Check your Aiven dashboard for the correct database name.")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    sys.exit(1)

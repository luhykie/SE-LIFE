"""
Migration script to add password column to logs table
Run this script to update your existing database
"""
import pymysql
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_HOST = os.environ.get('DB_HOST')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')

def migrate():
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
        
        # Check if password column already exists in logs
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'logs' 
            AND COLUMN_NAME = 'password'
        """, (DB_NAME,))
        
        exists = cursor.fetchone()[0]
        
        if exists:
            print("✓ Column 'password' already exists in logs table")
        else:
            # Add the password column
            cursor.execute("""
                ALTER TABLE logs 
                ADD COLUMN password VARCHAR(255)
            """)
            connection.commit()
            print("✓ Successfully added 'password' column to logs table")
        
        cursor.close()
        connection.close()
        print("\nMigration completed successfully!")
        print("\n⚠️  IMPORTANT: When adding new patients, make sure to set a password.")
        print("⚠️  Existing patients may need to have their passwords set by an admin.")
        
    except Exception as e:
        print(f"✗ Error during migration: {e}")
        print("\nIf you're using SQLite, the column will be created automatically on next run.")

if __name__ == "__main__":
    print("Starting migration to add password column to logs table...")
    migrate()

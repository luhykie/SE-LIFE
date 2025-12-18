"""
Check DOB format in database
"""
import sqlite3

try:
    # Try SQLite first
    conn = sqlite3.connect('patient_records.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=== Checking patients DOB format ===")
    cursor.execute("SELECT id, first_name, last_name, dob FROM patients LIMIT 5")
    patients = cursor.fetchall()
    
    for patient in patients:
        print(f"Patient #{patient['id']}: {patient['first_name']} {patient['last_name']}")
        print(f"  DOB: {patient['dob']} (type: {type(patient['dob'])})")
        print()
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    print("\nTrying MySQL...")
    
    try:
        import pymysql
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        
        conn = pymysql.connect(
            host=os.environ.get('DB_HOST'),
            port=int(os.environ.get('DB_PORT', 3306)),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            database=os.environ.get('DB_NAME'),
            cursorclass=pymysql.cursors.DictCursor
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT id, first_name, last_name, dob FROM patients LIMIT 5")
        patients = cursor.fetchall()
        
        for patient in patients:
            print(f"Patient #{patient['id']}: {patient['first_name']} {patient['last_name']}")
            print(f"  DOB: {patient['dob']} (type: {type(patient['dob'])})")
            print()
        
        conn.close()
        
    except Exception as e2:
        print(f"MySQL Error: {e2}")

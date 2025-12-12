"""
Script to initialize MySQL database with all required tables and seed data.
Run this once after setting up your Aiven MySQL database.

Usage:
    python init_mysql_db.py

Make sure to set the environment variables before running:
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
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

# Validate all credentials are present
if not all([DB_HOST, DB_USER, DB_PASSWORD, DB_NAME]):
    print("ERROR: Missing required environment variables!")
    print("Please set: DB_HOST, DB_USER, DB_PASSWORD, DB_NAME")
    sys.exit(1)

print(f"Connecting to MySQL database at {DB_HOST}:{DB_PORT}...")

try:
    # Connect to MySQL
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
    
    # Create tables
    print("\nCreating tables...")
    
    # Patients table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INT AUTO_INCREMENT PRIMARY KEY,
            last_name VARCHAR(255) NOT NULL,
            first_name VARCHAR(255) NOT NULL,
            middle_name VARCHAR(255),
            suffix VARCHAR(50),
            dob DATE NOT NULL,
            sex VARCHAR(50) NOT NULL,
            contact VARCHAR(50),
            address TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Patients table created")
    
    # Logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            log_id INT AUTO_INCREMENT PRIMARY KEY,
            id INT,
            last_name VARCHAR(255),
            first_name VARCHAR(255),
            middle_name VARCHAR(255),
            suffix VARCHAR(50),
            dob DATE,
            sex VARCHAR(50),
            contact VARCHAR(50),
            address TEXT,
            notes TEXT,
            action VARCHAR(50),
            deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("✓ Logs table created")
    
    # Workers/Admin table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            barangay_id VARCHAR(255) PRIMARY KEY,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL
        )
    """)
    print("✓ Workers table created")
    
    # Patient accounts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_accounts (
            patient_id INT PRIMARY KEY,
            username VARCHAR(255) UNIQUE,
            password VARCHAR(255) NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        )
    """)
    print("✓ Patient accounts table created")
    
    # Marketplace Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marketplace_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            stock INT NOT NULL,
            price DECIMAL(10, 2) DEFAULT 0
        )
    """)
    print("✓ Marketplace items table created")
    
    # Cart table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL,
            item_id INT NOT NULL,
            quantity INT NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        )
    """)
    print("✓ Cart table created")
    
    # Medical Services table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medical_services (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            category VARCHAR(100) NOT NULL
        )
    """)
    print("✓ Medical services table created")
    
    # Health Records table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_records (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL UNIQUE,
            blood_type VARCHAR(10),
            allergies TEXT,
            chronic_conditions TEXT,
            status VARCHAR(50) DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        )
    """)
    print("✓ Health records table created")
    
    # Service Requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS service_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL,
            service_id INT NOT NULL,
            request_type VARCHAR(100) NOT NULL,
            notes TEXT,
            status VARCHAR(50) DEFAULT 'Pending',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
            FOREIGN KEY (service_id) REFERENCES medical_services(id) ON DELETE CASCADE
        )
    """)
    print("✓ Service requests table created")
    
    # Purchase Orders table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            patient_id INT NOT NULL,
            total_amount DECIMAL(10, 2) NOT NULL,
            status VARCHAR(50) DEFAULT 'Completed',
            purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
        )
    """)
    print("✓ Purchase orders table created")
    
    # Purchase Order Items table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS purchase_order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT NOT NULL,
            item_id INT NOT NULL,
            item_name VARCHAR(255) NOT NULL,
            quantity INT NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (order_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES marketplace_items(id) ON DELETE CASCADE
        )
    """)
    print("✓ Purchase order items table created")
    
    # Add seed data
    print("\nAdding seed data...")
    
    # Default admin
    cursor.execute("SELECT * FROM workers WHERE barangay_id = 'ADMIN123'")
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO workers (barangay_id, password, role) VALUES ('ADMIN123', 'password', 'worker')")
        print("✓ Default admin added (ID: ADMIN123, Password: password)")
    
    # Default patient
    cursor.execute("SELECT * FROM patients WHERE id = 1")
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO patients (id, last_name, first_name, dob, sex, contact) VALUES (1, 'Dela Cruz', 'Juan', '1990-01-01', 'Male', '09170000001')")
        print("✓ Default patient added")
    
    # Default patient account
    cursor.execute("SELECT * FROM patient_accounts WHERE patient_id = 1")
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO patient_accounts (patient_id, username, password) VALUES (1, '1', 'password')")
        print("✓ Default patient account added (Username: 1, Password: password)")
    
    # Default health record
    cursor.execute("SELECT * FROM health_records WHERE patient_id = 1")
    if cursor.fetchone() is None:
        cursor.execute("""
            INSERT INTO health_records (patient_id, blood_type, allergies, chronic_conditions, status) 
            VALUES (1, 'O+', 'Penicillin, Peanuts', 'None', 'Active')
        """)
        print("✓ Default health record added")
    
    # Default marketplace items
    cursor.execute("SELECT COUNT(*) as cnt FROM marketplace_items")
    count_result = cursor.fetchone()
    if count_result['cnt'] == 0:
        cursor.execute("""
            INSERT INTO marketplace_items (name, description, stock, price) VALUES 
            ('Vitamin C Supplement', 'Boost your immunity with Vitamin C', 50, 150.00),
            ('First Aid Kit', 'Complete first aid kit for emergencies', 10, 500.00),
            ('Pain Reliever', 'Fast-acting pain relief tablets', 100, 75.00),
            ('Blood Pressure Monitor', 'Digital blood pressure monitoring device', 15, 2500.00),
            ('Thermometer', 'Digital thermometer for accurate readings', 30, 200.00)
        """)
        print("✓ Default marketplace items added (5 items)")
    
    # Default medical services
    cursor.execute("SELECT COUNT(*) as cnt FROM medical_services")
    count_services = cursor.fetchone()
    if count_services['cnt'] == 0:
        cursor.execute("""
            INSERT INTO medical_services (name, description, category) VALUES 
            ('Vaccine', 'Immunization services', 'Preventive'),
            ('Dental Appointment', 'Professional dental care and checkup', 'Dental'),
            ('Health Checkup', 'Comprehensive physical examination', 'General'),
            ('Blood Test', 'Laboratory blood analysis', 'Laboratory'),
            ('Consultation', 'Medical consultation with healthcare provider', 'General'),
            ('Eye Checkup', 'Vision and eye health examination', 'Specialist')
        """)
        print("✓ Default medical services added (6 services)")
    
    conn.commit()
    print("\n✅ Database initialization completed successfully!")
    print("\nYou can now run your Flask application with USE_MYSQL=True")
    
except pymysql.Error as e:
    print(f"\n❌ Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
finally:
    if 'conn' in locals():
        conn.close()
        print("Database connection closed.")

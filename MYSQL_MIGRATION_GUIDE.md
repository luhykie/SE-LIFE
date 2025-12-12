# Migration Guide: SQLite to MySQL with Aiven

This guide will help you migrate your SE-LIFE Flask application from SQLite to MySQL hosted on Aiven.

## Why MySQL with Aiven?

- **Real-time Synchronization**: Changes are instantly visible across all users
- **Cloud Hosted**: No need to manage database files locally
- **Scalable**: Better performance for multiple concurrent users
- **Reliable**: Automatic backups and high availability

## Step 1: Set up Aiven MySQL Database

1. **Create an Aiven Account**
   - Go to https://aiven.io
   - Sign up for a free account
   - Verify your email

2. **Create a MySQL Service**
   - Click "Create Service"
   - Select "MySQL"
   - Choose a cloud provider and region (select one close to your Render region)
   - Select the Free tier (sufficient for testing)
   - Give it a name (e.g., "se-life-db")
   - Click "Create Service"
   - Wait 5-10 minutes for provisioning

3. **Get Connection Details**
   - Once the service is running, go to the "Overview" tab
   - Note down these values:
     - **Host**: (e.g., `mysql-xxxxx.aivencloud.com`)
     - **Port**: Usually `3306`
     - **User**: Usually `avnadmin`
     - **Password**: Click "Show" to reveal it
     - **Database**: `defaultdb` (or create a new database)

4. **Download SSL Certificate** (Optional but recommended)
   - In the service page, go to the "Overview" tab
   - Download the CA certificate if you want SSL connections

## Step 2: Initialize the MySQL Database

### Option A: Local Initialization (Recommended for first-time setup)

1. **Install dependencies locally:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables** (replace with your Aiven credentials):
   
   **On Windows (PowerShell):**
   ```powershell
   $env:DB_HOST="your-mysql-host.aivencloud.com"
   $env:DB_PORT="3306"
   $env:DB_USER="avnadmin"
   $env:DB_PASSWORD="your-password"
   $env:DB_NAME="defaultdb"
   ```
   
   **On Windows (CMD):**
   ```cmd
   set DB_HOST=your-mysql-host.aivencloud.com
   set DB_PORT=3306
   set DB_USER=avnadmin
   set DB_PASSWORD=your-password
   set DB_NAME=defaultdb
   ```
   
   **On Mac/Linux:**
   ```bash
   export DB_HOST="your-mysql-host.aivencloud.com"
   export DB_PORT="3306"
   export DB_USER="avnadmin"
   export DB_PASSWORD="your-password"
   export DB_NAME="defaultdb"
   ```

3. **Run the initialization script:**
   ```bash
   python init_mysql_db.py
   ```

   You should see output like:
   ```
   ✓ Connected successfully!
   ✓ Patients table created
   ✓ Logs table created
   ...
   ✅ Database initialization completed successfully!
   ```

### Option B: Python Shell

If you prefer, you can also initialize the database directly from Python:

```python
import os
os.environ['USE_MYSQL'] = 'True'
os.environ['DB_HOST'] = 'your-mysql-host.aivencloud.com'
os.environ['DB_PORT'] = '3306'
os.environ['DB_USER'] = 'avnadmin'
os.environ['DB_PASSWORD'] = 'your-password'
os.environ['DB_NAME'] = 'defaultdb'

from app import init_db
init_db()
```

## Step 3: Test Locally with MySQL

1. **Set environment variables** (same as Step 2)

2. **Add one more variable to enable MySQL:**
   ```bash
   # Windows PowerShell
   $env:USE_MYSQL="True"
   
   # Windows CMD
   set USE_MYSQL=True
   
   # Mac/Linux
   export USE_MYSQL="True"
   ```

3. **Run your Flask app:**
   ```bash
   python app.py
   ```

4. **Test the application:**
   - Open browser to `http://localhost:5000`
   - Login with default credentials:
     - Admin: ID=`ADMIN123`, Password=`password`
     - Patient: Username=`1`, Password=`password`
   - Add a patient, edit records, etc.
   - Verify changes are being saved to MySQL

## Step 4: Deploy to Render

1. **Update Render Environment Variables**
   - Go to your Render dashboard
   - Select your "se-life" service
   - Go to "Environment" tab
   - Add the following environment variables:

   | Key | Value | Secret? |
   |-----|-------|---------|
   | `USE_MYSQL` | `True` | No |
   | `DB_HOST` | Your Aiven MySQL host | No |
   | `DB_PORT` | `3306` | No |
   | `DB_USER` | Your Aiven username | No |
   | `DB_PASSWORD` | Your Aiven password | **Yes** |
   | `DB_NAME` | `defaultdb` (or your database name) | No |

2. **Push your code to Git:**
   ```bash
   git add .
   git commit -m "Migrate to MySQL with Aiven"
   git push origin main
   ```

3. **Deploy on Render:**
   - Render will automatically detect the changes and start deploying
   - Monitor the deployment logs
   - Wait for the deployment to complete

4. **Verify deployment:**
   - Visit your Render app URL
   - Login and test functionality
   - Data should now sync in real-time!

## Step 5: Migrate Existing Data (Optional)

If you have existing data in `patients.db` that you want to migrate to MySQL:

### Using a Python Script

Create a file `migrate_data.py`:

```python
import sqlite3
import pymysql
import os

# SQLite connection
sqlite_conn = sqlite3.connect('patients.db')
sqlite_conn.row_factory = sqlite3.Row
sqlite_cursor = sqlite_conn.cursor()

# MySQL connection
mysql_conn = pymysql.connect(
    host=os.environ['DB_HOST'],
    port=int(os.environ.get('DB_PORT', 3306)),
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    database=os.environ['DB_NAME'],
    cursorclass=pymysql.cursors.DictCursor
)
mysql_cursor = mysql_conn.cursor()

# Migrate patients
print("Migrating patients...")
sqlite_cursor.execute("SELECT * FROM patients WHERE id > 1")  # Skip default patient
for row in sqlite_cursor.fetchall():
    mysql_cursor.execute("""
        INSERT INTO patients (last_name, first_name, middle_name, suffix, dob, sex, contact, address, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (row['last_name'], row['first_name'], row['middle_name'], row['suffix'], 
          row['dob'], row['sex'], row['contact'], row['address'], row['notes']))

# Migrate other tables similarly...

mysql_conn.commit()
print("Migration completed!")

sqlite_conn.close()
mysql_conn.close()
```

Run it:
```bash
python migrate_data.py
```

## Testing the Migration

1. **Test Admin Functions:**
   - Login as admin (ADMIN123 / password)
   - View all patients
   - Add a new patient
   - Edit patient records
   - Delete a patient and check logs

2. **Test Patient Functions:**
   - Login as patient (1 / password)
   - View profile
   - Update health records
   - Add items to cart
   - Request medical services
   - Place an order

3. **Test Real-time Sync:**
   - Open two browser windows
   - Login to both
   - Make changes in one window
   - Refresh the other window
   - Changes should be reflected immediately!

## Troubleshooting

### Connection Issues

**Problem:** Can't connect to Aiven MySQL

**Solutions:**
- Verify all environment variables are set correctly
- Check if Aiven service is running (green status)
- Verify firewall allows outbound connections to port 3306
- Check if you're using the correct password (no extra spaces)

### SSL/TLS Errors

**Problem:** SSL certificate verification failed

**Solution:** Add `ssl={'verify_mode': False}` to connection (not recommended for production):
```python
db = pymysql.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    ssl={'verify_mode': False}
)
```

### Table Creation Errors

**Problem:** Error creating tables

**Solution:** Make sure you have CREATE privileges. Check Aiven user permissions.

### Character Encoding Issues

**Problem:** Special characters not displaying correctly

**Solution:** Add charset to connection:
```python
db = pymysql.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    charset='utf8mb4'
)
```

## Switching Between SQLite and MySQL

The code now supports both databases:

- **Local Development (SQLite):** Don't set `USE_MYSQL` or set it to `False`
- **Production (MySQL):** Set `USE_MYSQL=True` with all DB credentials

This allows you to:
- Develop locally with SQLite (no internet needed)
- Deploy to production with MySQL (real-time sync)

## Important Notes

1. **Free Tier Limits:** Aiven free tier has limitations. Monitor your usage.
2. **Connection Pooling:** For production, consider implementing connection pooling.
3. **Backups:** Aiven provides automatic backups, but export important data regularly.
4. **Security:** Always use environment variables for sensitive data.
5. **SSL:** For production, enable SSL connections to Aiven.

## Support

If you encounter issues:
- Check Aiven service logs
- Check Render deployment logs
- Review Flask application logs
- Contact Aiven support for database issues
- Contact Render support for deployment issues

## Next Steps

1. ✅ Set up proper authentication (change default passwords!)
2. ✅ Enable SSL for database connections
3. ✅ Set up monitoring and alerting
4. ✅ Implement proper error handling
5. ✅ Add database connection pooling for better performance

---

**Congratulations!** Your application now uses MySQL with real-time synchronization! 🎉

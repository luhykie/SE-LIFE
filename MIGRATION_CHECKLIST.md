# MySQL Migration Checklist

Use this checklist to track your migration progress!

## ☐ Phase 1: Aiven Setup (15 minutes)

- [ ] Create Aiven account at https://aiven.io
- [ ] Verify email
- [ ] Create new MySQL service
  - [ ] Select cloud provider & region
  - [ ] Choose Free tier
  - [ ] Name your service (e.g., "se-life-db")
- [ ] Wait for provisioning to complete (5-10 min)
- [ ] Note down connection details:
  - [ ] Host: ____________________
  - [ ] Port: ____________________ (usually 3306)
  - [ ] User: ____________________ (usually avnadmin)
  - [ ] Password: ____________________
  - [ ] Database: ____________________ (usually defaultdb)

## ☐ Phase 2: Local Setup (10 minutes)

- [ ] Install Python dependencies
  ```bash
  pip install -r requirements.txt
  ```

- [ ] Set environment variables (choose your OS):
  
  **Windows PowerShell:**
  ```powershell
  $env:DB_HOST="your-host.aivencloud.com"
  $env:DB_PORT="3306"
  $env:DB_USER="avnadmin"
  $env:DB_PASSWORD="your-password"
  $env:DB_NAME="defaultdb"
  ```
  
  **Windows CMD:**
  ```cmd
  set DB_HOST=your-host.aivencloud.com
  set DB_PORT=3306
  set DB_USER=avnadmin
  set DB_PASSWORD=your-password
  set DB_NAME=defaultdb
  ```
  
  **Mac/Linux:**
  ```bash
  export DB_HOST="your-host.aivencloud.com"
  export DB_PORT="3306"
  export DB_USER="avnadmin"
  export DB_PASSWORD="your-password"
  export DB_NAME="defaultdb"
  ```

- [ ] Test database connection
  ```bash
  python test_connection.py
  ```
  - [ ] Connection successful?
  - [ ] Can see server version?

- [ ] Initialize database
  ```bash
  python init_mysql_db.py
  ```
  - [ ] All tables created?
  - [ ] Seed data inserted?

## ☐ Phase 3: Local Testing (10 minutes)

- [ ] Enable MySQL mode
  ```bash
  # Windows PowerShell
  $env:USE_MYSQL="True"
  
  # Windows CMD
  set USE_MYSQL=True
  
  # Mac/Linux
  export USE_MYSQL="True"
  ```

- [ ] Run application
  ```bash
  python app.py
  ```

- [ ] Test admin functions:
  - [ ] Login as admin (ADMIN123 / password)
  - [ ] View patient list
  - [ ] Add new patient
  - [ ] Edit patient record
  - [ ] Delete patient
  - [ ] View logs

- [ ] Test patient functions:
  - [ ] Login as patient (1 / password)
  - [ ] View profile
  - [ ] Update health records
  - [ ] Browse marketplace
  - [ ] Add items to cart
  - [ ] Request medical service
  - [ ] Place order

- [ ] Verify data persistence:
  - [ ] Stop the app
  - [ ] Restart the app
  - [ ] Changes still there?

## ☐ Phase 4: Deploy to Render (15 minutes)

- [ ] Go to Render dashboard
- [ ] Select your "se-life" service
- [ ] Go to "Environment" tab
- [ ] Add environment variables:
  - [ ] `USE_MYSQL` = `True`
  - [ ] `DB_HOST` = (your Aiven host)
  - [ ] `DB_PORT` = `3306`
  - [ ] `DB_USER` = (your Aiven user)
  - [ ] `DB_PASSWORD` = (your Aiven password) ⚠️ **Mark as secret!**
  - [ ] `DB_NAME` = (your database name)

- [ ] Commit and push code:
  ```bash
  git add .
  git commit -m "Add MySQL support with Aiven"
  git push origin main
  ```

- [ ] Monitor deployment:
  - [ ] Deployment started?
  - [ ] No build errors?
  - [ ] Deployment successful?

- [ ] Test production app:
  - [ ] Open Render app URL
  - [ ] Login works?
  - [ ] Can view/add/edit/delete records?
  - [ ] Data persists after refresh?

## ☐ Phase 5: Real-Time Sync Testing (5 minutes)

- [ ] Open app in two different browsers/windows
- [ ] Login to both
- [ ] Make changes in one window:
  - [ ] Add a patient
  - [ ] Edit a record
  - [ ] Add marketplace item to cart
- [ ] Refresh the other window
  - [ ] Changes appear immediately?
  - [ ] Data is synchronized?

## ☐ Phase 6: Security & Cleanup (10 minutes)

- [ ] Change default passwords:
  - [ ] Admin password changed?
  - [ ] Test patient password changed?

- [ ] Review security:
  - [ ] Database password marked as secret in Render?
  - [ ] .env file NOT committed to git?
  - [ ] .gitignore includes .env?

- [ ] Create backup:
  - [ ] Note where Aiven stores automatic backups
  - [ ] Export important data manually?

- [ ] Update documentation:
  - [ ] Add your specific Aiven details (without passwords!)
  - [ ] Document any custom changes

## ☐ Optional Enhancements

- [ ] Install python-dotenv for easier local development
  ```bash
  pip install python-dotenv
  ```
  - [ ] Add to requirements.txt
  - [ ] Create .env file
  - [ ] Update app.py to load .env

- [ ] Enable SSL for database connection
  - [ ] Download CA certificate from Aiven
  - [ ] Update connection to use SSL

- [ ] Set up monitoring:
  - [ ] Configure Aiven alerts
  - [ ] Set up Render alerts
  - [ ] Monitor database size

- [ ] Performance optimization:
  - [ ] Add database connection pooling
  - [ ] Add query caching
  - [ ] Optimize slow queries

## 📊 Troubleshooting Checklist

If something doesn't work:

- [ ] **Can't connect to MySQL:**
  - [ ] All environment variables set correctly?
  - [ ] Aiven service status is "Running"?
  - [ ] No typos in host/password?
  - [ ] Run `python test_connection.py` for diagnostics

- [ ] **Tables not created:**
  - [ ] Ran `python init_mysql_db.py`?
  - [ ] Check for error messages
  - [ ] User has CREATE privileges?

- [ ] **App uses SQLite on Render:**
  - [ ] `USE_MYSQL=True` set in Render environment?
  - [ ] All DB_* variables set?
  - [ ] Redeployed after setting variables?

- [ ] **Data not syncing:**
  - [ ] Using production URL (not localhost)?
  - [ ] Both users connected to same database?
  - [ ] Refresh the page after changes?

- [ ] **Character encoding issues:**
  - [ ] Special characters not displaying?
  - [ ] Try adding charset='utf8mb4' to connection

## ✅ Migration Complete!

When all boxes are checked:
- ✅ You have a cloud-hosted MySQL database
- ✅ Your app supports real-time synchronization
- ✅ Local development still works with SQLite
- ✅ Production uses MySQL on Render
- ✅ Data persists across deployments

**🎉 Congratulations! Your migration is complete!**

---

## 📞 Support Resources

- **Aiven Documentation:** https://docs.aiven.io
- **Aiven Support:** Available in dashboard
- **Render Documentation:** https://render.com/docs
- **PyMySQL Documentation:** https://pymysql.readthedocs.io
- **Flask Documentation:** https://flask.palletsprojects.com

## 📝 Notes

Use this space to record any custom configurations or issues you encountered:

```
[Your notes here]
```

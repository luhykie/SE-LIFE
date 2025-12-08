from flask import Flask, render_template, request, redirect, url_for, g, session
import sqlite3
from datetime import datetime, date 
from functools import wraps

app = Flask(__name__)
DATABASE = "patients.db"
app.secret_key = 'this_is_a_secure_random_key_for_session_management' 

# -----------------------------
# Security & Utility Functions
# -----------------------------

def login_required(f):
    """Decorator to enforce worker/admin login for specific routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != 'worker':
            # Redirect non-workers to the worker sign-in page
            return redirect(url_for('worker_signin'))
        return f(*args, **kwargs)
    return decorated_function

def calculate_age(dob_str):
    """Calculates age accurately from a DOB string (YYYY-MM-DD)."""
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except (ValueError, TypeError):
        return None

# -----------------------------
# Database Connection & Setup
# -----------------------------
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Patients table
    c.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            middle_name TEXT,
            suffix TEXT,
            dob TEXT NOT NULL,
            sex TEXT NOT NULL,
            contact TEXT,
            address TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Logs table
    c.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER,
            last_name TEXT,
            first_name TEXT,
            middle_name TEXT,
            suffix TEXT,
            dob TEXT,
            sex TEXT,
            contact TEXT,
            address TEXT,
            notes TEXT,
            action TEXT,
            deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Workers/Admin table
    c.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            barangay_id TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)
    # Patient accounts table (separate from patient demographics)
    c.execute("""
        CREATE TABLE IF NOT EXISTS patient_accounts (
            patient_id INTEGER UNIQUE,
            username TEXT UNIQUE,
            password TEXT NOT NULL,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    """)
    # Marketplace Items table
    c.execute("""
        CREATE TABLE IF NOT EXISTS marketplace_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            stock INTEGER NOT NULL,
            price REAL DEFAULT 0
        )
    """)
    # Cart table (stores temporary cart items per patient session)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    """)
    # Medical Services table
    c.execute("""
        CREATE TABLE IF NOT EXISTS medical_services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL
        )
    """)
    # Health Records table (patient health information)
    c.execute("""
        CREATE TABLE IF NOT EXISTS health_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL UNIQUE,
            blood_type TEXT,
            allergies TEXT,
            chronic_conditions TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    """)
    
    # Service Requests table (patient requests for medical services)
    c.execute("""
        CREATE TABLE IF NOT EXISTS service_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            request_type TEXT NOT NULL,
            notes TEXT,
            status TEXT DEFAULT 'Pending',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (service_id) REFERENCES medical_services(id)
        )
    """)
    
    # Add a default admin if none exists (for testing)
    c.execute("SELECT * FROM workers WHERE barangay_id = 'ADMIN123'")
    if c.fetchone() is None:
        c.execute("INSERT INTO workers (barangay_id, password, role) VALUES ('ADMIN123', 'password', 'worker')")
    
    # Add a default patient if none exists (for testing)
    c.execute("SELECT * FROM patients WHERE id = 1")
    if c.fetchone() is None:
         c.execute("INSERT INTO patients (id, last_name, first_name, dob, sex, contact) VALUES (1, 'Dela Cruz', 'Juan', '1990-01-01', 'Male', '09170000001')")
    # Ensure a patient account exists for the default patient (username = '1', password = 'password')
    c.execute("SELECT * FROM patient_accounts WHERE patient_id = 1")
    if c.fetchone() is None:
        c.execute("INSERT INTO patient_accounts (patient_id, username, password) VALUES (1, '1', 'password')")
    
    # Add default health record for patient if none exists
    c.execute("SELECT * FROM health_records WHERE patient_id = 1")
    if c.fetchone() is None:
        c.execute("""
            INSERT INTO health_records (patient_id, blood_type, allergies, chronic_conditions, status) 
            VALUES (1, 'O+', 'Penicillin, Peanuts', 'None', 'Active')
        """)
    
    # Add default marketplace items if none exist
    count_result = c.execute("SELECT COUNT(*) as cnt FROM marketplace_items").fetchone()
    if count_result[0] == 0:
        c.execute("""
            INSERT INTO marketplace_items (name, description, stock, price) VALUES 
            ('Vitamin C Supplement', 'Boost your immunity with Vitamin C', 50, 150.00),
            ('First Aid Kit', 'Complete first aid kit for emergencies', 10, 500.00),
            ('Pain Reliever', 'Fast-acting pain relief tablets', 100, 75.00),
            ('Blood Pressure Monitor', 'Digital blood pressure monitoring device', 15, 2500.00),
            ('Thermometer', 'Digital thermometer for accurate readings', 30, 200.00)
        """)
    
    # Add default medical services if none exist
    count_services = c.execute("SELECT COUNT(*) as cnt FROM medical_services").fetchone()
    if count_services[0] == 0:
        c.execute("""
            INSERT INTO medical_services (name, description, category) VALUES 
            ('Vaccine', 'Immunization services', 'Preventive'),
            ('Dental Appointment', 'Professional dental care and checkup', 'Dental'),
            ('Health Checkup', 'Comprehensive physical examination', 'General'),
            ('Blood Test', 'Laboratory blood analysis', 'Laboratory'),
            ('Consultation', 'Medical consultation with healthcare provider', 'General'),
            ('Eye Checkup', 'Vision and eye health examination', 'Specialist')
        """)
        
    conn.commit()
    conn.close()

# -----------------------------
# Authentication & Home Routes
# -----------------------------
@app.route("/")
def home():
    # Don't clear session here, just render. Session management happens on signin/logout
    return render_template("home.html")

@app.route("/worker_signin", methods=["GET", "POST"])
def worker_signin():
    """Handles sign-in for workers/admins (Renders worker_signin.html)."""
    if request.method == "POST":
        try:
            barangay_id = request.form["barangay_id"]
            password = request.form["password"]

            db = get_db()
            worker = db.execute("SELECT * FROM workers WHERE barangay_id = ? AND password = ?", (barangay_id, password)).fetchone()
            
            if worker:
                session["user_id"] = worker["barangay_id"]
                session["role"] = worker["role"]
                return redirect(url_for("patients")) 
            else:
                return render_template("worker_signin.html", error="Invalid credentials or Barangay ID.")
        except KeyError:
            return render_template("worker_signin.html", error="Sign-in failed: Missing form field. Please ensure all fields are complete.")
    
    return render_template("worker_signin.html", error=None)

@app.route("/patient_signin", methods=["GET", "POST"])
def patient_signin():
    """Handles sign-in for patients (Renders signin.html)."""
    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        password = request.form.get("password")
        db = get_db()
        c = db.cursor()
        account = c.execute("SELECT * FROM patient_accounts WHERE username = ? AND password = ?", (patient_id, password)).fetchone()
        if account:
            session["user_id"] = account["patient_id"] if "patient_id" in account.keys() else account[0]
            session["role"] = 'patient'
            return redirect(url_for("patient_profile"))
        else:
            return render_template("signin.html", error="Invalid Patient ID or Password.")

    return render_template("signin.html", error=None)

@app.route("/logout")
def logout():
    """Clears session and redirects to home."""
    session.clear()
    return redirect(url_for('home'))

@app.route("/signup")
def signup():
    # Landing page for signup: choose patient or worker
    return render_template("signup.html")


@app.route("/patient_signup", methods=["GET", "POST"])
def patient_signup():
    if request.method == "POST":
        data = request.form
        db = get_db()
        c = db.cursor()
        # Create patient record
        c.execute("""
            INSERT INTO patients (last_name, first_name, middle_name, suffix, dob, sex, contact, address, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("last_name",""), data.get("first_name",""), data.get("middle_name"), data.get("suffix"),
            data.get("dob","1970-01-01"), data.get("sex",""), data.get("contact"), data.get("address"), data.get("notes")
        ))
        patient_id = c.lastrowid

        # Username will be the patient ID (string)
        username = str(patient_id)
        password = data.get("password", "")
        c.execute("INSERT INTO patient_accounts (patient_id, username, password) VALUES (?, ?, ?)",
                  (patient_id, username, password))
        db.commit()

        return render_template("signup_success.html", patient_id=username)

    return render_template("patient_signup.html")


@app.route("/worker_signup", methods=["GET", "POST"])
def worker_signup():
    if request.method == "POST":
        data = request.form
        db = get_db()
        c = db.cursor()
        barangay_id = data.get("employee_id")
        role = data.get("role","worker")
        password = data.get("password")
        # Insert worker/admin (if not exists)
        try:
            c.execute("INSERT INTO workers (barangay_id, password, role) VALUES (?, ?, ?)", (barangay_id, password, role))
            db.commit()
        except Exception:
            # ignore duplicate for now
            pass

        return redirect(url_for("worker_signin"))

    return render_template("worker_signup.html")

# -----------------------------
# Patient Administration (Worker/Admin Secured View)
# -----------------------------
@app.route("/patients")
@login_required # SECURED
def patients():
    db = get_db()
    c = db.cursor()

    # --- GET ALL FILTER AND SORT PARAMS ---
    gender_filter = request.args.get("gender", "All")
    sort_by = request.args.get("sort", "id")
    age_input = request.args.get("age", "")
    id_input = request.args.get("patient_id", "")
    search = request.args.get("search", "").strip()
    last_name_start = request.args.get("last_name_start", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    query = "SELECT * FROM patients WHERE 1=1"
    params = []

    # Apply filters (Database side)
    if gender_filter in ["Male", "Female"]:
        query += " AND sex = ?"
        params.append(gender_filter)
    if search:
        query += " AND (first_name LIKE ? OR last_name LIKE ? OR contact LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    if last_name_start:
        query += " AND last_name LIKE ?"
        params.append(last_name_start + "%")
    if start_date or end_date:
        if start_date and end_date:
            query += " AND DATE(created_at) BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        elif start_date:
            query += " AND DATE(created_at) >= ?"
            params.append(start_date)
        elif end_date:
            query += " AND DATE(created_at) <= ?"
            params.append(end_date)


    c.execute(query, params)
    patients_data = c.fetchall()

    # Apply filters (Python side for Age and ID)
    if age_input:
        try:
            age = int(age_input)
            if age > 0:
                patients_data = [p for p in patients_data if calculate_age(p["dob"]) == age]
        except ValueError:
            pass

    if id_input:
        try:
            patient_id = int(id_input)
            if patient_id > 0:
                patients_data = [p for p in patients_data if p["id"] == patient_id]
        except ValueError:
            pass

    # Sorting
    def get_age_for_sort(p):
        age = calculate_age(p["dob"])
        return age if age is not None else (float('inf') if sort_by == "age_asc" else float('-inf'))

    if sort_by == "age_asc":
        patients_data = sorted(patients_data, key=get_age_for_sort)
    elif sort_by == "age_desc":
        patients_data = sorted(patients_data, key=get_age_for_sort, reverse=True)
    elif sort_by == "last_name":
        patients_data = sorted(patients_data, key=lambda x: x["last_name"].lower())
    else:
        patients_data = sorted(patients_data, key=lambda x: x["id"])

    return render_template(
        "patients.html",
        patients=patients_data,
        gender_filter=gender_filter,
        sort_by=sort_by,
        age_input=age_input,
        id_input=id_input,
        search=search,
        last_name_start=last_name_start,
        start_date=start_date,
        end_date=end_date
    )

@app.route("/add", methods=["GET", "POST"])
@login_required # SECURED
def add_patient():
    if request.method == "POST":
        data = request.form
        db = get_db()
        c = db.cursor()
        c.execute("""
            INSERT INTO patients 
            (last_name, first_name, middle_name, suffix, dob, sex, contact, address, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data["last_name"], data["first_name"], data.get("middle_name"), data.get("suffix"), data["dob"], 
              data["sex"], data["contact"], data.get("address"), data.get("notes")))
        # Get the new patient id
        patient_id = c.lastrowid

        # Insert associated health record if health fields provided
        blood_type = data.get("blood_type")
        allergies = data.get("allergies")
        chronic = data.get("chronic_conditions")
        status = data.get("status", "Active")

        c.execute("INSERT INTO health_records (patient_id, blood_type, allergies, chronic_conditions, status) VALUES (?, ?, ?, ?, ?)",
                  (patient_id, blood_type, allergies, chronic, status))

        db.commit()
        return redirect(url_for("patients"))

    return render_template("add_patient.html")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required # SECURED
def edit_patient(id):
    db = get_db()
    c = db.cursor()
    patient = c.execute("SELECT * FROM patients WHERE id = ?", (id,)).fetchone()

    if not patient:
        return "Patient not found", 404

    # Fetch health record for this patient (if any)
    health = c.execute("SELECT * FROM health_records WHERE patient_id = ?", (id,)).fetchone()

    if request.method == "POST":
        data = request.form
        c.execute("""
            UPDATE patients
            SET last_name = ?, first_name = ?, middle_name = ?, suffix = ?, dob = ?, sex = ?, contact = ?, address = ?, notes = ?
            WHERE id = ?
        """, (data["last_name"], data["first_name"], data.get("middle_name"), data.get("suffix"), data["dob"], 
              data["sex"], data["contact"], data.get("address"), data.get("notes"), id))

        # Update or create health record
        blood_type = data.get("blood_type")
        allergies = data.get("allergies")
        chronic = data.get("chronic_conditions")
        status = data.get("status", "Active")

        if health:
            c.execute("""
                UPDATE health_records
                SET blood_type = ?, allergies = ?, chronic_conditions = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE patient_id = ?
            """, (blood_type, allergies, chronic, status, id))
        else:
            c.execute("""
                INSERT INTO health_records (patient_id, blood_type, allergies, chronic_conditions, status)
                VALUES (?, ?, ?, ?, ?)
            """, (id, blood_type, allergies, chronic, status))

        db.commit()
        return redirect(url_for("patients"))

    return render_template("edit_patient.html", patient=patient, health_record=health)

@app.route("/remove/<int:id>", methods=["POST"])
@login_required # SECURED
def remove_patient(id):
    db = get_db()
    c = db.cursor()
    patient = c.execute("SELECT * FROM patients WHERE id = ?", (id,)).fetchone()
    
    if patient:
        c.execute("""
            INSERT INTO logs 
            (id, last_name, first_name, middle_name, suffix, dob, sex, contact, address, notes, action) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (patient["id"], patient["last_name"], patient["first_name"], patient["middle_name"], patient["suffix"],
              patient["dob"], patient["sex"], patient["contact"], patient["address"], patient["notes"], "DELETED"))
        c.execute("DELETE FROM patients WHERE id = ?", (id,))
        db.commit()

    return redirect(url_for("patients"))

@app.route("/remove", methods=["GET", "POST"])
@login_required # SECURED
def remove_multiple():
    db = get_db()
    c = db.cursor()

    if request.method == "POST":
        ids_input = request.form.getlist("ids")
        if ids_input:
            for pid in ids_input:
                patient = c.execute("SELECT * FROM patients WHERE id = ?", (pid,)).fetchone()
                if patient:
                    c.execute("""
                        INSERT INTO logs 
                        (id, last_name, first_name, middle_name, suffix, dob, sex, contact, address, notes, action) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (patient["id"], patient["last_name"], patient["first_name"], patient["middle_name"], patient["suffix"],
                          patient["dob"], patient["sex"], patient["contact"], patient["address"], patient["notes"], "DELETED"))

            c.execute(f"DELETE FROM patients WHERE id IN ({','.join(['?']*len(ids_input))})", ids_input)
            db.commit()
        return redirect(url_for("patients"))

    patients_list = c.execute("SELECT id, first_name, last_name FROM patients").fetchall()
    return render_template("remove_patient.html", patients=patients_list)

@app.route("/view/<int:id>")
@login_required # SECURED
def view_patient(id):
    db = get_db()
    c = db.cursor()
    patient = c.execute("SELECT * FROM patients WHERE id = ?", (id,)).fetchone()
    
    if not patient:
        return "Patient not found", 404

    patient_dict = dict(patient)
    patient_dict["age"] = calculate_age(patient["dob"])
    patient_dict["gender"] = patient["sex"]
    patient_dict["date_added"] = patient["created_at"]
    # Fetch linked health record (if any) and attach fields for admin view
    health = c.execute("SELECT * FROM health_records WHERE patient_id = ?", (id,)).fetchone()
    if health:
        # health is a sqlite3.Row — convert to dict-like access
        try:
            patient_dict["blood_type"] = health["blood_type"]
            patient_dict["allergies"] = health["allergies"]
            patient_dict["chronic_conditions"] = health["chronic_conditions"]
            patient_dict["health_status"] = health["status"]
            patient_dict["health_created_at"] = health["created_at"]
            patient_dict["health_updated_at"] = health["updated_at"]
        except Exception:
            # Fallback if row behaves like tuple
            patient_dict["blood_type"] = health[2] if len(health) > 2 else None
            patient_dict["allergies"] = health[3] if len(health) > 3 else None
            patient_dict["chronic_conditions"] = health[4] if len(health) > 4 else None
            patient_dict["health_status"] = health[5] if len(health) > 5 else None
            patient_dict["health_created_at"] = health[6] if len(health) > 6 else None
            patient_dict["health_updated_at"] = health[7] if len(health) > 7 else None
    else:
        patient_dict["blood_type"] = None
        patient_dict["allergies"] = None
        patient_dict["chronic_conditions"] = None
        patient_dict["health_status"] = None
        patient_dict["health_created_at"] = None
        patient_dict["health_updated_at"] = None

    return render_template("view_records.html", patient=patient_dict)

@app.route("/logs")
@login_required # SECURED
def logs():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM logs ORDER BY deleted_at DESC")
    logs = c.fetchall()
    return render_template("logs.html", logs=logs)

# -----------------------------
# Patient Portal Routes (Secured to self)
# -----------------------------

@app.route("/patient_profile")
def patient_profile():
    """Secured patient profile view, redirects if not logged in as patient."""
    patient_id = session.get("user_id")
    if session.get("role") != 'patient' or not patient_id:
        return redirect(url_for('patient_signin'))
        
    db = get_db()
    c = db.cursor()
    
    patient = c.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    
    if patient:
        patient_dict = dict(patient)
        patient_dict["age"] = calculate_age(patient["dob"])
        # Attach health record if present
        health = c.execute("SELECT * FROM health_records WHERE patient_id = ?", (patient_id,)).fetchone()
        if health:
            try:
                patient_dict["blood_type"] = health["blood_type"]
                patient_dict["allergies"] = health["allergies"]
                patient_dict["chronic_conditions"] = health["chronic_conditions"]
                patient_dict["health_status"] = health["status"]
                patient_dict["health_created_at"] = health["created_at"]
                patient_dict["health_updated_at"] = health["updated_at"]
            except Exception:
                patient_dict["blood_type"] = health[2] if len(health) > 2 else None
                patient_dict["allergies"] = health[3] if len(health) > 3 else None
                patient_dict["chronic_conditions"] = health[4] if len(health) > 4 else None
                patient_dict["health_status"] = health[5] if len(health) > 5 else None
                patient_dict["health_created_at"] = health[6] if len(health) > 6 else None
                patient_dict["health_updated_at"] = health[7] if len(health) > 7 else None
        else:
            patient_dict["blood_type"] = None
            patient_dict["allergies"] = None
            patient_dict["chronic_conditions"] = None
            patient_dict["health_status"] = None
            patient_dict["health_created_at"] = None
            patient_dict["health_updated_at"] = None

        return render_template("patient_profile.html", patient=patient_dict)
    else:
        # If record is missing, force sign-out
        session.clear() 
        return redirect(url_for('patient_signin'))

@app.route("/my_profile/edit", methods=["GET", "POST"])
def patient_edit_profile():
    """Allows a logged-in patient to edit ONLY their own record."""
    patient_id = session.get("user_id")
    # CRITICAL SECURITY CHECK:
    if session.get("role") != 'patient' or not patient_id:
        return redirect(url_for('patient_signin'))

    db = get_db()
    c = db.cursor()
    patient = c.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()

    if not patient:
        return "Patient record not found.", 404

    if request.method == "POST":
        data = request.form
        # We use the SECURED patient_id from the session, not the form
        c.execute("""
            UPDATE patients
            SET last_name = ?, first_name = ?, middle_name = ?, suffix = ?, dob = ?, sex = ?, contact = ?, address = ?, notes = ?
            WHERE id = ?
        """, (data["last_name"], data["first_name"], data.get("middle_name"), data.get("suffix"), data["dob"], 
              patient["sex"], data["contact"], data.get("address"), patient["notes"], patient_id)) # Note: Sex and Notes are read-only for patient
        db.commit()
        return redirect(url_for("patient_profile"))

    # Render the patient-specific edit template
    return render_template("patient_edit_profile.html", patient=patient)


@app.route("/patient_marketplace")
def patient_marketplace():
    """Marketplace route (Requires patient login)."""
    if session.get("role") != 'patient':
        return redirect(url_for('patient_signin'))
    
    patient_id = session.get("user_id")
    db = get_db()
    c = db.cursor()
    
    # Fetch all marketplace items
    items = c.execute("SELECT * FROM marketplace_items WHERE stock > 0").fetchall()
    
    # Count items in cart
    cart_count = c.execute("SELECT COUNT(*) as cnt FROM cart WHERE patient_id = ?", (patient_id,)).fetchone()["cnt"]
    
    return render_template("patient_marketplace.html", items=items, cart_count=cart_count)

@app.route("/add_to_cart/<int:item_id>", methods=["POST"])
def add_to_cart(item_id):
    """Adds item to patient's cart."""
    if session.get("role") != 'patient':
        return redirect(url_for('patient_signin'))
    
    patient_id = session.get("user_id")
    quantity = request.form.get("quantity", 1, type=int)
    
    if quantity < 1:
        quantity = 1
    
    db = get_db()
    c = db.cursor()
    
    # Check if item exists and has stock
    item = c.execute("SELECT * FROM marketplace_items WHERE id = ?", (item_id,)).fetchone()
    if not item or item["stock"] < quantity:
        return redirect(url_for("patient_marketplace"))
    
    # Check if item already in cart
    cart_item = c.execute("SELECT * FROM cart WHERE patient_id = ? AND item_id = ?", (patient_id, item_id)).fetchone()
    
    if cart_item:
        # Update quantity
        c.execute("UPDATE cart SET quantity = quantity + ? WHERE patient_id = ? AND item_id = ?", 
                  (quantity, patient_id, item_id))
    else:
        # Add new item to cart
        c.execute("INSERT INTO cart (patient_id, item_id, quantity) VALUES (?, ?, ?)", 
                  (patient_id, item_id, quantity))
    
    db.commit()
    return redirect(url_for("patient_marketplace"))

@app.route("/cart")
def view_cart():
    """Displays patient's shopping cart."""
    if session.get("role") != 'patient':
        return redirect(url_for('patient_signin'))
    
    patient_id = session.get("user_id")
    db = get_db()
    c = db.cursor()
    
    # Fetch cart items with product details
    cart_items = c.execute("""
        SELECT c.id, c.quantity, m.id as item_id, m.name, m.price, m.stock
        FROM cart c
        JOIN marketplace_items m ON c.item_id = m.id
        WHERE c.patient_id = ?
        ORDER BY c.added_at DESC
    """, (patient_id,)).fetchall()
    
    # Calculate totals
    total_price = sum(item["price"] * item["quantity"] for item in cart_items)
    
    return render_template("cart.html", cart_items=cart_items, total_price=total_price)

@app.route("/update_cart/<int:cart_id>", methods=["POST"])
def update_cart(cart_id):
    """Updates quantity of item in cart."""
    if session.get("role") != 'patient':
        return redirect(url_for('patient_signin'))
    
    patient_id = session.get("user_id")
    quantity = request.form.get("quantity", 1, type=int)
    
    if quantity < 1:
        quantity = 1
    
    db = get_db()
    c = db.cursor()
    
    # Verify cart item belongs to patient
    cart_item = c.execute("SELECT * FROM cart WHERE id = ? AND patient_id = ?", (cart_id, patient_id)).fetchone()
    if not cart_item:
        return redirect(url_for("view_cart"))
    
    # Check stock availability
    item = c.execute("SELECT * FROM marketplace_items WHERE id = ?", (cart_item["item_id"],)).fetchone()
    if quantity > item["stock"]:
        quantity = item["stock"]
    
    if quantity > 0:
        c.execute("UPDATE cart SET quantity = ? WHERE id = ?", (quantity, cart_id))
    else:
        c.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
    
    db.commit()
    return redirect(url_for("view_cart"))

@app.route("/remove_from_cart/<int:cart_id>", methods=["POST"])
def remove_from_cart(cart_id):
    """Removes item from cart."""
    if session.get("role") != 'patient':
        return redirect(url_for('patient_signin'))
    
    patient_id = session.get("user_id")
    db = get_db()
    c = db.cursor()
    
    # Verify cart item belongs to patient
    cart_item = c.execute("SELECT * FROM cart WHERE id = ? AND patient_id = ?", (cart_id, patient_id)).fetchone()
    if cart_item:
        c.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
        db.commit()
    
    return redirect(url_for("view_cart"))

@app.route("/clear_cart", methods=["POST"])
def clear_cart():
    """Clears all items from patient's cart."""
    if session.get("role") != 'patient':
        return redirect(url_for('patient_signin'))
    
    patient_id = session.get("user_id")
    db = get_db()
    c = db.cursor()
    
    c.execute("DELETE FROM cart WHERE patient_id = ?", (patient_id,))
    db.commit()
    
    return redirect(url_for("view_cart"))

@app.route("/medical_services")
def medical_services():
    """Displays available medical services for patient to request."""
    if session.get("role") != 'patient':
        return redirect(url_for('patient_signin'))
    
    patient_id = session.get("user_id")
    db = get_db()
    c = db.cursor()
    
    # Fetch all available medical services grouped by category
    services = c.execute("SELECT * FROM medical_services ORDER BY category, name").fetchall()
    
    return render_template("medical_services.html", services=services)

@app.route("/request_service/<int:service_id>", methods=["POST"])
def request_service(service_id):
    """Handles medical service request from patient."""
    if session.get("role") != 'patient':
        return redirect(url_for('patient_signin'))
    
    patient_id = session.get("user_id")
    request_type = request.form.get("request_type", "General Request")
    notes = request.form.get("notes", "")
    
    db = get_db()
    c = db.cursor()
    
    # Verify service exists
    service = c.execute("SELECT * FROM medical_services WHERE id = ?", (service_id,)).fetchone()
    if not service:
        return redirect(url_for("medical_services"))
    
    # Insert service request
    c.execute("""
        INSERT INTO service_requests (patient_id, service_id, request_type, notes)
        VALUES (?, ?, ?, ?)
    """, (patient_id, service_id, request_type, notes))
    
    db.commit()
    return redirect(url_for("my_service_requests"))

@app.route("/my_service_requests")
def my_service_requests():
    """Displays patient's submitted medical service requests."""
    if session.get("role") != 'patient':
        return redirect(url_for('patient_signin'))
    
    patient_id = session.get("user_id")
    db = get_db()
    c = db.cursor()
    
    # Fetch patient's service requests
    requests_data = c.execute("""
        SELECT sr.id, sr.request_type, sr.notes, sr.status, sr.requested_at, ms.name as service_name
        FROM service_requests sr
        JOIN medical_services ms ON sr.service_id = ms.id
        WHERE sr.patient_id = ?
        ORDER BY sr.requested_at DESC
    """, (patient_id,)).fetchall()
    
    return render_template("my_service_requests.html", requests=requests_data)

@app.route("/health_records")
def view_health_records():
    """Displays patient's health record."""
    if session.get("role") != 'patient':
        return redirect(url_for('patient_signin'))
    
    patient_id = session.get("user_id")
    db = get_db()
    c = db.cursor()
    
    # Fetch patient and health record
    patient_row = c.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    health_record = c.execute("""
        SELECT * FROM health_records WHERE patient_id = ?
    """, (patient_id,)).fetchone()
    
    if not health_record:
        # If no health record exists, create one
        c.execute("""
            INSERT INTO health_records (patient_id) VALUES (?)
        """, (patient_id,))
        db.commit()
        health_record = c.execute("""
            SELECT * FROM health_records WHERE patient_id = ?
        """, (patient_id,)).fetchone()
    
    # Prepare a patient dict for the template (to match other templates)
    patient = dict(patient_row) if patient_row else None
    if patient and patient.get("dob"):
        patient["age"] = calculate_age(patient["dob"])

    return render_template("my_records.html", health_record=health_record, patient=patient)

@app.route("/edit_health_records", methods=["GET", "POST"])
def edit_health_records():
    """Allows patient to edit their health record."""
    if session.get("role") != 'patient':
        return redirect(url_for('patient_signin'))
    
    patient_id = session.get("user_id")
    db = get_db()
    c = db.cursor()
    
    # Fetch patient health record
    health_record = c.execute("""
        SELECT * FROM health_records WHERE patient_id = ?
    """, (patient_id,)).fetchone()
    
    if not health_record:
        # If no health record exists, create one
        c.execute("""
            INSERT INTO health_records (patient_id) VALUES (?)
        """, (patient_id,))
        db.commit()
        health_record = c.execute("""
            SELECT * FROM health_records WHERE patient_id = ?
        """, (patient_id,)).fetchone()
    
    if request.method == "POST":
        blood_type = request.form.get("blood_type", "").strip()
        allergies = request.form.get("allergies", "").strip()
        chronic_conditions = request.form.get("chronic_conditions", "").strip()
        status = request.form.get("status", "Active")
        
        # Update health record
        c.execute("""
            UPDATE health_records 
            SET blood_type = ?, allergies = ?, chronic_conditions = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE patient_id = ?
        """, (blood_type, allergies, chronic_conditions, status, patient_id))
        
        db.commit()
        return redirect(url_for("view_health_records"))
    
    return render_template("edit_health_records.html", health_record=health_record)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
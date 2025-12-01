from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
from datetime import datetime

app = Flask(__name__)
DATABASE = "patients.db"

# -----------------------------
# Database Connection
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
    conn.commit()
    conn.close()

# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/patients")
def patients():
    db = get_db()
    c = db.cursor()

    # --- GET FILTERS ---
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

    # Gender filter
    if gender_filter in ["Male", "Female"]:
        query += " AND sex = ?"
        params.append(gender_filter)

    # Search by name/contact
    if search:
        query += " AND (first_name LIKE ? OR last_name LIKE ? OR contact LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    # Last name starts with
    if last_name_start:
        query += " AND last_name LIKE ?"
        params.append(last_name_start + "%")

    # Date range filter
    if start_date and end_date:
        query += " AND DATE(created_at) BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    c.execute(query, params)
    patients = c.fetchall()

    # Age filter
    if age_input:
        try:
            age = int(age_input)
            if age > 0:
                filtered = []
                for p in patients:
                    dob = datetime.strptime(p["dob"], "%Y-%m-%d")
                    years = (datetime.now() - dob).days // 365
                    if years == age:
                        filtered.append(p)
                patients = filtered
        except ValueError:
            pass

    # ID filter
    if id_input:
        try:
            patient_id = int(id_input)
            if patient_id > 0:
                patients = [p for p in patients if p["id"] == patient_id]
        except ValueError:
            pass

    # Sorting
    if sort_by == "age_asc":
        patients = sorted(patients, key=lambda x: x["dob"], reverse=True)
    elif sort_by == "age_desc":
        patients = sorted(patients, key=lambda x: x["dob"])
    elif sort_by == "last_name":
        patients = sorted(patients, key=lambda x: x["last_name"].lower())
    elif sort_by == "first_name":
        patients = sorted(patients, key=lambda x: x["first_name"].lower())
    elif sort_by == "middle_name":
        patients = sorted(patients, key=lambda x: (x["middle_name"] or "").lower())
    elif sort_by == "suffix":
        patients = sorted(patients, key=lambda x: (x["suffix"] or "").lower())
    else:
        patients = sorted(patients, key=lambda x: x["id"])

    return render_template(
        "patients.html",
        patients=patients,
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
def add_patient():
    if request.method == "POST":
        last_name = request.form["last_name"]
        first_name = request.form["first_name"]
        middle_name = request.form["middle_name"]
        suffix = request.form["suffix"]
        dob = request.form["dob"]
        sex = request.form["sex"]
        contact = request.form["contact"]
        address = request.form["address"]
        notes = request.form["notes"]

        db = get_db()
        c = db.cursor()
        c.execute("""
            INSERT INTO patients 
            (last_name, first_name, middle_name, suffix, dob, sex, contact, address, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (last_name, first_name, middle_name, suffix, dob, sex, contact, address, notes))
        db.commit()
        return redirect(url_for("patients"))

    return render_template("add_patient.html")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_patient(id):
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM patients WHERE id = ?", (id,))
    patient = c.fetchone()

    if not patient:
        return "Patient not found", 404

    if request.method == "POST":
        last_name = request.form["last_name"]
        first_name = request.form["first_name"]
        middle_name = request.form["middle_name"]
        suffix = request.form["suffix"]
        dob = request.form["dob"]
        sex = request.form["sex"]
        contact = request.form["contact"]
        address = request.form["address"]
        notes = request.form["notes"]

        c.execute("""
            UPDATE patients
            SET last_name = ?, first_name = ?, middle_name = ?, suffix = ?, dob = ?, sex = ?, contact = ?, address = ?, notes = ?
            WHERE id = ?
        """, (last_name, first_name, middle_name, suffix, dob, sex, contact, address, notes, id))
        db.commit()
        return redirect(url_for("patients"))

    return render_template("edit_patient.html", patient=patient)

@app.route("/remove/<int:id>", methods=["POST"])
def remove_patient(id):
    db = get_db()
    c = db.cursor()

    # Log before delete
    c.execute("SELECT * FROM patients WHERE id = ?", (id,))
    patient = c.fetchone()
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
def remove_multiple():
    db = get_db()
    c = db.cursor()

    if request.method == "POST":
        ids_input = request.form.getlist("ids")
        if ids_input:
            # Log each before deleting
            for pid in ids_input:
                c.execute("SELECT * FROM patients WHERE id = ?", (pid,))
                patient = c.fetchone()
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

    c.execute("SELECT id, first_name, last_name FROM patients")
    patients_list = c.fetchall()
    return render_template("remove_patient.html", patients=patients_list)

@app.route("/view/<int:id>")
def view_patient(id):
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM patients WHERE id = ?", (id,))
    patient = c.fetchone()
    if not patient:
        return "Patient not found", 404

    dob = datetime.strptime(patient["dob"], "%Y-%m-%d")
    patient = dict(patient)
    patient["age"] = (datetime.now() - dob).days // 365
    patient["gender"] = patient["sex"]
    patient["date_added"] = patient["created_at"]

    return render_template("view_records.html", patient=patient)

# -----------------------------
# Logs Page
# -----------------------------
@app.route("/logs")
def logs():
    db = get_db()
    c = db.cursor()
    c.execute("SELECT * FROM logs ORDER BY deleted_at DESC")
    logs = c.fetchall()
    return render_template("logs.html", logs=logs)

# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)

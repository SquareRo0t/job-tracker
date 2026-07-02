from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "my_database.db"

# Sqlite 3
import sqlite3

# Flask
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

# ---------------------------------------------------------------

@app.route("/")
def home():
    with sqlite3.connect(DB_PATH) as conn:
        cursor3 = conn.cursor()

        data = cursor3.execute("SELECT * FROM JOB").fetchall()

        total = cursor3.execute("SELECT COUNT(*) FROM JOB").fetchone()[0]
        sökt = cursor3.execute("SELECT COUNT(*) FROM JOB WHERE status = ?", ("Sökt",)).fetchone()[0]
        intervju = cursor3.execute("SELECT COUNT(*) FROM JOB WHERE status = ?", ("Intervju",)).fetchone()[0]
        avslag = cursor3.execute("SELECT COUNT(*) FROM JOB WHERE status = ?", ("Avslag",)).fetchone()[0]

        search = request.args.get("search", "")
        cursor3.execute("SELECT * FROM JOB WHERE company LIKE ?", (f"%{search}%",))

        if search == "":
            data = cursor3.execute("SELECT * FROM JOB").fetchall()
        else:
            data = cursor3.execute("SELECT * FROM JOB WHERE company LIKE ?", (f"%{search}%",)).fetchall()

    return render_template(
        "index.html",jobs=data, total=total, sökt=sökt, intervju=intervju, avslag=avslag,)


# ---------------------------------------------------------------

@app.route("/add", methods=["POST"])
def add_job():
    # Hämta data från formuläret
    company = request.form["company"]
    date = request.form["date"]
    recruites_name = request.form["recruite_name"]
    email = request.form["email"]
    phone = request.form["phone"]
    status = request.form["status"]

    if not company or not date or not recruites_name or not email or not phone:
        return redirect("/")

    with sqlite3.connect(DB_PATH) as conn:
        cursor1 = conn.cursor()
        cursor1.execute(
            "INSERT INTO JOB (company, date_applied, recruiter_name, recruiter_email, recruiter_phone, status) VALUES (?, ?, ?, ?, ?, ?)",
            (company, date, recruites_name, email, phone, status),
        )
        conn.commit()
    return redirect("/")

# ---------------------------------------------------------------

@app.route("/delete/<int:job_id>", methods=["POST"])
def delete_job(job_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor4 = conn.cursor()
        cursor4.execute("DELETE FROM JOB WHERE ID = ?", (job_id,))

        conn.commit()

    return redirect("/")

# ---------------------------------------------------------------

@app.route("/update/<int:job_id>", methods=["POST"])
def update_job(job_id):
    new_status = request.form["status"]

    with sqlite3.connect(DB_PATH) as conn:
        cursor5 = conn.cursor()
        cursor5.execute(
            "UPDATE JOB SET status = ? WHERE id =?",
            (
                new_status,
                job_id,
            ),
        )

        conn.commit()

    return redirect("/")

# ----------------------------------------------------------------

def init_db():
    create_table = ["""CREATE TABLE IF NOT EXISTS  JOB (
        id INTEGER PRIMARY KEY,
        company TEXT NOT NULL,
        date_applied DATE NOT NULL,
        recruiter_name TEXT NOT NULL,
        recruiter_email TEXT NOT NULL UNIQUE,
        recruiter_phone TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL
        )"""]
    # create a database connection
    try:
        with sqlite3.connect(DB_PATH) as conn:

            # create a cursor
            cursor2 = conn.cursor()

            # execute statements
            for table2 in create_table:
                cursor2.execute(table2)

            # commit the changes
            conn.commit()

            print("Tables created successfully.")

    except sqlite3.OperationalError as e:
        print("Failed to create tables:", e)

# ---------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    app.run()

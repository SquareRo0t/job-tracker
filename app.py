from pathlib import Path

# Hämta sökvägen till mappen där app.py ligger
BASE_DIR = Path(__file__).resolve().parent

# Bygg sökvägen till databasen relativt till app.py
DB_PATH = BASE_DIR / "my_database.db"

# Sqlite 3 - används för att kommunicera med databasen
import sqlite3

# io — skapar en fil i minnet istället för på disk, csv — Pythons inbyggda bibliotek för att skriva CSV-filer
import io, csv

# Flask - webbramverk för att bygga webbappen. Response — låter oss skicka en fil som nedladdning till användaren
from flask import Flask, render_template, request, redirect, Response

# Flask-Login - hanterar inloggning och sessioner
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

app = Flask(__name__)

# Hemlig nyckel som används för att kryptera sessionscookies
# I ett riktigt projekt ska denna vara lång och slumpmässig, och aldrig delas med någon
app.secret_key = "HEMLIGA-NYCKELN"

# Skapa en LoginManager som hanterar inloggningslogiken
Login_manager=LoginManager()

# Koppla LoginManager till vår Flask-app
Login_manager.init_app(app)

# Om en oinloggad användare försöker nå en skyddad sida, skickas de hit
Login_manager.login_view="login"

# Användarklass som Flask-Login använder för att hantera inloggade användare
# UserMixin ger oss färdiga metoder som is_authenticated, is_active osv
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

# En enkel "databas" med en användare - i ett riktigt projekt 
# skulle detta ligga i databasen med krypterade lösenord
users = {
    "admin": User(1, "admin", "lösenord123")
}

# Flask-Login anropar denna funktion för att hämta användaren från databasen
# baserat på det id som sparats i sessionen
@Login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if str(user.id) == str(user_id):
            return user
    return None

# ---------------------------------------------------------------

@app.route("/")
@login_required
def home():
    with sqlite3.connect(DB_PATH) as conn:
        cursor3 = conn.cursor()

        # Hämta totalt antal ansökningar
        total = cursor3.execute("SELECT COUNT(*) FROM JOB").fetchone()[0]
       
        # Hämta antal ansökningar per status
        sökt = cursor3.execute("SELECT COUNT(*) FROM JOB WHERE status = ?", ("Sökt",)).fetchone()[0]
        intervju = cursor3.execute("SELECT COUNT(*) FROM JOB WHERE status = ?", ("Intervju",)).fetchone()[0]
        avslag = cursor3.execute("SELECT COUNT(*) FROM JOB WHERE status = ?", ("Avslag",)).fetchone()[0]

        # Hämta sökord och sorteringskolumn från URL-parametrar
        search = request.args.get("search", "")
        sort = request.args.get("sort", "id")

        # Tillåtna kolumner för sortering (skyddar mot SQL-injection)
        allowed_columns = ["company", "date_applied", "recruiter_name", "recruiter_email", "recruiter_phone", "status", "id"]
        
        # Om ogiltig kolumn skickas, sortera på id som standard
        if sort not in allowed_columns:
            sort = "id"

        # Hämta alla jobb eller filtrera baserat på sökord
        if search == "":
            data = cursor3.execute(f"SELECT * FROM JOB ORDER BY {sort}").fetchall()
        else:
            data = cursor3.execute(f"SELECT * FROM JOB WHERE company LIKE ? ORDER BY {sort}", (f"%{search}%",)).fetchall()

    # Skicka data till HTML-mallen
    return render_template(
        "index.html", jobs=data, total=total, sökt=sökt, intervju=intervju, avslag=avslag)

# ---------------------------------------------------------------

@app.route("/add", methods=["POST"])
@login_required
def add_job():

    # Hämta data från formuläret
    company = request.form["company"]
    date = request.form["date"]
    recruites_name = request.form["recruite_name"]
    email = request.form["email"]
    phone = request.form["phone"]
    status = request.form["status"]

    # Kontrollera att inga fält är tomma
    if not company or not date or not recruites_name or not email or not phone:
        return redirect("/")

    # Spara ansökan i databasen
    with sqlite3.connect(DB_PATH) as conn:
        cursor1 = conn.cursor()
        cursor1.execute(
            "INSERT INTO JOB (company, date_applied, recruiter_name, recruiter_email, recruiter_phone, status) VALUES (?, ?, ?, ?, ?, ?)",
            (company, date, recruites_name, email, phone, status),)
        conn.commit()
    
    # Skicka tillbaka användaren till startsidan
    return redirect("/")

# ---------------------------------------------------------------

@app.route("/delete/<int:job_id>", methods=["POST"])
@login_required
def delete_job(job_id):

    # Anslut till databasen och ta bort ansökan med matchande id
    with sqlite3.connect(DB_PATH) as conn:
        cursor4 = conn.cursor()
        cursor4.execute("DELETE FROM JOB WHERE ID = ?", (job_id,))
        conn.commit()

    # Skicka tillbaka användaren till startsidan
    return redirect("/")

# ---------------------------------------------------------------

@app.route("/update/<int:job_id>", methods=["POST"])
@login_required
def update_job(job_id):

    # Hämta det nya statusvärdet från formuläret
    new_status = request.form["status"]

    # Uppdatera statusen för ansökan med matchande id
    with sqlite3.connect(DB_PATH) as conn:
        cursor5 = conn.cursor()
        cursor5.execute("UPDATE JOB SET status = ? WHERE id = ?",(new_status, job_id,),)
        conn.commit()

    # Skicka tillbaka användaren till startsidan
    return redirect("/")

# ----------------------------------------------------------------

# @app.route("/edit/<int:job_id>")
# def edit_job(job_id):
#     # Hämta ansökan med matchande id från databasen 
#     with sqlite3.connect(DB_PATH) as conn:
#         cursor6 = conn.cursor()
#         # fetchone() hämtar bara en rad istället för alla
#         job = cursor6.execute("SELECT * FROM JOB WHERE id = ?",(job_id,)).fetchone()
#      # Skicka radens data till redigeringssidan
#     return render_template("edit.html", job=job)

# ----------------------------------------------------------------

@app.route("/edit/<int:job_id>", methods=["GET","POST"])
@login_required
def edit_job(job_id):

    if request.method == "POST":
        
        company = request.form["company"]
        date = request.form["date"]
        recruites_name = request.form["recruite_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        status = request.form["status"]
    
        # Hämta ansökan med matchande id från databasen 
        with sqlite3.connect(DB_PATH) as conn:
            cursor6 = conn.cursor()
            cursor6.execute("UPDATE JOB SET company = ?, date_applied = ?, recruiter_name = ?, recruiter_email = ?, recruiter_phone = ?, status = ? WHERE id = ?",(company, date, recruites_name, email, phone, status, job_id,))
            conn.commit()
    else:
        # Hämta ansökan med matchande id från databasen 
        with sqlite3.connect(DB_PATH) as conn:
            cursor6 = conn.cursor()
            # fetchone() hämtar bara en rad istället för alla
            job = cursor6.execute("SELECT * FROM JOB WHERE id = ?",(job_id,)).fetchone()
        # Skicka radens data till redigeringssidan
        return render_template("edit.html", job=job)

    # Skicka tillbaka användaren till startsidan
    return redirect("/")

# ----------------------------------------------------------------

@app.route("/export")
@login_required
def export_csv():

    # Hämta alla rader från databasen
    with sqlite3.connect(DB_PATH) as conn:
        cursor7 = conn.cursor()
        jobs = cursor7.execute("SELECT * FROM JOB").fetchall()

    # Skapa en fil i minnet med io.StringIO()
    output = io.StringIO()

    # Skapa en CSV-writer
    writer = csv.writer(output)

    writer.writerow(["Företagsnamn", "Datum", "Rekryterarens namn", "E-post", "Telefon", "Status"])

    # Loopa igenom alla jobb och skriv varje rad (hoppa över id med job[1:])
    for job in jobs:
        writer.writerow(job[1:])
    
    # Skicka CSV-filen som nedladdning till användaren
    output.seek(0)
    return Response(output, mimetype="text/csv", 
                    headers={"Content-Disposition": "attachment; filename=ansokningar.csv"})


# ----------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username].password == password:
            login_user(users[username])
            return redirect("/")
           
        return render_template("login.html", error="Fel användarnamn eller lösenord")
    return render_template("login.html")

# ----------------------------------------------------------------

@app.route("/logout")
@login_required # Måste vara inloggad för att logga ut
def logout():
    # Loggar ut användaren och rensar sessionen
    logout_user()
    return redirect("/login")

# ----------------------------------------------------------------

def init_db():

    # SQL-sats för att skapa tabellen om den inte redan finns
    create_table = ["""CREATE TABLE IF NOT EXISTS JOB (
        id INTEGER PRIMARY KEY,
        company TEXT NOT NULL,
        date_applied DATE NOT NULL,
        recruiter_name TEXT NOT NULL,
        recruiter_email TEXT NOT NULL,
        recruiter_phone TEXT NOT NULL,
        status TEXT NOT NULL
        )"""]
    
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor2 = conn.cursor()

            # Kör varje CREATE TABLE-sats
            for table2 in create_table:
                cursor2.execute(table2)

            # Spara ändringarna
            conn.commit()
            print("Tables created successfully.")

    except sqlite3.OperationalError as e:
        print("Failed to create tables:", e)

# ---------------------------------------------------------------

if __name__ == "__main__":
    # Skapa databasen och starta webbservern
    init_db()
    app.run()

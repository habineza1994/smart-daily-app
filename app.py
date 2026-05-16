# ================= IMPORTS =================
import os
import io
import datetime
import pymysql

from flask import Flask, request, redirect, session, send_file
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.pagesizes import A4

from ai_engine import analyze_finance


# ================= APP =================
app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "hirwa_secret_key")


# ================= SESSION SECURITY =================
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True


# ================= DATABASE =================
def get_db():
    return pymysql.connect(
        host=os.environ.get("MYSQLHOST"),
        user=os.environ.get("MYSQLUSER"),
        password=os.environ.get("MYSQLPASSWORD"),
        database=os.environ.get("MYSQLDATABASE"),
        port=int(os.environ.get("MYSQLPORT", 3306)),
        cursorclass=pymysql.cursors.DictCursor,
        ssl={"ssl": {}}
    )


# ================= HOME =================
@app.route("/")
def home():
    return """
    <h1>HIRWA SMART</h1>
    <p>System Running ✅</p>
    <a href="/login">Login</a>
    """


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        db = get_db()
        cur = db.cursor()

        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()

        db.close()

        if user and user["password"] == password:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/dashboard")

        return "Login Failed ❌"

    return """
    <style>
    body{font-family:Arial;background:linear-gradient(120deg,#4e54c8,#8f94fb);display:flex;justify-content:center;align-items:center;height:100vh}
    .card{background:white;padding:25px;border-radius:15px;width:350px}
    input,button{width:100%;padding:12px;margin:8px 0}
    button{background:#4e54c8;color:white;border:none;border-radius:8px}
    </style>

    <div class="card">
    <h2>Login</h2>
    <form method="POST">
    <input name="username" placeholder="Username">
    <input name="password" type="password" placeholder="Password">
    <button>Login</button>
    </form>
    </div>
    """


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    uid = session["user_id"]
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT COALESCE(SUM(amount),0) t FROM income WHERE user_id=%s", (uid,))
    income = float(cur.fetchone()["t"])

    cur.execute("SELECT COALESCE(SUM(amount),0) t FROM expenses WHERE user_id=%s", (uid,))
    expenses = float(cur.fetchone()["t"])

    cur.execute("SELECT COUNT(*) c FROM activities WHERE user_id=%s", (uid,))
    act = cur.fetchone()["c"]

    balance = income - expenses

    notif = "<div style='padding:10px;background:green;color:white'>OK</div>"
    if balance < 0:
        notif = "<div style='padding:10px;background:red;color:white'>LOW BALANCE ⚠</div>"

    return f"""
    <html>
    <head>
    <style>
    body{{font-family:Arial;background:#f4f6fb}}
    .header{{background:#4e54c8;color:white;padding:20px;text-align:center}}
    .card{{background:white;margin:15px;padding:15px;border-radius:10px}}
    a{{text-decoration:none}}
    </style>
    </head>

    <body>

    <div class="header">HIRWA SMART</div>

    {notif}

    <div class="card">
    <a href="/income">Income</a><br>
    <a href="/expenses">Expenses</a><br>
    <a href="/activity">Activities</a><br>
    <a href="/ai_advice">AI Advice</a><br>
    <a href="/logout">Logout</a>
    </div>

    <div class="card">
    <h3>Summary</h3>
    Income: {income}<br>
    Expenses: {expenses}<br>
    Balance: {balance}<br>
    Activities: {act}
    </div>

    </body>
    </html>
    """


# ================= INCOME =================
@app.route("/income", methods=["GET","POST"])
def income():

    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        cur.execute("""
        INSERT INTO income(amount, source, date, user_id)
        VALUES(%s,%s,%s,%s)
        """, (
            request.form["amount"],
            request.form["source"],
            request.form["date"],
            session["user_id"]
        ))
        db.commit()
        return redirect("/income")

    cur.execute("SELECT * FROM income WHERE user_id=%s", (session["user_id"],))
    rows = cur.fetchall()

    html = "<h2>Income</h2><form method='POST'>"
    html += "<input name='amount' placeholder='Amount'>"
    html += "<input name='source' placeholder='Source'>"
    html += "<input type='date' name='date'>"
    html += "<button>Add</button></form><hr>"

    for r in rows:
        html += f"{r['amount']} - {r['source']} - {r['date']}<br>"

    return html


# ================= EXPENSES =================
@app.route("/expenses", methods=["GET","POST"])
def expenses():

    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        cur.execute("""
        INSERT INTO expenses(amount, category, date, user_id)
        VALUES(%s,%s,%s,%s)
        """, (
            request.form["amount"],
            request.form["category"],
            request.form["date"],
            session["user_id"]
        ))
        db.commit()
        return redirect("/expenses")

    cur.execute("SELECT * FROM expenses WHERE user_id=%s", (session["user_id"],))
    rows = cur.fetchall()

    html = "<h2>Expenses</h2><form method='POST'>"
    html += "<input name='amount' placeholder='Amount'>"
    html += "<input name='category' placeholder='Category'>"
    html += "<input type='date' name='date'>"
    html += "<button>Add</button></form><hr>"

    for r in rows:
        html += f"{r['amount']} - {r['category']} - {r['date']}<br>"

    return html


# ================= ACTIVITIES =================
@app.route("/activity", methods=["GET","POST"])
def activity():

    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    if request.method == "POST":
        cur.execute("""
        INSERT INTO activities(activity_name, date, user_id)
        VALUES(%s,%s,%s)
        """, (
            request.form["activity_name"],
            request.form["date"],
            session["user_id"]
        ))
        db.commit()
        return redirect("/activity")

    cur.execute("SELECT * FROM activities WHERE user_id=%s", (session["user_id"],))
    rows = cur.fetchall()

    html = "<h2>Activities</h2><form method='POST'>"
    html += "<input name='activity_name' placeholder='Activity'>"
    html += "<input type='date' name='date'>"
    html += "<button>Add</button></form><hr>"

    for r in rows:
        html += f"{r['activity_name']} - {r['date']}<br>"

    return html


# ================= AI =================
@app.route("/ai_advice")
def ai_advice():

    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT amount FROM income WHERE user_id=%s", (session["user_id"],))
    income = cur.fetchall()

    cur.execute("SELECT amount FROM expenses WHERE user_id=%s", (session["user_id"],))
    expenses = cur.fetchall()

    summary, advice = analyze_finance(income, expenses)

    return f"""
    <h2>AI Advice</h2>
    <pre>{summary}</pre>
    <p>{advice}</p>
    <a href="/dashboard">Back</a>
    """


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)

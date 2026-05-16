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

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":
        try:
            username = request.form.get("username","").strip()
            password = request.form.get("password","").strip()

            db = get_db()
            cur = db.cursor()

            cur.execute(
                "SELECT * FROM users WHERE username=%s",
                (username,)
            )

            user = cur.fetchone()
            db.close()

            if user and user["password"] == password:
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                return redirect("/dashboard")

            return """
            <div style="color:white;background:red;padding:10px;text-align:center;">
                Login Failed ❌ Username cyangwa Password si byo
            </div>
            """


        except Exception as e:
            return f"<h3 style='color:red;'>Server Error: {str(e)}</h3>"


    return """
<!DOCTYPE html>
<html>
<head>
<title>HIRWA SMART Login</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
body {
    margin:0;
    font-family:Arial;
    background: linear-gradient(135deg,#4e54c8,#8f94fb);
    height:100vh;
    display:flex;
    justify-content:center;
    align-items:center;
}

.card {
    background:white;
    width:90%;
    max-width:420px;
    padding:30px;
    border-radius:18px;
    box-shadow:0 10px 30px rgba(0,0,0,0.2);
    text-align:center;
}

h2 {
    margin-bottom:10px;
    color:#4e54c8;
}

p {
    color:#666;
    margin-bottom:20px;
}

input {
    width:100%;
    padding:14px;
    margin:10px 0;
    border-radius:10px;
    border:1px solid #ddd;
    outline:none;
}

input:focus {
    border-color:#4e54c8;
}

button {
    width:100%;
    padding:14px;
    border:none;
    border-radius:10px;
    background:#4e54c8;
    color:white;
    font-size:16px;
    cursor:pointer;
}

button:hover {
    background:#3b42a0;
}

.footer {
    margin-top:15px;
    font-size:12px;
    color:#999;
}
</style>

</head>

<body>

<div class="card">

<h2>HIRWA SMART</h2>
<p>Login to your account</p>

<form method="POST">

<input name="username" placeholder="Username" required>
<input name="password" type="password" placeholder="Password" required>

<button type="submit">LOGIN</button>

</form>

<div class="footer">
Secure Finance System © 2026
</div>

</div>

</body>
</html>
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

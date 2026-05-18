# ================= HIRWA SMART PRO VERSION (FULL RESTORED + DESIGN FIXED) =================

import os
import io
import datetime
import pymysql
from flask import Flask, request, redirect, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.pagesizes import A4
from ai_engine import analyze_finance

# ================= APP =================
app = Flask(__name__)

# ================= SECURITY =================
app.secret_key = os.environ.get("SECRET_KEY", "hirwa_secret_key_change_this")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = True
app.permanent_session_lifetime = datetime.timedelta(minutes=30)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

# ================= DB =================
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

# ================= INIT DB =================
@app.route("/initdb")
def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) UNIQUE,
        password VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS income(
        id INT AUTO_INCREMENT PRIMARY KEY,
        amount DECIMAL(10,2),
        source VARCHAR(255),
        date DATE,
        description TEXT,
        done_by VARCHAR(100),
        status VARCHAR(50) DEFAULT 'approved',
        user_id INT,
        deleted_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id INT AUTO_INCREMENT PRIMARY KEY,
        amount DECIMAL(10,2),
        category VARCHAR(255),
        date DATE,
        description TEXT,
        done_by VARCHAR(100),
        status VARCHAR(50) DEFAULT 'approved',
        user_id INT,
        deleted_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS activities(
        id INT AUTO_INCREMENT PRIMARY KEY,
        activity_name VARCHAR(255),
        description TEXT,
        status VARCHAR(50),
        date DATE,
        done_by VARCHAR(100),
        user_id INT,
        deleted_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    db.commit()
    db.close()
    return "Database Ready ✅"

# ================= HOME =================
@app.route("/")
def home():
    return """
    <html>
    <head>
    <style>
    body{font-family:Arial;background:linear-gradient(120deg,#4e54c8,#8f94fb);color:white;text-align:center;padding-top:80px}
    .card{background:white;color:black;width:320px;margin:auto;padding:25px;border-radius:15px;box-shadow:0 10px 25px rgba(0,0,0,0.3)}
    a{display:block;margin:10px;padding:10px;background:#4e54c8;color:white;text-decoration:none;border-radius:10px}
    </style>
    </head>
    <body>
    <div class='card'>
    <h2>HIRWA SMART PRO</h2>
    <a href='/login'>Login</a>
    <a href='/register'>Register</a>
    </div>
    </body>
    </html>
    """

# ================= REGISTER =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = generate_password_hash(request.form["password"].strip())

        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO users(username,password) VALUES(%s,%s)", (username,password))
        db.commit()
        db.close()
        return redirect("/login")

    return """
    <html><body style='font-family:Arial;background:#f4f6fb;display:flex;justify-content:center;align-items:center;height:100vh'>
    <div style='background:white;padding:25px;border-radius:15px;width:300px;box-shadow:0 10px 20px rgba(0,0,0,0.2)'>
    <h2>Register</h2>
    <form method='POST'>
    <input name='username' placeholder='Username' style='width:100%;padding:10px;margin:5px 0'><br>
    <input name='password' type='password' placeholder='Password' style='width:100%;padding:10px;margin:5px 0'><br>
    <button style='width:100%;padding:10px;background:#4e54c8;color:white;border:none'>Register</button>
    </form>
    </div>
    </body></html>
    """

# ================= LOGIN =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        db.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect("/dashboard")

        return "Login Failed ❌"

    return """
<!DOCTYPE html>
<html>
<head>
<title>HIRWA SMART Login</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>

*{
margin:0;
padding:0;
box-sizing:border-box;
font-family:Arial,sans-serif;
}

body{
height:100vh;
display:flex;
justify-content:center;
align-items:center;
background:linear-gradient(135deg,#4e54c8,#8f94fb);
padding:20px;
}

.card{
background:white;
width:100%;
max-width:420px;
padding:35px;
border-radius:25px;
box-shadow:0 15px 35px rgba(0,0,0,.2);
}

.logo{
text-align:center;
margin-bottom:25px;
}

.logo h1{
color:#4e54c8;
font-size:32px;
}

.logo p{
color:gray;
font-size:14px;
}

.input-box{
margin-bottom:15px;
}

input{
width:100%;
padding:14px;
border-radius:12px;
border:1px solid #ddd;
outline:none;
font-size:15px;
}

input:focus{
border-color:#4e54c8;
}

button{
width:100%;
padding:14px;
border:none;
border-radius:12px;
background:#4e54c8;
color:white;
font-size:16px;
cursor:pointer;
}

button:hover{
opacity:.9;
}

.footer{
margin-top:20px;
text-align:center;
font-size:13px;
color:gray;
}

</style>

</head>

<body>

<div class="card">

<div class="logo">
<h1>HIRWA SMART</h1>
<p>Financial Management System</p>
</div>

<form method="POST">

<div class="input-box">
<input type="text"
name="username"
placeholder="Username"
required>
</div>

<div class="input-box">
<input type="password"
name="password"
placeholder="Password"
required>
</div>

<button type="submit">
Login
</button>

</form>

<div class="footer">
Secure System v1.0
</div>

</div>

</body>
</html>
"""

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    return f"""
    <html>
    <head>
    <style>
    body{{margin:0;font-family:Arial;background:#f4f6fb}}
    .header{{background:linear-gradient(90deg,#4e54c8,#8f94fb);color:white;padding:20px;text-align:center;font-size:22px}}
    .card{{background:white;margin:15px;padding:20px;border-radius:15px;box-shadow:0 4px 10px rgba(0,0,0,0.1)}}
    a{{display:block;padding:10px;color:#4e54c8;text-decoration:none}}
    </style>
    </head>
    <body>
    <div class='header'>HIRWA SMART PRO</div>
    <div class='card'>Welcome {session['username']}</div>
    <div class='card'>
    <a href='/income'>💰 Income</a>
    <a href='/expenses'>💸 Expenses</a>
    <a href='/activity'>📋 Activities</a>
    <a href='/ai_advice'>🧠 AI Advice</a>
    <a href='/logout'>🚪 Logout</a>
    </div>
    </body>
    </html>
    """

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


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

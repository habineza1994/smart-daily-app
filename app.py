import os
import pymysql
from flask import Flask, request, redirect, session, send_file
from datetime import datetime

# PDF / DOC / EXCEL
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document
from openpyxl import Workbook

app = Flask(__name__)
app.secret_key = "hirwa_secret_key"


# ================= DB =================
def get_db():
    return pymysql.connect(
        host=os.environ.get('MYSQLHOST'),
        user=os.environ.get('MYSQLUSER'),
        password=os.environ.get('MYSQLPASSWORD'),
        database=os.environ.get('MYSQLDATABASE'),
        cursorclass=pymysql.cursors.DictCursor
    )


# ================= INIT DB =================
@app.route("/initdb")
def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100),
        password VARCHAR(255)
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS income(
        id INT AUTO_INCREMENT PRIMARY KEY,
        amount DECIMAL(10,2),
        source VARCHAR(255),
        date DATE,
        note TEXT,
        user_id INT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NULL,
        deleted_at DATETIME NULL
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS expenses(
        id INT AUTO_INCREMENT PRIMARY KEY,
        amount DECIMAL(10,2),
        category VARCHAR(255),
        date DATE,
        note TEXT,
        user_id INT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NULL,
        deleted_at DATETIME NULL
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS activities(
        id INT AUTO_INCREMENT PRIMARY KEY,
        activity_name VARCHAR(255),
        done_by VARCHAR(255),
        date DATE,
        description TEXT,
        user_id INT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        deleted_at DATETIME NULL
    )""")

    db.commit()
    return "DB READY"


# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s",
                    (request.form["username"], request.form["password"]))
        user = cur.fetchone()

        if user:
            session["user_id"] = user["id"]
            return redirect("/dashboard")

        return "Invalid login ❌"

    return """
    <html>
    <body style="font-family:Arial;background:#4e54c8;color:white;text-align:center;padding-top:100px;">
        <h2>HIRWA SMART LOGIN</h2>
        <form method="POST">
            <input name="username" placeholder="Username"><br><br>
            <input name="password" type="password" placeholder="Password"><br><br>
            <button>Login</button>
        </form>
    </body>
    </html>
    """


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]
    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT COALESCE(SUM(amount),0) as t FROM income WHERE user_id=%s AND deleted_at IS NULL", (user_id,))
    income = float(cur.fetchone()["t"])

    cur.execute("SELECT COALESCE(SUM(amount),0) as t FROM expenses WHERE user_id=%s AND deleted_at IS NULL", (user_id,))
    expenses = float(cur.fetchone()["t"])

    balance = income - expenses

    cur.execute("SELECT * FROM activities WHERE user_id=%s AND deleted_at IS NULL ORDER BY id DESC LIMIT 5", (user_id,))
    activities = cur.fetchall()

    notification = ""
    if balance < 0:
        notification = "<div style='background:red;color:white;padding:10px;border-radius:8px;'>⚠ Negative Balance!</div>"
    else:
        notification = "<div style='background:green;color:white;padding:10px;border-radius:8px;'>✅ Healthy Finance</div>"

    return f"""
    <html>
    <body style="font-family:Arial;background:#f4f6fb;margin:0;">

    <div style="background:#4e54c8;color:white;padding:15px;display:flex;justify-content:space-between;">
        <h3>HIRWA SMART</h3>
        <a href="/logout" style="color:white;">Logout</a>
    </div>

    {notification}

    <div style="display:flex;gap:10px;padding:10px;">
        <div style="background:white;padding:15px;border-radius:10px;">Income<br><b>{income}</b></div>
        <div style="background:white;padding:15px;border-radius:10px;">Expenses<br><b>{expenses}</b></div>
        <div style="background:white;padding:15px;border-radius:10px;">Balance<br><b>{balance}</b></div>
    </div>

    <div style="padding:10px;">
        <h3>Recent Activities</h3>
        {"".join([f"<div>{a['activity_name']} - {a['date']}</div>" for a in activities])}
    </div>

    <div style="padding:10px;">
        <a href='/income'>Income</a> |
        <a href='/expenses'>Expenses</a> |
        <a href='/activities'>Activities</a>
    </div>

    </body>
    </html>
    """


# ================= INCOME =================
@app.route("/income", methods=["GET", "POST"])
def income():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()
    uid = session["user_id"]

    if request.args.get("delete"):
        cur.execute("UPDATE income SET deleted_at=NOW() WHERE id=%s AND user_id=%s",
                    (request.args.get("delete"), uid))
        db.commit()
        return redirect("/income")

    if request.method == "POST":
        cur.execute("""INSERT INTO income(amount,source,date,note,user_id)
                       VALUES(%s,%s,%s,%s,%s)""",
                    (request.form["amount"], request.form["source"],
                     request.form["date"], request.form["note"], uid))
        db.commit()
        return redirect("/income")

    cur.execute("SELECT * FROM income WHERE user_id=%s AND deleted_at IS NULL", (uid,))
    rows = cur.fetchall()
 def some_function():
    table = "".join([
        f"<tr><td>{r['amount']}</td><td>{r['category']}</td><td>{r['date']}</td></tr>"
        for r in rows
    ])
    return f"""
    <a href="/logout" style="float:right;">Logout</a>
    <h2>Income</h2>

    <form method="POST">
        <input name="amount" placeholder="Amount">
        <input name="source" placeholder="Source">
        <input name="date" type="date">
        <input name="note" placeholder="Note">
        <button>Save</button>
    </form>

    <table border="1">{table}</table>
    <a href="/dashboard">Back</a>
    """


# ================= EXPENSES =================
@app.route("/expenses", methods=["GET", "POST"])
def expenses():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()
    uid = session["user_id"]

    if request.args.get("delete"):
        cur.execute("UPDATE expenses SET deleted_at=NOW() WHERE id=%s AND user_id=%s",
                    (request.args.get("delete"), uid))
        db.commit()
        return redirect("/expenses")

    if request.method == "POST":
        cur.execute("""INSERT INTO expenses(amount,category,date,note,user_id)
                       VALUES(%s,%s,%s,%s,%s)""",
                    (request.form["amount"], request.form["category"],
                     request.form["date"], request.form["note"], uid))
        db.commit()
        return redirect("/expenses")

    cur.execute("SELECT * FROM expenses WHERE user_id=%s AND deleted_at IS NULL", (uid,))
    rows = cur.fetchall()

    table = "".join([f"<tr><td>{r['amount']}</td><td>{r['category']}</td><td>{r['date']}</td>
                      <td>{r['note']}</td>
                      <td><a href='?delete={r['id']}'>Delete</a></td></tr>" for r in rows])

    return f"""
    <a href="/logout" style="float:right;">Logout</a>
    <h2>Expenses</h2>

    <form method="POST">
        <input name="amount">
        <input name="category">
        <input name="date" type="date">
        <input name="note">
        <button>Save</button>
    </form>

    <table border="1">{table}</table>
    <a href="/dashboard">Back</a>
    """


# ================= ACTIVITIES =================
@app.route("/activities", methods=["GET", "POST"])
def activities():
    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()
    uid = session["user_id"]

    if request.method == "POST":
        cur.execute("""INSERT INTO activities(activity_name,done_by,date,description,user_id)
                       VALUES(%s,%s,%s,%s,%s)""",
                    (request.form["name"], "user",
                     request.form["date"], request.form["desc"], uid))
        db.commit()
        return redirect("/activities")

    cur.execute("SELECT * FROM activities WHERE user_id=%s AND deleted_at IS NULL", (uid,))
    rows = cur.fetchall()

    table = "".join([f"<tr><td>{r['activity_name']}</td><td>{r['date']}</td>
                      <td>{r['description']}</td></tr>" for r in rows])

    return f"""
    <a href="/logout" style="float:right;">Logout</a>
    <h2>Activities</h2>

    <form method="POST">
        <input name="name" placeholder="Activity">
        <input name="date" type="date">
        <input name="desc" placeholder="Description">
        <button>Save</button>
    </form>

    <table border="1">{table}</table>
    <a href="/dashboard">Back</a>
    """


if __name__ == "__main__":
    app.run(debug=True)

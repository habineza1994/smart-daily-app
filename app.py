import os
import datetime
import pymysql
from flask import Flask, request, redirect, session, send_file

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
        deleted_at DATETIME DEFAULT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS expenses(
        id INT AUTO_INCREMENT PRIMARY KEY,
        amount DECIMAL(10,2),
        category VARCHAR(255),
        date DATE,
        note TEXT,
        user_id INT,
        deleted_at DATETIME DEFAULT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS activities(
        id INT AUTO_INCREMENT PRIMARY KEY,
        activity_name VARCHAR(255),
        done_by VARCHAR(255),
        date DATE,
        description TEXT,
        user_id INT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    db.commit()
    return "DB READY"


# ================= AUTH =================
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO users(username,password) VALUES(%s,%s)",
            (request.form['username'], request.form['password'])
        )
        db.commit()
        return redirect('/login')

    return """
    <h2>Register</h2>
    <form method="POST">
    Username:<input name="username"><br>
    Password:<input name="password"><br>
    <button>Register</button>
    </form>
    """


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s",
                    (request.form['username'], request.form['password']))
        user = cur.fetchone()

        if user:
            session['user_id'] = user['id']
            return redirect("/dashboard")

        return "Login failed ❌"

    return """
    <h2>Login</h2>
    <form method="POST">
        Username:<input name="username"><br>
        Password:<input name="password"><br>
        <button>Login</button>
    </form>
    """


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= DASHBOARD (YOUR ORIGINAL UI RESTORED) =================
@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    # SUMMARY (safe addition only)
    cur.execute("SELECT COALESCE(SUM(amount),0) total FROM income WHERE user_id=%s", (user_id,))
    income = float(cur.fetchone()['total'])

    cur.execute("SELECT COALESCE(SUM(amount),0) total FROM expenses WHERE user_id=%s", (user_id,))
    expenses = float(cur.fetchone()['total'])

    balance = income - expenses

    # activity count
    cur.execute("SELECT COUNT(*) c FROM activities WHERE user_id=%s", (user_id,))
    activity_count = cur.fetchone()['c']

    conn.close()

    return f"""
<!DOCTYPE html>
<html>
<head>
<title>HIRWA SMART Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
body{{margin:0;font-family:Arial;background:#f4f6fb}}

.header{{
    background:linear-gradient(90deg,#4e54c8,#8f94fb);
    color:white;padding:20px;text-align:center;
    font-size:22px;font-weight:bold;
}}

.card{{
    background:white;margin:15px;padding:18px;
    border-radius:15px;box-shadow:0 4px 10px rgba(0,0,0,0.08);
    display:flex;justify-content:space-between;
}}

.income{{border-left:8px solid #28a745}}
.expense{{border-left:8px solid #dc3545}}
.activity{{border-left:8px solid #007bff}}

.summary{{
    margin:15px;background:white;padding:15px;border-radius:15px;
}}

.box{{width:32%;padding:12px;border-radius:10px;color:white;text-align:center}}

.income-box{{background:#28a745}}
.expense-box{{background:#dc3545}}
.balance-box{{background:#007bff}}
</style>
</head>

<body>

<div class="header">HIRWA SMART</div>

<div class="card income" onclick="location.href='/income'">
<h2>💰 Income</h2><span>Track income</span>
</div>

<div class="card expense" onclick="location.href='/expenses'">
<h2>💸 Expenses</h2><span>Track expenses</span>
</div>

<div class="card activity" onclick="location.href='/activities'">
<h2>📋 Activities</h2><span>{activity_count} activities</span>
</div>

<div class="summary">
<h3>Summary</h3>
<div style="display:flex;justify-content:space-between">
<div class="box income-box">Income<br>{income}</div>
<div class="box expense-box">Expenses<br>{expenses}</div>
<div class="box balance-box">Balance<br>{balance}</div>
</div>
</div>

</body>
</html>
"""


# ================= ACTIVITIES =================
@app.route("/activities", methods=["GET","POST"])
def activities():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        cur.execute("""
            INSERT INTO activities(activity_name,done_by,date,description,user_id)
            VALUES(%s,%s,%s,%s,%s)
        """, (
            request.form['activity_name'],
            request.form['done_by'],
            request.form['date'],
            request.form['description'],
            user_id
        ))
        conn.commit()
        return redirect("/activities")

    cur.execute("SELECT * FROM activities WHERE user_id=%s ORDER BY id DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()

    table = "".join(
        f"<tr><td>{r['activity_name']}</td><td>{r['date']}</td><td>{r['description']}</td></tr>"
        for r in rows
    )

    return f"""
    <h2>Activities</h2>

    <form method="POST">
        Name:<input name="activity_name"><br>
        Done by:<input name="done_by"><br>
        Date:<input type="date" name="date"><br>
        Description:<input name="description"><br>
        <button>Add</button>
    </form>

    <table border="1" cellpadding="8">
        <tr><th>Name</th><th>Date</th><th>Description</th></tr>
        {table}
    </table>

    <a href="/dashboard">Back</a>
    """


if __name__ == "__main__":
    app.run(debug=True)

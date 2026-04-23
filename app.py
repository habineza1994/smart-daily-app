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


# ================= REGISTER =================
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


# ================= LOGIN (FIXED SESSION) =================
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor()

        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (request.form['username'], request.form['password'])
        )
        user = cur.fetchone()

        if user:
            session['user_id'] = user['id']
            return redirect("/dashboard")
        else:
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


# ================= DASHBOARD (ONE CLEAN VERSION ONLY) =================
@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    filter_type = request.args.get('filter', 'all')

    conn = get_db()
    cur = conn.cursor()

    income_filter = ""
    expense_filter = ""

    if filter_type == "today":
        income_filter = "AND DATE(created_at)=CURDATE()"
        expense_filter = "AND DATE(created_at)=CURDATE()"
    elif filter_type == "month":
        income_filter = "AND MONTH(created_at)=MONTH(CURDATE())"
        expense_filter = "AND MONTH(created_at)=MONTH(CURDATE())"

    # ================= SUMMARY =================
    cur.execute(f"""
        SELECT COALESCE(SUM(amount),0) total FROM income
        WHERE user_id=%s AND deleted_at IS NULL {income_filter}
    """, (user_id,))
    income = float(cur.fetchone()['total'])

    cur.execute(f"""
        SELECT COALESCE(SUM(amount),0) total FROM expenses
        WHERE user_id=%s AND deleted_at IS NULL {expense_filter}
    """, (user_id,))
    expenses = float(cur.fetchone()['total'])

    balance = income - expenses

    # ================= RECENT =================
    cur.execute("""
        SELECT 'Income' type, amount, created_at FROM income
        WHERE user_id=%s AND deleted_at IS NULL
        UNION ALL
        SELECT 'Expense', amount, created_at FROM expenses
        WHERE user_id=%s AND deleted_at IS NULL
        ORDER BY created_at DESC LIMIT 10
    """, (user_id, user_id))

    transactions = cur.fetchall()

    # ================= ACTIVITY COUNT =================
    cur.execute("SELECT COUNT(*) c FROM activities WHERE user_id=%s", (user_id,))
    activity_count = cur.fetchone()['c']

    conn.close()

    notification = """
    <div style='padding:10px;background:#28a745;color:white;border-radius:8px;'>
    System OK ✅
    </div>
    """
    if balance < 0:
        notification = """
        <div style='padding:10px;background:red;color:white;border-radius:8px;'>
        ⚠ Negative Balance Warning!
        </div>
        """

    rows_html = ""
    for t in transactions:
        rows_html += f"<tr><td>{t['type']}</td><td>{t['amount']}</td><td>{t['created_at']}</td></tr>"

    return f"""
    <html>
    <head>
    <title>HIRWA SMART</title>
    </head>

    <body style="font-family:Arial;background:#f4f6fb;padding:20px;">

    <h1>🔥 HIRWA SMART</h1>

    {notification}

    <h3>Summary</h3>
    <p>💰 Income: {income}</p>
    <p>💸 Expenses: {expenses}</p>
    <p>📊 Balance: {balance}</p>
    <p>📋 Activities: {activity_count}</p>

    <hr>

    <form method="GET">
        <select name="filter">
            <option value="all">All</option>
            <option value="today">Today</option>
            <option value="month">This Month</option>
        </select>
        <button>Filter</button>
    </form>

    <h3>Recent Transactions</h3>
    <table border="1" cellpadding="8">
        <tr><th>Type</th><th>Amount</th><th>Date</th></tr>
        {rows_html}
    </table>

    <hr>

    <a href="/income">Income</a> |
    <a href="/expenses">Expenses</a> |
    <a href="/activities">Activities</a> |
    <a href="/logout">Logout</a>

    </body>
    </html>
    """


# ================= ACTIVITIES (NEW) =================
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

    table = ""
    for r in rows:
        table += f"<tr><td>{r['activity_name']}</td><td>{r['date']}</td><td>{r['description']}</td></tr>"

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

    <br>
    <a href="/dashboard">Back</a>
    """


if __name__ == "__main__":
    app.run(debug=True)

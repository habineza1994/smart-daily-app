import os
import datetime
import pymysql
from flask import Flask, request, redirect, session, send_file
from docx import Document
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

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
        deleted_at DATETIME NULL
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS activities(
        id INT AUTO_INCREMENT PRIMARY KEY,
        activity_name VARCHAR(255),
        done_by VARCHAR(255),
        date DATE,
        description TEXT,
        user_id INT
    )""")

    db.commit()
    return "DB READY"


# ================= AUTH =================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO users(username,password) VALUES(%s,%s)",
                    (request.form['username'], request.form['password']))
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


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        db = get_db()
        cur = db.cursor(pymysql.cursors.DictCursor)

        cur.execute("""
            SELECT * FROM users
            WHERE username=%s AND password=%s
        """, (request.form["username"], request.form["password"]))

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


# ================= DASHBOARD (ONLY ONE - FIXED) =================
@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    filter_type = request.args.get('filter', 'all')

    conn = get_db()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    user_id = session['user_id']

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
        SELECT COALESCE(SUM(amount),0) AS total_income
        FROM income
        WHERE user_id=%s AND deleted_at IS NULL {income_filter}
    """, (user_id,))
    income = float(cur.fetchone()['total_income'])

    cur.execute(f"""
        SELECT COALESCE(SUM(amount),0) AS total_expenses
        FROM expenses
        WHERE user_id=%s AND deleted_at IS NULL {expense_filter}
    """, (user_id,))
    expenses = float(cur.fetchone()['total_expenses'])

    balance = income - expenses

    # ================= RECENT =================
    cur.execute("""
        SELECT 'Income' AS type, amount, created_at FROM income
        WHERE user_id=%s AND deleted_at IS NULL
        UNION ALL
        SELECT 'Expense', amount, created_at FROM expenses
        WHERE user_id=%s AND deleted_at IS NULL
        ORDER BY created_at DESC
        LIMIT 10
    """, (user_id, user_id))

    transactions = cur.fetchall()
    conn.close()

    # ================= NOTIFICATION =================
    notification = ""
    if balance < 0:
        notification = "<div style='background:red;color:white;padding:10px;'>⚠ Negative balance!</div>"
    else:
        notification = "<div style='background:green;color:white;padding:10px;'>✅ All good</div>"

    return f"""
    <h1>HIRWA SMART</h1>

    {notification}

    <form method="GET">
        <select name="filter">
            <option value="all">All</option>
            <option value="today">Today</option>
            <option value="month">Month</option>
        </select>
        <button>Filter</button>
    </form>

    <h3>Income: {income}</h3>
    <h3>Expenses: {expenses}</h3>
    <h3>Balance: {balance}</h3>

    <hr>

    <h2>Recent Transactions</h2>
    <table border="1">
        <tr><th>Type</th><th>Amount</th><th>Date</th></tr>
        {"".join([f"<tr><td>{t['type']}</td><td>{t['amount']}</td><td>{t['created_at']}</td></tr>" for t in transactions])}
    </table>

    <br><br>
    <a href="/income">Income</a> |
    <a href="/expenses">Expenses</a> |
    <a href="/logout">Logout</a>
    """


# ================= SIMPLE ROUTES PLACEHOLDERS =================
@app.route('/income')
def income():
    return "Income page"

@app.route('/expenses')
def expenses():
    return "Expenses page"

@app.route('/activities')
def activities():
    return "Activities page"


# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)

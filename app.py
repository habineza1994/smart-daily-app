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
        user_id INT
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS expenses(
        id INT AUTO_INCREMENT PRIMARY KEY,
        amount DECIMAL(10,2),
        category VARCHAR(255),
        date DATE,
        note TEXT,
        user_id INT
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


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (request.form['username'], request.form['password'])
        )
        user = cur.fetchone()

        if user:
            session['user_id'] = user['id']
            return redirect('/dashboard')

        return "Login Failed"

    return """
    <h2>Login</h2>
    <form method="POST">
    Username:<input name="username"><br>
    Password:<input name="password"><br>
    <button>Login</button>
    </form>
    """


# ================= DASHBOARD =================
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    return """
    <h2>HIRWA SMART Dashboard</h2>
    <a href="/income">Income</a><br>
    <a href="/expenses">Expenses</a><br>
    <a href="/activities">Activities</a><br>
    """


# ================= INCOME =================
@app.route('/income', methods=['GET','POST'])
def income():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        cur.execute("""
        INSERT INTO income(amount,source,date,note,user_id)
        VALUES(%s,%s,%s,%s,%s)
        """, (
            request.form['amount'],
            request.form['source'],
            request.form['date'],
            request.form['note'],
            session['user_id']
        ))
        db.commit()

    cur.execute("SELECT * FROM income WHERE user_id=%s ORDER BY id DESC", (session['user_id'],))
    rows = cur.fetchall()

    html = """
    <h3>Add Income</h3>
    <form method="POST">
    Amount:<input name="amount"><br>
    Source:<input name="source"><br>
    Date:<input type="date" name="date"><br>
    Note:<input name="note"><br>
    <button>Save</button>
    </form><hr>
    <h3>All Income</h3>
    """

    for r in rows:
        html += f"{r['amount']} - {r['source']} - {r['date']}<br>"

    html += '<br><a href="/dashboard">Back</a>'
    return html


# ================= EXPENSES =================
@app.route('/expenses', methods=['GET','POST'])
def expenses():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        cur.execute("""
        INSERT INTO expenses(amount,category,date,note,user_id)
        VALUES(%s,%s,%s,%s,%s)
        """, (
            request.form['amount'],
            request.form['category'],
            request.form['date'],
            request.form['note'],
            session['user_id']
        ))
        db.commit()

    cur.execute("SELECT * FROM expenses WHERE user_id=%s ORDER BY id DESC", (session['user_id'],))
    rows = cur.fetchall()

    html = """
    <h3>Add Expense</h3>
    <form method="POST">
    Amount:<input name="amount"><br>
    Category:<input name="category"><br>
    Date:<input type="date" name="date"><br>
    Note:<input name="note"><br>
    <button>Save</button>
    </form><hr>
    <h3>All Expenses</h3>
    """

    for r in rows:
        html += f"{r['amount']} - {r['category']} - {r['date']}<br>"

    html += '<br><a href="/dashboard">Back</a>'
    return html


# ================= ACTIVITIES =================
@app.route('/activities', methods=['GET','POST'])
def activities():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        cur.execute("""
        INSERT INTO activities(activity_name,done_by,date,description,user_id)
        VALUES(%s,%s,%s,%s,%s)
        """, (
            request.form['activity_name'],
            request.form['done_by'],
            request.form['date'],
            request.form['description'],
            session['user_id']
        ))
        db.commit()

    cur.execute("SELECT * FROM activities WHERE user_id=%s ORDER BY id DESC", (session['user_id'],))
    rows = cur.fetchall()

    html = """
    <h3>Add Activity</h3>
    <form method="POST">
    Activity Name:<input name="activity_name"><br>
    Done By:<input name="done_by"><br>
    Date:<input type="date" name="date"><br>
    Description:<input name="description"><br>
    <button>Save</button>
    </form><hr>
    <h3>All Activities</h3>
    """

    for r in rows:
        html += f"{r['activity_name']} - {r['date']}<br>"

    html += '<br><a href="/dashboard">Back</a>'
    return html


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

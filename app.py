import os
import datetime
import pymysql

from flask import Flask, request, redirect, session

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
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS expenses(
        id INT AUTO_INCREMENT PRIMARY KEY,
        amount DECIMAL(10,2),
        category VARCHAR(255),
        date DATE,
        note TEXT,
        user_id INT,
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


# ================= LOGIN (YOUR DESIGN RESTORED) =================
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
<!DOCTYPE html>
<html>
<head>
<title>HIRWA SMART Login</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>
body{
    margin:0;
    font-family: Arial;
    background:linear-gradient(120deg,#4e54c8,#8f94fb);
    height:100vh;
    display:flex;
    justify-content:center;
    align-items:center;
}

.card{
    background:white;
    width:92%;
    max-width:420px;
    border-radius:20px;
    padding:25px;
    box-shadow:0 10px 25px rgba(0,0,0,0.15);
}

input{
    width:100%;
    padding:14px;
    margin:10px 0;
    border-radius:10px;
    border:1px solid #ddd;
}

button{
    width:100%;
    padding:14px;
    border:none;
    border-radius:10px;
    background:#4e54c8;
    color:white;
}
</style>
</head>

<body>

<div class="card">
<h2 style="text-align:center;">HIRWA SMART</h2>
<form method="POST">
<input name="username" placeholder="Username">
<input name="password" type="password" placeholder="Password">
<button>Login</button>
</form>
</div>

</body>
</html>
"""


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ================= DASHBOARD (YOUR ORIGINAL BACK) =================
@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    return """
    <h1>HIRWA SMART Dashboard</h1>

    <a href="/income">💰 Income</a><br>
    <a href="/expenses">💸 Expenses</a><br>
    <a href="/activities">📋 Activities</a><br>
    <a href="/logout">Logout</a>
    """


# ================= INCOME (FIXED) =================
@app.route('/income', methods=['GET','POST'])
def income():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()
    user_id = session['user_id']

    if request.method == 'POST':
        cur.execute("""
            INSERT INTO income(amount,source,date,note,user_id)
            VALUES(%s,%s,%s,%s,%s)
        """, (
            request.form['amount'],
            request.form['source'],
            request.form['date'],
            request.form['note'],
            user_id
        ))
        db.commit()
        return redirect('/income')

    cur.execute("SELECT * FROM income WHERE user_id=%s", (user_id,))
    rows = cur.fetchall()

    table = "".join(
        f"<tr><td>{r['amount']}</td><td>{r['source']}</td><td>{r['date']}</td></tr>"
        for r in rows
    )

    return f"""
    <h2>Income</h2>

    <form method="POST">
        Amount:<input name="amount"><br>
        Source:<input name="source"><br>
        Date:<input type="date" name="date"><br>
        Note:<input name="note"><br>
        <button>Save</button>
    </form>

    <table border="1">
        <tr><th>Amount</th><th>Source</th><th>Date</th></tr>
        {table}
    </table>

    <a href="/dashboard">Back</a>
    """


# ================= EXPENSES (FIXED) =================
@app.route('/expenses', methods=['GET','POST'])
def expenses():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()
    user_id = session['user_id']

    if request.method == 'POST':
        cur.execute("""
            INSERT INTO expenses(amount,category,date,note,user_id)
            VALUES(%s,%s,%s,%s,%s)
        """, (
            request.form['amount'],
            request.form['category'],
            request.form['date'],
            request.form['note'],
            user_id
        ))
        db.commit()
        return redirect('/expenses')

    cur.execute("SELECT * FROM expenses WHERE user_id=%s", (user_id,))
    rows = cur.fetchall()

    table = "".join(
        f"<tr><td>{r['amount']}</td><td>{r['category']}</td><td>{r['date']}</td></tr>"
        for r in rows
    )

    return f"""
    <h2>Expenses</h2>

    <form method="POST">
        Amount:<input name="amount"><br>
        Category:<input name="category"><br>
        Date:<input type="date" name="date"><br>
        Note:<input name="note"><br>
        <button>Save</button>
    </form>

    <table border="1">
        <tr><th>Amount</th><th>Category</th><th>Date</th></tr>
        {table}
    </table>

    <a href="/dashboard">Back</a>
    """


# ================= ACTIVITIES =================
@app.route('/activities', methods=['GET','POST'])
def activities():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()
    user_id = session['user_id']

    if request.method == 'POST':
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
        db.commit()
        return redirect('/activities')

    cur.execute("SELECT * FROM activities WHERE user_id=%s", (user_id,))
    rows = cur.fetchall()

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
        <button>Save</button>
    </form>

    <table border="1">
        <tr><th>Name</th><th>Date</th><th>Description</th></tr>
        {table}
    </table>

    <a href="/dashboard">Back</a>
    """


if __name__ == "__main__":
    app.run(debug=True)

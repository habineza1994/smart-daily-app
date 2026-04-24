import os
<<<<<<< Updated upstream
=======
from ai_engine import analyze_finance
import datetime
>>>>>>> Stashed changes
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
    font-family:Arial;
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
    padding:25px;
    border-radius:20px;
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


# ================= DASHBOARD (FULL DESIGN RESTORED) =================
@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    db = get_db()
    cur = db.cursor()

    # FILTER (safe)
    filter_type = request.args.get('filter','all')

    income_filter = ""
    expense_filter = ""

    if filter_type == "today":
        income_filter = "AND DATE(date)=CURDATE()"
        expense_filter = "AND DATE(date)=CURDATE()"
    elif filter_type == "month":
        income_filter = "AND MONTH(date)=MONTH(CURDATE())"
        expense_filter = "AND MONTH(date)=MONTH(CURDATE())"

    # SUMMARY
    cur.execute(f"SELECT COALESCE(SUM(amount),0) t FROM income WHERE user_id=%s {income_filter}", (user_id,))
    income = float(cur.fetchone()['t'])

    cur.execute(f"SELECT COALESCE(SUM(amount),0) t FROM expenses WHERE user_id=%s {expense_filter}", (user_id,))
    expenses = float(cur.fetchone()['t'])

    balance = income - expenses

    # ACTIVITY COUNT
    cur.execute("SELECT COUNT(*) c FROM activities WHERE user_id=%s", (user_id,))
    act = cur.fetchone()['c']

    db.close()

    # NOTIFICATION
    notif = "<div style='padding:10px;background:green;color:white;border-radius:8px'>System OK</div>"
    if balance < 0:
        notif = "<div style='padding:10px;background:red;color:white;border-radius:8px'>Low Balance Warning ⚠</div>"

    return f"""
<!DOCTYPE html>
<html>
<head>
<title>Dashboard</title>

<style>
body{{margin:0;font-family:Arial;background:#f4f6fb}}

.header{{
    background:linear-gradient(90deg,#4e54c8,#8f94fb);
    color:white;
    padding:20px;
    text-align:center;
    font-size:22px;
    font-weight:bold;
}}

.card{{
    background:white;
    margin:15px;
    padding:18px;
    border-radius:15px;
    box-shadow:0 4px 10px rgba(0,0,0,0.08);
}}

.summary{{
    margin:15px;
    background:white;
    padding:15px;
    border-radius:15px;
}}

.box{{width:32%;padding:12px;border-radius:10px;color:white;text-align:center}}

.income-box{{background:#28a745}}
.expense-box{{background:#dc3545}}
.balance-box{{background:#007bff}}

a{{text-decoration:none;color:black}}
</style>
</head>

<body>

<div class="header">HIRWA SMART</div>

{notif}

<div class="card">
<h3>Menu</h3>
<a href="/income">💰 Income</a><br>
<a href="/expenses">💸 Expenses</a><br>
<a href="/activities">📋 Activities</a><br>
<a href="/logout">🚪 Logout</a>
</div>

<div class="card">
<form method="GET">
<select name="filter">
<option value="all">All</option>
<option value="today">Today</option>
<option value="month">This Month</option>
</select>
<button>Filter</button>
</form>
</div>

<div class="summary">
<h3>Summary</h3>
<div style="display:flex;justify-content:space-between">
<div class="box income-box">Income<br>{income}</div>
<div class="box expense-box">Expenses<br>{expenses}</div>
<div class="box balance-box">Balance<br>{balance}</div>
</div>
<p>Activities: {act}</p>
</div>

</body>
</html>
"""
# ---------- INCOME ----------
@app.route('/income', methods=['GET','POST'])
def income():
    db = get_db(); cur = db.cursor()

    if request.method == 'POST':
        cur.execute("INSERT INTO income(amount,source,date,note) VALUES(%s,%s,%s,%s)",
                    (request.form['amount'],request.form['source'],
                     request.form['date'],request.form['note']))
        db.commit()
        return redirect('/income')

    delete_id = request.args.get('delete')
    if delete_id:
        cur.execute("UPDATE income SET deleted=1 WHERE id=%s",(delete_id,))
        db.commit()
        return redirect('/income')

    cur.execute("SELECT * FROM income WHERE deleted=0 ORDER BY id DESC")
    rows = cur.fetchall()

    table = ""
    for r in rows:
        table += f"""
        <tr>
        <td>{r['amount']}</td>
        <td>{r['source']}</td>
        <td>{r['date']}</td>
        <td>{r['note']}</td>
        <td>{r['created_at']}</td>
        <td><a class='btn' href='?delete={r["id"]}'>Delete</a></td>
        </tr>
        """

    return f"""
    {STYLE}
    <h2>💰 Income</h2>
    <a class='btn' href='/income_pdf'>PDF</a>
    <form method='POST'>
        <input name='amount' placeholder='Amount' required>
        <input name='source' placeholder='Source' required>
        <input type='date' name='date' required>
        <input name='note' placeholder='Note'>
        <button>Save</button>
    </form>
    <table>
    <tr><th>Amount</th><th>Source</th><th>Date</th><th>Note</th><th>Created</th><th>Action</th></tr>
    {table}
    </table>
    <a href='/dashboard'>Back</a>
    """

# ---------- INCOME PDF ----------
@app.route('/income_pdf')
def income_pdf():
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT amount,source,date FROM income WHERE deleted=0")
    rows = cur.fetchall()

    file = "/tmp/income.pdf"
    doc = SimpleDocTemplate(file, pagesize=A4)

    data = [["Amount","Source","Date"]]
    for r in rows:
        data.append([r['amount'],r['source'],str(r['date'])])

    doc.build([Table(data)])
    return send_file(file, as_attachment=True)

# ---------- EXPENSES ----------
@app.route('/expenses', methods=['GET','POST'])
def expenses():
    db = get_db(); cur = db.cursor()

    if request.method == 'POST':
        cur.execute("INSERT INTO expenses(amount,category,date,note) VALUES(%s,%s,%s,%s)",
                    (request.form['amount'],request.form['category'],
                     request.form['date'],request.form['note']))
        db.commit()
        return redirect('/expenses')

    delete_id = request.args.get('delete')
    if delete_id:
        cur.execute("UPDATE expenses SET deleted=1 WHERE id=%s",(delete_id,))
        db.commit()
        return redirect('/expenses')

    cur.execute("SELECT * FROM expenses WHERE deleted=0 ORDER BY id DESC")
    rows = cur.fetchall()

    table = ""
    for r in rows:
        table += f"""
        <tr>
        <td>{r['amount']}</td>
        <td>{r['category']}</td>
        <td>{r['date']}</td>
        <td>{r['note']}</td>
        <td>{r['created_at']}</td>
        <td><a class='btn' href='?delete={r["id"]}'>Delete</a></td>
        </tr>
        """

    return f"""
    {STYLE}
    <h2>💸 Expenses</h2>
    <a class='btn' href='/dashboard'>Back</a>
    <form method='POST'>
        <input name='amount' placeholder='Amount' required>
        <input name='category' placeholder='Category' required>
        <input type='date' name='date' required>
        <input name='note' placeholder='Note'>
        <button>Save</button>
    </form>
    <table>
    <tr><th>Amount</th><th>Category</th><th>Date</th><th>Note</th><th>Created</th><th>Action</th></tr>
    {table}
    </table>
    """

# ---------- ACTIVITIES ----------
@app.route('/activities', methods=['GET','POST'])
def activities():
    db = get_db(); cur = db.cursor()

    if request.method == 'POST':
        cur.execute("INSERT INTO activities(activity_name,done_by,date,description) VALUES(%s,%s,%s,%s)",
                    (request.form['name'],request.form['done_by'],
                     request.form['date'],request.form['description']))
        db.commit()
        return redirect('/activities')

    delete_id = request.args.get('delete')
    if delete_id:
        cur.execute("UPDATE activities SET deleted=1 WHERE id=%s",(delete_id,))
        db.commit()
        return redirect('/activities')

    cur.execute("SELECT * FROM activities WHERE deleted=0 ORDER BY id DESC")
    rows = cur.fetchall()

    table = ""
    for r in rows:
        table += f"""
        <tr>
        <td>{r['activity_name']}</td>
        <td>{r['done_by']}</td>
        <td>{r['date']}</td>
        <td>{r['description']}</td>
        <td>{r['created_at']}</td>
        <td><a class='btn' href='?delete={r["id"]}'>Delete</a></td>
        </tr>
        """

    return f"""
    {STYLE}
    <h2>📋 Activities</h2>
    <a class='btn' href='/dashboard'>Back</a>
    <form method='POST'>
        <input name='name' placeholder='Activity name' required>
        <input name='done_by' placeholder='Done by' required>
        <input type='date' name='date' required>
        <input name='description' placeholder='Description'>
        <button>Save</button>
    </form>
    <table>
    <tr><th>Name</th><th>Done by</th><th>Date</th><th>Description</th><th>Created</th><th>Action</th></tr>
    {table}
    </table>
    """
' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()
    user_id = session['user_id']

    if request.method == 'POST':
        cur.execute("INSERT INTO expenses(amount,category,date,note,user_id) VALUES(%s,%s,%s,%s,%s)",
                    (request.form['amount'], request.form['category'], request.form['date'], request.form['note'], user_id))
        db.commit()
        return redirect('/expenses')

    cur

@app.route('/ai_advice')
def ai_advice():
    if 'user_id' not in session:
        return redirect('/')

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Fata incomes
    cursor.execute("SELECT amount FROM income WHERE user_id=%s", (session['user_id'],))
    incomes = cursor.fetchall()

    # Fata expenses
    cursor.execute("SELECT amount FROM expenses WHERE user_id=%s", (session['user_id'],))
    expenses = cursor.fetchall()

    conn.close()

    summary, advice = analyze_finance(incomes, expenses)

    return f"""
    <h2>🧠 AI Financial Advisor</h2>
    <pre>{summary}</pre>
    <h3>Advice:</h3>
    <p>{advice}</p>
    <a href="/dashboard">⬅ Back to Dashboard</a>
    """
if __name__ == "__main__":
    app.run(debug=True)

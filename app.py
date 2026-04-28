import os
from ai_engine import analyze_finance
import datetime
import pymysql
from flask import Flask, request, redirect, session, send_file

from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.pagesizes import A4

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


# ================= INIT DB (PRO VERSION SAFE) =================
@app.route("/initdb")
def init_db():
    db = get_db()
    cur = db.cursor()

    # ================= USERS =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) UNIQUE,
        password VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ================= INCOME =================
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

    # ================= EXPENSES =================
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

    # ================= ACTIVITIES =================
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activities(
        id INT AUTO_INCREMENT PRIMARY KEY,
        activity_name VARCHAR(255),
        done_by VARCHAR(255),
        date DATE,
        description TEXT,
        status VARCHAR(50) DEFAULT 'pending',
        user_id INT,
        deleted_at TIMESTAMP NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """)

    # ================= INDEXES =================
    try:
        cur.execute("CREATE INDEX idx_income_user ON income(user_id)")
    except:
        pass

    try:
        cur.execute("CREATE INDEX idx_expenses_user ON expenses(user_id)")
    except:
        pass

    try:
        cur.execute("CREATE INDEX idx_activities_user ON activities(user_id)")
    except:
        pass

    # ================= AUTO FIX (SAFE FOR OLD DB) =================

    # INCOME
    for q in [
        "ALTER TABLE income ADD COLUMN description TEXT",
        "ALTER TABLE income ADD COLUMN done_by VARCHAR(100)",
        "ALTER TABLE income ADD COLUMN status VARCHAR(50) DEFAULT 'approved'",
        "ALTER TABLE income ADD COLUMN deleted_at TIMESTAMP NULL",
        "ALTER TABLE income ADD COLUMN updated_at TIMESTAMP NULL"
    ]:
        try:
            cur.execute(q)
        except:
            pass

    # EXPENSES
    for q in [
        "ALTER TABLE expenses ADD COLUMN description TEXT",
        "ALTER TABLE expenses ADD COLUMN done_by VARCHAR(100)",
        "ALTER TABLE expenses ADD COLUMN status VARCHAR(50) DEFAULT 'approved'",
        "ALTER TABLE expenses ADD COLUMN deleted_at TIMESTAMP NULL",
        "ALTER TABLE expenses ADD COLUMN updated_at TIMESTAMP NULL"
    ]:
        try:
            cur.execute(q)
        except:
            pass

    # ACTIVITIES
    for q in [
        "ALTER TABLE activities ADD COLUMN description TEXT",
        "ALTER TABLE activities ADD COLUMN status VARCHAR(50) DEFAULT 'pending'",
        "ALTER TABLE activities ADD COLUMN deleted_at TIMESTAMP NULL",
        "ALTER TABLE activities ADD COLUMN updated_at TIMESTAMP NULL"
    ]:
        try:
            cur.execute(q)
        except:
            pass

    db.commit()
    return "🚀 PRO DATABASE READY (SAFE MODE) ✅"
# ================= LOGIN =================
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


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    db = get_db()
    cur = db.cursor()

    filter_type = request.args.get('filter','all')

    income_filter = ""
    expense_filter = ""

    if filter_type == "today":
        income_filter = "AND DATE(date)=CURDATE()"
        expense_filter = "AND DATE(date)=CURDATE()"
    elif filter_type == "month":
        income_filter = "AND MONTH(date)=MONTH(CURDATE())"
        expense_filter = "AND MONTH(date)=MONTH(CURDATE())"

    cur.execute(f"SELECT COALESCE(SUM(amount),0) t FROM income WHERE user_id=%s {income_filter}", (user_id,))
    income = float(cur.fetchone()['t'])

    cur.execute(f"SELECT COALESCE(SUM(amount),0) t FROM expenses WHERE user_id=%s {expense_filter}", (user_id,))
    expenses = float(cur.fetchone()['t'])

    balance = income - expenses

    cur.execute("SELECT COUNT(*) c FROM activities WHERE user_id=%s", (user_id,))
    act = cur.fetchone()['c']

    db.close()

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
.header{{background:linear-gradient(90deg,#4e54c8,#8f94fb);color:white;padding:20px;text-align:center;font-size:22px;font-weight:bold;}}
.card{{background:white;margin:15px;padding:18px;border-radius:15px;box-shadow:0 4px 10px rgba(0,0,0,0.08);}}
.summary{{margin:15px;background:white;padding:15px;border-radius:15px;}}
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


@app.route("/income", methods=["GET", "POST"])
def income():
    db = get_db()
    cur = db.cursor()

    # ================= ADD / UPDATE =================
    if request.method == "POST":
        if request.form.get("id"):  # UPDATE
            cur.execute("""
                UPDATE income 
                SET amount=%s, source=%s, date=%s, description=%s
                WHERE id=%s
            """, (
                request.form['amount'],
                request.form['source'],
                request.form['date'],
                request.form.get('description', ''),
                request.form['id']
            ))
        else:  # ADD
            cur.execute("""
                INSERT INTO income (amount, source, date, description, done_by)
                VALUES (%s,%s,%s,%s,%s)
            """, (
                request.form['amount'],
                request.form['source'],
                request.form['date'],
                request.form.get('description',''),
                session.get("username")
            ))

        db.commit()
        return redirect("/income")

    # ================= DELETE (SOFT) =================
    if request.args.get("delete"):
        cur.execute("""
            UPDATE income SET deleted_at=NOW()
            WHERE id=%s
        """, (request.args.get("delete"),))
        db.commit()
        return redirect("/income")

    # ================= EDIT FETCH =================
    edit_data = None
    if request.args.get("edit"):
        cur.execute("SELECT * FROM income WHERE id=%s", (request.args.get("edit"),))
        edit_data = cur.fetchone()

        # FIX DATE FORMAT
        if edit_data and edit_data['date']:
            edit_data['date'] = str(edit_data['date'])

    # ================= FETCH DATA =================
    cur.execute("SELECT * FROM income WHERE deleted_at IS NULL ORDER BY id DESC")
    data = cur.fetchall()

    total = sum([float(r['amount']) for r in data])

    # ================= FORM =================
    html = f"""
    <h2>💰 Income</h2>

    <form method="POST">
        <input type="hidden" name="id" value="{edit_data['id'] if edit_data else ''}">
        
        Amount: <input name="amount" value="{edit_data['amount'] if edit_data else ''}" required><br>
        Source: <input name="source" value="{edit_data['source'] if edit_data else ''}" required><br>
        Date: <input name="date" type="date" value="{edit_data['date'] if edit_data else ''}" required><br>
        Description: <input name="description" value="{edit_data['description'] if edit_data else ''}"><br>
        
        <button>{'Update Income' if edit_data else 'Add Income'}</button>
    </form>

    <h3>Total: {total}</h3>

    <table border="1">
    <tr>
        <th>Amount</th>
        <th>Source</th>
        <th>Date</th>
        <th>Description</th>
        <th>Action</th>
    </tr>
    """

    # ================= TABLE =================
    for r in data:
        html += f"""
        <tr>
            <td>{r['amount']}</td>
            <td>{r['source']}</td>
            <td>{r['date']}</td>
            <td>{r['description'] if r['description'] else ''}</td>
            <td>
                <a href="/income?edit={r['id']}">Edit</a> |
                <a href="/income?delete={r['id']}" onclick="return confirm('Delete this record?')">Delete</a>
            </td>
        </tr>
        """

    html += "</table><br><a href='/dashboard'>Back</a>"

    return html
@app.route('/expenses', methods=['GET','POST'])
def expenses():
    db = get_db()
    cur = db.cursor()

    # ================= ADD =================
    if request.method == 'POST':
        cur.execute("""
        INSERT INTO expenses(amount, category, date, description, done_by, user_id)
        VALUES(%s,%s,%s,%s,%s,%s)
        """, (
            request.form['amount'],
            request.form['category'],
            request.form['date'],
            request.form['description'],
            session.get('username'),
            session.get('user_id')
        ))
        db.commit()
        return redirect('/expenses')

    # ================= DELETE (SOFT) =================
    if 'delete' in request.args:
        cur.execute("UPDATE expenses SET deleted_at=NOW() WHERE id=%s", (request.args.get('delete'),))
        db.commit()
        return redirect('/expenses')

    # ================= FETCH =================
    cur.execute("SELECT * FROM expenses WHERE deleted_at IS NULL ORDER BY id DESC")
    rows = cur.fetchall()

    # ================= TABLE =================
    table = ""
    for r in rows:
        table += f"""
        <tr>
            <td>{r['amount']}</td>
            <td>{r['category']}</td>
            <td>{r['date']}</td>
            <td>{r.get('description','')}</td>
            <td>{r['done_by']}</td>
            <td>{r['status']}</td>
            <td>{r['created_at']}</td>
            <td>
                <a href='?delete={r['id']}'>Delete</a>
            </td>
        </tr>
        """

    return f"""
    <h2>💸 Expenses</h2>

    <form method="POST">
        <input name="amount" placeholder="Amount"><br>
        <input name="category" placeholder="Category"><br>
        <input name="date" type="date"><br>
        <input name="description" placeholder="Description"><br>
        <button>Add</button>
    </form>

    <table border="1">
        <tr>
            <th>Amount</th>
            <th>Category</th>
            <th>Date</th>
            <th>Description</th>
            <th>Done By</th>
            <th>Status</th>
            <th>Created</th>
            <th>Action</th>
        </tr>
        {table}
    </table>

    <br>
    <a href='/dashboard'>Back</a>
    """

# ---------- ACTIVITIES ----------
@app.route("/activity", methods=["GET", "POST"])
def activity():
    db = get_db()
    cur = db.cursor()

    # ================= ADD / UPDATE =================
    if request.method == "POST":
        if request.form.get("id"):  # UPDATE
            cur.execute("""
                UPDATE activity 
                SET title=%s, description=%s, status=%s, date=%s
                WHERE id=%s
            """, (
                request.form['title'],
                request.form.get('description',''),
                request.form['status'],
                request.form['date'],
                request.form['id']
            ))
        else:  # ADD
            cur.execute("""
                INSERT INTO activity (title, description, status, date, done_by, user_id)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                request.form['title'],
                request.form.get('description',''),
                request.form['status'],
                request.form['date'],
                session.get("username"),
                session.get("user_id")
            ))

        db.commit()
        return redirect("/activity")

    # ================= DELETE (SOFT) =================
    if request.args.get("delete"):
        cur.execute("""
            UPDATE activity SET deleted_at=NOW()
            WHERE id=%s
        """, (request.args.get("delete"),))
        db.commit()
        return redirect("/activity")

    # ================= EDIT FETCH =================
    edit_data = None
    if request.args.get("edit"):
        cur.execute("SELECT * FROM activity WHERE id=%s", (request.args.get("edit"),))
        edit_data = cur.fetchone()

    # ================= FETCH DATA =================
    cur.execute("""
        SELECT * FROM activity 
        WHERE deleted_at IS NULL 
        ORDER BY id DESC
    """)
    data = cur.fetchall()

    total = len(data)

    # ================= FORM =================
    html = f"""
    <h2>📋 Activity</h2>

    <form method="POST">
        <input type="hidden" name="id" value="{edit_data['id'] if edit_data else ''}">
        
        Title: <input name="title" value="{edit_data['title'] if edit_data else ''}"><br>
        
        Description: <input name="description" value="{edit_data.get('description','') if edit_data else ''}"><br>
        
        Status:
        <select name="status">
            <option value="pending" {'selected' if edit_data and edit_data['status']=='pending' else ''}>Pending</option>
            <option value="done" {'selected' if edit_data and edit_data['status']=='done' else ''}>Done</option>
        </select><br>

        Date: <input type="date" name="date" value="{edit_data['date'] if edit_data else ''}"><br>
        
        <button>{'Update' if edit_data else 'Add'}</button>
    </form>

    <h3>Total Activities: {total}</h3>

    <table border="1">
    <tr>
        <th>Title</th>
        <th>Description</th>
        <th>Status</th>
        <th>Date</th>
        <th>Done By</th>
        <th>Created</th>
        <th>Action</th>
    </tr>
    """

    # ================= TABLE =================
    for r in data:
        html += f"""
        <tr>
            <td>{r['title']}</td>
            <td>{r.get('description','')}</td>
            <td>{r['status']}</td>
            <td>{r['date']}</td>
            <td>{r['done_by']}</td>
            <td>{r['created_at']}</td>
            <td>
                <a href="?edit={r['id']}">Edit</a> |
                <a href="?delete={r['id']}">Delete</a>
            </td>
        </tr>
        """

    html += "</table><br><a href='/dashboard'>Back</a>"

    return html

# ---------- AI ----------
@app.route('/ai_advice')
def ai_advice():
    if 'user_id' not in session:
        return redirect('/')

    conn = get_db()
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT amount FROM income WHERE user_id=%s", (session['user_id'],))
    incomes = cursor.fetchall()

    cursor.execute("SELECT amount FROM expenses WHERE user_id=%s", (session['user_id'],))
    expenses = cursor.fetchall()

    conn.close()

    summary, advice = analyze_finance(incomes, expenses)

    return f"""
    <h2>🧠 AI Financial Advisor</h2>
    <pre>{summary}</pre>
    <h3>Advice:</h3>
    <p>{advice}</p>
    <a href="/dashboard">⬅ Back</a>
    """


if __name__ == "__main__":
    app.run(debug=True)

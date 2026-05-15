# ================= IMPORTS =================
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
# ================= PDF EXPORT =================
@app.route("/income/pdf")
def income_pdf():

    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT * FROM income ORDER BY id DESC")
    rows = cur.fetchall()

    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4)

    data = [["Amount", "Source", "Date", "Description"]]

    for r in rows:
        data.append([
            str(r['amount']),
            r['source'],
            str(r['date']),
            str(r.get('description', '-'))
        ])

    table = Table(data)
    pdf.build([table])

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="income_report.pdf",
        mimetype="application/pdf"
    )


# ================= INCOME =================
@app.route("/income", methods=["GET", "POST"])
def income():

    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()

    # ================= DELETE =================
    delete_id = request.args.get("delete")

    if delete_id:
        cur.execute("DELETE FROM income WHERE id=%s", (delete_id,))
        db.commit()
        return redirect("/income")

    # ================= EDIT =================
    edit_id = request.args.get("edit")
    edit_data = None

    if edit_id:
        cur.execute("SELECT * FROM income WHERE id=%s", (edit_id,))
        edit_data = cur.fetchone()

    # ================= SEARCH =================
    search = request.args.get("search", "")

    # ================= ADD / UPDATE =================
    if request.method == "POST":

        try:
            income_id = request.form.get("id")

            amount = request.form.get("amount")
            source = request.form.get("source")
            date = request.form.get("date")
            description = request.form.get("description")

            if not amount or not source:
                return "Amount and Source are required ❌"

            try:
                amount = float(amount)
            except:
                return "Amount must be a number ❌"

            if not date:
                date = None

            if income_id:
                cur.execute("""
                UPDATE income
                SET amount=%s,
                    source=%s,
                    date=%s,
                    description=%s
                WHERE id=%s
                """, (amount, source, date, description, income_id))

            else:
                cur.execute("""
                INSERT INTO income(
                    amount,
                    source,
                    date,
                    description,
                    done_by,
                    user_id
                )
                VALUES(%s,%s,%s,%s,%s,%s)
                """, (
                    amount,
                    source,
                    date,
                    description,
                    session.get('username'),
                    session.get('user_id')
                ))

            db.commit()
            return redirect("/income")

        except Exception as e:
            return f"ERROR: {str(e)}"

    # ================= FETCH =================
    if search:
        cur.execute("""
        SELECT * FROM income
        WHERE source LIKE %s OR description LIKE %s
        ORDER BY id DESC
        """, (f"%{search}%", f"%{search}%"))
    else:
        cur.execute("SELECT * FROM income ORDER BY id DESC")

    data = cur.fetchall()

    cur.execute("SELECT COALESCE(SUM(amount),0) AS total FROM income")
    total = cur.fetchone()['total']

    db.close()

    # ================= EDIT VALUES =================
    amount_val = edit_data["amount"] if edit_data else ""
    source_val = edit_data["source"] if edit_data else ""
    date_val = edit_data["date"] if edit_data else ""
    desc_val = edit_data["description"] if edit_data else ""
    edit_id_val = edit_data["id"] if edit_data else ""

    # ================= HTML ROWS =================
    html_rows = ""

    for r in data:
        html_rows += f"""
<tr>
<td>{r['amount']}</td>
<td>{r['source']}</td>
<td>{r['date']}</td>
<td>{r.get('description','-')}</td>
<td>
<a class="edit" href="/income?edit={r['id']}">Edit</a>
<a class="delete" href="/income?delete={r['id']}" onclick="return confirm('Delete this item?')">Delete</a>
</td>
</tr>
"""

    # ================= FINAL HTML =================
    return f"""
<!DOCTYPE html>
<html>
<head>
<title>Income</title>

<style>
body {{
    font-family: 'Segoe UI';
    background: #f4f6fb;
    margin: 20px;
}}

.container {{
    max-width: 1000px;
    margin: auto;
}}

h2 {{
    text-align: center;
}}

.card {{
    background: white;
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 20px;
}}

form {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
}}

input {{
    padding: 10px;
    border: 1px solid #ddd;
    border-radius: 8px;
}}

button {{
    grid-column: span 2;
    padding: 12px;
    background: #4e54c8;
    color: white;
    border: none;
    border-radius: 8px;
}}

table {{
    width: 100%;
    border-collapse: collapse;
}}

th {{
    background: #4e54c8;
    color: white;
    padding: 10px;
}}

td {{
    text-align: center;
    padding: 10px;
}}

.edit {{ background: orange; color: white; padding:5px; border-radius:5px; }}
.delete {{ background: red; color: white; padding:5px; border-radius:5px; }}

.search {{
    display:flex;
    gap:10px;
}}

.search input {{
    flex:1;
}}

.total {{
    background:#eaf2ff;
    padding:10px;
    border-radius:10px;
    margin-bottom:10px;
}}
</style>

</head>

<body>

<div class="container">

<h2>💰 Income Management</h2>

<div class="total">
Total Income: {total}
</div>

<div class="card">

<form method="GET" class="search">
<input name="search" placeholder="Search income">
<button>Search</button>
</form>

<form method="POST">

<input type="hidden" name="id" value="{edit_id_val}">

<input name="amount" placeholder="Amount" value="{amount_val}" required>
<input name="source" placeholder="Source" value="{source_val}" required>
<input type="date" name="date" value="{date_val}">
<input name="description" placeholder="Description" value="{desc_val}">

<button>{'Update Income' if edit_data else 'Add Income'}</button>

</form>

</div>

<div class="card">

<table>
<tr>
<th>Amount</th>
<th>Source</th>
<th>Date</th>
<th>Description</th>
<th>Action</th>
</tr>

{html_rows}

</table>

<br>

<div style="text-align:center;">
<a href="/dashboard">⬅ Back</a>
</div>

</div>

</div>

</body>
</html>
"""
# ================= EXPENSES =================
@app.route('/expenses', methods=['GET', 'POST'])
def expenses():

    db = get_db()
    cur = db.cursor()

    # ADD
    if request.method == 'POST':

        cur.execute("""
        INSERT INTO expenses(
            amount,
            category,
            date,
            description,
            done_by,
            user_id
        )
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

    # DELETE
    if request.args.get('delete'):

        cur.execute("""
        UPDATE expenses
        SET deleted_at=NOW()
        WHERE id=%s
        """, (request.args.get('delete'),))

        db.commit()

        return redirect('/expenses')

    # FETCH
    cur.execute("""
    SELECT * FROM expenses
    WHERE deleted_at IS NULL
    ORDER BY id DESC
    """)

    rows = cur.fetchall()

    db.close()

    table = ""

    for r in rows:

        table += f"""
<tr>

<td>{r['amount']}</td>

<td>{r['category']}</td>

<td>{r['date']}</td>

<td>{r.get('description','')}</td>

<td>{r.get('done_by','')}</td>

<td>{r['created_at']}</td>

<td>
<a href='?delete={r['id']}'>Delete</a>
</td>

</tr>
"""

    return f"""
<h2>💸 Expenses</h2>

<form method="POST">

<input name="amount" placeholder="Amount"><br><br>

<input name="category" placeholder="Category"><br><br>

<input name="date" type="date"><br><br>

<input name="description" placeholder="Description"><br><br>

<button>Add</button>

</form>

<table border="1">

<tr>
<th>Amount</th>
<th>Category</th>
<th>Date</th>
<th>Description</th>
<th>Done By</th>
<th>Created</th>
<th>Action</th>
</tr>

{table}

</table>

<br>

<a href='/dashboard'>Back</a>
"""


# ================= ACTIVITIES =================
@app.route("/activity", methods=["GET", "POST"])
def activity():

    db = get_db()
    cur = db.cursor()

    # ADD / UPDATE
    if request.method == "POST":

        if request.form.get("id"):

            cur.execute("""
            UPDATE activities
            SET activity_name=%s,
                description=%s,
                status=%s,
                date=%s
            WHERE id=%s
            """, (
                request.form['activity_name'],
                request.form.get('description', ''),
                request.form['status'],
                request.form['date'],
                request.form['id']
            ))

        else:

            cur.execute("""
            INSERT INTO activities(
                activity_name,
                description,
                status,
                date,
                done_by,
                user_id
            )
            VALUES(%s,%s,%s,%s,%s,%s)
            """, (
                request.form['activity_name'],
                request.form.get('description', ''),
                request.form['status'],
                request.form['date'],
                session.get("username"),
                session.get("user_id")
            ))

        db.commit()

        return redirect("/activity")

    # DELETE
    if request.args.get("delete"):

        cur.execute("""
        UPDATE activities
        SET deleted_at=NOW()
        WHERE id=%s
        """, (request.args.get("delete"),))

        db.commit()

        return redirect("/activity")

    # EDIT
    edit_data = None

    if request.args.get("edit"):

        cur.execute("""
        SELECT * FROM activities
        WHERE id=%s
        """, (request.args.get("edit"),))

        edit_data = cur.fetchone()

    # FETCH
    cur.execute("""
    SELECT * FROM activities
    WHERE deleted_at IS NULL
    ORDER BY id DESC
    """)

    data = cur.fetchall()

    db.close()

    total = len(data)

    html = f"""
<h2>📋 Activity</h2>

<form method="POST">

<input type="hidden" name="id" value="{edit_data['id'] if edit_data else ''}">

Activity Name:
<input name="activity_name" value="{edit_data['activity_name'] if edit_data else ''}"><br><br>

Description:
<input name="description" value="{edit_data.get('description','') if edit_data else ''}"><br><br>

Status:

<select name="status">

<option value="pending"
{'selected' if edit_data and edit_data['status']=='pending' else ''}>
Pending
</option>

<option value="done"
{'selected' if edit_data and edit_data['status']=='done' else ''}>
Done
</option>

</select><br><br>

Date:
<input type="date" name="date" value="{edit_data['date'] if edit_data else ''}"><br><br>

<button>{'Update' if edit_data else 'Add'}</button>

</form>

<h3>Total Activities: {total}</h3>

<table border="1">

<tr>
<th>Activity</th>
<th>Description</th>
<th>Status</th>
<th>Date</th>
<th>Done By</th>
<th>Created</th>
<th>Action</th>
</tr>
"""

    for r in data:

        html += f"""
<tr>

<td>{r['activity_name']}</td>

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

    html += """
</table>

<br>

<a href='/dashboard'>Back</a>
"""

    return html


# ================= AI =================
@app.route('/ai_advice')
def ai_advice():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT amount FROM income WHERE user_id=%s",
        (session['user_id'],)
    )

    incomes = cursor.fetchall()

    cursor.execute(
        "SELECT amount FROM expenses WHERE user_id=%s",
        (session['user_id'],)
    )

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


# ================= RUN =================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

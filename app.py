# ================= IMPORTS =================
import os
import io
import pymysql

from flask import Flask, request, redirect, session, send_file

from reportlab.platypus import SimpleDocTemplate, Table
from reportlab.lib.pagesizes import A4

from ai_engine import analyze_finance

app = Flask(__name__)

# ================= SECRET KEY =================
app.secret_key = os.environ.get("SECRET_KEY", "hirwa_secret_key")


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

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) UNIQUE,
        password VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # INCOME
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

    db.commit()
    db.close()

    return "🚀 DATABASE READY (FULL FIXED VERSION)"


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

    # DELETE
    delete_id = request.args.get("delete")

    if delete_id:
        cur.execute("DELETE FROM income WHERE id=%s", (delete_id,))
        db.commit()
        return redirect("/income")

    # EDIT
    edit_id = request.args.get("edit")
    edit_data = None

    if edit_id:
        cur.execute("SELECT * FROM income WHERE id=%s", (edit_id,))
        edit_data = cur.fetchone()

    # SEARCH
    search = request.args.get("search", "")

    # ADD / UPDATE
    if request.method == "POST":

        try:
            income_id = request.form.get("id")

            amount = request.form.get("amount")
            source = request.form.get("source")
            date = request.form.get("date")
            description = request.form.get("description")

            # VALIDATION
            if not amount or not source:
                return "Amount and Source are required ❌"

            try:
                amount = float(amount)
            except:
                return "Amount must be a number ❌"

            if not date:
                date = None

            # UPDATE
            if income_id:

                cur.execute("""
                UPDATE income
                SET amount=%s,
                    source=%s,
                    date=%s,
                    description=%s
                WHERE id=%s
                """, (amount, source, date, description, income_id))

            # INSERT
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

    # FETCH (SEARCH ENABLED)
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

    # EDIT VALUES
    amount_val = edit_data["amount"] if edit_data else ""
    source_val = edit_data["source"] if edit_data else ""
    date_val = edit_data["date"] if edit_data else ""
    desc_val = edit_data["description"] if edit_data else ""
    edit_id_val = edit_data["id"] if edit_data else ""

    return f"""
<h2>💰 Income Management</h2>

<a href="/income/pdf"><button>📄 Export PDF</button></a>

<form method="GET">
    <input name="search" placeholder="Search income...">
    <button>Search</button>
</form>

<h3>Total: {total}</h3>

<form method="POST">

<input type="hidden" name="id" value="{edit_id_val}">

<input name="amount" placeholder="Amount" value="{amount_val}" required><br><br>

<input name="source" placeholder="Source" value="{source_val}" required><br><br>

<input type="date" name="date" value="{date_val}"><br><br>

<input name="description" placeholder="Description" value="{desc_val}"><br><br>

<button>{'Update' if edit_data else 'Add'}</button>

</form>

<table border="1">

<tr>
<th>Amount</th>
<th>Source</th>
<th>Date</th>
<th>Description</th>
<th>Action</th>
</tr>

""" + "".join([
f"""
<tr>
<td>{r['amount']}</td>
<td>{r['source']}</td>
<td>{r['date']}</td>
<td>{r.get('description','-')}</td>
<td>
<a href="/income?edit={r['id']}">Edit</a> |
<a href="/income?delete={r['id']}">Delete</a>
</td>
</tr>
""" for r in data
]) + """
</table>

<br>
<a href="/dashboard">⬅ Back</a>
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

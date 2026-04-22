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
from flask import Response
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook
from docx import Document


@app.route('/income', methods=['GET','POST'])
def income():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()
    user_id = session['user_id']

    # ===== DELETE =====
    delete_id = request.args.get('delete')
    if delete_id:
        cur.execute("DELETE FROM income WHERE id=%s AND user_id=%s", (delete_id, user_id))
        db.commit()
        return redirect('/income')

    # ===== ADD =====
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

    # ===== FETCH =====
    cur.execute("SELECT * FROM income WHERE user_id=%s ORDER BY id DESC", (user_id,))
    rows = cur.fetchall()

    total = sum(float(r['amount']) for r in rows)

    # ===== HTML =====
    html = f"""
    <h2>Add Income</h2>
    <form method="POST">
    Amount:<input name="amount"><br>
    Source:<input name="source"><br>
    Date:<input type="date" name="date"><br>
    Note:<input name="note"><br>
    <button>Save</button>
    </form>

    <h3>Total Income: {total}</h3>

    <table border="1" cellpadding="8">
    <tr>
        <th>#</th><th>Amount</th><th>Source</th><th>Date</th><th>Note</th><th>Actions</th>
    </tr>
    """

    for i, r in enumerate(rows, 1):
        html += f"""
        <tr>
            <td>{i}</td>
            <td>{r['amount']}</td>
            <td>{r['source']}</td>
            <td>{r['date']}</td>
            <td>{r['note']}</td>
            <td>
                <a href="/income?delete={r['id']}">Delete</a>
            </td>
        </tr>
        """

    html += """
    </table>
    <br>
    <a href="/income/report/pdf">Download PDF</a> |
    <a href="/income/report/docx">Download DOC</a> |
    <a href="/income/report/excel">Download Excel</a>
    <br><br>
    <a href="/dashboard">Back</a>
    """
    return html
@app.route('/income/report/pdf')
def income_pdf():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM income WHERE user_id=%s", (session['user_id'],))
    rows = cur.fetchall()

    file = "income_report.pdf"
    doc = SimpleDocTemplate(file)
    styles = getSampleStyleSheet()

    content = "INCOME REPORT\n\n"
    for r in rows:
        content += f"{r['amount']} - {r['source']} - {r['date']}\n"

    doc.build([Paragraph(content, styles['Normal'])])
    return send_file(file, as_attachment=True)


@app.route('/income/report/docx')
def income_docx():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM income WHERE user_id=%s", (session['user_id'],))
    rows = cur.fetchall()

    file = "income_report.docx"
    doc = Document()
    doc.add_heading("Income Report", 0)

    for r in rows:
        doc.add_paragraph(f"{r['amount']} - {r['source']} - {r['date']}")

    doc.save(file)
    return send_file(file, as_attachment=True)


@app.route('/income/report/excel')
def income_excel():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM income WHERE user_id=%s", (session['user_id'],))
    rows = cur.fetchall()

    file = "income_report.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["Amount", "Source", "Date", "Note"])

    for r in rows:
        ws.append([r['amount'], r['source'], r['date'], r['note']])

    wb.save(file)
    return send_file(file, as_attachment=True)

# ================= EXPENSES =================
@app.route('/expenses', methods=['GET','POST'])
def expenses():
    if 'user_id' not in session:
        return redirect('/login')

    db = get_db()
    cur = db.cursor()
    user_id = session['user_id']

    # ===== DELETE =====
    delete_id = request.args.get('delete')
    if delete_id:
        cur.execute("DELETE FROM expenses WHERE id=%s AND user_id=%s", (delete_id, user_id))
        db.commit()
        return redirect('/expenses')

    # ===== ADD =====
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

    # ===== FETCH =====
    cur.execute("SELECT * FROM expenses WHERE user_id=%s ORDER BY id DESC", (user_id,))
    rows = cur.fetchall()

    total = sum(float(r['amount']) for r in rows)

    # ===== HTML =====
    html = f"""
    <h2>Add Expense</h2>
    <form method="POST">
    Amount:<input name="amount"><br>
    Category:<input name="category"><br>
    Date:<input type="date" name="date"><br>
    Note:<input name="note"><br>
    <button>Save</button>
    </form>

    <h3>Total Expenses: {total}</h3>

    <table border="1" cellpadding="8">
    <tr>
        <th>#</th><th>Amount</th><th>Category</th><th>Date</th><th>Note</th><th>Actions</th>
    </tr>
    """

    for i, r in enumerate(rows, 1):
        html += f"""
        <tr>
            <td>{i}</td>
            <td>{r['amount']}</td>
            <td>{r['category']}</td>
            <td>{r['date']}</td>
            <td>{r['note']}</td>
            <td>
                <a href="/expenses?delete={r['id']}">Delete</a>
            </td>
        </tr>
        """

    html += """
    </table>
    <br>
    <a href="/expenses/report/pdf">Download PDF</a> |
    <a href="/expenses/report/docx">Download DOC</a> |
    <a href="/expenses/report/excel">Download Excel</a>
    <br><br>
    <a href="/dashboard">Back</a>
    """
    return html
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook
from docx import Document


@app.route('/expenses/report/pdf')
def expenses_pdf():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM expenses WHERE user_id=%s", (session['user_id'],))
    rows = cur.fetchall()

    file = "expenses_report.pdf"
    doc = SimpleDocTemplate(file)
    styles = getSampleStyleSheet()

    content = "EXPENSE REPORT\n\n"
    for r in rows:
        content += f"{r['amount']} - {r['category']} - {r['date']}\n"

    doc.build([Paragraph(content, styles['Normal'])])
    return send_file(file, as_attachment=True)


@app.route('/expenses/report/docx')
def expenses_docx():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM expenses WHERE user_id=%s", (session['user_id'],))
    rows = cur.fetchall()

    file = "expenses_report.docx"
    doc = Document()
    doc.add_heading("Expenses Report", 0)

    for r in rows:
        doc.add_paragraph(f"{r['amount']} - {r['category']} - {r['date']}")

    doc.save(file)
    return send_file(file, as_attachment=True)


@app.route('/expenses/report/excel')
def expenses_excel():
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM expenses WHERE user_id=%s", (session['user_id'],))
    rows = cur.fetchall()

    file = "expenses_report.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["Amount", "Category", "Date", "Note"])

    for r in rows:
        ws.append([r['amount'], r['category'], r['date'], r['note']])

    wb.save(file)
    return send_file(file, as_attachment=True)
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

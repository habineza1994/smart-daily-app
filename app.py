from flask import Flask, request, jsonify, send_file
from flask_mysql import MySQL
from flask_bcrypt import Bcrypt
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import datetime

app = Flask(__name__)

app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'finance_db'

mysql = MySQL(app)
bcrypt = Bcrypt(app)

# ---------- AUTH ----------
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    hashed = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO users(username,password) VALUES(%s,%s)",
                (data['username'], hashed))
    conn.commit()
    return jsonify({"message": "User created"})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE username=%s",
                (data['username'],))
    user = cur.fetchone()
    if user and bcrypt.check_password_hash(user[0], data['password']):
        return jsonify({"message": "Login success"})
    return jsonify({"message": "Login failed"}), 401


# ---------- INCOME ----------
@app.route('/income', methods=['POST'])
def add_income():
    data = request.json
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO income(amount,source,date,note) VALUES(%s,%s,%s,%s)",
        (data['amount'], data['source'], data['date'], data['note'])
    )
    conn.commit()
    return jsonify({"message": "Income added"})


@app.route('/income', methods=['GET'])
def list_income():
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM income")
    return jsonify(cur.fetchall())


# ---------- EXPENSES ----------
@app.route('/expenses', methods=['POST'])
def add_expense():
    data = request.json
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO expenses(amount,category,date,note) VALUES(%s,%s,%s,%s)",
        (data['amount'], data['category'], data['date'], data['note'])
    )
    conn.commit()
    return jsonify({"message": "Expense added"})


@app.route('/expenses', methods=['GET'])
def list_expenses():
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM expenses")
    return jsonify(cur.fetchall())


# ---------- ACTIVITIES ----------
@app.route('/activities', methods=['POST'])
def add_activity():
    data = request.json
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO activities(activity_name,done_by,date,description) VALUES(%s,%s,%s,%s)",
        (data['activity_name'], data['done_by'], data['date'], data['description'])
    )
    conn.commit()
    return jsonify({"message": "Activity added"})


@app.route('/activities', methods=['GET'])
def list_activities():
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM activities")
    return jsonify(cur.fetchall())


# ---------- REPORT ----------
@app.route('/report', methods=['GET'])
def report():
    conn = mysql.connect()
    cur = conn.cursor()

    cur.execute("SELECT SUM(amount) FROM income")
    total_income = cur.fetchone()[0] or 0

    cur.execute("SELECT SUM(amount) FROM expenses")
    total_expense = cur.fetchone()[0] or 0

    profit = total_income - total_expense

    file = "report.pdf"
    doc = SimpleDocTemplate(file)
    styles = getSampleStyleSheet()

    content = f"""
    FINANCE REPORT
    Date: {datetime.date.today()}

    Total Income: {total_income}
    Total Expense: {total_expense}
    Profit: {profit}
    """

    doc.build([Paragraph(content, styles['Normal'])])

    return send_file(file, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)

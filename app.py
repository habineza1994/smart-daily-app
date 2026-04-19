from flask import Flask, request, jsonify, send_file
from flask_mysql import MySQL
from flask_bcrypt import Bcrypt
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import jwt
import datetime
import config

app = Flask(__name__)

# ---------- CONFIG ----------
app.config['MYSQL_DATABASE_HOST'] = config.MYSQL_HOST
app.config['MYSQL_DATABASE_USER'] = config.MYSQL_USER
app.config['MYSQL_DATABASE_PASSWORD'] = config.MYSQL_PASSWORD
app.config['MYSQL_DATABASE_DB'] = config.MYSQL_DB

mysql = MySQL(app)
bcrypt = Bcrypt(app)

# ---------- HELPERS ----------
def get_user_id():
    token = request.headers.get('Authorization')
    if not token:
        return None
    try:
        data = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
        return data['user_id']
    except:
        return None


# ---------- AUTH ----------
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    hashed = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users(username,password) VALUES(%s,%s)",
        (data['username'], hashed)
    )
    conn.commit()
    return jsonify({"message": "User created"})


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, password FROM users WHERE username=%s",
        (data['username'],)
    )
    user = cur.fetchone()

    if user and bcrypt.check_password_hash(user[1], data['password']):
        token = jwt.encode({
            'user_id': user[0],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, config.SECRET_KEY, algorithm='HS256')

        return jsonify({"token": token})

    return jsonify({"message": "Login failed"}), 401


# ---------- INCOME ----------
@app.route('/income', methods=['POST'])
def add_income():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO income(amount,source,date,note,user_id) VALUES(%s,%s,%s,%s,%s)",
        (data['amount'], data['source'], data['date'], data['note'], user_id)
    )
    conn.commit()
    return jsonify({"message": "Income added"})


@app.route('/income', methods=['GET'])
def list_income():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM income WHERE user_id=%s", (user_id,))
    return jsonify(cur.fetchall())


# ---------- EXPENSES ----------
@app.route('/expenses', methods=['POST'])
def add_expense():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO expenses(amount,category,date,note,user_id) VALUES(%s,%s,%s,%s,%s)",
        (data['amount'], data['category'], data['date'], data['note'], user_id)
    )
    conn.commit()
    return jsonify({"message": "Expense added"})


@app.route('/expenses', methods=['GET'])
def list_expenses():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM expenses WHERE user_id=%s", (user_id,))
    return jsonify(cur.fetchall())


# ---------- ACTIVITIES ----------
@app.route('/activities', methods=['POST'])
def add_activity():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO activities(activity_name,done_by,date,description,user_id) VALUES(%s,%s,%s,%s,%s)",
        (data['activity_name'], data['done_by'], data['date'], data['description'], user_id)
    )
    conn.commit()
    return jsonify({"message": "Activity added"})


@app.route('/activities', methods=['GET'])
def list_activities():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = mysql.connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM activities WHERE user_id=%s", (user_id,))
    return jsonify(cur.fetchall())


# ---------- REPORT ----------
@app.route('/report', methods=['GET'])
def report():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = mysql.connect()
    cur = conn.cursor()

    cur.execute("SELECT SUM(amount) FROM income WHERE user_id=%s", (user_id,))
    total_income = cur.fetchone()[0] or 0

    cur.execute("SELECT SUM(amount) FROM expenses WHERE user_id=%s", (user_id,))
    total_expense = cur.fetchone()[0] or 0

    profit = total_income - total_expense

    file = f"report_{user_id}.pdf"
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

import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import config
from flask import Flask, request, jsonify, send_file

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY


# ================= DATABASE =================
def get_db():
    return pymysql.connect(
        host=config.MYSQL_HOST,
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        database=config.MYSQL_DB,
        cursorclass=pymysql.cursors.DictCursor
    )
@app.route("/initdb")
def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()
    return "DB Initialized"

# ================= HOME =================
@app.route("/")
def home():
    return "HIRWA SMART DAILY APP IS WORKING ✅"


# ================= TOKEN HELPER =================
def get_user_id():
    token = request.headers.get('Authorization')
    if not token:
        return None
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return data['user_id']
    except:
        return None


# ================= AUTH =================
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    password = generate_password_hash(data['password'])

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO users(username,password) VALUES(%s,%s)",
        (data['username'], password)
    )
    db.commit()

    return jsonify({"message": "User created"})


@app.route('/login', methods=['POST'])
def login():
    data = request.json

    db = get_db()
    cur = db.cursor()
    cur.execute(
        "SELECT id, password FROM users WHERE username=%s",
        (data['username'],)
    )
    user = cur.fetchone()

    if user and check_password_hash(user['password'], data['password']):
        token = jwt.encode({
            'user_id': user['id'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({"token": token})

    return jsonify({"message": "Login failed"}), 401


# ================= INCOME =================
@app.route('/income', methods=['POST'])
def add_income():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO income(amount,source,date,note,user_id) VALUES(%s,%s,%s,%s,%s)",
        (data['amount'], data['source'], data['date'], data['note'], user_id)
    )
    db.commit()

    return jsonify({"message": "Income added"})


@app.route('/income', methods=['GET'])
def list_income():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM income WHERE user_id=%s", (user_id,))
    return jsonify(cur.fetchall())


# ================= EXPENSES =================
@app.route('/expenses', methods=['POST'])
def add_expense():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO expenses(amount,category,date,note,user_id) VALUES(%s,%s,%s,%s,%s)",
        (data['amount'], data['category'], data['date'], data['note'], user_id)
    )
    db.commit()

    return jsonify({"message": "Expense added"})


@app.route('/expenses', methods=['GET'])
def list_expenses():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM expenses WHERE user_id=%s", (user_id,))
    return jsonify(cur.fetchall())


# ================= ACTIVITIES =================
@app.route('/activities', methods=['POST'])
def add_activity():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO activities(activity_name,done_by,date,description,user_id) VALUES(%s,%s,%s,%s,%s)",
        (data['activity_name'], data['done_by'], data['date'], data['description'], user_id)
    )
    db.commit()

    return jsonify({"message": "Activity added"})


@app.route('/activities', methods=['GET'])
def list_activities():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM activities WHERE user_id=%s", (user_id,))
    return jsonify(cur.fetchall())


# ================= REPORT PDF =================
@app.route('/report', methods=['GET'])
def report():
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    db = get_db()
    cur = db.cursor()

    cur.execute("SELECT SUM(amount) AS total FROM income WHERE user_id=%s", (user_id,))
    total_income = cur.fetchone()['total'] or 0

    cur.execute("SELECT SUM(amount) AS total FROM expenses WHERE user_id=%s", (user_id,))
    total_expense = cur.fetchone()['total'] or 0

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


# ================= RUN =================
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

import os
import jwt
import datetime
import config
import pymysql

from flask import Flask, request, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY


# ===== MySQL connection using pymysql =====
def get_db():
    return pymysql.connect(
        host=os.environ.get('MYSQLHOST'),
        user=os.environ.get('MYSQLUSER'),
        password=os.environ.get('MYSQLPASSWORD'),
        database=os.environ.get('MYSQLDATABASE'),
        cursorclass=pymysql.cursors.DictCursor
    )
@app.route("/initdb")
def init_db():
    conn = get_db()
    cur = conn.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(100) NOT NULL,
        password VARCHAR(255) NOT NULL
    )
    """)

    # INCOME
    cur.execute("""
    CREATE TABLE IF NOT EXISTS income (
        id INT AUTO_INCREMENT PRIMARY KEY,
        amount DECIMAL(10,2),
        source VARCHAR(255),
        date DATE,
        note TEXT,
        user_id INT
    )
    """)

    # EXPENSES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INT AUTO_INCREMENT PRIMARY KEY,
        amount DECIMAL(10,2),
        category VARCHAR(255),
        date DATE,
        note TEXT,
        user_id INT
    )
    """)

    # ACTIVITIES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activities (
        id INT AUTO_INCREMENT PRIMARY KEY,
        activity_name VARCHAR(255),
        done_by VARCHAR(255),
        date DATE,
        description TEXT,
        user_id INT
    )
    """)

    conn.commit()
    cur.close()
    conn.close()
    return "ALL TABLES CREATED"
# ================= TEST DB =================
@app.route("/testdb")
def test_db():
    import os, pymysql
    try:
        conn = pymysql.connect(
            host=os.environ.get("MYSQLHOST"),
            user=os.environ.get("MYSQLUSER"),
            password=os.environ.get("MYSQLPASSWORD"),
            database=os.environ.get("MYSQLDATABASE"),
            port=int(os.environ.get("MYSQLPORT", 3306))
        )
        conn.close()
        return "DB OK"
    except Exception as e:
        return f"DB ERROR: {e}"
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

@app.route('/users', methods=['GET'])
def get_users():
    token = request.headers.get('Authorization')

    if not token:
        return jsonify({"message": "Token is missing"}), 401

    try:
        token = token.split(" ")[1]
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        user_id = data['user_id']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, username FROM users")
        users = cursor.fetchall()

        result = []
        for u in users:
            result.append({
                "id": u[0],
                "username": u[1]
            })

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 401
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

@app.errorhandler(Exception)
def handle_exception(e):
    return f"SERVER ERROR:\n{e}", 500
# ================= RUN =================
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

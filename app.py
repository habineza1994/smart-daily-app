from flask import Flask, request, redirect, render_template, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback_secret_key")

# ================= DATABASE =================
def get_db():
    conn = sqlite3.connect('app.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        amount INTEGER
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task TEXT,
        done INTEGER DEFAULT 0
    )''')

    conn.commit()
    conn.close()

init_db()

# ================= AUTH CHECK =================
def login_required():
    if 'user_id' not in session:
        return False
    return True

# ================= HOME =================
@app.route('/')
def home():
    if not login_required():
        return redirect('/login_page')

    conn = get_db()
    c = conn.cursor()

    user_id = session['user_id']

    c.execute("SELECT SUM(amount) FROM finance WHERE user_id=? AND type='income'", (user_id,))
    income = c.fetchone()[0] or 0

    c.execute("SELECT SUM(amount) FROM finance WHERE user_id=? AND type='expense'", (user_id,))
    expense = c.fetchone()[0] or 0

    balance = income - expense

    c.execute("SELECT * FROM notes WHERE user_id=?", (user_id,))
notes = [dict(row) for row in c.fetchall()]

c.execute("SELECT * FROM tasks WHERE user_id=?", (user_id,))
tasks = [dict(row) for row in c.fetchall()])

    conn.close()

    return render_template('dashboard.html',
                           income=income,
                           expense=expense,
                           balance=balance,
                           notes=notes,
                           tasks=tasks)

# ================= REGISTER =================
@app.route('/register_page')
def register_page():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']

    if not username or not password:
        return "Fill all fields"

    hashed = generate_password_hash(password)

    conn = get_db()
    c = conn.cursor()

    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
        conn.commit()
    except Exception as e:
        return "User already exists"

    conn.close()
    return redirect('/login_page')

# ================= LOGIN =================
@app.route('/login_page')
def login_page():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        return redirect('/')

    return "Login failed"

# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login_page')

# ================= FINANCE =================
@app.route('/add', methods=['POST'])
def add():
    if not login_required():
        return redirect('/login_page')

    try:
        amount = int(request.form['amount'])
    except:
        return "Invalid amount"

    ftype = request.form['type']

    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO finance (user_id, type, amount) VALUES (?, ?, ?)",
              (session['user_id'], ftype, amount))
    conn.commit()
    conn.close()

    return redirect('/')

# ================= NOTES =================
@app.route('/add_note', methods=['POST'])
def add_note():
    if not login_required():
        return redirect('/login_page')

    content = request.form['content']
    if not content:
        return redirect('/')

    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO notes (user_id, content) VALUES (?, ?)",
              (session['user_id'], content))
    conn.commit()
    conn.close()

    return redirect('/')

@app.route('/delete_note/<int:id>', methods=['POST'])
def delete_note(id):
    if not login_required():
        return redirect('/login_page')

    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM notes WHERE id=? AND user_id=?", (id, session['user_id']))
    conn.commit()
    conn.close()

    return redirect('/')

# ================= TASKS =================
@app.route('/add_task', methods=['POST'])
def add_task():
    if not login_required():
        return redirect('/login_page')

    task = request.form['task']
    if not task:
        return redirect('/')

    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id, task) VALUES (?, ?)",
              (session['user_id'], task))
    conn.commit()
    conn.close()

    return redirect('/')

@app.route('/toggle_task/<int:id>', methods=['POST'])
def toggle_task(id):
    if not login_required():
        return redirect('/login_page')

    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE tasks SET done = CASE WHEN done=1 THEN 0 ELSE 1 END WHERE id=? AND user_id=?",
              (id, session['user_id']))
    conn.commit()
    conn.close()

    return redirect('/')

@app.route('/delete_task/<int:id>', methods=['POST'])
def delete_task(id):
    if not login_required():
        return redirect('/login_page')

    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (id, session['user_id']))
    conn.commit()
    conn.close()

    return redirect('/')

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)

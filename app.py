from flask import Flask, request, redirect, render_template_string, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_key_123"

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()

    # USERS
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    ''')

    # FINANCE
    c.execute('''
    CREATE TABLE IF NOT EXISTS finance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT,
        amount INTEGER
    )
    ''')

    # NOTES
    c.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT
    )
    ''')

    # TASKS
    c.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        task TEXT
    )
    ''')

    conn.commit()
    conn.close()

# CALL DATABASE
init_db()

# ================= HOME =================
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect('/login_page')

    conn = sqlite3.connect('app.db')
    c = conn.cursor()

    # FINANCE
    c.execute("SELECT SUM(amount) FROM finance WHERE user_id=? AND type='income'", (session['user_id'],))
    income = c.fetchone()[0] or 0

    c.execute("SELECT SUM(amount) FROM finance WHERE user_id=? AND type='expense'", (session['user_id'],))
    expense = c.fetchone()[0] or 0

    balance = income - expense

    conn.close()

    return render_template_string('''
    <h2>Smart Daily App</h2>
    <a href="/logout">Logout</a>

    <h3>💰 Finance</h3>
    <form method="post" action="/add">
        <input name="amount" placeholder="Amount" required>
        <select name="type">
            <option value="income">Income</option>
            <option value="expense">Expense</option>
        </select>
        <button>Add</button>
    </form>

    <p>Income: {{income}}</p>
    <p>Expense: {{expense}}</p>
    <p><b>Balance: {{balance}}</b></p>

    <h3>📝 Notes</h3>
    <form method="post" action="/add_note">
        <input name="content" placeholder="Write note">
        <button>Add Note</button>
    </form>

    <h3>📅 Tasks</h3>
    <form method="post" action="/add_task">
        <input name="task" placeholder="New task">
        <button>Add Task</button>
    </form>
    ''', income=income, expense=expense, balance=balance)

# ================= REGISTER PAGE =================
@app.route('/register_page')
def register_page():
    return render_template_string('''
    <h2>Register</h2>
    <form method="post" action="/register">
        <input name="username" placeholder="Username" required><br><br>
        <input name="password" type="password" placeholder="Password" required><br><br>
        <button type="submit">Register</button>
    </form>
    <a href="/login_page">Go to Login</a>
    ''')

# ================= LOGIN PAGE =================
@app.route('/login_page')
def login_page():
    return render_template_string('''
    <h2>Login</h2>
    <form method="post" action="/login">
        <input name="username" placeholder="Username" required><br><br>
        <input name="password" type="password" placeholder="Password" required><br><br>
        <button type="submit">Login</button>
    </form>
    <a href="/register_page">Create account</a>
    ''')

# ================= REGISTER =================
@app.route('/register', methods=['POST'])
def register():
    u = request.form['username']
    p = request.form['password']

    hashed_password = generate_password_hash(p)

    conn = sqlite3.connect('app.db')
    c = conn.cursor()

    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (u, hashed_password))
        conn.commit()
    except:
        pass

    conn.close()
    return redirect('/login_page')

# ================= LOGIN =================
@app.route('/login', methods=['POST'])
def login():
    u = request.form['username']
    p = request.form['password']

    conn = sqlite3.connect('app.db')
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE username=?", (u,))
    user = c.fetchone()

    conn.close()

    if user and check_password_hash(user[2], p):
        session['user_id'] = user[0]
        return redirect('/')

    return "Login Failed ❌"

# ================= ADD FINANCE =================
@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect('/login_page')

    amount = int(request.form['amount'])
    t = request.form['type']

    conn = sqlite3.connect('app.db')
    c = conn.cursor()

    c.execute("INSERT INTO finance (user_id, type, amount) VALUES (?, ?, ?)",
              (session['user_id'], t, amount))

    conn.commit()
    conn.close()

    return redirect('/')

# ================= ADD NOTE =================
@app.route('/add_note', methods=['POST'])
def add_note():
    if 'user_id' not in session:
        return redirect('/login_page')

    content = request.form['content']

    conn = sqlite3.connect('app.db')
    c = conn.cursor()

    c.execute("INSERT INTO notes (user_id, content) VALUES (?, ?)",
              (session['user_id'], content))

    conn.commit()
    conn.close()

    return redirect('/')

# ================= ADD TASK =================
@app.route('/add_task', methods=['POST'])
def add_task():
    if 'user_id' not in session:
        return redirect('/login_page')

    task = request.form['task']

    conn = sqlite3.connect('app.db')
    c = conn.cursor()

    c.execute("INSERT INTO tasks (user_id, task) VALUES (?, ?)",
              (session['user_id'], task))

    conn.commit()
    conn.close()

    return redirect('/')

# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login_page')

# ================= RUN =================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

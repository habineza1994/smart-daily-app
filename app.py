from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, redirect, render_template_string, session
import sqlite3
import hashlib

app = Flask(__name__)
app.secret_key = 'super_secret_key'

# ---------- DATABASE ----------
conn = sqlite3.connect('app.db')
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)''')

c.execute('''CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    amount REAL,
    description TEXT
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
    status TEXT
)''')

conn.commit()
conn.close()

# ---------- HTML ----------
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { font-family: Arial; padding: 10px; background:#f5f5f5; }
.card { background:white; padding:10px; margin:10px 0; border-radius:10px; }
input, select { width:100%; padding:8px; margin:5px 0; }
button { width:100%; padding:10px; background:green; color:white; border:none; }
</style>
</head>
<body>

<h2>🔥 Smart Daily App</h2>

{% if not session.get('user_id') %}

<div class="card">
<h3>Login</h3>
<form method="POST" action="/login">
<input name="username" required>
<input type="password" name="password" required>
<button>Login</button>
</form>
</div>

<div class="card">
<h3>Register</h3>
<form method="POST" action="/register">
<input name="username" required>
<input type="password" name="password" required>
<button>Register</button>
</form>
</div>

{% else %}

<div class="card"><a href="/logout">Logout</a></div>

<div class="card">
<h3>💰 Finance</h3>
<form method="POST" action="/add">
<select name="type">
<option value="income">Income</option>
<option value="expense">Expense</option>
</select>
<input name="amount" type="number" required>
<input name="description">
<button>Add</button>
</form>

<p>Income: {{income}}</p>
<p>Expense: {{expense}}</p>
<p><b>Balance: {{balance}}</b></p>
</div>

<div class="card">
<h3>📝 Notes</h3>
<form method="POST" action="/add_note">
<input name="content" placeholder="Write note" required>
<button>Add Note</button>
</form>

<ul>
{% for n in notes %}
<li>{{n[2]}}</li>
{% endfor %}
</ul>
</div>

<div class="card">
<h3>📅 Tasks</h3>
<form method="POST" action="/add_task">
<input name="task" placeholder="New task" required>
<button>Add Task</button>
</form>

<ul>
{% for t in tasks %}
<li>{{t[2]}} - {{t[3]}}</li>
{% endfor %}
</ul>
</div>

{% endif %}

</body>
</html>
"""

# ---------- FUNCTIONS ----------
def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

# ---------- ROUTES ----------
@app.route('/')
def index():
    if not session.get('user_id'):
        return render_template_string(TEMPLATE, income=0, expense=0, balance=0, notes=[], tasks=[])

    conn = sqlite3.connect('app.db')
    c = conn.cursor()

    c.execute("SELECT * FROM transactions WHERE user_id=?", (session['user_id'],))
    data = c.fetchall()

    c.execute("SELECT * FROM notes WHERE user_id=?", (session['user_id'],))
    notes = c.fetchall()

    c.execute("SELECT * FROM tasks WHERE user_id=?", (session['user_id'],))
    tasks = c.fetchall()

    conn.close()

    income = sum([x[3] for x in data if x[2]=='income'])
    expense = sum([x[3] for x in data if x[2]=='expense'])
    balance = income - expense

    return render_template_string(TEMPLATE, income=income, expense=expense, balance=balance, notes=notes, tasks=tasks)
@app.route('/register', methods=['POST'])
def register():
    u = request.form['username']
    p = hash_password(request.form['password'])

    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    try:
        hashed_password = generate_password_hash(password)

c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
    except:
        pass
    conn.close()
    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    u = request.form['username']
    p = hash_password(request.form['password'])

    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
    user = c.fetchone()
    conn.close()

    if user:
        if user and check_password_hash(user[2], password):

    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/add', methods=['POST'])
def add():
    if not session.get('user_id'):
        return redirect('/')

    t = request.form['type']
    a = float(request.form['amount'])
    d = request.form['description']

    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("INSERT INTO transactions (user_id, type, amount, description) VALUES (?,?,?,?)",
              (session['user_id'], t, a, d))
    conn.commit()
    conn.close()

    return redirect('/')

@app.route('/add_note', methods=['POST'])
def add_note():
    if not session.get('user_id'):
        return redirect('/')

    content = request.form['content']

    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("INSERT INTO notes (user_id, content) VALUES (?,?)", (session['user_id'], content))
    conn.commit()
    conn.close()

    return redirect('/')

@app.route('/add_task', methods=['POST'])
def add_task():
    if not session.get('user_id'):
        return redirect('/')

    task = request.form['task']

    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id, task, status) VALUES (?,?,?)",
              (session['user_id'], task, 'pending'))
    conn.commit()
    conn.close()

    return redirect('/')

if __name__ == '__main__':
    import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

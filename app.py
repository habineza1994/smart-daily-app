from flask import Flask, request, redirect, render_template_string, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "very_long_random_secret_key_!@#2026_secure"

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect('app.db')
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

# ================= HOME =================
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect('/login_page')

    conn = sqlite3.connect('app.db')
    c = conn.cursor()

    c.execute("SELECT SUM(amount) FROM finance WHERE user_id=? AND type='income'", (session['user_id'],))
    income = c.fetchone()[0] or 0

    c.execute("SELECT SUM(amount) FROM finance WHERE user_id=? AND type='expense'", (session['user_id'],))
    expense = c.fetchone()[0] or 0

    balance = income - expense

    c.execute("SELECT id, content FROM notes WHERE user_id=?", (session['user_id'],))
    notes = c.fetchall()

    c.execute("SELECT id, task, done FROM tasks WHERE user_id=?", (session['user_id'],))
    tasks = c.fetchall()

    conn.close()

    return render_template_string('''
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
    body { font-family: Arial; background: #f4f6f9; padding: 20px; }
    .card { background: white; padding: 15px; margin-bottom: 15px;
            border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1);}
    button { background: #4CAF50; color: white; border: none; padding: 6px 10px; border-radius: 5px;}
    input, select { padding: 6px; margin: 5px; border-radius: 5px; border: 1px solid #ccc;}
    .done { text-decoration: line-through; color: gray; }
    </style>

    <h2>📱 Smart Daily App</h2>
    <a href="/logout">Logout</a>

    <div class="card">
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

    <canvas id="chart"></canvas>
    </div>

    <div class="card">
    <h3>📝 Notes</h3>
    <form method="post" action="/add_note">
        <input name="content">
        <button>Add</button>
    </form>

    <ul>
    {% for note in notes %}
        <li>{{note[1]}} <a href="/delete_note/{{note[0]}}">❌</a></li>
    {% endfor %}
    </ul>
    </div>

    <div class="card">
    <h3>📅 Tasks</h3>
    <form method="post" action="/add_task">
        <input name="task">
        <button>Add</button>
    </form>

    <ul>
    {% for task in tasks %}
        <li class="{{'done' if task[2]==1 else ''}}">
            {{task[1]}}
            <a href="/toggle_task/{{task[0]}}">✅</a>
            <a href="/delete_task/{{task[0]}}">❌</a>
        </li>
    {% endfor %}
    </ul>
    </div>

    <script>
    // CHART
    new Chart(document.getElementById("chart"), {
        type: 'pie',
        data: {
            labels: ['Income', 'Expense'],
            datasets: [{
                data: [{{income}}, {{expense}}],
                backgroundColor: ['green', 'red']
            }]
        }
    });

    // NOTIFICATION
    if (Notification.permission !== "granted") {
        Notification.requestPermission();
    }

    function notify() {
        new Notification("Smart Daily App", {
            body: "Wibuke gukora tasks zawe!"
        });
    }

    setTimeout(notify, 5000);
    </script>
    ''', income=income, expense=expense, balance=balance, notes=notes, tasks=tasks)

# باقي routes ntizihindutse (zose zigume uko zari)
# ================= REST OF YOUR CODE =================

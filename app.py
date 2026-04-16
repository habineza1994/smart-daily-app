from flask import Flask, request, redirect, render_template_string, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# ================= HOME =================
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect('/login_page')

    return render_template_string('''
    <h2>Smart Daily App</h2>
    <a href="/logout">Logout</a>

    <h3>Welcome 🎉</h3>
    ''')

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

# ================= LOGOUT =================
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login_page')

# ================= RUN =================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

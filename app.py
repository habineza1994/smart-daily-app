# ================= TASK TOGGLE =================
@app.route('/toggle_task/<int:id>')
def toggle_task(id):
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("UPDATE tasks SET done = CASE WHEN done=1 THEN 0 ELSE 1 END WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

# ================= AUTH =================
@app.route('/register_page')
def register_page():
    return render_template_string('''
    <h2>Register</h2>
    <form method="post" action="/register">
        <input name="username" required><br><br>
        <input name="password" type="password" required><br><br>
        <button>Register</button>
    </form>
    <a href="/login_page">Login</a>
    ''')

@app.route('/login_page')
def login_page():
    return render_template_string('''
    <h2>Login</h2>
    <form method="post" action="/login">
        <input name="username" required><br><br>
        <input name="password" type="password" required><br><br>
        <button>Login</button>
    </form>
    <a href="/register_page">Register</a>
    ''')

@app.route('/register', methods=['POST'])
def register():
    u = request.form['username']
    p = generate_password_hash(request.form['password'])

    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (u, p))
        conn.commit()
    except:
        pass
    conn.close()
    return redirect('/login_page')

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

    return "Login Failed"

# ================= ACTIONS =================
@app.route('/add', methods=['POST'])
def add():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("INSERT INTO finance (user_id, type, amount) VALUES (?, ?, ?)",
              (session['user_id'], request.form['type'], int(request.form['amount'])))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/add_note', methods=['POST'])
def add_note():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("INSERT INTO notes (user_id, content) VALUES (?, ?)",
              (session['user_id'], request.form['content']))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/delete_note/<int:id>')
def delete_note(id):
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("DELETE FROM notes WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/add_task', methods=['POST'])
def add_task():
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("INSERT INTO tasks (user_id, task) VALUES (?, ?)",
              (session['user_id'], request.form['task']))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/delete_task/<int:id>')
def delete_task(id):
    conn = sqlite3.connect('app.db')
    c = conn.cursor()
    c.execute("DELETE FROM tasks WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login_page')

# ================= RUN =================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

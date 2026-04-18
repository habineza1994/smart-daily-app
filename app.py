from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_key"

# ================= DATABASE =================
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user',
        active INTEGER DEFAULT 1
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        content TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= AUTH =================
@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()

        if user and check_password_hash(user["password"], password) and user["active"] == 1:
            session["user_id"] = user["id"]
            session["role"] = user["role"]

            if user["role"] == "admin":
                return redirect("/admin")
            return redirect("/dashboard")

        return "Login Failed"

    return render_template("login.html")


@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        conn = get_db()
        conn.execute("INSERT INTO users (username,password) VALUES (?,?)", (username,password))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")

# ================= ADMIN =================
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect("/")

    conn = get_db()
    users = conn.execute("SELECT * FROM users").fetchall()
    records = conn.execute("""
        SELECT records.*, users.username 
        FROM records 
        JOIN users ON records.user_id = users.id
    """).fetchall()

    return render_template("admin.html", users=users, records=records)


@app.route("/disable/<int:id>")
def disable(id):
    conn = get_db()
    conn.execute("UPDATE users SET active=0 WHERE id=?", (id,))
    conn.commit()
    return redirect("/admin")


# ================= USER =================
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    if request.method == "POST":
        content = request.form["content"]

        conn = get_db()
        conn.execute("INSERT INTO records (user_id, content) VALUES (?,?)",
                     (session["user_id"], content))
        conn.commit()

    conn = get_db()
    records = conn.execute("SELECT * FROM records WHERE user_id=?",
                           (session["user_id"],)).fetchall()

    return render_template("user.html", records=records)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)

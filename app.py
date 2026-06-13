# ================= HIRWA SMART PRO VERSION (SUPABASE READY) =================

import os
import io
import datetime
import psycopg2

from flask import Flask, request, redirect, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash

from reportlab.platypus import (
SimpleDocTemplate,
Table,
TableStyle,
Paragraph,
Spacer
)

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# Optional AI engine import (safe fallback)

try:
from ai_engine import analyze_finance
except ImportError:
analyze_finance = None

# ================= APP =================

app = Flask(**name**)

# ================= SECURITY =================

app.secret_key = os.environ.get(
"SECRET_KEY",
"hirwa_secret_key_change_this"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Production Ready

app.config["SESSION_COOKIE_SECURE"] = True

app.permanent_session_lifetime = datetime.timedelta(minutes=30)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

# ================= SUPABASE DATABASE =================

def get_db():
conn = psycopg2.connect(
os.environ["DATABASE_URL"],
sslmode="require"
)
return conn

# ================= INIT DB (SUPABASE POSTGRESQL VERSION) =================
@app.route("/initdb")
def init_db():

    db = get_db()
    cur = db.cursor()

    # USERS
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # INCOME
    cur.execute("""
    CREATE TABLE IF NOT EXISTS income(
        id SERIAL PRIMARY KEY,
        amount REAL,
        source TEXT,
        date TEXT,
        description TEXT,
        done_by TEXT,
        status TEXT DEFAULT 'approved',
        user_id INTEGER,
        deleted_at TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # EXPENSES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses(
        id SERIAL PRIMARY KEY,
        amount REAL,
        category TEXT,
        date TEXT,
        description TEXT,
        done_by TEXT,
        status TEXT DEFAULT 'approved',
        user_id INTEGER,
        deleted_at TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # ACTIVITIES
    cur.execute("""
    CREATE TABLE IF NOT EXISTS activities(
        id SERIAL PRIMARY KEY,
        activity_name TEXT,
        description TEXT,
        status TEXT,
        date TEXT,
        done_by TEXT,
        user_id INTEGER,
        deleted_at TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    db.commit()
    cur.close()
    db.close()

    return "Supabase Database Ready ✅"


# ================= HOME =================
@app.route("/")
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>

    <title>HIRWA SMART PRO</title>

    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <style>

    *{
        margin:0;
        padding:0;
        box-sizing:border-box;
        font-family:Arial,sans-serif;
    }

    body{
        min-height:100vh;
        display:flex;
        justify-content:center;
        align-items:center;
        background:linear-gradient(120deg,#4e54c8,#8f94fb);
        padding:20px;
    }

    .card{
        background:white;
        color:black;
        width:100%;
        max-width:400px;
        padding:35px;
        border-radius:20px;
        text-align:center;
        box-shadow:0 15px 35px rgba(0,0,0,0.25);
    }

    h1{
        color:#4e54c8;
        margin-bottom:10px;
    }

    .subtitle{
        color:#666;
        margin-bottom:25px;
        font-size:14px;
    }

    a{
        display:block;
        margin:12px 0;
        padding:12px;
        background:#4e54c8;
        color:white;
        text-decoration:none;
        border-radius:12px;
        transition:0.3s;
        font-weight:bold;
    }

    a:hover{
        background:#2e3192;
        transform:translateY(-2px);
    }

    .footer{
        margin-top:20px;
        color:gray;
        font-size:12px;
    }

    </style>

    </head>

    <body>

    <div class="card">

        <h1>HIRWA SMART PRO</h1>

        <p class="subtitle">
            Financial Management System
        </p>

        <a href="/login">
            🔐 Login
        </a>

        <a href="/register">
            📝 Register
        </a>

        <div class="footer">
            Version 1.0 | Smart Finance Solution
        </div>

    </div>

    </body>
    </html>
    """

# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password_raw = request.form.get("password", "").strip()

        # ================= VALIDATION =================
        if not username or not password_raw:
            return """
            <h3 style='color:red;text-align:center'>
            Username and Password required ❌
            </h3>
            """

        if len(password_raw) < 4:
            return """
            <h3 style='color:red;text-align:center'>
            Password must be at least 4 characters ❌
            </h3>
            """

        password = generate_password_hash(password_raw)

        db = get_db()
        cur = db.cursor()

        try:

            # ================= CHECK USER =================
            cur.execute(
                "SELECT id FROM users WHERE username = %s",
                (username,)
            )

            existing = cur.fetchone()

            if existing:
                cur.close()
                db.close()

                return """
                <h3 style='color:red;text-align:center'>
                Username already exists ❌
                </h3>
                """

            # ================= INSERT USER =================
            cur.execute(
                """
                INSERT INTO users (username, password)
                VALUES (%s, %s)
                """,
                (username, password)
            )

            db.commit()

            cur.close()
            db.close()

            return redirect("/login")

        except Exception as e:

            db.rollback()
            cur.close()
            db.close()

            return f"""
            <h3 style='color:red;text-align:center'>
            Error: {str(e)}
            </h3>
            """

    # ================= UI =================
    return """
<!DOCTYPE html>
<html>
<head>

<title>HIRWA SMART - Register</title>

<meta name="viewport" content="width=device-width, initial-scale=1">

<style>

*{
margin:0;
padding:0;
box-sizing:border-box;
font-family:Arial,sans-serif;
}

body{
height:100vh;
display:flex;
justify-content:center;
align-items:center;
background:linear-gradient(135deg,#4e54c8,#8f94fb);
padding:20px;
}

.card{
background:white;
width:100%;
max-width:420px;
padding:35px;
border-radius:25px;
box-shadow:0 15px 35px rgba(0,0,0,.2);
}

.logo{
text-align:center;
margin-bottom:25px;
}

.logo h1{
color:#4e54c8;
font-size:30px;
}

.logo p{
color:gray;
font-size:14px;
}

input{
width:100%;
padding:14px;
border-radius:12px;
border:1px solid #ddd;
outline:none;
font-size:15px;
margin-bottom:15px;
}

input:focus{
border-color:#4e54c8;
}

button{
width:100%;
padding:14px;
border:none;
border-radius:12px;
background:#4e54c8;
color:white;
font-size:16px;
cursor:pointer;
transition:.3s;
}

button:hover{
opacity:.9;
}

.login-link{
margin-top:20px;
text-align:center;
font-size:14px;
}

.login-link a{
color:#4e54c8;
text-decoration:none;
font-weight:bold;
}

.footer{
margin-top:20px;
text-align:center;
font-size:12px;
color:gray;
}

</style>

</head>

<body>

<div class="card">

<div class="logo">
<h1>HIRWA SMART</h1>
<p>Create your account</p>
</div>

<form method="POST">

<input type="text" name="username" placeholder="Username" required>

<input type="password" name="password" placeholder="Password" required>

<button type="submit">Register</button>

</form>

<div class="login-link">
Already have an account?
<a href="/login">Login</a>
</div>

<div class="footer">
Secure Registration System
</div>

</div>

</body>
</html>
"""

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        # ================= VALIDATION =================
        if not username or not password:
            return """
            <h3 style='color:red;text-align:center'>
            Fill all fields ❌
            </h3>
            """

        db = get_db()
        cur = db.cursor()

        try:

            # ================= FETCH USER (POSTGRES FIX) =================
            cur.execute(
                "SELECT * FROM users WHERE username = %s",
                (username,)
            )

            user = cur.fetchone()

            cur.close()
            db.close()

            # ================= VERIFY PASSWORD =================
            if user and check_password_hash(
                user["password"],
                password
            ):

                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session.permanent = True

                return redirect("/dashboard")

            return """
            <h3 style='color:red;text-align:center'>
            Invalid Username or Password ❌
            </h3>
            """

        except Exception as e:

            try:
                cur.close()
                db.close()
            except:
                pass

            return f"""
            <h3 style='color:red;text-align:center'>
            Error: {str(e)}
            </h3>
            """

    # ================= UI (UNCHANGED PRO DESIGN) =================
    return """
<!DOCTYPE html>
<html>

<head>

<title>HIRWA SMART Login</title>

<meta name="viewport" content="width=device-width, initial-scale=1">

<style>

*{
margin:0;
padding:0;
box-sizing:border-box;
font-family:Arial,sans-serif;
}

body{
height:100vh;
display:flex;
justify-content:center;
align-items:center;
background:linear-gradient(135deg,#4e54c8,#8f94fb);
padding:20px;
}

.card{
background:white;
width:100%;
max-width:420px;
padding:35px;
border-radius:25px;
box-shadow:0 15px 35px rgba(0,0,0,.2);
}

.logo{
text-align:center;
margin-bottom:25px;
}

.logo h1{
color:#4e54c8;
font-size:32px;
}

.logo p{
color:gray;
font-size:14px;
}

.input-box{
margin-bottom:15px;
position:relative;
}

input{
width:100%;
padding:14px;
border-radius:12px;
border:1px solid #ddd;
outline:none;
font-size:15px;
}

input:focus{
border-color:#4e54c8;
}

.password-toggle{
position:absolute;
right:15px;
top:14px;
cursor:pointer;
color:#4e54c8;
font-size:13px;
}

button{
width:100%;
padding:14px;
border:none;
border-radius:12px;
background:#4e54c8;
color:white;
font-size:16px;
cursor:pointer;
transition:.3s;
}

button:hover{
opacity:.9;
}

.forgot{
text-align:right;
margin-bottom:18px;
}

.forgot a{
text-decoration:none;
font-size:13px;
color:#4e54c8;
}

.footer{
margin-top:20px;
text-align:center;
font-size:13px;
color:gray;
}

.footer a{
color:#4e54c8;
text-decoration:none;
font-weight:bold;
}

</style>

</head>

<body>

<div class="card">

<div class="logo">
<h1>HIRWA SMART</h1>
<p>Financial Management System</p>
</div>

<form method="POST">

<div class="input-box">
<input type="text" name="username" placeholder="Username" required>
</div>

<div class="input-box">
<input id="password" type="password" name="password" placeholder="Password" required>

<span class="password-toggle" onclick="togglePassword()">
👁 Show
</span>

</div>

<div class="forgot">
<a href="/forgot_password">Forgot Password?</a>
</div>

<button type="submit">Login</button>

</form>

<div class="footer">
Secure System v1.0 <br><br>

Don't have an account?<br><br>

<a href="/register">Create Account</a>
</div>

</div>

<script>

function togglePassword(){
let pass = document.getElementById("password");

if(pass.type === "password"){
pass.type = "text";
document.querySelector(".password-toggle").innerHTML = "🙈 Hide";
}else{
pass.type = "password";
document.querySelector(".password-toggle").innerHTML = "👁 Show";
}
}

</script>

</body>

</html>
"""

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():

    # ================= AUTH =================
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']
    username = session.get('username', 'User')

    db = get_db()
    cur = db.cursor()

    try:

        # ================= INCOME =================
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS total FROM income WHERE user_id = %s",
            (user_id,)
        )
        income = float(cur.fetchone()["total"])

        # ================= EXPENSES =================
        cur.execute(
            "SELECT COALESCE(SUM(amount),0) AS total FROM expenses WHERE user_id = %s",
            (user_id,)
        )
        expenses = float(cur.fetchone()["total"])

        # ================= BALANCE =================
        balance = income - expenses

        # ================= ACTIVITY COUNT =================
        cur.execute(
            "SELECT COUNT(*) AS total FROM activities WHERE user_id = %s",
            (user_id,)
        )
        activities = cur.fetchone()["total"]

    except Exception as e:
        cur.close()
        db.close()
        return f"""
        <div style="padding:20px;color:red;text-align:center">
            Dashboard Error ❌<br>{str(e)}
        </div>
        """

    cur.close()
    db.close()

    # ================= STATUS NOTIFICATION =================
    if balance < 0:
        notif_color = "#f8d7da"
        notif_text = "⚠ Low Balance Warning"
        notif_text_color = "#721c24"
    else:
        notif_color = "#d4edda"
        notif_text = "✅ System Running Normally"
        notif_text_color = "#155724"

    # ================= HTML UI =================
    return f"""
<!DOCTYPE html>
<html>
<head>
<title>HIRWA SMART Dashboard</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>

* {{
    margin:0;
    padding:0;
    box-sizing:border-box;
    font-family:Arial;
}}

body {{
    background:#f4f6fb;
}}

.wrapper {{
    display:flex;
    min-height:100vh;
}}

.sidebar {{
    width:260px;
    background:linear-gradient(180deg,#4e54c8,#6c63ff);
    padding:25px;
    color:white;
}}

.sidebar h2 {{
    margin-bottom:20px;
}}

.sidebar a {{
    display:block;
    padding:12px;
    margin:8px 0;
    background:rgba(255,255,255,0.15);
    color:white;
    text-decoration:none;
    border-radius:10px;
    transition:0.3s;
}}

.sidebar a:hover {{
    background:rgba(255,255,255,0.3);
}}

.logout {{
    background:#ff4d4d !important;
}}

.main {{
    flex:1;
    padding:25px;
}}

.header {{
    background:linear-gradient(90deg,#4e54c8,#8f94fb);
    padding:20px;
    border-radius:20px;
    color:white;
    display:flex;
    justify-content:space-between;
    align-items:center;
}}

.cards {{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
    gap:15px;
    margin-top:20px;
}}

.card {{
    padding:20px;
    border-radius:20px;
    color:white;
    box-shadow:0 10px 25px rgba(0,0,0,0.1);
}}

.income {{ background:#28a745; }}
.expense {{ background:#dc3545; }}
.balance {{ background:#007bff; }}
.activity {{ background:#ff9800; }}

.chart-box {{
    margin-top:25px;
    background:white;
    padding:20px;
    border-radius:20px;
    box-shadow:0 5px 15px rgba(0,0,0,0.08);
}}

canvas {{
    height:350px !important;
}}

.notification {{
    background:{notif_color};
    color:{notif_text_color};
    padding:12px;
    border-radius:10px;
    margin-top:15px;
}}

</style>

</head>

<body>

<div class="wrapper">

<div class="sidebar">

<h2>HIRWA SMART</h2>
<p>👤 {username}</p>

<br>

<a href="/dashboard">🏠 Dashboard</a>
<a href="/income">💰 Income</a>
<a href="/expenses">💸 Expenses</a>
<a href="/activity">📋 Activities</a>
<a href="/ai_advice">🧠 AI Advice</a>
<a href="/export_pdf">📄 PDF Report</a>
<a href="/logout" class="logout">🚪 Logout</a>

</div>

<div class="main">

<div class="header">
    <div>
        <h2>Dashboard</h2>
        <p>Welcome back, {username}</p>
    </div>
</div>

<div class="notification">
    {notif_text}
</div>

<div class="cards">

<div class="card income">
<h3>💰 Income</h3>
<h1>{income}</h1>
</div>

<div class="card expense">
<h3>💸 Expenses</h3>
<h1>{expenses}</h1>
</div>

<div class="card balance">
<h3>📊 Balance</h3>
<h1>{balance}</h1>
</div>

<div class="card activity">
<h3>📋 Activities</h3>
<h1>{activities}</h1>
</div>

</div>

<div class="chart-box">
<h3>📈 Financial Overview</h3>
<br>
<canvas id="financeChart"></canvas>
</div>

</div>

</div>

<script>

const ctx = document.getElementById("financeChart");

new Chart(ctx, {{
    type: "bar",
    data: {{
        labels: ["Income", "Expenses", "Balance"],
        datasets: [{{
            label: "RWF",
            data: [{income}, {expenses}, {balance}]
        }}]
    }},
    options: {{
        responsive: true,
        maintainAspectRatio: false
    }}
}});

</script>

</body>
</html>
"""
# ================= LOGOUT =================
@app.route("/logout")
def logout():

    # Clear all session data securely
    session.clear()

    return redirect("/login")
# ================= INCOME =================
@app.route("/income", methods=["GET", "POST"])
def income():

    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    try:

        # ================= ADD INCOME =================
        if request.method == "POST" and "edit_id" not in request.form:

            amount = request.form.get("amount", "").strip()
            source = request.form.get("source", "").strip()
            date = request.form.get("date", "").strip()

            if not amount or not source or not date:
                return "<h3 style='color:red;text-align:center'>All fields required ❌</h3>"

            try:
                amount = float(amount)
                if amount <= 0:
                    return "<h3 style='color:red;text-align:center'>Amount must be > 0 ❌</h3>"
            except:
                return "<h3 style='color:red;text-align:center'>Invalid amount ❌</h3>"

            cur.execute("""
                INSERT INTO income(amount, source, date, user_id)
                VALUES (%s, %s, %s, %s)
            """, (amount, source, date, session["user_id"]))

            db.commit()
            return redirect("/income")

        # ================= EDIT INCOME (LOAD) =================
        edit_data = None
        edit_id = request.args.get("edit")

        if edit_id:
            cur.execute("""
                SELECT * FROM income
                WHERE id = %s AND user_id = %s AND deleted_at IS NULL
            """, (edit_id, session["user_id"]))
            edit_data = cur.fetchone()

        # ================= UPDATE INCOME =================
        if request.method == "POST" and "edit_id" in request.form:

            edit_id = request.form.get("edit_id")
            amount = request.form.get("amount", "").strip()
            source = request.form.get("source", "").strip()
            date = request.form.get("date", "").strip()

            cur.execute("""
                UPDATE income
                SET amount=%s,
                    source=%s,
                    date=%s,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=%s AND user_id=%s
            """, (amount, source, date, edit_id, session["user_id"]))

            db.commit()
            return redirect("/income")

        # ================= SOFT DELETE =================
        delete_id = request.args.get("delete")
        if delete_id:
            cur.execute("""
                UPDATE income
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE id=%s AND user_id=%s
            """, (delete_id, session["user_id"]))
            db.commit()
            return redirect("/income")

        # ================= FETCH INCOME =================
        cur.execute("""
            SELECT * FROM income
            WHERE user_id=%s AND deleted_at IS NULL
            ORDER BY date DESC
        """, (session["user_id"],))

        rows = cur.fetchall()

        # ================= TOTAL =================
        cur.execute("""
            SELECT COALESCE(SUM(amount),0) AS total
            FROM income
            WHERE user_id=%s AND deleted_at IS NULL
        """, (session["user_id"],))

        total_income = cur.fetchone()["total"]

    except Exception as e:
        cur.close()
        db.close()
        return f"<h3 style='color:red;text-align:center'>Error ❌ {str(e)}</h3>"

    cur.close()
    db.close()

    # ================= UI =================
    html = f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
    body {{
        font-family:Arial;
        background:#f4f6fb;
        padding:20px;
    }}

    .box {{
        background:white;
        padding:20px;
        border-radius:15px;
        max-width:700px;
        margin:auto;
        box-shadow:0 5px 15px rgba(0,0,0,0.1);
    }}

    input {{
        width:100%;
        padding:10px;
        margin:5px 0;
        border-radius:10px;
        border:1px solid #ddd;
    }}

    button {{
        width:100%;
        padding:10px;
        background:#28a745;
        color:white;
        border:none;
        border-radius:10px;
        cursor:pointer;
    }}

    .item {{
        padding:10px;
        border-bottom:1px solid #eee;
        display:flex;
        justify-content:space-between;
    }}

    .total {{
        background:#007bff;
        color:white;
        padding:10px;
        border-radius:10px;
        margin-bottom:15px;
        text-align:center;
    }}

    .actions a {{
        margin-left:10px;
        text-decoration:none;
        font-size:13px;
    }}

    .edit {{ color:green; }}
    .delete {{ color:red; }}
    </style>

    </head>

    <body>

    <div class="box">

    <h2>💰 Income PRO CRUD</h2>

    <div class="total">
        Total Income: {float(total_income):,.0f} RWF
    </div>
    """

    # ================= EDIT FORM =================
    if edit_data:
        html += f"""
        <form method="POST">
            <input type="hidden" name="edit_id" value="{edit_data['id']}">
            <input name="amount" value="{edit_data['amount']}" placeholder="Amount">
            <input name="source" value="{edit_data['source']}" placeholder="Source">
            <input type="date" name="date" value="{edit_data['date']}">
            <button>Update Income</button>
        </form>
        <hr>
        """
    else:
        html += """
        <form method="POST">
            <input name="amount" placeholder="Amount">
            <input name="source" placeholder="Source">
            <input type="date" name="date">
            <button>Add Income</button>
        </form>
        <hr>
        """

    # ================= LIST =================
    for r in rows:
        html += f"""
        <div class="item">
            <span>💰 {r['source']} - {r['date']} - <b>{float(r['amount']):,.0f}</b> RWF</span>

            <span class="actions">
                <a class="edit" href="/income?edit={r['id']}">Edit</a>
                <a class="delete" href="/income?delete={r['id']}">Delete</a>
            </span>
        </div>
        """

    html += """
    </div>
    </body>
    </html>
    """

    return html

# ================= EXPENSES =================
@app.route("/expenses", methods=["GET", "POST"])
def expenses():

    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    try:

        # ================= ADD EXPENSE =================
        if request.method == "POST" and "edit_id" not in request.form:

            amount = request.form.get("amount", "").strip()
            category = request.form.get("category", "").strip()
            date = request.form.get("date", "").strip()

            if not amount or not category or not date:
                return "<h3 style='color:red;text-align:center'>All fields required ❌</h3>"

            try:
                amount = float(amount)
                if amount <= 0:
                    return "<h3 style='color:red;text-align:center'>Amount must be > 0 ❌</h3>"
            except:
                return "<h3 style='color:red;text-align:center'>Invalid amount ❌</h3>"

            cur.execute("""
                INSERT INTO expenses(amount, category, date, user_id)
                VALUES (%s, %s, %s, %s)
            """, (amount, category, date, session["user_id"]))

            db.commit()
            return redirect("/expenses")

        # ================= LOAD EDIT =================
        edit_data = None
        edit_id = request.args.get("edit")

        if edit_id:
            cur.execute("""
                SELECT * FROM expenses
                WHERE id=%s AND user_id=%s AND deleted_at IS NULL
            """, (edit_id, session["user_id"]))
            edit_data = cur.fetchone()

        # ================= UPDATE EXPENSE =================
        if request.method == "POST" and "edit_id" in request.form:

            edit_id = request.form.get("edit_id")
            amount = request.form.get("amount", "").strip()
            category = request.form.get("category", "").strip()
            date = request.form.get("date", "").strip()

            try:
                amount = float(amount)
            except:
                return "<h3 style='color:red;text-align:center'>Invalid amount ❌</h3>"

            cur.execute("""
                UPDATE expenses
                SET amount=%s,
                    category=%s,
                    date=%s,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=%s AND user_id=%s
            """, (amount, category, date, edit_id, session["user_id"]))

            db.commit()
            return redirect("/expenses")

        # ================= SOFT DELETE =================
        delete_id = request.args.get("delete")
        if delete_id:
            cur.execute("""
                UPDATE expenses
                SET deleted_at=CURRENT_TIMESTAMP
                WHERE id=%s AND user_id=%s
            """, (delete_id, session["user_id"]))
            db.commit()
            return redirect("/expenses")

        # ================= FETCH =================
        cur.execute("""
            SELECT * FROM expenses
            WHERE user_id=%s AND deleted_at IS NULL
            ORDER BY date DESC
        """, (session["user_id"],))

        rows = cur.fetchall()

        # ================= TOTAL =================
        cur.execute("""
            SELECT COALESCE(SUM(amount),0) AS total
            FROM expenses
            WHERE user_id=%s AND deleted_at IS NULL
        """, (session["user_id"],))

        total_expenses = cur.fetchone()["total"]

    except Exception as e:
        cur.close()
        db.close()
        return f"<h3 style='color:red;text-align:center'>Error ❌ {str(e)}</h3>"

    cur.close()
    db.close()

    # ================= UI =================
    html = f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
    body {{
        font-family:Arial;
        background:#f4f6fb;
        padding:20px;
    }}

    .box {{
        background:white;
        padding:20px;
        border-radius:15px;
        max-width:700px;
        margin:auto;
        box-shadow:0 5px 15px rgba(0,0,0,0.1);
    }}

    input {{
        width:100%;
        padding:10px;
        margin:5px 0;
        border-radius:10px;
        border:1px solid #ddd;
    }}

    button {{
        width:100%;
        padding:10px;
        background:#dc3545;
        color:white;
        border:none;
        border-radius:10px;
        cursor:pointer;
    }}

    .item {{
        padding:10px;
        border-bottom:1px solid #eee;
        display:flex;
        justify-content:space-between;
        align-items:center;
    }}

    .total {{
        background:#dc3545;
        color:white;
        padding:10px;
        border-radius:10px;
        margin-bottom:15px;
        text-align:center;
    }}

    .actions a {{
        margin-left:10px;
        font-size:13px;
        text-decoration:none;
    }}

    .edit {{ color:green; }}
    .delete {{ color:red; }}
    </style>
    </head>

    <body>

    <div class="box">

    <h2>💸 Expenses PRO CRUD</h2>

    <div class="total">
        Total Expenses: {float(total_expenses):,.0f} RWF
    </div>
    """

    # ================= EDIT FORM =================
    if edit_data:
        html += f"""
        <form method="POST">
            <input type="hidden" name="edit_id" value="{edit_data['id']}">
            <input name="amount" value="{edit_data['amount']}" placeholder="Amount">
            <input name="category" value="{edit_data['category']}" placeholder="Category">
            <input type="date" name="date" value="{edit_data['date']}">
            <button>Update Expense</button>
        </form>
        <hr>
        """
    else:
        html += """
        <form method="POST">
            <input name="amount" placeholder="Amount">
            <input name="category" placeholder="Category">
            <input type="date" name="date">
            <button>Add Expense</button>
        </form>
        <hr>
        """

    # ================= LIST =================
    for r in rows:
        html += f"""
        <div class="item">
            <span>💸 {r['category']} - {r['date']} - <b>{float(r['amount']):,.0f}</b> RWF</span>

            <span>
                <a class="edit" href="/expenses?edit={r['id']}">Edit</a>
                <a class="delete" href="/expenses?delete={r['id']}">Delete</a>
            </span>
        </div>
        """

    html += """
    </div>
    </body>
    </html>
    """

    return html

# ================= ACTIVITIES PRO =================
@app.route("/activity", methods=["GET", "POST"])
def activity():

    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    try:

        # ================= ADD ACTIVITY =================
        if request.method == "POST" and "edit_id" not in request.form:

            activity_name = request.form.get("activity_name", "").strip()
            date = request.form.get("date", "").strip()

            if not activity_name or not date:
                return "<h3 style='color:red;text-align:center'>All fields required ❌</h3>"

            cur.execute("""
                INSERT INTO activities(activity_name, date, user_id)
                VALUES (%s, %s, %s)
            """, (
                activity_name,
                date,
                session["user_id"]
            ))

            db.commit()
            return redirect("/activity")

        # ================= LOAD EDIT =================
        edit_data = None
        edit_id = request.args.get("edit")

        if edit_id:
            cur.execute("""
                SELECT * FROM activities
                WHERE id=%s AND user_id=%s AND deleted_at IS NULL
            """, (edit_id, session["user_id"]))
            edit_data = cur.fetchone()

        # ================= UPDATE =================
        if request.method == "POST" and "edit_id" in request.form:

            edit_id = request.form.get("edit_id")
            activity_name = request.form.get("activity_name", "").strip()
            date = request.form.get("date", "").strip()

            if not activity_name or not date:
                return "<h3 style='color:red;text-align:center'>All fields required ❌</h3>"

            cur.execute("""
                UPDATE activities
                SET activity_name=%s,
                    date=%s,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=%s AND user_id=%s
            """, (activity_name, date, edit_id, session["user_id"]))

            db.commit()
            return redirect("/activity")

        # ================= SOFT DELETE =================
        delete_id = request.args.get("delete")
        if delete_id:
            cur.execute("""
                UPDATE activities
                SET deleted_at=CURRENT_TIMESTAMP
                WHERE id=%s AND user_id=%s
            """, (delete_id, session["user_id"]))
            db.commit()
            return redirect("/activity")

        # ================= FETCH =================
        cur.execute("""
            SELECT * FROM activities
            WHERE user_id=%s AND deleted_at IS NULL
            ORDER BY date DESC
        """, (session["user_id"],))

        rows = cur.fetchall()

        # ================= COUNT =================
        cur.execute("""
            SELECT COUNT(*) AS total
            FROM activities
            WHERE user_id=%s AND deleted_at IS NULL
        """, (session["user_id"],))

        total_activities = cur.fetchone()["total"]

    except Exception as e:
        cur.close()
        db.close()
        return f"<h3 style='color:red;text-align:center'>Error ❌ {str(e)}</h3>"

    cur.close()
    db.close()

    # ================= UI =================
    html = f"""
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <style>
    body {{
        font-family:Arial;
        background:#f4f6fb;
        padding:20px;
    }}

    .box {{
        background:white;
        padding:20px;
        border-radius:15px;
        max-width:700px;
        margin:auto;
        box-shadow:0 5px 15px rgba(0,0,0,0.1);
    }}

    input {{
        width:100%;
        padding:10px;
        margin:5px 0;
        border-radius:10px;
        border:1px solid #ddd;
    }}

    button {{
        width:100%;
        padding:10px;
        background:#ff9800;
        color:white;
        border:none;
        border-radius:10px;
        cursor:pointer;
    }}

    .item {{
        padding:10px;
        border-bottom:1px solid #eee;
        display:flex;
        justify-content:space-between;
        align-items:center;
    }}

    .total {{
        background:#ff9800;
        color:white;
        padding:10px;
        border-radius:10px;
        margin-bottom:15px;
        text-align:center;
    }}

    .actions a {{
        margin-left:10px;
        text-decoration:none;
        font-size:13px;
    }}

    .edit {{ color:green; }}
    .delete {{ color:red; }}
    </style>
    </head>

    <body>

    <div class="box">

    <h2>📋 Activities PRO CRUD</h2>

    <div class="total">
        Total Activities: {total_activities}
    </div>
    """

    # ================= EDIT FORM =================
    if edit_data:
        html += f"""
        <form method="POST">
            <input type="hidden" name="edit_id" value="{edit_data['id']}">
            <input name="activity_name" value="{edit_data['activity_name']}" placeholder="Activity Name">
            <input type="date" name="date" value="{edit_data['date']}">
            <button>Update Activity</button>
        </form>
        <hr>
        """
    else:
        html += """
        <form method="POST">
            <input name="activity_name" placeholder="Activity Name">
            <input type="date" name="date">
            <button>Add Activity</button>
        </form>
        <hr>
        """

    # ================= LIST =================
    for r in rows:
        html += f"""
        <div class="item">
            <span>📌 {r['activity_name']} - {r['date']}</span>
            <span>
                <a class="edit" href="/activity?edit={r['id']}">Edit</a>
                <a class="delete" href="/activity?delete={r['id']}">Delete</a>
            </span>
        </div>
        """

    html += """
    </div>
    </body>
    </html>
    """

    return html

# ================= AI ADVICE (PRO) =================
@app.route("/ai_advice")
def ai_advice():

    if "user_id" not in session:
        return redirect("/login")

    db = get_db()
    cur = db.cursor()

    try:

        # ================= INCOME =================
        cur.execute("""
            SELECT COALESCE(SUM(amount),0) AS total
            FROM income
            WHERE user_id = %s
        """, (session["user_id"],))

        total_income = float(cur.fetchone()["total"])

        # ================= EXPENSES =================
        cur.execute("""
            SELECT COALESCE(SUM(amount),0) AS total
            FROM expenses
            WHERE user_id = %s
        """, (session["user_id"],))

        total_expenses = float(cur.fetchone()["total"])

        balance = total_income - total_expenses

        # ================= RAW DATA =================
        cur.execute("""
            SELECT amount FROM income
            WHERE user_id = %s
        """, (session["user_id"],))
        income = cur.fetchall()

        cur.execute("""
            SELECT amount FROM expenses
            WHERE user_id = %s
        """, (session["user_id"],))
        expenses = cur.fetchall()

    except Exception as e:
        cur.close()
        db.close()
        return f"<h3 style='color:red;text-align:center'>Error ❌ {str(e)}</h3>"

    cur.close()
    db.close()

    # ================= AI ENGINE SAFE CALL =================
    summary = "No AI summary available"
    advice = "No AI advice available"

    if analyze_finance:
        try:
            summary, advice = analyze_finance(income, expenses)
        except:
            summary = "AI engine error"
            advice = "Check your financial data consistency"

    # ================= STATUS =================
    if balance < 0:
        status_color = "#dc3545"
        status_text = "⚠ Financial Risk"
    elif balance < total_income * 0.3:
        status_color = "#ff9800"
        status_text = "⚠ Medium Stability"
    else:
        status_color = "#28a745"
        status_text = "✅ Healthy Finance"

    # ================= UI =================
    return f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">

<style>

body {{
    font-family:Arial;
    background:#f4f6fb;
    padding:20px;
}}

.box {{
    background:white;
    padding:25px;
    border-radius:15px;
    max-width:800px;
    margin:auto;
    box-shadow:0 5px 15px rgba(0,0,0,0.1);
}}

.card {{
    padding:15px;
    border-radius:10px;
    margin-bottom:15px;
    color:white;
    background:{status_color};
    text-align:center;
    font-weight:bold;
}}

.stats {{
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
    gap:10px;
    margin-bottom:20px;
}}

.stat {{
    background:#eee;
    padding:15px;
    border-radius:10px;
    text-align:center;
}}

pre {{
    background:#f8f9fa;
    padding:15px;
    border-radius:10px;
    overflow:auto;
}}

.advice {{
    background:#e3f2fd;
    padding:15px;
    border-radius:10px;
}}

a {{
    display:block;
    text-align:center;
    margin-top:15px;
    text-decoration:none;
    color:#4e54c8;
    font-weight:bold;
}}

</style>

</head>

<body>

<div class="box">

<h2>🧠 AI Financial Advisor</h2>

<div class="card">
{status_text}
</div>

<div class="stats">

<div class="stat">
<h3>💰 Income</h3>
<p>{total_income:,.0f} RWF</p>
</div>

<div class="stat">
<h3>💸 Expenses</h3>
<p>{total_expenses:,.0f} RWF</p>
</div>

<div class="stat">
<h3>📊 Balance</h3>
<p>{balance:,.0f} RWF</p>
</div>

</div>

<h3>📈 Summary</h3>
<pre>{summary}</pre>

<h3>💡 Advice</h3>
<div class="advice">
{advice}
</div>

<a href="/dashboard">⬅ Back to Dashboard</a>

</div>

</body>
</html>
"""

if __name__ == "__main__":

    import os

    app.run(
        debug=os.environ.get("FLASK_DEBUG", "False") == "True",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )

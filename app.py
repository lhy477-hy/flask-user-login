from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import sys

app = Flask(__name__)
app.secret_key = "dev-key-2025"

USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "email": "admin@example.com",
        "phone": "13800138000",
        "balance": 99999
    },
    "alice": {
        "username": "alice",
        "password": "alice2025",
        "role": "user",
        "email": "alice@example.com",
        "phone": "13900139001",
        "balance": 100
    }
}

# ===== SQLite 数据库初始化 =====
DATABASE_DIR = "data"
DATABASE_PATH = os.path.join(DATABASE_DIR, "users.db")


def init_db():
    if not os.path.exists(DATABASE_DIR):
        os.makedirs(DATABASE_DIR)
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            phone TEXT
        )
    """)
    # 插入默认用户（重复插入时忽略）
    c.execute("INSERT OR IGNORE INTO users (username, password, email, phone) VALUES ('admin', 'admin123', 'admin@example.com', '13800138000')")
    c.execute("INSERT OR IGNORE INTO users (username, password, email, phone) VALUES ('alice', 'alice2025', 'alice@example.com', '13900139001')")
    conn.commit()
    conn.close()
    print("[DB] 数据库初始化完成，路径:", DATABASE_PATH)


@app.route("/")
def index():
    username = session.get("username")
    user_info = None
    search_results = None
    keyword = request.args.get("keyword", "")
    if keyword:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        sql = "SELECT id, username, email, phone FROM users WHERE username LIKE ? OR email LIKE ?"
        param = f"%{keyword}%"
        print(f"[SQL] {sql} (参数: {param})")
        sys.stdout.flush()
        c.execute(sql, (param, param))
        search_results = c.fetchall()
        conn.close()
    if username and username in USERS:
        user_info = USERS[username]
    return render_template("index.html", user=user_info, search_results=search_results, keyword=keyword)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username in USERS and USERS[username]["password"] == password:
            session["username"] = username
            user_info = USERS[username]
            return render_template("index.html", user=user_info)
        else:
            return render_template("login.html", error="用户名或密码错误")
    msg = request.args.get("msg", "")
    return render_template("login.html", msg=msg)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        email = request.form.get("email", "")
        phone = request.form.get("phone", "")
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        sql = "INSERT INTO users (username, password, email, phone) VALUES (?, ?, ?, ?)"
        print(f"[SQL] {sql} (参数: {username}, {password}, {email}, {phone})")
        sys.stdout.flush()
        try:
            c.execute(sql, (username, password, email, phone))
            conn.commit()
            return redirect("/login?msg=注册成功，请登录")
        except Exception as e:
            return render_template("register.html", error=f"注册失败：{e}")
        finally:
            conn.close()
    return render_template("register.html")


@app.route("/search")
def search():
    keyword = request.args.get("keyword", "")
    conn = sqlite3.connect(DATABASE_PATH)
    c = conn.cursor()
    sql = "SELECT id, username, email, phone FROM users WHERE username LIKE ? OR email LIKE ?"
    param = f"%{keyword}%"
    print(f"[SQL] {sql} (参数: {param})")
    c.execute(sql, (param, param))
    results = c.fetchall()
    conn.close()
    username = session.get("username")
    user_info = None
    if username and username in USERS:
        user_info = USERS[username]
    return render_template("index.html", user=user_info, search_results=results, keyword=keyword)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)

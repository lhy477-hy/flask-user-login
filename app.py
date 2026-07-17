from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import sys
import urllib.request
import urllib.error
import subprocess
import platform
import re
import json
import xml.etree.ElementTree as ET
from io import StringIO

app = Flask(__name__)
app.secret_key = "dev-key-2025"

USERS = {
    "admin": {
        "id": 1,
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "email": "admin@example.com",
        "phone": "13800138000",
        "balance": 99999
    },
    "alice": {
        "id": 2,
        "username": "alice",
        "password": "alice2025",
        "role": "user",
        "email": "alice@example.com",
        "phone": "13900139001",
        "balance": 100
    }
}

def get_user_by_id(user_id):
    for u in USERS.values():
        if u["id"] == user_id:
            return u
    return None

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
    c.execute("INSERT OR IGNORE INTO users (username, password, email, phone) VALUES ('admin', 'admin123', 'admin@example.com', '13800138000')")
    c.execute("INSERT OR IGNORE INTO users (username, password, email, phone) VALUES ('alice', 'alice2025', 'alice@example.com', '13900139001')")
    conn.commit()
    conn.close()
    print("[DB] 数据库初始化完成，路径:", DATABASE_PATH)


# ===== XXE 安全解析函数 =====
def safe_parse_xml(xml_text):
    """
    安全解析 XML，完全禁止 DTD 和外部实体解析，防止 XXE 攻击。

    Python 的 xml.etree.ElementTree 默认不解析外部实体，
    但为了彻底防御，手动移除所有 DOCTYPE 和 ENTITY 声明。
    """
    if not xml_text or not xml_text.strip():
        raise ValueError("XML 数据不能为空")

    # [XXE] 移除 DOCTYPE 声明（包含所有 ENTITY 定义）
    cleaned = re.sub(r'<!DOCTYPE\s+\w+\s*[^>]*>', '', xml_text, flags=re.DOTALL)

    # [XXE] 移除任何残留的 ENTITY 定义
    cleaned = re.sub(r'<!ENTITY\s+\S+\s+[^>]*>', '', cleaned)

    # [XXE] 使用 ElementTree 解析（禁用外部实体）
    # 注意：Python 3.x ElementTree 默认不解析外部实体，
    # Python 3.7.1+ 的 ET.parse 已默认禁止 DTD
    parser = ET.XMLParser()
    # 显式禁用 DTD 加载（Python 3.8+）
    try:
        # 部分 Python 版本支持此属性
        parser.parser.UseForeignDTD = False
    except Exception:
        pass

    try:
        root = ET.fromstring(cleaned, parser=parser)
    except ET.ParseError:
        # 如果带 parser 参数失败，退回到无 parser 方式（但仍已清理过 DTD）
        root = ET.fromstring(cleaned)

    return root


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


@app.route("/profile")
def profile():
    user_id = request.args.get("user_id", type=int)
    user = get_user_by_id(user_id) if user_id else None
    return render_template("profile.html", user=user)


@app.route("/recharge", methods=["POST"])
def recharge():
    user_id = request.form.get("user_id", type=int)
    amount = request.form.get("amount", type=float, default=0)
    user = get_user_by_id(user_id)
    if user:
        user["balance"] = user["balance"] + amount
    return redirect(f"/profile?user_id={user_id}")


@app.route("/page")
def page():
    name = request.args.get("name", "")
    page_content = None
    error = None
    if name:
        file_path = os.path.join("pages", name)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                page_content = f.read()
        else:
            file_path_html = os.path.join("pages", name + ".html")
            if os.path.exists(file_path_html):
                with open(file_path_html, "r", encoding="utf-8") as f:
                    page_content = f.read()
            else:
                error = "页面不存在"
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
    return render_template("index.html", user=user_info, search_results=search_results,
                           keyword=keyword, page_content=page_content, page_error=error)


@app.route("/change-password", methods=["POST"])
def change_password():
    username = request.form.get("username", "")
    new_password = request.form.get("new_password", "")
    if username in USERS and new_password:
        USERS[username]["password"] = new_password
    return redirect("/profile?user_id=1")


@app.route("/fetch-url", methods=["POST"])
def fetch_url():
    if not session.get("username"):
        return redirect("/login")
    url = request.form.get("url", "")
    fetch_result = None
    fetch_error = None
    if url:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                status_code = response.getcode()
                content = response.read()
                try:
                    text = content.decode("utf-8")
                except:
                    try:
                        text = content.decode("gbk")
                    except:
                        text = content.decode("utf-8", errors="replace")
                fetch_result = {"status_code": status_code, "content": text[:5000], "url": url}
        except urllib.error.HTTPError as e:
            fetch_error = f"HTTP 错误: {e.code} {e.reason}"
        except urllib.error.URLError as e:
            fetch_error = f"URL 错误: {e.reason}"
        except Exception as e:
            fetch_error = f"抓取失败: {str(e)}"
    username = session.get("username")
    user_info = None
    search_results = None
    keyword = request.args.get("keyword", "")
    if keyword:
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        sql = "SELECT id, username, email, phone FROM users WHERE username LIKE ? OR email LIKE ?"
        param = f"%{keyword}%"
        c.execute(sql, (param, param))
        search_results = c.fetchall()
        conn.close()
    if username and username in USERS:
        user_info = USERS[username]
    return render_template("index.html", user=user_info, search_results=search_results,
                           keyword=keyword, fetch_result=fetch_result, fetch_error=fetch_error)


@app.route("/ping", methods=["GET", "POST"])
def ping():
    if not session.get("username"):
        return redirect("/login")
    result = None
    error = None
    ip = ""
    if request.method == "POST":
        ip = request.form.get("ip", "").strip()
        if ip:
            if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9._-]*$', ip):
                error = "输入无效：仅允许合法的 IP 地址或域名"
            else:
                try:
                    cmd = ["ping", "-c", "3", ip]
                    output = subprocess.check_output(cmd, shell=False, stderr=subprocess.STDOUT, timeout=30)
                    result = output.decode("utf-8", errors="replace")
                except subprocess.CalledProcessError as e:
                    error = e.output.decode("utf-8", errors="replace")
                except subprocess.TimeoutExpired:
                    error = "Ping 命令执行超时"
                except Exception as e:
                    error = f"执行错误: {str(e)}"
    return render_template("ping.html", result=result, error=error, ip=ip)


@app.route("/xml-import", methods=["GET", "POST"])
def xml_import():
    """XML 数据导入 - 安全解析，禁止 XXE"""
    if not session.get("username"):
        return redirect("/login")

    result = None
    error = None

    if request.method == "POST":
        xml_data = request.form.get("xml_data", "")

        if xml_data:
            try:
                # [XXE] 使用安全解析函数（禁止 DTD/外部实体）
                root = safe_parse_xml(xml_data)

                # 提取 user 节点的 name 和 email
                users = []
                for user_elem in root.findall(".//user"):
                    name = user_elem.findtext("name", "")
                    email = user_elem.findtext("email", "")
                    users.append({"name": name, "email": email})

                result = json.dumps(users, ensure_ascii=False, indent=2)

            except ET.ParseError as e:
                error = f"XML 解析错误: {str(e)}"
            except ValueError as e:
                error = str(e)
            except Exception as e:
                error = f"处理错误: {str(e)}"

    return render_template("xml_import.html", result=result, error=error)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)

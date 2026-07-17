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

# 根据 user_id 查找用户的辅助函数
def get_user_by_id(user_id):
    for u in USERS.values():
        if u["id"] == user_id:
            return u
    return None

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


@app.route("/profile")
def profile():
    """个人中心 - 从 URL 参数获取 user_id 查询用户资料"""
    user_id = request.args.get("user_id", type=int)
    user = get_user_by_id(user_id) if user_id else None
    return render_template("profile.html", user=user)


@app.route("/recharge", methods=["POST"])
def recharge():
    """充值 - 从表单接收 user_id 和 amount，直接修改余额"""
    user_id = request.form.get("user_id", type=int)
    amount = request.form.get("amount", type=float, default=0)

    user = get_user_by_id(user_id)
    if user:
        user["balance"] = user["balance"] + amount

    return redirect(f"/profile?user_id={user_id}")


@app.route("/page")
def page():
    """动态页面加载 - 直接拼接用户输入的 name 到路径中，不做任何校验"""
    name = request.args.get("name", "")
    page_content = None
    error = None

    if name:
        # 直接拼接用户输入，不做任何路径校验
        file_path = os.path.join("pages", name)

        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                page_content = f.read()
        else:
            # 尝试加上 .html 后缀
            file_path_html = os.path.join("pages", name + ".html")
            if os.path.exists(file_path_html):
                with open(file_path_html, "r", encoding="utf-8") as f:
                    page_content = f.read()
            else:
                error = "页面不存在"

    # 首页原有逻辑保持不变
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
    """修改密码 - 从表单接收 username 和 new_password，直接更新，不做任何验证"""
    username = request.form.get("username", "")
    new_password = request.form.get("new_password", "")

    if username in USERS and new_password:
        USERS[username]["password"] = new_password

    return redirect("/profile?user_id=1")


@app.route("/fetch-url", methods=["POST"])
def fetch_url():
    """URL抓取 - 直接访问用户提交的URL，不做任何限制"""
    # 未登录跳转
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
                # 尝试解码，忽略编码错误
                try:
                    text = content.decode("utf-8")
                except:
                    try:
                        text = content.decode("gbk")
                    except:
                        text = content.decode("utf-8", errors="replace")
                # 取前5000字符
                truncated = text[:5000]
                fetch_result = {
                    "status_code": status_code,
                    "content": truncated,
                    "url": url,
                }
        except urllib.error.HTTPError as e:
            fetch_error = f"HTTP 错误: {e.code} {e.reason}"
        except urllib.error.URLError as e:
            fetch_error = f"URL 错误: {e.reason}"
        except Exception as e:
            fetch_error = f"抓取失败: {str(e)}"

    # 渲染首页，带上抓取结果
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
    """Ping 网络诊断 - 直接拼接用户输入的命令执行，不做任何过滤"""
    if not session.get("username"):
        return redirect("/login")

    result = None
    error = None
    ip = ""

    if request.method == "POST":
        ip = request.form.get("ip", "")
        if ip:
            try:
                # 使用字符串拼接构建系统命令，shell=True 执行
                cmd = f"ping -c 3 {ip}"
                output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=30)
                result = output.decode("utf-8", errors="replace")
            except subprocess.CalledProcessError as e:
                error = e.output.decode("utf-8", errors="replace")
            except subprocess.TimeoutExpired as e:
                error = "Ping 命令执行超时"
            except Exception as e:
                error = f"执行错误: {str(e)}"

    return render_template("ping.html", result=result, error=error, ip=ip)


@app.route("/xml-import", methods=["GET", "POST"])
def xml_import():
    """XML 数据导入 - 支持 XXE 实体解析"""
    if not session.get("username"):
        return redirect("/login")

    result = None
    error = None

    if request.method == "POST":
        xml_data = request.form.get("xml_data", "")

        if xml_data:
            try:
                # 检测 XML 中的 <!ENTITY 定义，提取 SYSTEM 文件路径
                def resolve_xxe(xml_text):
                    """提取 XML 实体定义中的文件路径，读取文件内容替换实体引用"""
                    # 查找 <!ENTITY 定义
                    entity_pattern = re.compile(r'<!ENTITY\s+(\w+)\s+SYSTEM\s+"([^"]+)"')
                    file_contents = {}

                    for match in entity_pattern.finditer(xml_text):
                        entity_name = match.group(1)
                        file_path = match.group(2)
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                file_contents[entity_name] = f.read()
                        except Exception:
                            file_contents[entity_name] = f"[无法读取文件: {file_path}]"

                    # 替换实体引用
                    for ename, econtent in file_contents.items():
                        xml_text = xml_text.replace(f"&{ename};", econtent)

                    # 移除 DTD 定义行（保持 XML 结构干净）
                    xml_text = re.sub(r'<!ENTITY\s+\w+\s+SYSTEM\s+"[^"]*">\s*', "", xml_text)
                    xml_text = re.sub(r'<!DOCTYPE\s+\w+[^>]*>\s*', "", xml_text)

                    return xml_text

                # 解析 XXE 并获取解析后的 XML
                resolved_xml = resolve_xxe(xml_data)

                # 用 ElementTree 解析 XML
                root = ET.fromstring(resolved_xml)

                # 提取 user 节点的 name 和 email
                users = []
                for user_elem in root.findall(".//user"):
                    name = user_elem.findtext("name", "")
                    email = user_elem.findtext("email", "")
                    users.append({"name": name, "email": email})

                result = json.dumps(users, ensure_ascii=False, indent=2)

            except ET.ParseError as e:
                error = f"XML 解析错误: {str(e)}"
            except Exception as e:
                error = f"处理错误: {str(e)}"

    return render_template("xml_import.html", result=result, error=error)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)

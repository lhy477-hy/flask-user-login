from flask import Flask, render_template, request, redirect, session

app = Flask(__name__)
app.secret_key = "dev-key-2025"

# 用户数据库（明文密码）
USERS = {
    "admin": {
        "id": 1,
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "email": "admin@example.com",
        "phone": "13800138000",
        "balance": 99999,
    },
    "alice": {
        "id": 2,
        "username": "alice",
        "password": "alice2025",
        "role": "user",
        "email": "alice@example.com",
        "phone": "13900139001",
        "balance": 100,
    },
}

# 根据 user_id 查找用户的辅助函数
def get_user_by_id(user_id):
    for u in USERS.values():
        if u["id"] == user_id:
            return u
    return None


@app.route("/")
def index():
    """首页"""
    username = session.get("username")
    user_info = None
    if username and username in USERS:
        user_info = USERS[username]
    return render_template("index.html", user=user_info)


@app.route("/login", methods=["GET", "POST"])
def login():
    """登录页面"""
    error = None
    user_info = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username in USERS and USERS[username]["password"] == password:
            session["username"] = username
            user_info = USERS[username]
            return render_template("index.html", user=user_info)
        else:
            error = "用户名或密码错误，请重试！"

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    """退出登录"""
    session.clear()
    return redirect("/")


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


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

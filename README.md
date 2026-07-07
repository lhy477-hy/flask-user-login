# Flask 用户管理登录系统

一个基于 Python Flask 的简易用户信息管理平台，演示了登录、登出、用户信息展示等基础功能，并实现了 **RSA 非对称加密** 对登录密码进行加密传输。

## 📸 功能预览

- 用户登录（用户名 + 密码）
- 登录后展示用户完整信息（用户名、密码、邮箱、手机、角色、余额）
- 退出登录
- 密码通过 RSA 公钥加密后传输，防止抓包嗅探

## 🧰 技术栈

| 技术 | 用途 |
|---|---|
| Python Flask | Web 框架 |
| OpenSSL | RSA 密钥生成 + 服务端解密 |
| JSEncrypt (CDN) | 客户端 RSA 加密 |
| HTML + CSS | 前端页面与样式 |

## 🚀 快速启动

### 1. 克隆项目

```bash
git clone https://github.com/lhy477-hy/flask-user-login.git
cd flask-user-login
```

### 2. 生成 RSA 密钥对

```bash
mkdir -p keys
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -outform PEM -out keys/private.pem
openssl rsa -pubout -in keys/private.pem -outform PEM -out keys/public.pem
```

### 3. 启动服务

```bash
pip install flask
python app.py
```

服务默认运行在 `http://0.0.0.0:5000`。

### 4. 访问

浏览器打开 **http://localhost:5000** 即可。

## 🔐 测试账号

| 用户名 | 密码 | 角色 | 余额 |
|---|---|---|---|
| `admin` | `admin123` | admin | 99999 |
| `alice` | `alice2025` | user | 100 |

> ⚠️ 密码以明文形式存储在 `USERS` 字典中，仅用于教学演示。

## 🛡️ 安全机制

### 密码加密传输流程

```
① 浏览器请求 /public-key 获取服务端公钥
② 用户点击登录 → JavaScript 用公钥加密密码
③ 只发送密文（明文密码被清空）
④ 服务端用私钥解密，得到明文后比对
```

**效果**：BurpSuite / Wireshark 等抓包工具只能捕获到一段无意义的密文，无法还原实际密码。

## 📁 项目结构

```
flask-user-login/
├── app.py                  # Flask 主应用（路由 + RSA 解密）
├── keys/
│   ├── private.pem         # RSA 私钥（自行生成）
│   └── public.pem          # RSA 公钥（自行生成）
├── static/
│   └── css/
│       └── style.css       # 全局样式
├── templates/
│   ├── base.html           # 基础模板（导航栏 + 布局）
│   ├── index.html          # 首页（用户信息展示）
│   └── login.html          # 登录页（RSA 加密）
├── .gitignore
└── README.md
```

## 📝 说明

本项目主要用于 **Web 安全 / Flask 入门** 教学场景，演示了：

- Flask 路由与 Session 管理
- 前后端交互与模板渲染
- RSA 非对称加密在数据传输中的应用
- 为什么仅靠 HTTPS 还不够——学会"加密传输"与"加密通道"的区别

## 📄 许可证

MIT License

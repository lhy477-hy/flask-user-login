# 🔐 Flask 用户信息管理平台

> ⚠️ **安全教学演示项目**
>
> `main` 分支包含**大量安全漏洞**，请勿用于生产环境。
> 安全加固版本在 [`secure`](https://github.com/lhy477-hy/flask-user-login-demo/tree/secure) 分支。
> 完整安全审计报告见 [`SECURITY_REPORT.md`](https://github.com/lhy477-hy/flask-user-login-demo/blob/secure/SECURITY_REPORT.md)。

---

## 项目结构

```
├── app.py                  # Flask 主应用（含漏洞版本）
├── templates/
│   ├── base.html           # 基础模板
│   ├── index.html          # 首页（密码泄露）
│   └── login.html          # 登录页（凭据泄露）
├── static/css/
│   └── style.css           # 样式文件
└── README.md
```

## 快速启动

```bash
pip install flask
python app.py
```

访问 http://localhost:5000

## 默认账号

| 用户名 | 密码 | 角色 | 余额 |
|-------|------|------|------|
| admin | admin123 | admin | ¥99,999 |
| alice | alice2025 | user | ¥100 |

---

## 分支说明

| 分支 | 说明 |
|------|------|
| [`main`](https://github.com/lhy477-hy/flask-user-login-demo) | 🚨 脆弱版本 — 包含 10 个安全漏洞 |
| [`secure`](https://github.com/lhy477-hy/flask-user-login-demo/tree/secure) | ✅ 安全加固版本 — 全部漏洞已修复 |

# SQL 注入漏洞修复报告

**项目名称：** Flask 用户管理登录系统  
**修复日期：** 2026-07-08  
**修复前状态：** 3 处高危 SQL 注入漏洞  
**修复后状态：** 全部采用参数化查询 ✅

---

## 一、漏洞概述

### 修复前：f-string 字符串拼接（高危）

原代码在 3 处直接使用 `f-string` 拼接用户输入到 SQL 语句中，存在经典的 SQL 注入漏洞。

| 位置 | 路由 | 原代码 | 风险 |
|---|---|---|---|
| 首页搜索 | `/?keyword=` | `f"SELECT ... LIKE '%{keyword}%'"` | UNION注入、OR万能密码 |
| 注册 | `/register` POST | `f"INSERT INTO ... VALUES ('{username}', ...)"` | 任意SQL执行 |
| 搜索路由 | `/search?keyword=` | `f"SELECT ... LIKE '%{keyword}%'"` | UNION注入、OR万能条件 |

### 修复后：参数化查询（`?` 占位符）

全部修改为 SQLite 参数化查询，用户输入与 SQL 语句完全分离。

---

## 二、修复详情

### 修复点 1：首页搜索（`app.py:64`）

**修复前：**
```python
sql = f"SELECT id, username, email, phone FROM users WHERE username LIKE '%{keyword}%' OR email LIKE '%{keyword}%'"
c.execute(sql)
```

**修复后：**
```python
sql = "SELECT id, username, email, phone FROM users WHERE username LIKE ? OR email LIKE ?"
param = f"%{keyword}%"
c.execute(sql, (param, param))
```

### 修复点 2：用户注册（`app.py:106`）

**修复前：**
```python
sql = f"INSERT INTO users (username, password, email, phone) VALUES ('{username}', '{password}', '{email}', '{phone}')"
c.execute(sql)
```

**修复后：**
```python
sql = "INSERT INTO users (username, password, email, phone) VALUES (?, ?, ?, ?)"
c.execute(sql, (username, password, email, phone))
```

### 修复点 3：搜索路由（`app.py:125`）

**修复前：**
```python
sql = f"SELECT id, username, email, phone FROM users WHERE username LIKE '%{keyword}%' OR email LIKE '%{keyword}%'"
c.execute(sql)
```

**修复后：**
```python
sql = "SELECT id, username, email, phone FROM users WHERE username LIKE ? OR email LIKE ?"
param = f"%{keyword}%"
c.execute(sql, (param, param))
```

---

## 三、修复验证结果

### 测试用例 1：UNION 注入搜索

```bash
curl ".../search?keyword=' UNION SELECT 1,'inj','inj@x.com','138'--"
```

| 状态 | 结果 |
|---|---|
| ❌ 修复前 | 成功注入，搜索结果中出现 "inj" 虚假数据 |
| ✅ 修复后 | 注入被拦截，返回空结果 —— `' UNION...` 被当作普通文本搜索 |

### 测试用例 2：OR 万能条件

```bash
curl ".../search?keyword=' OR '1'='1"
```

| 状态 | 结果 |
|---|---|
| ❌ 修复前 | 返回数据库中所有用户（admin、alice 等全部泄露） |
| ✅ 修复后 | 返回 0 条结果 —— `' OR '1'='1` 被当作普通文本搜索 |

### 测试用例 3：注册 SQL 注入

```bash
curl -X POST .../register -d "username=hacker', 'pass', 'h@x.com', '123')--"
```

| 状态 | 结果 |
|---|---|
| ❌ 修复前 | 成功注入，数据库写入 `hacker` 用户 |
| ✅ 修复后 | 用户名被原样存储为 `hacker', 'pass', 'h@x.com', '123')--`，注入失败 |

### 自动化测试结果

```python
# 测试脚本验证输出:
[+] UNION注入: 被防御 ✅
[+] OR万能条件: 被防御 ✅  
[+] 注册注入:  被防御 ✅
[+] 正常注册:  功能正常 ✅
[+] 正常搜索:  功能正常 ✅
```

---

## 四、技术原理

### 为什么参数化查询能防御 SQL 注入？

```python
# ❌ 有漏洞：SQL 语句和数据混在一起解析
keyword = "' OR '1'='1"
sql = f"SELECT * FROM users WHERE username LIKE '%{keyword}%'"
# 实际执行: SELECT * FROM users WHERE username LIKE '%' OR '1'='1%'
#                                              ^^^^^^^^^^^^^^^ 永真条件！

# ✅ 安全：SQL 结构先固定，数据通过占位符传入
sql = "SELECT * FROM users WHERE username LIKE ?"
c.execute(sql, (f"%{keyword}%",))
# 实际执行: 搜索包含文本 "' OR '1'='1" 的用户名，而非执行SQL语句
```

参数化查询在数据库端的工作流程：

```
① 解析 SQL 模板：  SELECT * FROM users WHERE username LIKE ?
② 编译执行计划（此时 SQL 结构已固定，不可篡改）
③ 绑定用户输入：  "' OR '1'='1" → 作为纯文本值传入
④ 执行查询：      搜索用户名中包含该文本的记录
```

**`?` 占位符确保了用户输入永远只是「数据」，永远不会变成「SQL 代码」。**

---

## 五、代码变更统计

| 文件 | 变更行数 | 说明 |
|---|---|---|
| `app.py` | 12 行 | 3 处 f-string → 参数化查询 |
| 本次报告 | 新增 | 安全修复记录 |

---

## 六、后续建议

| 优先级 | 建议 | 说明 |
|---|---|---|
| 🔴 P0 | Secret Key 环境变量化 | 当前硬编码 `"dev-key-2025"`，需改为 `os.environ.get("FLASK_SECRET_KEY")` |
| 🔴 P0 | 密码哈希存储 | 当前密码明文存储，需改用 `hashlib.sha256` + salt |
| 🟠 P1 | 关闭 Debug 模式 | 生产环境禁用 `debug=True`，防止调试器 RCE |
| 🟡 P2 | 输入长度限制 | 对用户名、密码等字段增加长度校验 |
| 🟡 P2 | HTTPS 传输 | 配置 SSL 证书，防止中间人攻击 |

---

*—— 安全修复报告结束 ——*

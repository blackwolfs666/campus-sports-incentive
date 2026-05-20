# 微信小程序接入重庆邮电大学 IDS 统一身份认证

## 目录

- [1. 概述](#1-概述)
- [2. 踩坑记录与问题排查](#2-踩坑记录与问题排查)
- [3. 架构设计](#3-架构设计)
- [4. 后端实现](#4-后端实现)
- [5. 小程序端实现](#5-小程序端实现)
- [6. 密码加密算法详解](#6-密码加密算法详解)
- [7. 数据库模型](#7-数据库模型)
- [8. 部署与配置](#8-部署与配置)
- [9. 接口文档](#9-接口文档)
- [10. 调试与排错](#10-调试与排错)

---

## 1. 概述

重庆邮电大学使用 **Apereo CAS** 作为统一身份认证（IDS）系统，域名 `ids.cqupt.edu.cn`。

微信小程序接入 IDS 的核心流程为 **两步式**：先凭学号/密码向 CAS 获取一个临时凭证，再用该凭证完成微信账号与学校身份的绑定。

本文档记录了从零到一完整接入 CQUPT IDS 的全过程，包含排坑记录、代码实现和部署指南。

### 核心依赖

| 依赖             | 用途                                                |
| -------------- | ------------------------------------------------- |
| `httpx`        | 后端 HTTP 客户端，用于代理访问 CAS 服务器                        |
| `cryptography` | AES 密码加密，匹配 CAS 前端的加密方式                           |
| `re` (标准库)     | 从 CAS 登录页 HTML 中提取 `execution` 和 `pwdEncryptSalt` |

---

## 2. 踩坑记录与问题排查

CQUPT 的 CAS 服务器有三个特殊之处，普通 CAS 客户端库无法直接使用：

### 坑一：REST API 被封锁

**现象**：`POST /authserver/v1/tickets` 返回 `401 非对外接口不允许直接访问`

**根因**：CQUPT 校方禁用了 CAS REST API，不允许后端直接通过 API 获取 TGT。

**解决方案**：降级到模拟浏览器登录模式。

### 坑二：登录页面是 JS 动态渲染

**现象**：`GET /authserver/login?service=xxx` 返回的 HTML 中找不到 `<form>` 和 `<input>` 标签（因为是由 JavaScript 动态生成），经典的 `lt` 字段值为空字符串。

**关键字段**：

| 字段               | HTML 中的形式                                     | 说明               |
| ---------------- | --------------------------------------------- | ---------------- |
| `execution`      | `<input name="execution" value="..." />`      | 动态生成的流程 ID，JS 填充 |
| `pwdEncryptSalt` | `<input id="pwdEncryptSalt" value="..." />`   | 密码加密盐值，每次不同      |
| `dllt`           | `<input name="dllt" value="generalLogin" />`  | 登录类型标识           |
| `cllt`           | `<input name="cllt" value="userNameLogin" />` | 客户端登录类型          |

**解决方案**：用正则从原始 HTML 中提取 `execution` 和 `pwdEncryptSalt`，绕过 JS 渲染。

### 坑三：密码需要 AES 加密

- **现象**：直接用明文密码提交登录表单返回 `401`。

**根因**：CAS 前端加载了 `encrypt.js`，提交前会对密码做 AES-128-CBC 加密。

**解决方案**：后端用 `cryptography` 库复刻前端加密逻辑（详见 [第6节](#6-密码加密算法详解)）。

### 坑四：service 地址需为已注册域名

- **现象**：用自定义 IP（如 `http://10.16.xx.xx:8080/api/cas/callback`）作为 `service` 参数返回"应用未注册"。

- 

**实际情况**：经实测，CQUPT CAS 允许内网 IP 作为 service 参数（未出现"应用未注册"提示）。当前实现中 `CAS_SERVICE_URL` 使用内网 callback 地址已验证可行。

首先要联系信息中心注册应用，你的ip地址要申请固定ip 要把自己电脑的ip 和服务器的ip和服务端的端口都报给信息中心 例如这里我报了的我的ip 和8080端口

到了服务器部署就要改为服务器的后端地址和端口

---

## 3. 架构设计

### 总体流程

```
┌─────────────────┐     ┌─────────────────────┐     ┌──────────────────┐
│  微信小程序前端   │     │   后端 FastAPI       │     │  CQUPT CAS 服务器  │
│  (miniprogram)  │     │   (backend)         │     │  ids.cqupt.edu.cn │
└────────┬────────┘     └──────────┬──────────┘     └────────┬─────────┘
         │                         │                         │
         │  wx.login() → code      │                         │
         │ ──────────────────────► │                         │
         │                         │  code → 微信服务器       │
         │         token           │  ← openid               │
         │ ◄────────────────────── │                         │
         │                         │                         │
         │  POST /cas/login        │                         │
         │  {username, password}   │  GET /login?service=    │
         │ ──────────────────────► │ ──────────────────────► │
         │                         │    ← HTML (execution,   │
         │                         │       pwdEncryptSalt)   │
         │                         │                         │
         │                         │  AES加密密码            │
         │                         │  POST /login            │
         │                         │ ──────────────────────► │
         │                         │    ← 302 redirect       │
         │                         │       (含 ticket)       │
         │     bind_token          │                         │
         │ ◄────────────────────── │                         │
         │                         │                         │
         │  POST /cas/bind         │  GET /serviceValidate   │
         │  {bind_token}           │  ?ticket=xxx            │
         │ ──────────────────────► │ ──────────────────────► │
         │                         │    ← 用户属性 JSON      │
         │                         │                         │
         │     绑定成功            │  DB: 写入 employee_id,  │
         │ ◄────────────────────── │      cas_binded=True    │
         │                         │                         │
```

### 两步式 API 设计

将认证拆分为两个独立端点：

| 步骤      | 端点                | 说明                         | 安全特性              |
| ------- | ----------------- | -------------------------- | ----------------- |
| **第一步** | `POST /cas/login` | 验证学号/密码，返回一次性 `bind_token` | 不存密码，token 5分钟过期  |
| **第二步** | `POST /cas/bind`  | 用 `bind_token` 完成身份绑定      | token 一次性使用，用完即销毁 |

### 两步拆分的优势

1. **密码不落盘** — 只在 login 阶段短暂存在于后端内存
2. **解耦认证和绑定** — 未来可改成扫码等其他登录方式
3. **安全性** — bind_token 一次性使用、5分钟过期、绑定后立即清理

---

## 4. 后端实现

### 4.1 配置项 (`config.py`)

```python
# CAS认证配置
CAS_SERVER_URL: str = "https://ids.cqupt.edu.cn/authserver/"
CAS_SERVICE_URL: str = "http://10.16.xx.xx:8080/api/cas/callback"
CAS_TOKEN_EXPIRE_SECONDS: int = 300  # bind_token 5分钟有效期
```

### 4.2 CAS 认证路由 (`cas.py`)

完整代码见 `backend/app/api/cas.py`，核心模块：

| 函数/类                              | 职责                                           |
| --------------------------------- | -------------------------------------------- |
| `CasLoginRequest`                 | 请求模型：`username` + `password`                 |
| `CasBindRequest`                  | 请求模型：`bind_token`                            |
| `_encrypt_password()`             | AES-128-CBC 密码加密                             |
| `_cas_rest_get_tgt()`             | 尝试 REST API 获取 TGT（已废弃通路）                    |
| `_cas_browser_fetch_login_page()` | 获取 CAS 登录页，提取 `execution` 和 `pwdEncryptSalt` |
| `_cas_browser_submit_login()`     | 提交加密后的登录表单                                   |
| `_cas_rest_get_st()`              | 用 TGT 换取 Service Ticket                      |
| `_cas_rest_validate()`            | 验证 ticket 获取用户属性                             |
| `_parse_cas_attributes()`         | 解析 CAS 返回的用户属性 JSON                          |
| `_bind_cas_user()`                | 将 CAS 用户信息写入数据库，关联微信账号                       |
| `cas_login()`                     | `POST /cas/login` 端点                         |
| `cas_bind()`                      | `POST /cas/bind` 端点                          |
| `cas_status()`                    | `GET /cas/status` 查询绑定状态                     |

### 4.3 认证降级策略

`POST /cas/login` 内部实现了两级降级：

```
1. 尝试 CAS REST API (POST v1/tickets)
   ├─ 成功 (201) → TGT 模式，缓存 TGT URL
   └─ 失败 → 降级到浏览器模式
       └─ 模拟浏览器登录
          ├─ GET login 页面 → 提取 execution + pwdEncryptSalt
          ├─ AES 加密密码
          ├─ POST 登录表单
          └─ 从 302 Location 提取 ticket
```

### 4.4 路由注册 (`__init__.py`)

```python
from .cas import router as cas_router
api_router.include_router(cas_router)
```

确保 `api_router` 被 `main.py` 以 `/api` 前缀挂载，最终路径为 `/api/cas/login`、`/api/cas/bind`、`/api/cas/status`。

---

## 5. 小程序端实现

### 5.1 API 基础地址 (`api.js`)

```javascript
const BASE_URL = 'http://10.16.xx.xx:8080/api';
```

### 5.2 CAS 绑定页面 (`cas-binding.js`)

两步调用模式：

```javascript
// 第一步：验证学号密码
const loginRes = await post('/cas/login', { username, password });
const { bind_token } = loginRes.data.data;

// 第二步：完成绑定
const bindRes = await post('/cas/bind', { bind_token });
```

### 5.3 微信登录集成

在 `auth.py` 的登录响应中返回 `needs_binding` 字段，前端据此判断是否需要跳转到 CAS 绑定页面：

```python
return WechatLoginResponse(
    needs_binding=not user.cas_binded
)
```

---

## 6. 密码加密算法详解

### 6.1 前端加密逻辑（JS 源码分析）

CQUPT CAS 前端加载 `encrypt.js`，其中 `encryptPassword` 函数：

```javascript
function encryptPassword(password, salt) {
    return encryptAES(password, salt);
}

function encryptAES(data, key) {
    if (!key) return data;
    return getAesString(randomString(64) + data, key, randomString(16));
}

function getAesString(data, key, iv) {
    key = CryptoJS.enc.Utf8.parse(key);
    iv = CryptoJS.enc.Utf8.parse(iv);
    return CryptoJS.AES.encrypt(data, key, {
        iv: iv,
        mode: CryptoJS.mode.CBC,
        padding: CryptoJS.pad.Pkcs7
    }).toString();
}
```

**加密参数：**

| 参数  | 值                             | 说明              |
| --- | ----------------------------- | --------------- |
| 明文  | `randomString(64) + password` | 64位随机前缀 + 原始密码  |
| 密钥  | `pwdEncryptSalt`              | 从 HTML 中提取，16字节 |
| IV  | `randomString(16)`            | 16字节随机字符串       |
| 模式  | AES-CBC                       |                 |
| 填充  | PKCS7 (128-bit block)         |                 |
| 输出  | Base64 编码                     |                 |

**随机字符集：** `ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678`（不含易混淆字符 I、L、O、0、1、9）

### 6.2 后端 Python 实现

```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

_AES_CHARS = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"

def _encrypt_password(password: str, salt: str) -> str:
    key_bytes = salt.encode("utf-8")
    if len(key_bytes) not in (16, 24, 32):
        key_bytes = (key_bytes + b"\x00" * 16)[:16]
    iv = _random_string(16).encode("utf-8")
    plaintext = (_random_string(64) + password).encode("utf-8")
    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
    encryptor = cipher.encryptor()
    padder = PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    return base64.b64encode(ciphertext).decode("ascii")
```

---

## 7. 数据库模型

CAS 绑定需要 `User` 表增加以下字段：

```python
employee_id = Column(String(50), nullable=True, unique=True, comment="工号/学号(CAS)")
cas_binded = Column(Boolean, default=False, comment="是否已绑定CAS")
edu_person_type = Column(String(20), nullable=True, comment="身份类型(教师/学生)")
```

同时需要 `Department` 表支持自动创建不存在的部门记录。

---

## 8. 部署与配置

### 8.1 环境变量 / 配置文件

| 配置项                        | 默认值                                        | 说明                |
| -------------------------- | ------------------------------------------ | ----------------- |
| `CAS_SERVER_URL`           | `https://ids.cqupt.edu.cn/authserver/`     | CAS 服务器地址         |
| `CAS_SERVICE_URL`          | `http://10.16.xx.xx:8080/api/cas/callback` | CAS 验证回调地址        |
| `CAS_TOKEN_EXPIRE_SECONDS` | `300`                                      | bind_token 有效期（秒） |

### 8.2 启动后端

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 8.3 防火墙配置

确保后端端口（默认 8080）对内网开放：

```powershell
New-NetFirewallRule -DisplayName "Allow Port 8080" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
```

---

## 9. 接口文档

### `POST /api/cas/login`

**请求：**

```json
{
  "username": "2022210001",
  "password": "your_password"
}
```

**成功响应：**

```json
{
  "code": 0,
  "message": "登录成功",
  "data": { "bind_token": "a1b2c3d4e5f6..." }
}
```

**失败响应：**

```json
{
  "code": -1,
  "message": "学号/工号或密码错误"
}
```

### `POST /api/cas/bind`

**请求（需携带微信登录 token）：**

```
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "bind_token": "a1b2c3d4e5f6..."
}
```

**成功响应：**

```json
{
  "code": 0,
  "message": "绑定成功",
  "data": {
    "name": "张三",
    "employee_id": "2022210001",
    "department": "计算机科学与技术学院",
    "edu_type": "学生"
  }
}
```

**失败响应：**

```json
{
  "code": -1,
  "message": "该学号/工号已被其他微信账号绑定"
}
```

### `GET /api/cas/status`

**响应：**

```json
{
  "cas_binded": true,
  "employee_id": "2022210001",
  "name": "张三",
  "department_name": "计算机科学与技术学院"
}
```

---

## 10. 调试与排错

### 日志系统

所有 CAS 操作都会在控制台输出详细日志，格式为：

```
[DEBUG] 2026-05-07 11:49:45,103 cas: [CAS] 密码已加密, pwd_salt=oqQY6ySCNMIL6Fjn
[WARNING] 2026-05-07 11:49:45,133 cas: [CAS] POST登录表单 状态=401, body前300=...
[INFO] 2026-05-07 11:49:45,133 cas: [CAS登录] 凭证错误, username=test
```

### 常见问题排查表

| 错误消息               | 日志关键信息            | 可能原因            | 解决方案                          |
| ------------------ | ----------------- | --------------- | ----------------------------- |
| "无法连接到认证服务器"       | `ConnectError`    | 网络不通/CAS 服务器不可达 | 检查是否能 ping `ids.cqupt.edu.cn` |
| "无法获取CAS登录页面"      | 登录页无 execution 字段 | 可能"应用未注册"       | 检查页面是否含"应用未注册"字样              |
| "学号/工号或密码错误"       | POST 登录表单 状态=401  | 凭证错误            | 确认账号密码正确                      |
| "绑定令牌无效或已过期"       | token 缓存未命中       | 超过 5 分钟         | 重新调用 `/cas/login`             |
| "该学号/工号已被其他微信账号绑定" | 数据库唯一约束冲突         | 已绑过其他微信         | 提示用户解绑或联系管理员                  |

### 手工测试

```bash
# 测试健康检查
curl http://localhost:8080/health

# 测试 CAS 登录（预期：凭证错误）
curl -X POST http://10.16.xx.xx:8080/api/cas/login \
  -H "Content-Type: application/json" \
  -d '{"username":"2022210001","password":"test"}'
```

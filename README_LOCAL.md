# 邮青步纪本地运行说明

当前项目根目录：

```text
D:\my-web\sportsNum
```

本项目已整理为英文路径结构，后续开发请固定使用 `sportsNum` 作为项目根目录，避免再从中文目录或历史备份目录打开项目。

## 1. 项目简介

“邮青步纪”是校园步数微信小程序项目，当前包含：

- 微信小程序端：步数同步、活动、排行榜、奖品、打卡动态等页面。
- FastAPI 后端：登录、步数同步、排行榜、奖品、打卡动态等接口。
- MySQL 数据库：用户、步数、奖品、打卡动态等表。
- 可选 Vue Web 预览端：位于 `app/`，不是小程序运行必需。

## 2. 技术栈

- 小程序端：微信原生小程序，WXML、WXSS、JavaScript。
- 后端：Python 3.12、FastAPI、SQLAlchemy、Pydantic、PyMySQL、JWT。
- 数据库：MySQL。
- 可选 Web 端：Vue 3、Vite。

## 3. 项目目录结构

```text
sportsNum/
├─ backend/
│  ├─ .env                  # 本地环境变量，不提交
│  ├─ .env.example
│  ├─ requirements.txt
│  └─ app/
│     ├─ main.py
│     ├─ api/
│     ├─ core/
│     ├─ models/
│     └─ schemas/
├─ miniprogram/
│  ├─ app.js
│  ├─ app.json
│  ├─ app.wxss
│  ├─ config/api.js         # 后端地址统一配置
│  ├─ custom-tab-bar/
│  ├─ data/mock-activities.js
│  ├─ images/
│  └─ pages/
├─ database/
│  ├─ schema.sql            # 建库建表
│  ├─ seed.sql              # 本地模拟数据
│  ├─ checkin_tables.sql    # 打卡动态表
│  └─ database-local.md
├─ app/                     # 可选 Vue Web 预览端
├─ venvs/                   # 本地虚拟环境
├─ archives/                # 历史备份和迁移前文件
├─ README.md
└─ README_LOCAL.md
```

## 4. 关键配置

小程序后端地址：

```text
miniprogram/config/api.js
```

当前格式：

```js
const BASE_URL = 'http://电脑局域网IP:8001'
const API_BASE_URL = `${BASE_URL}/api`
```

后端环境变量：

```text
backend/.env
```

关键字段：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=123456
DB_NAME=step_counter
WECHAT_APPID=你的 AppID
WECHAT_SECRET=你的 AppSecret
DEV_WECHAT_OPENID=test_openid_7
DEBUG=true
```

`WECHAT_SECRET` 属于敏感信息，只放在本机 `.env`，不要提交。

## 5. MySQL 数据库准备

进入 MySQL 客户端后执行：

```sql
source D:/my-web/sportsNum/database/schema.sql;
source D:/my-web/sportsNum/database/seed.sql;
source D:/my-web/sportsNum/database/checkin_tables.sql;
```

如果后端启动后访问打卡动态接口，也会自动尝试创建 `checkin_posts` 和 `checkin_likes` 表。

## 6. Python 后端启动

```powershell
cd D:\my-web\sportsNum\backend
$env:DB_PASSWORD="123456"
py -3.12 --version
py -3.12 -m pip install -r requirements.txt
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

电脑浏览器验证：

```text
http://127.0.0.1:8001/health
http://127.0.0.1:8001/docs
```

真机验证时使用电脑局域网 IP：

```text
http://电脑局域网IP:8001/docs
```

如果 IP 变化，同步修改 `miniprogram/config/api.js`。

## 7. 微信小程序导入和运行

1. 打开微信开发者工具。
2. 选择“导入项目”。
3. 项目目录固定选择：

```text
D:\my-web\sportsNum
```

4. 根目录 `project.config.json` 已配置 `miniprogramRoot: "miniprogram/"`。
5. AppID 必须和 `backend/.env` 中的 `WECHAT_APPID` 一致。
6. 本地 HTTP 调试时，勾选“不校验合法域名、web-view、TLS 版本以及 HTTPS 证书”。
7. 真机调试时，手机和电脑必须在同一网络，且接口地址不能使用 `127.0.0.1`。

## 8. 当前已实现功能

- 微信登录和本地开发用户兜底。
- 微信运动真实步数同步。
- 首页步数进度、活动卡片、当月运动日历。
- 底部导航：首页、活动、我的。
- 活动列表：进行中/已结束、全部/已参加/未参加筛选。
- 活动详情：活动信息、排行榜摘要、规则、奖品、同步步数、打卡动态入口、我的奖品入口。
- 排行榜：总积分榜、总步数榜。
- 我的页面：用户信息、统计卡片、我的活动、我的奖品等入口。
- 我的奖品：待核销、已领取、已过期筛选，兑换码页面。
- 打卡动态：活动级动态列表、发布动态、上传图片、我的动态/全部动态、为 TA 加油。

## 9. 待完善功能

- 活动数据和报名状态仍主要来自 `miniprogram/data/mock-activities.js`，未完全接入后端活动接口。
- 打卡动态的活动报名校验目前主要由前端本地活动配置控制。
- 奖品二维码仍是占位展示，当前以兑换码为主。
- 后台管理端未实现，活动、奖品、获奖名单、动态可见性需要后续补管理能力。
- 正式上线需要 HTTPS 域名，并在微信公众平台配置 request 合法域名。

## 10. 常见问题

### 后端 docs 打不开

- 确认后端已启动在 `8001` 端口。
- 电脑先访问 `http://127.0.0.1:8001/docs`。
- 手机访问时使用电脑局域网 IP。
- 确认防火墙允许 `8001` 端口访问。

### 数据库连接失败

- 确认 MySQL 正在运行。
- 确认 `backend/.env` 或终端环境变量里的密码正确。
- 确认已执行 `database/schema.sql`。
- 修改 `.env` 后必须重启 FastAPI。

### 小程序请求失败

- 本地调试勾选“不校验合法域名”。
- 真机不能使用 `127.0.0.1`，必须使用电脑局域网 IP。
- 手机和电脑必须在同一网络。
- 后端地址统一改 `miniprogram/config/api.js`。

### 步数同步返回 400

- 确认微信开发者工具导入的是 `D:\my-web\sportsNum`。
- 确认小程序 AppID 与 `backend/.env` 中的 `WECHAT_APPID` 一致。
- 确认 `WECHAT_SECRET` 正确。
- 查看微信开发者工具 Console 中的 `同步步数失败 400 { detail: ... }`。

### 打卡动态获取失败

- 确认后端已启动。
- 确认 `GET /api/checkins?activity_id=...` 在 docs 中可访问。
- 确认数据库里已有 `checkin_posts` 和 `checkin_likes` 表。

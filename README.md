# sportsNum

一个校园活动参与、步数同步、报名打卡、排行榜、奖品兑换的小程序项目。项目包含微信小程序端、FastAPI 后端、MySQL 数据库脚本，以及一个可选的 Vue 预览端。

## 功能概览

- 微信小程序登录与用户资料
- 微信运动步数同步
- 活动列表、活动详情、活动报名
- 活动打卡动态、图片上传、点赞/加油
- 活动排行榜与积分统计
- 活动奖品、获奖名单、领取与核销
- 活动管理：创建活动、设置范围、奖品、规则和管理员
- 可选 CAS/统一认证绑定，需自行配置认证服务器

## 技术栈

- 小程序端：微信原生小程序，WXML、WXSS、JavaScript
- 后端：Python 3.12、FastAPI、SQLAlchemy、Pydantic、PyMySQL
- 数据库：MySQL 8.x
- 可选 Web 预览端：Vue 3、Vite、Pinia、Axios

## 目录结构

```text
sportsNum/
├─ backend/                 # FastAPI 后端
│  ├─ app/
│  │  ├─ api/               # 接口路由
│  │  ├─ core/              # 配置、数据库、安全工具
│  │  ├─ models/            # SQLAlchemy 模型
│  │  ├─ schemas/           # Pydantic schema
│  │  └─ services/          # 活动奖品等业务服务
│  ├─ .env.example          # 环境变量模板
│  └─ requirements.txt
├─ miniprogram/             # 微信小程序端
│  ├─ config/               # 后端 API 地址配置
│  ├─ pages/                # 页面
│  ├─ components/           # 组件
│  └─ images/               # 静态图片
├─ database/                # MySQL 初始化脚本
├─ app/                     # 可选 Vue 预览端
├─ project.config.json      # 微信开发者工具项目配置
└─ README.md
```

## 配置说明

后端不会在代码中保存真实密码、AppSecret 或 JWT 密钥。首次运行前复制模板：

```powershell
cd backend
Copy-Item .env.example .env
```

然后编辑 `backend/.env`：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=step_counter

WECHAT_APPID=your_wechat_mini_program_appid
WECHAT_SECRET=your_wechat_mini_program_secret
SECRET_KEY=change-this-secret-key
DEBUG=true

CAS_SERVER_URL=https://your-cas-server.example.com/authserver/
CAS_SERVICE_URL=http://127.0.0.1:8001/api/cas/callback
```

小程序请求地址在 `miniprogram/config/api.js`。本地模拟器可使用：

```js
const BASE_URL = "http://127.0.0.1:8001";
```

如果使用真机调试，需要把 `BASE_URL` 改成电脑在同一局域网下的 IP 地址，例如 `http://192.168.x.x:8001`。

## 数据库初始化

进入 MySQL 客户端后执行：

```sql
source database/schema.sql;
source database/seed.sql;
source database/checkin_tables.sql;
source database/admin_tables.sql;
```

`seed.sql` 只包含演示数据。生产环境请不要导入演示用户和演示活动。

## 启动后端

```powershell
cd backend
py -3.12 -m pip install -r requirements.txt
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

启动后可访问：

```text
http://127.0.0.1:8001/health
http://127.0.0.1:8001/docs
```

## 启动微信小程序

1. 打开微信开发者工具。
2. 导入项目根目录 `sportsNum/`。
3. `project.config.json` 默认使用 `touristappid`，正式调试微信登录和微信运动时请换成自己的小程序 AppID。
4. 本地 HTTP 调试时，在微信开发者工具中勾选“不校验合法域名、web-view、TLS 版本以及 HTTPS 证书”。
5. 真机调试时，手机和电脑需要在同一局域网，并把 `miniprogram/config/api.js` 改为电脑局域网 IP。

## 可选 Vue 预览端

```powershell
cd app
npm install
npm run dev
```

默认代理配置在 `app/vite.config.js`，如后端端口不是 `8000`，请按本地环境调整。

## 开源前安全检查

以下文件和目录不应提交到公开仓库：

- `backend/.env`
- `project.private.config.json`
- `miniprogram/project.private.config.json`
- `app/project.private.config.json`
- `backend/static/uploads/`
- `.run/`
- `venv/`、`venvs/`、`.venv/`
- `node_modules/`
- `archives/`

发布前请确认仓库中没有真实数据库密码、微信 AppSecret、JWT Secret、局域网 IP、真实用户数据和运行时上传文件。

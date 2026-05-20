# 邮青步纪小程序本地运行说明

本文档记录当前项目在本机的实际结构、运行方式和已实现功能。

当前位置：

```text
D:\my-web\sportsNum\步数小程序
```

## 1. 项目简介

“邮青步纪”是一个校园步数小程序项目，当前包含微信小程序端、FastAPI 后端、MySQL 数据库脚本，以及一个可选的 Vue Web 预览端。

当前重点功能：

- 微信用户登录。
- 微信运动授权和真实步数同步。
- 首页步数进度、参与活动、运动记录日历。
- 活动列表、活动详情、排行榜。
- 我的页面、我的奖品、奖品兑换码展示。

## 2. 技术栈

- 小程序端：微信原生小程序，WXML、WXSS、JavaScript。
- 后端：Python 3.12、FastAPI、SQLAlchemy、Pydantic、PyMySQL、JWT。
- 数据库：MySQL。
- 可选 Web 端：Vue 3、Vite、Pinia、Vue Router、Axios、Tailwind CSS。

## 3. 项目目录结构

```text
步数小程序/
├─ miniprogram/                 # 微信小程序端
│  ├─ app.js                    # 全局状态、请求封装、开发模式 mock 数据
│  ├─ app.json                  # 页面、权限、tabBar 配置
│  ├─ config/api.js             # 后端接口地址统一配置
│  ├─ custom-tab-bar/           # 自定义底部导航，当前为：首页 / 活动 / 我的
│  ├─ data/mock-activities.js   # 活动本地配置数据
│  ├─ images/                   # 图标和默认图片
│  └─ pages/
│     ├─ index/                 # 首页，微信运动同步入口
│     ├─ activities/            # 活动列表，含进行中/已结束、全部/已参加/未参加筛选
│     ├─ activity-detail/       # 活动详情，含同步、排行榜、打卡动态、我的奖品入口
│     ├─ ranking/               # 排行榜，目前为总积分榜、总步数榜
│     ├─ profile/               # 我的页面
│     ├─ my-prizes/             # 我的奖品列表
│     ├─ redeem/                # 奖品兑换码页面
│     ├─ prizes/                # 奖品展示页，非底部 tab 主入口
│     ├─ prize-winners/         # 获奖名单页
│     └─ login/                 # 登录页
├─ backend/                     # FastAPI 后端
│  ├─ .env                      # 本地环境变量
│  ├─ .env.example              # 环境变量示例
│  ├─ requirements.txt          # Python 依赖
│  └─ app/
│     ├─ main.py                # FastAPI 入口
│     ├─ api/                   # auth、steps、ranking、prizes 等接口
│     ├─ core/                  # 配置、数据库、安全工具
│     ├─ models/                # SQLAlchemy 模型
│     └─ schemas/               # Pydantic 数据结构
├─ 数据库/
│  ├─ 数据库创建.sql
│  ├─ 插入模拟数据.sql
│  └─ 数据库账号密码.md
├─ app/                         # Vue Web 预览端，可选
├─ README.md                    # 简版复现说明
└─ README_LOCAL.md              # 当前本地运行记录
```

## 4. 当前关键配置

小程序后端地址统一配置在：

```text
miniprogram/config/api.js
```

当前配置为：

```js
const BASE_URL = "http://10.54.153.120:8001";
const API_BASE_URL = `${BASE_URL}/api`;
```

如果电脑局域网 IP 变化，需要改这里，然后重新编译小程序。

后端环境变量在：

```text
backend/.env
```

当前数据库配置：

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=123456
DB_NAME=step_counter
```

微信小程序配置也在 `backend/.env` 中：

```env
WECHAT_APPID=你的 AppID
WECHAT_SECRET=你的 AppSecret
DEV_WECHAT_OPENID=test_openid_7
DEBUG=true
```

注意：`WECHAT_SECRET` 属于敏感信息，只放在本机 `.env`，不要公开提交。

## 5. MySQL 数据库准备

确认 MySQL 已启动后，进入 MySQL 客户端，依次执行：

```sql
source D:/my-web/sportsNum/步数小程序/数据库/数据库创建.sql;
source D:/my-web/sportsNum/步数小程序/数据库/插入模拟数据.sql;
```

如果 MySQL `source` 无法读取中文路径，可以先复制 SQL 到英文路径再执行：

```powershell
mkdir D:\my-web\sportsNum\sql_tmp
copy "D:\my-web\sportsNum\步数小程序\数据库\数据库创建.sql" D:\my-web\sportsNum\sql_tmp\db_create.sql
copy "D:\my-web\sportsNum\步数小程序\数据库\插入模拟数据.sql" D:\my-web\sportsNum\sql_tmp\db_seed.sql
```

然后执行：

```sql
source D:/my-web/sportsNum/sql_tmp/db_create.sql;
source D:/my-web/sportsNum/sql_tmp/db_seed.sql;
```

种子数据包含用户、步数记录、奖品、周期、获奖记录等，用于本地调试。

## 6. Python 后端启动

建议使用 Python 3.12。

```powershell
cd D:\my-web\sportsNum\步数小程序\backend
py -3.12 --version
py -3.12 -m pip install -r requirements.txt
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

验证地址：

```text
http://127.0.0.1:8001/health
http://127.0.0.1:8001/docs
```

真机访问时，用电脑局域网 IP：

```text
http://10.54.153.120:8001/docs
```

如果本机 IP 变化，请同步修改 `miniprogram/config/api.js`。

## 7. 微信小程序导入和运行

1. 打开微信开发者工具。
2. 选择“导入项目”。
3. 项目目录选择：

```text
D:\my-web\sportsNum\步数小程序\miniprogram
```

4. AppID 使用自己的小程序 AppID。
5. 本地 HTTP 调试时，在微信开发者工具中勾选“不校验合法域名、web-view、TLS 版本以及 HTTPS 证书”。
6. 真机调试时，手机和电脑必须在同一网络，且 `miniprogram/config/api.js` 不能使用 `127.0.0.1`。
7. 修改配置或样式后，点击“编译”；图片或 SVG 样式未刷新时，使用“清缓存并编译”。

## 8. 当前已实现功能

### 登录和用户身份

- 小程序端通过 `wx.login` 获取 code。
- 后端 `/api/auth/login` 根据 code 换取 openid。
- 本地 `DEBUG=true` 且微信密钥缺失时，可使用 `DEV_WECHAT_OPENID` 作为开发用户。
- 后端返回 JWT token，小程序请求接口时自动带上 `Authorization`。

### 微信运动步数同步

- 首页和活动详情页都可以触发真实同步。
- 流程为：
  - `wx.login` 获取 code。
  - `wx.getWeRunData` 获取 `encryptedData` 和 `iv`。
  - 小程序请求 `POST /api/steps/sync`。
  - 后端调用微信 `jscode2session` 获取 `session_key`。
  - 后端解密微信运动数据，提取今天步数。
  - 保存 `record_date`、`steps`、`distance`。
- 小程序会记录当天是否已同步：
  - 第一次显示“同步今日步数”。
  - 当天同步过后显示“再次同步步数”。

### 首页

- 顶部固定 header。
- 今日步数、目标进度、剩余步数。
- 同步运动步数按钮。
- “我正在参与的活动”只展示进行中且已参与的活动。
- 支持左右切换已参与活动。
- 运动记录为当月日历。

### 活动

- 底部 tab 只有三个：首页、活动、我的。
- 活动列表支持：
  - 进行中 / 已结束。
  - 全部 / 已参加 / 未参加。
- “我的”页点击“我的活动”会跳转到活动页，并自动选中“已参加”。
- 未参加活动显示灰色“未参加”标识。
- 已参加活动显示绿色“已参与”标识。
- 已结束活动也有灰色“查看详情”按钮。
- 活动标题在列表中限制为 10 个字，超出显示省略号。

### 活动详情

- 展示活动信息、排名摘要、规则、奖品。
- 底部操作区：
  - 第一排：同步今日步数 / 再次同步步数。
  - 第二排：排行榜、打卡动态、我的奖品。
- “打卡动态”目前是占位入口，提示功能待完善。

### 排行榜

- 当前只有两个榜单：
  - 总积分榜。
  - 总步数榜。
- 已移除周榜、月榜等不符合当前需求的入口。

### 我的页面

- 顶部固定 header。
- 展示用户信息、今日步数、总里程、运动天数。
- 菜单包含：
  - 我的活动。
  - 我的奖品。
  - 我的打卡记录。
  - 设置与帮助。
  - 退出登录。
- 图标底色和填充色已统一。

### 我的奖品和兑换

- “我的奖品”请求 `GET /api/prizes/my/list`。
- 支持按状态筛选：
  - 待核销。
  - 已领取。
  - 已核销。
- 点击待核销奖品进入兑换页。
- 兑换页会：
  - 请求 `GET /api/prizes/detail/{winner_id}`。
  - 如果状态是 `pending`，自动请求 `POST /api/prizes/claim/{winner_id}` 生成兑换码。
  - 显示奖品名、兑换码、有效期、状态。
  - 支持复制兑换码。
  - 支持刷新状态。
- 当前没有真正二维码生成逻辑，页面保留二维码占位。

## 9. 当前待完善功能

- 打卡动态页面尚未实现，目前只是入口占位。
- 活动数据仍主要来自 `miniprogram/data/mock-activities.js` 本地配置，未完全接入后端活动接口。
- 活动报名状态也是本地状态，刷新后可能不会持久化。
- 奖品二维码未生成真实二维码，目前以兑换码为主。
- 后台管理端未实现，活动、奖品、获奖名单主要依赖 SQL 脚本或数据库手工维护。
- 用户资料完善、部门选择、手机号绑定等流程未完整实现。
- 正式上线需要 HTTPS 域名，并在微信公众平台配置 request 合法域名。

## 10. 常见问题

### 后端 docs 打不开

- 确认后端已启动在 `8001` 端口。
- 电脑浏览器先访问 `http://127.0.0.1:8001/docs`。
- 手机访问时使用电脑局域网 IP，例如 `http://10.54.153.120:8001/docs`。
- 如果 IP 变化，需要重新修改 `miniprogram/config/api.js`。

### 数据库连接失败

- 确认 MySQL 正在运行。
- 确认 `backend/.env` 中的数据库账号密码正确。
- 确认已执行 `数据库创建.sql`。
- 修改 `.env` 后必须重启 FastAPI。

### 小程序请求失败

- 开发者工具本地调试时勾选“不校验合法域名”。
- 真机不能使用 `127.0.0.1`，必须使用电脑局域网 IP。
- 手机和电脑必须在同一网络。
- 后端防火墙需要允许 `8001` 端口访问。

### 步数同步失败

- 确认后端 `backend/.env` 已配置正确的 `WECHAT_APPID` 和 `WECHAT_SECRET`。
- 确认小程序 AppID 与后端 AppID 一致。
- 确认手机端已经授权微信运动。
- 查看后端日志中 `/api/steps/sync` 的具体错误。

### 我的奖品为空

- 当前我的奖品依赖数据库 `winners` 表。
- 如果当前登录用户没有获奖记录，页面会显示暂无奖品。
- 本地调试可确认 `DEV_WECHAT_OPENID` 对应的用户是否在 `winners` 表中有数据。

## 11.启动相关

### 后端启动

- 终端输入：
  cd D:\my-web\sportsNum\步数小程序\backend
  py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

### 前端访问

- 浏览器输入：
  http://127.0.0.1:8001/docs

- 注意：
  如果是真机测试，需要获取电脑局域网IP

终端输入：ipconfig

# 活动真实数据、状态与海报修复总结

更新时间：2026-05-20

## 1. 修改了哪些文件

### 小程序端

- `miniprogram/app.js`
  - 移除 `devMode` 和 `mockRequest`，请求统一走后端接口。
  - 增加 `globalData.currentActivity`，用于活动列表到详情页的临时活动缓存。

- `miniprogram/config/api.js`
  - 调整后端 API 地址配置。

- `miniprogram/data/mock-activities.js`
  - 已删除，不再使用本地活动假数据。

- `miniprogram/pages/activities/activities.js`
  - 活动列表不再加载本地 mock。
  - 接口失败时不再回退到本地活动。
  - 点击活动时校验 `id`，并缓存当前活动对象。
  - 对 `posterUrl` 做后端静态资源地址补全。

- `miniprogram/pages/activities/activities.wxml`
  - 活动列表封面优先显示活动海报。
  - 将 `mock-note` 改为 `filter-note`。

- `miniprogram/pages/activities/activities.wxss`
  - 增加活动列表海报图片样式。
  - 同步 `filter-note` 样式名。

- `miniprogram/pages/activity-detail/activity-detail.js`
  - 移除本地活动 mock 依赖。
  - 详情页只按 URL 中的真实活动 ID 请求后端。
  - 接口失败时不再回退到其他活动。
  - 对 `posterUrl`、奖品图片 URL 做静态资源地址补全。
  - 同步步数后重新刷新当前活动详情。

- `miniprogram/pages/activity-detail/activity-detail.wxml`
  - 顶部 hero 区域优先显示创建活动时上传的海报。

- `miniprogram/pages/activity-detail/activity-detail.wxss`
  - 增加详情页海报图片样式。

- `miniprogram/pages/index/index.js`
  - 首页“我正在参与的活动”不再使用本地活动兜底。
  - 移除模拟数据模式判断。

- `miniprogram/pages/ranking/ranking.js`
  - 排行榜不再从本地活动配置取标题。
  - 活动信息统一从后端获取。

- `miniprogram/pages/checkin-feed/checkin-feed.js`
  - 打卡动态页不再使用本地活动配置兜底。

- `miniprogram/pages/checkin-edit/checkin-edit.js`
  - 发布打卡页不再使用本地活动配置兜底。

- `miniprogram/pages/admin-activity-form/admin-activity-form.js`
  - 活动后台表单已有海报上传、奖品图片上传和 URL 规范化相关调整。

- `miniprogram/pages/my-prizes/my-prizes.js`
- `miniprogram/pages/my-prizes/my-prizes.wxml`
- `miniprogram/pages/my-prizes/my-prizes.wxss`
- `miniprogram/pages/redeem/redeem.json`
  - 奖品展示和核销相关页面存在配套调整。

### 后端

- `backend/app/api/activities.py`
  - 用户端活动接口不再注入默认演示活动。
  - 用户端活动状态改为按当前时间动态计算。
  - `/activities` 状态筛选基于动态状态过滤。
  - `/activities/{id}` 返回真实活动详情。
  - `join` 报名校验基于动态状态。
  - 返回 `posterUrl` 给小程序端。

- `backend/app/schemas/schemas.py`
  - `ActivityResponse` 增加 `posterUrl` 字段。

- `backend/app/api/auth.py`
  - 移除无 token 时返回开发测试用户的逻辑。
  - 移除缺微信配置时返回假 openid 的逻辑。

- `backend/app/api/admin.py`
- `backend/app/api/prizes.py`
- `backend/app/models/models.py`
- `backend/app/services/activity_awards.py`
  - 活动奖品、获奖记录、活动海报/奖品图片、核销权限相关配套调整。

### 数据库脚本

- `database/admin_tables.sql`
- `database/schema.sql`
  - 补充活动海报、活动奖品图片、获奖记录活动归属等字段结构。

### Vue 预览端

- `app/src/views/Login.vue`
  - 移除 mock 登录 code。

- `app/src/views/Home.vue`
  - 移除随机步数同步，改为依赖微信环境的真实 `wx.login` 和 `wx.getWeRunData`。

## 2. 当前项目运行方式

### 后端

在项目根目录为：

```text
D:\my-web\sportsNum
```

启动 FastAPI 后端：

```powershell
cd D:\my-web\sportsNum\backend
$env:DB_PASSWORD="123456"
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

验证地址：

```text
http://127.0.0.1:8001/health
http://127.0.0.1:8001/docs
```

真机或微信开发者工具访问后端时，确认：

```text
miniprogram/config/api.js
```

中的 `BASE_URL` 是当前电脑局域网 IP，例如：

```js
const BASE_URL = "http://10.213.115.129:8001";
```

### 小程序

微信开发者工具导入项目根目录：

```text
D:\my-web\sportsNum
```

根目录 `project.config.json` 已指向：

```json
"miniprogramRoot": "miniprogram/"
```

修改接口、活动数据、图片字段后，建议在微信开发者工具中执行：

```text
清缓存并重新编译
```

### 数据库

首次建库或重建库时执行：

```sql
source D:/my-web/sportsNum/database/schema.sql;
source D:/my-web/sportsNum/database/admin_tables.sql;
source D:/my-web/sportsNum/database/checkin_tables.sql;
```

当前已移除运行时默认活动注入，活动数据应通过后台创建或真实数据库写入。

## 3. 已知问题

- `app` Vue 预览端执行 `npm run build` 失败，原因是本地 `app/node_modules/.bin/vite.cmd` 缺失。需要重新安装依赖后再构建。
- 项目中 README 和部分历史文档仍提到 mock 或模拟数据，但运行代码 `miniprogram`、`app/src`、`backend/app` 已清理相关入口。
- 后端活动接口现在不再自动插入默认活动。如果数据库为空，小程序活动列表会显示为空，需要先通过后台创建活动。
- 小程序端删除 mock 后更依赖真实登录、真实后端和真实数据库。后端 `.env` 中必须配置可用的数据库和微信参数。
- 海报图片依赖后端静态文件服务。若图片仍不显示，需要检查 `/static/uploads/...` 文件是否存在，以及 `BASE_URL` 是否能从小程序环境访问。
- 微信开发者工具可能缓存旧包。活动详情仍显示绿色渐变时，应先清缓存并重新编译。
- 工作区中还有本次之前的未提交改动，提交前需要统一 review 一次 diff，避免把不相关改动混入同一个提交。

## 4. 下一个任务应该从哪里开始

建议从真实活动闭环验证开始：

1. 重启后端，打开 `/docs` 确认接口正常。
2. 在微信开发者工具中清缓存并重新编译。
3. 用后台创建一个新活动，上传海报，保存后确认数据库 `activities.poster_url` 有值。
4. 在用户端活动列表检查：
   - 活动状态是否按当前时间显示。
   - 活动卡片封面是否显示上传海报。
   - 点击活动是否进入同一个活动详情。
5. 在活动详情页检查：
   - 顶部海报是否为后台上传的图片。
   - 活动名称、描述、报名时间、面向对象、参与人数是否来自当前活动。
6. 继续做报名、同步步数、排行榜、打卡动态、奖品展示和核销的完整真实数据测试。

优先排查点：

- 如果点击活动仍跳错，先在 `miniprogram/pages/activities/activities.js` 的 `goDetail` 中打印点击的 `id`，再在 `activity-detail.js` 的 `onLoad` 中打印收到的 `options.id`。
- 如果海报不显示，先请求 `/api/activities/{id}` 看 `posterUrl` 是否返回，再用浏览器打开 `BASE_URL + posterUrl` 验证静态文件能否访问。

## 5. 当前校验结果

已执行并通过：

```powershell
node --check miniprogram\app.js
node --check miniprogram\pages\activities\activities.js
node --check miniprogram\pages\activity-detail\activity-detail.js
node --check miniprogram\pages\index\index.js
node --check miniprogram\pages\ranking\ranking.js
node --check miniprogram\pages\checkin-feed\checkin-feed.js
node --check miniprogram\pages\checkin-edit\checkin-edit.js
python -c "compile(... backend/app/api/activities.py ...); compile(... backend/app/api/auth.py ...); compile(... backend/app/schemas/schemas.py ...)"
```

已搜索确认运行代码中没有以下入口：

```text
mock
模拟
devMode
假数据
使用本地
mock-activities
DEFAULT_ACTIVITIES
ensure_default_activities
```

搜索范围：

```text
miniprogram
app/src
backend/app
```

# 活动奖品映射与获奖生成修改总结

## 1. 修改了哪些文件

### 后端服务

- `backend/app/services/activity_awards.py`
  - 新增活动奖品配置与实际奖品记录的映射逻辑。
  - 从 `activities.prizes_json` 中读取奖品配置，并补齐 `prize_id`，稳定关联到 `prizes.id`。
  - 如果活动奖品配置找不到已有奖品，会按奖品名称创建新的 `prizes` 记录。
  - 新增活动获奖记录生成流程：
    - 读取活动参与用户；
    - 按活动时间范围汇总步数；
    - 计算排名、积分、达标天数、连续达标天数、打卡动态天数；
    - 按活动获奖规则筛选获奖用户；
    - 按活动奖品配置给用户生成 `winners` 记录；
    - 生成时写入 `activity_id`。

- `backend/app/services/__init__.py`
  - 新增 services 包初始化文件，便于后端服务模块导入。

### 后端接口

- `backend/app/api/admin.py`
  - 后台活动详情返回映射后的活动奖品配置，包含 `prize_id`。
  - 创建活动后立即补齐活动奖品和 `prizes.id` 的映射。
  - 新增接口：

```text
POST /api/admin/activities/{activity_id}/winners/generate
```

  - 该接口用于活动结束后生成获奖记录。
  - 仅活动根管理员可调用。
  - 活动未结束时会拒绝生成。

- `backend/app/api/activities.py`
  - 默认活动初始化时补齐奖品映射。
  - 活动详情返回映射后的 `activity.prizes`，活动奖品中带 `prize_id`、`image_url`、`prize_type` 等字段。
  - 活动结束后的“是否获奖”和“获奖名称”改为读取真实 `winners` 记录，而不是只按固定排名推断。

- `backend/app/api/prizes.py`
  - `/prizes` 新增 `activity_id` 查询参数，可按活动返回该活动配置关联的奖品列表。
  - 后台核销成功响应增加活动名称、获奖用户、核销后状态，便于后台页面展示。

### 后端数据结构

- `backend/app/schemas/schemas.py`
  - `ActivityPrizeItem` 增加 `prize_id`、`quantity`。
  - `AdminPrizeConfig` 增加 `prize_id`。
  - `RedeemResponse` 增加 `user_name`、`status`。

### 小程序页面

- `miniprogram/pages/admin-redeem/admin-redeem.js`
  - 接收后台核销接口返回的 `activity_name`、`user_name`、`status`。

- `miniprogram/pages/admin-redeem/admin-redeem.wxml`
  - 核销成功结果中展示活动、获奖用户和状态。

## 2. 当前项目运行方式

### 启动后端

```powershell
cd D:\my-web\sportsNum\backend
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

后端启动后可访问：

```text
http://127.0.0.1:8001/docs
```

接口统一挂在 `/api` 前缀下，例如：

```text
POST http://127.0.0.1:8001/api/admin/activities/{activity_id}/winners/generate
```

### 启动小程序

1. 使用微信开发者工具导入：

```text
D:\my-web\sportsNum\miniprogram
```

2. 确认接口地址：

```text
miniprogram/config/api.js
```

`BASE_URL` 需要指向当前后端地址。真机调试时应使用电脑局域网 IP，例如：

```js
const BASE_URL = "http://电脑IP:8001";
```

3. 真机测试时需要确认：

- 手机和电脑在同一局域网。
- 手机浏览器能访问 `http://电脑IP:8001/docs`。
- 小程序请求路径能正确拼接 `/api` 前缀。

## 3. 已知问题

- 当前目录不是 Git 仓库，无法通过 `git status` 做变更审计。
- `py -3.12 -m py_compile ...` 仍会因为现有 `__pycache__` 文件写入权限被 Windows 拒绝；本次改用 `ast.parse` 和模块导入检查。
- 本次没有做业务流程测试，也没有做微信开发者工具或真机测试。
- 新增了后台生成获奖记录接口，但小程序后台页面暂时没有新增“生成获奖记录”按钮，需要通过接口文档或接口工具调用。
- 活动奖品映射目前仍基于 `activities.prizes_json` 自动补齐 `prize_id`，还没有新增独立活动奖品表。
- 如果奖品配置的名称和已有 `prizes.name` 重名，会复用最早的同名奖品；这适合当前演示数据，但生产环境最好改为独立活动奖品表。
- 获奖生成逻辑按现有规则字段做了通用兼容，但不同活动规则的业务口径还需要进一步明确，例如积分计算、达标天数、参与奖和排名奖是否可以叠加。
- 活动未结束时生成获奖记录会被拒绝；如果需要管理员提前结算，需要单独设计强制结算权限和状态流转。

## 4. 下一个任务应该从哪里开始

建议下一步从“后台获奖生成入口和活动奖品表”开始。

具体任务：

1. 给后台活动详情页新增“生成获奖记录”按钮。
   - 仅根管理员可见。
   - 仅活动结束后可点击。
   - 点击后调用 `POST /api/admin/activities/{activity_id}/winners/generate`。
   - 展示生成结果：新增数量、更新数量、跳过数量、总数。

2. 将活动奖品配置从 JSON 迁移为独立表。
   - 建议新增 `activity_prizes` 表。
   - 字段包含 `activity_id`、`prize_id`、`rank_label`、`rank_start`、`rank_end`、`quantity`、`sort_order`。
   - 后续活动详情、后台活动编辑、获奖生成都统一读这张表。

3. 明确活动获奖规则的生产口径。
   - 积分如何计算。
   - 达标天数是否必须满足。
   - 排名奖和参与奖是否可叠加。
   - 多个奖品规则命中时如何分配奖品。

4. 完整业务测试。
   - 用户报名活动。
   - 用户同步步数。
   - 活动结束后管理员生成获奖记录。
   - 用户在“我的奖品”看到真实获奖记录。
   - 用户生成兑换码和二维码。
   - 活动管理员核销。
   - 用户端刷新后状态变为已领取。

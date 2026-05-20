# 奖品核销权限与活动归属修改总结

## 1. 修改了哪些文件

### 后端数据模型与接口

- `backend/app/models/models.py`
  - 给 `Winner` 获奖记录增加 `activity_id` 字段。
  - 给 `winners.activity_id` 增加索引，用于按活动归属查询和校验。

- `backend/app/schemas/schemas.py`
  - `WinnerResponse` 增加 `activity_id`。
  - `WinnerWithDetails` 增加 `activity_name`。
  - `MyPrizeItem` 增加 `activity_id`、`activity_name`。
  - `RedeemResponse` 增加 `activity_id`、`activity_name`，便于后台核销成功后明确返回奖品所属活动。

- `backend/app/api/prizes.py`
  - 新增 `ensure_winner_activity_column()`，在运行时确保旧数据库里的 `winners` 表具备 `activity_id` 字段。
  - 对本地演示数据中的 1-4 号获奖记录做兼容补齐：如果缺少 `activity_id`，会回填为 `campus-spring-2026`。
  - `/prizes/my/list` 返回我的奖品时，关联活动表并返回活动名称。
  - `/prizes/winners/{prize_id}` 返回获奖名单时，带上活动 ID 和活动名称。
  - `/prizes/admin/redeem` 后台核销时，从“只校验当前用户是否是任意活动管理员”改为：
    - 先读取获奖记录的 `activity_id`；
    - 校验该活动是否存在；
    - 校验当前用户是否是该活动的管理员；
    - 只有管理该活动的用户才可以核销该奖品。
  - 如果获奖记录没有活动 ID，会返回冲突错误，避免无归属奖品被任意管理员核销。

### 数据库脚本

- `database/schema.sql`
  - `winners` 表新增 `activity_id` 字段。
  - 新增 `idx_winner_activity` 索引。

- `database/seed.sql`
  - 演示获奖记录写入时增加 `activity_id`。
  - 重复执行种子数据时同步更新获奖记录的活动归属。

- `database/admin_tables.sql`
  - 增加旧库补丁：给 `winners` 表补充 `activity_id` 字段。

### 小程序页面

- `miniprogram/pages/my-prizes/my-prizes.wxml`
  - “我的奖品”列表来源展示优先使用活动名称。
  - 如果没有活动名称，再回退到周期名称或默认活动名称。

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

真机调试时需要用电脑局域网 IP 访问，例如：

```text
http://电脑IP:8001/docs
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

`BASE_URL` 需要指向当前后端地址。真机测试时应使用电脑局域网 IP，例如：

```js
const BASE_URL = "http://电脑IP:8001";
```

3. 真机测试要求：

- 手机和电脑在同一局域网。
- 手机浏览器能访问 `http://电脑IP:8001/docs`。
- 后端数据库中 `winners.activity_id` 必须有值，否则后台核销会被拒绝。

## 3. 已知问题

- 现有项目不是 Git 仓库，无法通过 `git status` 做变更审计。
- `py -3.12 -m compileall app` 会因为现有 `__pycache__` 文件写入权限被 Windows 拒绝而失败；已改用 `ast.parse` 和模块导入检查确认相关源码语法与导入正常。
- 旧获奖记录如果没有 `activity_id`，后台核销会返回“获奖记录缺少活动ID，无法核销”。当前仅对本地演示数据 1-4 号记录做了自动回填。
- 目前奖品主表 `prizes` 仍是全局奖品表，活动奖品配置主要存在 `activities.prizes_json` 中；活动奖品配置和实际获奖记录之间还没有完全统一为生产级数据关系。
- 后台管理员权限已经细化到“只能核销自己管理活动的奖品”，但获奖记录生成流程本身还没有完整实现活动维度的自动发奖。
- 二维码 SVG 已能生成，但真机扫码兼容性仍需要在微信开发者工具和真实手机上完整验证。
- 部分中文文件在普通 PowerShell 默认编码下可能显示乱码，查看时建议显式使用 UTF-8。

## 4. 下一个任务应该从哪里开始

建议下一步从“活动维度的获奖生成与奖品配置统一”开始。

具体任务：

1. 建立活动奖品配置和实际奖品记录的稳定映射。
   - 明确 `activities.prizes_json` 中每个奖品配置如何对应 `prizes.id`。
   - 或者新增活动奖品表，避免长期依赖 JSON 配置。

2. 实现活动结束后的获奖记录生成流程。
   - 按活动规则计算排名、积分、达标天数或打卡天数。
   - 给符合条件的用户生成 `winners` 记录。
   - 生成时必须写入 `activity_id`。

3. 统一活动详情、奖品列表、我的奖品的数据来源。
   - 活动详情展示活动奖品。
   - 我的奖品展示实际获奖记录。
   - 后台核销展示奖品所属活动、获奖用户、奖品状态。

4. 做完整真机流程测试。
   - 用户参与活动并同步步数。
   - 活动产生获奖记录。
   - 用户生成兑换码和二维码。
   - 活动管理员扫码核销。
   - 数据库状态变为 `redeemed`。
   - 用户端刷新后显示已领取。


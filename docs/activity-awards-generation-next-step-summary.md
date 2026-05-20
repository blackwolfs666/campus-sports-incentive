# 活动奖品、兑换凭证与小程序展示修改总结

## 1. 修改了哪些文件

### 后端数据结构

- `backend/app/models/models.py`
  - `ActivityPrize` 增加 `image_url` 字段，用于活动奖品单独配置展示图片。
  - 当前图片存储策略是数据库保存图片 URL 或相对路径，不保存图片二进制。

- `database/schema.sql`
  - `activities` 补充 `poster_url` 字段，用于活动海报。
  - `activity_prizes` 补充 `image_url` 字段，用于活动奖品展示图片。

- `database/admin_tables.sql`
  - 增加 `activity_prizes.image_url` 的增量补字段语句。
  - 继续保留后台增量建表和活动后台相关字段补齐逻辑。

### 后端服务与接口

- `backend/app/services/activity_awards.py`
  - 新增活动奖品表结构补齐逻辑，确保 `activity_prizes.image_url` 存在。
  - 活动奖品序列化时优先使用 `activity_prizes.image_url`，其次使用 `prizes.image_url`，最后使用默认奖品图。
  - 从旧 `activities.prizes_json` 迁移到 `activity_prizes` 时同步保存奖品图片地址。

- `backend/app/api/admin.py`
  - 后台初始化表时补齐 `activity_prizes.image_url`。

- `backend/app/api/prizes.py`
  - 增加本地二维码文件缺失检测。
  - `/api/prizes/detail/{winner_id}` 返回详情时，如果 `claimed` 或 `redeemed` 状态已有兑换码，但二维码文件不存在，会自动重新生成二维码并回写 `winners.claim_qrcode`。
  - 该逻辑只补二维码文件和二维码路径，不会新增奖品或新增获奖记录。

### 小程序页面

- `miniprogram/pages/redeem/redeem.json`
  - 将奖品兑换页改为自定义导航栏，去掉小程序原生顶部导航。

- `miniprogram/pages/index/index.js`
  - 首页同步运动步数成功后，额外刷新“我参与的活动”，避免活动卡片停留在旧状态。

- `miniprogram/pages/activity-detail/activity-detail.js`
  - 活动详情页 `onShow` 时重新拉取活动详情。
  - 在详情页同步步数成功后重新拉取当前活动详情。

- `miniprogram/pages/my-prizes/my-prizes.js`
  - “待生成”文案改为“待核销”。
  - 修复已过期奖品被归类到待核销列表的问题。
  - 三个列表页统一使用“查看凭证”操作文案。

- `miniprogram/pages/my-prizes/my-prizes.wxml`
  - 奖品状态标识放回奖品名称右侧。
  - 右侧按钮单独放在操作区。

- `miniprogram/pages/my-prizes/my-prizes.wxss`
  - 调整“我的奖品”卡片布局。
  - “查看凭证”按钮宽度调整为约卡片内容宽度的五分之一。
  - 状态标识紧贴奖品名称，长标题仍可截断。

### 本地数据库测试数据

- 已给数据库用户 `id=8` 写入测试奖品记录，覆盖三类页面状态：
  - `pending`
  - `claimed`
  - `redeemed`
- 测试周期名称：

```text
用户8奖品状态测试周期
```

- 已为测试奖品补充图片路径，并修复测试兑换码对应二维码文件。

### 其他注意

- `miniprogram/config/api.js` 当前也有改动，表现为本地接口地址变化。这是本地调试配置，不属于本轮业务逻辑改动。

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

常用接口示例：

```text
GET  http://127.0.0.1:8001/api/prizes/my/list
GET  http://127.0.0.1:8001/api/prizes/detail/{winner_id}
POST http://127.0.0.1:8001/api/prizes/claim/{winner_id}
POST http://127.0.0.1:8001/api/admin/activities/{activity_id}/winners/generate
```

### 启动小程序

1. 使用微信开发者工具导入：

```text
D:\my-web\sportsNum\miniprogram
```

2. 检查接口地址：

```text
miniprogram/config/api.js
```

真机调试时，`BASE_URL` 需要指向电脑局域网 IP，例如：

```js
const BASE_URL = "http://电脑IP:8001";
```

3. 真机测试时确认：

- 手机和电脑在同一局域网。
- 手机浏览器能访问 `http://电脑IP:8001/docs`。
- 小程序请求路径能正确拼接 `/api` 前缀。

## 3. 已知问题

- 本次已做静态语法校验和本地数据库写入验证，但没有用微信开发者工具完整回归全部页面。
- 生产环境建议使用对象存储或 CDN 保存上传图片，数据库继续保存图片 URL，不建议把图片二进制写入 MySQL。
- `activity_prizes` 已有运行时补表逻辑，但正式环境仍建议使用迁移脚本管理表结构。
- `activities.prizes_json` 仍作为兼容字段保留，后续可以在确认新表稳定后逐步弱化旧字段依赖。
- 当前“过期”不是独立数据库状态，而是通过 `claim_deadline < 当前时间` 推导出来；如果后续新增 `expired` 枚举状态，需要同步更新后端和小程序状态判断。
- 二维码自动补生成只适用于已有 `claim_code` 的记录；`pending` 状态如果还没有兑换码，无法生成二维码。
- 小程序奖品列表样式已按当前截图调整，但仍需要真机确认不同奖品名称长度下的视觉效果。

## 4. 下一个任务应该从哪里开始

建议下一步从“真机回归奖品领取与核销链路”开始。

具体任务：

1. 在微信开发者工具或真机上验证用户 8 的三类奖品状态。
   - 待核销列表能看到待处理奖品。
   - 已领取列表能看到已核销奖品。
   - 已过期列表能看到超过 `claim_deadline` 的奖品。

2. 验证兑换凭证页。
   - 待核销奖品能显示兑换码和二维码。
   - 已领取奖品仍能显示历史二维码。
   - 二维码文件缺失时，刷新详情后后端能自动补生成。

3. 验证上传图片链路。
   - 新建活动时上传活动海报，确认 `activities.poster_url` 入库。
   - 配置奖品图片，确认 `prizes.image_url` 或 `activity_prizes.image_url` 入库。
   - 小程序页面能通过返回 URL 正常展示图片。

4. 做完整活动闭环测试。
   - 管理员创建活动。
   - 用户报名和同步步数。
   - 活动结束后生成获奖记录。
   - 用户领取兑换码。
   - 活动管理员核销。
   - 用户端状态更新。

5. 梳理正式迁移方案。
   - 将运行时补字段逻辑整理为明确的数据库迁移脚本。
   - 评估是否需要为上传文件接入对象存储。

## 5. 文档位置

```text
D:\my-web\sportsNum\docs\activity-awards-generation-next-step-summary.md
```

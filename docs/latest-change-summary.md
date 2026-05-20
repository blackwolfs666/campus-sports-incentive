# 邮青步纪本次修改总结

## 1. 修改了哪些文件

### 我的页面

- `miniprogram/pages/profile/profile.wxml`
  - 在用户信息区域增加 `ID：U0000001` 展示。
  - 点击用户 ID 可复制。
  - 移除了“绑定学校身份 / 绑定学校账号”独立卡片。

- `miniprogram/pages/profile/profile.js`
  - 增加用户 ID 格式化逻辑。
  - 增加复制用户 ID 交互。
  - “设置与帮助”入口改为跳转设置页。

- `miniprogram/pages/profile/profile.wxss`
  - 用户 ID 样式调整为和部门一致的小字灰色样式。
  - 清理已移除绑定卡片相关样式。

### 设置与帮助页面

- `miniprogram/pages/settings/settings.json`
- `miniprogram/pages/settings/settings.wxml`
- `miniprogram/pages/settings/settings.js`
- `miniprogram/pages/settings/settings.wxss`
  - 新增“设置与帮助”页面。
  - 包含用户信息、复制用户 ID、绑定学校账号、微信运动权限、本地缓存、帮助说明。
  - 已绑定学校账号时，再次点击会提示是否换绑；确认后才进入绑定页面。

- `miniprogram/app.json`
  - 注册 `pages/settings/settings` 页面。

### 学校账号绑定页面

- `miniprogram/pages/cas-binding/cas-binding.wxml`
- `miniprogram/pages/cas-binding/cas-binding.json`
  - 页面标题统一为“绑定学校账号”。

### 奖品兑换与核销

- `backend/app/api/prizes.py`
  - 用户端只生成兑换码，不再允许自助核销。
  - 只有后台管理员通过扫码或输入兑换码才会把奖品状态改为已核销。
  - 增加兑换二维码生成逻辑。

- `miniprogram/pages/my-prizes/my-prizes.js`
- `miniprogram/pages/my-prizes/my-prizes.wxss`
  - 修正奖品状态展示逻辑。

## 2. 当前项目运行方式

### 启动后端

```powershell
cd D:\my-web\sportsNum\backend
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 启动小程序

1. 使用微信开发者工具导入：

```text
D:\my-web\sportsNum\miniprogram
```

2. 确认前端接口地址：

```text
miniprogram/config/api.js
```

`BASE_URL` 需要设置为当前电脑局域网 IP，例如：

```js
const BASE_URL = "http://你的电脑IP:8001";
```

3. 真机测试要求：

- 手机和电脑在同一局域网。
- 手机浏览器能访问：

```text
http://电脑IP:8001/docs
```

如果手机浏览器无法访问 FastAPI 文档，小程序也无法正常请求后端。

## 3. 已知问题

- 学校 CAS 绑定目前是初步接入结构，真实可用还依赖学校 CAS 服务地址、回调地址、字段映射是否正确。
- 奖品二维码已生成 SVG，但真机扫码兼容性还需要实际测试确认。
- 后台奖品核销目前只校验“当前用户是否是活动管理员”，还没有细化到“只能核销自己管理活动的奖品”，因为奖品获奖记录和活动关系还不够完整。
- “我的消息”“退出登录”等入口仍是占位。
- 部分数据仍依赖本地测试数据，活动、奖品、管理员、排行榜的生产级数据关系还需要进一步梳理。
- 图片上传目前主要是本地静态路径 / 上传占位，后续需要统一成正式上传和存储方案。

## 4. 下一个任务应该从哪里开始

建议从“后台核销权限和奖品归属关系”开始。

具体任务：

1. 给奖品获奖记录明确关联活动 ID。
2. 后台核销时校验：当前管理员必须管理该奖品所属活动。
3. 奖品列表、活动详情、活动奖品配置统一使用活动维度的数据。
4. 真机测试完整流程：
   - 用户获奖；
   - 生成兑换码 / 二维码；
   - 管理员扫码；
   - 数据库状态变为已核销；
   - 用户端刷新显示已领取。

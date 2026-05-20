# 项目本地结构

项目根目录：
D:\my-web\sportsNum

后端：
D:\my-web\sportsNum\backend

小程序：
D:\my-web\sportsNum\miniprogram

数据库脚本：
D:\my-web\sportsNum\database

文档：
D:\my-web\sportsNum\docs

# 启动须知

后端启动：
cd D:\my-web\sportsNum\backend
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload

//启动不成功可以修改端口尝试

如果网络修改，需要先

- 终端输入ipconfig，查询ipv4地址
- 在D:\my-web\sportsNum\miniprogram\config\api.js
- 修改：
  const BASE_URL = 'http://10.197.187.147:8001'
  const API_BASE_URL = `${BASE_URL}/api`

# 省token的注意事项

- 一个任务开一个线程/对话
  可以每次任务结束了让codex总结，
  请总结本次修改：
  1. 修改了哪些文件
  2. 当前项目运行方式
  3. 已知问题
  4. 下一个任务应该从哪里开始
  5. 创建并写入一个新的md文档

- 不要让它自己找代码，要指定文件和修改范围
  提示词包含目标、上下文、约束、完成标准，这能减少 Codex 乱猜和反复探索

  只检查 frontend/src/pages/activity 相关文件，不要扫描整个项目。
  目标：修复活动详情页点击报名无反应的问题。
  已知现象：点击按钮后页面没有变化，控制台无明显报错。
  限制：不要重构页面，只做最小修改。
  完成标准：点击报名后能调用 /api/activity/join，并给出成功/失败提示。

- 可以先把问题发给codex，让它定位，输出预计修改的文件内容，再根据文件内容写提示词，让它修改
  先不要修改代码。请只阅读相关文件，定位问题原因，并告诉我你准备改哪些文件。

  按你刚才的方案做最小修改，不要改无关文件。

- 可以写一个短的AGENTS.md，让 Codex 每次知道项目结构、启动命令、测试命令、注意事项；官方也建议用它保存仓库规则，但要保持小而实用
  太长了也会占用上下文

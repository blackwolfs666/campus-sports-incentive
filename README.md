# 邮青步纪

当前项目根目录：

```text
D:\my-web\sportsNum
```

这是一个校园步数微信小程序项目，包含微信小程序端、FastAPI 后端、MySQL 数据库脚本，以及一个可选的 Vue Web 预览端。

## 目录结构

```text
sportsNum/
├─ backend/          # FastAPI 后端
├─ miniprogram/      # 微信小程序端，根目录 project.config.json 指向这里
├─ database/         # MySQL 脚本，已提供英文文件名
├─ app/              # 可选 Vue Web 预览端
├─ venvs/            # 本地 Python 虚拟环境，不提交
├─ archives/         # 历史备份、旧压缩包、迁移前文件
├─ README.md
└─ README_LOCAL.md
```

## 快速启动

后端：

```powershell
cd D:\my-web\sportsNum\backend
$env:DB_PASSWORD="123456"
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

小程序接口地址：

```text
miniprogram/config/api.js
```

微信开发者工具导入目录：

```text
D:\my-web\sportsNum
```

根目录 `project.config.json` 已配置 `miniprogramRoot: "miniprogram/"`。

数据库脚本：

```text
database/schema.sql
database/seed.sql
database/checkin_tables.sql
```

更详细的本地运行说明见：

```text
README_LOCAL.md
```

# SkillHub 技能实践与项目协作平台

SkillHub 面向高校学生与校园组织，将技能、作品、真实项目和四维评价连接成可展示、可验证、持续成长的档案。MVP 包含三类角色认证、作品上传、项目审核与申请、录用、评价、技能积分和管理后台；不包含支付、聊天与 AI 功能。

## 环境要求

- Python 3.11+
- Node.js 20+
- Windows PowerShell

## 后端安装与启动

```powershell
cd backend
python -m venv .venv
./.venv/Scripts/python -m pip install -e ".[dev]"
Copy-Item .env.example .env
./.venv/Scripts/python -m app.seed
./.venv/Scripts/python -m uvicorn app.main:app --reload
```

后端地址为 `http://127.0.0.1:8000`，API 文档为 `http://127.0.0.1:8000/docs`。上传文件保存在 `backend/uploads/`，SQLite 数据库默认为 `backend/skillhub.db`。

## 前端安装与启动

另开一个 PowerShell：

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

访问 `http://localhost:5173`。Vite 会将 `/api` 和 `/uploads` 代理到 FastAPI。

## 演示账号

所有账号密码均为 `Student123!`：

| 用户名 | 角色 |
| --- | --- |
| `admin` | 管理员 |
| `student` | 数据方向学生 |
| `designer` | 设计方向学生 |
| `campus_org` | 校园需求方 |

## 测试与构建

```powershell
cd backend
./.venv/Scripts/python -m pytest -q --cov=app --cov-report=term-missing

cd ../frontend
npm run test -- --run --maxWorkers=1 --no-file-parallelism
npm run build
```

## 课堂演示流程

1. 使用 `campus_org` 发布项目。
2. 使用 `admin` 在项目审核页通过项目。
3. 使用 `student` 在项目大厅提交申请。
4. 使用 `campus_org` 录用学生并依次开始、结束项目。
5. 需求方填写四维评价，项目自动完成。
6. 返回学生工作台，查看作品、完成项目和评价共同产生的技能积分与等级更新。

## 第二阶段扩展

- 将 `DATABASE_URL` 切换为 PostgreSQL，并用 Alembic 管理迁移。
- 将本地上传替换为 OSS/S3 对象存储和签名 URL。
- 在独立 `agents/` 服务中加入项目匹配、需求分析和成长建议 Agent，保持现有 REST 边界不变。
- 生产环境应更换 JWT 密钥、启用 HTTPS、限制 CORS、增加审计日志与上传病毒扫描。

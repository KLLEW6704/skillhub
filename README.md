# SkillHub：面向高校学生的技能证据与真实项目验证平台

SkillHub 不把一次自报或一次 AI 打分包装成“能力认证”。它把一条更谨慎的验证链路做成可运行原型：

**作品证据 → AI 动态答辩 → 透明 AI 辅助初评 → 人工复核 → 真实项目交付验证**

当前版本用于课程实践与产品假设验证，不是学校官方认证系统。系统生成的徽章明确标记为“SkillHub 试行技能徽章”；种子数据中的作品也明确标记为演示样本，不代表真实学生成果。

## 当前可演示能力

- 学生建立技能档案，上传作品并记录创作背景、个人职责、制作过程和迭代说明。
- 每份作品可设为仅自己可见、仅授权项目可见或公开展示；申请项目时单独选择授权作品。
- 经学生明确同意后，对 PNG、JPEG、WebP 静态视觉作品发起 AI 观察；不支持的格式仍可保存，但不会伪装成已完成 AI 评估。
- AI 先返回可观察事实与证据缺口，再生成三道针对性问题；学生回答后才形成带证据引用的量表初评。
- AI 运行状态、失败原因和重试记录可追踪；初评不会自动改变权限、项目状态或成长活跃度。
- 管理员可查看 AI 运行与待复核记录、分配评审；评审可检查原作品、答辩和量表，调分与结论必须填写理由。
- 人工复核通过后可生成可公开核验、可撤销的试行徽章。
- 项目方发布项目时填写交付物与验收标准，只能查看学生为该项目主动授权的作品；项目完成后的四维评价形成独立的真实项目验证记录。
- 公开学生页将“成长活跃度、公开作品证据、AI 边界、人工核验、真实项目记录、项目评价”分区展示，避免混成一个看似权威的总分。

## 技术组成

- 后端：FastAPI、SQLAlchemy、SQLite、Pydantic、JWT
- 前端：React、TypeScript、Vite、TanStack Query、React Router
- 模型接口：DashScope 的 OpenAI 兼容接口

## 本地启动

环境建议：Python 3.11+、Node.js 20+、Windows PowerShell。

### 上台演示时最快打开

在文件资源管理器中进入本项目文件夹，双击 `start-demo.cmd`。它会打开“SkillHub Backend”和“SkillHub Frontend”两个运行窗口，并在数秒后自动打开 `http://127.0.0.1:5173/`。

- 第一次运行会自动准备演示环境，可能需要几分钟和网络连接；建议在正式演示前至少运行一次。
- 演示期间不要关闭两个运行窗口。
- 演示结束后直接关闭这两个窗口即可。
- 如果浏览器没有自动打开，手动在 Chrome 或 Edge 地址栏输入 `http://127.0.0.1:5173/`。
- 若首次自动准备失败，可先双击 `setup-demo.cmd`，根据窗口提示修复后再运行 `start-demo.cmd`。

下面是需要手动控制服务时的启动方式。

后端：

```powershell
cd backend
python -m venv .venv
./.venv/Scripts/python -m pip install -e ".[dev]"
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
./.venv/Scripts/python -m app.seed
./.venv/Scripts/python -m uvicorn app.main:app --reload
```

后端地址为 `http://127.0.0.1:8000`，接口文档为 `http://127.0.0.1:8000/docs`。SQLite 数据库默认为 `backend/skillhub.db`，上传文件保存在 `backend/uploads/`。

前端（另开一个 PowerShell）：

```powershell
cd frontend
npm install
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm run dev
```

访问 `http://localhost:5173`。开发服务器会把 `/api` 与 `/uploads` 请求转发给后端。

## AI 配置

在 `backend/.env` 中配置以下变量。不要提交真实密钥：

```dotenv
DASHSCOPE_API_KEY=你的密钥
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen3.7-flash
```

未配置密钥或模型调用失败时，系统会保存真实失败状态与脱敏错误，并允许重试，不会生成假结果。模型名称需要具备图像理解能力；若账号无权使用默认模型，请只修改 `DASHSCOPE_MODEL`。

## 演示账号

所有种子账号密码均为 `Student123!`：

| 用户名 | 角色 | 演示重点 |
| --- | --- | --- |
| `student` | 学生 | 技能、作品证据、授权与 AI 答辩 |
| `designer` | 学生 | 设计作品和已完成项目记录 |
| `campus_org` | 项目方 | 发布项目、查看授权申请、验收评价 |
| `reviewer` | 评审 | 人工证据复核与调分理由 |
| `admin` | 管理员 | 用户、项目、AI 运行与复核分配 |

## 建议演示顺序

1. 以 `student` 登录，打开“作品证据与 AI 答辩”，说明证据字段、可见范围和 AI 授权边界。
2. 上传一张静态视觉作品，明确勾选 AI 处理同意，发起 AI 观察。
3. 对照“可观察事实”和“证据缺口”回答三道动态问题，提交复评。
4. 以 `admin` 查看 AI 运行和待人工复核记录，并分配给 `reviewer`。
5. 以 `reviewer` 核对原件与答辩，填写调分/决定理由；通过后展示公开核验页。
6. 以 `campus_org` 发布带交付物与验收标准的项目，查看申请者主动授权的作品。
7. 完成项目并评价，再回到学生公开页，说明“人工核验”和“真实项目验证”是两条独立证据。

## 验证

```powershell
cd backend
./.venv/Scripts/python -m pytest -q --cov=app --cov-report=term-missing

cd ../frontend
npm run test -- --run
npm run lint
npm run build
```

当前仓库不包含支付、即时聊天、校方背书、生产级对象存储或自动录用。生产部署还需更换 JWT 密钥、启用 HTTPS、限制跨域、执行上传内容安全检查，并迁移到受管数据库与对象存储。

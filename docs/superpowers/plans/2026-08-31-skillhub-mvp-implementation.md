# SkillHub MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a course-demo-ready SkillHub application that completes the student skill-growth loop with real authentication, uploads, project applications, reviews, administration, and responsive UI.

**Architecture:** A React/TypeScript/Vite frontend calls a versioned FastAPI REST API. FastAPI separates routes, schemas, services, and SQLAlchemy models; SQLite stores application data and a local uploads directory stores portfolio files. Skill growth is recalculated by one domain service whenever portfolio, project, or review evidence changes.

**Tech Stack:** React, TypeScript, Vite, Tailwind CSS, React Router, TanStack Query, FastAPI, SQLAlchemy 2, Pydantic 2, SQLite, PyJWT, pwdlib/Argon2, Pytest, Vitest, React Testing Library.

---

## File map

```text
SkillHub/
├─ backend/
│  ├─ pyproject.toml
│  ├─ .env.example
│  ├─ uploads/.gitkeep
│  ├─ app/
│  │  ├─ main.py                       # FastAPI construction, middleware, static uploads
│  │  ├─ api/deps.py                   # DB/current-user/role dependencies
│  │  ├─ api/v1/router.py              # Versioned router composition
│  │  ├─ api/v1/{auth,profiles,skills,portfolios,projects,applications,reviews,admin}.py
│  │  ├─ core/config.py                # Typed environment settings
│  │  ├─ core/security.py              # Password and JWT helpers
│  │  ├─ db/base.py                    # Declarative base and model imports
│  │  ├─ db/session.py                 # Engine, session factory, dependency
│  │  ├─ models/{user,profile,skill,portfolio,project,application,review}.py
│  │  ├─ schemas/{auth,profile,skill,portfolio,project,application,review,admin}.py
│  │  ├─ services/{auth,profiles,portfolios,growth,projects,applications,reviews,uploads}.py
│  │  └─ seed.py                       # Idempotent demo data initializer
│  └─ tests/
│     ├─ conftest.py
│     ├─ test_health.py
│     ├─ test_auth.py
│     ├─ test_profiles_skills.py
│     ├─ test_portfolios.py
│     ├─ test_projects_admin.py
│     ├─ test_applications.py
│     ├─ test_reviews_growth.py
│     └─ test_seed.py
├─ frontend/
│  ├─ package.json
│  ├─ vite.config.ts
│  ├─ tailwind.config.js
│  ├─ src/
│  │  ├─ main.tsx
│  │  ├─ app/router.tsx
│  │  ├─ app/providers.tsx
│  │  ├─ styles/index.css
│  │  ├─ lib/api.ts
│  │  ├─ lib/types.ts
│  │  ├─ features/auth/{auth-store,ProtectedRoute,LoginPage,RegisterPage}.tsx
│  │  ├─ features/public/{HomePage,ProjectsPage,ProjectDetailPage,TalentPage,ProfilePage}.tsx
│  │  ├─ features/student/{StudentLayout,OverviewPage,ProfileEditPage,SkillsPage,PortfoliosPage,ApplicationsPage}.tsx
│  │  ├─ features/requester/{RequesterLayout,OverviewPage,ProjectFormPage,MyProjectsPage,ApplicantsPage,ReviewPage}.tsx
│  │  ├─ features/admin/{AdminLayout,OverviewPage,UsersPage,ProjectsPage}.tsx
│  │  ├─ components/{AppShell,Button,Field,EmptyState,StatusBadge,SkillLevel,ProjectCard,RatingSummary,Toast}.tsx
│  │  └─ test/{setup.ts,render.tsx,server.ts}
│  └─ src/**/*.test.tsx
├─ README.md
└─ docs/superpowers/specs/2026-08-31-skillhub-mvp-design.md
```

## Task 1: Backend foundation and health endpoint

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`

- [x] **Step 1: Declare the backend package and dependencies**

Create `backend/pyproject.toml` with Python 3.11+ and these runtime dependencies: `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `pydantic-settings`, `python-multipart`, `PyJWT`, `pwdlib[argon2]`, `email-validator`. Add `pytest`, `pytest-cov`, and `httpx` to the `dev` extra. Configure Pytest with `pythonpath = ["."]` and `testpaths = ["tests"]`.

- [x] **Step 2: Write the failing health test**

```python
def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "skillhub-api"}
```

- [x] **Step 3: Run the test and verify RED**

Run from `backend/`:

```powershell
python -m venv .venv
./.venv/Scripts/python -m pip install -e ".[dev]"
./.venv/Scripts/python -m pytest tests/test_health.py -v
```

Expected: collection/import failure because `app.main` does not exist.

- [x] **Step 4: Implement the minimal application factory**

`backend/app/core/config.py` must expose a cached `Settings` object with `app_name`, `api_prefix`, `database_url`, `jwt_secret`, `access_token_minutes`, `frontend_origin`, `upload_dir`, and `max_upload_mb`. `backend/app/main.py` must create FastAPI, add CORS for the configured frontend origin, create `/api/v1/health`, create the upload directory, and mount `/uploads` as static files.

```python
@app.get(f"{settings.api_prefix}/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "skillhub-api"}
```

- [x] **Step 5: Run the focused test and full backend test command**

```powershell
./.venv/Scripts/python -m pytest tests/test_health.py -v
./.venv/Scripts/python -m pytest -q
```

Expected: one passing test and no warnings caused by application code.

- [x] **Step 6: Commit**

```powershell
git add backend
git commit -m "feat: scaffold SkillHub API"
```

## Task 2: Users, authentication, and role guards

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/core/security.py`
- Create: `backend/app/services/auth.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/v1/auth.py`
- Create: `backend/app/api/v1/router.py`
- Modify: `backend/app/db/base.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_auth.py`

- [x] **Step 1: Write failing authentication tests**

Cover these separate behaviors:

```python
def test_student_can_register(client):
    response = client.post("/api/v1/auth/register", json={
        "username": "student_new", "email": "new@example.com",
        "password": "StrongPass123", "role": "student",
        "school": "SkillHub University", "college": "计算机学院",
        "major": "软件工程", "grade": "2025"
    })
    assert response.status_code == 201
    assert response.json()["role"] == "student"

def test_admin_role_cannot_be_self_registered(client):
    payload = {"username": "bad_admin", "email": "bad@example.com", "password": "StrongPass123", "role": "admin"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 422

def test_login_returns_bearer_token(client, student_user):
    response = client.post("/api/v1/auth/login", data={"username": student_user.username, "password": "Student123!"})
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"

def test_inactive_user_cannot_access_me(client, inactive_token):
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {inactive_token}"}).status_code == 403
```

- [x] **Step 2: Run and verify RED**

```powershell
./.venv/Scripts/python -m pytest tests/test_auth.py -v
```

Expected: endpoint/model import failures.

- [x] **Step 3: Implement the user model and authentication API**

Create `UserRole` with `student`, `requester`, `admin`; create a unique username/email `User` model; hash passwords through `PasswordHash.recommended()`; issue JWTs with `sub`, `role`, and `exp`; implement `POST /register`, form-encoded `POST /login`, and `GET /me`. Registration schema must allow only `student` and `requester`.

Implement reusable dependencies:

```python
def require_roles(*roles: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="当前角色无权执行此操作")
        return current_user
    return dependency
```

- [x] **Step 4: Verify GREEN and regression suite**

```powershell
./.venv/Scripts/python -m pytest tests/test_auth.py -v
./.venv/Scripts/python -m pytest -q
```

- [x] **Step 5: Commit**

```powershell
git add backend/app backend/tests
git commit -m "feat: add authentication and role guards"
```

## Task 3: Profiles and student skills

**Files:**
- Create: `backend/app/models/profile.py`
- Create: `backend/app/models/skill.py`
- Create: `backend/app/schemas/profile.py`
- Create: `backend/app/schemas/skill.py`
- Create: `backend/app/services/profiles.py`
- Create: `backend/app/api/v1/profiles.py`
- Create: `backend/app/api/v1/skills.py`
- Modify: `backend/app/api/v1/router.py`
- Create: `backend/tests/test_profiles_skills.py`

- [x] **Step 1: Write failing profile and skill tests**

Test that student registration creates an editable `StudentProfile`, requester registration creates `RequesterProfile`, a student can add a unique skill, a requester receives 403 from skill mutation, duplicate normalized names return 409, and public profile output contains skill level and growth score.

```python
def test_student_adds_skill(client, student_headers):
    response = client.post("/api/v1/skills", headers=student_headers, json={"name": "Python", "description": "数据处理与接口开发"})
    assert response.status_code == 201
    assert response.json()["level"] == 1
    assert response.json()["growth_score"] == 0
```

- [x] **Step 2: Run and verify RED**

```powershell
./.venv/Scripts/python -m pytest tests/test_profiles_skills.py -v
```

- [x] **Step 3: Implement profiles and skill CRUD**

Expose:

- `GET/PATCH /profiles/me`
- `GET /profiles/students`
- `GET /profiles/students/{user_id}`
- `GET/POST /skills`
- `PATCH/DELETE /skills/{skill_id}`

Normalize skill names with `name.strip()` for display and a lowercased normalized column for uniqueness. Delete must be rejected with 409 when the skill still has portfolio evidence.

- [x] **Step 4: Verify GREEN**

```powershell
./.venv/Scripts/python -m pytest tests/test_profiles_skills.py -v
./.venv/Scripts/python -m pytest -q
```

- [x] **Step 5: Commit**

```powershell
git add backend/app backend/tests
git commit -m "feat: add profiles and skills"
```

## Task 4: Portfolio uploads and file safety

**Files:**
- Create: `backend/app/models/portfolio.py`
- Create: `backend/app/schemas/portfolio.py`
- Create: `backend/app/services/uploads.py`
- Create: `backend/app/services/portfolios.py`
- Create: `backend/app/api/v1/portfolios.py`
- Modify: `backend/app/api/v1/router.py`
- Create: `backend/uploads/.gitkeep`
- Create: `backend/tests/test_portfolios.py`

- [x] **Step 1: Write failing upload tests**

Create multipart tests for a permitted PNG, a rejected executable, an oversized stream, a skill owned by another student, and portfolio deletion. Assert the stored filename is generated rather than using `../../photo.png`.

```python
def test_upload_portfolio_adds_skill_evidence(client, student_headers, student_skill, tiny_png):
    response = client.post(
        "/api/v1/portfolios",
        headers=student_headers,
        data={"skill_id": student_skill.id, "title": "校园海报", "description": "迎新视觉"},
        files={"file": ("poster.png", tiny_png, "image/png")},
    )
    assert response.status_code == 201
    assert response.json()["file_url"].startswith("/uploads/")
```

- [x] **Step 2: Run and verify RED**

```powershell
./.venv/Scripts/python -m pytest tests/test_portfolios.py -v
```

- [x] **Step 3: Implement safe local uploads**

Allow image, video, PDF, DOC/DOCX, PPT/PPTX MIME/extension pairs. Stream to disk while counting bytes; stop and remove the partial file when the configured limit is exceeded. Generate `uuid4` filenames and return relative `/uploads/<name>` URLs. On portfolio deletion, remove the database record and its owned local file.

- [x] **Step 4: Verify GREEN**

```powershell
./.venv/Scripts/python -m pytest tests/test_portfolios.py -v
./.venv/Scripts/python -m pytest -q
```

- [x] **Step 5: Commit**

```powershell
git add backend/app backend/tests backend/uploads/.gitkeep
git commit -m "feat: add portfolio uploads"
```

## Task 5: Projects, public filters, and admin approval

**Files:**
- Create: `backend/app/models/project.py`
- Create: `backend/app/schemas/project.py`
- Create: `backend/app/services/projects.py`
- Create: `backend/app/api/v1/projects.py`
- Create: `backend/app/api/v1/admin.py`
- Create: `backend/app/schemas/admin.py`
- Modify: `backend/app/api/v1/router.py`
- Create: `backend/tests/test_projects_admin.py`

- [x] **Step 1: Write failing project tests**

Cover requester creation, student creation rejection, creator-only editing while pending, admin approval/rejection, non-admin audit rejection, and public filtering by keyword/category/skill/deadline.

```python
def test_approved_project_appears_in_public_hall(client, requester_project, admin_headers):
    client.post(f"/api/v1/admin/projects/{requester_project.id}/approve", headers=admin_headers)
    response = client.get("/api/v1/projects", params={"skill": "摄影"})
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [requester_project.id]
```

- [x] **Step 2: Run and verify RED**

```powershell
./.venv/Scripts/python -m pytest tests/test_projects_admin.py -v
```

- [x] **Step 3: Implement project and admin endpoints**

Expose public `GET /projects` and `GET /projects/{id}`; requester `POST /projects`, `GET /projects/mine`, `PATCH /projects/{id}`; admin `GET /admin/stats`, `GET /admin/users`, `PATCH /admin/users/{id}/status`, `GET /admin/projects`, and approve/reject actions. Use an association table for required skill names. Keep `audit_status` independent from `lifecycle_status`.

- [x] **Step 4: Verify GREEN**

```powershell
./.venv/Scripts/python -m pytest tests/test_projects_admin.py -v
./.venv/Scripts/python -m pytest -q
```

- [x] **Step 5: Commit**

```powershell
git add backend/app backend/tests
git commit -m "feat: add projects and moderation"
```

## Task 6: Applications and project lifecycle

**Files:**
- Create: `backend/app/models/application.py`
- Create: `backend/app/schemas/application.py`
- Create: `backend/app/services/applications.py`
- Create: `backend/app/api/v1/applications.py`
- Modify: `backend/app/services/projects.py`
- Modify: `backend/app/api/v1/projects.py`
- Modify: `backend/app/api/v1/router.py`
- Create: `backend/tests/test_applications.py`

- [ ] **Step 1: Write failing workflow tests**

Test student application, duplicate rejection, requester-role rejection, expired-project rejection, creator-only acceptance/rejection, start-without-member rejection, and ordered transitions `recruiting → in_progress → awaiting_review`.

```python
def test_project_owner_accepts_application(client, requester_headers, pending_application):
    response = client.post(f"/api/v1/applications/{pending_application.id}/accept", headers=requester_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
```

- [ ] **Step 2: Run and verify RED**

```powershell
./.venv/Scripts/python -m pytest tests/test_applications.py -v
```

- [ ] **Step 3: Implement application and transition services**

Expose `POST /projects/{id}/applications`, `GET /applications/mine`, `GET /projects/{id}/applications`, accept/reject actions, and `POST /projects/{id}/start` plus `POST /projects/{id}/finish-work`. Enforce ownership and exact predecessor state in one service function.

- [ ] **Step 4: Verify GREEN**

```powershell
./.venv/Scripts/python -m pytest tests/test_applications.py -v
./.venv/Scripts/python -m pytest -q
```

- [ ] **Step 5: Commit**

```powershell
git add backend/app backend/tests
git commit -m "feat: add applications and project workflow"
```

## Task 7: Reviews and skill-growth recalculation

**Files:**
- Create: `backend/app/models/review.py`
- Create: `backend/app/schemas/review.py`
- Create: `backend/app/services/growth.py`
- Create: `backend/app/services/reviews.py`
- Create: `backend/app/api/v1/reviews.py`
- Modify: `backend/app/services/portfolios.py`
- Modify: `backend/app/api/v1/router.py`
- Create: `backend/tests/test_reviews_growth.py`

- [ ] **Step 1: Write failing review and level tests**

Write separate tests for score range, non-owner, non-accepted student, duplicate review, application completion, automatic project completion after all accepted students are reviewed, and these growth boundaries:

```python
@pytest.mark.parametrize(("score", "level"), [(0, 1), (19, 1), (20, 2), (59, 2), (60, 3), (119, 3), (120, 4)])
def test_level_thresholds(score, level):
    assert level_for_score(score) == level

def test_growth_combines_portfolio_project_and_review(db_session, completed_evidence):
    skill = recalculate_skill(db_session, completed_evidence.skill_id)
    assert skill.growth_score == 42  # 10 portfolio + 20 project + 4.0 average * 3
    assert skill.level == 2
```

- [ ] **Step 2: Run and verify RED**

```powershell
./.venv/Scripts/python -m pytest tests/test_reviews_growth.py -v
```

- [ ] **Step 3: Implement one authoritative growth service**

Implement:

```python
def level_for_score(score: int) -> int:
    if score >= 120:
        return 4
    if score >= 60:
        return 3
    if score >= 20:
        return 2
    return 1
```

`recalculate_skill` must count portfolios for the skill, completed accepted applications whose project required skills match the normalized skill name, and the matching reviews' four-score average multiplied by three. Call it after portfolio create/delete and review create. Expose `POST /projects/{project_id}/reviews/{student_id}` and public/student review reads.

- [ ] **Step 4: Verify GREEN**

```powershell
./.venv/Scripts/python -m pytest tests/test_reviews_growth.py -v
./.venv/Scripts/python -m pytest -q --cov=app --cov-report=term-missing
```

- [ ] **Step 5: Commit**

```powershell
git add backend/app backend/tests
git commit -m "feat: add reviews and skill growth"
```

## Task 8: Idempotent demo data

**Files:**
- Create: `backend/app/seed.py`
- Create: `backend/tests/test_seed.py`
- Modify: `backend/pyproject.toml`

- [ ] **Step 1: Write the failing seed test**

```python
def test_seed_is_idempotent(db_session):
    seed_database(db_session)
    first_counts = table_counts(db_session)
    seed_database(db_session)
    assert table_counts(db_session) == first_counts
    assert first_counts["users"] >= 4
    assert first_counts["projects"] >= 4
```

- [ ] **Step 2: Run and verify RED**

```powershell
./.venv/Scripts/python -m pytest tests/test_seed.py -v
```

- [ ] **Step 3: Implement demo identities and scenarios**

Seed `admin/Student123!`, `student/Student123!`, `designer/Student123!`, and `campus_org/Student123!` with clearly documented usernames. Include approved recruiting, pending-audit, in-progress, and completed projects; skills, local placeholder file URLs, accepted/rejected applications, and reviews. Identify records by stable unique usernames/titles so reruns do not duplicate data.

- [ ] **Step 4: Verify GREEN and run the seed command against a fresh file DB**

```powershell
./.venv/Scripts/python -m pytest tests/test_seed.py -v
Remove-Item -LiteralPath ./skillhub.db -ErrorAction SilentlyContinue
./.venv/Scripts/python -m app.seed
./.venv/Scripts/python -m app.seed
```

Expected: both seed runs exit 0 and record counts remain stable.

- [ ] **Step 5: Commit**

```powershell
git add backend
git commit -m "feat: add SkillHub demo data"
```

## Task 9: Frontend scaffold, visual system, and authentication

**Files:**
- Create: `frontend/` via Vite React TypeScript scaffold
- Create: `frontend/src/styles/index.css`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/types.ts`
- Create: `frontend/src/app/providers.tsx`
- Create: `frontend/src/app/router.tsx`
- Create: `frontend/src/features/auth/auth-store.tsx`
- Create: `frontend/src/features/auth/ProtectedRoute.tsx`
- Create: `frontend/src/features/auth/LoginPage.tsx`
- Create: `frontend/src/features/auth/RegisterPage.tsx`
- Create: `frontend/src/components/AppShell.tsx`
- Create: `frontend/src/test/setup.ts`
- Create: `frontend/src/features/auth/auth-store.test.tsx`

- [ ] **Step 1: Scaffold and install frontend dependencies**

```powershell
npm create vite@latest frontend -- --template react-ts
Set-Location frontend
npm install
npm install react-router-dom @tanstack/react-query lucide-react clsx
npm install -D tailwindcss@3 postcss autoprefixer vitest jsdom msw @testing-library/react @testing-library/jest-dom @testing-library/user-event
npx tailwindcss init -p
```

Add `"test": "vitest"` to `package.json`, configure `environment: "jsdom"` and `setupFiles: ["./src/test/setup.ts"]` in `vite.config.ts`, and start/reset/close the MSW server from the Vitest setup file.

- [ ] **Step 2: Write a failing auth-state test**

```tsx
it('restores the current user when a saved token exists', async () => {
  localStorage.setItem('skillhub_token', 'saved-token')
  server.use(http.get('/api/v1/auth/me', () => HttpResponse.json({ id: 1, username: 'student', role: 'student' })))
  render(<AuthProvider><AuthProbe /></AuthProvider>)
  expect(await screen.findByText('student')).toBeInTheDocument()
})
```

- [ ] **Step 3: Run and verify RED**

```powershell
npm run test -- --run src/features/auth/auth-store.test.tsx
```

- [ ] **Step 4: Implement providers, API client, routes, and auth screens**

The API client must attach the saved Bearer token, parse FastAPI `detail`, clear auth on 401, and expose typed helpers. `ProtectedRoute` accepts allowed roles. Implement the “成长档案馆” variables in CSS: warm paper background, ink green, amber, brick, serif display type, subtle paper grid, square/low-radius cards, visible focus states, and reduced-motion rules.

- [ ] **Step 5: Verify GREEN, typecheck, and build**

```powershell
npm run test -- --run
npm run build
```

- [ ] **Step 6: Commit**

```powershell
git add frontend
git commit -m "feat: scaffold SkillHub frontend and auth"
```

## Task 10: Public discovery pages

**Files:**
- Create: `frontend/src/features/public/HomePage.tsx`
- Create: `frontend/src/features/public/ProjectsPage.tsx`
- Create: `frontend/src/features/public/ProjectDetailPage.tsx`
- Create: `frontend/src/features/public/TalentPage.tsx`
- Create: `frontend/src/features/public/ProfilePage.tsx`
- Create: `frontend/src/components/ProjectCard.tsx`
- Create: `frontend/src/components/SkillLevel.tsx`
- Create: `frontend/src/components/RatingSummary.tsx`
- Create: `frontend/src/features/public/ProjectsPage.test.tsx`

- [ ] **Step 1: Write failing discovery tests**

Test that skill/category filters produce the expected query parameters, expired projects render a closed application state, and a public profile renders skill level, portfolio, project history, and review averages.

- [ ] **Step 2: Run and verify RED**

```powershell
npm run test -- --run src/features/public/ProjectsPage.test.tsx
```

- [ ] **Step 3: Implement public pages with real API data**

Use TanStack Query keys that include filters. The homepage must show a numbered growth-loop hero, recommended project cards, popular skill counts, and highlighted students. Use semantic headings, keyboard-accessible controls, skeleton loading, and useful empty states.

- [ ] **Step 4: Verify GREEN and build**

```powershell
npm run test -- --run
npm run build
```

- [ ] **Step 5: Commit**

```powershell
git add frontend/src
git commit -m "feat: add public project and talent discovery"
```

## Task 11: Student workspace

**Files:**
- Create: `frontend/src/features/student/StudentLayout.tsx`
- Create: `frontend/src/features/student/OverviewPage.tsx`
- Create: `frontend/src/features/student/ProfileEditPage.tsx`
- Create: `frontend/src/features/student/SkillsPage.tsx`
- Create: `frontend/src/features/student/PortfoliosPage.tsx`
- Create: `frontend/src/features/student/ApplicationsPage.tsx`
- Create: `frontend/src/features/student/SkillsPage.test.tsx`
- Modify: `frontend/src/app/router.tsx`

- [ ] **Step 1: Write failing student-workspace tests**

Test create-skill submission, duplicate-name error display, multipart portfolio upload progress, delete confirmation behavior, and grouping applications by status.

- [ ] **Step 2: Run and verify RED**

```powershell
npm run test -- --run src/features/student/SkillsPage.test.tsx
```

- [ ] **Step 3: Implement student screens**

The overview shows each skill's level, score, and next threshold. Skills page shows the three evidence sources. Portfolio upload requires a skill and file. Applications page links back to project details and reflects pending/accepted/rejected/finished states.

- [ ] **Step 4: Verify GREEN and build**

```powershell
npm run test -- --run
npm run build
```

- [ ] **Step 5: Commit**

```powershell
git add frontend/src
git commit -m "feat: add student skill workspace"
```

## Task 12: Requester workflow

**Files:**
- Create: `frontend/src/features/requester/RequesterLayout.tsx`
- Create: `frontend/src/features/requester/OverviewPage.tsx`
- Create: `frontend/src/features/requester/ProjectFormPage.tsx`
- Create: `frontend/src/features/requester/MyProjectsPage.tsx`
- Create: `frontend/src/features/requester/ApplicantsPage.tsx`
- Create: `frontend/src/features/requester/ReviewPage.tsx`
- Create: `frontend/src/features/requester/MyProjectsPage.test.tsx`
- Modify: `frontend/src/app/router.tsx`

- [ ] **Step 1: Write failing requester-workflow tests**

Test required skill entry, pending-audit messaging, ownership action visibility, accept/reject mutations, state transition button availability, four scores constrained to 1–5, and duplicate review error display.

- [ ] **Step 2: Run and verify RED**

```powershell
npm run test -- --run src/features/requester/MyProjectsPage.test.tsx
```

- [ ] **Step 3: Implement requester pages**

Project cards must distinguish audit status from lifecycle status. Applicants page shows student skills, work samples, application message, and clear accept/reject actions. Review page shows one form per accepted student and completion progress.

- [ ] **Step 4: Verify GREEN and build**

```powershell
npm run test -- --run
npm run build
```

- [ ] **Step 5: Commit**

```powershell
git add frontend/src
git commit -m "feat: add requester project workflow"
```

## Task 13: Admin workspace

**Files:**
- Create: `frontend/src/features/admin/AdminLayout.tsx`
- Create: `frontend/src/features/admin/OverviewPage.tsx`
- Create: `frontend/src/features/admin/UsersPage.tsx`
- Create: `frontend/src/features/admin/ProjectsPage.tsx`
- Create: `frontend/src/features/admin/ProjectsPage.test.tsx`
- Modify: `frontend/src/app/router.tsx`

- [ ] **Step 1: Write failing admin tests**

Test that pending projects render approve/reject controls, approved projects do not, user status changes require confirmation, and non-admin routes redirect to 403.

- [ ] **Step 2: Run and verify RED**

```powershell
npm run test -- --run src/features/admin/ProjectsPage.test.tsx
```

- [ ] **Step 3: Implement admin overview and moderation**

Display user/project/application/completion counts, a filterable user table, and a filterable project table. Keep actions compact and clearly labeled; show mutation results with toasts and refresh affected queries.

- [ ] **Step 4: Verify GREEN and build**

```powershell
npm run test -- --run
npm run build
```

- [ ] **Step 5: Commit**

```powershell
git add frontend/src
git commit -m "feat: add SkillHub admin workspace"
```

## Task 14: End-to-end integration, documentation, and final verification

**Files:**
- Create: `README.md`
- Create: `frontend/.env.example`
- Modify: `backend/.env.example`
- Modify: `frontend/vite.config.ts`
- Modify: `backend/app/main.py`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/app/router.tsx`
- Modify: `frontend/src/styles/index.css`

- [ ] **Step 1: Write the runbook before final verification**

README must contain:

- Product purpose and MVP scope.
- Windows PowerShell setup for backend and frontend.
- Environment file instructions.
- Database seed command.
- Demo usernames and password.
- Exact test/build commands.
- A six-step classroom demo script: admin approval → student application → requester acceptance → project start/finish → review → skill-level update.
- Clear second-stage extension notes for PostgreSQL, object storage, and AI agents.

- [ ] **Step 2: Configure local development integration**

Set Vite `/api` and `/uploads` proxies to FastAPI. Confirm frontend URLs use relative API paths so the same build can be reverse-proxied later. Add `.env.example` values without real secrets.

- [ ] **Step 3: Run fresh backend verification**

```powershell
Set-Location backend
./.venv/Scripts/python -m pytest -q --cov=app --cov-report=term-missing
./.venv/Scripts/python -m app.seed
```

Expected: zero failures; seed exits 0.

- [ ] **Step 4: Run fresh frontend verification**

```powershell
Set-Location ../frontend
npm run test -- --run
npm run build
```

Expected: zero failed tests, TypeScript compilation succeeds, Vite production build exits 0.

- [ ] **Step 5: Run the application and verify the real workflow in the browser**

Start FastAPI and Vite in separate terminals. Use the seeded accounts to verify all six classroom-demo transitions and inspect desktop plus 375px responsive layout. Check browser console and server output for errors.

- [ ] **Step 6: Review requirements line by line**

Confirm the design spec sections for authentication, student profile, portfolio, project publish/audit, application, completion/review, level display, admin minimum, responsive UI, local upload, demo data, and extension boundaries each have a working screen and API.

- [ ] **Step 7: Commit the verified delivery**

```powershell
git add README.md backend frontend
git commit -m "docs: add SkillHub setup and demo guide"
git status --short
```

Expected: clean working tree after the final commit.

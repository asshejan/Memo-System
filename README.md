# Inter-Office Memo Management System

A multi-tenant web application for creating office memos and routing them through a
sequential approval/review workflow, with comments, attachments, notifications, search,
delegation, versioning, audit logging, and PDF export.

Built for CSE226 "Foundations of Vibe Coding" (North South University).

**Live deployment**: https://memo-system-nu.vercel.app (frontend) /
https://memo-system-api.onrender.com (API). Demo login: `admin@acme.example` /
`Password123!` (see the full account table below).

## Tech stack

- **Backend**: FastAPI (Python 3.11), SQLAlchemy 2.0 + Alembic, PostgreSQL, JWT cookie auth (`passlib`/`bcrypt`), `reportlab` for PDF export.
- **Frontend**: Next.js 16 (App Router, TypeScript), Tailwind CSS. All authenticated pages are client components that call the backend through a same-origin `/api/*` rewrite proxy — this keeps the session cookie same-site (`SameSite=Lax`) with no CORS complexity.
- **Database**: PostgreSQL (developed against Neon; any standard Postgres works).

## Repository layout

```
backend/    FastAPI application, SQLAlchemy models, Alembic migrations, seed script
frontend/   Next.js application
```

## Prerequisites

- Python 3.11+ (the code uses modern `X | None` union type-hint syntax, which requires 3.10+; built and tested on 3.11)
- Node.js 20+ and npm
- A PostgreSQL database (e.g. a free [Neon](https://neon.tech) or [Supabase](https://supabase.com) project)

## 1. Backend setup

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env:
#   DATABASE_URL      postgresql+psycopg2://... (your Postgres connection string;
#                      note the +psycopg2 driver segment — Neon/Supabase give you a
#                      plain postgresql:// URL, prepend +psycopg2 to the scheme)
#   JWT_SECRET         a long random string, e.g. `python -c "import secrets; print(secrets.token_urlsafe(48))"`
#   FRONTEND_ORIGIN     http://localhost:3000 for local dev

alembic upgrade head             # creates all tables
python -m app.seed               # creates two demo organizations with seed users (see below)

uvicorn app.main:app --reload --port 8000
```

Backend is now running at `http://localhost:8000`. Interactive API docs: `http://localhost:8000/docs`.

### Demo accounts created by the seed script

Password for every seeded account: `Password123!`

| Organization | Admin | Employee | Dept Head | Finance Manager | Director |
|---|---|---|---|---|---|
| Acme (`acme`) | admin@acme.example | employee@acme.example | depthead@acme.example | finance@acme.example | director@acme.example |
| Globex (`globex`) | admin@globex.example | employee@globex.example | depthead@globex.example | finance@globex.example | director@globex.example |

The two organizations exist specifically to demonstrate tenant isolation — a Globex user
can never see an Acme memo, and vice versa.

## 2. Frontend setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local: BACKEND_URL=http://localhost:8000 (or wherever the backend is running)

npm run dev
```

Frontend is now running at `http://localhost:3000`. Sign in with a seed account, or use
"Create one" on the login page to self-register a brand new organization.

## 3. Running the demonstration scenario

1. Go to `/signup`, create a new organization (or log in as `admin@acme.example`).
2. As an admin, add a couple more users under Admin → Users, and a department under Admin → Departments.
3. Log in as a regular user, go to "New memo", fill in subject/body, save as draft.
4. On the memo's detail page, build an approval sequence (or pick the seeded "Purchase Request" template) and submit.
5. Log in as each workflow participant in turn (their inbox will show the memo) and approve / reject / request changes / comment.
6. Watch the memo's status, current step, and timeline update after each action.
7. Try logging in as a user from the *other* seeded organization and confirm you get a 404 when visiting the same memo URL directly — this demonstrates tenant isolation is enforced server-side, not just hidden in the UI.

## Building for production

```bash
cd frontend && npm run build && npm run start   # or deploy to Vercel
cd backend  && uvicorn app.main:app --host 0.0.0.0 --port $PORT   # or deploy to Render/Railway/Fly
```

See `docs/project-documentation.md` for architecture, database design, security notes,
known limitations, and deployment URLs.

## Submission checklist (course requirement, not app functionality)

Before submitting, per the course's spec sections 26–27:

- [x] Deployed: frontend on Vercel (https://memo-system-nu.vercel.app), backend on Render (https://memo-system-api.onrender.com), database on Neon. Both Vercel and Render are connected to this repo's `main` branch for auto-deploy on push.
- [ ] Export this Claude Code conversation's complete prompt/response history (the session used to build this project) and add its link to `docs/project-documentation.md` §27.1. Do not include any secrets (API keys, `.env` contents, database passwords) in that export — redact if any appear.
- [ ] Prepare a ZIP of this repository (excluding `backend/venv`, `frontend/node_modules`, and any `.env`/`.env.local` files, all already gitignored) for the source-code submission link, or simply link the GitHub repo.
- [ ] Provide demonstration credentials (the seeded accounts in this README work) and confirm the deployed app is reachable.

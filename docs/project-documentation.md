# Inter-Office Memo Management System — Project Documentation

CSE226 "Foundations of Vibe Coding" — Summer 2026, North South University

## 1. System Overview

A multi-tenant web application for creating internal office memos and routing them
through a configurable, sequential approval/review workflow. Each organization (tenant)
manages its own departments, users, memo categories, and workflow templates, with strict
data isolation between organizations. A memo author defines an ordered list of
participants; the memo moves through that sequence one step at a time, with each
participant able to approve, reject, request changes, or comment. The system tracks the
complete history of every memo (comments, approvals, versions, timestamps) and surfaces
it as a chronological timeline.

## 2. Requirements Implemented

Implemented in full: multi-tenant organizations with self-service signup; department and
user management (invite, activate/deactivate, role/department assignment); authentication
(login/logout/change password, cookie-based sessions) and role-based authorization
(org admin vs. regular user) enforced server-side on every endpoint; memo CRUD with
drafts, auto-generated memo numbers, priority, category; sequential workflow engine
(approve / reject / request changes / comment, with only the current participant able to
act, and delegates able to act on an assignee's behalf); memo statuses per spec section 5;
inbox / my memos / completed views; memo detail page with workflow state, comments, and
a synthesized activity timeline; comments (general/approval/rejection/change-request,
immutable once created); file attachments (upload/download/delete, size and MIME-type
restricted, served only through an authenticated endpoint — never a guessable static URL);
in-app notifications with unread tracking; search/filter scoped to the caller's
organization and authorized memos; user and org-admin dashboards; department and memo
category management; reusable workflow templates; delegation (time-bounded, records both
delegate and delegating user on every action taken); memo versioning on resubmission;
audit log of the events listed in spec section 18; basic reporting (counts by status/
department/category, average completion time, pending/rejected/change-request counts);
PDF export of a memo including its approval history and comments; responsive UI with a
mobile navigation drawer.

Not fully implemented — see §9 Known Limitations: password-reset-via-email (a
"reset forgotten password" flow requires an email delivery service, which was out of
scope given the timeline), and email notifications (in-app notifications are implemented;
email is optional per spec §10 "may additionally support").

## 3. Technology Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (ORM), Alembic (migrations),
  Pydantic v2 (request/response validation), `passlib`+`bcrypt` (password hashing),
  `python-jose` (JWT), `reportlab` (PDF generation).
- **Frontend**: TypeScript, Next.js 16 (App Router), React 19, Tailwind CSS 4.
- **Database**: PostgreSQL (developed against Neon serverless Postgres).
- **Authentication**: JWT stored in an `httpOnly`, `Secure`, `SameSite=Lax` cookie, issued
  and verified entirely by the backend.
- **File storage**: attachment binary content is stored as `bytea` directly in Postgres
  alongside metadata, rather than a separate object-storage service — see §5 and §9.
- **Hosting**: frontend on Vercel, backend on Render, database on Neon.
- **AI coding tool used**: Claude Code (Anthropic), used throughout for architecture,
  backend, frontend, debugging, and documentation — see §8.

## 4. System Architecture

```
 Browser
   │  HTTPS
   ▼
 Next.js app (Vercel)
   │  same-origin /api/* requests (rewrite proxy → no CORS, cookie stays same-site)
   ▼
 FastAPI backend (Render)
   │  SQLAlchemy / psycopg2
   ▼
 PostgreSQL (Neon) — also stores attachment binary data
```

The frontend never talks to the backend's public URL directly from the browser; every
`/api/*` request is same-origin and gets rewritten server-side by Next.js
(`next.config.ts` → `rewrites()`) to the FastAPI backend URL. This was a deliberate
architectural choice: it means the session cookie can be a plain `SameSite=Lax` cookie
with no cross-site cookie or CORS configuration to get right under time pressure, while
still keeping the two services independently deployable.

Major backend components: `app/routers/*` (one router per resource — auth, admin,
directory, memos, attachments, inbox, notifications, search, delegations, audit, reports,
pdf_export), `app/services/*` (tenant-scoping helper, the workflow state machine, audit
logging, notification creation, memo-number generation), `app/models/*` (SQLAlchemy ORM
models), `app/schemas/*` (Pydantic request/response contracts).

## 5. Database Design

Every tenant-scoped table carries an `organization_id` foreign key: `departments`,
`users`, `memo_categories`, `workflow_templates` (+ `workflow_template_positions`),
`memos`, `notifications`, `audit_logs`, `delegations`. A memo's workflow is modeled as
`workflow_instances` (one per memo, tracks `current_step_index` and overall status) with
child rows in `workflow_steps` (one per participant position, tracking that step's own
status, who acted, when, and their comment). `memo_versions` snapshots the memo's prior
subject/body every time it is resubmitted after a change request. `comments` and
`attachments` both hang off `memo_id`; attachments store the file's bytes directly
(`LargeBinary`/`bytea`) plus filename/MIME-type/size/uploader metadata.

**How multi-tenancy is implemented**: at the application layer, not via Postgres
row-level security. Every authenticated request resolves the caller's `organization_id`
from their session (`get_current_user` dependency), and every query that touches a
tenant-scoped table filters by it — either through the shared
`services/scoping.get_org_scoped_or_404` helper (fetch-by-id with an organization check
that 404s instead of leaking existence) or an explicit `.where(Model.organization_id ==
current_user.organization_id)` clause. A memo is additionally only *visible* to its
author, its org's admins, or a current/past workflow participant on it
(`services/authorization.assert_can_view_memo`) — same-organization users with no
connection to a given memo cannot open it just because they share a tenant.

## 6. Workflow Design

A memo's workflow is a strict, ordered sequence of `WorkflowStep` rows created at submit
time (either from a `WorkflowTemplate`'s positions or a custom ad-hoc sequence the author
builds in the UI). Exactly one step is ever `current`; every action endpoint
(`/memos/{id}/approve|reject|request-changes`) re-derives the current step from the
`WorkflowInstance.current_step_index` server-side and checks that the acting user is
either that step's `assigned_user_id` or an active delegate of that user
(`services/workflow_engine.resolve_actor_for_step`) — the frontend hides action buttons
from the wrong user, but the backend independently enforces the same rule, so hiding the
button is a UX convenience, not the security boundary.

- **Approve** marks the step approved and either advances `current_step_index` to the
  next step (notifying its assignee) or, if it was the last step, marks the whole memo
  `approved` and notifies the author. This also serves as the spec's "Forward/Complete
  Review" action.
- **Reject** terminates the workflow immediately; the memo becomes `rejected` (terminal).
- **Request Changes** requires a comment, sets the memo to `changes_requested`, and
  returns control to the author.
- **Resubmit** (author only, only while `changes_requested`) snapshots the previous
  subject/body into `memo_versions`, applies the edits, and — as a deliberate
  simplification — **restarts the workflow from the first step** rather than resuming at
  the step that requested changes. The spec's own worked example is ambiguous on this
  point; restarting was chosen because it guarantees every participant reviews the
  version they're approving, and it's a strictly simpler, more auditable state machine
  than resuming mid-sequence. This is documented as a deliberate design decision, not an
  oversight.

## 7. Security

- **Authentication**: bcrypt password hashing (cost factor via `passlib`, pinned to
  `bcrypt==4.0.1` for compatibility), JWT session tokens in an `httpOnly` cookie
  (inaccessible to JavaScript, mitigating XSS token theft), `Secure` flag enabled in
  production so the cookie is never sent over plain HTTP.
- **Authorization**: every protected endpoint depends on `get_current_user` (rejects
  missing/invalid/expired tokens and deactivated accounts) and, where relevant,
  `require_org_admin`. Workflow actions additionally re-check "is it actually this user's
  turn" server-side on every call, independent of what the UI shows.
- **Tenant isolation**: enforced at the application layer as described in §5, treated as
  a first-class requirement rather than a UI concern — verified with an explicit
  cross-tenant test (see §10).
- **File security**: attachments are validated against an allow-list of MIME types and a
  size cap (`ATTACHMENT_MAX_BYTES`) before being stored; they are served only through an
  authenticated, authorized `GET /memos/{id}/attachments/{id}/download` endpoint that
  re-checks memo visibility, so a valid session cookie for the wrong organization or a
  guessed attachment ID both fail closed.
- **Input validation**: all request bodies are typed Pydantic v2 models; invalid input is
  rejected with a 422 before it reaches business logic.
- **Error handling**: HTTP exceptions return a short `detail` string; unhandled
  exceptions are not caught and re-exposed with internals (FastAPI's default handler
  avoids leaking stack traces to the client in production).
- **Injection protection**: all database access goes through SQLAlchemy's parameterized
  query builder — no raw/string-interpolated SQL anywhere in the codebase.
- **Transport security**: HTTPS is provided by the hosting platforms (Vercel and Render
  both terminate TLS in front of the application).

## 8. Vibe-Coding Process

**AI tool used**: Claude Code (Anthropic), for essentially the entire implementation —
architecture and planning, backend code, frontend code, debugging, and this
documentation.

**How requirements were communicated**: the full PDF requirements specification was
provided directly to the assistant, which read it in full before designing the data
model, API surface, and page list, then produced a written build plan (prioritized by
spec section) that was reviewed and approved before implementation began.

**How generated code was evaluated**: after each major layer was written (models →
schemas → routers → workflow engine → frontend pages), the assistant ran real
verification rather than relying on code review alone: `tsc --noEmit` and `next build`
for the frontend on every batch of new pages; a live backend process against a real
Postgres database (Neon) with `alembic revision --autogenerate` + `alembic upgrade head`
to prove the models actually produce a valid schema; a seeded two-organization dataset;
and a scripted `curl`-based walkthrough of the real HTTP API (login → create draft →
submit with a workflow → out-of-turn action rejected → cross-tenant access rejected →
approval → completion) run against the live server, not mocked.

**How errors were identified and corrected**: the initial `python-jose`/SQLAlchemy stack
failed to import under the machine's system Python 3.9 because the code uses `X | None`
type-hint syntax (PEP 604, requires 3.10+); this was diagnosed from the traceback and
fixed by installing an isolated Python 3.11 via `uv` rather than rewriting every
annotation to `Optional[X]`. A `passlib`/`bcrypt` version-compatibility bug
(`bcrypt>=4.1`'s removed internals broke `passlib 1.7.4`'s backend self-test, raising
`ValueError: password cannot be longer than 72 bytes` on the *first* hash call
regardless of password length) was diagnosed from a live traceback during the seed run
and fixed by pinning `bcrypt==4.0.1` in `requirements.txt`. A submit-workflow endpoint bug
(`AttributeError: 'UUID' object has no attribute 'id'`, from mistakenly treating a
single-column `select(User.id)` result as if it returned ORM objects) was caught by the
same live `curl` walkthrough and fixed immediately, then grepped for elsewhere in the
codebase to confirm it wasn't repeated.

**How the team verified the system satisfies the requirements**: by exercising the real
HTTP API end-to-end against a real database rather than trusting generated code — see the
specific checks in §10 below, several of which (out-of-turn action, cross-tenant access)
directly target the spec's explicit security requirements rather than just the happy
path.

## 9. Known Limitations

- **Password reset via email** is not implemented (login, logout, change-password, and
  profile update are). A genuine "forgot password" flow needs an email-delivery service,
  which was descoped given the project timeline; an org admin can still get a locked-out
  user back in by creating a fresh account or (if added) resetting their password
  directly.
- **Email notifications** are not implemented — only in-app notifications (spec marks
  email as optional, "may additionally support").
- **Attachment storage** is Postgres `bytea` rather than a dedicated object-storage
  service (S3/Supabase Storage/etc.). This was a deliberate scope trade-off to avoid
  provisioning and wiring up an additional external service under time pressure; it is
  fine at the file-size cap enforced (10MB/file) but would not scale to large files or
  very high attachment volume.
- **Workflow resubmission restarts the sequence from step 1** rather than resuming from
  the step that requested changes — see the design rationale in §6.
- **Rich text formatting** in the memo body is plain text in this build rather than a
  WYSIWYG/rich-text editor; the spec asks for "basic rich-text formatting" as a should-level
  item.
- **Memo number sequencing** uses a simple per-organization row count rather than a
  database sequence/lock, which is not safe under concurrent submissions racing for the
  same organization (acceptable for a demo; would need a `SELECT ... FOR UPDATE` or a
  Postgres sequence per organization for production use under real concurrency).

## 10. Verification Performed

- Full backend import/startup check against a live Postgres connection.
- `alembic revision --autogenerate` produced the complete expected schema (all 15
  tables) with no manual corrections needed beyond the model definitions themselves.
- Seeded two organizations (Acme, Globex), five users each, via `python -m app.seed`.
- Scripted `curl` walkthrough against the running backend: login as four different
  seeded users (including a second-organization admin) → author creates a draft memo →
  submits it with a one-step workflow → the assigned participant's inbox correctly shows
  it → an unauthorized user (not the current step's assignee) attempting to approve gets
  **HTTP 403** → a user from the *other* organization requesting the same memo URL gets
  **HTTP 404** (not 403 — existence itself is not leaked across tenants) → the correct
  participant approves it → the memo's status and step status both correctly flip to
  `approved`.
- Frontend: `npx tsc --noEmit` (zero errors) and `next build` (all 21 routes compile and
  prerender successfully) after every major batch of pages.
- Verified the browser-facing cookie/session flow specifically (not just the raw
  backend API) by hitting `/api/auth/login` and `/api/auth/me` through the Next.js dev
  server's rewrite proxy with a cookie jar, confirming the `httpOnly` session cookie set
  by the FastAPI backend round-trips correctly through the same-origin proxy exactly as
  it would from real browser JavaScript.

## Deployment Information

- **Live System**: https://memo-system-nu.vercel.app (frontend, Vercel) — backed by
  https://memo-system-api.onrender.com (API, Render) and a Neon PostgreSQL database.
  Both are connected to the `main` branch of the GitHub repo below, so future pushes
  auto-deploy.
- **Source Code**: https://github.com/asshejan/Memo-System
- **Installation Instructions**: `README.md` at the repository root
- **Demonstration accounts**: see the table in `README.md` ("Demo accounts created by
  the seed script") — password `Password123!` for every seeded account, across two
  separate organizations (`acme`, `globex`) to demonstrate tenant isolation.
- **AI Prompt/Response History**: _the student should export this Claude Code
  conversation and add its link here before submission — see the note at the end of
  `README.md`'s task list_

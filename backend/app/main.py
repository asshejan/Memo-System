from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import (
    auth, profile, admin, directory, memos, attachments,
    inbox, notifications, search, delegations, audit, reports, pdf_export,
)

app = FastAPI(title="Inter-Office Memo Management System API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(admin.router)
app.include_router(directory.router)
app.include_router(memos.router)
app.include_router(attachments.router)
app.include_router(inbox.router)
app.include_router(notifications.router)
app.include_router(search.router)
app.include_router(delegations.router)
app.include_router(audit.router)
app.include_router(reports.router)
app.include_router(pdf_export.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password, create_access_token
from app.db import get_db
from app.models.organization import Organization
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.auth import OrgSignupRequest, LoginRequest, ChangePasswordRequest, UserOut
from app.services.audit import log_event

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, user_id: str) -> None:
    token = create_access_token(subject=user_id)
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup_organization(payload: OrgSignupRequest, response: Response, db: Session = Depends(get_db)):
    existing_org = db.execute(
        select(Organization).where(Organization.identifier == payload.organization_identifier)
    ).scalars().first()
    if existing_org:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization identifier is already taken")

    existing_user = db.execute(select(User).where(User.email == payload.admin_email)).scalars().first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already registered")

    org = Organization(name=payload.organization_name, identifier=payload.organization_identifier)
    db.add(org)
    db.flush()

    admin = User(
        organization_id=org.id,
        name=payload.admin_name,
        email=payload.admin_email,
        password_hash=hash_password(payload.admin_password),
        role=UserRole.org_admin,
    )
    db.add(admin)
    db.flush()

    log_event(
        db,
        organization_id=org.id,
        user_id=admin.id,
        event_type="organization_created",
        description=f"Organization '{org.name}' created with initial administrator {admin.email}",
        entity_type="Organization",
        entity_id=str(org.id),
    )
    db.commit()
    db.refresh(admin)

    _set_session_cookie(response, str(admin.id))
    return admin


@router.post("/login", response_model=UserOut)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.email == payload.email)).scalars().first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user.status.value != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    log_event(
        db,
        organization_id=user.organization_id,
        user_id=user.id,
        event_type="user_login",
        description=f"{user.email} logged in",
        entity_type="User",
        entity_id=str(user.id),
    )
    db.commit()

    _set_session_cookie(response, str(user.id))
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    log_event(
        db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        event_type="user_logout",
        description=f"{current_user.email} logged out",
        entity_type="User",
        entity_id=str(current_user.id),
    )
    db.commit()
    response.delete_cookie(settings.cookie_name, path="/")


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()

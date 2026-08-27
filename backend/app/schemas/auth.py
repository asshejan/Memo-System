import uuid

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.enums import UserRole, UserStatus


class OrgSignupRequest(BaseModel):
    organization_name: str
    organization_identifier: str
    admin_name: str
    admin_email: EmailStr
    admin_password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    email: str
    designation: str | None
    department_id: uuid.UUID | None
    role: UserRole
    status: UserStatus


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    identifier: str
    logo_url: str | None
    contact_email: str | None
    contact_phone: str | None

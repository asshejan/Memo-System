import uuid

from pydantic import BaseModel, EmailStr, ConfigDict

from app.models.enums import UserRole, UserStatus, DepartmentStatus, CategoryStatus


class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None


class DepartmentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: DepartmentStatus | None = None


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: str | None
    status: DepartmentStatus


class UserInvite(BaseModel):
    name: str
    email: EmailStr
    password: str
    designation: str | None = None
    department_id: uuid.UUID | None = None
    role: UserRole = UserRole.regular_user


class UserUpdate(BaseModel):
    name: str | None = None
    designation: str | None = None
    department_id: uuid.UUID | None = None
    role: UserRole | None = None
    status: UserStatus | None = None


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: CategoryStatus | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: str | None
    status: CategoryStatus


class TemplatePositionIn(BaseModel):
    position_index: int
    label: str


class TemplateCreate(BaseModel):
    name: str
    positions: list[TemplatePositionIn]


class TemplatePositionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    position_index: int
    label: str


class TemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    positions: list[TemplatePositionOut]


class OrganizationUpdate(BaseModel):
    name: str | None = None
    logo_url: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None

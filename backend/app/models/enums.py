import enum


class UserRole(str, enum.Enum):
    org_admin = "org_admin"
    regular_user = "regular_user"


class UserStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class DepartmentStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class CategoryStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"


class MemoPriority(str, enum.Enum):
    normal = "normal"
    high = "high"
    urgent = "urgent"


class MemoStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    pending_review = "pending_review"
    pending_approval = "pending_approval"
    changes_requested = "changes_requested"
    rejected = "rejected"
    approved = "approved"
    cancelled = "cancelled"


class WorkflowInstanceStatus(str, enum.Enum):
    in_progress = "in_progress"
    approved = "approved"
    rejected = "rejected"
    changes_requested = "changes_requested"
    cancelled = "cancelled"


class WorkflowStepStatus(str, enum.Enum):
    pending = "pending"
    current = "current"
    approved = "approved"
    rejected = "rejected"
    changes_requested = "changes_requested"
    skipped = "skipped"


class CommentType(str, enum.Enum):
    general = "general"
    approval = "approval"
    rejection = "rejection"
    change_request = "change_request"


class DelegationStatus(str, enum.Enum):
    active = "active"
    revoked = "revoked"
    expired = "expired"

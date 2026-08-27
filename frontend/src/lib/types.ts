export type UserRole = "org_admin" | "regular_user";
export type UserStatus = "active" | "inactive";
export type DepartmentStatus = "active" | "inactive";
export type CategoryStatus = "active" | "inactive";
export type MemoPriority = "normal" | "high" | "urgent";
export type MemoStatus =
  | "draft"
  | "submitted"
  | "pending_review"
  | "pending_approval"
  | "changes_requested"
  | "rejected"
  | "approved"
  | "cancelled";
export type WorkflowInstanceStatus = "in_progress" | "approved" | "rejected" | "changes_requested" | "cancelled";
export type WorkflowStepStatus = "pending" | "current" | "approved" | "rejected" | "changes_requested" | "skipped";
export type CommentType = "general" | "approval" | "rejection" | "change_request";
export type DelegationStatus = "active" | "revoked" | "expired";

export interface User {
  id: string;
  organization_id: string;
  name: string;
  email: string;
  designation: string | null;
  department_id: string | null;
  role: UserRole;
  status: UserStatus;
}

export interface Organization {
  id: string;
  name: string;
  identifier: string;
  logo_url: string | null;
  contact_email: string | null;
  contact_phone: string | null;
}

export interface Department {
  id: string;
  name: string;
  description: string | null;
  status: DepartmentStatus;
}

export interface Category {
  id: string;
  name: string;
  description: string | null;
  status: CategoryStatus;
}

export interface TemplatePosition {
  id: string;
  position_index: number;
  label: string;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  positions: TemplatePosition[];
}

export interface Memo {
  id: string;
  organization_id: string;
  memo_number: string;
  subject: string;
  body: string;
  author_id: string;
  department_id: string | null;
  category_id: string | null;
  priority: MemoPriority;
  status: MemoStatus;
  created_at: string;
  submitted_at: string | null;
}

export interface WorkflowStep {
  id: string;
  position_index: number;
  label: string | null;
  assigned_user_id: string;
  status: WorkflowStepStatus;
  acted_at: string | null;
  acted_by_id: string | null;
  comment: string | null;
}

export interface WorkflowInstance {
  id: string;
  current_step_index: number;
  status: WorkflowInstanceStatus;
  steps: WorkflowStep[];
}

export interface Comment {
  id: string;
  author_id: string;
  on_behalf_of_id: string | null;
  comment_type: CommentType;
  text: string;
  created_at: string;
}

export interface MemoVersion {
  id: string;
  version_number: number;
  editor_id: string;
  subject: string;
  body: string;
  created_at: string;
}

export interface MemoDetail extends Memo {
  workflow_instance: WorkflowInstance | null;
  comments: Comment[];
  versions: MemoVersion[];
}

export interface Attachment {
  id: string;
  memo_id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  uploaded_by_id: string;
  created_at: string;
}

export interface Notification {
  id: string;
  memo_id: string | null;
  event_type: string;
  message: string;
  read_at: string | null;
  created_at: string;
}

export interface Delegation {
  id: string;
  delegating_user_id: string;
  delegate_user_id: string;
  start_date: string;
  end_date: string;
  reason: string | null;
  status: DelegationStatus;
}

export interface AuditLogEntry {
  id: string;
  user_id: string | null;
  event_type: string;
  entity_type: string | null;
  entity_id: string | null;
  description: string;
  created_at: string;
}

export interface DashboardData {
  awaiting_action: Memo[];
  my_memos: Memo[];
  recently_completed: Memo[];
  urgent_memos: Memo[];
  memo_counts_by_status: Record<string, number>;
}

export interface OrgStats {
  user_count: number;
  active_user_count: number;
  department_count: number;
  memo_count: number;
  pending_workflows: number;
  completed_workflows: number;
  rejected_workflows: number;
}

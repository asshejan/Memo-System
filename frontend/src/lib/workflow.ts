import { MemoDetail, WorkflowStep, Delegation } from "@/lib/types";

export function getCurrentStep(memo: MemoDetail): WorkflowStep | null {
  if (!memo.workflow_instance) return null;
  return memo.workflow_instance.steps.find((s) => s.status === "current") || null;
}

export function canActOnCurrentStep(memo: MemoDetail, userId: string, delegations: Delegation[]): boolean {
  const step = getCurrentStep(memo);
  if (!step || memo.status !== "pending_approval") return false;
  if (step.assigned_user_id === userId) return true;

  const today = new Date().toISOString().slice(0, 10);
  return delegations.some(
    (d) =>
      d.delegate_user_id === userId &&
      d.delegating_user_id === step.assigned_user_id &&
      d.status === "active" &&
      d.start_date <= today &&
      d.end_date >= today
  );
}

export interface TimelineEvent {
  timestamp: string;
  label: string;
  actorId?: string | null;
  comment?: string | null;
}

export function buildTimeline(memo: MemoDetail): TimelineEvent[] {
  const events: TimelineEvent[] = [];
  events.push({ timestamp: memo.created_at, label: "Memo created", actorId: memo.author_id });
  if (memo.submitted_at) {
    events.push({ timestamp: memo.submitted_at, label: "Memo submitted", actorId: memo.author_id });
  }
  if (memo.workflow_instance) {
    for (const step of memo.workflow_instance.steps) {
      if (step.acted_at) {
        const verb =
          step.status === "approved"
            ? "approved"
            : step.status === "rejected"
              ? "rejected"
              : step.status === "changes_requested"
                ? "requested changes on"
                : "acted on";
        events.push({
          timestamp: step.acted_at,
          label: `${step.label || "Participant"} ${verb} the memo`,
          actorId: step.acted_by_id,
          comment: step.comment,
        });
      }
    }
  }
  for (const comment of memo.comments) {
    if (comment.comment_type === "general") {
      events.push({ timestamp: comment.created_at, label: "Comment added", actorId: comment.author_id, comment: comment.text });
    }
  }
  for (const version of memo.versions) {
    events.push({ timestamp: version.created_at, label: `Revision saved (version ${version.version_number})`, actorId: version.editor_id });
  }
  return events.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());
}

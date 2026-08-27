"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError, downloadUrl } from "@/lib/api";
import { Attachment, Delegation, MemoDetail, MemoPriority } from "@/lib/types";
import { useAuth } from "@/context/AuthContext";
import { useDirectory } from "@/context/DirectoryContext";
import { canActOnCurrentStep, buildTimeline } from "@/lib/workflow";
import { Button, Card, ErrorText, Input, Label, Select, StatusBadge, PriorityBadge, Textarea } from "@/components/ui";
import WorkflowBuilder, { ParticipantRow } from "@/components/WorkflowBuilder";

export default function MemoDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuth();
  const { users, departments, categories, nameOf } = useDirectory();

  const [memo, setMemo] = useState<MemoDetail | null>(null);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [delegations, setDelegations] = useState<Delegation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [m, a, d] = await Promise.all([
        api.get<MemoDetail>(`/memos/${id}`),
        api.get<Attachment[]>(`/memos/${id}/attachments`),
        api.get<Delegation[]>("/delegations"),
      ]);
      setMemo(m);
      setAttachments(a);
      setDelegations(d);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load memo");
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <ErrorText>{error}</ErrorText>;
  if (!memo || !user) return <p className="text-sm text-slate-500">Loading…</p>;

  const isAuthor = memo.author_id === user.id;
  const isDraft = memo.status === "draft";
  const canAct = canActOnCurrentStep(memo, user.id, delegations);
  const canResubmit = memo.status === "changes_requested" && isAuthor;
  const timeline = buildTimeline(memo);

  async function runAction(fn: () => Promise<void>) {
    setActionError(null);
    setBusy(true);
    try {
      await fn();
      await load();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{memo.memo_number}</p>
          <h1 className="text-xl font-semibold">{memo.subject}</h1>
          <div className="mt-2 flex gap-2">
            <StatusBadge status={memo.status} />
            <PriorityBadge priority={memo.priority} />
          </div>
        </div>
        <a href={downloadUrl(`/memos/${memo.id}/pdf`)} target="_blank" rel="noreferrer">
          <Button variant="secondary">Export PDF</Button>
        </a>
      </div>

      <Card className="p-5">
        <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <Info label="Author" value={nameOf(memo.author_id)} />
          <Info label="Department" value={departments.find((d) => d.id === memo.department_id)?.name || "—"} />
          <Info label="Category" value={categories.find((c) => c.id === memo.category_id)?.name || "—"} />
          <Info label="Created" value={new Date(memo.created_at).toLocaleString()} />
        </dl>
      </Card>

      {isDraft && isAuthor ? (
        <DraftEditor memo={memo} onChanged={load} />
      ) : (
        <Card className="p-5">
          <h2 className="mb-2 text-sm font-semibold text-slate-700">Body</h2>
          <p className="whitespace-pre-wrap text-sm text-slate-800">{memo.body}</p>
        </Card>
      )}

      {isDraft && isAuthor && (
        <Card className="p-5">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Define approval workflow &amp; submit</h2>
          <WorkflowBuilder
            users={users}
            submitting={busy}
            onSubmit={(templateId, rows: ParticipantRow[]) =>
              runAction(async () => {
                await api.post(`/memos/${memo.id}/submit`, { template_id: templateId, participants: rows });
              })
            }
          />
          <ErrorText>{actionError}</ErrorText>
        </Card>
      )}

      {isDraft && isAuthor && (
        <Button
          variant="danger"
          onClick={() =>
            runAction(async () => {
              await api.delete(`/memos/${memo.id}`);
              router.push("/memos");
            })
          }
        >
          Delete draft
        </Button>
      )}

      {memo.workflow_instance && (
        <Card className="p-5">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Workflow</h2>
          <ol className="space-y-2">
            {memo.workflow_instance.steps.map((step) => (
              <li
                key={step.id}
                className={`flex items-center justify-between rounded-md border px-3 py-2 text-sm ${
                  step.status === "current" ? "border-indigo-300 bg-indigo-50" : "border-slate-200"
                }`}
              >
                <span>
                  {step.position_index + 1}. {step.label || nameOf(step.assigned_user_id)} — {nameOf(step.assigned_user_id)}
                </span>
                <StatusBadge status={step.status === "current" ? "pending_review" : step.status} />
              </li>
            ))}
          </ol>
        </Card>
      )}

      {canAct && (
        <WorkflowActionPanel memoId={memo.id} busy={busy} onAction={runAction} error={actionError} />
      )}

      {canResubmit && <ResubmitPanel memo={memo} onSubmit={runAction} />}

      <Card className="p-5">
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Activity timeline</h2>
        <ul className="space-y-2 text-sm">
          {timeline.map((event, i) => (
            <li key={i} className="border-l-2 border-slate-200 pl-3">
              <p className="text-slate-800">
                <span className="font-medium">{new Date(event.timestamp).toLocaleString()}</span> — {event.label}
                {event.actorId ? ` by ${nameOf(event.actorId)}` : ""}
              </p>
              {event.comment && <p className="text-slate-500">&quot;{event.comment}&quot;</p>}
            </li>
          ))}
        </ul>
      </Card>

      <AttachmentsPanel memoId={memo.id} attachments={attachments} isAuthor={isAuthor} onChanged={load} />

      <CommentsPanel memo={memo} nameOf={nameOf} onChanged={load} />

      {memo.versions.length > 0 && (
        <Card className="p-5">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">Previous versions</h2>
          <div className="space-y-3">
            {memo.versions.map((v) => (
              <details key={v.id} className="rounded-md border border-slate-200 p-3 text-sm">
                <summary className="cursor-pointer font-medium">
                  Version {v.version_number} — {nameOf(v.editor_id)} — {new Date(v.created_at).toLocaleString()}
                </summary>
                <p className="mt-2 font-medium">{v.subject}</p>
                <p className="whitespace-pre-wrap text-slate-600">{v.body}</p>
              </details>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-slate-400">{label}</dt>
      <dd className="font-medium text-slate-800">{value}</dd>
    </div>
  );
}

function DraftEditor({ memo, onChanged }: { memo: MemoDetail; onChanged: () => Promise<void> }) {
  const { departments, categories } = useDirectory();
  const [subject, setSubject] = useState(memo.subject);
  const [body, setBody] = useState(memo.body);
  const [departmentId, setDepartmentId] = useState(memo.department_id || "");
  const [categoryId, setCategoryId] = useState(memo.category_id || "");
  const [priority, setPriority] = useState<MemoPriority>(memo.priority);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    setSaving(true);
    setError(null);
    try {
      await api.patch(`/memos/${memo.id}`, {
        subject,
        body,
        department_id: departmentId || null,
        category_id: categoryId || null,
        priority,
      });
      await onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card className="space-y-4 p-5">
      <div>
        <Label>Subject</Label>
        <Input value={subject} onChange={(e) => setSubject(e.target.value)} />
      </div>
      <div>
        <Label>Body</Label>
        <Textarea rows={8} value={body} onChange={(e) => setBody(e.target.value)} />
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div>
          <Label>Department</Label>
          <Select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
            <option value="">—</option>
            {departments.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>Category</Label>
          <Select value={categoryId} onChange={(e) => setCategoryId(e.target.value)}>
            <option value="">—</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>Priority</Label>
          <Select value={priority} onChange={(e) => setPriority(e.target.value as MemoPriority)}>
            <option value="normal">Normal</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </Select>
        </div>
      </div>
      <ErrorText>{error}</ErrorText>
      <Button onClick={save} disabled={saving}>
        {saving ? "Saving…" : "Save draft"}
      </Button>
    </Card>
  );
}

function WorkflowActionPanel({
  memoId,
  busy,
  onAction,
  error,
}: {
  memoId: string;
  busy: boolean;
  onAction: (fn: () => Promise<void>) => Promise<void>;
  error: string | null;
}) {
  const [comment, setComment] = useState("");

  return (
    <Card className="space-y-3 p-5">
      <h2 className="text-sm font-semibold text-slate-700">It&apos;s your turn to act on this memo</h2>
      <div>
        <Label>Comment</Label>
        <Textarea rows={3} value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Required for reject / request changes" />
      </div>
      <ErrorText>{error}</ErrorText>
      <div className="flex flex-wrap gap-2">
        <Button
          disabled={busy}
          onClick={() => onAction(async () => { await api.post(`/memos/${memoId}/approve`, { comment: comment || null }); })}
        >
          Approve &amp; forward
        </Button>
        <Button
          variant="danger"
          disabled={busy}
          onClick={() => onAction(async () => { await api.post(`/memos/${memoId}/reject`, { comment }); })}
        >
          Reject
        </Button>
        <Button
          variant="secondary"
          disabled={busy}
          onClick={() => onAction(async () => { await api.post(`/memos/${memoId}/request-changes`, { comment }); })}
        >
          Request changes
        </Button>
      </div>
    </Card>
  );
}

function ResubmitPanel({ memo, onSubmit }: { memo: MemoDetail; onSubmit: (fn: () => Promise<void>) => Promise<void> }) {
  const [subject, setSubject] = useState(memo.subject);
  const [body, setBody] = useState(memo.body);
  const [busy, setBusy] = useState(false);

  return (
    <Card className="space-y-3 p-5">
      <h2 className="text-sm font-semibold text-slate-700">Changes were requested — revise &amp; resubmit</h2>
      <div>
        <Label>Subject</Label>
        <Input value={subject} onChange={(e) => setSubject(e.target.value)} />
      </div>
      <div>
        <Label>Body</Label>
        <Textarea rows={6} value={body} onChange={(e) => setBody(e.target.value)} />
      </div>
      <Button
        disabled={busy}
        onClick={async () => {
          setBusy(true);
          await onSubmit(async () => {
            await api.post(`/memos/${memo.id}/resubmit`, { subject, body });
          });
          setBusy(false);
        }}
      >
        {busy ? "Resubmitting…" : "Resubmit"}
      </Button>
    </Card>
  );
}

function AttachmentsPanel({
  memoId,
  attachments,
  isAuthor,
  onChanged,
}: {
  memoId: string;
  attachments: Attachment[];
  isAuthor: boolean;
  onChanged: () => Promise<void>;
}) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", file);
      await api.postForm(`/memos/${memoId}/attachments`, form);
      await onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed");
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  }

  return (
    <Card className="space-y-3 p-5">
      <h2 className="text-sm font-semibold text-slate-700">Attachments</h2>
      {attachments.length === 0 && <p className="text-sm text-slate-500">No attachments.</p>}
      <ul className="space-y-1 text-sm">
        {attachments.map((a) => (
          <li key={a.id} className="flex items-center justify-between">
            <a href={downloadUrl(`/memos/${memoId}/attachments/${a.id}/download`)} className="text-indigo-600 hover:underline">
              {a.filename}
            </a>
            <span className="text-xs text-slate-400">{(a.size_bytes / 1024).toFixed(0)} KB</span>
          </li>
        ))}
      </ul>
      {isAuthor && (
        <div>
          <input type="file" onChange={handleUpload} disabled={uploading} className="text-sm" />
          <ErrorText>{error}</ErrorText>
        </div>
      )}
    </Card>
  );
}

function CommentsPanel({
  memo,
  nameOf,
  onChanged,
}: {
  memo: MemoDetail;
  nameOf: (id: string | null | undefined) => string;
  onChanged: () => Promise<void>;
}) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!text.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await api.post(`/memos/${memo.id}/comments`, { text });
      setText("");
      await onChanged();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add comment");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="space-y-3 p-5">
      <h2 className="text-sm font-semibold text-slate-700">Comments</h2>
      <ul className="space-y-3 text-sm">
        {memo.comments.map((c) => (
          <li key={c.id} className="rounded-md bg-slate-50 p-2">
            <p className="text-xs text-slate-400">
              {nameOf(c.author_id)} · {new Date(c.created_at).toLocaleString()} · {c.comment_type.replace("_", " ")}
            </p>
            <p>{c.text}</p>
          </li>
        ))}
      </ul>
      <div className="flex gap-2">
        <Textarea rows={2} value={text} onChange={(e) => setText(e.target.value)} placeholder="Add a comment…" />
        <Button onClick={submit} disabled={busy}>
          Post
        </Button>
      </div>
      <ErrorText>{error}</ErrorText>
    </Card>
  );
}

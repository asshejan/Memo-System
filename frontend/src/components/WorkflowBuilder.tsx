"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { WorkflowTemplate, User } from "@/lib/types";
import { Button, Label, Select } from "@/components/ui";

export interface ParticipantRow {
  position_index: number;
  user_id: string;
  label: string;
}

export default function WorkflowBuilder({
  users,
  onSubmit,
  submitting,
}: {
  users: User[];
  onSubmit: (templateId: string | null, participants: ParticipantRow[]) => void;
  submitting: boolean;
}) {
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [templateId, setTemplateId] = useState<string>("");
  const [rows, setRows] = useState<ParticipantRow[]>([{ position_index: 0, user_id: "", label: "" }]);

  useEffect(() => {
    api.get<WorkflowTemplate[]>("/admin/templates").then(setTemplates).catch(() => {});
  }, []);

  function applyTemplate(id: string) {
    setTemplateId(id);
    const template = templates.find((t) => t.id === id);
    if (template) {
      setRows(template.positions.map((p) => ({ position_index: p.position_index, user_id: "", label: p.label })));
    }
  }

  function updateRow(index: number, patch: Partial<ParticipantRow>) {
    setRows((prev) => prev.map((r, i) => (i === index ? { ...r, ...patch } : r)));
  }

  function addRow() {
    setRows((prev) => [...prev, { position_index: prev.length, user_id: "", label: "" }]);
  }

  function removeRow(index: number) {
    setRows((prev) => prev.filter((_, i) => i !== index).map((r, i) => ({ ...r, position_index: i })));
  }

  const activeUsers = users.filter((u) => u.status === "active");

  return (
    <div className="space-y-4">
      <div>
        <Label>Use a workflow template (optional)</Label>
        <Select value={templateId} onChange={(e) => applyTemplate(e.target.value)}>
          <option value="">Custom sequence</option>
          {templates.map((t) => (
            <option key={t.id} value={t.id}>
              {t.name}
            </option>
          ))}
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Approval sequence (in order)</Label>
        {rows.map((row, index) => (
          <div key={index} className="flex items-center gap-2">
            <span className="w-6 shrink-0 text-sm text-slate-400">{index + 1}.</span>
            <Select
              className="flex-1"
              value={row.user_id}
              onChange={(e) => updateRow(index, { user_id: e.target.value })}
              required
            >
              <option value="">Select user…</option>
              {activeUsers.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name} ({u.email})
                </option>
              ))}
            </Select>
            <input
              className="w-40 rounded-md border border-slate-300 px-2 py-2 text-sm"
              placeholder="Role label"
              value={row.label}
              onChange={(e) => updateRow(index, { label: e.target.value })}
            />
            {rows.length > 1 && (
              <button type="button" onClick={() => removeRow(index)} className="text-sm text-slate-400 hover:text-red-600">
                ✕
              </button>
            )}
          </div>
        ))}
        <button type="button" onClick={addRow} className="text-sm font-medium text-indigo-600 hover:underline">
          + Add participant
        </button>
      </div>

      <Button
        type="button"
        disabled={submitting || rows.some((r) => !r.user_id)}
        onClick={() => onSubmit(templateId || null, rows)}
      >
        {submitting ? "Submitting…" : "Submit memo"}
      </Button>
    </div>
  );
}

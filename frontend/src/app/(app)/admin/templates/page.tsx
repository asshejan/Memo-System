"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { WorkflowTemplate } from "@/lib/types";
import { Button, Card, ErrorText, Input, Label } from "@/components/ui";

export default function TemplatesAdminPage() {
  const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
  const [name, setName] = useState("");
  const [labels, setLabels] = useState<string[]>([""]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setTemplates(await api.get<WorkflowTemplate[]>("/admin/templates"));
  }

  useEffect(() => {
    load();
  }, []);

  function updateLabel(index: number, value: string) {
    setLabels((prev) => prev.map((l, i) => (i === index ? value : l)));
  }

  async function handleCreate() {
    setError(null);
    const filled = labels.map((l) => l.trim()).filter(Boolean);
    if (!name.trim() || filled.length === 0) {
      setError("Provide a name and at least one position label");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/admin/templates", {
        name,
        positions: filled.map((label, i) => ({ position_index: i, label })),
      });
      setName("");
      setLabels([""]);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create template");
    } finally {
      setSubmitting(false);
    }
  }

  async function remove(id: string) {
    await api.delete(`/admin/templates/${id}`);
    await load();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Workflow Templates</h1>
      <p className="text-sm text-slate-500">
        A template defines an ordered list of approval positions (e.g. Employee → Department Head → Finance → Director).
        Users pick from this template when submitting a memo and assign an actual person to each position.
      </p>

      <Card className="max-w-lg space-y-4 p-6">
        <h2 className="text-sm font-semibold text-slate-700">Create template</h2>
        <div>
          <Label>Template name</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Purchase Request" />
        </div>
        <div className="space-y-2">
          <Label>Positions (in order)</Label>
          {labels.map((label, i) => (
            <Input key={i} value={label} onChange={(e) => updateLabel(i, e.target.value)} placeholder={`Position ${i + 1}`} />
          ))}
          <button type="button" className="text-sm font-medium text-indigo-600 hover:underline" onClick={() => setLabels((p) => [...p, ""])}>
            + Add position
          </button>
        </div>
        <ErrorText>{error}</ErrorText>
        <Button onClick={handleCreate} disabled={submitting}>
          {submitting ? "Creating…" : "Create template"}
        </Button>
      </Card>

      <Card className="divide-y divide-slate-100">
        {templates.map((t) => (
          <div key={t.id} className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium">{t.name}</p>
              <p className="text-sm text-slate-500">{t.positions.map((p) => p.label).join(" → ")}</p>
            </div>
            <Button variant="danger" onClick={() => remove(t.id)}>
              Delete
            </Button>
          </div>
        ))}
      </Card>
    </div>
  );
}

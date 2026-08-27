"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Department, DepartmentStatus } from "@/lib/types";
import { Button, Card, ErrorText, Input, Label } from "@/components/ui";

export default function DepartmentsAdminPage() {
  const [departments, setDepartments] = useState<Department[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setDepartments(await api.get<Department[]>("/admin/departments"));
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post("/admin/departments", { name, description: description || null });
      setName("");
      setDescription("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create department");
    } finally {
      setSubmitting(false);
    }
  }

  async function toggleStatus(dept: Department) {
    const next: DepartmentStatus = dept.status === "active" ? "inactive" : "active";
    await api.patch(`/admin/departments/${dept.id}`, { status: next });
    await load();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Departments</h1>

      <Card className="max-w-lg space-y-4 p-6">
        <h2 className="text-sm font-semibold text-slate-700">Add department</h2>
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <Label>Name</Label>
            <Input required value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <Label>Description</Label>
            <Input value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <ErrorText>{error}</ErrorText>
          <Button type="submit" disabled={submitting}>
            {submitting ? "Adding…" : "Add"}
          </Button>
        </form>
      </Card>

      <Card className="divide-y divide-slate-100">
        {departments.map((d) => (
          <div key={d.id} className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium">{d.name}</p>
              <p className="text-sm text-slate-500">{d.description}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className={`text-xs font-medium ${d.status === "active" ? "text-green-600" : "text-slate-400"}`}>
                {d.status}
              </span>
              <Button variant="secondary" onClick={() => toggleStatus(d)}>
                {d.status === "active" ? "Deactivate" : "Activate"}
              </Button>
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}

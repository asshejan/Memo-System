"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Category, CategoryStatus } from "@/lib/types";
import { Button, Card, ErrorText, Input, Label } from "@/components/ui";

export default function CategoriesAdminPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setCategories(await api.get<Category[]>("/admin/categories"));
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post("/admin/categories", { name, description: description || null });
      setName("");
      setDescription("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create category");
    } finally {
      setSubmitting(false);
    }
  }

  async function toggleStatus(cat: Category) {
    const next: CategoryStatus = cat.status === "active" ? "inactive" : "active";
    await api.patch(`/admin/categories/${cat.id}`, { status: next });
    await load();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Memo Categories</h1>

      <Card className="max-w-lg space-y-4 p-6">
        <h2 className="text-sm font-semibold text-slate-700">Add category</h2>
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <Label>Name</Label>
            <Input required value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Financial" />
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
        {categories.map((c) => (
          <div key={c.id} className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium">{c.name}</p>
              <p className="text-sm text-slate-500">{c.description}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className={`text-xs font-medium ${c.status === "active" ? "text-green-600" : "text-slate-400"}`}>{c.status}</span>
              <Button variant="secondary" onClick={() => toggleStatus(c)}>
                {c.status === "active" ? "Deactivate" : "Activate"}
              </Button>
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}

"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { Department, Category, Memo, MemoPriority } from "@/lib/types";
import { Button, Card, ErrorText, Input, Label, Select, Textarea } from "@/components/ui";

export default function NewMemoPage() {
  const router = useRouter();
  const [departments, setDepartments] = useState<Department[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [priority, setPriority] = useState<MemoPriority>("normal");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    api.get<Department[]>("/directory/departments").then(setDepartments).catch(() => {});
    api.get<Category[]>("/directory/categories").then(setCategories).catch(() => {});
  }, []);

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const memo = await api.post<Memo>("/memos", {
        subject,
        body,
        department_id: departmentId || null,
        category_id: categoryId || null,
        priority,
      });
      router.push(`/memos/${memo.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save draft");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <h1 className="text-xl font-semibold">New memo</h1>
      <Card className="p-6">
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <Label>Subject</Label>
            <Input required value={subject} onChange={(e) => setSubject(e.target.value)} />
          </div>
          <div>
            <Label>Body</Label>
            <Textarea required rows={10} value={body} onChange={(e) => setBody(e.target.value)} />
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
          <div className="flex justify-end gap-2">
            <Button type="submit" disabled={submitting}>
              {submitting ? "Saving…" : "Save draft"}
            </Button>
          </div>
          <p className="text-xs text-slate-500">
            You&apos;ll define the approval workflow and submit the memo on the next screen.
          </p>
        </form>
      </Card>
    </div>
  );
}

"use client";

import { FormEvent, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Memo, MemoPriority, MemoStatus } from "@/lib/types";
import { useDirectory } from "@/context/DirectoryContext";
import { Button, Card, ErrorText, Input, Label, Select } from "@/components/ui";
import MemoList from "@/components/MemoList";

const STATUS_OPTIONS: MemoStatus[] = [
  "draft", "submitted", "pending_review", "pending_approval", "changes_requested", "rejected", "approved", "cancelled",
];

export default function SearchPage() {
  const { departments, categories } = useDirectory();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [results, setResults] = useState<Memo[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(e: FormEvent) {
    e.preventDefault();
    setError(null);
    const params = new URLSearchParams();
    if (q) params.set("q", q);
    if (status) params.set("status_filter", status);
    if (priority) params.set("priority", priority as MemoPriority);
    if (departmentId) params.set("department_id", departmentId);
    if (categoryId) params.set("category_id", categoryId);
    if (dateFrom) params.set("date_from", dateFrom);
    if (dateTo) params.set("date_to", dateTo);
    try {
      setResults(await api.get<Memo[]>(`/search/memos?${params.toString()}`));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Search failed");
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Search memos</h1>
      <Card className="p-5">
        <form onSubmit={handleSearch} className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="sm:col-span-3">
            <Label>Keyword (subject, body, memo number)</Label>
            <Input value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
          <div>
            <Label>Status</Label>
            <Select value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">Any</option>
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s.replace("_", " ")}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label>Priority</Label>
            <Select value={priority} onChange={(e) => setPriority(e.target.value)}>
              <option value="">Any</option>
              <option value="normal">Normal</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </Select>
          </div>
          <div>
            <Label>Department</Label>
            <Select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
              <option value="">Any</option>
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
              <option value="">Any</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label>From date</Label>
            <Input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </div>
          <div>
            <Label>To date</Label>
            <Input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </div>
          <div className="flex items-end">
            <Button type="submit">Search</Button>
          </div>
        </form>
      </Card>
      <ErrorText>{error}</ErrorText>
      {results && (
        <Card className="p-5">
          <MemoList memos={results} emptyLabel="No memos matched your search." />
        </Card>
      )}
    </div>
  );
}

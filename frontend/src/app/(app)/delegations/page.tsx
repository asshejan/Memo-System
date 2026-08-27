"use client";

import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useDirectory } from "@/context/DirectoryContext";
import { api, ApiError } from "@/lib/api";
import { Delegation } from "@/lib/types";
import { Button, Card, ErrorText, Input, Label, Select } from "@/components/ui";

export default function DelegationsPage() {
  const { user } = useAuth();
  const { users, nameOf } = useDirectory();
  const [delegations, setDelegations] = useState<Delegation[]>([]);
  const [delegateId, setDelegateId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [reason, setReason] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setDelegations(await api.get<Delegation[]>("/delegations"));
  }

  useEffect(() => {
    load();
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post("/delegations", { delegate_user_id: delegateId, start_date: startDate, end_date: endDate, reason: reason || null });
      setDelegateId("");
      setStartDate("");
      setEndDate("");
      setReason("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create delegation");
    } finally {
      setSubmitting(false);
    }
  }

  async function revoke(id: string) {
    await api.post(`/delegations/${id}/revoke`);
    await load();
  }

  const given = delegations.filter((d) => d.delegating_user_id === user?.id);
  const received = delegations.filter((d) => d.delegate_user_id === user?.id);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Delegations</h1>
      <p className="text-sm text-slate-500">
        Delegate your workflow-approval authority to another user for a specific period, e.g. while you&apos;re on leave.
      </p>

      <Card className="p-5">
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Delegate to someone</h2>
        <form onSubmit={handleSubmit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <Label>Delegate</Label>
            <Select required value={delegateId} onChange={(e) => setDelegateId(e.target.value)}>
              <option value="">Select user…</option>
              {users.filter((u) => u.id !== user?.id && u.status === "active").map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label>Reason (optional)</Label>
            <Input value={reason} onChange={(e) => setReason(e.target.value)} />
          </div>
          <div>
            <Label>Start date</Label>
            <Input type="date" required value={startDate} onChange={(e) => setStartDate(e.target.value)} />
          </div>
          <div>
            <Label>End date</Label>
            <Input type="date" required value={endDate} onChange={(e) => setEndDate(e.target.value)} />
          </div>
          <div className="sm:col-span-2">
            <ErrorText>{error}</ErrorText>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Saving…" : "Create delegation"}
            </Button>
          </div>
        </form>
      </Card>

      <Card className="p-5">
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Delegations you&apos;ve given</h2>
        {given.length === 0 && <p className="text-sm text-slate-500">None.</p>}
        <ul className="space-y-2 text-sm">
          {given.map((d) => (
            <li key={d.id} className="flex items-center justify-between rounded-md border border-slate-200 p-2">
              <span>
                {nameOf(d.delegate_user_id)} · {d.start_date} → {d.end_date} · {d.status}
              </span>
              {d.status === "active" && (
                <button onClick={() => revoke(d.id)} className="text-xs text-red-600 hover:underline">
                  Revoke
                </button>
              )}
            </li>
          ))}
        </ul>
      </Card>

      <Card className="p-5">
        <h2 className="mb-3 text-sm font-semibold text-slate-700">Delegations you&apos;ve received</h2>
        {received.length === 0 && <p className="text-sm text-slate-500">None.</p>}
        <ul className="space-y-2 text-sm">
          {received.map((d) => (
            <li key={d.id} className="rounded-md border border-slate-200 p-2">
              On behalf of {nameOf(d.delegating_user_id)} · {d.start_date} → {d.end_date} · {d.status}
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}

"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { AuditLogEntry } from "@/lib/types";
import { useDirectory } from "@/context/DirectoryContext";
import { Card, ErrorText } from "@/components/ui";

export default function AuditLogPage() {
  const [entries, setEntries] = useState<AuditLogEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { nameOf } = useDirectory();

  useEffect(() => {
    api
      .get<AuditLogEntry[]>("/audit-log")
      .then(setEntries)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load audit log"));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Audit Log</h1>
      <p className="text-sm text-slate-500">Read-only record of significant system events for this organization.</p>
      <ErrorText>{error}</ErrorText>
      <Card className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
              <th className="p-3">Time</th>
              <th className="p-3">Event</th>
              <th className="p-3">User</th>
              <th className="p-3">Description</th>
            </tr>
          </thead>
          <tbody>
            {entries?.map((e) => (
              <tr key={e.id} className="border-b border-slate-100">
                <td className="p-3 whitespace-nowrap text-slate-500">{new Date(e.created_at).toLocaleString()}</td>
                <td className="p-3 whitespace-nowrap">{e.event_type.replace(/_/g, " ")}</td>
                <td className="p-3 whitespace-nowrap">{nameOf(e.user_id)}</td>
                <td className="p-3">{e.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

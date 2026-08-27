"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { useDirectory } from "@/context/DirectoryContext";
import { Card, ErrorText } from "@/components/ui";

interface ReportSummary {
  memos_by_status: Record<string, number>;
  memos_by_department: Record<string, number>;
  memos_by_category: Record<string, number>;
  urgent_memo_count: number;
  average_workflow_completion_hours: number | null;
  pending_approvals: number;
  rejected_count: number;
  change_requests_count: number;
}

export default function ReportsPage() {
  const [report, setReport] = useState<ReportSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { departments, categories } = useDirectory();

  useEffect(() => {
    api
      .get<ReportSummary>("/reports/summary")
      .then(setReport)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load report"));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Reports</h1>
      <ErrorText>{error}</ErrorText>
      {report && (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Stat label="Urgent memos" value={report.urgent_memo_count} />
            <Stat label="Pending approvals" value={report.pending_approvals} />
            <Stat label="Rejected" value={report.rejected_count} />
            <Stat label="Change requests" value={report.change_requests_count} />
            <Stat
              label="Avg. completion time"
              value={report.average_workflow_completion_hours != null ? `${report.average_workflow_completion_hours.toFixed(1)}h` : "—"}
            />
          </div>

          <Card className="p-5">
            <h2 className="mb-3 text-sm font-semibold text-slate-700">Memos by status</h2>
            <BarList data={report.memos_by_status} />
          </Card>

          <Card className="p-5">
            <h2 className="mb-3 text-sm font-semibold text-slate-700">Memos by department</h2>
            <BarList data={report.memos_by_department} labelFor={(id) => departments.find((d) => d.id === id)?.name || id} />
          </Card>

          <Card className="p-5">
            <h2 className="mb-3 text-sm font-semibold text-slate-700">Memos by category</h2>
            <BarList data={report.memos_by_category} labelFor={(id) => categories.find((c) => c.id === id)?.name || id} />
          </Card>
        </>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <Card className="p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </Card>
  );
}

function BarList({ data, labelFor }: { data: Record<string, number>; labelFor?: (key: string) => string }) {
  const entries = Object.entries(data);
  const max = Math.max(1, ...entries.map(([, v]) => v));
  if (entries.length === 0) return <p className="text-sm text-slate-500">No data yet.</p>;
  return (
    <div className="space-y-2">
      {entries.map(([key, value]) => (
        <div key={key} className="flex items-center gap-3 text-sm">
          <span className="w-40 shrink-0 truncate capitalize text-slate-600">{(labelFor ? labelFor(key) : key).replace(/_/g, " ")}</span>
          <div className="h-2 flex-1 rounded bg-slate-100">
            <div className="h-2 rounded bg-indigo-500" style={{ width: `${(value / max) * 100}%` }} />
          </div>
          <span className="w-6 text-right text-slate-500">{value}</span>
        </div>
      ))}
    </div>
  );
}

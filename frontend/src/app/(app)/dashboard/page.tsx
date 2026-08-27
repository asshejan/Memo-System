"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { DashboardData } from "@/lib/types";
import { Card, Button, ErrorText } from "@/components/ui";
import MemoList from "@/components/MemoList";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<DashboardData>("/dashboard")
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load dashboard"));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <Link href="/memos/new">
          <Button>New memo</Button>
        </Link>
      </div>

      <ErrorText>{error}</ErrorText>

      {data && (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <SummaryCard label="Awaiting your action" value={data.awaiting_action.length} />
            <SummaryCard label="Your memos" value={data.my_memos.length} />
            <SummaryCard label="Urgent" value={data.urgent_memos.length} tone="urgent" />
            <SummaryCard label="Recently completed" value={data.recently_completed.length} />
          </div>

          <Card className="p-5">
            <h2 className="mb-3 text-sm font-semibold text-slate-700">Awaiting your action</h2>
            <MemoList memos={data.awaiting_action} emptyLabel="Nothing needs your action right now." />
          </Card>

          <Card className="p-5">
            <h2 className="mb-3 text-sm font-semibold text-slate-700">Your memos</h2>
            <MemoList memos={data.my_memos.slice(0, 10)} emptyLabel="You haven't created any memos yet." />
          </Card>

          <Card className="p-5">
            <h2 className="mb-3 text-sm font-semibold text-slate-700">Recently completed</h2>
            <MemoList memos={data.recently_completed} emptyLabel="No completed memos yet." />
          </Card>
        </>
      )}
    </div>
  );
}

function SummaryCard({ label, value, tone }: { label: string; value: number; tone?: "urgent" }) {
  return (
    <Card className="p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`mt-1 text-2xl font-semibold ${tone === "urgent" ? "text-red-600" : "text-slate-900"}`}>{value}</p>
    </Card>
  );
}

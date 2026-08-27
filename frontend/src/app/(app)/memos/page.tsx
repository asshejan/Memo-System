"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { Memo } from "@/lib/types";
import { Card, ErrorText, Button } from "@/components/ui";
import MemoList from "@/components/MemoList";
import clsx from "clsx";

type Tab = "all" | "drafts" | "completed";

export default function MyMemosPage() {
  const [tab, setTab] = useState<Tab>("all");
  const [mine, setMine] = useState<Memo[] | null>(null);
  const [completed, setCompleted] = useState<Memo[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Memo[]>("/memos/mine")
      .then(setMine)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load memos"));
    api
      .get<Memo[]>("/memos-completed")
      .then(setCompleted)
      .catch(() => {});
  }, []);

  const drafts = (mine || []).filter((m) => m.status === "draft");
  const visible = tab === "drafts" ? drafts : tab === "completed" ? completed || [] : mine || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">My Memos</h1>
        <Link href="/memos/new">
          <Button>New memo</Button>
        </Link>
      </div>

      <div className="flex gap-1 border-b border-slate-200">
        {(["all", "drafts", "completed"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={clsx(
              "border-b-2 px-3 py-2 text-sm capitalize",
              tab === t ? "border-indigo-600 text-indigo-700" : "border-transparent text-slate-500 hover:text-slate-700"
            )}
          >
            {t}
          </button>
        ))}
      </div>

      <ErrorText>{error}</ErrorText>
      <Card className="p-5">{mine && <MemoList memos={visible} emptyLabel="Nothing here yet." />}</Card>
    </div>
  );
}

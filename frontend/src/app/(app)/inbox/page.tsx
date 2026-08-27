"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Memo } from "@/lib/types";
import { Card, ErrorText } from "@/components/ui";
import MemoList from "@/components/MemoList";

export default function InboxPage() {
  const [memos, setMemos] = useState<Memo[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Memo[]>("/inbox")
      .then(setMemos)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Failed to load inbox"));
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Inbox</h1>
      <p className="text-sm text-slate-500">Memos currently awaiting your action, ordered by priority.</p>
      <ErrorText>{error}</ErrorText>
      <Card className="p-5">{memos && <MemoList memos={memos} emptyLabel="Your inbox is empty." />}</Card>
    </div>
  );
}

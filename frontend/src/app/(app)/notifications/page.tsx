"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { Notification } from "@/lib/types";
import { Card, ErrorText, Button, EmptyState } from "@/components/ui";
import clsx from "clsx";

export default function NotificationsPage() {
  const [items, setItems] = useState<Notification[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setItems(await api.get<Notification[]>("/notifications"));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load notifications");
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function markAllRead() {
    await api.post("/notifications/mark-all-read");
    await load();
  }

  async function markRead(id: string) {
    await api.post(`/notifications/${id}/read`);
    await load();
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Notifications</h1>
        <Button variant="secondary" onClick={markAllRead}>
          Mark all as read
        </Button>
      </div>
      <ErrorText>{error}</ErrorText>
      <Card className="divide-y divide-slate-100">
        {items && items.length === 0 && <EmptyState>No notifications yet.</EmptyState>}
        {items?.map((n) => (
          <div key={n.id} className={clsx("flex items-center justify-between gap-3 p-4", !n.read_at && "bg-indigo-50/50")}>
            <div>
              <p className="text-sm text-slate-800">{n.message}</p>
              <p className="text-xs text-slate-400">{new Date(n.created_at).toLocaleString()}</p>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              {n.memo_id && (
                <Link href={`/memos/${n.memo_id}`} className="text-xs font-medium text-indigo-600 hover:underline">
                  View memo
                </Link>
              )}
              {!n.read_at && (
                <button onClick={() => markRead(n.id)} className="text-xs text-slate-400 hover:text-slate-700">
                  Mark read
                </button>
              )}
            </div>
          </div>
        ))}
      </Card>
    </div>
  );
}

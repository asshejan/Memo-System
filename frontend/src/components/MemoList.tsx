"use client";

import Link from "next/link";
import { Memo } from "@/lib/types";
import { StatusBadge, PriorityBadge, EmptyState } from "@/components/ui";
import { formatDistanceToNow } from "date-fns";

export default function MemoList({ memos, emptyLabel = "No memos to show." }: { memos: Memo[]; emptyLabel?: string }) {
  if (memos.length === 0) return <EmptyState>{emptyLabel}</EmptyState>;

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
            <th className="py-2 pr-4">Memo #</th>
            <th className="py-2 pr-4">Subject</th>
            <th className="py-2 pr-4">Priority</th>
            <th className="py-2 pr-4">Status</th>
            <th className="py-2 pr-4">Submitted</th>
            <th className="py-2 pr-4">Age</th>
          </tr>
        </thead>
        <tbody>
          {memos.map((memo) => (
            <tr key={memo.id} className="border-b border-slate-100 hover:bg-slate-50">
              <td className="py-2 pr-4">
                <Link href={`/memos/${memo.id}`} className="font-medium text-indigo-600 hover:underline">
                  {memo.memo_number}
                </Link>
              </td>
              <td className="py-2 pr-4">
                <Link href={`/memos/${memo.id}`} className="hover:underline">
                  {memo.subject}
                </Link>
              </td>
              <td className="py-2 pr-4">
                <PriorityBadge priority={memo.priority} />
              </td>
              <td className="py-2 pr-4">
                <StatusBadge status={memo.status} />
              </td>
              <td className="py-2 pr-4 text-slate-500">
                {memo.submitted_at ? new Date(memo.submitted_at).toLocaleDateString() : "—"}
              </td>
              <td className="py-2 pr-4 text-slate-500">
                {formatDistanceToNow(new Date(memo.created_at), { addSuffix: true })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

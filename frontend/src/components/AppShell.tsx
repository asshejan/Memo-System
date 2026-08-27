"use client";

import { ReactNode, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { api } from "@/lib/api";
import clsx from "clsx";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/inbox", label: "Inbox" },
  { href: "/memos", label: "My Memos" },
  { href: "/search", label: "Search" },
  { href: "/delegations", label: "Delegations" },
  { href: "/notifications", label: "Notifications" },
];

const ADMIN_NAV_ITEMS = [
  { href: "/admin", label: "Organization" },
  { href: "/admin/departments", label: "Departments" },
  { href: "/admin/users", label: "Users" },
  { href: "/admin/categories", label: "Categories" },
  { href: "/admin/templates", label: "Workflow Templates" },
  { href: "/admin/reports", label: "Reports" },
  { href: "/admin/audit-log", label: "Audit Log" },
];

export default function AppShell({ children }: { children: ReactNode }) {
  const { user, loading, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [unread, setUnread] = useState(0);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  useEffect(() => {
    setMobileOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    async function poll() {
      try {
        const res = await api.get<{ unread_count: number }>("/notifications/unread-count");
        if (!cancelled) setUnread(res.unread_count);
      } catch {
        // ignore transient polling failures
      }
    }
    poll();
    const id = setInterval(poll, 20000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [user, pathname]);

  if (loading || !user) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-slate-500">Loading…</p>
      </div>
    );
  }

  const nav = (
    <>
      <div className="border-b border-slate-200 px-4 py-4">
        <p className="text-sm font-semibold text-slate-900">Memo System</p>
        <p className="truncate text-xs text-slate-500">{user.email}</p>
      </div>
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 py-3">
        {NAV_ITEMS.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={clsx(
              "flex items-center justify-between rounded-md px-3 py-2 text-sm",
              pathname === item.href ? "bg-indigo-50 text-indigo-700" : "text-slate-600 hover:bg-slate-50"
            )}
          >
            {item.label}
            {item.href === "/notifications" && unread > 0 && (
              <span className="rounded-full bg-red-500 px-1.5 py-0.5 text-[10px] font-semibold text-white">{unread}</span>
            )}
          </Link>
        ))}
        {user.role === "org_admin" && (
          <>
            <p className="mt-4 px-3 text-xs font-semibold uppercase tracking-wide text-slate-400">Administration</p>
            {ADMIN_NAV_ITEMS.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "block rounded-md px-3 py-2 text-sm",
                  pathname === item.href ? "bg-indigo-50 text-indigo-700" : "text-slate-600 hover:bg-slate-50"
                )}
              >
                {item.label}
              </Link>
            ))}
          </>
        )}
      </nav>
      <div className="border-t border-slate-200 p-2">
        <Link href="/profile" className="block rounded-md px-3 py-2 text-sm text-slate-600 hover:bg-slate-50">
          Profile
        </Link>
        <button
          onClick={() => logout()}
          className="block w-full rounded-md px-3 py-2 text-left text-sm text-slate-600 hover:bg-slate-50"
        >
          Log out
        </button>
      </div>
    </>
  );

  return (
    <div className="flex min-h-screen flex-1 flex-col md:flex-row">
      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 md:hidden">
        <p className="text-sm font-semibold text-slate-900">Memo System</p>
        <button
          onClick={() => setMobileOpen((v) => !v)}
          className="relative rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-600"
        >
          Menu
          {unread > 0 && <span className="absolute -right-1 -top-1 h-2.5 w-2.5 rounded-full bg-red-500" />}
        </button>
      </header>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 flex md:hidden">
          <div className="absolute inset-0 bg-black/30" onClick={() => setMobileOpen(false)} />
          <aside className="relative z-50 flex w-72 max-w-[80%] flex-col bg-white shadow-xl">{nav}</aside>
        </div>
      )}

      <aside className="hidden w-60 shrink-0 border-r border-slate-200 bg-white md:flex md:flex-col">{nav}</aside>

      <main className="flex-1 overflow-x-hidden">
        <div className="mx-auto max-w-6xl px-4 py-6 md:px-8">{children}</div>
      </main>
    </div>
  );
}

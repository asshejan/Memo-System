"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Organization, OrgStats } from "@/lib/types";
import { Button, Card, ErrorText, Input, Label } from "@/components/ui";

export default function AdminOrganizationPage() {
  const [org, setOrg] = useState<Organization | null>(null);
  const [stats, setStats] = useState<OrgStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get<Organization>("/admin/organization").then(setOrg).catch(() => {});
    api.get<OrgStats>("/admin/stats").then(setStats).catch(() => {});
  }, []);

  async function handleSave(e: FormEvent) {
    e.preventDefault();
    if (!org) return;
    setError(null);
    setSaving(true);
    try {
      const updated = await api.patch<Organization>("/admin/organization", {
        name: org.name,
        contact_email: org.contact_email,
        contact_phone: org.contact_phone,
        logo_url: org.logo_url,
      });
      setOrg(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update organization");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Organization</h1>

      {stats && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <StatCard label="Users" value={stats.user_count} />
          <StatCard label="Active users" value={stats.active_user_count} />
          <StatCard label="Departments" value={stats.department_count} />
          <StatCard label="Memos" value={stats.memo_count} />
          <StatCard label="Pending workflows" value={stats.pending_workflows} />
          <StatCard label="Completed workflows" value={stats.completed_workflows} />
          <StatCard label="Rejected workflows" value={stats.rejected_workflows} />
        </div>
      )}

      {org && (
        <Card className="max-w-lg space-y-4 p-6">
          <h2 className="text-sm font-semibold text-slate-700">Organization details</h2>
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <Label>Identifier</Label>
              <Input value={org.identifier} disabled />
            </div>
            <div>
              <Label>Name</Label>
              <Input value={org.name} onChange={(e) => setOrg({ ...org, name: e.target.value })} />
            </div>
            <div>
              <Label>Contact email</Label>
              <Input value={org.contact_email || ""} onChange={(e) => setOrg({ ...org, contact_email: e.target.value })} />
            </div>
            <div>
              <Label>Contact phone</Label>
              <Input value={org.contact_phone || ""} onChange={(e) => setOrg({ ...org, contact_phone: e.target.value })} />
            </div>
            <ErrorText>{error}</ErrorText>
            <Button type="submit" disabled={saving}>
              {saving ? "Saving…" : "Save"}
            </Button>
          </form>
        </Card>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <Card className="p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
    </Card>
  );
}

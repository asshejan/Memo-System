"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { Button, Card, ErrorText, Input, Label } from "@/components/ui";

export default function SignupPage() {
  const router = useRouter();
  const { refresh } = useAuth();
  const [organizationName, setOrganizationName] = useState("");
  const [organizationIdentifier, setOrganizationIdentifier] = useState("");
  const [adminName, setAdminName] = useState("");
  const [adminEmail, setAdminEmail] = useState("");
  const [adminPassword, setAdminPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post("/auth/signup", {
        organization_name: organizationName,
        organization_identifier: organizationIdentifier,
        admin_name: adminName,
        admin_email: adminEmail,
        admin_password: adminPassword,
      });
      await refresh();
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Sign up failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex flex-1 items-center justify-center px-4 py-10">
      <Card className="w-full max-w-md p-6">
        <h1 className="mb-1 text-lg font-semibold">Create your organization</h1>
        <p className="mb-6 text-sm text-slate-500">
          This creates a new, isolated tenant and its first administrator account.
        </p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label>Organization name</Label>
            <Input required value={organizationName} onChange={(e) => setOrganizationName(e.target.value)} />
          </div>
          <div>
            <Label>Organization identifier</Label>
            <Input
              required
              placeholder="e.g. acme-corp"
              value={organizationIdentifier}
              onChange={(e) => setOrganizationIdentifier(e.target.value.toLowerCase().replace(/\s+/g, "-"))}
            />
          </div>
          <hr className="border-slate-200" />
          <div>
            <Label>Your name</Label>
            <Input required value={adminName} onChange={(e) => setAdminName(e.target.value)} />
          </div>
          <div>
            <Label>Your email</Label>
            <Input type="email" required value={adminEmail} onChange={(e) => setAdminEmail(e.target.value)} />
          </div>
          <div>
            <Label>Password</Label>
            <Input type="password" required minLength={8} value={adminPassword} onChange={(e) => setAdminPassword(e.target.value)} />
          </div>
          <ErrorText>{error}</ErrorText>
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? "Creating…" : "Create organization"}
          </Button>
        </form>
        <p className="mt-4 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-indigo-600 hover:underline">
            Sign in
          </Link>
        </p>
      </Card>
    </div>
  );
}

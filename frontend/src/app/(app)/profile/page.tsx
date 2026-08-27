"use client";

import { FormEvent, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { api, ApiError } from "@/lib/api";
import { Button, Card, ErrorText, Input, Label } from "@/components/ui";

export default function ProfilePage() {
  const { user, refresh } = useAuth();
  const [name, setName] = useState(user?.name || "");
  const [designation, setDesignation] = useState(user?.designation || "");
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSaving, setProfileSaving] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [passwordSaving, setPasswordSaving] = useState(false);

  if (!user) return null;

  async function saveProfile(e: FormEvent) {
    e.preventDefault();
    setProfileError(null);
    setProfileSaving(true);
    try {
      await api.patch("/profile/me", { name, designation });
      await refresh();
    } catch (err) {
      setProfileError(err instanceof ApiError ? err.message : "Failed to update profile");
    } finally {
      setProfileSaving(false);
    }
  }

  async function changePassword(e: FormEvent) {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(false);
    setPasswordSaving(true);
    try {
      await api.post("/auth/change-password", { current_password: currentPassword, new_password: newPassword });
      setPasswordSuccess(true);
      setCurrentPassword("");
      setNewPassword("");
    } catch (err) {
      setPasswordError(err instanceof ApiError ? err.message : "Failed to change password");
    } finally {
      setPasswordSaving(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg space-y-6">
      <h1 className="text-xl font-semibold">Profile</h1>

      <Card className="space-y-4 p-6">
        <h2 className="text-sm font-semibold text-slate-700">Your details</h2>
        <div>
          <Label>Email</Label>
          <Input value={user.email} disabled />
        </div>
        <div>
          <Label>Role</Label>
          <Input value={user.role === "org_admin" ? "Organization Administrator" : "Regular User"} disabled />
        </div>
        <form onSubmit={saveProfile} className="space-y-4">
          <div>
            <Label>Name</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <Label>Designation</Label>
            <Input value={designation} onChange={(e) => setDesignation(e.target.value)} />
          </div>
          <ErrorText>{profileError}</ErrorText>
          <Button type="submit" disabled={profileSaving}>
            {profileSaving ? "Saving…" : "Save profile"}
          </Button>
        </form>
      </Card>

      <Card className="space-y-4 p-6">
        <h2 className="text-sm font-semibold text-slate-700">Change password</h2>
        <form onSubmit={changePassword} className="space-y-4">
          <div>
            <Label>Current password</Label>
            <Input type="password" required value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
          </div>
          <div>
            <Label>New password</Label>
            <Input type="password" required minLength={8} value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          </div>
          <ErrorText>{passwordError}</ErrorText>
          {passwordSuccess && <p className="text-sm text-green-600">Password updated.</p>}
          <Button type="submit" disabled={passwordSaving}>
            {passwordSaving ? "Updating…" : "Update password"}
          </Button>
        </form>
      </Card>
    </div>
  );
}

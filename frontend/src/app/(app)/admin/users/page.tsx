"use client";

import { FormEvent, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { User, Department, UserRole, UserStatus } from "@/lib/types";
import { Button, Card, ErrorText, Input, Label, Select } from "@/components/ui";

export default function UsersAdminPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [designation, setDesignation] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [role, setRole] = useState<UserRole>("regular_user");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setUsers(await api.get<User[]>("/admin/users"));
    setDepartments(await api.get<Department[]>("/admin/departments"));
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post("/admin/users", {
        name,
        email,
        password,
        designation: designation || null,
        department_id: departmentId || null,
        role,
      });
      setName("");
      setEmail("");
      setPassword("");
      setDesignation("");
      setDepartmentId("");
      setRole("regular_user");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create user");
    } finally {
      setSubmitting(false);
    }
  }

  async function toggleStatus(user: User) {
    const next: UserStatus = user.status === "active" ? "inactive" : "active";
    await api.patch(`/admin/users/${user.id}`, { status: next });
    await load();
  }

  async function updateRole(user: User, newRole: UserRole) {
    await api.patch(`/admin/users/${user.id}`, { role: newRole });
    await load();
  }

  async function updateDepartment(user: User, deptId: string) {
    await api.patch(`/admin/users/${user.id}`, { department_id: deptId || null });
    await load();
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Users</h1>

      <Card className="max-w-xl space-y-4 p-6">
        <h2 className="text-sm font-semibold text-slate-700">Add user</h2>
        <form onSubmit={handleCreate} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <Label>Name</Label>
            <Input required value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <Label>Email</Label>
            <Input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <Label>Temporary password</Label>
            <Input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <div>
            <Label>Designation</Label>
            <Input value={designation} onChange={(e) => setDesignation(e.target.value)} />
          </div>
          <div>
            <Label>Department</Label>
            <Select value={departmentId} onChange={(e) => setDepartmentId(e.target.value)}>
              <option value="">—</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label>Role</Label>
            <Select value={role} onChange={(e) => setRole(e.target.value as UserRole)}>
              <option value="regular_user">Regular User</option>
              <option value="org_admin">Organization Administrator</option>
            </Select>
          </div>
          <div className="sm:col-span-2">
            <ErrorText>{error}</ErrorText>
            <Button type="submit" disabled={submitting}>
              {submitting ? "Adding…" : "Add user"}
            </Button>
          </div>
        </form>
      </Card>

      <Card className="overflow-x-auto">
        <table className="w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
              <th className="p-3">Name</th>
              <th className="p-3">Email</th>
              <th className="p-3">Department</th>
              <th className="p-3">Role</th>
              <th className="p-3">Status</th>
              <th className="p-3" />
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-slate-100">
                <td className="p-3">{u.name}</td>
                <td className="p-3 text-slate-500">{u.email}</td>
                <td className="p-3">
                  <Select value={u.department_id || ""} onChange={(e) => updateDepartment(u, e.target.value)}>
                    <option value="">—</option>
                    {departments.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </Select>
                </td>
                <td className="p-3">
                  <Select value={u.role} onChange={(e) => updateRole(u, e.target.value as UserRole)}>
                    <option value="regular_user">Regular User</option>
                    <option value="org_admin">Org Admin</option>
                  </Select>
                </td>
                <td className="p-3">
                  <span className={u.status === "active" ? "text-green-600" : "text-slate-400"}>{u.status}</span>
                </td>
                <td className="p-3">
                  <Button variant="secondary" onClick={() => toggleStatus(u)}>
                    {u.status === "active" ? "Deactivate" : "Activate"}
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

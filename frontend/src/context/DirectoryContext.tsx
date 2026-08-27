"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { api } from "@/lib/api";
import { User, Department, Category } from "@/lib/types";
import { useAuth } from "@/context/AuthContext";

interface DirectoryValue {
  users: User[];
  departments: Department[];
  categories: Category[];
  nameOf: (userId: string | null | undefined) => string;
  loaded: boolean;
}

const DirectoryContext = createContext<DirectoryValue | undefined>(undefined);

export function DirectoryProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!user) return;
    Promise.all([
      api.get<User[]>("/directory/users"),
      api.get<Department[]>("/directory/departments"),
      api.get<Category[]>("/directory/categories"),
    ])
      .then(([u, d, c]) => {
        setUsers(u);
        setDepartments(d);
        setCategories(c);
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, [user]);

  function nameOf(userId: string | null | undefined): string {
    if (!userId) return "—";
    const found = users.find((u) => u.id === userId);
    return found ? found.name : "Unknown user";
  }

  return (
    <DirectoryContext.Provider value={{ users, departments, categories, nameOf, loaded }}>
      {children}
    </DirectoryContext.Provider>
  );
}

export function useDirectory(): DirectoryValue {
  const ctx = useContext(DirectoryContext);
  if (!ctx) throw new Error("useDirectory must be used within DirectoryProvider");
  return ctx;
}

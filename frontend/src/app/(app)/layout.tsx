import AppShell from "@/components/AppShell";
import { DirectoryProvider } from "@/context/DirectoryContext";
import { ReactNode } from "react";

export default function AppGroupLayout({ children }: { children: ReactNode }) {
  return (
    <DirectoryProvider>
      <AppShell>{children}</AppShell>
    </DirectoryProvider>
  );
}

"use client";

import { UserButton } from "@clerk/react";
import Link from "next/link";

import { useUiStore } from "@/shared/stores/ui-store";

import { Button } from "../ui/Button";

export function AppShell({ children }: { children: React.ReactNode }) {
  const { sidebarCollapsed, toggleSidebar } = useUiStore();
  return (
    <div className="flex min-h-screen bg-zinc-950 text-zinc-100">
      <aside
        className={`shrink-0 border-r border-zinc-800 bg-zinc-950 transition-[width] ${sidebarCollapsed ? "w-[72px]" : "w-56"}`}
      >
        <div className="flex h-14 items-center justify-between border-b border-zinc-800 px-3">
          {!sidebarCollapsed && (
            <span className="text-xs font-semibold uppercase tracking-[0.2em] text-zinc-500">
              Governance
            </span>
          )}
          <Button variant="ghost" className="px-2 py-1 text-xs" onClick={toggleSidebar}>
            {sidebarCollapsed ? "»" : "«"}
          </Button>
        </div>
        <nav className="flex flex-col gap-1 p-3 text-sm">
          <Link
            href="/Dashboard/"
            className="rounded-lg px-3 py-2 font-medium text-zinc-200 hover:bg-zinc-900"
          >
            {!sidebarCollapsed ? "Compliance console" : "⌁"}
          </Link>
          <Link
            href="/framework"
            className="rounded-lg px-3 py-2 font-medium text-zinc-200 hover:bg-zinc-900"
          >
            {!sidebarCollapsed ? "Framework library" : ""}
          </Link>
        </nav>
      </aside>
      <div className="flex min-h-screen flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-zinc-800 px-6">
          <div className="text-sm text-zinc-400">
            Autonomous Cybersecurity Compliance{" "}
            <span className="text-zinc-600">&amp;</span> Incident Escalation AI
          </div>
          <UserButton />
        </header>
        <main className="flex-1 overflow-auto bg-gradient-to-br from-zinc-950 via-zinc-950 to-emerald-950/20 p-6 md:p-10">
          {children}
        </main>
      </div>
    </div>
  );
}

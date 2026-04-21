"use client";

import { ClerkProvider } from "@clerk/nextjs";
import { QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { createQueryClient } from "@/shared/api/query-client";

function MissingClerkEnv() {
  return (
    <div className="flex min-h-screen flex-col gap-4 bg-zinc-950 p-10 text-zinc-100">
      <h1 className="text-xl font-semibold text-red-400">Missing Clerk environment variables</h1>
      <p className="max-w-xl text-sm text-zinc-400">
        Set <code className="text-zinc-200">NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</code> and{" "}
        <code className="text-zinc-200">CLERK_SECRET_KEY</code> in the repo-root{" "}
        <code className="text-zinc-200">.env</code> (same file as the backend). Restart{" "}
        <code className="text-zinc-200">npm run dev</code> after saving. See{" "}
        <code className="text-zinc-200">.env.example</code>.
      </p>
    </div>
  );
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => createQueryClient());
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.trim();

  if (!publishableKey) {
    return <MissingClerkEnv />;
  }

  return (
    <ClerkProvider publishableKey={publishableKey}>
      <QueryClientProvider client={client}>{children}</QueryClientProvider>
    </ClerkProvider>
  );
}

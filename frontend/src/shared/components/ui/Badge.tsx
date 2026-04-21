export function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: "neutral" | "warn" | "ok" | "bad";
}) {
  const map = {
    neutral: "border-zinc-700 bg-zinc-900 text-zinc-300",
    warn: "border-amber-700/60 bg-amber-950/80 text-amber-200",
    ok: "border-emerald-700/60 bg-emerald-950/80 text-emerald-200",
    bad: "border-rose-700/60 bg-rose-950/80 text-rose-200",
  } as const;
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium ${map[tone]}`}
    >
      {children}
    </span>
  );
}

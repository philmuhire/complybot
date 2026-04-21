export function Spinner({ label = "Running analysis" }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 text-sm text-zinc-400">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-zinc-600 border-t-emerald-400" />
      {label}
    </div>
  );
}

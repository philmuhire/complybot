import type { HTMLAttributes } from "react";

export function Card({
  children,
  className = "",
  ...props
}: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-xl border border-zinc-800 bg-zinc-950/80 p-6 shadow-xl shadow-black/40 ${className}`}
      {...props}
    >
      {children}
    </div>
  );
}

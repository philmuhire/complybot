"use client";

import type { ButtonHTMLAttributes } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "danger";
};

const cls: Record<NonNullable<Props["variant"]>, string> = {
  primary:
    "rounded-lg bg-emerald-500/90 px-4 py-2 text-sm font-semibold text-zinc-950 hover:bg-emerald-400 disabled:opacity-40",
  ghost:
    "rounded-lg border border-zinc-700 bg-zinc-900/60 px-4 py-2 text-sm text-zinc-100 hover:bg-zinc-800 disabled:opacity-40",
  danger:
    "rounded-lg bg-rose-600/90 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-500 disabled:opacity-40",
};

export function Button({ variant = "primary", className = "", ...props }: Props) {
  return <button type="button" className={`${cls[variant]} ${className}`} {...props} />;
}

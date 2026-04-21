import type { Config } from "tailwindcss";

export default {
  content: [
    // All `className` sources (shared UI, features, app) — missing paths = unstyled dashboard
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
      },
    },
  },
  plugins: [],
} satisfies Config;

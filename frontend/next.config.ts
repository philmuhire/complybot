import type { NextConfig } from "next";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { loadEnvConfig } from "@next/env";

/**
 * Merge env from repo root + `frontend/` (both dirs).
 * Order: repo root first, then frontend — same as Next's rule that `.env.local` wins over `.env`
 * within a directory, so `frontend/.env.local` can override repo-root `.env` for keys you set.
 * Important: blank lines like KEY= in `frontend/.env.local` override earlier values (dotenv).
 */
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendDir = __dirname;
const repoRootBesideFrontend = path.join(frontendDir, "..");
const repoRootFromCwd =
  path.basename(process.cwd()) === "frontend"
    ? path.resolve(process.cwd(), "..")
    : process.cwd();

const dev = process.env.NODE_ENV !== "production";

for (const dir of [
  repoRootBesideFrontend,
  repoRootFromCwd,
  frontendDir,
]) {
  loadEnvConfig(dir, dev);
}

/** S3 + CloudFront: set STATIC_EXPORT=true (see scripts/deploy.sh) */
const staticExport = process.env.STATIC_EXPORT === "true";

const nextConfig: NextConfig = {
  ...(staticExport && {
    output: "export" as const,
    trailingSlash: true,
    images: { unoptimized: true },
  }),
};

export default nextConfig;

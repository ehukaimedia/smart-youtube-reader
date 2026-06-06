import type { NextConfig } from "next";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const frontendRoot = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(frontendRoot, "..");

const nextConfig: NextConfig = {
  turbopack: {
    root: repoRoot,
  },
};

export default nextConfig;

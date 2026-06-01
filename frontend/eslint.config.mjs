import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      // Local-first app: Reader/slicer/demo images are served at runtime from the
      // FastAPI backend on dynamic localhost/tailnet origins (and data: URLs), which
      // next/image's optimizer is not a fit for. Plain <img> is intentional here, so
      // this single rule is disabled while every other rule stays enforced (CI runs
      // lint with --max-warnings 0).
      "@next/next/no-img-element": "off",
    },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;

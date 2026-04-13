import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

export default defineConfig({
  plugins: [react()],
  css: {
    // Note: override postcss to empty to prevent @tailwindcss/postcss from
    // breaking vitest's config-loading phase (Tailwind 4 / Vite 5 incompatibility).
    postcss: { plugins: [] },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: [
      "src/**/*.{test,spec}.{ts,tsx}",
      "tests/**/*.{test,spec}.{ts,tsx}",
    ],
    exclude: ["node_modules", ".next", "dist"],
    css: false,
  },
  resolve: {
    alias: {
      "@features": path.resolve(__dirname, "./src/features"),
      "@shared": path.resolve(__dirname, "./src/shared"),
      "@widgets": path.resolve(__dirname, "./src/widgets"),
      "@": path.resolve(__dirname, "./src"),
    },
  },
});

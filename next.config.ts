import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow external images from trusted hosts used in the app (e.g. avatar placeholders)
  images: {
    // Use `domains` for simple host allowlist
    domains: ["i.pravatar.cc"],
    // Keep default loader/format behavior
  },
};

export default nextConfig;

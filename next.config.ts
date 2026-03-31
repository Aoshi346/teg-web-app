import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow external images from trusted hosts used in the app (e.g. avatar placeholders)
  images: {
    // Use `domains` for simple host allowlist
    domains: ["i.pravatar.cc", "images.unsplash.com"],
    // Remote patterns allow explicit protocol/host matching (Next 13+ recommendation)
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
    ],
  },
};

export default nextConfig;

import type { NextConfig } from "next";

const isFirebaseHosting = process.env.BUILD_FOR_FIREBASE === "1";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  ...(isFirebaseHosting
    ? {
        output: "export",
        trailingSlash: true,
        images: { unoptimized: true },
      }
    : {}),
};

export default nextConfig;

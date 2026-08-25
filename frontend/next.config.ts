import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  // Required for the multi-stage Docker build to produce a lean server.js bundle
  output: "standalone",
  reactStrictMode: false,
}

export default nextConfig

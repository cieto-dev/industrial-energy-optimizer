import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  // Required for the multi-stage Docker build to produce a lean server.js bundle
  output: "standalone",
}

export default nextConfig

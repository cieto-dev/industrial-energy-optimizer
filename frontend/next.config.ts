import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  // Required for Netlify drag and drop static HTML export
  output: "export",
  reactStrictMode: false,
  images: {
    unoptimized: true,
  },
}

export default nextConfig

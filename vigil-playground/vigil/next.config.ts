import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_ROUTER_URL:
      process.env.NEXT_PUBLIC_ROUTER_URL || 'http://localhost:8080',
  },
};

export default nextConfig;

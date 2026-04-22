/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  compiler: {
    // Enable removal of console logs in production
    removeConsole: process.env.NODE_ENV === 'production',
  },
  experimental: {
    // Enable large page optimization
    optimizePackageImports: ['lucide-react', '@radix-ui/react-dialog'],
  },
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
      },
      {
        protocol: 'http',
        hostname: 'backend',
        port: '8000',
      },
    ],
  },
}

module.exports = nextConfig

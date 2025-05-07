/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  transpilePackages: ['@pi-monorepo/ui'],
};

export default nextConfig;

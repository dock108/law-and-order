import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  webpack: (config, { isServer }) => {
    // Ignore require.extensions warnings from handlebars
    config.ignoreWarnings = [
      { module: /node_modules\/handlebars\/lib\/index\.js/ }
    ];
    return config;
  },
};

export default nextConfig;

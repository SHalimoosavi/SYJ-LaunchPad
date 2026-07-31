import type { NextConfig } from "next";

const securityHeaders = [
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  {
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: https:",
      "connect-src 'self' https:",
      "frame-ancestors 'none'",
    ].join("; "),
  },
];

import webpack from "webpack";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  output: "standalone",
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
  webpack: (config) => {
    // wagmi's Base Account connector transitively pulls in Coinbase's
    // @x402/* payment SDK (an optional crypto-payments feature we don't
    // use anywhere in this app). Ignoring it avoids bundling ~unused code
    // and the "module not found" build error it otherwise triggers.
    config.plugins.push(
      new webpack.IgnorePlugin({
        resourceRegExp: /^@x402\//,
      }),
      // MetaMask SDK's React Native code path (unused in a web app) and
      // pino's dev-only pretty-printer (unused since we don't call
      // pino with `transport: pino-pretty` in this project).
      new webpack.IgnorePlugin({
        resourceRegExp: /^@react-native-async-storage\/async-storage$/,
      }),
      new webpack.IgnorePlugin({
        resourceRegExp: /^pino-pretty$/,
      })
    );
    return config;
  },
};

export default nextConfig;

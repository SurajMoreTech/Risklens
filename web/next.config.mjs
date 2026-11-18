/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        // Serve Firebase Auth's redirect handlers (/__/auth/*) same-origin
        // through Next.js — desktop browsers partition cross-origin storage,
        // which breaks the redirect sign-in flow when popups are blocked.
        source: "/__/auth/:path*",
        destination: "https://risklens-eb4fo.firebaseapp.com/__/auth/:path*",
      },
    ];
  },
};

export default nextConfig;

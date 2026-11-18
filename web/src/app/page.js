"use client";

import { AuthProvider } from "@/lib/auth";
import Landing from "@/components/Landing";

export default function HomePage() {
  return (
    <AuthProvider>
      <Landing />
    </AuthProvider>
  );
}

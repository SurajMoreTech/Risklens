"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  GoogleAuthProvider,
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  signOut as firebaseSignOut,
  onAuthStateChanged,
} from "firebase/auth";
import { auth, isDummyConfig, authReady } from "./firebase";

const AuthContext = createContext(null);

// Where to send the user once sign-in finishes. Kept in sessionStorage so it also
// survives the full-page reload of the redirect fallback.
const NEXT_KEY = "risklens_next";
const setNext = (path) => {
  try {
    if (path) sessionStorage.setItem(NEXT_KEY, path);
    else sessionStorage.removeItem(NEXT_KEY);
  } catch (e) { /* ignore */ }
};

const DEMO_USER = {
  uid: "demo-patient-101",
  displayName: "Alex Rivera (Demo)",
  email: "alex.rivera@risklens.demo",
  photoURL: "https://api.dicebear.com/7.x/avataaars/svg?seed=Felix",
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // After a successful sign-in, go to the page the sign-in was started for (e.g. /dashboard).
  useEffect(() => {
    if (!user) return;
    try {
      const next = sessionStorage.getItem(NEXT_KEY);
      if (next) {
        sessionStorage.removeItem(NEXT_KEY);
        router.push(next);
      }
    } catch (e) { /* ignore */ }
  }, [user, router]);

  useEffect(() => {
    if (isDummyConfig) {
      // Demo mode: use in-memory state. Try recovering from sessionStorage
      // as a fallback (more universally available than localStorage).
      try {
        const saved = sessionStorage.getItem("risklens_demo_user");
        if (saved) {
          setUser(JSON.parse(saved));
        }
      } catch (e) {
        // sessionStorage not available — stay logged out in demo mode
      }
      setLoading(false);
      return;
    }

    // Wait for persistence to be configured, then check for a redirect
    // result first (so the user is set before onAuthStateChanged fires),
    // then attach the listener. This eliminates the race where the route
    // guard sees loading=false + user=null and kicks the user back to /.
    let unsubscribe = () => {};
    let cancelled = false;

    (async () => {
      // Await persistence, then FULLY resolve any pending redirect result
      // before attaching the listener / clearing loading. If the listener
      // fires first with user=null, the route guard sees loading=false +
      // user=null and bounces the user back to / (the redirect loop).
      await authReady;
      if (cancelled) return;

      // 1. Pick up any pending redirect result (mobile Safari fallback).
      try {
        const result = await getRedirectResult(auth);
        if (result?.user && !cancelled) {
          setUser(result.user);
        }
      } catch (error) {
        console.warn("Redirect result check:", error.code);
      }
      if (cancelled) return;

      // 2. Attach the persistent listener — this fires immediately with the
      //    cached user from IndexedDB (browserLocalPersistence), so the page
      //    never flashes "logged out" on refresh.
      unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
        if (!cancelled) {
          setUser(firebaseUser);
          setLoading(false);
        }
      });
    })();

    return () => {
      cancelled = true;
      unsubscribe();
    };
  }, []);

  const signInWithGoogle = async (nextPath) => {
    setNext(nextPath); // clears any stale value when no path is given
    if (isDummyConfig) {
      try {
        sessionStorage.setItem("risklens_demo_user", JSON.stringify(DEMO_USER));
      } catch (e) {
        // sessionStorage not available — in-memory only
      }
      setUser(DEMO_USER);
      return DEMO_USER;
    }

    const provider = new GoogleAuthProvider();

    try {
      // Primary: use popup — works across all browsers without redirect loops
      const result = await signInWithPopup(auth, provider);
      return result.user;
    } catch (error) {
      // If popup is blocked (e.g., mobile browsers sometimes block popups),
      // fall back to redirect as a last resort.
      if (error.code === "auth/popup-blocked") {
        console.warn("Popup blocked, falling back to redirect...");
        try {
          await signInWithRedirect(auth, provider);
          return null; // Will redirect — result picked up on return
        } catch (redirectError) {
          console.error("Redirect sign-in also failed:", redirectError);
          setNext(null);
          throw redirectError;
        }
      }
      // Cancelled by the user (closed the popup, or clicked twice) — not an error,
      // and no redirect should start.
      if (
        error.code === "auth/popup-closed-by-user" ||
        error.code === "auth/cancelled-popup-request"
      ) {
        setNext(null);
        return null;
      }
      setNext(null);
      console.error("Google sign-in error:", error);
      throw error;
    }
  };

  const signOut = async () => {
    if (isDummyConfig) {
      try {
        sessionStorage.removeItem("risklens_demo_user");
      } catch (e) {
        // ignore
      }
      setUser(null);
      return;
    }
    try {
      await firebaseSignOut(auth);
    } catch (error) {
      console.error("Sign-out error:", error);
      throw error;
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, signInWithGoogle, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

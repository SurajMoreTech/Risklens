"use client";

import { createContext, useContext, useEffect, useState } from "react";
import {
  GoogleAuthProvider,
  signInWithPopup,
  signInWithRedirect,
  getRedirectResult,
  signOut as firebaseSignOut,
  onAuthStateChanged,
} from "firebase/auth";
import { auth, isDummyConfig } from "./firebase";

const AuthContext = createContext(null);

const DEMO_USER = {
  uid: "demo-patient-101",
  displayName: "Alex Rivera (Demo)",
  email: "alex.rivera@risklens.demo",
  photoURL: "https://api.dicebear.com/7.x/avataaars/svg?seed=Felix",
};

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

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

    // Listen for auth state changes (fires on page load with cached user)
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
      setLoading(false);
    });

    // Check for redirect result (fallback if popup was blocked)
    getRedirectResult(auth)
      .then((result) => {
        if (result?.user) {
          setUser(result.user);
        }
      })
      .catch((error) => {
        // Redirect result errors are non-fatal; the onAuthStateChanged
        // listener is the primary auth state source.
        console.warn("Redirect result check:", error.code);
      });

    return () => unsubscribe();
  }, []);

  const signInWithGoogle = async () => {
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
      if (
        error.code === "auth/popup-blocked" ||
        error.code === "auth/popup-closed-by-user"
      ) {
        console.warn("Popup blocked/closed, falling back to redirect...");
        try {
          await signInWithRedirect(auth, provider);
          return null; // Will redirect — result picked up on return
        } catch (redirectError) {
          console.error("Redirect sign-in also failed:", redirectError);
          throw redirectError;
        }
      }
      // Cancelled by user — don't treat as error
      if (error.code === "auth/cancelled-popup-request") {
        return null;
      }
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

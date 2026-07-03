"use client";

import { createContext, useContext, useEffect, useState } from "react";
import {
  GoogleAuthProvider,
  signInWithRedirect,
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
      const saved = localStorage.getItem("risklens_demo_user");
      if (saved) {
        try { setUser(JSON.parse(saved)); } catch (e) {}
      }
      setLoading(false);
      return;
    }
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      setUser(user);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  const signInWithGoogle = async () => {
    if (isDummyConfig) {
      localStorage.setItem("risklens_demo_user", JSON.stringify(DEMO_USER));
      setUser(DEMO_USER);
      return DEMO_USER;
    }
    const provider = new GoogleAuthProvider();
    try {
      await signInWithRedirect(auth, provider);
      return null;
    } catch (error) {
      console.error("Google sign-in error:", error);
      throw error;
    }
  };

  const signOut = async () => {
    if (isDummyConfig) {
      localStorage.removeItem("risklens_demo_user");
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

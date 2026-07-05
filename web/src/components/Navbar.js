"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const router = useRouter();
  const { user, signInWithGoogle, signOut } = useAuth();
  const mobileMenuRef = useRef(null);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Close mobile menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (
        mobileOpen &&
        mobileMenuRef.current &&
        !mobileMenuRef.current.contains(e.target) &&
        !e.target.closest(".navbar-hamburger")
      ) {
        setMobileOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("touchstart", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("touchstart", handleClickOutside);
    };
  }, [mobileOpen]);

  // Lock body scroll when mobile menu is open
  useEffect(() => {
    if (mobileOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileOpen]);

  const handleSignIn = async () => {
    try {
      await signInWithGoogle();
      setMobileOpen(false);
    } catch (e) {
      console.error("Sign-in failed:", e);
    }
  };

  const handleNavClick = () => {
    setMobileOpen(false);
  };

  return (
    <nav className={`navbar ${scrolled ? "scrolled" : ""}`}>
      <div className="navbar-inner">
        <Link href="/" className="navbar-logo">
          <div className="navbar-logo-icon">🔬</div>
          RiskLens
        </Link>

        {/* Desktop nav links */}
        <ul className="navbar-links">
          <li>
            <Link href="/#how-it-works">How It Works</Link>
          </li>
          <li>
            <Link href="/#about">About</Link>
          </li>
          <li>
            <Link href="/#contact">Contact</Link>
          </li>
          {user && (
            <li>
              <Link href="/dashboard">Dashboard</Link>
            </li>
          )}
        </ul>

        {/* Desktop auth */}
        <div className="navbar-auth">
          {user ? (
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <img
                src={user.photoURL || "/default-avatar.png"}
                alt="Profile"
                className="dashboard-avatar"
                style={{ width: 32, height: 32 }}
                referrerPolicy="no-referrer"
              />
              <button className="btn btn-ghost btn-sm" onClick={() => router.push("/dashboard")}>
                Dashboard
              </button>
              <button className="btn btn-ghost btn-sm" onClick={signOut}>
                Sign Out
              </button>
            </div>
          ) : (
            <button className="btn btn-google" onClick={handleSignIn}>
              <svg width="18" height="18" viewBox="0 0 24 24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
              Sign in with Google
            </button>
          )}
        </div>

        {/* Hamburger button (mobile only) */}
        <button
          className={`navbar-hamburger ${mobileOpen ? "active" : ""}`}
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Toggle navigation menu"
          aria-expanded={mobileOpen}
        >
          <span className="hamburger-line" />
          <span className="hamburger-line" />
          <span className="hamburger-line" />
        </button>
      </div>

      {/* Mobile menu overlay */}
      {mobileOpen && <div className="navbar-mobile-overlay" onClick={() => setMobileOpen(false)} />}

      {/* Mobile slide-out menu */}
      <div
        className={`navbar-mobile-menu ${mobileOpen ? "open" : ""}`}
        ref={mobileMenuRef}
      >
        <ul className="navbar-mobile-links">
          <li>
            <Link href="/#how-it-works" onClick={handleNavClick}>
              How It Works
            </Link>
          </li>
          <li>
            <Link href="/#about" onClick={handleNavClick}>
              About
            </Link>
          </li>
          <li>
            <Link href="/#contact" onClick={handleNavClick}>
              Contact
            </Link>
          </li>
          {user && (
            <li>
              <Link href="/dashboard" onClick={handleNavClick}>
                Dashboard
              </Link>
            </li>
          )}
        </ul>

        <div className="navbar-mobile-auth">
          {user ? (
            <div className="navbar-mobile-user">
              <div className="navbar-mobile-user-info">
                <img
                  src={user.photoURL || "/default-avatar.png"}
                  alt="Profile"
                  className="dashboard-avatar"
                  style={{ width: 36, height: 36 }}
                  referrerPolicy="no-referrer"
                />
                <div>
                  <div style={{ fontWeight: 600, fontSize: "0.92rem", color: "var(--text-primary)" }}>
                    {user.displayName || "User"}
                  </div>
                  <div style={{ fontSize: "0.78rem", color: "var(--text-tertiary)" }}>
                    {user.email}
                  </div>
                </div>
              </div>
              <button
                className="btn btn-primary btn-sm"
                style={{ width: "100%", justifyContent: "center" }}
                onClick={() => {
                  router.push("/dashboard");
                  setMobileOpen(false);
                }}
              >
                📊 Dashboard
              </button>
              <button
                className="btn btn-ghost btn-sm"
                style={{ width: "100%", justifyContent: "center" }}
                onClick={() => {
                  signOut();
                  setMobileOpen(false);
                }}
              >
                Sign Out
              </button>
            </div>
          ) : (
            <button
              className="btn btn-google"
              style={{ width: "100%", justifyContent: "center" }}
              onClick={handleSignIn}
            >
              <svg width="18" height="18" viewBox="0 0 24 24">
                <path
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                  fill="#4285F4"
                />
                <path
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  fill="#34A853"
                />
                <path
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  fill="#FBBC05"
                />
                <path
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  fill="#EA4335"
                />
              </svg>
              Sign in with Google
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}

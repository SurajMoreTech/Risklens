"use client";

import { useState } from "react";
import { useAuth } from "@/lib/auth";

export default function ReportCTA({ onDownload, onEmail, loading }) {
  const { user, signInWithGoogle } = useAuth();
  const [emailSent, setEmailSent] = useState(false);

  const handleEmail = async () => {
    if (onEmail) {
      await onEmail();
      setEmailSent(true);
    }
  };

  return (
    <div className="report-cta">
      <h3>📄 Get Your Full Report</h3>
      <p>
        Download a comprehensive 3-page clinical report with detailed analysis,
        SHAP explainability charts, and personalized recommendations.
      </p>

      <div className="report-cta-buttons">
        <button
          className="btn btn-primary btn-lg"
          onClick={onDownload}
          disabled={loading}
        >
          {loading ? "Generating..." : "📥 Download Full Report (PDF)"}
        </button>
        <button
          className="btn btn-secondary"
          onClick={handleEmail}
          disabled={emailSent}
        >
          {emailSent ? "✓ Email Sent" : "✉️ Email Me a Copy"}
        </button>
      </div>

      {!user && (
        <div className="report-cta-upsell">
          <p>
            🔒{" "}
            <a href="#" onClick={(e) => { e.preventDefault(); signInWithGoogle(); }}>
              Sign in with Google
            </a>{" "}
            to save this report and track your risk over time
          </p>
        </div>
      )}
    </div>
  );
}

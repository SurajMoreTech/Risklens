"use client";

import { AuthProvider } from "@/lib/auth";
import Navbar from "@/components/Navbar";
import Hero from "@/components/Hero";
import HowItWorks from "@/components/HowItWorks";
import Footer from "@/components/Footer";

function AboutSection() {
  return (
    <section className="section" id="about">
      <div className="container">
        <div className="about-grid">
          <div>
            <h2>What is RiskLens?</h2>
            <p style={{ marginTop: "1rem", fontSize: "1.05rem", lineHeight: 1.8 }}>
              RiskLens is an <strong>AI-powered diabetes pre-screening tool</strong> that
              estimates risk from a <strong>5-minute questionnaire</strong> — no blood draw needed.
            </p>
            <p style={{ marginTop: "1rem" }}>
              Trained on <strong>253,680 CDC BRFSS survey records</strong>, it compares four
              machine-learning models (Logistic Regression, Random Forest, XGBoost, LightGBM)
              and auto-selects the best performer. Every prediction includes a{" "}
              <strong>SHAP explanation</strong> showing exactly which factors drive the risk.
            </p>
            <p style={{ marginTop: "1rem" }}>
              This is a <strong>screening triage tool</strong> — it identifies who should
              get an HbA1c blood test, not who has diabetes. Think of it as Stage 1 of a
              two-stage system: questionnaire first (free, fast, scalable), then lab
              confirmation only for those flagged.
            </p>
          </div>
          <div>
            <div className="card" style={{ padding: "0", overflow: "hidden" }}>
              <div className="table-scroll-wrapper">
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr style={{ background: "var(--accent-teal-bg)" }}>
                      <th style={{ padding: "0.85rem 1rem", textAlign: "left", fontSize: "0.85rem", fontWeight: 600, color: "var(--accent-teal)" }}>Score</th>
                      <th style={{ padding: "0.85rem 1rem", textAlign: "left", fontSize: "0.85rem", fontWeight: 600, color: "var(--accent-teal)" }}>Risk Level</th>
                      <th style={{ padding: "0.85rem 1rem", textAlign: "left", fontSize: "0.85rem", fontWeight: 600, color: "var(--accent-teal)" }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr style={{ borderBottom: "1px solid var(--border-light)" }}>
                      <td style={{ padding: "0.85rem 1rem", fontWeight: 600, color: "var(--risk-low)" }}>0 – 29</td>
                      <td style={{ padding: "0.85rem 1rem" }}>✅ Low Risk</td>
                      <td style={{ padding: "0.85rem 1rem", color: "var(--text-tertiary)", fontSize: "0.9rem" }}>Lifestyle counseling, annual rescreening</td>
                    </tr>
                    <tr style={{ borderBottom: "1px solid var(--border-light)" }}>
                      <td style={{ padding: "0.85rem 1rem", fontWeight: 600, color: "var(--risk-moderate)" }}>30 – 69</td>
                      <td style={{ padding: "0.85rem 1rem" }}>⚠️ Moderate</td>
                      <td style={{ padding: "0.85rem 1rem", color: "var(--text-tertiary)", fontSize: "0.9rem" }}>Schedule HbA1c test within 3 months</td>
                    </tr>
                    <tr>
                      <td style={{ padding: "0.85rem 1rem", fontWeight: 600, color: "var(--risk-high)" }}>70 – 100</td>
                      <td style={{ padding: "0.85rem 1rem" }}>🔴 High Risk</td>
                      <td style={{ padding: "0.85rem 1rem", color: "var(--text-tertiary)", fontSize: "0.9rem" }}>Urgent HbA1c test + clinical evaluation</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div className="about-stats-row">
              <div className="card" style={{ textAlign: "center", padding: "1.25rem" }}>
                <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--accent-teal)", fontFamily: "var(--font-heading)" }}>82.3%</div>
                <div style={{ fontSize: "0.82rem", color: "var(--text-tertiary)" }}>Test AUROC</div>
              </div>
              <div className="card" style={{ textAlign: "center", padding: "1.25rem" }}>
                <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--accent-teal)", fontFamily: "var(--font-heading)" }}>78.5%</div>
                <div style={{ fontSize: "0.82rem", color: "var(--text-tertiary)" }}>Sensitivity</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function TrustBanner() {
  return (
    <section style={{
      background: "linear-gradient(135deg, var(--accent-teal), var(--accent-teal-dark))",
      padding: "3rem 0",
      textAlign: "center",
    }}>
      <div className="container">
        <p style={{
          color: "white",
          fontSize: "1.2rem",
          fontStyle: "italic",
          fontFamily: "var(--font-heading)",
          marginBottom: "0.5rem",
        }}>
          &ldquo;34.1 million US adults have diabetes. 88 million have prediabetes — most do not know it.&rdquo;
        </p>
        <p style={{ color: "rgba(255,255,255,0.8)", fontSize: "0.88rem" }}>— CDC, 2020</p>
      </div>
    </section>
  );
}

export default function HomePage() {
  return (
    <AuthProvider>
      <Navbar />
      <main>
        <Hero />
        <TrustBanner />
        <HowItWorks />
        <AboutSection />
      </main>
      <Footer />
    </AuthProvider>
  );
}

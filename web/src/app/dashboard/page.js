"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AuthProvider, useAuth } from "@/lib/auth";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import { getUserAssessments } from "@/lib/firestore";
import { downloadReport } from "@/lib/api";

function DashboardContent() {
  const router = useRouter();
  const { user, loading: authLoading } = useAuth();
  const [assessments, setAssessments] = useState([]);
  const [loadingData, setLoadingData] = useState(true);
  const [selectedAssessment, setSelectedAssessment] = useState(null);
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    if (!authLoading && !user) {
      router.push("/");
    }
  }, [user, authLoading, router]);

  useEffect(() => {
    if (user) {
      loadAssessments();
    }
  }, [user]);

  const loadAssessments = async () => {
    try {
      const data = await getUserAssessments(user.uid);
      setAssessments(data);
    } catch (error) {
      console.error("Error loading assessments:", error);
    } finally {
      setLoadingData(false);
    }
  };

  const handleDownloadReport = async (assessment) => {
    setDownloadingId(assessment.id);
    try {
      await downloadReport({
        patientName: user.displayName || "Patient",
        patientEmail: user.email || "",
        riskScore: assessment.riskScore,
        riskLevel: assessment.riskLevel,
        clinicalAction: assessment.clinicalAction || "",
        inputs: assessment.inputs || {},
        shapValues: assessment.shapValues || {},
        topDrivers: assessment.topDrivers || [],
        protectiveFactors: assessment.protectiveFactors || [],
      });
    } catch (error) {
      console.error("Download error:", error);
      alert("Error generating PDF. Make sure the API server is running.");
    } finally {
      setDownloadingId(null);
    }
  };

  const formatDate = (date) => {
    if (!date) return "N/A";
    const d = date instanceof Date ? date : new Date(date);
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const getRiskClass = (score) => {
    if (score < 30) return "low";
    if (score < 70) return "moderate";
    return "high";
  };

  const getLatestScore = () => {
    if (assessments.length === 0) return "—";
    return assessments[0].riskScore;
  };

  const getScoreTrend = () => {
    if (assessments.length < 2) return null;
    const latest = assessments[0].riskScore;
    const previous = assessments[1].riskScore;
    const diff = latest - previous;
    if (diff > 0) return { direction: "up", value: diff, bad: true };
    if (diff < 0) return { direction: "down", value: Math.abs(diff), bad: false };
    return { direction: "same", value: 0, bad: false };
  };

  if (authLoading || !user) {
    return (
      <>
        <Navbar />
        <div className="loading-container">
          <div className="loading-spinner" />
          <p className="loading-text">Loading...</p>
        </div>
      </>
    );
  }

  const trend = getScoreTrend();

  const FEATURE_LABELS = {
    HighBP: "High Blood Pressure", HighChol: "High Cholesterol",
    CholCheck: "Cholesterol Check", BMI: "BMI", Smoker: "Smoking History",
    Stroke: "Stroke History", HeartDiseaseorAttack: "Heart Disease",
    PhysActivity: "Physical Activity", Fruits: "Daily Fruit",
    Veggies: "Daily Vegetables", HvyAlcoholConsump: "Heavy Alcohol",
    AnyHealthcare: "Healthcare Coverage", NoDocbcCost: "Cost Barrier",
    GenHlth: "General Health", MentHlth: "Mental Health Days",
    PhysHlth: "Physical Health Days", DiffWalk: "Difficulty Walking",
    Sex: "Sex", Age: "Age Group", Education: "Education", Income: "Income",
  };

  return (
    <>
      <Navbar />
      <div className="dashboard-container">
        {/* Header */}
        <div className="dashboard-header">
          <div className="dashboard-profile">
            <img
              src={user.photoURL || "/default-avatar.png"}
              alt="Profile"
              className="dashboard-avatar"
              referrerPolicy="no-referrer"
            />
            <div>
              <h2 style={{ fontSize: "1.4rem", marginBottom: "0.15rem" }}>
                {user.displayName || "User"}
              </h2>
              <p style={{ color: "var(--text-tertiary)", fontSize: "0.88rem" }}>
                {user.email}
              </p>
            </div>
          </div>
          <button
            className="btn btn-primary"
            onClick={() => router.push("/assess")}
          >
            + New Assessment
          </button>
        </div>

        {/* Stats Cards */}
        <div className="dashboard-stats">
          <div className="card stat-card">
            <div className="stat-card-value">{assessments.length}</div>
            <div className="stat-card-label">Total Assessments</div>
          </div>
          <div className="card stat-card">
            <div
              className="stat-card-value"
              style={{
                color: assessments.length > 0
                  ? `var(--risk-${getRiskClass(getLatestScore())})`
                  : "var(--text-muted)",
              }}
            >
              {getLatestScore()}
            </div>
            <div className="stat-card-label">Latest Score</div>
          </div>
          <div className="card stat-card">
            {trend ? (
              <>
                <div
                  className="stat-card-value"
                  style={{
                    color: trend.bad ? "var(--risk-high)" : "var(--risk-low)",
                  }}
                >
                  {trend.direction === "up" ? "↑" : trend.direction === "down" ? "↓" : "→"}{" "}
                  {trend.value} pts
                </div>
                <div className="stat-card-label">
                  {trend.bad ? "Risk Increased" : "Risk Decreased"}
                </div>
              </>
            ) : (
              <>
                <div className="stat-card-value" style={{ color: "var(--text-muted)" }}>—</div>
                <div className="stat-card-label">Trend (need 2+ assessments)</div>
              </>
            )}
          </div>
        </div>

        {/* Score Trend Chart (simple visual) */}
        {assessments.length > 1 && (
          <div className="card" style={{ marginBottom: "2rem", padding: "1.5rem" }}>
            <h3 style={{ marginBottom: "1rem", fontSize: "1.1rem" }}>📈 Risk Score Trend</h3>
            <div style={{ display: "flex", alignItems: "end", gap: "4px", height: "120px", padding: "0 1rem" }}>
              {assessments.slice(0, 10).reverse().map((a, i) => {
                const maxScore = Math.max(...assessments.slice(0, 10).map(x => x.riskScore), 100);
                const height = Math.max((a.riskScore / maxScore) * 100, 8);
                return (
                  <div key={a.id} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
                    <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>{a.riskScore}</span>
                    <div
                      style={{
                        width: "100%",
                        maxWidth: "40px",
                        height: `${height}%`,
                        borderRadius: "4px 4px 0 0",
                        background: `var(--risk-${getRiskClass(a.riskScore)})`,
                        opacity: 0.8,
                        transition: "height 0.5s ease",
                        cursor: "pointer",
                      }}
                      title={`Score: ${a.riskScore} — ${formatDate(a.timestamp)}`}
                      onClick={() => setSelectedAssessment(selectedAssessment?.id === a.id ? null : a)}
                    />
                    <span style={{ fontSize: "0.65rem", color: "var(--text-muted)" }}>
                      {a.timestamp instanceof Date
                        ? a.timestamp.toLocaleDateString("en-US", { month: "short", day: "numeric" })
                        : ""}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Assessment History Table */}
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div style={{ padding: "1.25rem 1.5rem", borderBottom: "1px solid var(--border-light)" }}>
            <h3 style={{ fontSize: "1.1rem" }}>📋 Assessment History</h3>
          </div>

          {assessments.length === 0 ? (
            <div style={{ padding: "3rem", textAlign: "center" }}>
              <p style={{ fontSize: "1.1rem", color: "var(--text-tertiary)", marginBottom: "1rem" }}>
                No assessments yet
              </p>
              <button
                className="btn btn-primary"
                onClick={() => router.push("/assess")}
              >
                Take Your First Assessment
              </button>
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Score</th>
                    <th>Risk Level</th>
                    <th>Action</th>
                    <th>Report</th>
                  </tr>
                </thead>
                <tbody>
                  {assessments.map((a) => (
                    <tr
                      key={a.id}
                      onClick={() => setSelectedAssessment(selectedAssessment?.id === a.id ? null : a)}
                      style={{ cursor: "pointer" }}
                    >
                      <td>{formatDate(a.timestamp)}</td>
                      <td>
                        <span className={`score-dot ${getRiskClass(a.riskScore)}`} />
                        <strong>{a.riskScore}</strong> / 100
                      </td>
                      <td>
                        <span className={`risk-badge ${getRiskClass(a.riskScore)}`} style={{ fontSize: "0.82rem", padding: "0.3rem 0.8rem" }}>
                          {a.riskLevel}
                        </span>
                      </td>
                      <td style={{ fontSize: "0.85rem", color: "var(--text-tertiary)", maxWidth: "200px" }}>
                        {a.clinicalAction || "—"}
                      </td>
                      <td>
                        <button
                          className="btn btn-ghost btn-sm"
                          onClick={(e) => { e.stopPropagation(); handleDownloadReport(a); }}
                          disabled={downloadingId === a.id}
                        >
                          {downloadingId === a.id ? "..." : "📥 PDF"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Selected Assessment Detail */}
        {selectedAssessment && (
          <div className="card" style={{ marginTop: "1.5rem", animation: "slideUp 0.3s ease-out" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
              <h3 style={{ fontSize: "1.1rem" }}>
                🔍 Assessment Detail — {formatDate(selectedAssessment.timestamp)}
              </h3>
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => setSelectedAssessment(null)}
              >
                ✕ Close
              </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.5rem" }}>
              <div style={{ textAlign: "center", padding: "1rem", background: "var(--bg-secondary)", borderRadius: "var(--radius-md)" }}>
                <div style={{ fontSize: "2rem", fontWeight: 700, color: `var(--risk-${getRiskClass(selectedAssessment.riskScore)})`, fontFamily: "var(--font-heading)" }}>
                  {selectedAssessment.riskScore}
                </div>
                <div style={{ fontSize: "0.82rem", color: "var(--text-tertiary)" }}>Risk Score</div>
              </div>
              <div style={{ textAlign: "center", padding: "1rem", background: "var(--bg-secondary)", borderRadius: "var(--radius-md)" }}>
                <div style={{ fontSize: "1.2rem", fontWeight: 700, color: `var(--risk-${getRiskClass(selectedAssessment.riskScore)})` }}>
                  {selectedAssessment.riskLevel}
                </div>
                <div style={{ fontSize: "0.82rem", color: "var(--text-tertiary)" }}>Risk Level</div>
              </div>
            </div>

            {/* Input values */}
            {selectedAssessment.inputs && (
              <div style={{ marginBottom: "1.5rem" }}>
                <h4 style={{ fontSize: "0.95rem", marginBottom: "0.75rem", color: "var(--text-secondary)" }}>
                  Health Indicators
                </h4>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "0.5rem" }}>
                  {Object.entries(selectedAssessment.inputs).map(([key, value]) => (
                    <div key={key} style={{ display: "flex", justifyContent: "space-between", padding: "0.5rem 0.75rem", background: "var(--bg-secondary)", borderRadius: "var(--radius-sm)", fontSize: "0.85rem" }}>
                      <span style={{ color: "var(--text-tertiary)" }}>{FEATURE_LABELS[key] || key}</span>
                      <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>{value}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Top drivers */}
            {selectedAssessment.topDrivers && selectedAssessment.topDrivers.length > 0 && (
              <div>
                <h4 style={{ fontSize: "0.95rem", marginBottom: "0.75rem", color: "var(--text-secondary)" }}>
                  Top Risk Drivers
                </h4>
                {selectedAssessment.topDrivers.slice(0, 3).map((d, i) => (
                  <div key={i} className="shap-driver" style={{ marginBottom: "0.5rem" }}>
                    <div className="shap-driver-info">
                      <div className="shap-driver-icon positive">▲</div>
                      <div>
                        <div className="shap-driver-name">{FEATURE_LABELS[d.feature] || d.feature}</div>
                        <div className="shap-driver-value">Value: {d.value}</div>
                      </div>
                    </div>
                    <div className="shap-driver-impact positive">
                      +{Math.abs((d.shapValue || 0) * 100).toFixed(0)} pts
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      <Footer />
    </>
  );
}

export default function DashboardPage() {
  return (
    <AuthProvider>
      <DashboardContent />
    </AuthProvider>
  );
}

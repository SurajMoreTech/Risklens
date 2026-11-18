import { auth, isDummyConfig } from "./firebase";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ---------------------------------------------------------------------------
// Helper: get a fresh Firebase ID token for the current user.
// Returns null in demo mode (no real Firebase user).
// ---------------------------------------------------------------------------
async function getIdToken(userOverride = null) {
  if (isDummyConfig) return null;
  // Prefer the caller-provided user (just signed in) over auth.currentUser,
  // which can still be stale immediately after a popup/redirect sign-in.
  const user = userOverride || auth.currentUser;
  if (!user) return null;
  return user.getIdToken();
}

// Build auth headers — omit Authorization in demo mode so the API can still
// be called without a Firebase project configured locally.
async function authHeaders(userOverride = null) {
  const token = await getIdToken(userOverride);
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ---------------------------------------------------------------------------
// Helper: turn a FastAPI error body into a readable message. HTTP 422
// validation errors return detail as an array of { loc, msg } objects —
// format those explicitly so the message never shows "[object Object]".
// ---------------------------------------------------------------------------
function parseApiError(errorBody, fallback) {
  if (!errorBody) return fallback;
  if (Array.isArray(errorBody.detail)) {
    return errorBody.detail
      .map((err) => `${err.loc.slice(1).join(".")}: ${err.msg}`)
      .join("; ");
  }
  return errorBody.detail || JSON.stringify(errorBody);
}

// ---------------------------------------------------------------------------
// POST /api/predict
// ---------------------------------------------------------------------------
export async function predictRisk(inputs, userOverride = null) {
  console.log("[RiskLens API] POST /api/predict →", API_BASE);
  console.log("[RiskLens API] Payload keys:", Object.keys(inputs).sort());
  console.log("[RiskLens API] Payload:", JSON.stringify(inputs));

  let response;
  try {
    response = await fetch(`${API_BASE}/api/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(await authHeaders(userOverride)),
      },
      body: JSON.stringify(inputs),
    });
  } catch (networkError) {
    console.error("[RiskLens API] Network error:", networkError);
    throw new Error(
      "Cannot reach the prediction server. Make sure the API is running."
    );
  }

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const errorBody = await response.json();
      detail = parseApiError(errorBody, detail);
    } catch {
      // couldn't parse error body
    }
    console.error("[RiskLens API] Error response:", detail);
    throw new Error(detail);
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// POST /api/report/pdf
// ---------------------------------------------------------------------------
export async function downloadReport(reportData) {
  const response = await fetch(`${API_BASE}/api/report/pdf`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(await authHeaders()),
    },
    body: JSON.stringify(reportData),
  });

  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try {
      const errorBody = await response.json();
      detail = parseApiError(errorBody, detail);
    } catch {
      // couldn't parse error body
    }
    console.error("[RiskLens API] Report error response:", detail);
    throw new Error(`Report generation failed (${detail})`);
  }

  // Use the server-supplied filename from Content-Disposition when available
  const disposition = response.headers.get("Content-Disposition") ?? "";
  const match = disposition.match(/filename="([^"]+)"/);
  const filename = match ? match[1] : "risklensreport.pdf";

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }, 300);
}

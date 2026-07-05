const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function predictRisk(inputs) {
  console.log("[RiskLens API] POST /api/predict →", API_BASE);

  let response;
  try {
    response = await fetch(`${API_BASE}/api/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
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
      detail = errorBody.detail || JSON.stringify(errorBody);
    } catch {
      // couldn't parse error body
    }
    console.error("[RiskLens API] Error response:", detail);
    throw new Error(detail);
  }

  return response.json();
}

export async function downloadReport(reportData) {
  const response = await fetch(`${API_BASE}/api/report/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(reportData),
  });

  if (!response.ok) {
    throw new Error("Report generation failed");
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "risklensreport.pdf";
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  }, 300);
}

"""
pages/1_🩺_My_Dashboard.py — RiskLens Personal Dashboard
═══════════════════════════════════════════════════════════
A personal dashboard for a logged-in user showing:
  • Profile header & session stats
  • Risk score trend chart
  • Assessment history table
  • Detailed SHAP breakdown of selected assessment
  • PDF download for any assessment

Run via:  streamlit run app/app.py
This page appears automatically in the sidebar as "My Dashboard".
"""

import os
import sys
import json
import base64
import io as _io
from datetime import datetime

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# ── Path setup ─────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(_HERE, "..", "..", "src"))
sys.path.append(os.path.join(_HERE, "..", ".."))

MODEL_DIR = os.path.join(_HERE, "..", "..", "models")

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="My Dashboard — RiskLens",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===================================================================
#  CUSTOM CSS
# ===================================================================
DASHBOARD_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #080f1e 0%, #0d1829 100%); }
#MainMenu, footer, header { visibility: hidden; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F2B46 0%, #080f1e 100%);
}
section[data-testid="stSidebar"] [data-testid="stMarkdown"] p,
section[data-testid="stSidebar"] [data-testid="stMarkdown"] li {
    color: #c8d6e5 !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background: rgba(13,148,136,0.07);
    border: 1px solid rgba(13,148,136,0.2);
    border-radius: 14px;
    padding: 1rem 1.2rem;
}
[data-testid="stMetricLabel"] { color: #8899aa !important; font-size: 0.82rem !important; }
[data-testid="stMetricValue"] { color: #e2e8f0 !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"] { font-size: 0.85rem !important; }

/* Card wrapper */
.dash-card {
    background: rgba(14,26,46,0.85);
    border: 1px solid rgba(30,58,95,0.7);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.dash-card h3 {
    color: #e2e8f0;
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 1.05rem;
    margin-bottom: 0.8rem;
}

/* Assessment history table */
.hist-table { width:100%; border-collapse:collapse; }
.hist-table th {
    text-align:left; padding:0.65rem 1rem;
    color:#8899aa; font-size:0.78rem;
    text-transform:uppercase; letter-spacing:0.8px;
    border-bottom:1px solid rgba(30,58,95,0.7);
}
.hist-table td {
    padding:0.75rem 1rem;
    color:#c8d6e5; font-size:0.9rem;
    border-bottom:1px solid rgba(30,58,95,0.35);
    vertical-align:middle;
}
.hist-table tr:hover td { background:rgba(13,148,136,0.05); }
.badge-low  { background:rgba(167,196,160,0.15); color:#A7C4A0; border:1px solid #A7C4A0; border-radius:999px; padding:2px 12px; font-size:0.78rem; font-weight:600; }
.badge-mod  { background:rgba(230,168,23,0.15);  color:#e6a817; border:1px solid #e6a817; border-radius:999px; padding:2px 12px; font-size:0.78rem; font-weight:600; }
.badge-high { background:rgba(232,146,124,0.15); color:#E8927C; border:1px solid #E8927C; border-radius:999px; padding:2px 12px; font-size:0.78rem; font-weight:600; }

/* Profile header */
.profile-header {
    background: linear-gradient(135deg, #0F2B46, #1E3A5F);
    border: 1px solid rgba(13,148,136,0.25);
    border-radius: 18px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.5rem;
    display: flex; align-items: center; gap: 1.5rem;
}

/* Trend bar */
.trend-bar-wrap { display:flex; align-items:flex-end; gap:6px; height:110px; padding:0 0.5rem; }
.trend-bar { border-radius:6px 6px 0 0; min-width:28px; cursor:pointer; transition:opacity .2s; }
.trend-bar:hover { opacity:0.75; }

/* Shap row */
.shap-row { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.shap-label { color:#c8d6e5; font-size:0.85rem; min-width:180px; }
.shap-bar-pos { background:linear-gradient(90deg,#E8927C,#e06040); border-radius:4px; height:18px; }
.shap-bar-neg { background:linear-gradient(90deg,#0D9488,#0a7a71); border-radius:4px; height:18px; }
.shap-val  { color:#8899aa; font-size:0.78rem; min-width:40px; text-align:right; }

/* Dashboard title */
.dash-title {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 2rem; font-weight: 800;
    background: linear-gradient(90deg,#5eead4,#0D9488);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0;
}
.dash-sub { color:#8899aa; font-size:0.95rem; margin-top:2px; }
</style>
"""
st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)


# ===================================================================
#  FEATURE LABEL MAP
# ===================================================================
FEATURE_LABELS = {
    "HighBP": "High Blood Pressure", "HighChol": "High Cholesterol",
    "CholCheck": "Cholesterol Check (5yr)", "BMI": "BMI",
    "Smoker": "Smoking History", "Stroke": "Stroke History",
    "HeartDiseaseorAttack": "Heart Disease / MI",
    "PhysActivity": "Physical Activity", "Fruits": "Daily Fruit Intake",
    "Veggies": "Daily Vegetable Intake", "HvyAlcoholConsump": "Heavy Alcohol Use",
    "AnyHealthcare": "Healthcare Coverage", "NoDocbcCost": "Cost Barrier to Doctor",
    "GenHlth": "General Health (1–5)", "MentHlth": "Mental Health Days",
    "PhysHlth": "Physical Health Days", "DiffWalk": "Difficulty Walking",
    "Sex": "Sex", "Age": "Age Group", "Education": "Education Level",
    "Income": "Income Level",
}


# ===================================================================
#  HELPERS
# ===================================================================
def risk_color(score):
    if score < 30: return "#A7C4A0"
    if score < 70: return "#e6a817"
    return "#E8927C"

def risk_label(score):
    if score < 30: return "Low Risk", "badge-low"
    if score < 70: return "Moderate Risk", "badge-mod"
    return "High Risk", "badge-high"

def format_dt(dt):
    if isinstance(dt, str):
        try: dt = datetime.fromisoformat(dt)
        except: return dt
    if isinstance(dt, datetime):
        return dt.strftime("%b %d, %Y  %I:%M %p")
    return str(dt)

def load_model_artifacts():
    try:
        model      = joblib.load(os.path.join(MODEL_DIR, "best_model.pkl"))
        model_name = joblib.load(os.path.join(MODEL_DIR, "model_name.pkl"))
        threshold  = joblib.load(os.path.join(MODEL_DIR, "threshold.pkl")) if os.path.exists(os.path.join(MODEL_DIR,"threshold.pkl")) else 0.5
        return model, model_name, threshold
    except:
        return None, None, None


# ===================================================================
#  SESSION / HISTORY  (stored in st.session_state)
# ===================================================================
def get_history():
    """Return assessment history list from session state."""
    return st.session_state.get("risklens_history", [])

def save_assessment(entry: dict):
    """Append a new assessment entry to history."""
    history = get_history()
    entry["id"] = f"assess-{len(history)+1:03d}"
    entry["timestamp"] = datetime.now().isoformat()
    history.insert(0, entry)
    st.session_state["risklens_history"] = history


# ===================================================================
#  PDF DOWNLOAD  (calls FastAPI)
# ===================================================================
def download_pdf_from_api(assessment: dict, patient_name: str, patient_email: str) -> bytes | None:
    try:
        import requests
        api_base = "http://localhost:8000"
        payload = {
            "patientName": patient_name,
            "patientEmail": patient_email,
            "riskScore": assessment.get("riskScore", 0),
            "riskLevel": assessment.get("riskLevel", "Unknown"),
            "clinicalAction": assessment.get("clinicalAction", ""),
            "inputs": assessment.get("inputs", {}),
            "shapValues": assessment.get("shapValues", {}),
            "topDrivers": assessment.get("topDrivers", []),
            "protectiveFactors": assessment.get("protectiveFactors", []),
        }
        resp = requests.post(f"{api_base}/api/report/pdf", json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.content
        st.error(f"API Error {resp.status_code}: {resp.text[:200]}")
        return None
    except Exception as e:
        st.error(f"Could not reach API server: {e}")
        return None


# ===================================================================
#  MAIN DASHBOARD
# ===================================================================
def main():

    # ── Sidebar profile / nav ─────────────────────────────────────
    with st.sidebar:
        st.markdown(
            "<h1 style='text-align:center;color:#0D9488;"
            "font-family:Plus Jakarta Sans,sans-serif;"
            "font-size:1.6rem;margin-bottom:0;'>🔬 RiskLens</h1>"
            "<p style='text-align:center;color:#A7C4A0;font-size:0.8rem;"
            "margin-top:2px;letter-spacing:1.5px;'>PERSONAL DASHBOARD</p>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # Patient name input (simple auth for Streamlit)
        if "patient_name" not in st.session_state:
            st.session_state["patient_name"] = ""
        if "patient_email" not in st.session_state:
            st.session_state["patient_email"] = ""

        st.markdown("<p style='color:#8899aa;font-size:0.8rem;'>👤 Your profile</p>", unsafe_allow_html=True)
        patient_name = st.text_input("Your Name", value=st.session_state["patient_name"], placeholder="e.g. Alex Rivera")
        patient_email = st.text_input("Email (optional)", value=st.session_state["patient_email"], placeholder="alex@email.com")
        if patient_name:
            st.session_state["patient_name"] = patient_name
        if patient_email:
            st.session_state["patient_email"] = patient_email

        st.markdown("---")

        model, model_name, threshold = load_model_artifacts()
        if model_name:
            st.markdown(
                f"<p style='color:#556677;font-size:0.72rem;text-align:center;'>"
                f"Model: {model_name}<br>"
                f"Threshold: {int(threshold*100)}%<br>"
                f"Dataset: CDC BRFSS (253,680 records)"
                f"</p>",
                unsafe_allow_html=True,
            )
        st.markdown("---")
        if st.button("🏠 Go to Main App", use_container_width=True):
            st.switch_page("app.py")

    # ── Page title ────────────────────────────────────────────────
    st.markdown(
        "<p class='dash-title'>🩺 My Personal Dashboard</p>"
        "<p class='dash-sub'>Your diabetes risk assessment history, trends, and detailed health insights</p>"
        "<hr style='border-color:rgba(30,58,95,0.6);margin:1rem 0 1.5rem;'>",
        unsafe_allow_html=True,
    )

    if not st.session_state.get("patient_name"):
        st.info("👈 Please enter your name in the sidebar to get started, then run an assessment from the main page.")
        st.stop()

    display_name = st.session_state["patient_name"]
    history = get_history()

    # ── Profile header ────────────────────────────────────────────
    st.markdown(
        f"""
        <div style='background:linear-gradient(135deg,#0F2B46,#1E3A5F);
            border:1px solid rgba(13,148,136,0.25);border-radius:18px;
            padding:1.6rem 2rem;margin-bottom:1.5rem;'>
        <div style='display:flex;align-items:center;gap:1.2rem;'>
            <div style='width:58px;height:58px;border-radius:50%;
                background:linear-gradient(135deg,#0D9488,#5eead4);
                display:flex;align-items:center;justify-content:center;
                font-size:1.5rem;font-weight:800;color:#0a0f1e;'>
                {display_name[0].upper()}
            </div>
            <div>
                <p style='color:#e2e8f0;font-family:Plus Jakarta Sans,sans-serif;
                    font-size:1.3rem;font-weight:700;margin:0;'>
                    {display_name}
                </p>
                <p style='color:#8899aa;font-size:0.85rem;margin:2px 0 0;'>
                    {st.session_state.get("patient_email","") or "No email set"} &nbsp;·&nbsp;
                    {len(history)} assessment{"s" if len(history) != 1 else ""} recorded
                </p>
            </div>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Stat metrics ──────────────────────────────────────────────
    latest_score = history[0]["riskScore"] if history else None
    avg_score    = round(sum(h["riskScore"] for h in history) / len(history)) if history else None
    trend_delta  = None
    if len(history) >= 2:
        trend_delta = history[0]["riskScore"] - history[1]["riskScore"]

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    with col_s1:
        st.metric("📋 Total Assessments", len(history))
    with col_s2:
        if latest_score is not None:
            lbl, _ = risk_label(latest_score)
            st.metric("🎯 Latest Score", f"{latest_score}/100", delta=lbl)
        else:
            st.metric("🎯 Latest Score", "—")
    with col_s3:
        if avg_score is not None:
            st.metric("📊 Average Score", f"{avg_score}/100")
        else:
            st.metric("📊 Average Score", "—")
    with col_s4:
        if trend_delta is not None:
            direction = "↑ Risk Up" if trend_delta > 0 else ("↓ Risk Down" if trend_delta < 0 else "→ No Change")
            st.metric("📈 Trend", f"{abs(trend_delta)} pts", delta=direction,
                      delta_color="inverse" if trend_delta > 0 else "normal")
        else:
            st.metric("📈 Trend", "—", help="Need 2+ assessments")

    st.markdown("<div style='height:1.2rem;'></div>", unsafe_allow_html=True)

    if not history:
        st.markdown(
            """
            <div style='text-align:center;padding:4rem 2rem;
                background:rgba(14,26,46,0.85);border:1px solid rgba(30,58,95,0.7);
                border-radius:16px;'>
            <p style='font-size:3rem;'>🩺</p>
            <p style='color:#e2e8f0;font-size:1.2rem;font-weight:600;font-family:Plus Jakarta Sans,sans-serif;'>
                No assessments yet
            </p>
            <p style='color:#8899aa;font-size:0.95rem;'>
                Complete the health questionnaire on the main page to see your results here.
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

    # ── Risk Score Trend Chart ─────────────────────────────────────
    if len(history) > 1:
        with st.expander("📈 Risk Score Trend", expanded=True):
            chart_data = list(reversed(history[:12]))
            scores = [h["riskScore"] for h in chart_data]
            labels = [format_dt(h["timestamp"])[:6] for h in chart_data]

            fig, ax = plt.subplots(figsize=(10, 3))
            fig.patch.set_facecolor("#0d1829")
            ax.set_facecolor("#0d1829")

            bar_colors = [risk_color(s) for s in scores]
            bars = ax.bar(range(len(scores)), scores, color=bar_colors,
                          alpha=0.85, width=0.65, zorder=3)

            # Value labels on bars
            for bar, score in zip(bars, scores):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.8,
                        str(score), ha="center", va="bottom",
                        color="#e2e8f0", fontsize=9, fontweight="bold")

            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, color="#8899aa", fontsize=8, rotation=20)
            ax.set_ylim(0, 105)
            ax.set_ylabel("Risk Score", color="#8899aa", fontsize=9)
            ax.tick_params(colors="#8899aa")
            ax.spines[:].set_color("rgba(30,58,95,0.5)")
            ax.yaxis.grid(True, color="rgba(30,58,95,0.4)", linestyle="--", linewidth=0.5)
            ax.set_axisbelow(True)

            # Threshold lines
            ax.axhline(y=30, color="#A7C4A0", linestyle="--", linewidth=1, alpha=0.5, label="Low/Mod threshold")
            ax.axhline(y=70, color="#E8927C", linestyle="--", linewidth=1, alpha=0.5, label="Mod/High threshold")
            ax.legend(facecolor="#0d1829", labelcolor="#8899aa", fontsize=8, framealpha=0.6)

            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)

    # ── Assessment History Table ───────────────────────────────────
    st.markdown(
        "<div class='dash-card'><h3>📋 Assessment History</h3>",
        unsafe_allow_html=True,
    )

    table_rows = ""
    for i, h in enumerate(history):
        lbl, badge_cls = risk_label(h["riskScore"])
        color = risk_color(h["riskScore"])
        table_rows += f"""
        <tr>
            <td>{format_dt(h.get('timestamp',''))}</td>
            <td><span style='color:{color};font-weight:700;font-size:1.05rem;'>{h['riskScore']}</span>
                <span style='color:#556677;font-size:0.82rem;'>/100</span></td>
            <td><span class='{badge_cls}'>{lbl}</span></td>
            <td style='color:#8899aa;font-size:0.85rem;max-width:240px;'>{h.get('clinicalAction','—')}</td>
            <td style='color:#556677;font-size:0.82rem;'>{h.get('id','')}</td>
        </tr>
        """

    st.markdown(
        f"""
        <div style='overflow-x:auto;'>
        <table class='hist-table'>
            <thead><tr>
                <th>Date & Time</th><th>Score</th><th>Risk Level</th>
                <th>Recommendation</th><th>ID</th>
            </tr></thead>
            <tbody>{table_rows}</tbody>
        </table>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Selected Assessment Detail ─────────────────────────────────
    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#8899aa;font-size:0.85rem;'>👇 Select an assessment to view full details and download PDF</p>",
        unsafe_allow_html=True,
    )

    assess_options = {f"#{i+1} — {format_dt(h['timestamp'])} | Score: {h['riskScore']}/100": h
                      for i, h in enumerate(history)}
    selected_key = st.selectbox("Select Assessment", list(assess_options.keys()), label_visibility="collapsed")
    selected = assess_options[selected_key]

    col_left, col_right = st.columns([1.4, 1])

    # ── Left: detail ──────────────────────────────────────────────
    with col_left:
        score  = selected["riskScore"]
        lbl, _ = risk_label(score)
        color  = risk_color(score)

        st.markdown(
            f"""
            <div class='dash-card'>
            <h3>🔍 Assessment Detail</h3>
            <div style='display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.2rem;'>
                <div style='text-align:center;padding:1rem;background:rgba(0,0,0,0.25);border-radius:12px;'>
                    <p style='color:#8899aa;font-size:0.78rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;'>Risk Score</p>
                    <p style='color:{color};font-size:2.8rem;font-weight:800;font-family:Plus Jakarta Sans,sans-serif;margin:0;'>
                        {score}<span style='font-size:1.2rem;color:#556677;'>/100</span>
                    </p>
                </div>
                <div style='text-align:center;padding:1rem;background:rgba(0,0,0,0.25);border-radius:12px;'>
                    <p style='color:#8899aa;font-size:0.78rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;'>Risk Level</p>
                    <p style='color:{color};font-size:1.5rem;font-weight:700;font-family:Plus Jakarta Sans,sans-serif;margin:0;'>
                        {lbl}
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Clinical recommendation
        action = selected.get("clinicalAction", "")
        if action:
            icon = "🔴" if score >= 70 else ("⚠️" if score >= 30 else "✅")
            border = "#E8927C" if score >= 70 else ("#e6a817" if score >= 30 else "#A7C4A0")
            txt_col = "#f4a997" if score >= 70 else ("#f0d060" if score >= 30 else "#bfe0b8")
            st.markdown(
                f"<div style='background:rgba(0,0,0,0.2);border-left:3px solid {border};"
                f"padding:0.75rem 1rem;border-radius:8px;margin-bottom:1rem;'>"
                f"<p style='color:{txt_col};font-size:0.88rem;margin:0;'>"
                f"{icon} <b>Recommendation:</b> {action}</p></div>",
                unsafe_allow_html=True,
            )

        # Health indicators
        inputs = selected.get("inputs", {})
        if inputs:
            st.markdown("<p style='color:#8899aa;font-size:0.82rem;text-transform:uppercase;"
                        "letter-spacing:0.8px;margin-bottom:8px;'>Health Indicators</p>",
                        unsafe_allow_html=True)
            inp_rows = ""
            for k, v in inputs.items():
                lab = FEATURE_LABELS.get(k, k)
                inp_rows += (
                    f"<div style='display:flex;justify-content:space-between;"
                    f"padding:6px 10px;background:rgba(0,0,0,0.2);border-radius:6px;"
                    f"margin-bottom:4px;font-size:0.83rem;'>"
                    f"<span style='color:#8899aa;'>{lab}</span>"
                    f"<span style='color:#e2e8f0;font-weight:600;'>{v}</span></div>"
                )
            st.markdown(f"<div style='max-height:240px;overflow-y:auto;'>{inp_rows}</div>",
                        unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Right: SHAP drivers + PDF ──────────────────────────────────
    with col_right:
        top_drivers       = selected.get("topDrivers", [])
        protective_factors= selected.get("protectiveFactors", [])

        if top_drivers or protective_factors:
            st.markdown("<div class='dash-card'><h3>🧠 SHAP Risk Drivers</h3>", unsafe_allow_html=True)

            all_shap = [(d.get("featureLabel") or FEATURE_LABELS.get(d.get("feature",""), d.get("feature","")),
                         d.get("shapValue", 0))
                        for d in (top_drivers + protective_factors)]
            if all_shap:
                max_abs = max(abs(v) for _, v in all_shap) or 1
                shap_rows = ""
                for label, val in sorted(all_shap, key=lambda x: -abs(x[1]))[:10]:
                    bar_pct = int(abs(val) / max_abs * 160)
                    bar_cls = "shap-bar-pos" if val > 0 else "shap-bar-neg"
                    sign = "+" if val > 0 else ""
                    shap_rows += (
                        f"<div class='shap-row'>"
                        f"<div class='shap-label'>{label[:22]}</div>"
                        f"<div class='{bar_cls}' style='width:{bar_pct}px;'></div>"
                        f"<div class='shap-val'>{sign}{val:.3f}</div>"
                        f"</div>"
                    )
                st.markdown(shap_rows, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # ── PDF Download ────────────────────────────────────────────
        st.markdown("<div class='dash-card'><h3>📄 PDF Report</h3>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color:#8899aa;font-size:0.85rem;'>Generate and download your clinical risk assessment PDF report.</p>",
            unsafe_allow_html=True,
        )

        # Check if API is reachable
        api_ok = False
        try:
            import requests
            r = requests.get("http://localhost:8000/api/health", timeout=2)
            api_ok = r.status_code == 200
        except:
            pass

        if not api_ok:
            st.warning("⚠️ API server is not running. Start it with:\n\n`python -m uvicorn api.main:app --port 8000`")
        else:
            patient_name_val  = st.session_state.get("patient_name", "Patient")
            patient_email_val = st.session_state.get("patient_email", "")

            if st.button("📥 Download risklensreport.pdf", type="primary", use_container_width=True):
                with st.spinner("Generating PDF…"):
                    pdf_bytes = download_pdf_from_api(selected, patient_name_val, patient_email_val)
                if pdf_bytes:
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = (
                        f'<a href="data:application/pdf;base64,{b64}" '
                        f'download="risklensreport.pdf" '
                        f'style="display:inline-block;background:linear-gradient(135deg,#0D9488,#0a7a71);'
                        f'color:#fff;text-decoration:none;padding:0.6rem 1.5rem;border-radius:10px;'
                        f'font-weight:600;font-size:0.92rem;margin-top:8px;">'
                        f'✅ Click here to save risklensreport.pdf</a>'
                    )
                    st.markdown(href, unsafe_allow_html=True)
                    st.success(f"PDF ready! ({len(pdf_bytes)//1024} KB)")

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Disclaimer ─────────────────────────────────────────────────
    st.markdown(
        """
        <div style='margin-top:2rem;text-align:center;padding:1rem;
            background:rgba(14,26,46,0.6);border-radius:12px;
            border:1px solid rgba(30,58,95,0.4);'>
        <p style='color:#556677;font-size:0.8rem;margin:0;'>
            ⚕️ RiskLens is a <b style='color:#8899aa;'>pre-screening tool</b> — not a clinical diagnosis.
            Results do not replace professional medical advice. Always consult a healthcare provider.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ===================================================================
#  ENTRY POINT
# ===================================================================
main()

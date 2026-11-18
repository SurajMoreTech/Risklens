"""
app.py — RiskLens v2: Diabetes Risk Pre-Screening Tool
═══════════════════════════════════════════════════════
Dataset:  CDC BRFSS Diabetes Health Indicators (253,680 records)
Model:    Best of LR / RF / XGBoost / LightGBM (auto-selected)
Features: 21 questionnaire features + 4 engineered = 25 total

This is a SCREENING TRIAGE tool — no blood test required.
Input:  5-minute patient questionnaire (21 items)
Output: Risk score (0–100) + clinical recommendation + SHAP explanation

Run:  streamlit run app/app.py
"""

import os
import sys

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
import streamlit as st
import streamlit.components.v1 as components

# ── Paths & imports ────────────────────────────────────────────────
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from preprocess import (  # noqa: E402
    AGE_MAP, EDUCATION_MAP, GENHLTH_MAP, INCOME_MAP,
    BRFSS_FEATURE_COLUMNS, ENGINEERED_COLUMNS, engineer_features,
)

MODEL_DIR  = os.path.join(os.path.dirname(__file__), "..", "models")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="RiskLens — Diabetes Risk Screening",
    page_icon="🔬",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ===================================================================
#  CUSTOM CSS
# ===================================================================
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #080f1e; }
#MainMenu, footer, header { visibility: hidden; }

/* Doctor palette sections (navy/teal) */
.st-key-hero-section,
.st-key-why-section,
.st-key-results-section {
    background: linear-gradient(135deg, #0F2B46 0%, #162d4a 50%, #1E3A5F 100%);
    padding: 2.5rem 2rem; border-radius: 18px; margin-bottom: 1rem;
    border: 1px solid rgba(13,148,136,0.15);
}

/* Patient palette sections (cream/sage) */
.st-key-about-section,
.st-key-form-section {
    background: linear-gradient(135deg, #FFF8F0 0%, #FFF5EB 100%);
    padding: 2.5rem 2rem; border-radius: 18px; margin-bottom: 1rem;
    border: 1px solid rgba(167,196,160,0.3);
}

/* Quote dividers */
.st-key-quote-1, .st-key-quote-2, .st-key-quote-3 {
    background: linear-gradient(90deg, #0D9488 0%, #A7C4A0 50%, #0D9488 100%);
    padding: 1.4rem 2rem; border-radius: 14px; margin-bottom: 1rem; text-align: center;
}

/* Disclaimer banner */
.st-key-disclaimer-banner {
    background: linear-gradient(90deg, #1E3A5F, #0F2B46);
    border-left: 4px solid #E8927C;
    padding: 1rem 1.5rem; border-radius: 10px; margin-bottom: 1rem;
}

/* Footer */
.st-key-footer-section {
    background-color: #0a1628; padding: 1.5rem 2rem;
    border-radius: 14px; border-top: 1px solid #1E3A5F;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F2B46 0%, #080f1e 100%);
}
section[data-testid="stSidebar"] [data-testid="stMarkdown"] p,
section[data-testid="stSidebar"] [data-testid="stMarkdown"] li,
section[data-testid="stSidebar"] [data-testid="stMarkdown"] span {
    color: #c8d6e5 !important;
}

/* Form styling */
.st-key-form-section label,
.st-key-form-section [data-testid="stWidgetLabel"] p {
    color: #5B4636 !important; font-weight: 500 !important;
}

/* Predict button */
.st-key-form-section button[kind="primaryFormSubmit"],
.st-key-form-section .stFormSubmitButton > button {
    background: linear-gradient(135deg, #0D9488, #0a7a71) !important;
    color: #FFFFFF !important; border: none !important;
    border-radius: 10px !important; padding: 0.65rem 2.5rem !important;
    font-size: 1.05rem !important; font-weight: 600 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    letter-spacing: 0.5px; transition: transform 0.15s, box-shadow 0.15s;
}
.st-key-form-section .stFormSubmitButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(13,148,136,0.35) !important;
}

/* Animations */
@keyframes fadeInUp {
    from { opacity:0; transform:translateY(24px); }
    to   { opacity:1; transform:translateY(0); }
}
.st-key-hero-section  { animation: fadeInUp .7s ease-out; }
.st-key-about-section { animation: fadeInUp .7s ease-out .15s both; }
.st-key-why-section   { animation: fadeInUp .7s ease-out .25s both; }
.st-key-form-section  { animation: fadeInUp .7s ease-out .35s both; }
</style>
"""

# ===================================================================
#  GLUCOSE MOLECULE — canvas animation
# ===================================================================
GLUCOSE_HTML = """
<canvas id="mol" style="display:block;margin:0 auto;
       filter:drop-shadow(0 0 12px rgba(13,148,136,0.35));"></canvas>
<script>
(function(){
var c=document.getElementById('mol'),
    x=c.getContext('2d'),W=280,H=300;
c.width=W;c.height=H;
var atoms=[
 ['O',0,1.15,.2],['C',1,.58,-.2],['C',1,-.58,.2],
 ['C',0,-1.15,-.2],['C',-1,-.58,.2],['C',-1,.58,-.2],
 ['C',-1.7,1.15,-.5],
 ['O',1.7,.58,-.7],['O',1.7,-.58,.7],['O',0,-1.9,-.7],
 ['O',-1.7,-.58,.7],['O',-2.4,1.7,-.5]
];
var bonds=[
 [0,1],[1,2],[2,3],[3,4],[4,5],[5,0],
 [5,6],[1,7],[2,8],[3,9],[4,10],[6,11]
];
var col={C:'#0D9488',O:'#E8927C'},
    hi ={C:'#5eead4',O:'#f4a997'},
    dk ={C:'#0a7a71',O:'#c0604a'},
    sz ={C:15,O:13};
var ay=0,ax=0;
function rot(px,py,pz){
 var x1=px*Math.cos(ay)-pz*Math.sin(ay),
     z1=px*Math.sin(ay)+pz*Math.cos(ay),
     y1=py*Math.cos(ax)-z1*Math.sin(ax),
     z2=py*Math.sin(ax)+z1*Math.cos(ax);
 return[x1,y1,z2];
}
function prj(px,py,pz){
 var s=55,d=5,f=d/(d+pz);
 return[W/2+px*s*f,H/2-py*s*f,f];
}
function draw(){
 x.clearRect(0,0,W,H);
 var ra=atoms.map(function(a){var r=rot(a[1],a[2],a[3]);
   return{t:a[0],rx:r[0],ry:r[1],rz:r[2]};});
 bonds.forEach(function(b){
   var p1=prj(ra[b[0]].rx,ra[b[0]].ry,ra[b[0]].rz),
       p2=prj(ra[b[1]].rx,ra[b[1]].ry,ra[b[1]].rz);
   x.beginPath();x.moveTo(p1[0],p1[1]);x.lineTo(p2[0],p2[1]);
   x.strokeStyle='rgba(180,200,220,0.45)';x.lineWidth=2.5;x.stroke();
 });
 var idx=ra.map(function(_,i){return i;}).sort(function(a,b){return ra[a].rz-ra[b].rz;});
 idx.forEach(function(i){
   var a=ra[i],p=prj(a.rx,a.ry,a.rz),r=sz[a.t]*p[2];
   var g=x.createRadialGradient(p[0]-r*.3,p[1]-r*.3,r*.05,p[0],p[1],r);
   g.addColorStop(0,hi[a.t]);g.addColorStop(.55,col[a.t]);g.addColorStop(1,dk[a.t]);
   x.beginPath();x.arc(p[0],p[1],r,0,Math.PI*2);x.fillStyle=g;x.fill();
 });
 ay+=.007;ax+=.003;
 requestAnimationFrame(draw);
}
draw();
})();
</script>
"""


# ===================================================================
#  LOAD MODEL ARTIFACTS
# ===================================================================
@st.cache_resource
def load_artifacts():
    model      = joblib.load(os.path.join(MODEL_DIR, "best_model.pkl"))
    scaler     = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))
    model_name = joblib.load(os.path.join(MODEL_DIR, "model_name.pkl"))
    feature_cols = joblib.load(os.path.join(MODEL_DIR, "feature_cols.pkl"))
    thr_path   = os.path.join(MODEL_DIR, "threshold.pkl")
    threshold  = joblib.load(thr_path) if os.path.exists(thr_path) else 0.50
    return model, scaler, model_name, threshold, feature_cols


@st.cache_resource
def get_explainer(_model, model_name):
    if model_name == "Logistic Regression":
        bg = np.zeros((1, 25))  # 21 + 4 engineered
        return shap.LinearExplainer(_model, bg)
    return shap.TreeExplainer(_model)


# ===================================================================
#  RISK SCORE & TIER
# ===================================================================
def calculate_risk_score(probability):
    """Map probability to a 0-100 risk score with clinical actions."""
    score = int(probability * 100)
    if score < 30:
        return score, "Low Risk", "#A7C4A0", "✅", "Lifestyle counseling, annual rescreening"
    elif score < 70:
        return score, "Moderate Risk", "#e6a817", "⚠️", "Schedule HbA1c test within 3 months"
    else:
        return score, "High Risk", "#E8927C", "🔴", "Urgent HbA1c test + clinical evaluation"


# ===================================================================
#  HELPERS
# ===================================================================
def asset_path(name):
    return os.path.join(ASSETS_DIR, name)

def section_heading(text, color="#E2E8F0", sub=None, sub_color="#A7C4A0"):
    html = f"<h2 style='color:{color};font-family:Plus Jakarta Sans,sans-serif;margin-bottom:0.2rem;'>{text}</h2>"
    if sub:
        html += f"<p style='color:{sub_color};font-size:1.05rem;margin-top:0;'>{sub}</p>"
    st.markdown(html, unsafe_allow_html=True)

def dark_text(text, size="1rem", color="#c8d6e5"):
    st.markdown(f"<p style='color:{color};font-size:{size};line-height:1.7;'>{text}</p>",
                unsafe_allow_html=True)

def patient_heading(text, sub=None):
    html = f"<h2 style='color:#5B4636;font-family:Plus Jakarta Sans,sans-serif;margin-bottom:0.2rem;'>{text}</h2>"
    if sub:
        html += f"<p style='color:#7a6552;font-size:1.05rem;margin-top:0;'>{sub}</p>"
    st.markdown(html, unsafe_allow_html=True)


# ===================================================================
#  MAIN APP
# ===================================================================
def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    try:
        model, scaler, model_name, threshold, feature_cols = load_artifacts()
    except FileNotFoundError:
        st.error("No trained model found. Run `python src/train_model.py` first.")
        return

    # ══════════════════════════════════════════════════════════════
    #  SIDEBAR
    # ══════════════════════════════════════════════════════════════
    with st.sidebar:
        st.markdown(
            "<h1 style='text-align:center;color:#0D9488;"
            "font-family:Plus Jakarta Sans,sans-serif;"
            "font-size:1.8rem;margin-bottom:0;'>🔬 RiskLens</h1>"
            "<p style='text-align:center;color:#A7C4A0;font-size:0.85rem;"
            "margin-top:2px;letter-spacing:1.5px;'>PRE-SCREENING TOOL</p>",
            unsafe_allow_html=True,
        )

        components.html(GLUCOSE_HTML, height=320)

        st.markdown(
            "<p style='text-align:center;color:#5eead4;font-size:0.7rem;"
            "margin-top:-8px;letter-spacing:1px;'>GLUCOSE · C₆H₁₂O₆</p>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown(
            "<p style='color:#8899aa;font-size:0.82rem;line-height:1.6;'>"
            "<b style='color:#c8d6e5;'>Navigate</b><br>"
            "↓ About RiskLens<br>"
            "↓ Why No Blood Test?<br>"
            "↓ Health Questionnaire<br>"
            "↓ Risk Score & SHAP</p>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown(
            f"<p style='color:#556677;font-size:0.72rem;text-align:center;'>"
            f"Model: {model_name}<br>"
            f"Dataset: CDC BRFSS (253,680 records)<br>"
            f"Features: {len(feature_cols)} | Threshold: {int(threshold*100)}%"
            f"</p>",
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════
    #  HERO SECTION
    # ══════════════════════════════════════════════════════════════
    with st.container(key="hero-section"):
        hero_col1, hero_col2 = st.columns([3, 2])

        with hero_col1:
            st.markdown(
                "<h1 style='color:#E2E8F0;font-family:Plus Jakarta Sans,sans-serif;"
                "font-size:2.6rem;line-height:1.15;margin-bottom:0.3rem;'>"
                "🔬 RiskLens</h1>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<p style='color:#5eead4;font-size:1.3rem;font-weight:500;"
                "font-family:Plus Jakarta Sans,sans-serif;margin-top:0;'>"
                "See inside the prediction</p>",
                unsafe_allow_html=True,
            )
            dark_text(
                "An AI-powered <b>diabetes pre-screening tool</b> that estimates "
                "risk from a <b>5-minute questionnaire</b> — no blood draw needed. "
                "Trained on <b>253,680 CDC survey records</b>, it compares 4 "
                "machine-learning models and explains <em>exactly why</em> using SHAP.",
                size="1.05rem",
            )
            st.markdown(
                "<p style='color:#8899aa;font-size:0.85rem;margin-top:1rem;"
                "border-top:1px solid #1E3A5F;padding-top:0.8rem;'>"
                "⚠️ <b>Screening tool</b> — not a medical diagnosis. "
                "This tool helps determine who should get laboratory testing, "
                "not who has diabetes.</p>",
                unsafe_allow_html=True,
            )

        with hero_col2:
            hero_img = asset_path("hero_diabetes.png")
            if os.path.exists(hero_img):
                st.image(hero_img, use_container_width=True)

    # ── Disclaimer Banner ─────────────────────────────────────────
    with st.container(key="disclaimer-banner"):
        st.markdown(
            "<p style='color:#E2E8F0;font-size:0.95rem;margin:0;'>"
            "⚕️ <b>Pre-screening tool for Type 2 Diabetes risk.</b> "
            "Based on 21 questionnaire items from the CDC BRFSS survey. "
            "No blood test values are used — this predicts who should "
            "<em>get</em> tested, not who <em>has</em> diabetes.</p>",
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════
    #  ABOUT SECTION (Patient palette)
    # ══════════════════════════════════════════════════════════════
    with st.container(key="about-section"):
        patient_heading("What is RiskLens?",
                        "A questionnaire-based diabetes screening triage tool")

        st.markdown(
            """
            <div style='color:#5B4636;font-size:1rem;line-height:1.75;'>
            <p>RiskLens analyses <b>21 health and lifestyle questions</b> — blood
            pressure, cholesterol, BMI, physical activity, diet, smoking, age,
            and more — to estimate a patient's probability of having or
            developing Type 2 Diabetes.</p>
            <p>Under the hood, it compares <b>four machine-learning models</b>
            (Logistic Regression, Random Forest, XGBoost, and LightGBM)
            trained on <b>253,680 CDC BRFSS survey records</b>. The best
            performer is auto-selected for predictions.</p>
            <p>Every prediction generates a <b>risk score from 0 to 100</b>
            with a specific clinical recommendation, plus a <b>SHAP waterfall
            plot</b> showing exactly which factors drove the risk up or down.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Risk triage table
        st.markdown(
            """
            <table style='width:100%;border-collapse:collapse;margin-top:1rem;
                          border:1px solid #e0d5c5;border-radius:8px;overflow:hidden;'>
            <tr style='background:#f5ece0;'>
                <th style='color:#5B4636;text-align:left;padding:10px;font-size:0.9rem;'>Score</th>
                <th style='color:#5B4636;text-align:left;padding:10px;font-size:0.9rem;'>Risk Level</th>
                <th style='color:#5B4636;text-align:left;padding:10px;font-size:0.9rem;'>Recommended Action</th>
            </tr>
            <tr style='border-bottom:1px solid #e8ddd0;'>
                <td style='color:#A7C4A0;padding:10px;font-weight:600;'>0 – 29</td>
                <td style='color:#5B4636;padding:10px;'>✅ Low Risk</td>
                <td style='color:#7a6552;padding:10px;'>Lifestyle counseling, annual rescreening</td>
            </tr>
            <tr style='border-bottom:1px solid #e8ddd0;'>
                <td style='color:#e6a817;padding:10px;font-weight:600;'>30 – 69</td>
                <td style='color:#5B4636;padding:10px;'>⚠️ Moderate Risk</td>
                <td style='color:#7a6552;padding:10px;'>Schedule HbA1c test within 3 months</td>
            </tr>
            <tr>
                <td style='color:#E8927C;padding:10px;font-weight:600;'>70 – 100</td>
                <td style='color:#5B4636;padding:10px;'>🔴 High Risk</td>
                <td style='color:#7a6552;padding:10px;'>Urgent HbA1c test + clinical evaluation</td>
            </tr>
            </table>
            """,
            unsafe_allow_html=True,
        )

    # ── Quote 1 ───────────────────────────────────────────────────
    with st.container(key="quote-1"):
        st.markdown(
            "<p style='color:#FFFFFF;font-size:1.15rem;font-style:italic;"
            "margin:0;font-family:Georgia,serif;'>"
            "\"34.1 million US adults have diabetes. 88 million have prediabetes "
            "— most do not know it.\"</p>"
            "<p style='color:#e0f2f1;font-size:0.85rem;margin-top:4px;'>— CDC, 2020</p>",
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════
    #  WHY NO BLOOD TEST SECTION (Doctor palette)
    # ══════════════════════════════════════════════════════════════
    with st.container(key="why-section"):
        why_col1, why_col2 = st.columns([3, 2])

        with why_col1:
            section_heading("Why No Blood Test?",
                            sub="The case for questionnaire-based screening")

            dark_text(
                "<b>Traditional diabetes diagnosis</b> requires lab tests like HbA1c "
                "or fasting glucose — but these are <b>expensive, require a clinic "
                "visit, and most at-risk people never get tested</b>. That's why "
                "88 million Americans with prediabetes don't know they have it."
            )
            dark_text(
                "🏥 <b>This tool uses a different approach:</b> 21 questions you "
                "can answer in 5 minutes, based on the CDC's Behavioral Risk Factor "
                "Surveillance System (BRFSS). The model identifies who should "
                "<em>go get</em> an HbA1c test — acting as a triage filter that "
                "reduces unnecessary lab costs while catching high-risk patients."
            )
            dark_text(
                "💡 <b>Think of it as Stage 1</b> of a two-stage system: "
                "questionnaire first (free, fast, scalable), then lab confirmation "
                "only for those flagged as moderate or high risk.",
                color="#A7C4A0",
            )

        with why_col2:
            hba1c_img = asset_path("hba1c_education.png")
            if os.path.exists(hba1c_img):
                st.image(hba1c_img, use_container_width=True)

    # ── Quote 2 ───────────────────────────────────────────────────
    with st.container(key="quote-2"):
        st.markdown(
            "<p style='color:#FFFFFF;font-size:1.15rem;font-style:italic;"
            "margin:0;font-family:Georgia,serif;'>"
            "\"An ounce of prevention is worth a pound of cure.\"</p>"
            "<p style='color:#e0f2f1;font-size:0.85rem;margin-top:4px;'>"
            "— Benjamin Franklin</p>",
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════
    #  INPUT FORM (Patient palette)
    # ══════════════════════════════════════════════════════════════
    with st.container(key="form-section"):
        form_top1, form_top2 = st.columns([3, 2])
        with form_top1:
            patient_heading("Health Questionnaire",
                            "Answer 21 questions to generate your risk score (5 min)")
        with form_top2:
            well_img = asset_path("wellness_lifestyle.png")
            if os.path.exists(well_img):
                st.image(well_img, use_container_width=True)

        with st.form("patient_form"):
            # ── Section: Cardiovascular ───────────────────────────
            st.markdown("<h4 style='color:#5B4636;margin-top:0.5rem;'>❤️ Cardiovascular</h4>",
                        unsafe_allow_html=True)
            cv1, cv2, cv3, cv4 = st.columns(4)
            with cv1:
                high_bp = st.selectbox("High blood pressure?", ["No", "Yes"],
                                       help="Have you been told by a doctor that you have high blood pressure?")
            with cv2:
                high_chol = st.selectbox("High cholesterol?", ["No", "Yes"],
                                         help="Have you been told by a doctor that you have high cholesterol?")
            with cv3:
                chol_check = st.selectbox("Cholesterol check (5yr)?", ["No", "Yes"],
                                          help="Have you had a cholesterol check within the past 5 years?")
            with cv4:
                heart_disease = st.selectbox("Heart disease / MI?", ["No", "Yes"],
                                             help="Ever been told you have coronary heart disease or a heart attack?")

            cv5, cv6, _ , _ = st.columns(4)
            with cv5:
                stroke = st.selectbox("Ever had a stroke?", ["No", "Yes"])
            with cv6:
                diff_walk = st.selectbox("Difficulty walking?", ["No", "Yes"],
                                         help="Serious difficulty walking or climbing stairs?")

            # ── Section: Body & Health ────────────────────────────
            st.markdown("<h4 style='color:#5B4636;margin-top:1rem;'>🏥 Body & Health</h4>",
                        unsafe_allow_html=True)
            bh1, bh2, bh3, bh4 = st.columns(4)
            with bh1:
                bmi = st.number_input("BMI", min_value=10, max_value=98, value=25,
                                      help="Body Mass Index (integer)")
            with bh2:
                gen_hlth_label = st.selectbox("General health?", list(GENHLTH_MAP.keys()),
                                             help="How would you rate your general health?")
            with bh3:
                phys_hlth = st.number_input("Physical health (days)", min_value=0,
                                           max_value=30, value=0,
                                           help="Days of poor physical health in past 30 days")
            with bh4:
                ment_hlth = st.number_input("Mental health (days)", min_value=0,
                                           max_value=30, value=0,
                                           help="Days of poor mental health in past 30 days")

            # ── Section: Lifestyle ────────────────────────────────
            st.markdown("<h4 style='color:#5B4636;margin-top:1rem;'>🏃 Lifestyle</h4>",
                        unsafe_allow_html=True)
            ls1, ls2, ls3, ls4 = st.columns(4)
            with ls1:
                smoker = st.selectbox("Smoker?", ["No", "Yes"],
                                      help="Smoked at least 100 cigarettes in your lifetime?")
            with ls2:
                phys_activity = st.selectbox("Physical activity?", ["No", "Yes"],
                                             help="Physical activity in past 30 days (non-job)?")
            with ls3:
                fruits = st.selectbox("Eat fruit daily?", ["No", "Yes"],
                                      help="Consume fruit 1 or more times per day?")
            with ls4:
                veggies = st.selectbox("Eat vegetables daily?", ["No", "Yes"],
                                       help="Consume vegetables 1 or more times per day?")

            ls5, _, _, _ = st.columns(4)
            with ls5:
                heavy_alcohol = st.selectbox("Heavy alcohol?", ["No", "Yes"],
                                             help="Men: >14 drinks/week, Women: >7 drinks/week?")

            # ── Section: Demographics ─────────────────────────────
            st.markdown("<h4 style='color:#5B4636;margin-top:1rem;'>👤 Demographics</h4>",
                        unsafe_allow_html=True)
            dm1, dm2, dm3, dm4 = st.columns(4)
            with dm1:
                sex = st.selectbox("Sex", ["Female", "Male"])
            with dm2:
                age_label = st.selectbox("Age range", list(AGE_MAP.keys()))
            with dm3:
                education_label = st.selectbox("Education", list(EDUCATION_MAP.keys()))
            with dm4:
                income_label = st.selectbox("Income", list(INCOME_MAP.keys()))

            # ── Section: Healthcare Access ────────────────────────
            st.markdown("<h4 style='color:#5B4636;margin-top:1rem;'>🏥 Healthcare Access</h4>",
                        unsafe_allow_html=True)
            ha1, ha2, _, _ = st.columns(4)
            with ha1:
                any_healthcare = st.selectbox("Have insurance?", ["No", "Yes"],
                                              help="Have any kind of healthcare coverage?")
            with ha2:
                no_doc_cost = st.selectbox("Couldn't afford doctor?", ["No", "Yes"],
                                           help="Couldn't see doctor due to cost in past 12 months?")

            submitted = st.form_submit_button("🔬  Calculate Risk Score",
                                              type="primary", use_container_width=True)

    # ══════════════════════════════════════════════════════════════
    #  RESULTS (Doctor palette — conditional)
    # ══════════════════════════════════════════════════════════════
    if submitted:
        # ── Encode inputs ─────────────────────────────────────────
        yn = lambda v: 1 if v == "Yes" else 0  # noqa: E731

        raw_row = {
            "HighBP": yn(high_bp),
            "HighChol": yn(high_chol),
            "CholCheck": yn(chol_check),
            "BMI": bmi,
            "Smoker": yn(smoker),
            "Stroke": yn(stroke),
            "HeartDiseaseorAttack": yn(heart_disease),
            "PhysActivity": yn(phys_activity),
            "Fruits": yn(fruits),
            "Veggies": yn(veggies),
            "HvyAlcoholConsump": yn(heavy_alcohol),
            "AnyHealthcare": yn(any_healthcare),
            "NoDocbcCost": yn(no_doc_cost),
            "GenHlth": GENHLTH_MAP[gen_hlth_label],
            "MentHlth": ment_hlth,
            "PhysHlth": phys_hlth,
            "DiffWalk": yn(diff_walk),
            "Sex": 1 if sex == "Male" else 0,
            "Age": AGE_MAP[age_label],
            "Education": EDUCATION_MAP[education_label],
            "Income": INCOME_MAP[income_label],
        }

        input_df = pd.DataFrame([raw_row])
        input_df = engineer_features(input_df)

        # Ensure column order matches training
        input_df = input_df[feature_cols]

        # Scale if needed
        if model_name == "Logistic Regression":
            input_processed = scaler.transform(input_df)
        else:
            input_processed = input_df

        prob = model.predict_proba(input_processed)[0][1]
        score, tier, tier_color, tier_icon, action = calculate_risk_score(prob)

        # ── Save to session history ───────────────────────────────
        import shap as _shap
        try:
            explainer_for_save = get_explainer(model, model_name)
            if model_name == "Logistic Regression":
                shap_input_save = pd.DataFrame(scaler.transform(input_df), columns=feature_cols)
            else:
                shap_input_save = input_df
            sv = explainer_for_save(shap_input_save)
            shap_vals_dict = dict(zip(feature_cols, sv.values[0].tolist()))
            # Build top drivers and protective factors
            sorted_shap = sorted(shap_vals_dict.items(), key=lambda x: x[1], reverse=True)
            top_drivers_list = [
                {"feature": k, "featureLabel": k, "value": float(raw_row.get(k, 0)), "shapValue": v, "direction": "risk"}
                for k, v in sorted_shap[:5] if v > 0
            ]
            protective_list = [
                {"feature": k, "featureLabel": k, "value": float(raw_row.get(k, 0)), "shapValue": v, "direction": "protective"}
                for k, v in reversed(sorted_shap[-5:]) if v < 0
            ]
        except Exception:
            shap_vals_dict = {}
            top_drivers_list = []
            protective_list = []

        history_entry = {
            "riskScore": score,
            "riskLevel": tier,
            "clinicalAction": action,
            "inputs": raw_row,
            "shapValues": shap_vals_dict,
            "topDrivers": top_drivers_list,
            "protectiveFactors": protective_list,
        }
        existing = st.session_state.get("risklens_history", [])
        new_id = f"assess-{len(existing)+1:03d}"
        history_entry["id"] = new_id
        from datetime import datetime as _dt
        history_entry["timestamp"] = _dt.now().isoformat()
        st.session_state["risklens_history"] = [history_entry] + existing

        # ── Quote 3 ──────────────────────────────────────────────
        with st.container(key="quote-3"):
            st.markdown(
                "<p style='color:#FFFFFF;font-size:1.15rem;font-style:italic;"
                "margin:0;font-family:Georgia,serif;'>"
                "\"Take care of your body. It's the only place you have to live.\"</p>"
                "<p style='color:#e0f2f1;font-size:0.85rem;margin-top:4px;'>"
                "— Jim Rohn</p>",
                unsafe_allow_html=True,
            )

        with st.container(key="results-section"):
            section_heading("Your Risk Score",
                            sub="Based on your 21-question health assessment")

            # ── Score + Tier ──────────────────────────────────────
            r1, r2 = st.columns(2)
            with r1:
                st.markdown(
                    f"<div style='text-align:center;padding:1.5rem;background:rgba(0,0,0,0.2);"
                    f"border-radius:14px;'>"
                    f"<p style='color:#8899aa;font-size:0.85rem;margin-bottom:4px;"
                    f"text-transform:uppercase;letter-spacing:1px;'>Risk Score</p>"
                    f"<p style='color:{tier_color};font-size:3.5rem;font-weight:800;"
                    f"font-family:Plus Jakarta Sans,sans-serif;margin:0;'>"
                    f"{score}<span style='font-size:1.5rem;color:#667788;'>/100</span></p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            with r2:
                st.markdown(
                    f"<div style='text-align:center;padding:1.5rem;background:rgba(0,0,0,0.2);"
                    f"border-radius:14px;'>"
                    f"<p style='color:#8899aa;font-size:0.85rem;margin-bottom:4px;"
                    f"text-transform:uppercase;letter-spacing:1px;'>Risk Level</p>"
                    f"<p style='color:{tier_color};font-size:2.2rem;font-weight:700;"
                    f"font-family:Plus Jakarta Sans,sans-serif;margin:0;'>"
                    f"{tier_icon} {tier}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            # ── Clinical Recommendation ───────────────────────────
            st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

            if tier == "High Risk":
                st.markdown(
                    f"<div style='background:rgba(232,146,124,0.12);border-left:4px solid #E8927C;"
                    f"padding:1rem 1.2rem;border-radius:8px;'>"
                    f"<p style='color:#f4a997;font-size:0.95rem;margin:0;'>"
                    f"🔴 <b>Recommended:</b> {action}. This patient's risk factors "
                    f"strongly suggest further clinical evaluation.</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            elif tier == "Moderate Risk":
                st.markdown(
                    f"<div style='background:rgba(230,168,23,0.1);border-left:4px solid #e6a817;"
                    f"padding:1rem 1.2rem;border-radius:8px;'>"
                    f"<p style='color:#f0d060;font-size:0.95rem;margin:0;'>"
                    f"⚠️ <b>Recommended:</b> {action}. Lifestyle modifications "
                    f"(diet, exercise, weight management) may also help reduce risk.</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div style='background:rgba(167,196,160,0.12);border-left:4px solid #A7C4A0;"
                    f"padding:1rem 1.2rem;border-radius:8px;'>"
                    f"<p style='color:#bfe0b8;font-size:0.95rem;margin:0;'>"
                    f"✅ <b>Recommended:</b> {action}. Keep up healthy habits.</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

            st.markdown(
                "<p style='color:#556677;font-size:0.8rem;margin-top:1rem;text-align:center;'>"
                "⚠️ This is a pre-screening estimate, not a clinical diagnosis. "
                "No model is ever 100% accurate.</p>",
                unsafe_allow_html=True,
            )

            # ── Go to Dashboard button ────────────────────────────
            st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
            st.markdown(
                f"<div style='background:rgba(13,148,136,0.1);border:1px solid rgba(13,148,136,0.3);"
                f"border-radius:10px;padding:1rem 1.2rem;margin-bottom:1rem;'>"
                f"<p style='color:#5eead4;font-size:0.92rem;margin:0;'>"
                f"✅ Assessment <b>{new_id}</b> saved to your dashboard.</p>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if st.button("🩺 View My Dashboard & History →", type="primary", use_container_width=True):
                st.switch_page("pages/1_🩺_My_Dashboard.py")

            # ── SHAP waterfall ────────────────────────────────────
            st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
            section_heading("Why did the model assign this score?",
                            sub="SHAP waterfall — each bar shows how a factor pushed "
                                "the risk higher (red) or lower (blue)")

            try:
                explainer = get_explainer(model, model_name)

                if model_name == "Logistic Regression":
                    shap_input = pd.DataFrame(
                        scaler.transform(input_df), columns=feature_cols
                    )
                else:
                    shap_input = input_df

                shap_values = explainer(shap_input)

                fig, ax = plt.subplots(figsize=(10, 7))
                fig.patch.set_facecolor("white")
                shap.plots.waterfall(shap_values[0], show=False, max_display=15)
                plt.tight_layout()
                st.pyplot(fig)
                plt.close(fig)

            except Exception as e:
                st.markdown(
                    f"<p style='color:#E8927C;font-size:0.9rem;'>"
                    f"⚠️ Could not generate SHAP explanation: {e}</p>",
                    unsafe_allow_html=True,
                )


    # ══════════════════════════════════════════════════════════════
    #  FOOTER
    # ══════════════════════════════════════════════════════════════
    with st.container(key="footer-section"):
        st.markdown(
            """
            <div style='text-align:center;'>
            <p style='color:#556677;font-size:0.82rem;line-height:1.7;'>
            <b style='color:#8899aa;'>RiskLens</b> is an educational project
            demonstrating the ML lifecycle: data cleaning, model comparison,
            threshold tuning, and SHAP explainability.<br>
            This is a <b>pre-screening</b> tool — it predicts who should
            get laboratory testing, not who has diabetes.<br>
            No model is ever 100% accurate. Predictions should not replace
            professional medical advice.<br><br>
            <span style='color:#3d4f60;'>
            Built with Python · XGBoost · LightGBM · SHAP · Streamlit<br>
            Dataset: CDC BRFSS Diabetes Health Indicators (253,680 records)
            </span>
            </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()

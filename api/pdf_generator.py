"""
pdf_generator.py — Professional 3-page clinical PDF report for RiskLens.

Uses ReportLab to produce a polished A4 document with:
  Page 1: Cover page — branding, patient info, large risk gauge, recommendation.
  Page 2: Detailed analysis — risk-factor table, SHAP waterfall, clinical text.
  Page 3: Personalised recommendations, lifestyle tips, QR code to CDC.

Every page carries a consistent footer with a disclaimer and report ID.
"""

from __future__ import annotations

import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

import qrcode
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from api.shap_utils import generate_gauge_png, generate_waterfall_png

logger = logging.getLogger("risklens.pdf")

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
TEAL = colors.HexColor("#0d9488")
TEAL_LIGHT = colors.HexColor("#ccfbf1")
DARK = colors.HexColor("#1f2937")
GREY = colors.HexColor("#6b7280")
GREY_LIGHT = colors.HexColor("#f3f4f6")
WHITE = colors.white
GREEN = colors.HexColor("#22c55e")
AMBER = colors.HexColor("#f59e0b")
RED = colors.HexColor("#ef4444")

PAGE_W, PAGE_H = A4
LEFT_MARGIN = 2.0 * cm
RIGHT_MARGIN = 2.0 * cm
TOP_MARGIN = 2.5 * cm
BOTTOM_MARGIN = 2.5 * cm

# ---------------------------------------------------------------------------
# Population averages (BRFSS dataset)
# ---------------------------------------------------------------------------
POPULATION_AVERAGES: dict[str, float] = {
    "HighBP": 0.44,
    "HighChol": 0.42,
    "CholCheck": 0.96,
    "BMI": 28.4,
    "Smoker": 0.44,
    "Stroke": 0.04,
    "HeartDiseaseorAttack": 0.09,
    "PhysActivity": 0.72,
    "Fruits": 0.63,
    "Veggies": 0.79,
    "HvyAlcoholConsump": 0.06,
    "AnyHealthcare": 0.95,
    "NoDocbcCost": 0.08,
    "GenHlth": 2.5,
    "MentHlth": 3.2,
    "PhysHlth": 4.3,
    "DiffWalk": 0.17,
    "Sex": 0.44,
    "Age": 8.0,
    "Education": 5.0,
    "Income": 6.2,
}

# Human-friendly display names for the 21 input features
FEATURE_DISPLAY: dict[str, str] = {
    "HighBP": "High Blood Pressure",
    "HighChol": "High Cholesterol",
    "CholCheck": "Cholesterol Check (5yr)",
    "BMI": "Body Mass Index",
    "Smoker": "Smoker (≥100 cigs)",
    "Stroke": "History of Stroke",
    "HeartDiseaseorAttack": "Heart Disease / MI",
    "PhysActivity": "Physical Activity (30d)",
    "Fruits": "Daily Fruit Intake",
    "Veggies": "Daily Vegetable Intake",
    "HvyAlcoholConsump": "Heavy Alcohol Use",
    "AnyHealthcare": "Healthcare Coverage",
    "NoDocbcCost": "Cost-Barrier to Doctor",
    "GenHlth": "General Health (1-5)",
    "MentHlth": "Poor Mental Health Days",
    "PhysHlth": "Poor Physical Health Days",
    "DiffWalk": "Difficulty Walking",
    "Sex": "Sex (0=F, 1=M)",
    "Age": "Age Category (1-13)",
    "Education": "Education Level (1-6)",
    "Income": "Income Level (1-8)",
}

# For binary 0/1 features, define which value is "concerning"
_BINARY_CONCERN: dict[str, int] = {
    "HighBP": 1, "HighChol": 1, "Smoker": 1, "Stroke": 1,
    "HeartDiseaseorAttack": 1, "HvyAlcoholConsump": 1,
    "NoDocbcCost": 1, "DiffWalk": 1,
    # Protective features where 0 is concerning
    "CholCheck": 0, "PhysActivity": 0, "Fruits": 0, "Veggies": 0,
    "AnyHealthcare": 0,
}


def _risk_colour(level: str) -> colors.Color:
    return {"Low": GREEN, "Moderate": AMBER, "High": RED}.get(level, GREY)


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "CoverTitle", parent=base["Title"],
            fontSize=28, leading=34, textColor=DARK,
            fontName="Helvetica-Bold", alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "CoverSubtitle", parent=base["Normal"],
            fontSize=13, leading=18, textColor=GREY,
            fontName="Helvetica", alignment=TA_LEFT,
        ),
        "heading": ParagraphStyle(
            "SectionHeading", parent=base["Heading2"],
            fontSize=14, leading=18, textColor=TEAL,
            fontName="Helvetica-Bold", spaceBefore=12, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "BodyText", parent=base["Normal"],
            fontSize=10, leading=14, textColor=DARK,
            fontName="Helvetica", alignment=TA_JUSTIFY,
        ),
        "body_bold": ParagraphStyle(
            "BodyBold", parent=base["Normal"],
            fontSize=10, leading=14, textColor=DARK,
            fontName="Helvetica-Bold",
        ),
        "small": ParagraphStyle(
            "SmallText", parent=base["Normal"],
            fontSize=8, leading=10, textColor=GREY,
            fontName="Helvetica",
        ),
        "footer": ParagraphStyle(
            "FooterText", parent=base["Normal"],
            fontSize=7, leading=9, textColor=GREY,
            fontName="Helvetica", alignment=TA_CENTER,
        ),
        "score_large": ParagraphStyle(
            "ScoreLarge", parent=base["Title"],
            fontSize=56, leading=60, fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        ),
        "table_header": ParagraphStyle(
            "TableHeader", parent=base["Normal"],
            fontSize=9, leading=12, textColor=WHITE,
            fontName="Helvetica-Bold",
        ),
        "table_cell": ParagraphStyle(
            "TableCell", parent=base["Normal"],
            fontSize=9, leading=12, textColor=DARK,
            fontName="Helvetica",
        ),
        "bullet": ParagraphStyle(
            "BulletText", parent=base["Normal"],
            fontSize=10, leading=14, textColor=DARK,
            fontName="Helvetica", leftIndent=18,
            bulletIndent=6, bulletFontName="Helvetica",
        ),
    }


# ---------------------------------------------------------------------------
# Footer — drawn on every page via onPage callback
# ---------------------------------------------------------------------------
def _draw_footer(canvas, doc, report_id: str):
    """Draw the persistent footer on every page."""
    canvas.saveState()
    # Thin teal line
    canvas.setStrokeColor(TEAL)
    canvas.setLineWidth(0.5)
    canvas.line(LEFT_MARGIN, BOTTOM_MARGIN - 8 * mm, PAGE_W - RIGHT_MARGIN, BOTTOM_MARGIN - 8 * mm)
    # Footer text
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(GREY)
    footer_text = (
        f"Generated by RiskLens  |  Not a substitute for professional medical advice  |  "
        f"Report ID: {report_id}"
    )
    canvas.drawCentredString(PAGE_W / 2, BOTTOM_MARGIN - 14 * mm, footer_text)
    # Page number
    canvas.drawRightString(
        PAGE_W - RIGHT_MARGIN, BOTTOM_MARGIN - 14 * mm,
        f"Page {canvas.getPageNumber()}",
    )
    canvas.restoreState()


# ---------------------------------------------------------------------------
# QR Code helper
# ---------------------------------------------------------------------------
def _generate_qr_bytes(url: str, size: int = 160) -> bytes:
    """Return PNG bytes of a QR code linking to *url*."""
    qr = qrcode.QRCode(
        version=1, error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6, border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    img = img.resize((size, size), PILImage.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Status assessment for the risk-factor table
# ---------------------------------------------------------------------------
def _assess_status(feature: str, value: float) -> tuple[str, colors.Color]:
    """Return a (label, colour) pair indicating concern vs normal."""
    pop_avg = POPULATION_AVERAGES.get(feature)
    if pop_avg is None:
        return ("—", GREY)

    # Binary features
    if feature in _BINARY_CONCERN:
        concern_val = _BINARY_CONCERN[feature]
        if int(value) == concern_val:
            return ("⚠ Concern", RED)
        return ("✓ Normal", GREEN)

    # Continuous / ordinal features — compare to population average
    # Higher is worse for: BMI, GenHlth, MentHlth, PhysHlth
    # Lower is worse for: Education, Income
    worse_if_higher = {"BMI", "GenHlth", "MentHlth", "PhysHlth"}
    worse_if_lower = {"Education", "Income"}

    if feature in worse_if_higher:
        if value > pop_avg * 1.15:
            return ("⚠ Concern", RED)
        return ("✓ Normal", GREEN)
    elif feature in worse_if_lower:
        if value < pop_avg * 0.85:
            return ("⚠ Concern", RED)
        return ("✓ Normal", GREEN)

    # Default: Age, Sex — neutral
    return ("—", GREY)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def generate_report(
    patient_name: str,
    patient_email: str,
    risk_score: int,
    risk_level: str,
    clinical_action: str,
    inputs_dict: dict[str, Any],
    shap_values_dict: dict[str, float],
    top_drivers: list[dict],
    protective_factors: list[dict],
) -> bytes:
    """Build a 3-page A4 clinical PDF and return the raw bytes.

    Parameters
    ----------
    patient_name : str
    patient_email : str
    risk_score : int  (0-100)
    risk_level : str  ("Low" | "Moderate" | "High")
    clinical_action : str
    inputs_dict : dict  – the 21 raw BRFSS inputs
    shap_values_dict : dict  – {feature: SHAP value}
    top_drivers : list[dict]  – positive-SHAP drivers
    protective_factors : list[dict]  – negative-SHAP protective factors

    Returns
    -------
    bytes – PDF content
    """
    report_id = str(uuid.uuid4())[:12].upper()
    generated_at = datetime.now(timezone.utc).strftime("%B %d, %Y at %H:%M UTC")
    styles = _build_styles()

    buf = io.BytesIO()

    # ── Document setup ────────────────────────────────────────────────
    def _footer_cb(canvas, doc):
        _draw_footer(canvas, doc, report_id)

    frame = Frame(
        LEFT_MARGIN, BOTTOM_MARGIN,
        PAGE_W - LEFT_MARGIN - RIGHT_MARGIN,
        PAGE_H - TOP_MARGIN - BOTTOM_MARGIN,
        id="main",
    )
    template = PageTemplate(id="default", frames=[frame], onPage=_footer_cb)

    doc = BaseDocTemplate(
        buf,
        pagesize=A4,
        title=f"RiskLens Report — {patient_name}",
        author="RiskLens Diabetes Risk Predictor",
    )
    doc.addPageTemplates([template])

    story: list = []

    # ══════════════════════════════════════════════════════════════════
    #  PAGE 1 — COVER
    # ══════════════════════════════════════════════════════════════════

    # Teal accent bar (simulated with a coloured table row)
    accent_bar = Table(
        [[""]],
        colWidths=[PAGE_W - LEFT_MARGIN - RIGHT_MARGIN],
        rowHeights=[6 * mm],
    )
    accent_bar.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TEAL),
        ("LINEBELOW", (0, 0), (-1, -1), 0, TEAL),
    ]))
    story.append(accent_bar)
    story.append(Spacer(1, 12 * mm))

    # Logo text
    story.append(Paragraph("RiskLens", styles["title"]))
    story.append(Paragraph("Confidential Diabetes Risk Assessment Report", styles["subtitle"]))
    story.append(Spacer(1, 10 * mm))

    # Patient info table
    info_data = [
        [Paragraph("<b>Patient Name:</b>", styles["body"]),
         Paragraph(patient_name, styles["body"])],
        [Paragraph("<b>Email:</b>", styles["body"]),
         Paragraph(patient_email, styles["body"])],
        [Paragraph("<b>Report Date:</b>", styles["body"]),
         Paragraph(generated_at, styles["body"])],
        [Paragraph("<b>Report ID:</b>", styles["body"]),
         Paragraph(report_id, styles["body"])],
    ]
    info_table = Table(info_data, colWidths=[4.5 * cm, 12 * cm])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, GREY_LIGHT),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 12 * mm))

    # ── Gauge chart ───────────────────────────────────────────────────
    gauge_png = generate_gauge_png(risk_score, risk_level)
    gauge_img = Image(io.BytesIO(gauge_png), width=10 * cm, height=6.4 * cm)
    gauge_img.hAlign = "CENTER"
    story.append(gauge_img)
    story.append(Spacer(1, 6 * mm))

    # Risk score text
    score_colour = _risk_colour(risk_level)
    story.append(Paragraph(
        f'<font color="{score_colour.hexval()}" size="36"><b>{risk_score}</b></font>'
        f'<font color="{GREY.hexval()}" size="14"> / 100</font>',
        ParagraphStyle("CenteredScore", alignment=TA_CENTER, fontSize=36, leading=40),
    ))
    story.append(Paragraph(
        f'<font color="{score_colour.hexval()}" size="16"><b>{risk_level} Risk</b></font>',
        ParagraphStyle("CenteredLevel", alignment=TA_CENTER, fontSize=16, leading=20),
    ))
    story.append(Spacer(1, 8 * mm))

    # Clinical recommendation
    rec_table = Table(
        [[Paragraph(f"<b>Clinical Recommendation:</b> {clinical_action}", styles["body"])]],
        colWidths=[PAGE_W - LEFT_MARGIN - RIGHT_MARGIN - 1 * cm],
    )
    rec_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TEAL_LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, TEAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    rec_table.hAlign = "CENTER"
    story.append(rec_table)
    story.append(Spacer(1, 10 * mm))

    # Disclaimer
    story.append(Paragraph(
        "<i>This report is generated by an AI model and is intended for informational "
        "purposes only. It does not constitute medical advice, diagnosis, or treatment. "
        "Always consult a qualified healthcare professional.</i>",
        styles["small"],
    ))

    # ══════════════════════════════════════════════════════════════════
    #  PAGE 2 — DETAILED ANALYSIS
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())

    story.append(Paragraph("Detailed Risk Analysis", styles["title"]))
    story.append(Spacer(1, 4 * mm))

    # ── Risk-Factor Table ─────────────────────────────────────────────
    story.append(Paragraph("Your Risk Factors", styles["heading"]))

    header_row = [
        Paragraph("<b>Factor</b>", styles["table_header"]),
        Paragraph("<b>Your Value</b>", styles["table_header"]),
        Paragraph("<b>Pop. Average</b>", styles["table_header"]),
        Paragraph("<b>Status</b>", styles["table_header"]),
    ]
    table_data = [header_row]

    # Ordered keys for the 21 BRFSS features
    ordered_features = [
        "HighBP", "HighChol", "CholCheck", "BMI", "Smoker",
        "Stroke", "HeartDiseaseorAttack", "PhysActivity",
        "Fruits", "Veggies", "HvyAlcoholConsump",
        "AnyHealthcare", "NoDocbcCost", "GenHlth",
        "MentHlth", "PhysHlth", "DiffWalk", "Sex",
        "Age", "Education", "Income",
    ]

    for feat in ordered_features:
        val = inputs_dict.get(feat, "—")
        pop = POPULATION_AVERAGES.get(feat, "—")
        display_name = FEATURE_DISPLAY.get(feat, feat)

        status_text, status_colour = _assess_status(feat, float(val) if val != "—" else 0)

        # Format values for display
        val_str = f"{val:.1f}" if isinstance(val, float) and val != int(val) else str(val)
        pop_str = f"{pop:.2f}" if isinstance(pop, float) else str(pop)

        table_data.append([
            Paragraph(display_name, styles["table_cell"]),
            Paragraph(str(val_str), styles["table_cell"]),
            Paragraph(pop_str, styles["table_cell"]),
            Paragraph(
                f'<font color="{status_colour.hexval()}">{status_text}</font>',
                styles["table_cell"],
            ),
        ])

    col_widths = [6.5 * cm, 3.0 * cm, 3.5 * cm, 3.5 * cm]
    risk_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    risk_table.setStyle(TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), TEAL),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        # Alternating row colours
        *[("BACKGROUND", (0, i), (-1, i), GREY_LIGHT) for i in range(2, len(table_data), 2)],
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(risk_table)
    story.append(Spacer(1, 8 * mm))

    # ── SHAP Waterfall Chart ──────────────────────────────────────────
    story.append(Paragraph("What Drives Your Risk", styles["heading"]))

    waterfall_png = generate_waterfall_png(shap_values_dict, max_display=10)
    waterfall_img = Image(
        io.BytesIO(waterfall_png),
        width=15 * cm,
        height=8 * cm,
    )
    waterfall_img.hAlign = "CENTER"
    story.append(waterfall_img)
    story.append(Spacer(1, 6 * mm))

    # Top positive drivers
    if top_drivers:
        story.append(Paragraph("<b>Top Risk-Increasing Factors:</b>", styles["body_bold"]))
        for d in top_drivers[:3]:
            feat_label = d.get("featureLabel", d.get("feature", "Unknown"))
            feat_val = d.get("value", "—")
            shap_val = d.get("shapValue", 0)
            points = int(round(abs(shap_val) * 100))
            story.append(Paragraph(
                f'<bullet>&bull;</bullet> <b>{feat_label}</b> ({feat_val}) → '
                f'<font color="{RED.hexval()}">+{points} points</font>',
                styles["bullet"],
            ))
        story.append(Spacer(1, 4 * mm))

    # Protective factors
    if protective_factors:
        story.append(Paragraph("<b>Top Protective Factors:</b>", styles["body_bold"]))
        for d in protective_factors[:3]:
            feat_label = d.get("featureLabel", d.get("feature", "Unknown"))
            feat_val = d.get("value", "—")
            shap_val = d.get("shapValue", 0)
            points = int(round(abs(shap_val) * 100))
            story.append(Paragraph(
                f'<bullet>&bull;</bullet> <b>{feat_label}</b> ({feat_val}) → '
                f'<font color="{GREEN.hexval()}">-{points} points</font>',
                styles["bullet"],
            ))
        story.append(Spacer(1, 6 * mm))

    # ── Clinical Interpretation ───────────────────────────────────────
    story.append(Paragraph("Clinical Interpretation", styles["heading"]))

    interpretations = {
        "Low": (
            "Your overall diabetes risk score falls within the <b>low-risk</b> category. "
            "Based on the 21 health indicators assessed, your current profile does not "
            "suggest elevated metabolic risk. Key protective factors — such as regular "
            "physical activity, healthy BMI, and absence of cardiovascular comorbidities — "
            "contribute positively to this assessment."
            "<br/><br/>"
            "While this is encouraging, low risk does not mean zero risk. We recommend "
            "maintaining your current healthy behaviours and scheduling routine annual "
            "screenings with your primary-care provider to monitor blood glucose levels."
        ),
        "Moderate": (
            "Your diabetes risk score falls within the <b>moderate-risk</b> range. "
            "Several of your health indicators — particularly those highlighted as risk "
            "drivers in the chart above — suggest that lifestyle modifications and/or "
            "clinical follow-up may be beneficial."
            "<br/><br/>"
            "We recommend scheduling an <b>HbA1c test</b> or <b>fasting glucose test</b> "
            "with your healthcare provider in the coming weeks. Early intervention at this "
            "stage — including dietary adjustments, increased physical activity, and weight "
            "management — can significantly reduce your long-term risk of developing "
            "Type 2 diabetes."
        ),
        "High": (
            "Your diabetes risk score is in the <b>high-risk</b> category. Multiple "
            "health indicators — including cardiovascular factors, BMI, and lifestyle "
            "markers — are contributing to elevated risk."
            "<br/><br/>"
            "We strongly recommend <b>urgent clinical evaluation</b>. This should include "
            "a comprehensive metabolic panel, HbA1c testing, and discussion with your "
            "doctor about potential referral to an endocrinologist. Early diagnosis and "
            "treatment can prevent or delay the progression of diabetes and its "
            "complications."
            "<br/><br/>"
            "Please do not delay — schedule an appointment with your healthcare provider "
            "as soon as possible."
        ),
    }
    story.append(Paragraph(
        interpretations.get(risk_level, interpretations["Moderate"]),
        styles["body"],
    ))

    # ══════════════════════════════════════════════════════════════════
    #  PAGE 3 — RECOMMENDATIONS
    # ══════════════════════════════════════════════════════════════════
    story.append(PageBreak())

    story.append(Paragraph("Personalised Recommendations", styles["title"]))
    story.append(Spacer(1, 4 * mm))

    # ── Action Plan ───────────────────────────────────────────────────
    story.append(Paragraph("Action Plan", styles["heading"]))

    action_plans = {
        "High": [
            "<b>1. Urgent Medical Evaluation</b> — Schedule a comprehensive metabolic "
            "panel and HbA1c test within the next 1-2 weeks.",
            "<b>2. Specialist Referral</b> — Ask your doctor about referral to an "
            "endocrinologist for detailed diabetes risk assessment.",
            "<b>3. Blood Pressure &amp; Cholesterol Management</b> — If you have elevated "
            "BP or cholesterol, ensure they are being actively managed with medication "
            "and/or lifestyle changes.",
            "<b>4. Weight Management Program</b> — If your BMI is above 25, consider "
            "enrolling in a structured weight-loss programme under medical supervision.",
            "<b>5. Continuous Glucose Monitoring</b> — Discuss with your doctor whether "
            "a CGM device could help track your glucose trends.",
        ],
        "Moderate": [
            "<b>1. Schedule HbA1c Testing</b> — Request a fasting glucose or HbA1c test "
            "at your next medical appointment.",
            "<b>2. Lifestyle Modifications</b> — Focus on increasing physical activity "
            "to at least 150 minutes/week of moderate aerobic exercise.",
            "<b>3. Dietary Improvements</b> — Reduce refined carbohydrates and increase "
            "fibre intake; consider consulting a registered dietitian.",
            "<b>4. Monitor Key Indicators</b> — Track your blood pressure, weight, and "
            "waist circumference monthly.",
            "<b>5. Follow-Up Screening</b> — Repeat this risk assessment in 6 months to "
            "track your progress.",
        ],
        "Low": [
            "<b>1. Annual Screening</b> — Continue routine annual health check-ups "
            "including fasting glucose.",
            "<b>2. Maintain Healthy Habits</b> — Your current lifestyle appears to be "
            "protective — keep up the good work!",
            "<b>3. Stay Physically Active</b> — Aim for at least 150 minutes of moderate "
            "exercise per week.",
            "<b>4. Balanced Nutrition</b> — Continue a diet rich in whole grains, fruits, "
            "vegetables, and lean protein.",
            "<b>5. Monitor Changes</b> — If you notice any changes in thirst, urination, "
            "fatigue, or vision, consult your doctor promptly.",
        ],
    }
    for item in action_plans.get(risk_level, action_plans["Moderate"]):
        story.append(Paragraph(f"<bullet>&bull;</bullet> {item}", styles["bullet"]))
        story.append(Spacer(1, 2 * mm))

    story.append(Spacer(1, 6 * mm))

    # ── Lifestyle Tips ────────────────────────────────────────────────
    story.append(Paragraph("Lifestyle Tips for Diabetes Prevention", styles["heading"]))

    lifestyle_tips = [
        ("<b>Diet:</b> Follow a Mediterranean or DASH eating pattern. Prioritise "
         "non-starchy vegetables, whole grains, legumes, nuts, and lean proteins. "
         "Limit sugary beverages and processed foods."),
        ("<b>Exercise:</b> Aim for 150+ minutes of moderate aerobic activity per week "
         "(brisk walking, swimming, cycling). Add 2-3 sessions of resistance training."),
        ("<b>Sleep:</b> Aim for 7-9 hours of quality sleep per night. Poor sleep is "
         "linked to insulin resistance and weight gain."),
        ("<b>Stress Management:</b> Chronic stress raises cortisol, which can impair "
         "glucose metabolism. Consider mindfulness, yoga, or counselling."),
        ("<b>Smoking Cessation:</b> If you smoke, quitting reduces your diabetes risk "
         "by 30-40%% within 5 years. Ask your doctor about cessation programs."),
    ]
    for tip in lifestyle_tips:
        story.append(Paragraph(f"<bullet>&bull;</bullet> {tip}", styles["bullet"]))
        story.append(Spacer(1, 2 * mm))

    story.append(Spacer(1, 8 * mm))

    # ── QR Code to CDC ────────────────────────────────────────────────
    story.append(Paragraph("Learn More", styles["heading"]))
    story.append(Paragraph(
        "Scan the QR code below to visit the CDC Diabetes Prevention page for "
        "evidence-based resources and tools:",
        styles["body"],
    ))
    story.append(Spacer(1, 4 * mm))

    try:
        qr_bytes = _generate_qr_bytes("https://www.cdc.gov/diabetes/")
        qr_img = Image(io.BytesIO(qr_bytes), width=3.5 * cm, height=3.5 * cm)
        qr_img.hAlign = "CENTER"
        story.append(qr_img)
    except Exception as exc:
        logger.warning("QR code generation failed: %s", exc)
        story.append(Paragraph(
            '<link href="https://www.cdc.gov/diabetes/" color="blue">'
            "https://www.cdc.gov/diabetes/</link>",
            styles["body"],
        ))

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph(
        '<font color="#0d9488"><b>https://www.cdc.gov/diabetes/</b></font>',
        ParagraphStyle("QRLink", alignment=TA_CENTER, fontSize=9, leading=12),
    ))

    story.append(Spacer(1, 10 * mm))

    # Final disclaimer
    story.append(Paragraph(
        "<i>This report was generated by the RiskLens AI system on "
        f"{generated_at}. It is intended for informational and educational "
        "purposes only and does not constitute a medical diagnosis. Always "
        "consult a qualified healthcare professional for medical advice, "
        "diagnosis, and treatment.</i>",
        styles["small"],
    ))

    # ── Build PDF ─────────────────────────────────────────────────────
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()

"""
predict.py — Prediction endpoint for the RiskLens Diabetes Risk Predictor.

Accepts all 21 BRFSS feature values, runs feature engineering and the XGBoost
model, computes SHAP explanations, and returns a structured JSON response with
the risk score, risk level, clinical recommendation, and feature-level drivers.
"""

from __future__ import annotations

import logging
from typing import Literal

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from api.shap_utils import compute_shap

logger = logging.getLogger("risklens.predict")

router = APIRouter(prefix="/api", tags=["prediction"])


# ---------------------------------------------------------------------------
# Feature engineering (mirrors src/preprocess.py)
# ---------------------------------------------------------------------------
def _engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add the same composite features created during training."""
    df = df.copy()
    df["Cardio_Risk"] = (
        df["HighBP"] + df["HighChol"] + df["HeartDiseaseorAttack"] + df["Stroke"]
    )
    df["Lifestyle_Risk"] = (
        (1 - df["PhysActivity"])
        + (1 - df["Fruits"])
        + (1 - df["Veggies"])
        + df["Smoker"]
    )
    df["Health_Access"] = df["AnyHealthcare"] - df["NoDocbcCost"]
    df["BMI_x_Age"] = df["BMI"] * df["Age"]
    return df


# ---------------------------------------------------------------------------
# Human-readable feature names for the front-end
# ---------------------------------------------------------------------------
FEATURE_LABELS: dict[str, str] = {
    "HighBP": "High Blood Pressure",
    "HighChol": "High Cholesterol",
    "CholCheck": "Cholesterol Check (5 yrs)",
    "BMI": "Body Mass Index",
    "Smoker": "Smoker (≥ 100 cigarettes)",
    "Stroke": "History of Stroke",
    "HeartDiseaseorAttack": "Heart Disease / Attack",
    "PhysActivity": "Physical Activity",
    "Fruits": "Fruit Consumption",
    "Veggies": "Vegetable Consumption",
    "HvyAlcoholConsump": "Heavy Alcohol Consumption",
    "AnyHealthcare": "Has Healthcare Coverage",
    "NoDocbcCost": "Couldn't See Doctor (Cost)",
    "GenHlth": "General Health (1-5)",
    "MentHlth": "Mental Health (bad days/mo)",
    "PhysHlth": "Physical Health (bad days/mo)",
    "DiffWalk": "Difficulty Walking",
    "Sex": "Sex (0=F, 1=M)",
    "Age": "Age Category (1-13)",
    "Education": "Education Level (1-6)",
    "Income": "Income Level (1-8)",
    "Cardio_Risk": "Cardiovascular Risk Score",
    "Lifestyle_Risk": "Lifestyle Risk Score",
    "Health_Access": "Health Access Score",
    "BMI_x_Age": "BMI × Age Interaction",
}


# ---------------------------------------------------------------------------
# Pydantic request / response models
# ---------------------------------------------------------------------------
class PredictionRequest(BaseModel):
    """All 21 BRFSS health-indicator inputs required for a prediction."""

    HighBP: int = Field(..., ge=0, le=1, description="High blood pressure: 0=No, 1=Yes")
    HighChol: int = Field(..., ge=0, le=1, description="High cholesterol: 0=No, 1=Yes")
    CholCheck: int = Field(..., ge=0, le=1, description="Cholesterol check in past 5 years: 0=No, 1=Yes")
    BMI: float = Field(..., ge=10, le=100, description="Body Mass Index")
    Smoker: int = Field(..., ge=0, le=1, description="Smoked ≥100 cigarettes in lifetime: 0=No, 1=Yes")
    Stroke: int = Field(..., ge=0, le=1, description="Ever told you had a stroke: 0=No, 1=Yes")
    HeartDiseaseorAttack: int = Field(..., ge=0, le=1, description="CHD or MI: 0=No, 1=Yes")
    PhysActivity: int = Field(..., ge=0, le=1, description="Physical activity in past 30 days: 0=No, 1=Yes")
    Fruits: int = Field(..., ge=0, le=1, description="Consume fruit ≥1/day: 0=No, 1=Yes")
    Veggies: int = Field(..., ge=0, le=1, description="Consume vegetables ≥1/day: 0=No, 1=Yes")
    HvyAlcoholConsump: int = Field(..., ge=0, le=1, description="Heavy drinker: 0=No, 1=Yes")
    AnyHealthcare: int = Field(..., ge=0, le=1, description="Has any healthcare coverage: 0=No, 1=Yes")
    NoDocbcCost: int = Field(..., ge=0, le=1, description="Couldn't see doctor because of cost: 0=No, 1=Yes")
    GenHlth: int = Field(..., ge=1, le=5, description="General health: 1=Excellent … 5=Poor")
    MentHlth: float = Field(..., ge=0, le=30, description="Days of poor mental health (past 30)")
    PhysHlth: float = Field(..., ge=0, le=30, description="Days of poor physical health (past 30)")
    DiffWalk: int = Field(..., ge=0, le=1, description="Serious difficulty walking: 0=No, 1=Yes")
    Sex: int = Field(..., ge=0, le=1, description="Sex: 0=Female, 1=Male")
    Age: int = Field(..., ge=0, le=13, description="Age category 0-13 (12-17 … 80+)")
    Education: int = Field(..., ge=1, le=6, description="Education level 1-6")
    Income: int = Field(..., ge=1, le=8, description="Income level 1-8")


class DriverDetail(BaseModel):
    """A single SHAP-driven risk driver."""
    feature: str
    featureLabel: str
    value: float
    shapValue: float
    direction: Literal["risk", "protective"]


class PredictionResponse(BaseModel):
    """Full prediction result returned to the front-end."""
    riskScore: int = Field(..., ge=0, le=100, description="Risk score 0-100")
    riskLevel: Literal["Low", "Moderate", "High"]
    riskColor: str = Field(..., description="Hex colour for UI rendering")
    clinicalAction: str
    probability: float = Field(..., ge=0.0, le=1.0)
    topDrivers: list[DriverDetail]
    protectiveFactors: list[DriverDetail] = Field(default_factory=list)
    allShapValues: dict[str, float]


# ---------------------------------------------------------------------------
# Clinical-action text per risk tier
# ---------------------------------------------------------------------------
def _clinical_action(risk_level: str) -> str:
    actions = {
        "Low": (
            "Your current risk is low. Continue healthy habits and schedule "
            "routine annual screenings with your primary-care provider."
        ),
        "Moderate": (
            "Moderate risk detected. Consider scheduling an HbA1c or fasting "
            "glucose test and discuss lifestyle modifications with your doctor."
        ),
        "High": (
            "High risk indicated. Urgent clinical evaluation recommended — "
            "request a comprehensive metabolic panel, HbA1c, and consider "
            "referral to an endocrinologist."
        ),
    }
    return actions.get(risk_level, actions["Moderate"])


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------
@router.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest, req: Request):
    """Run the diabetes risk prediction pipeline.

    Steps:
        1. Build a single-row DataFrame from the validated request.
        2. Engineer 4 composite features (matches training pipeline).
        3. Reorder columns to match the model's expected feature order.
        4. Obtain the predicted probability from the XGBoost model.
        5. Convert probability → 0-100 risk score & categorical level.
        6. Compute per-feature SHAP values.
        7. Extract the top 5 risk drivers and top 3 protective factors.
        8. Return the complete PredictionResponse.
    """
    try:
        # ── 1. Request → DataFrame ────────────────────────────────────
        input_data = request.model_dump()
        df = pd.DataFrame([input_data])

        # ── 2. Feature engineering ────────────────────────────────────
        df = _engineer_features(df)

        # ── 3. Column ordering ────────────────────────────────────────
        model = req.app.state.model
        feature_cols: list[str] = req.app.state.feature_cols

        # Ensure all expected columns are present
        missing = set(feature_cols) - set(df.columns)
        if missing:
            raise ValueError(f"Missing features after engineering: {missing}")

        df_ordered = df[feature_cols]

        # ── 4. Prediction ─────────────────────────────────────────────
        # Use predict_proba if available; fall back to predict otherwise.
        if hasattr(model, "predict_proba"):
            proba = float(model.predict_proba(df_ordered)[0, 1])
        else:
            proba = float(model.predict(df_ordered)[0])

        # ── 5. Score & level ──────────────────────────────────────────
        risk_score = int(round(proba * 100))
        risk_score = max(0, min(100, risk_score))

        if risk_score < 30:
            risk_level = "Low"
            risk_color = "#22c55e"   # green
        elif risk_score < 70:
            risk_level = "Moderate"
            risk_color = "#f59e0b"   # amber
        else:
            risk_level = "High"
            risk_color = "#ef4444"   # red

        clinical_action = _clinical_action(risk_level)

        # ── 6. SHAP values ────────────────────────────────────────────
        shap_dict = compute_shap(model, df_ordered, feature_cols)

        # ── 7. Top drivers & protective factors ───────────────────────
        sorted_positive = sorted(
            ((k, v) for k, v in shap_dict.items() if v > 0),
            key=lambda kv: kv[1],
            reverse=True,
        )
        sorted_negative = sorted(
            ((k, v) for k, v in shap_dict.items() if v < 0),
            key=lambda kv: kv[1],
        )

        top_drivers: list[DriverDetail] = []
        for feat, sv in sorted_positive[:5]:
            top_drivers.append(
                DriverDetail(
                    feature=feat,
                    featureLabel=FEATURE_LABELS.get(feat, feat),
                    value=float(df_ordered[feat].iloc[0]),
                    shapValue=round(sv, 6),
                    direction="risk",
                )
            )

        protective_factors: list[DriverDetail] = []
        for feat, sv in sorted_negative[:3]:
            protective_factors.append(
                DriverDetail(
                    feature=feat,
                    featureLabel=FEATURE_LABELS.get(feat, feat),
                    value=float(df_ordered[feat].iloc[0]),
                    shapValue=round(sv, 6),
                    direction="protective",
                )
            )

        # ── 8. Response ───────────────────────────────────────────────
        return PredictionResponse(
            riskScore=risk_score,
            riskLevel=risk_level,
            riskColor=risk_color,
            clinicalAction=clinical_action,
            probability=round(proba, 6),
            topDrivers=top_drivers,
            protectiveFactors=protective_factors,
            allShapValues={k: round(v, 6) for k, v in shap_dict.items()},
        )

    except ValueError as exc:
        logger.error("Validation error during prediction: %s", exc)
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected error during prediction")
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred while processing the prediction.",
        ) from exc

"""
preprocess.py
Data cleaning and preprocessing utilities for the Patient Disease Risk Predictor.
Dataset: CDC BRFSS Diabetes Health Indicators (253,680 records).

All 21 features are already numeric (no text encoding needed).
Feature engineering adds 4 composite features for a total of 25.

Two datasets are used:
- Balanced 50/50 split for training (prevents class imbalance bias)
- Full imbalanced binary for real-world testing
"""

import os

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

# ── Paths ──────────────────────────────────────────────────────────
RAW_DIR = os.path.join("data", "raw")
BALANCED_FILE = os.path.join(RAW_DIR, "diabetes_binary_5050split_health_indicators_BRFSS2015.csv")
FULL_FILE = os.path.join(RAW_DIR, "diabetes_binary_health_indicators_BRFSS2015.csv")

TARGET_COLUMN = "Diabetes_binary"
RANDOM_STATE = 42

# ── Original 21 BRFSS feature columns ─────────────────────────────
BRFSS_FEATURE_COLUMNS = [
    "HighBP", "HighChol", "CholCheck", "BMI", "Smoker",
    "Stroke", "HeartDiseaseorAttack", "PhysActivity",
    "Fruits", "Veggies", "HvyAlcoholConsump",
    "AnyHealthcare", "NoDocbcCost", "GenHlth",
    "MentHlth", "PhysHlth", "DiffWalk", "Sex",
    "Age", "Education", "Income",
]

# ── Engineered feature names ──────────────────────────────────────
ENGINEERED_COLUMNS = [
    "Cardio_Risk", "Lifestyle_Risk", "Health_Access", "BMI_x_Age",
]

# ── Human-readable label maps for Streamlit form ──────────────────
AGE_MAP = {
    "18-24": 1, "25-29": 2, "30-34": 3, "35-39": 4,
    "40-44": 5, "45-49": 6, "50-54": 7, "55-59": 8,
    "60-64": 9, "65-69": 10, "70-74": 11, "75-79": 12,
    "80+": 13,
}

GENHLTH_MAP = {
    "Excellent": 1, "Very Good": 2, "Good": 3, "Fair": 4, "Poor": 5,
}

EDUCATION_MAP = {
    "Never attended / Kindergarten": 1,
    "Elementary (Grades 1-8)": 2,
    "Some high school (Grades 9-11)": 3,
    "High school graduate / GED": 4,
    "Some college / technical school": 5,
    "College graduate": 6,
}

INCOME_MAP = {
    "Less than $10,000": 1,
    "$10,000 – $14,999": 2,
    "$15,000 – $19,999": 3,
    "$20,000 – $24,999": 4,
    "$25,000 – $34,999": 5,
    "$35,000 – $49,999": 6,
    "$50,000 – $74,999": 7,
    "$75,000 or more": 8,
}


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add composite risk scores and interaction features.

    Cardio_Risk:     sum of HighBP + HighChol + HeartDiseaseorAttack + Stroke (0-4)
    Lifestyle_Risk:  sum of no-PhysActivity + no-Fruits + no-Veggies + Smoker (0-4)
    Health_Access:   AnyHealthcare − NoDocbcCost (−1 to +1)
    BMI_x_Age:       BMI × Age bucket (metabolic risk interaction)
    """
    df = df.copy()
    df["Cardio_Risk"] = (
        df["HighBP"] + df["HighChol"] + df["HeartDiseaseorAttack"] + df["Stroke"]
    )
    df["Lifestyle_Risk"] = (
        (1 - df["PhysActivity"]) + (1 - df["Fruits"]) + (1 - df["Veggies"]) + df["Smoker"]
    )
    df["Health_Access"] = df["AnyHealthcare"] - df["NoDocbcCost"]
    df["BMI_x_Age"] = df["BMI"] * df["Age"]
    return df


def load_and_prepare(balanced_path=None, full_path=None):
    """
    Load both datasets, deduplicate, engineer features, and return
    train/val/test splits with a fitted scaler.

    Returns:
        X_train, X_val, X_test,
        X_train_scaled, X_val_scaled, X_test_scaled,
        y_train, y_val, y_test,
        scaler, feature_cols
    """
    if balanced_path is None:
        balanced_path = BALANCED_FILE
    if full_path is None:
        full_path = FULL_FILE

    # Load
    balanced = pd.read_csv(balanced_path)
    full = pd.read_csv(full_path)

    # Deduplicate
    balanced = balanced.drop_duplicates()
    full = full.drop_duplicates()

    # Engineer
    balanced = engineer_features(balanced)
    full = engineer_features(full)

    # Feature columns (exclude target + categorical bins if present)
    exclude = {TARGET_COLUMN, "BMI_Category", "Age_Group"}
    feature_cols = [c for c in balanced.columns if c not in exclude]

    X_bal = balanced[feature_cols]
    y_bal = balanced[TARGET_COLUMN]
    X_full = full[feature_cols]
    y_full = full[TARGET_COLUMN]

    # Split balanced for train/val
    X_train, X_val, y_train, y_val = train_test_split(
        X_bal, y_bal, test_size=0.2, random_state=RANDOM_STATE, stratify=y_bal,
    )

    # Full imbalanced as final test
    X_test, y_test = X_full, y_full

    # Scale (for LR and other linear models)
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)
    X_test_scaled = scaler.transform(X_test)

    return (
        X_train, X_val, X_test,
        X_train_scaled, X_val_scaled, X_test_scaled,
        y_train, y_val, y_test,
        scaler, feature_cols,
    )
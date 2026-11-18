"""
prepare_data.py
Derives the binary and balanced 50/50 CSVs from the 3-class BRFSS file.

The 3-class file has:
  0 = No diabetes, 1 = Prediabetes, 2 = Diabetes

We derive:
  - Binary: merge class 1+2 → 1 (Prediabetes/Diabetes)
  - Balanced 50/50: downsample the majority class to match minority

Saves to data/raw/ so the original file is never modified.

Usage:
    python src/prepare_data.py
"""

import os
import pandas as pd

THREE_CLASS_PATH = os.path.join("data", "diabetes_012_health_indicators_BRFSS2015.csv")
RAW_DIR = os.path.join("data", "raw")

BINARY_FILE = "diabetes_binary_health_indicators_BRFSS2015.csv"
BALANCED_FILE = "diabetes_binary_5050split_health_indicators_BRFSS2015.csv"


def main():
    os.makedirs(RAW_DIR, exist_ok=True)

    print("Loading 3-class file...")
    df = pd.read_csv(THREE_CLASS_PATH)
    print(f"  Shape: {df.shape}")
    print(f"  Target distribution:")
    print(f"    0 (No diabetes):  {(df['Diabetes_012'] == 0).sum():,}")
    print(f"    1 (Prediabetes):  {(df['Diabetes_012'] == 1).sum():,}")
    print(f"    2 (Diabetes):     {(df['Diabetes_012'] == 2).sum():,}")

    # ── Create binary version ─────────────────────────────────────
    binary = df.copy()
    binary["Diabetes_binary"] = (binary["Diabetes_012"] >= 1).astype(int)
    binary = binary.drop(columns=["Diabetes_012"])
    binary_path = os.path.join(RAW_DIR, BINARY_FILE)
    binary.to_csv(binary_path, index=False)
    print(f"\nBinary file saved: {binary_path}")
    print(f"  Shape: {binary.shape}")
    print(f"  Class 0: {(binary['Diabetes_binary'] == 0).sum():,}")
    print(f"  Class 1: {(binary['Diabetes_binary'] == 1).sum():,}")

    # ── Create balanced 50/50 version ─────────────────────────────
    pos = binary[binary["Diabetes_binary"] == 1]
    neg = binary[binary["Diabetes_binary"] == 0]
    minority_count = len(pos)

    # Downsample majority class to match minority
    neg_downsampled = neg.sample(n=minority_count, random_state=42)
    balanced = pd.concat([pos, neg_downsampled], ignore_index=True)
    balanced = balanced.sample(frac=1, random_state=42).reset_index(drop=True)

    balanced_path = os.path.join(RAW_DIR, BALANCED_FILE)
    balanced.to_csv(balanced_path, index=False)
    print(f"\nBalanced file saved: {balanced_path}")
    print(f"  Shape: {balanced.shape}")
    print(f"  Class 0: {(balanced['Diabetes_binary'] == 0).sum():,}")
    print(f"  Class 1: {(balanced['Diabetes_binary'] == 1).sum():,}")

    print("\nDone. Data preparation complete.")


if __name__ == "__main__":
    main()

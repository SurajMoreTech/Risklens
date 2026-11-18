"""
shap_utils.py — SHAP explanation utilities and chart generators.

Provides:
  • ``compute_shap``          – TreeExplainer wrapper with caching.
  • ``generate_waterfall_png`` – SHAP waterfall chart rendered to PNG bytes.
  • ``generate_gauge_png``     – Circular gauge chart rendered to PNG bytes.

All matplotlib rendering uses the non-interactive ``Agg`` backend so the API
can run headlessly on any server.
"""

from __future__ import annotations

import io
import logging
import math
from functools import lru_cache
from typing import Any

import matplotlib
matplotlib.use("Agg")  # Must come before any pyplot import
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import shap

logger = logging.getLogger("risklens.shap")


# ---------------------------------------------------------------------------
# SHAP computation
# ---------------------------------------------------------------------------
@lru_cache(maxsize=1)
def _get_explainer(model_id: int, model: Any) -> shap.TreeExplainer:
    """Return a cached ``TreeExplainer`` for the given model.

    We use ``id(model)`` as the cache key so the explainer is rebuilt only
    when a genuinely different model object is loaded.
    """
    logger.info("Creating new TreeExplainer for model id=%d", model_id)
    return shap.TreeExplainer(model)


def compute_shap(
    model: Any,
    input_df: pd.DataFrame,
    feature_cols: list[str],
) -> dict[str, float]:
    """Compute SHAP values for a single-row input DataFrame.

    Parameters
    ----------
    model:
        Trained tree-based model (XGBoost, LightGBM, etc.).
    input_df:
        DataFrame with exactly one row and columns matching *feature_cols*.
    feature_cols:
        Ordered list of feature names used during training.

    Returns
    -------
    dict
        Mapping of feature name → SHAP value (positive = increases risk).
    """
    explainer = _get_explainer(id(model), model)
    shap_values = explainer.shap_values(input_df[feature_cols])

    # For binary classifiers shap_values may be a list [class-0, class-1].
    if isinstance(shap_values, list):
        values = shap_values[1]  # class-1 = diabetes positive
    else:
        values = shap_values

    # Flatten to 1-D if needed
    values = np.asarray(values).flatten()

    return {feat: float(val) for feat, val in zip(feature_cols, values)}


# ---------------------------------------------------------------------------
# SHAP waterfall chart
# ---------------------------------------------------------------------------
def generate_waterfall_png(
    shap_values_dict: dict[str, float],
    base_value: float | None = None,
    max_display: int = 10,
) -> bytes:
    """Render a horizontal waterfall-style bar chart of SHAP values.

    Uses a clean matplotlib implementation instead of the built-in SHAP
    waterfall plot for better control over styling and compatibility.

    Parameters
    ----------
    shap_values_dict:
        {feature_name: shap_value} dict from ``compute_shap``.
    base_value:
        Expected base value (E[f(x)]). Shown as text if provided.
    max_display:
        Maximum number of features to display.

    Returns
    -------
    bytes
        PNG image bytes.
    """
    # Sort by absolute magnitude, take top N
    sorted_items = sorted(
        shap_values_dict.items(), key=lambda kv: abs(kv[1]), reverse=True
    )[:max_display]
    # Reverse so the most important feature is at the top
    sorted_items = list(reversed(sorted_items))

    features = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]

    fig, ax = plt.subplots(figsize=(8, max(4, len(features) * 0.45)))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    colours = ["#ef4444" if v > 0 else "#3b82f6" for v in values]

    y_pos = np.arange(len(features))
    bars = ax.barh(y_pos, values, color=colours, height=0.6, edgecolor="none")

    # Value labels on bars
    for bar, val in zip(bars, values):
        x_offset = bar.get_width()
        ha = "left" if val >= 0 else "right"
        ax.text(
            x_offset + (0.002 if val >= 0 else -0.002),
            bar.get_y() + bar.get_height() / 2,
            f"{val:+.4f}",
            va="center",
            ha=ha,
            fontsize=8,
            fontweight="bold",
            color="#374151",
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(features, fontsize=9, color="#374151")
    ax.set_xlabel("SHAP Value (impact on diabetes risk)", fontsize=10, color="#374151")
    ax.set_title("Feature Impact on Prediction", fontsize=12, fontweight="bold", color="#1f2937")
    ax.axvline(0, color="#9ca3af", linewidth=0.8, linestyle="-")

    # Legend
    risk_patch = mpatches.Patch(color="#ef4444", label="Increases risk")
    protect_patch = mpatches.Patch(color="#3b82f6", label="Decreases risk")
    ax.legend(handles=[risk_patch, protect_patch], loc="lower right", fontsize=8)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#d1d5db")
    ax.spines["bottom"].set_color("#d1d5db")

    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Risk-score gauge chart
# ---------------------------------------------------------------------------
def generate_gauge_png(score: int, risk_level: str) -> bytes:
    """Render a semicircular gauge chart showing the patient's risk score.

    The gauge is divided into three colour zones:
        0–29  green  (Low)
        30–69 amber  (Moderate)
        70–100 red   (High)

    Parameters
    ----------
    score:
        Integer risk score 0-100.
    risk_level:
        One of "Low", "Moderate", "High".

    Returns
    -------
    bytes
        PNG image bytes.
    """
    fig, ax = plt.subplots(figsize=(5, 3.2), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor("white")

    # Gauge spans from π (left) to 0 (right) — a 180° arc
    # We'll draw the gauge from 180° → 0° (left to right, as in a car gauge)
    start_angle = math.pi
    end_angle = 0.0

    # Zone boundaries (fraction of the 180° arc)
    zones = [
        (0.00, 0.30, "#22c55e"),  # Green  — Low
        (0.30, 0.70, "#f59e0b"),  # Amber  — Moderate
        (0.70, 1.00, "#ef4444"),  # Red    — High
    ]

    # Draw zone arcs
    n_pts = 200
    for frac_start, frac_end, colour in zones:
        theta_start = start_angle - frac_start * math.pi
        theta_end = start_angle - frac_end * math.pi
        theta = np.linspace(theta_start, theta_end, n_pts)
        inner = np.full_like(theta, 0.65)
        outer = np.full_like(theta, 1.0)
        ax.fill_between(theta, inner, outer, color=colour, alpha=0.85)

    # Needle
    needle_frac = max(0, min(score, 100)) / 100.0
    needle_angle = start_angle - needle_frac * math.pi
    ax.plot(
        [needle_angle, needle_angle],
        [0, 0.90],
        color="#1f2937",
        linewidth=2.5,
        solid_capstyle="round",
    )
    # Needle hub
    hub = plt.Circle((0, 0), 0.08, transform=ax.transData, color="#1f2937", zorder=5)
    ax.add_patch(hub)

    # Labels around the arc
    for val, label in [(0, "0"), (30, "30"), (70, "70"), (100, "100")]:
        angle = start_angle - (val / 100.0) * math.pi
        ax.text(
            angle, 1.15, label,
            ha="center", va="center",
            fontsize=8, color="#6b7280",
            transform=ax.get_xaxis_transform(),
        )

    # Central score display
    colour_map = {"Low": "#22c55e", "Moderate": "#f59e0b", "High": "#ef4444"}
    score_colour = colour_map.get(risk_level, "#6b7280")

    ax.text(
        math.pi / 2, -0.25,
        str(score),
        ha="center", va="center",
        fontsize=32, fontweight="bold",
        color=score_colour,
        transform=ax.transAxes,
    )
    ax.text(
        math.pi / 2, -0.45,
        f"{risk_level} Risk",
        ha="center", va="center",
        fontsize=11, fontweight="semibold",
        color=score_colour,
        transform=ax.transAxes,
    )

    # Hide polar scaffolding
    ax.set_ylim(0, 1.2)
    ax.set_thetamin(0)
    ax.set_thetamax(180)
    ax.set_axis_off()

    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

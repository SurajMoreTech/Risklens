"""
main.py — FastAPI application entry-point for the RiskLens Diabetes Risk Predictor.

Responsibilities:
  • Bootstrap the FastAPI app with CORS for the React frontend.
  • Load serialised ML artefacts (model, scaler, threshold, feature list) once at
    startup and store them on ``app.state`` so every request handler can access
    them without re-deserialising.
  • Mount the ``/api/predict`` and ``/api/report`` routers.
  • Expose a lightweight ``GET /api/health`` readiness probe.

Run with:
    uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager

import joblib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------------------------
# CORS origins — set ALLOWED_ORIGINS env var to a comma-separated list.
# Example (Render dashboard):
#   ALLOWED_ORIGINS=https://risklens.vercel.app,https://www.risklens.vercel.app
# Defaults to localhost only so the server is never open to "*" in production.
# ---------------------------------------------------------------------------
_raw_origins = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173",
)
ALLOWED_ORIGINS: list[str] = [o.strip() for o in _raw_origins.split(",") if o.strip()]

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("risklens.api")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "..", "models")


# ---------------------------------------------------------------------------
# Lifespan — load model artefacts once at startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load heavy ML artefacts into ``app.state`` during startup."""
    try:
        logger.info("Loading model artefacts from %s …", MODELS_DIR)
        app.state.model = joblib.load(os.path.join(MODELS_DIR, "best_model.pkl"))
        app.state.scaler = joblib.load(os.path.join(MODELS_DIR, "scaler.pkl"))
        app.state.threshold = joblib.load(os.path.join(MODELS_DIR, "threshold.pkl"))
        app.state.feature_cols = joblib.load(os.path.join(MODELS_DIR, "feature_cols.pkl"))
        app.state.model_name = joblib.load(os.path.join(MODELS_DIR, "model_name.pkl"))
        logger.info(
            "Model loaded: %s | Threshold: %.3f | Features: %d",
            app.state.model_name,
            app.state.threshold,
            len(app.state.feature_cols),
        )
    except FileNotFoundError as exc:
        logger.critical("Missing artefact — %s. Server cannot start.", exc)
        sys.exit(1)
    except Exception as exc:
        logger.critical("Failed to load artefacts: %s", exc, exc_info=True)
        sys.exit(1)

    yield  # ← Application serves requests between these lines

    # Shutdown: nothing to clean up for now.
    logger.info("Shutting down RiskLens API.")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="RiskLens — Diabetes Risk Predictor API",
    description=(
        "ML-powered diabetes risk assessment using the CDC BRFSS dataset. "
        "Provides risk scores, SHAP explanations, and downloadable PDF reports."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Browsers hide non-safelisted response headers from cross-origin JS unless
    # they are explicitly exposed — required for the personalised PDF filename.
    expose_headers=["Content-Disposition", "Content-Length"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
from api.predict import router as predict_router   # noqa: E402
from api.report import router as report_router     # noqa: E402

app.include_router(predict_router)
app.include_router(report_router)


# ---------------------------------------------------------------------------
# Health-check
# ---------------------------------------------------------------------------
@app.get("/api/health", tags=["system"])
async def health_check():
    """Lightweight readiness probe.

    Returns HTTP 200 with basic status metadata when the service is healthy
    and model artefacts are loaded.
    """
    return {
        "status": "healthy",
        "model": getattr(app.state, "model_name", "unknown"),
        "features": len(getattr(app.state, "feature_cols", [])),
        "threshold": getattr(app.state, "threshold", None),
    }

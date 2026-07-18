# Handoff — RiskLens AI Disease Risk Predictor

Last updated: 2026-07-18

---

## Changes made this session

- **Fixed CORS `expose_headers` (code-review finding)** — `api/main.py` CORSMiddleware now sets `expose_headers=["Content-Disposition", "Content-Length"]`. Without it, browsers hide non-safelisted response headers from cross-origin JS, so `response.headers.get("Content-Disposition")` in `web/src/lib/api.js` was always `null` and every PDF downloaded as the fallback `risklensreport.pdf`. Verified with curl: `access-control-expose-headers` is now present on responses.
- **Installed `firebase-admin` locally** — it was in `api/requirements.txt` but not installed in the local Python environment, so `api/main.py` crashed on import (`ModuleNotFoundError: No module named 'firebase_admin'`) and the server never started. This was the main "project not working" cause locally.
- **Added `FIREBASE_SERVICE_ACCOUNT_FILE` support in `api/auth.py`** — for local dev you can now point at a key file on disk instead of pasting the whole JSON into an env var. `FIREBASE_SERVICE_ACCOUNT_JSON` still takes precedence (use that on Render).
- **Hardened `.gitignore`** — Firebase service-account key patterns (`*service-account*.json`, `*firebase-adminsdk*.json`) and `temp_diff.patch` are now ignored so secrets can't be committed by accident.

## Verified working (local, 2026-07-18)

- `python -m uvicorn api.main:app --port 8000` starts cleanly; model artefacts load (XGBoost, 25 features, threshold 0.525).
- `GET /api/health` → 200.
- CORS preflight (`OPTIONS /api/report/pdf` from `http://localhost:3000`) → 200 with correct allow headers.
- Responses now carry `access-control-expose-headers: Content-Disposition, Content-Length`.
- `POST /api/predict` without a token → 401 (auth enforcement works).
- `web/node_modules` present; frontend env (`web/.env.local`) has real Firebase config.

---

## Changes made previous session (2026-07-17)

- **Deleted `web/src/lib/firestore.js`** — was a 100% duplicate of `dashboard-store.js`; all consumers should import from `dashboard-store.js` instead.
- **Removed dead `BRFSS_FEATURE_COLUMNS` constant from `api/predict.py`** — never referenced anywhere; column order is sourced from `app.state.feature_cols` (loaded from `feature_cols.pkl` at startup).
- **Added `interview/` to `.gitignore`** — personal notes directory, not for the repo.

---

## Currently working

- API is fully functional: `POST /api/predict` → XGBoost + SHAP → JSON response, `POST /api/report/pdf` → ReportLab PDF download.
- Firebase Auth (Google Sign-In) works on Chrome/Firefox; Safari/Brave uses `signInWithRedirect` to avoid popup-blocker issues.
- Dashboard reads assessment history from Firestore (`dashboard-store.js`).
- Frontend deployed on Vercel; backend deployed on Render (`render.yaml` present).

---

## Last being worked on

- **CORS expose_headers fix + local environment repair** (this session, 2026-07-18) — see "Changes made this session" above.
- **Secure CORS allowlist + Firebase token verification** (commit `954d049`).
- **Ponytail cleanup pass** (commit `126dfb5`) — dead code removal across `api/` and `web/src/lib/`.

---

## Known bugs / risks

- ~~**`allow_origins=["*"]` with `allow_credentials=True`**~~ ✅ **Fixed** — `api/main.py` now reads `ALLOWED_ORIGINS` env var; defaults to localhost only. Set `ALLOWED_ORIGINS=https://your-app.vercel.app` in the Render dashboard.
- ~~**`Age` field accepts `0`**~~ ✅ **Fixed** — `predict.py` now validates `ge=1`, matching the BRFSS encoding (1–13).
- ~~**PDF filename is always `risklensreport.pdf`**~~ ✅ **Fixed** — `report.py` sanitises `patientName` and generates `risklens_<PatientName>.pdf`.
- ~~**No auth on API endpoints**~~ ✅ **Fixed** — `api/auth.py` verifies Firebase ID tokens on `/api/predict` and `/api/report/pdf`. Frontend (`api.js`) attaches `Authorization: Bearer <token>`.
- ~~**`Content-Disposition` not exposed via CORS**~~ ✅ **Fixed 2026-07-18** — `expose_headers=["Content-Disposition", "Content-Length"]` added to CORSMiddleware; the personalised filename now reaches the browser.
- **Auth not configured locally** — until `FIREBASE_SERVICE_ACCOUNT_JSON` (or the new `FIREBASE_SERVICE_ACCOUNT_FILE`) is set, `/api/predict` and `/api/report/pdf` return 503/401. The health endpoint works regardless.

---

## Next steps

- [ ] **Set `FIREBASE_SERVICE_ACCOUNT_JSON` in Render dashboard** → paste the full contents of your Firebase service-account JSON key (Firebase Console → Project Settings → Service Accounts → Generate new key). For local dev, download the key somewhere OUTSIDE the repo and set `FIREBASE_SERVICE_ACCOUNT_FILE=<path-to-key.json>` before starting uvicorn.
- [ ] **Set `ALLOWED_ORIGINS` in Render dashboard** → `https://<your-app>.vercel.app`.
- [ ] End-to-end test in the browser: sign in → run an assessment → download PDF and confirm the filename is `risklens_<PatientName>.pdf` (not the fallback).
- [ ] Expand disease support beyond diabetes (Heart Disease, Stroke — listed in README future enhancements).
- [ ] Add a Doctor Dashboard with role-based access control.
- [ ] Write unit tests for `_engineer_features`, the SHAP utility, and the PDF generator.
- [ ] Add an AI chatbot / conversational interface.

---

## Architecture quick-reference

| Layer | Tech | Entry point |
|---|---|---|
| Frontend | Next.js (App Router) | `web/src/app/` |
| Auth | Firebase Auth (Google) | `web/src/lib/auth.js` |
| Firestore | Firebase Firestore | `web/src/lib/dashboard-store.js` |
| API client | Fetch wrapper | `web/src/lib/api.js` |
| Backend | FastAPI + Uvicorn | `api/main.py` |
| Prediction | XGBoost + SHAP | `api/predict.py` |
| PDF Reports | ReportLab | `api/report.py`, `api/pdf_generator.py` |
| ML training | Scikit-learn pipeline | `src/` |
| Models | Serialised `.pkl` files | `models/` |
| Deployment (API) | Render | `render.yaml` |
| Deployment (Web) | Vercel | (Vercel project settings) |

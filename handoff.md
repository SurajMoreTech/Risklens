# Handoff — RiskLens AI Disease Risk Predictor

Last updated: 2026-07-17

---

## Changes made this session

- **Deleted `web/src/lib/firestore.js`** — was a 100% duplicate of `dashboard-store.js`; all consumers should import from `dashboard-store.js` instead.
- **Removed dead `ALLOWED_ORIGINS` list from `api/main.py`** — it was never wired into the middleware (CORS is set to `allow_origins=["*"]`), so the list was misleading dead code.
- **Removed dead `safe_name` variable from `api/report.py`** — the filename was always hardcoded to `"risklensreport.pdf"`; the sanitisation block was unreachable.
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

- **Ponytail cleanup pass** (commit `126dfb5`) — dead code removal across `api/` and `web/src/lib/`.
- **Footer contact info** (commit `85e1f70`) — Suraj More's details added to the footer.
- **API payload logging** (commit `cb08bf1`) — request body now logged on prediction calls for debugging.

---

## Known bugs / risks

- ~~**`allow_origins=["*"]` with `allow_credentials=True`**~~ ✅ **Fixed** — `api/main.py` now reads `ALLOWED_ORIGINS` env var; defaults to localhost only. Set `ALLOWED_ORIGINS=https://your-app.vercel.app` in the Render dashboard.
- ~~**`Age` field accepts `0`**~~ ✅ **Fixed** — `predict.py` now validates `ge=1`, matching the BRFSS encoding (1–13).
- ~~**PDF filename is always `risklensreport.pdf`**~~ ✅ **Fixed** — `report.py` sanitises `patientName` and generates `risklens_<PatientName>.pdf`.
- **No auth on API endpoints** — ✅ **Fixed** — `api/auth.py` verifies Firebase ID tokens on `/api/predict` and `/api/report/pdf`. Frontend (`api.js`) attaches `Authorization: Bearer <token>`. **Action required**: set `FIREBASE_SERVICE_ACCOUNT_JSON` in Render dashboard (see next steps).

---

## Next steps

- [x] Fix CORS: `allow_origins=["*"]` → env-var-driven allowlist (`ALLOWED_ORIGINS`).
- [x] Tighten `Age` field validation: `ge=0` → `ge=1`.
- [x] Personalised PDF filenames: sanitise `patientName` and use in `Content-Disposition`.
- [x] Add Firebase ID-token verification: `api/auth.py` + `verify_token` dependency on `/api/predict` and `/api/report/pdf`. Frontend injects `Authorization: Bearer <token>`.
- [ ] **Set `ALLOWED_ORIGINS` in Render dashboard** → `https://<your-app>.vercel.app`.
- [ ] **Set `FIREBASE_SERVICE_ACCOUNT_JSON` in Render dashboard** → paste the full contents of your Firebase service-account JSON key (Firebase Console → Project Settings → Service Accounts → Generate new key).
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

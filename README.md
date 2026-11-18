# 🩺 RiskLens – AI Disease Risk Predictor

RiskLens is a full-stack web application that predicts a patient's diabetes risk using machine learning. It combines a Next.js frontend, FastAPI backend, and Firebase Authentication to provide secure predictions, health insights, and downloadable reports.

## ✨ Features

- 🔐 Firebase Authentication (Google Sign-In)
- 🤖 Machine Learning-based Diabetes Risk Prediction (XGBoost)
- 📊 Interactive Dashboard & SHAP Explainability Visualizations
- 📄 PDF Report Generation
- 📧 Report Sharing via Email
- 📱 Responsive User Interface
- ⚡ FastAPI REST API

## 🛠 Tech Stack

| Category | Technologies |
|----------|--------------|
| Frontend | Next.js, React |
| Backend | FastAPI, Python |
| Machine Learning | Scikit-learn, XGBoost, SHAP, Pandas, NumPy |
| Database | Firebase Firestore |
| Authentication | Firebase Authentication |
| Reports | ReportLab (PDF generation) |

## 📂 Project Structure

```
patient-disease-risk-predictor/
├── api/          # FastAPI backend (prediction, reports, SHAP)
├── data/         # Dataset (download separately — see below)
├── models/       # Trained ML models (.pkl)
├── src/          # ML training pipeline
├── app/          # Streamlit app (legacy)
└── web/          # Next.js frontend
```

## 🚀 Getting Started

### Clone the repository

```bash
git clone https://github.com/SurajMoreTech/Risklens.git
cd Risklens
```

### Backend

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

### Frontend

```bash
cd web
npm install
npm run dev
```

### Firebase Setup

1. Create a `.env.local` file inside `web/` (see `web/.env.example` for the template)
2. Add your Firebase project credentials
3. Enable **Google Authentication** and **Firestore** in the Firebase Console

### Dataset

Download the CDC BRFSS dataset from [Kaggle](https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset) and place it in the `data/` folder.

## 🔮 Future Enhancements

- Multiple disease prediction
- Doctor dashboard
- AI chatbot
- Cloud deployment
- Role-based access control

## 👨‍💻 Author

**Suraj More**

- GitHub: [SurajMoreTech](https://github.com/SurajMoreTech)

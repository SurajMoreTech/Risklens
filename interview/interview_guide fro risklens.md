# 🩺 RiskLens: Comprehensive Project Breakdown & Interview Guide

This document is designed to help you explain **RiskLens** end-to-end in an interview. It covers the *what*, *why*, and *how* of the project, diving deep into your technical decisions, machine learning rationale, and software architecture.

---

## 1. The Core Problem & Business Value
**Interview Question: "What did you build, and why does it matter?"**

**Your Answer:**
I built **RiskLens**, a full-stack, AI-powered pre-screening tool for Type 2 Diabetes. 

Currently, millions of people have prediabetes or diabetes and don't know it because traditional diagnosis requires a blood test (like HbA1c or fasting glucose), which involves a clinic visit and costs money. 

**My solution** was to build a non-invasive "Stage 1" triage tool. It takes 21 simple lifestyle and health questions (that take 5 minutes to answer) and uses machine learning to predict their risk. It acts as a filter: it tells high-risk individuals, *"You need to go get a blood test immediately,"* while saving healthy individuals the time and cost.

---

## 2. The Machine Learning Pipeline (The "Why")
**Interview Question: "Walk me through your ML approach. Why did you choose the model you did?"**

### Deep Dive: The Data, The Imbalance, and The Accuracy Paradox
**Interview Question: "Tell me about the dataset. How did you handle data imbalances?"**

- **The Dataset (BRFSS):** I used the **CDC BRFSS (Behavioral Risk Factor Surveillance System) 2015 dataset**. The BRFSS is an annual telephone survey conducted by the CDC that collects data on health-related risk behaviors, chronic health conditions, and use of preventive services. The dataset contains **253,680 survey responses** with 21 feature columns (like BMI, age, physical activity, etc.) and a target variable indicating diabetes status.

- **The Challenge (Class Imbalance & The Accuracy Paradox):** 
  Out of the 253,680 records, only about 39,977 (approx 15%) represent individuals with prediabetes or diabetes, while the vast majority (approx 85%) represent healthy individuals. 
  This introduces a classic machine learning problem called the **Accuracy Paradox**. If I train a model on this raw, imbalanced data, the algorithm quickly figures out that it can achieve 85% accuracy simply by predicting "No Diabetes" for *every single person*. 
  From an algorithm's perspective, 85% accuracy is a great score. But from a medical perspective, it's catastrophic: the model has a Sensitivity (Recall) of 0%. It missed every single diabetic patient.

- **The Fix (Strategic Resampling):** 
  To force the model to actually learn the underlying patterns of diabetes (rather than just guessing the majority class), I used a technique called **Random Undersampling**. 
  1. I took all 39,977 positive cases (diabetics).
  2. I randomly sampled an *exact equal number* (39,977) of negative cases (non-diabetics) from the majority pool.
  3. This created a new, artificially **balanced 50/50 training dataset** of roughly 80,000 rows.
  
- **Crucial Best Practice (Preventing Data Leakage):**
  *(This is a great point to bring up in an interview to show seniority.)* 
  I **only** used that artificial 50/50 split for the *training* phase. For the *testing and validation* phase, I evaluated the model against the **full, original 253,680-row imbalanced dataset**. 
  Why? Because you must always evaluate your model on data that reflects the real world. If I tested the model on a 50/50 dataset, the evaluation metrics would be artificially inflated. Testing on the full dataset proves the model actually works in a real-world clinical setting where diabetes is the minority class.

### Model Selection: Why XGBoost?
I trained and compared four models:
1. **Logistic Regression:** As an interpretable baseline.
2. **Random Forest:** To capture non-linear relationships.
3. **LightGBM:** For speed and efficiency.
4. **XGBoost:** **(The Winner)**

**Why XGBoost won:**
XGBoost is the state-of-the-art for tabular (spreadsheet-style) data. It handles non-linear relationships beautifully, is robust against outliers, and in my tests, it achieved the best **Test AUROC (0.8227)**. Deep Learning (Neural Networks) would be overkill here and less interpretable. 

### Healthcare Metrics vs. Standard Accuracy
**Crucial Interview Point:** "In healthcare, standard accuracy is a trap."
I evaluated my models based on **Sensitivity (Recall)** and **Specificity**, not just accuracy.
- **Why?** Missing a diabetic patient (False Negative) is dangerous. Telling a healthy person to get a blood test (False Positive) is just a slight inconvenience. 
- Therefore, I tuned the model's threshold (using Youden's J statistic) to prioritize **Sensitivity (Recall)**, achieving nearly **80% recall**.

### Explainability (SHAP)
Doctors and patients won't trust a "black box" that just spits out a number. I integrated **SHAP (SHapley Additive exPlanations)**. For every single prediction, SHAP calculates exactly *how much* each feature (like BMI, Age, or Blood Pressure) pushed the score up or down. This allows the app to generate a personalized explanation for the user.

---

## 3. The Tech Stack (The "Why")
**Interview Question: "Why did you choose this specific tech stack for the application?"**

My goal was to build a modern, scalable application that separates the heavy machine learning computations from the fast, interactive user interface.

### 🐍 Backend: FastAPI (Python)
- **Why not Django or Flask?** FastAPI is significantly faster (built on Starlette/asyncio). It automatically generates Swagger API documentation, which made it incredibly easy to test my ML endpoints. Since my ML stack (Pandas, Scikit-learn, XGBoost, SHAP) is in Python, the backend *had* to be Python. FastAPI is the most modern choice for serving ML models.
- **What it does:** It loads the `.pkl` XGBoost model into memory on startup. It exposes endpoints to receive the 21 questions, run the model prediction, calculate SHAP values, and dynamically generate a PDF report using `ReportLab`.

### ⚛️ Frontend: Next.js & React
- **Why Next.js?** Next.js provides a robust React framework. I wanted a clean, medical-grade, responsive UI. Next.js offers great performance, component reusability, and a modern developer experience. 
- **What it does:** It handles the multi-step questionnaire, displays the interactive results (including a dynamic risk gauge), and communicates with the FastAPI backend via REST API calls.

### 🔐 Auth & Database: Firebase
- **Why Firebase?** Security and speed of development. 
- **Authentication:** Firebase Auth gives me enterprise-grade security (Google Sign-in) out of the box without me having to manage password hashing.
- **Firestore (Database):** NoSQL document database. 
- **Crucial Architecture Decision (HIPAA/Privacy mindset):** I intentionally separated the data. I have a `users` collection (containing names and emails - PII) and an `assessments` collection (containing the health data and risk scores). This means the health data is kept separate from identity, simulating real-world medical data privacy best practices.

---

## 4. End-to-End Workflow: How it actually works
**Interview Question: "Walk me through what happens when a user clicks 'Predict'?"**

1. **Frontend:** The user fills out the 21-question React form and clicks submit.
2. **API Call:** Next.js sends a JSON payload via an HTTP POST request to the FastAPI backend (`/api/predict`).
3. **Preprocessing:** FastAPI receives the data, applies the same `MinMaxScaler` used during training, and engineers the 4 composite features (like `Cardio_Risk`).
4. **Prediction:** The XGBoost model (`.predict_proba()`) calculates the risk probability. 
5. **Explainability:** The `shap.TreeExplainer` calculates the feature contributions for this specific user.
6. **Response:** FastAPI sends back a JSON response containing the Risk Score (0-100), Risk Level (Low/Med/High), and the top SHAP drivers.
7. **UI Update:** The React frontend displays the risk gauge and explanations.
8. **Report Generation (Optional):** If the user clicks "Download Report", a separate call goes to FastAPI, which uses `ReportLab` to draw a medical-grade PDF containing the SHAP charts and returns it as a downloadable file stream.
9. **Persistence:** If logged in, the assessment data is saved to Firebase Firestore.

---

## 5. Potential Interview Curveballs

**Q: "What were the biggest challenges you faced?"**
*Answer:* "Handling the class imbalance in the CDC dataset. Initially, the model looked highly accurate but had terrible recall (it wasn't finding the diabetics). I had to pivot to training on a 50/50 balanced split and tuning the decision threshold to prioritize recall. Another challenge was translating the complex XGBoost output into a user-friendly SHAP waterfall chart that a non-technical patient could understand."

**Q: "If you had 3 more months, what would you add?"**
*Answer:* "I would implement the 'Stage 2' of this pipeline. Right now, this is a pre-screening tool (questionnaire only). I would build a second model that takes this risk score *plus* actual lab results (like HbA1c and Fasting Glucose) to provide a definitive clinical diagnosis probability. I'd also deploy the ML models using a proper MLOps tool like MLflow or Dockerize the FastAPI backend for cloud deployment."

**Q: "Why didn't you use Deep Learning?"**
*Answer:* "Deep learning is fantastic for unstructured data like images or text. But for structured, tabular data like this survey, gradient boosting trees like XGBoost consistently outperform neural networks, require less data to train, and crucially for healthcare, are much easier to interpret and explain using SHAP."

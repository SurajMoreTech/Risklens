"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { AuthProvider, useAuth } from "@/lib/auth";
import Navbar from "@/components/Navbar";
import ProgressBar from "@/components/ProgressBar";
import LoadingAnalysis from "@/components/LoadingAnalysis";
import { predictRisk } from "@/lib/api";
import { saveDashboardAssessment } from "@/lib/dashboard-store";

// ── Question definitions (21 BRFSS questions) ─────────────────
const QUESTIONS = [
  // Cardiovascular (6)
  { key: "HighBP", category: "❤️ Cardiovascular", question: "Have you been told by a doctor that you have high blood pressure?", help: "This includes borderline high or pre-hypertension.", type: "yesno" },
  { key: "HighChol", category: "❤️ Cardiovascular", question: "Have you been told by a doctor that you have high cholesterol?", help: "Based on a blood cholesterol test.", type: "yesno" },
  { key: "CholCheck", category: "❤️ Cardiovascular", question: "Have you had a cholesterol check within the past 5 years?", help: "Any blood test that included cholesterol levels.", type: "yesno" },
  { key: "Stroke", category: "❤️ Cardiovascular", question: "Have you ever had a stroke?", help: "A stroke occurs when blood flow to the brain is blocked.", type: "yesno" },
  { key: "HeartDiseaseorAttack", category: "❤️ Cardiovascular", question: "Have you ever been told you have coronary heart disease or had a heart attack?", help: "Includes coronary heart disease (CHD) or myocardial infarction (MI).", type: "yesno" },
  { key: "DiffWalk", category: "❤️ Cardiovascular", question: "Do you have serious difficulty walking or climbing stairs?", help: "Due to a physical, mental, or emotional condition.", type: "yesno" },

  // Body & Health (4)
  { key: "BMI", category: "🏥 Body & Health", question: "What is your Body Mass Index (BMI)?", help: "BMI = weight (kg) / height² (m). Average is 25. Use a BMI calculator if unsure.", type: "number", min: 10, max: 98, default: 25, unit: "kg/m²" },
  { key: "GenHlth", category: "🏥 Body & Health", question: "How would you rate your general health?", help: "Your overall health status in general.", type: "select", options: [
    { label: "Excellent", value: 1 }, { label: "Very Good", value: 2 },
    { label: "Good", value: 3 }, { label: "Fair", value: 4 }, { label: "Poor", value: 5 },
  ]},
  { key: "PhysHlth", category: "🏥 Body & Health", question: "In the past 30 days, how many days was your physical health not good?", help: "Includes physical illness or injury. Enter 0 if none.", type: "number", min: 0, max: 30, default: 0, unit: "days" },
  { key: "MentHlth", category: "🏥 Body & Health", question: "In the past 30 days, how many days was your mental health not good?", help: "Includes stress, depression, or emotional problems. Enter 0 if none.", type: "number", min: 0, max: 30, default: 0, unit: "days" },

  // Lifestyle (5)
  { key: "Smoker", category: "🏃 Lifestyle", question: "Have you smoked at least 100 cigarettes in your lifetime?", help: "100 cigarettes = about 5 packs. This indicates a smoking history.", type: "yesno" },
  { key: "PhysActivity", category: "🏃 Lifestyle", question: "Have you had any physical activity in the past 30 days?", help: "Physical activity outside of your regular job (exercise, walking, etc.).", type: "yesno" },
  { key: "Fruits", category: "🏃 Lifestyle", question: "Do you consume fruit at least once per day?", help: "Includes 100% fruit juice.", type: "yesno" },
  { key: "Veggies", category: "🏃 Lifestyle", question: "Do you consume vegetables at least once per day?", help: "Includes all forms of vegetables (fresh, frozen, canned).", type: "yesno" },
  { key: "HvyAlcoholConsump", category: "🏃 Lifestyle", question: "Are you a heavy alcohol consumer?", help: "Men: more than 14 drinks per week. Women: more than 7 drinks per week.", type: "yesno" },

  // Demographics (4)
  { key: "Sex", category: "👤 Demographics", question: "What is your biological sex?", help: "As assigned at birth, for medical risk assessment.", type: "select", options: [
    { label: "Female", value: 0 }, { label: "Male", value: 1 },
  ]},
  { key: "Age", category: "👤 Demographics", question: "What is your age range?", help: "Select the bracket that includes your current age.", type: "select", options: [
    { label: "12-17", value: 0 }, { label: "18-24", value: 1 }, { label: "25-29", value: 2 }, { label: "30-34", value: 3 },
    { label: "35-39", value: 4 }, { label: "40-44", value: 5 }, { label: "45-49", value: 6 },
    { label: "50-54", value: 7 }, { label: "55-59", value: 8 }, { label: "60-64", value: 9 },
    { label: "65-69", value: 10 }, { label: "70-74", value: 11 }, { label: "75-79", value: 12 },
    { label: "80+", value: 13 },
  ]},
  { key: "Education", category: "👤 Demographics", question: "What is your highest level of education?", help: "Education level can correlate with health literacy and access.", type: "select", options: [
    { label: "Never attended / Kindergarten", value: 1 },
    { label: "Elementary (Grades 1-8)", value: 2 },
    { label: "Some high school (Grades 9-11)", value: 3 },
    { label: "High school graduate / GED", value: 4 },
    { label: "Some college / technical school", value: 5 },
    { label: "College graduate", value: 6 },
  ]},
  { key: "Income", category: "👤 Demographics", question: "What is your annual household income?", help: "Income can affect healthcare access and nutrition quality.", type: "select", options: [
    { label: "Less than $10,000", value: 1 }, { label: "$10,000 – $14,999", value: 2 },
    { label: "$15,000 – $19,999", value: 3 }, { label: "$20,000 – $24,999", value: 4 },
    { label: "$25,000 – $34,999", value: 5 }, { label: "$35,000 – $49,999", value: 6 },
    { label: "$50,000 – $74,999", value: 7 }, { label: "$75,000 or more", value: 8 },
  ]},

  // Healthcare Access (2)
  { key: "AnyHealthcare", category: "🏥 Healthcare Access", question: "Do you have any kind of healthcare coverage?", help: "Includes health insurance, prepaid plans, or government plans.", type: "yesno" },
  { key: "NoDocbcCost", category: "🏥 Healthcare Access", question: "Was there a time in the past 12 months you couldn't see a doctor due to cost?", help: "Financial barrier to accessing healthcare.", type: "yesno" },
];

// ── Personal Details Form ─────────────────────────────────────
function PersonalDetailsStep({ data, onChange, onNext, errors }) {
  return (
    <div className="form-card" style={{ animation: "fadeInUp 0.5s ease-out" }}>
      <div className="form-header">
        <h2>Personal Details</h2>
        <p>We&apos;ll use this to generate your personalized report</p>
      </div>

      <div className="form-group">
        <label className="form-label">Full Name *</label>
        <input
          type="text"
          className="form-input"
          placeholder="Enter your full name"
          value={data.name}
          onChange={(e) => onChange("name", e.target.value)}
        />
        {errors.name && <div className="form-error">{errors.name}</div>}
      </div>

      <div className="form-group">
        <label className="form-label">Email Address *</label>
        <input
          type="email"
          className="form-input"
          placeholder="your@email.com"
          value={data.email}
          onChange={(e) => onChange("email", e.target.value)}
        />
        {errors.email && <div className="form-error">{errors.email}</div>}
      </div>

      <div className="form-row">
        <div className="form-group">
          <label className="form-label">
            Phone <span className="form-label-optional">(Optional)</span>
          </label>
          <input
            type="tel"
            className="form-input"
            placeholder="+1 (555) 000-0000"
            value={data.phone}
            onChange={(e) => onChange("phone", e.target.value)}
          />
        </div>
        <div className="form-group">
          <label className="form-label">Gender *</label>
          <select
            className="form-select"
            value={data.gender}
            onChange={(e) => onChange("gender", e.target.value)}
          >
            <option value="">Select gender</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Prefer not to say</option>
          </select>
          {errors.gender && <div className="form-error">{errors.gender}</div>}
        </div>
      </div>

      <div className="form-footer">
        <div></div>
        <button className="btn btn-primary" onClick={onNext}>
          Continue to Assessment →
        </button>
      </div>
    </div>
  );
}

// ── Single Question Component ─────────────────────────────────
function QuestionStep({ question, answer, onAnswer }) {
  return (
    <div className="question-card">
      <div className="question-category">{question.category}</div>
      <h3 className="question-text">{question.question}</h3>
      <p className="question-help">{question.help}</p>

      {question.type === "yesno" && (
        <div className="question-options">
          <button
            className={`option-btn ${answer === 0 ? "selected" : ""}`}
            onClick={() => onAnswer(0)}
          >
            <span className="option-indicator" />
            No
          </button>
          <button
            className={`option-btn ${answer === 1 ? "selected" : ""}`}
            onClick={() => onAnswer(1)}
          >
            <span className="option-indicator" />
            Yes
          </button>
        </div>
      )}

      {question.type === "select" && (
        <div className="question-options">
          {question.options.map((opt) => (
            <button
              key={opt.value}
              className={`option-btn ${answer === opt.value ? "selected" : ""}`}
              onClick={() => onAnswer(opt.value)}
            >
              <span className="option-indicator" />
              {opt.label}
            </button>
          ))}
        </div>
      )}

      {question.type === "number" && (
        <div className="question-number-input">
          <input
            type="number"
            min={question.min}
            max={question.max}
            value={answer ?? question.default}
            onChange={(e) => {
              const val = parseInt(e.target.value, 10);
              if (!isNaN(val)) onAnswer(val);
            }}
          />
          <span>{question.unit}</span>
        </div>
      )}
    </div>
  );
}

// ── Consent Step ──────────────────────────────────────────────
function ConsentStep({ consented, onChange, onPredict, loading }) {
  return (
    <div className="form-card" style={{ animation: "fadeInUp 0.5s ease-out" }}>
      <div className="form-header">
        <h2>Ready to Submit</h2>
        <p>Please review the consent below before getting your results</p>
      </div>

      <div className="checkbox-group" style={{ marginBottom: "1.5rem" }}>
        <input
          type="checkbox"
          id="consent"
          checked={consented}
          onChange={(e) => onChange(e.target.checked)}
        />
        <label htmlFor="consent">
          I consent to anonymized use of my health data for improving this
          screening model. My identity will never be shared. I understand this
          is a screening tool and not a medical diagnosis.
        </label>
      </div>

      <button
        className="btn btn-primary btn-lg w-full"
        onClick={onPredict}
        disabled={!consented || loading}
        style={{ width: "100%" }}
      >
        {loading ? "Processing..." : "🔬 Predict My Risk"}
      </button>
    </div>
  );
}

// ── Main Assessment Page ──────────────────────────────────────
function AssessmentContent() {
  const router = useRouter();
  const { user, signInWithGoogle } = useAuth();

  // Step: "personal" | "questions" | "consent" | "loading"
  const [step, setStep] = useState("personal");
  const [questionIndex, setQuestionIndex] = useState(0);
  const [personal, setPersonal] = useState({ name: "", email: "", phone: "", gender: "" });
  const [personalErrors, setPersonalErrors] = useState({});
  const [answers, setAnswers] = useState({});
  const [consented, setConsented] = useState(false);
  const [loading, setLoading] = useState(false);

  // Load from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem("risklens_assessment");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.personal) setPersonal(parsed.personal);
        if (parsed.answers) setAnswers(parsed.answers);
        if (parsed.questionIndex) setQuestionIndex(parsed.questionIndex);
        if (parsed.step && parsed.step !== "loading") setStep(parsed.step);
      }
    } catch (e) { /* ignore */ }
  }, []);

  // Save to localStorage
  useEffect(() => {
    try {
      localStorage.setItem("risklens_assessment", JSON.stringify({
        personal, answers, questionIndex, step: step === "loading" ? "consent" : step,
      }));
    } catch (e) { /* ignore */ }
  }, [personal, answers, questionIndex, step]);

  const handlePersonalChange = (field, value) => {
    setPersonal((prev) => ({ ...prev, [field]: value }));
    setPersonalErrors((prev) => ({ ...prev, [field]: null }));
  };

  const validatePersonal = () => {
    const errors = {};
    if (!personal.name || personal.name.trim().length < 2) errors.name = "Name must be at least 2 characters";
    if (!personal.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(personal.email)) errors.email = "Please enter a valid email";
    if (!personal.gender) errors.gender = "Please select your gender";
    setPersonalErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handlePersonalNext = () => {
    if (validatePersonal()) {
      setStep("questions");
    }
  };

  const handleAnswer = (value) => {
    const key = QUESTIONS[questionIndex].key;
    setAnswers((prev) => ({ ...prev, [key]: value }));

    // Auto-advance for yes/no and select after a short delay
    if (QUESTIONS[questionIndex].type !== "number") {
      setTimeout(() => {
        if (questionIndex < QUESTIONS.length - 1) {
          setQuestionIndex((prev) => prev + 1);
        } else {
          setStep("consent");
        }
      }, 300);
    }
  };

  const handleNext = () => {
    if (questionIndex < QUESTIONS.length - 1) {
      setQuestionIndex((prev) => prev + 1);
    } else {
      setStep("consent");
    }
  };

  const handleBack = () => {
    if (questionIndex > 0) {
      setQuestionIndex((prev) => prev - 1);
    } else {
      setStep("personal");
    }
  };

  // ── Refs to coordinate API completion + animation completion ──
  const apiDoneRef = useRef(false);
  const animDoneRef = useRef(false);

  const tryNavigate = useCallback(() => {
    if (apiDoneRef.current && animDoneRef.current) {
      router.push("/results");
    }
  }, [router]);

  const handlePredict = useCallback(async () => {
    apiDoneRef.current = false;
    animDoneRef.current = false;

    // Ensure the user is signed in so we can send a valid Firebase auth token.
    // If not yet logged in, trigger Google sign-in before proceeding.
    if (!user) {
      try {
        const signedInUser = await signInWithGoogle();
        if (!signedInUser) return; // user cancelled the popup
      } catch (signInError) {
        alert("Sign-in is required to get a prediction. Please try again.");
        return;
      }
    }

    setLoading(true);
    setStep("loading");

    try {
      // Fill defaults for any unanswered number questions
      const fullAnswers = {};
      QUESTIONS.forEach((q) => {
        if (answers[q.key] !== undefined) {
          fullAnswers[q.key] = answers[q.key];
        } else if (q.type === "number") {
          fullAnswers[q.key] = q.default;
        } else if (q.type === "yesno") {
          fullAnswers[q.key] = 0;
        } else if (q.type === "select") {
          fullAnswers[q.key] = q.options[0].value;
        }
      });

      console.log("[RiskLens] Sending prediction payload:", JSON.stringify(fullAnswers));
      const result = await predictRisk(fullAnswers);
      console.log("[RiskLens] Prediction succeeded:", result.riskScore);

      // Save to Firestore via dashboard-store
      let assessmentId = null;
      if (user) {
        try {
          assessmentId = await saveDashboardAssessment(
            user.uid,
            {
              riskScore: result.riskScore,
              riskLevel: result.riskLevel,
              clinicalAction: result.clinicalAction,
              inputs: fullAnswers,
              shapValues: result.allShapValues || {},
              topDrivers: result.topDrivers || [],
              protectiveFactors: result.protectiveFactors || [],
            },
            {
              name: personal.name,
              email: personal.email,
              phone: personal.phone,
            }
          );
        } catch (firebaseError) {
          console.error("Firebase save error:", firebaseError);
          // Continue even if Firebase save fails
        }
      }

      // Store result in sessionStorage for the results page
      sessionStorage.setItem("risklens_result", JSON.stringify({
        ...result,
        personal,
        inputs: fullAnswers,
        assessmentId,
      }));

      // Clear assessment progress
      localStorage.removeItem("risklens_assessment");

      // Mark API as done and try to navigate
      apiDoneRef.current = true;
      tryNavigate();

    } catch (error) {
      console.error("Prediction error:", error);
      alert("Error getting prediction. Make sure the API server is running.\n\nDetails: " + error.message);
      setStep("consent");
      setLoading(false);
      return;
    }
  }, [answers, personal, user, signInWithGoogle, tryNavigate]);

  const handleLoadingComplete = useCallback(() => {
    // Mark animation as done and try to navigate
    animDoneRef.current = true;
    tryNavigate();
  }, [tryNavigate]);

  return (
    <>
      <Navbar />
      <div className="form-section" style={{ paddingBottom: "4rem" }}>
        {step === "personal" && (
          <PersonalDetailsStep
            data={personal}
            onChange={handlePersonalChange}
            onNext={handlePersonalNext}
            errors={personalErrors}
          />
        )}

        {step === "questions" && (
          <div className="form-card">
            <ProgressBar current={questionIndex + 1} total={QUESTIONS.length} />

            <QuestionStep
              question={QUESTIONS[questionIndex]}
              answer={answers[QUESTIONS[questionIndex].key]}
              onAnswer={handleAnswer}
            />

            <div className="form-footer">
              <button className="btn btn-ghost" onClick={handleBack}>
                ← Back
              </button>
              {QUESTIONS[questionIndex].type === "number" && (
                <button className="btn btn-primary" onClick={handleNext}>
                  {questionIndex < QUESTIONS.length - 1 ? "Next →" : "Review & Submit"}
                </button>
              )}
            </div>
          </div>
        )}

        {step === "consent" && (
          <ConsentStep
            consented={consented}
            onChange={setConsented}
            onPredict={handlePredict}
            loading={loading}
          />
        )}

        {step === "loading" && (
          <LoadingAnalysis onComplete={handleLoadingComplete} />
        )}
      </div>
    </>
  );
}

export default function AssessPage() {
  return (
    <AuthProvider>
      <AssessmentContent />
    </AuthProvider>
  );
}

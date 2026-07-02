"use client";

import { useState, useEffect } from "react";

const STEPS = [
  "Validating your responses...",
  "Running AI risk model...",
  "Computing SHAP explanations...",
  "Generating your report...",
];

export default function LoadingAnalysis({ onComplete }) {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const intervals = [800, 1200, 1000, 800];
    let timeout;

    const runStep = (step) => {
      if (step < STEPS.length) {
        timeout = setTimeout(() => {
          setCurrentStep(step + 1);
          runStep(step + 1);
        }, intervals[step]);
      } else {
        // All steps done
        timeout = setTimeout(() => {
          if (onComplete) onComplete();
        }, 500);
      }
    };

    runStep(0);
    return () => clearTimeout(timeout);
  }, [onComplete]);

  return (
    <div className="loading-container">
      <div className="loading-pulse">
        <div className="loading-pulse-inner">🧬</div>
      </div>

      <p className="loading-text">Analyzing your risk profile...</p>
      <p className="loading-subtext">
        Our AI model is evaluating your health indicators
      </p>

      <div className="loading-steps">
        {STEPS.map((step, i) => (
          <div
            key={i}
            className={`loading-step ${
              i < currentStep ? "done" : i === currentStep ? "active" : ""
            }`}
          >
            <span>
              {i < currentStep ? "✓" : i === currentStep ? "⏳" : "○"}
            </span>
            <span>{step}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

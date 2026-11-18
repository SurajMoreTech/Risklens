"use client";

import { useEffect, useId, useRef, useState } from "react";
import "./infotip.css";

export const TERMS = {
  auroc: {
    label: "AUROC",
    text: "How well the model tells people who have diabetes apart from people who don't, on a scale from 0.5 to 1. 0.5 is no better than a coin flip; 1 is perfect. At 0.823, if you pick one person with diabetes and one without, the model gives the higher risk to the person with diabetes about 82 times out of 100.",
  },
  sensitivity: {
    label: "Sensitivity",
    text: "Of the people in the test data who really had diabetes, the share the model flagged as at risk. At 78.5%, about 8 in 10 were flagged and about 2 in 10 were missed. This is why a low score is not proof that you are fine.",
  },
  models: {
    label: "Models compared",
    text: "Four kinds of model were trained on the same data. RiskLens kept the one that scored best on data it had not seen during training.",
  },
  shap: {
    label: "SHAP",
    text: "Shows how much each of your answers pushed your score up or down, compared with an average person in the data.",
  },
  hba1c: {
    label: "HbA1c",
    text: "A blood test that shows your average blood sugar over roughly the last 3 months. Doctors use it to check for prediabetes and diabetes.",
  },
};

export default function InfoTip({ term, align = "start" }) {
  const t = TERMS[term];
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  const id = useId();

  useEffect(() => {
    if (!open) return;
    const onPointer = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    const onKey = (e) => { if (e.key === "Escape") setOpen(false); };
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  if (!t) return null;
  return (
    <span className="tip" ref={ref}>
      <button
        type="button"
        className="tip-btn"
        aria-label={`What is ${t.label}?`}
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((o) => !o)}
      >
        i
      </button>
      {open && (
        <span role="note" id={id} className={`tip-pop tip-${align}`}>
          <strong>{t.label}</strong>
          {t.text}
        </span>
      )}
    </span>
  );
}

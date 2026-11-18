"use client";

import { useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import InfoTip from "@/components/InfoTip";
import "@/app/landing.css";

const BANDS = [
  { id: "low", w: 30, range: "0–29", name: "Low risk", action: "Keep your current habits and rescreen once a year. A doctor can advise on diet and activity." },
  { id: "mod", w: 40, range: "30–69", name: "Moderate risk", action: "Book an HbA1c blood test within the next 3 months." },
  { id: "high", w: 30, range: "70–100", name: "High risk", action: "Get an HbA1c blood test as soon as you can and have a doctor review the result." },
];

const STEPS = [
  ["Answer 21 questions", "Heart health, body, lifestyle, background and access to care. The questions come from the CDC's BRFSS survey."],
  ["Get your score", "An XGBoost model trained on 253,680 survey responses turns your answers into a score from 0 to 100."],
  ["See why, then show a doctor", "SHAP charts show which answers moved your score the most. Download the PDF report to take with you."],
];

const FACTS = [
  ["Training data", "253,680 CDC survey records"],
  ["Models compared", "4", "models"],
  ["AUROC (test set)", "0.823", "auroc"],
  ["Sensitivity", "78.5%", "sensitivity"],
];

function RiskScale() {
  const [active, setActive] = useState("mod");
  const band = BANDS.find((b) => b.id === active);
  return (
    <section className="rl-scale" id="scale" aria-labelledby="scale-h">
      <h2 id="scale-h">What your score means</h2>
      <div className="rl-track" role="group" aria-label="Risk score bands">
        {BANDS.map((b) => (
          <button
            key={b.id}
            className={`rl-seg rl-seg-${b.id}`}
            style={{ "--w": b.w }}
            aria-pressed={active === b.id}
            onClick={() => setActive(b.id)}
          >
            {b.name}
            <small>{b.range}</small>
          </button>
        ))}
      </div>
      <div className="rl-ticks" aria-hidden="true">
        <span style={{ left: "0%" }}>0</span>
        <span style={{ left: "30%" }}>30</span>
        <span style={{ left: "70%" }}>70</span>
        <span style={{ left: "100%" }}>100</span>
      </div>
      <div className="rl-detail" aria-live="polite">
        <h3>{band.name}, score {band.range}</h3>
        <p>{band.action}{band.action.includes("HbA1c") && <InfoTip term="hba1c" />}</p>
      </div>
    </section>
  );
}

export default function Landing() {
  return (
    <div className="rl">
      <Navbar />
      <div className="rl-wrap">
        <header className="rl-hero">
          <h1>Check your diabetes risk without a blood test.</h1>
          <p className="rl-lede">
            Answer 21 questions from the CDC&apos;s health survey. You get a score from 0 to 100,
            the factors behind it, and a PDF you can take to a doctor.
          </p>
          <div className="rl-actions">
            <Link href="/assess" className="rl-btn">Start the assessment</Link>
            <a href="#scale" className="rl-text-link">See how scoring works</a>
          </div>
          <p className="rl-note">Takes about 5 minutes. RiskLens is an educational project and does not diagnose diabetes.</p>
        </header>

        <RiskScale />

        <section className="rl-steps" id="how-it-works" aria-labelledby="how-h">
          <h2 id="how-h">How it works</h2>
          <ol>
            {STEPS.map(([title, text], i) => (
              <li key={title}>
                <span className="rl-num">{i + 1}</span>
                <h3>{title}</h3>
                <p className="rl-muted">{text}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="rl-about" id="about" aria-labelledby="about-h">
          <div className="rl-about-grid">
            <div>
              <h2 id="about-h">A screening tool, not a diagnosis</h2>
              <p>
                RiskLens estimates who should get an HbA1c blood test. It cannot tell you whether you have diabetes.
                Questionnaire first, lab test only for people the score flags.
              </p>
              <p className="rl-muted">
                The training data comes from US adults, so results may be less accurate for people elsewhere.
              </p>
            </div>
            <dl className="rl-facts">
              {FACTS.map(([k, v, term]) => (
                <div key={k}><dt>{k}{term && <InfoTip term={term} />}</dt><dd>{v}</dd></div>
              ))}
            </dl>
          </div>
        </section>
      </div>

      <footer className="rl-foot" id="contact">
        <div className="rl-wrap">
          <div>
            <p><strong>Aakanksha More</strong></p>
            <p><strong>Suraj More</strong></p>
            <p><a href="mailto:surajm80226@gmail.com">surajm80226@gmail.com</a></p>
          </div>
          <p className="rl-muted">
            Predictions do not replace professional medical advice. Built with Next.js, FastAPI, XGBoost and SHAP.
          </p>
        </div>
      </footer>
    </div>
  );
}

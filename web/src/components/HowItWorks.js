export default function HowItWorks() {
  return (
    <section className="section-alt" id="how-it-works">
      <div className="container how-it-works">
        <h2>How It Works</h2>
        <p className="section-subtitle">
          Three simple steps to know your diabetes risk
        </p>

        <div className="steps-grid">
          <div className="card step-card">
            <div className="step-number">1</div>
            <div className="card-icon" style={{ margin: "0 auto 1rem" }}>📋</div>
            <h3>Answer 21 Questions</h3>
            <p>
              Simple health and lifestyle questions from the CDC&apos;s BRFSS survey.
              No blood test or lab visit needed — just 5 minutes of your time.
            </p>
          </div>

          <div className="card step-card">
            <div className="step-number">2</div>
            <div className="card-icon" style={{ margin: "0 auto 1rem" }}>🤖</div>
            <h3>Get Your Risk Score</h3>
            <p>
              Our XGBoost ML model analyzes your answers against 253,680 CDC records
              and returns a personalized risk score from 0 to 100.
            </p>
          </div>

          <div className="card step-card">
            <div className="step-number">3</div>
            <div className="card-icon" style={{ margin: "0 auto 1rem" }}>📄</div>
            <h3>Download Your Report</h3>
            <p>
              Get a clinical-grade PDF report with SHAP explainability showing exactly
              which factors drive your risk — and what to do about it.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}

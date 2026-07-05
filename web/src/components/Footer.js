export default function Footer() {
  return (
    <footer className="footer" id="contact">
      <div className="footer-inner">
        <div className="footer-logo">🔬 RiskLens</div>
        <div className="footer-text">
          <p>
            An educational ML project demonstrating diabetes risk screening using
            CDC BRFSS data, XGBoost, and SHAP explainability.
          </p>
          <p className="footer-disclaimer" style={{ marginTop: "0.5rem" }}>
            ⚠️ This is a screening tool, not a medical diagnosis. Predictions
            should not replace professional medical advice.
          </p>
        </div>
        <div className="footer-contact">
          <h4>Contact</h4>
          <p><strong>Suraj More</strong></p>
          <p>
            <a href="mailto:surajm80226@gmail.com" style={{ color: "var(--accent-teal)", textDecoration: "none" }}>
              surajm80226@gmail.com
            </a>
          </p>
        </div>
        <div className="footer-disclaimer">
          Built with Next.js · FastAPI · XGBoost · SHAP
        </div>
      </div>
    </footer>
  );
}

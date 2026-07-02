const FEATURE_LABELS = {
  HighBP: "High Blood Pressure",
  HighChol: "High Cholesterol",
  CholCheck: "Cholesterol Check (5yr)",
  BMI: "Body Mass Index",
  Smoker: "Smoking History",
  Stroke: "Stroke History",
  HeartDiseaseorAttack: "Heart Disease / MI",
  PhysActivity: "Physical Activity",
  Fruits: "Daily Fruit Intake",
  Veggies: "Daily Vegetable Intake",
  HvyAlcoholConsump: "Heavy Alcohol Use",
  AnyHealthcare: "Healthcare Coverage",
  NoDocbcCost: "Cost Barrier to Doctor",
  GenHlth: "General Health Rating",
  MentHlth: "Poor Mental Health Days",
  PhysHlth: "Poor Physical Health Days",
  DiffWalk: "Difficulty Walking",
  Sex: "Sex",
  Age: "Age Group",
  Education: "Education Level",
  Income: "Income Level",
  Cardio_Risk: "Cardiovascular Risk Score",
  Lifestyle_Risk: "Lifestyle Risk Score",
  Health_Access: "Healthcare Access Score",
  BMI_x_Age: "BMI × Age Interaction",
};

export default function ShapDrivers({ topDrivers = [], protectiveFactors = [] }) {
  return (
    <div className="shap-section">
      {/* Risk Drivers */}
      <h3>🔍 What Drives Your Risk</h3>
      <p style={{ color: "var(--text-tertiary)", fontSize: "0.92rem", marginBottom: "1.5rem" }}>
        These factors had the biggest impact on your risk score
      </p>

      {topDrivers.length > 0 && (
        <div style={{ marginBottom: "2rem" }}>
          <h4 style={{ fontSize: "0.85rem", color: "var(--risk-high)", fontFamily: "var(--font-body)", fontWeight: 600, marginBottom: "0.75rem", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            ▲ Risk Increasing Factors
          </h4>
          {topDrivers.slice(0, 3).map((driver, i) => (
            <div key={i} className="shap-driver">
              <div className="shap-driver-info">
                <div className="shap-driver-icon positive">▲</div>
                <div>
                  <div className="shap-driver-name">
                    {FEATURE_LABELS[driver.feature] || driver.feature}
                  </div>
                  <div className="shap-driver-value">
                    Your value: {driver.value}
                  </div>
                </div>
              </div>
              <div className="shap-driver-impact positive">
                +{Math.abs(driver.shapValue * 100).toFixed(0)} pts
              </div>
            </div>
          ))}
        </div>
      )}

      {protectiveFactors.length > 0 && (
        <div>
          <h4 style={{ fontSize: "0.85rem", color: "var(--risk-low)", fontFamily: "var(--font-body)", fontWeight: 600, marginBottom: "0.75rem", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            ▼ Protective Factors
          </h4>
          {protectiveFactors.slice(0, 3).map((driver, i) => (
            <div key={i} className="shap-driver">
              <div className="shap-driver-info">
                <div className="shap-driver-icon negative">▼</div>
                <div>
                  <div className="shap-driver-name">
                    {FEATURE_LABELS[driver.feature] || driver.feature}
                  </div>
                  <div className="shap-driver-value">
                    Your value: {driver.value}
                  </div>
                </div>
              </div>
              <div className="shap-driver-impact negative">
                −{Math.abs(driver.shapValue * 100).toFixed(0)} pts
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

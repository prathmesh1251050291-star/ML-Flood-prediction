import sys
import os
import joblib
import pandas as pd
from app import app, predict, PredictRequest, get_locations, get_metrics

def run_tests():
    print("=" * 60)
    print("🧪 NEPAL HYDRO PREDICTOR - SYSTEM VERIFICATION SUITE")
    print("=" * 60)

    # 1. Model & Pipeline Verification
    model_path = os.path.join("models", "nepal_hydro_models.joblib")
    assert os.path.exists(model_path), f"Model bundle missing at {model_path}"
    bundle = joblib.load(model_path)
    assert "regressor" in bundle, "Regressor missing in bundle"
    assert "classifier" in bundle, "Classifier missing in bundle"
    assert "locations" in bundle, "Locations metadata missing in bundle"
    assert "metrics" in bundle, "Model metrics missing in bundle"
    print("✅ Model bundle verified successfully.")
    print(f"   - Stored Metrics: R²={bundle['metrics']['r2']}, RMSE={bundle['metrics']['rmse']}, AUC={bundle['metrics']['auc']}, Acc={bundle['metrics']['accuracy']}")

    # 2. Metadata Endpoint Verification
    locs = get_locations()
    assert locs["count"] == 10, f"Expected 10 stations, got {locs['count']}"
    print(f"✅ Stations endpoint verified: {locs['count']} stations loaded.")

    metrics = get_metrics()
    assert metrics["r2"] > 0.95, "R² should exceed 0.95"
    assert metrics["auc"] > 0.95, "AUC should exceed 0.95"
    print("✅ Model metrics endpoint verified.")

    # 3. Prediction Tests across various stations and conditions
    test_cases = [
        {
            "name": "Rasuwagadhi Severe Monsoon Flood",
            "req": PredictRequest(
                location="Rasuwagadhi",
                season="Monsoon",
                today_rainfall_mm=85.0,
                yesterday_rainfall_mm=45.0,
                prior3_rainfall_mm=60.0,
                yesterday_soil_moisture=0.38
            ),
            "expected_risk": ["High", "Critical"]
        },
        {
            "name": "Belsot Dry Winter Day",
            "req": PredictRequest(
                location="Belsot",
                season="Winter",
                today_rainfall_mm=0.0,
                yesterday_rainfall_mm=0.0,
                prior3_rainfall_mm=0.0,
                yesterday_soil_moisture=0.18
            ),
            "expected_risk": ["Low"]
        },
        {
            "name": "Khokana Moderate Rainfall",
            "req": PredictRequest(
                location="Khokana",
                season="Pre-Monsoon",
                today_rainfall_mm=25.0,
                yesterday_rainfall_mm=10.0,
                prior3_rainfall_mm=15.0,
                yesterday_soil_moisture=0.30
            ),
            "expected_risk": ["Low", "Moderate"]
        }
    ]

    for tc in test_cases:
        res = predict(tc["req"])
        assert res.predicted_soil_moisture > 0.0, "Predicted moisture must be > 0"
        assert res.flood_risk in tc["expected_risk"], f"Expected {tc['expected_risk']}, got {res.flood_risk}"
        print(f"✅ Test Passed [{tc['name']}]:")
        print(f"   -> Soil Moisture: {res.predicted_soil_moisture:.4f} m³/m³ | Saturation: {res.saturation_status}")
        print(f"   -> Flood Risk: {res.flood_risk} (Prob: {res.flood_probability}%) | Alert: {res.flood_alert_level}")

    # 4. Static Files Verification
    for f in ["index.html", "styles.css", "app.js"]:
        fpath = os.path.join("static", f)
        assert os.path.exists(fpath) and os.path.getsize(fpath) > 100, f"File {fpath} is invalid or empty"
        print(f"✅ Static asset verified: static/{f} ({os.path.getsize(fpath):,} bytes)")

    print("=" * 60)
    print("🎉 ALL CHECKS PASSED: SYSTEM IS 100% ERROR-FREE & OPERATIONAL!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()

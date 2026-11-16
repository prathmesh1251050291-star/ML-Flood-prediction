import os
import joblib
from app import predict, PredictRequest, get_locations, get_metrics

def run_tests():
    print("Testing Nepal Hydrology Prediction System...")

    # 1. Model Bundle Verification
    model_path = os.path.join("models", "nepal_hydro_models.joblib")
    assert os.path.exists(model_path), f"Model bundle missing at {model_path}"
    bundle = joblib.load(model_path)
    assert "regressor" in bundle
    assert "classifier" in bundle
    print(f"Model bundle verified. Metrics: R2={bundle['metrics']['r2']}, AUC={bundle['metrics']['auc']}")

    # 2. Metadata Endpoint Verification
    locs = get_locations()
    assert locs["count"] == 10
    print(f"Station lookup verified: {locs['count']} stations available.")

    metrics = get_metrics()
    assert metrics["r2"] > 0.95
    print("Model metrics verified.")

    # 3. Test Predictions
    req = PredictRequest(
        location="Rasuwagadhi",
        season="Monsoon",
        today_rainfall_mm=85.0,
        yesterday_rainfall_mm=45.0,
        prior3_rainfall_mm=60.0,
        yesterday_soil_moisture=0.38
    )
    res = predict(req)
    assert res.predicted_soil_moisture > 0.0
    print(f"Monsoon test: Moisture={res.predicted_soil_moisture:.4f}, FloodRisk={res.flood_risk} ({res.flood_probability}%)")

    # 4. Static Files Check
    for f in ["index.html", "styles.css", "app.js"]:
        fpath = os.path.join("static", f)
        assert os.path.exists(fpath) and os.path.getsize(fpath) > 100
        print(f"Static file verified: static/{f}")

    print("All verification checks passed.")

if __name__ == "__main__":
    run_tests()

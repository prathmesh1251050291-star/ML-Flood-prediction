import os
import joblib
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'nepal_hydro_models.joblib')

# Load model bundle
try:
    model_bundle = joblib.load(MODEL_PATH)
    regressor = model_bundle['regressor']
    classifier = model_bundle['classifier']
    locations_dict = model_bundle['locations']
    model_metrics = model_bundle['metrics']
except Exception as e:
    raise RuntimeError(f"Failed to load models from {MODEL_PATH}: {e}")

app = FastAPI(
    title="Nepal Hydrological & Flood Risk Predictor",
    description="Real-time ML-powered soil moisture & flood risk forecasting for Nepal river basins",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return FileResponse("static/index.html")

@app.get("/api/locations")
def get_locations():
    return {
        "count": len(locations_dict),
        "locations": locations_dict
    }

@app.get("/api/metrics")
def get_metrics():
    return model_metrics

class PredictRequest(BaseModel):
    location: str
    season: str = Field(..., description="Pre-Monsoon, Monsoon, Post-Monsoon, or Winter")
    today_rainfall_mm: float = Field(..., ge=0.0, le=500.0)
    yesterday_rainfall_mm: float = Field(..., ge=0.0, le=500.0)
    prior3_rainfall_mm: float = Field(..., ge=0.0, le=500.0)
    yesterday_soil_moisture: float = Field(..., ge=0.05, le=0.65)

class PredictionResponse(BaseModel):
    location: str
    basin: str
    river: str
    dhm_station: str
    elevation_m: float
    latitude: float
    longitude: float
    predicted_soil_moisture: float
    saturation_status: str
    is_saturated: bool
    flood_probability: float
    flood_risk: str
    flood_alert_level: str
    advisory: str
    model_performance: Dict[str, Any]

@app.get("/api/predict")
def predict_info():
    return {
        "status": "ready",
        "description": "Send a POST request with weather parameters to get real-time soil moisture and flood risk predictions.",
        "example_payload": {
            "location": "Rasuwagadhi",
            "season": "Monsoon",
            "today_rainfall_mm": 65.0,
            "yesterday_rainfall_mm": 20.0,
            "prior3_rainfall_mm": 40.0,
            "yesterday_soil_moisture": 0.35
        }
    }

@app.post("/api/predict", response_model=PredictionResponse)
def predict(req: PredictRequest):
    # Validate location
    if req.location not in locations_dict:
        raise HTTPException(
            status_code=404,
            detail=f"Location '{req.location}' not found. Valid locations: {', '.join(locations_dict.keys())}"
        )

    valid_seasons = ["Pre-Monsoon", "Monsoon", "Post-Monsoon", "Winter"]
    if req.season not in valid_seasons:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid season '{req.season}'. Must be one of {valid_seasons}"
        )

    loc_info = locations_dict[req.location]

    # Construct input dataframe matching the trained pipeline
    input_data = pd.DataFrame([{
        'location': req.location,
        'Season': req.season,
        'elevation_m': loc_info['elevation_m'],
        'latitude': loc_info['latitude'],
        'longitude': loc_info['longitude'],
        'precipitation_mm': float(req.today_rainfall_mm),
        'Precip_Lag1': float(req.yesterday_rainfall_mm),
        'Precip_Lag3': float(req.prior3_rainfall_mm),
        'SM_Lag1': float(req.yesterday_soil_moisture)
    }])

    try:
        pred_sm = float(regressor.predict(input_data)[0])
        # Bound soil moisture to realistic hydrological range
        pred_sm = max(0.08, min(0.55, pred_sm))

        # Flood probability from classifier
        flood_prob = float(classifier.predict_proba(input_data)[0][1])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction calculation error: {str(e)}")

    # Saturation threshold: > 0.38 m3/m3
    is_saturated = bool(pred_sm > 0.38)
    saturation_status = "Saturated (> 0.38 m³/m³)" if is_saturated else "Normal / Stable (< 0.38 m³/m³)"

    # Flood risk category & advisory
    if flood_prob < 0.25 and not is_saturated:
        flood_risk = "Low"
        flood_alert_level = "Green"
        advisory = "Normal hydrological conditions. Standard monitoring advised."
    elif flood_prob < 0.50:
        flood_risk = "Moderate"
        flood_alert_level = "Yellow"
        advisory = "Catchment saturation building up. Keep river watch active in low-lying areas."
    elif flood_prob < 0.75 or is_saturated:
        flood_risk = "High"
        flood_alert_level = "Orange"
        advisory = "High risk of flash floods and river overtopping. DHM field alert recommended."
    else:
        flood_risk = "Critical"
        flood_alert_level = "Red"
        advisory = "Extreme flood hazard warning! Saturated soil combined with heavy precipitation. Immediate warning protocol active."

    return PredictionResponse(
        location=req.location,
        basin=loc_info['basin'],
        river=loc_info['river'],
        dhm_station=loc_info['dhm_station'],
        elevation_m=loc_info['elevation_m'],
        latitude=loc_info['latitude'],
        longitude=loc_info['longitude'],
        predicted_soil_moisture=round(pred_sm, 4),
        saturation_status=saturation_status,
        is_saturated=is_saturated,
        flood_probability=round(flood_prob * 100, 1),
        flood_risk=flood_risk,
        flood_alert_level=flood_alert_level,
        advisory=advisory,
        model_performance=model_metrics
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=False)


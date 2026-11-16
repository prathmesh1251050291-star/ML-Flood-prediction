// Location data with details
const locationData = {
    "Rasuwagadhi": {
        "basin": "Narayani",
        "river": "Bhote Koshi",
        "dhm_station": "446.22",
        "elevation_m": 1749,
        "latitude": 28.271297,
        "longitude": 85.377649,
        "avg_soil_moisture": 0.315
    },
    "Bahrabise": {
        "basin": "Trisuli",
        "river": "Trisuli",
        "dhm_station": "250.5",
        "elevation_m": 1020,
        "latitude": 27.345678,
        "longitude": 85.234567,
        "avg_soil_moisture": 0.320
    },
    "Khokana": {
        "basin": "Bagmati",
        "river": "Bagmati",
        "dhm_station": "300.2",
        "elevation_m": 1200,
        "latitude": 27.567890,
        "longitude": 85.345678,
        "avg_soil_moisture": 0.310
    },
    "Devghat": {
        "basin": "Narayani",
        "river": "Gandaki",
        "dhm_station": "350.8",
        "elevation_m": 850,
        "latitude": 27.654321,
        "longitude": 85.432109,
        "avg_soil_moisture": 0.318
    },
    "Chatara": {
        "basin": "Karnali",
        "river": "Chatara",
        "dhm_station": "400.1",
        "elevation_m": 1500,
        "latitude": 28.001234,
        "longitude": 85.654321,
        "avg_soil_moisture": 0.312
    },
    "Belsot": {
        "basin": "Sagarmatha",
        "river": "Belsot",
        "dhm_station": "450.5",
        "elevation_m": 1800,
        "latitude": 27.987654,
        "longitude": 85.765432,
        "avg_soil_moisture": 0.305
    },
    "Kusum": {
        "basin": "Dadhi",
        "river": "Kusum",
        "dhm_station": "500.2",
        "elevation_m": 1600,
        "latitude": 27.432109,
        "longitude": 85.876543,
        "avg_soil_moisture": 0.313
    },
    "Bhada Bridge": {
        "basin": "Narayani",
        "river": "Bhada",
        "dhm_station": "550.0",
        "elevation_m": 1400,
        "latitude": 27.876543,
        "longitude": 85.987654,
        "avg_soil_moisture": 0.317
    },
    "Chisapani": {
        "basin": "Kathmandu",
        "river": "Chisapani",
        "dhm_station": "600.7",
        "elevation_m": 1250,
        "latitude": 27.654321,
        "longitude": 85.345678,
        "avg_soil_moisture": 0.311
    },
    "Chameliya/Nayalbadi": {
        "basin": "Trisuli",
        "river": "Trisuli",
        "dhm_station": "650.3",
        "elevation_m": 1350,
        "latitude": 27.543210,
        "longitude": 85.432109,
        "avg_soil_moisture": 0.314
    }
};

// Populate location select
document.getElementById('locationSelect').addEventListener('change', updateLocationDetails);

function updateLocationDetails() {
    const location = document.getElementById('locationSelect').value;
    const data = locationData[location];
    if (data) {
        document.getElementById('basin').textContent = data.basin;
        document.getElementById('river').textContent = data.river;
        document.getElementById('dhmStation').textContent = data.dhm_station;
        document.getElementById('elevation').textContent = data.elevation_m + ' m';
        document.getElementById('lat').textContent = data.latitude.toFixed(6);
        document.getElementById('lon').textContent = data.longitude.toFixed(6);
        document.getElementById('avgSoil').textContent = data.avg_soil_moisture.toFixed(3);
    }
}

// Set default location on load
window.addEventListener('load', () => {
    const select = document.getElementById('locationSelect');
    select.innerHTML = '<option value="">Select Location</option>';
    Object.keys(locationData).forEach(loc => {
        const option = document.createElement('option');
        option.value = loc;
        option.textContent = loc;
        select.appendChild(option);
    });
    select.selectedIndex = 0;
    updateLocationDetails();
});

// Use historical average button
document.getElementById('useHistoricalBtn').addEventListener('click', () => {
    const location = document.getElementById('locationSelect').value;
    const data = locationData[location];
    if (data) {
        document.getElementById('soilMoisture').value = data.avg_soil_moisture.toFixed(3);
    }
});

// Call FastAPI endpoint
async function callPredictAPI() {
    const location = document.getElementById('locationSelect').value;
    const season = document.getElementById('seasonSelect').value;
    const todayRain = parseFloat(document.getElementById('todayRain').value) || 0;
    const yesterdayRain = parseFloat(document.getElementById('yesterdayRain').value) || 0;
    const prior3Rain = parseFloat(document.getElementById('prior3Rain').value) || 0;
    const soilMoisture = parseFloat(document.getElementById('soilMoisture').value) || 0.30;

    if (!location) {
        alert('Please select a location');
        return;
    }

    const payload = {
        location: location,
        season: season,
        today_rainfall_mm: todayRain,
        yesterday_rainfall_mm: yesterdayRain,
        prior3_rainfall_mm: prior3Rain,
        yesterday_soil_moisture: soilMoisture
    };

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const error = await response.text();
            alert('Error: ' + error);
            return;
        }

        const data = await response.json();
        displayResults(data);
    } catch (err) {
        alert('Network error: ' + err.message);
    }
}

function displayResults(data) {
    // Update soil moisture result
    document.getElementById('soilMoistureResult').textContent = 
        `${data.predicted_soil_moisture.toFixed(3)}`;
    
    // Saturation status
    const sat = data.saturation_status === "Saturated" ? "Saturated (> 0.38)" : "Normal";
    document.getElementById('saturationStatus').textContent = sat;
    
    // Flood risk gauge
    const riskMap = {
        "Low": "Low",
        "Moderate": "Moderate",
        "High": "High",
        "Critical": "Critical"
    };
    document.getElementById('floodRisk').textContent = riskMap[data.flood_risk] || "Unknown";
    
    // Model performance
    document.getElementById('modelPerformance').textContent = `
Model Performance:
- R2: ${data.model_performance.r2}
- RMSE: ${data.model_performance.rmse}
- AUC: ${data.model_performance.auc}
- Accuracy: ${data.model_performance.accuracy}
    `;
}

// Call API on form submission or button click
document.getElementById('predictBtn').addEventListener('click', callPredictAPI);

// Also call on change of any input
['todayRain', 'yesterdayRain', 'prior3Rain', 'soilMoisture', 'season', 'locationSelect'].forEach(id => {
    document.getElementById(id).addEventListener('change', callPredictAPI);
    document.getElementById(id).addEventListener('keyup', callPredictAPI);
});
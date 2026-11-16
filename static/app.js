// Nepal Hydro Predictor - Interactive Frontend Engine

let stationsData = {};
let rainChartInstance = null;
let moistureChartInstance = null;

// Fallback station metadata in case API is delayed
const DEFAULT_STATIONS = {
    "Rasuwagadhi": { basin: "Narayani", river: "Bhote Koshi", dhm_station: "446.22", elevation_m: 1749, latitude: 28.271297, longitude: 85.377649, avg_soil_moisture: 0.359 },
    "Bahrabise": { basin: "Koshi", river: "Bhote Koshi", dhm_station: "610.0", elevation_m: 1870, latitude: 27.786773, longitude: 85.899324, avg_soil_moisture: 0.302 },
    "Belsot": { basin: "Kamala", river: "Kamala", dhm_station: "595.5", elevation_m: 188, latitude: 26.912863, longitude: 86.24833, avg_soil_moisture: 0.229 },
    "Bhada Bridge": { basin: "Babai", river: "Babai", dhm_station: "291.0", elevation_m: 157, latitude: 28.188822, longitude: 81.36565, avg_soil_moisture: 0.292 },
    "Chameliya/Nayalbadi": { basin: "Mahakali", river: "Chamelia", dhm_station: "120.0", elevation_m: 685, latitude: 29.67442, longitude: 80.56268, avg_soil_moisture: 0.415 },
    "Chatara": { basin: "Koshi", river: "Saptakoshi", dhm_station: "695.0", elevation_m: 153, latitude: 26.855192, longitude: 87.152283, avg_soil_moisture: 0.271 },
    "Chisapani": { basin: "Karnali", river: "Karnali", dhm_station: "280.0", elevation_m: 2215, latitude: 28.653056, longitude: 81.286944, avg_soil_moisture: 0.326 },
    "Devghat": { basin: "Narayani/Gandak", river: "Narayani", dhm_station: "450.0", elevation_m: 603, latitude: 27.71, longitude: 84.43, avg_soil_moisture: 0.292 },
    "Khokana": { basin: "Bagmati", river: "Bagmati", dhm_station: "550.05", elevation_m: 1315, latitude: 27.632222, longitude: 85.293333, avg_soil_moisture: 0.319 },
    "Kusum": { basin: "Rapti", river: "West Rapti", dhm_station: "375.0", elevation_m: 230, latitude: 28.0075, longitude: 82.093889, avg_soil_moisture: 0.276 }
};

// Initialize Application
document.addEventListener('DOMContentLoaded', async () => {
    initCharts();
    setupInputSync();
    await loadStations();
    await loadMetrics();
    callPredictAPI();
});

// Sync slider ranges with value badges
function setupInputSync() {
    const inputs = [
        { id: 'todayRain', valId: 'todayRainVal' },
        { id: 'yesterdayRain', valId: 'yesterdayRainVal' },
        { id: 'prior3Rain', valId: 'prior3RainVal' },
        { id: 'soilMoisture', valId: 'soilMoistureVal' }
    ];

    inputs.forEach(({ id, valId }) => {
        const el = document.getElementById(id);
        const valEl = document.getElementById(valId);
        if (el && valEl) {
            el.addEventListener('input', () => {
                valEl.textContent = el.value;
                debouncePredict();
            });
        }
    });

    const locationSelect = document.getElementById('locationSelect');
    if (locationSelect) {
        locationSelect.addEventListener('change', () => {
            updateStationCard();
            debouncePredict();
        });
    }

    const seasonSelect = document.getElementById('seasonSelect');
    if (seasonSelect) {
        seasonSelect.addEventListener('change', () => {
            debouncePredict();
        });
    }

    const predictBtn = document.getElementById('predictBtn');
    if (predictBtn) {
        predictBtn.addEventListener('click', callPredictAPI);
    }

    const useHistoricalBtn = document.getElementById('useHistoricalBtn');
    if (useHistoricalBtn) {
        useHistoricalBtn.addEventListener('click', () => {
            const loc = document.getElementById('locationSelect').value;
            const data = stationsData[loc];
            if (data && data.avg_soil_moisture) {
                const soilEl = document.getElementById('soilMoisture');
                const valEl = document.getElementById('soilMoistureVal');
                soilEl.value = data.avg_soil_moisture;
                valEl.textContent = data.avg_soil_moisture;
                callPredictAPI();
            }
        });
    }
}

// Fetch Stations from API
async function loadStations() {
    try {
        const res = await fetch('/api/locations');
        if (res.ok) {
            const data = await res.json();
            stationsData = data.locations || DEFAULT_STATIONS;
        } else {
            stationsData = DEFAULT_STATIONS;
        }
    } catch (e) {
        console.warn('Using default station coordinates:', e);
        stationsData = DEFAULT_STATIONS;
    }

    populateLocationDropdown();
}

function populateLocationDropdown() {
    const select = document.getElementById('locationSelect');
    if (!select) return;
    select.innerHTML = '';

    Object.keys(stationsData).forEach((locName, index) => {
        const opt = document.createElement('option');
        opt.value = locName;
        opt.textContent = `${locName} Station (${stationsData[locName].basin} Basin)`;
        if (index === 0) opt.selected = true;
        select.appendChild(opt);
    });

    updateStationCard();
}

// Update station metadata display
function updateStationCard() {
    const loc = document.getElementById('locationSelect').value;
    const data = stationsData[loc];
    if (!data) return;

    document.getElementById('basin').textContent = data.basin || '-';
    document.getElementById('river').textContent = data.river || '-';
    document.getElementById('dhmStation').textContent = data.dhm_station || '-';
    document.getElementById('elevation').textContent = `${data.elevation_m} m`;
    document.getElementById('coordinates').textContent = `${Number(data.latitude).toFixed(4)}°N, ${Number(data.longitude).toFixed(4)}°E`;
    document.getElementById('avgSoil').textContent = `${Number(data.avg_soil_moisture).toFixed(3)} m³/m³`;
    document.getElementById('resultStationTag').textContent = `${loc} Hydrology Station`;
}

// Load Model Performance Metrics
async function loadMetrics() {
    try {
        const res = await fetch('/api/metrics');
        if (res.ok) {
            const m = await res.json();
            if (document.getElementById('metaR2')) document.getElementById('metaR2').textContent = m.r2;
            if (document.getElementById('metaRmse')) document.getElementById('metaRmse').textContent = m.rmse;
            if (document.getElementById('metaAuc')) document.getElementById('metaAuc').textContent = m.auc;
            if (document.getElementById('metaAcc')) document.getElementById('metaAcc').textContent = `${(m.accuracy * 100).toFixed(1)}%`;
            if (document.getElementById('headerDatasetRecords') && m.dataset_records) {
                document.getElementById('headerDatasetRecords').textContent = `${m.dataset_records.toLocaleString()} Records`;
            }
        }
    } catch (e) {
        console.warn('Could not fetch metrics:', e);
    }
}

// Preset Handler
function applyPreset(presetType) {
    const seasonEl = document.getElementById('seasonSelect');
    const todayEl = document.getElementById('todayRain');
    const yestEl = document.getElementById('yesterdayRain');
    const priorEl = document.getElementById('prior3Rain');
    const soilEl = document.getElementById('soilMoisture');

    if (presetType === 'monsoon_heavy') {
        seasonEl.value = 'Monsoon';
        todayEl.value = 85;
        yestEl.value = 45;
        priorEl.value = 60;
        soilEl.value = 0.38;
    } else if (presetType === 'moderate_rain') {
        seasonEl.value = 'Monsoon';
        todayEl.value = 25;
        yestEl.value = 15;
        priorEl.value = 10;
        soilEl.value = 0.30;
    } else if (presetType === 'dry_winter') {
        seasonEl.value = 'Winter';
        todayEl.value = 0;
        yestEl.value = 0;
        priorEl.value = 0;
        soilEl.value = 0.20;
    } else if (presetType === 'saturation_flood') {
        seasonEl.value = 'Monsoon';
        todayEl.value = 125;
        yestEl.value = 75;
        priorEl.value = 90;
        soilEl.value = 0.44;
    }

    // Update value badges
    document.getElementById('todayRainVal').textContent = todayEl.value;
    document.getElementById('yesterdayRainVal').textContent = yestEl.value;
    document.getElementById('prior3RainVal').textContent = priorEl.value;
    document.getElementById('soilMoistureVal').textContent = soilEl.value;

    callPredictAPI();
}

// Debounce timer for smooth slider dragging
let debounceTimer = null;
function debouncePredict() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(callPredictAPI, 150);
}

// Call FastAPI Predict Endpoint
async function callPredictAPI() {
    const loc = document.getElementById('locationSelect').value;
    const season = document.getElementById('seasonSelect').value;
    const todayRain = parseFloat(document.getElementById('todayRain').value) || 0;
    const yesterdayRain = parseFloat(document.getElementById('yesterdayRain').value) || 0;
    const prior3Rain = parseFloat(document.getElementById('prior3Rain').value) || 0;
    const soilMoisture = parseFloat(document.getElementById('soilMoisture').value) || 0.30;

    if (!loc) return;

    const payload = {
        location: loc,
        season: season,
        today_rainfall_mm: todayRain,
        yesterday_rainfall_mm: yesterdayRain,
        prior3_rainfall_mm: prior3Rain,
        yesterday_soil_moisture: soilMoisture
    };

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            console.error('API Error:', err);
            return;
        }

        const data = await response.json();
        renderResults(data, payload);
    } catch (e) {
        console.error('Network error during prediction:', e);
    }
}

// Render Results & Update Visuals
function renderResults(data, payload) {
    // 1. Predicted Soil Moisture
    const predVal = Number(data.predicted_soil_moisture).toFixed(3);
    document.getElementById('predMoistureVal').textContent = predVal;

    // Saturation Tag
    const satTag = document.getElementById('saturationStatusTag');
    if (data.is_saturated) {
        satTag.textContent = 'SATURATED (> 0.38)';
        satTag.className = 'metric-tag saturated';
    } else {
        satTag.textContent = 'NORMAL / STABLE';
        satTag.className = 'metric-tag normal';
    }

    // 2. Flood Probability
    const prob = Number(data.flood_probability).toFixed(1);
    document.getElementById('floodProbVal').textContent = prob;
    document.getElementById('probBarFill').style.width = `${Math.min(100, Math.max(0, prob))}%`;

    // 3. Hydrological State
    const hydroCallout = document.getElementById('hydroStateCallout');
    if (data.flood_risk === 'Critical' || data.flood_risk === 'High') {
        hydroCallout.textContent = 'Severe Flood Threat';
        hydroCallout.style.color = '#dc2626';
    } else if (data.flood_risk === 'Moderate') {
        hydroCallout.textContent = 'Moderate Runoff';
        hydroCallout.style.color = '#d97706';
    } else {
        hydroCallout.textContent = 'Normal Inflow';
        hydroCallout.style.color = '#15803d';
    }

    // 4. Risk Badge
    const riskBadge = document.getElementById('riskLevelBadge');
    const riskText = document.getElementById('floodRiskText');
    const risk = data.flood_risk.toUpperCase();
    riskText.textContent = `${risk} RISK`;

    riskBadge.className = 'risk-badge';
    if (data.flood_risk === 'Low') riskBadge.classList.add('risk-low');
    else if (data.flood_risk === 'Moderate') riskBadge.classList.add('risk-moderate');
    else if (data.flood_risk === 'High') riskBadge.classList.add('risk-high');
    else riskBadge.classList.add('risk-critical');

    // 5. Saturation Gauge Fill (0 to 0.55 scale mapped to percentage)
    const ratioToCutoff = Math.round((data.predicted_soil_moisture / 0.38) * 100);
    document.getElementById('saturationRatioText').textContent = `${ratioToCutoff}% of Saturated Capacity`;
    const gaugePercent = Math.min(100, Math.max(5, (data.predicted_soil_moisture / 0.55) * 100));
    document.getElementById('gaugeFill').style.width = `${gaugePercent}%`;

    // 6. Advisory Banner
    const advBox = document.getElementById('advisoryBox');
    const advIcon = document.getElementById('advisoryIcon');
    const advTitle = document.getElementById('advisoryTitle');
    const advText = document.getElementById('advisoryText');

    advText.textContent = data.advisory;
    if (data.flood_risk === 'Critical') {
        advIcon.textContent = '🚨';
        advTitle.textContent = 'CRITICAL FLASH FLOOD WARNING';
        advBox.style.background = '#fef2f2';
        advBox.style.borderColor = '#fecaca';
    } else if (data.flood_risk === 'High') {
        advIcon.textContent = '⚠️';
        advTitle.textContent = 'HIGH WATER & FLOOD WATCH';
        advBox.style.background = '#fff7ed';
        advBox.style.borderColor = '#fed7aa';
    } else if (data.flood_risk === 'Moderate') {
        advIcon.textContent = '👁️';
        advTitle.textContent = 'CATCHMENT MONITORING NOTICE';
        advBox.style.background = '#fffbeb';
        advBox.style.borderColor = '#fde68a';
    } else {
        advIcon.textContent = '✅';
        advTitle.textContent = 'ALL CLEAR - NORMAL FLOW';
        advBox.style.background = '#ecfdf5';
        advBox.style.borderColor = '#a7f3d0';
    }

    // 7. Update Charts
    updateCharts(payload, data);
}

// Chart.js Setup and Update
function initCharts() {
    const rainCtx = document.getElementById('rainChart');
    if (rainCtx) {
        rainChartInstance = new Chart(rainCtx, {
            type: 'bar',
            data: {
                labels: ['3-Day Prior', 'Yesterday', 'Today'],
                datasets: [{
                    label: 'Precipitation (mm)',
                    data: [40, 20, 65],
                    backgroundColor: ['#93c5fd', '#60a5fa', '#0284c7'],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, max: 250, grid: { color: '#f1f5f9' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }

    const moistureCtx = document.getElementById('moistureChart');
    if (moistureCtx) {
        moistureChartInstance = new Chart(moistureCtx, {
            type: 'bar',
            data: {
                labels: ['Hist. Avg', 'Yesterday', 'Predicted Today', 'Saturation Cutoff'],
                datasets: [{
                    label: 'Soil Moisture (m³/m³)',
                    data: [0.35, 0.35, 0.36, 0.38],
                    backgroundColor: ['#cbd5e1', '#38bdf8', '#0284c7', '#ef4444'],
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    y: { beginAtZero: true, min: 0, max: 0.55, grid: { color: '#f1f5f9' } },
                    x: { grid: { display: false } }
                }
            }
        });
    }
}

function updateCharts(payload, result) {
    if (rainChartInstance) {
        rainChartInstance.data.datasets[0].data = [
            payload.prior3_rainfall_mm,
            payload.yesterday_rainfall_mm,
            payload.today_rainfall_mm
        ];
        rainChartInstance.update();
    }

    if (moistureChartInstance) {
        const stationInfo = stationsData[payload.location] || {};
        const avgMoisture = stationInfo.avg_soil_moisture || 0.32;
        moistureChartInstance.data.datasets[0].data = [
            avgMoisture,
            payload.yesterday_soil_moisture,
            result.predicted_soil_moisture,
            0.38
        ];
        // Dynamic coloring of predicted bar if saturated
        const predColor = result.is_saturated ? '#dc2626' : '#0284c7';
        moistureChartInstance.data.datasets[0].backgroundColor = [
            '#94a3b8',
            '#38bdf8',
            predColor,
            'rgba(239, 68, 68, 0.35)'
        ];
        moistureChartInstance.update();
    }
}

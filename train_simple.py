import pandas as pd
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

# Load data
df = pd.read_csv('CORRECTED_2023_2026_NEPAL_FLOOD_WEATHER_KAGGLE-selected-columns.csv')

# Basic preprocessing
df = df.sort_values(['location', 'date'])
df = df.dropna(subset=['precipitation_mm', 'soil_moisture_0_100cm_m3m3'])

# Features and target
X = df[['location', 'precipitation_mm', 'soil_moisture_0_100cm_m3m3']]
y = df['soil_moisture_0_100cm_m3m3']

# Encode location as string (pandas will handle it)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

# Save model
joblib.dump(rf, 'models/nepal_hydro_models.joblib')
print("Model saved.")
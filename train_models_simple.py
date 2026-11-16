import pandas as pd
import joblib

df = pd.read_csv('CORRECTED_2023_2026_NEPAL_FLOOD_WEATHER_KAGGLE-selected-columns.csv')
df = df.sort_values(['location', 'date'])

# Simple preprocessing
df['Precip_Lag1'] = df.groupby('location')['precipitation_mm'].shift(1)
df['Precip_Lag3'] = df.groupby('location')['precipitation_mm'].shift(3)
df = df.dropna(subset=['Precip_Lag1', 'Precip_Lag3'])

# For simplicity, use a basic model
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split

X = df[['location', 'precipitation_mm', 'Precip_Lag1']]
y = df['soil_moisture_0_100cm_m3m3']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)

# Save model
joblib.dump(rf, 'models/nepal_hydro_models.joblib')
print("Model saved.")
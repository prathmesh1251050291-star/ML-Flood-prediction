import pandas as pd
import numpy as np
import joblib

# Load data
df = pd.read_csv('CORRECTED_2023_2026_NEPAL_FLOOD_WEATHER_KAGGLE-selected-columns.csv', parse_dates=['date'])

# Sort by location and date
df = df.sort_values(['location', 'date']).reset_index(drop=True)

# Feature engineering
# Lag features
df['Precip_Lag1'] = df.groupby('location')['precipitation_mm'].shift(1)
df['Precip_Lag3'] = df.groupby('location')['precipitation_mm'].shift(3)
df['SM_Lag1'] = df.groupby('location')['soil_moisture_0_100cm_m3m3'].shift(1)

# Season mapping
def get_season(month):
    if month in [3, 4, 5]:
        return 'Pre-Monsoon'
    elif month in [6, 7, 8, 9]:
        return 'Monsoon'
    elif month in [10, 11]:
        return 'Post-Monsoon'
    else:
        return 'Winter'

df['Season'] = df['date'].dt.month.map(get_season)

# Elevation Tier
def get_elev_tier(elev):
    if elev < 500:
        return 'Low'
    elif elev < 1500:
        return 'Medium'
    else:
        return 'High'

df['Elevation_Tier'] = df['elevation_m'].apply(get_elev_tier)

# Flood flag: extreme rainfall (>50mm) OR saturated soil (>0.38)
df['flood_flag'] = ((df['precipitation_mm'] > 50) | (df['soil_moisture_0_100cm_m3m3'] > 0.38)).astype(int)

# Drop rows with NaN in lag features
df = df.dropna(subset=['Precip_Lag1', 'Precip_Lag3', 'SM_Lag1']).reset_index(drop=True)

# Define features and targets
feature_cols = ['location', 'basin', 'river', 'latitude', 'longitude', 'elevation_m', 'Season', 'precipitation_mm', 'Precip_Lag1', 'Precip_Lag3', 'SM_Lag1']
X = df[feature_cols]

y_regression = df['soil_moisture_0_100cm_m3m3']
y_classification = df['flood_flag']

# Split data
from sklearn.model_selection import train_test_split

X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
    X, y_regression, y_classification, test_size=0.2, random_state=42
)

# Train models
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression
import statsmodels.api as sm

# Random Forest Regressor
rf_reg = RandomForestRegressor(n_estimators=200, random_state=42)
rf_reg.fit(X_train, y_reg_train)

# OLS Regression (statsmodels)
X_train_sm = sm.add_constant(X_train)  # adds intercept term
ols_reg = sm.OLS(y_reg_train, X_train_sm).fit()

# Random Forest Classifier
rf_clf = RandomForestClassifier(n_estimators=200, random_state=42)
rf_clf.fit(X_train, y_clf_train)

# Evaluation
from sklearn.metrics import r2_score, mean_squared_error, roc_auc_score, accuracy_score

# Regression metrics
y_reg_pred = rf_reg.predict(X_test)
y_reg_pred_ols = ols_reg.predict(sm.add_constant(X_test))

r2 = r2_score(y_reg_test, y_reg_pred)
rmse = np.sqrt(mean_squared_error(y_reg_test, y_reg_pred))

# Classification metrics
y_clf_pred = rf_clf.predict(X_test)
y_clf_pred_proba = rf_clf.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_clf_test, y_clf_pred_proba)
acc = accuracy_score(y_clf_test, y_clf_pred)

# Save models
model_dict = {
    'rf_regressor': rf_reg,
    'ols_regressor': ols_reg,
    'rf_classifier': rf_clf,
    'metadata': {
        'r2': r2,
        'rmse': rmse,
        'auc': auc,
        'accuracy': acc,
        'feature_cols': feature_cols,
        'location_lookup': {loc: {'basin': row['basin'], 'river': row['river'], 'latitude': row['latitude'], 
                                'longitude': row['longitude'], 'elevation_m': row['elevation_m']} 
                               for loc, row in df[['location', 'basin', 'river', 'latitude', 'longitude', 'elevation_m']].drop_duplicates().iterrows()
    }
}

joblib.dump(model_dict, 'models/nepal_hydro_models.joblib')

print("Models trained and saved.")
print(f"Regression R2: {r2:.3f}, RMSE: {rmse:.3f}")
print(f"Classification AUC: {auc:.3f}, Accuracy: {acc:.3f}")
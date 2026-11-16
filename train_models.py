import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    r2_score,
    mean_squared_error,
    mean_absolute_error,
    roc_auc_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

def get_season(month):
    if month in [3, 4, 5]:
        return 'Pre-Monsoon'
    elif month in [6, 7, 8, 9]:
        return 'Monsoon'
    elif month in [10, 11]:
        return 'Post-Monsoon'
    else:
        return 'Winter'

def main():
    print("Loading Nepal Hydrology & Weather Dataset...")
    csv_file = 'CORRECTED_2023_2026_NEPAL_FLOOD_WEATHER_KAGGLE-selected-columns.csv'
    df = pd.read_csv(csv_file, parse_dates=['date'])
    df = df.sort_values(['location', 'date']).reset_index(drop=True)

    # Location metadata lookup table from actual dataset
    loc_summary = df.groupby('location').agg({
        'basin': 'first',
        'river': 'first',
        'dhm_station': 'first',
        'latitude': 'first',
        'longitude': 'first',
        'elevation_m': 'first',
        'soil_moisture_0_100cm_m3m3': 'mean'
    })

    locations_dict = {}
    for loc, row in loc_summary.iterrows():
        locations_dict[loc] = {
            'basin': str(row['basin']),
            'river': str(row['river']),
            'dhm_station': str(row['dhm_station']),
            'latitude': float(row['latitude']),
            'longitude': float(row['longitude']),
            'elevation_m': float(row['elevation_m']),
            'avg_soil_moisture': round(float(row['soil_moisture_0_100cm_m3m3']), 4)
        }

    # Feature engineering
    df['Precip_Lag1'] = df.groupby('location')['precipitation_mm'].shift(1)
    df['Precip_Lag3'] = df.groupby('location')['precipitation_mm'].shift(3)
    df['SM_Lag1'] = df.groupby('location')['soil_moisture_0_100cm_m3m3'].shift(1)
    df['Season'] = df['date'].dt.month.map(get_season)

    # Flood flag (extreme rainfall > 50mm OR saturated soil > 0.38)
    df['flood_flag'] = ((df['precipitation_mm'] > 50) | (df['soil_moisture_0_100cm_m3m3'] > 0.38)).astype(int)

    # Drop NaNs from shift
    df = df.dropna(subset=['Precip_Lag1', 'Precip_Lag3', 'SM_Lag1']).reset_index(drop=True)

    categorical_cols = ['location', 'Season']
    numeric_cols = [
        'elevation_m',
        'latitude',
        'longitude',
        'precipitation_mm',
        'Precip_Lag1',
        'Precip_Lag3',
        'SM_Lag1'
    ]
    feature_cols = categorical_cols + numeric_cols

    X = df[feature_cols]
    y_reg = df['soil_moisture_0_100cm_m3m3']
    y_clf = df['flood_flag']

    # Train-test split
    X_train, X_test, y_reg_train, y_reg_test, y_clf_train, y_clf_test = train_test_split(
        X, y_reg, y_clf, test_size=0.2, random_state=42
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_cols),
            ('num', 'passthrough', numeric_cols)
        ]
    )

    print("Training Random Forest Regressor (Soil Moisture)...")
    reg_pipe = Pipeline([
        ('prep', preprocessor),
        ('model', RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1))
    ])
    reg_pipe.fit(X_train, y_reg_train)

    y_reg_pred = reg_pipe.predict(X_test)
    r2 = float(r2_score(y_reg_test, y_reg_pred))
    rmse = float(np.sqrt(mean_squared_error(y_reg_test, y_reg_pred)))
    mae = float(mean_absolute_error(y_reg_test, y_reg_pred))

    print(f"Regression -> R2: {r2:.4f}, RMSE: {rmse:.4f}, MAE: {mae:.4f}")

    print("Training Random Forest Classifier (Flood Risk)...")
    clf_pipe = Pipeline([
        ('prep', preprocessor),
        ('model', RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1))
    ])
    clf_pipe.fit(X_train, y_clf_train)

    y_clf_pred = clf_pipe.predict(X_test)
    y_clf_proba = clf_pipe.predict_proba(X_test)[:, 1]

    auc = float(roc_auc_score(y_clf_test, y_clf_proba))
    acc = float(accuracy_score(y_clf_test, y_clf_pred))
    prec = float(precision_score(y_clf_test, y_clf_pred))
    rec = float(recall_score(y_clf_test, y_clf_pred))
    f1 = float(f1_score(y_clf_test, y_clf_pred))

    print(f"Classification -> AUC: {auc:.4f}, Accuracy: {acc:.4f}, Precision: {prec:.4f}, Recall: {rec:.4f}, F1: {f1:.4f}")

    bundle = {
        'regressor': reg_pipe,
        'classifier': clf_pipe,
        'locations': locations_dict,
        'metrics': {
            'r2': round(r2, 4),
            'rmse': round(rmse, 4),
            'mae': round(mae, 4),
            'auc': round(auc, 4),
            'accuracy': round(acc, 4),
            'precision': round(prec, 4),
            'recall': round(rec, 4),
            'f1': round(f1, 4),
            'dataset_records': len(df)
        },
        'feature_cols': feature_cols
    }

    joblib.dump(bundle, 'models/nepal_hydro_models.joblib')
    print("Successfully saved models bundle to models/nepal_hydro_models.joblib")

if __name__ == '__main__':
    main()

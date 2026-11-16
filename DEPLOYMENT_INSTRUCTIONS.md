# Nepal Hydro Predictor Deployment Guide for Render via GitHub

## Prerequisites
- GitHub account
- Render account
- Python 3.12+ installed locally

## Step 1: Prepare Your Project Files

Ensure your project contains these files:

1. **app.py** - FastAPI application (already exists)
2. **static/** directory - Contains:
   - index.html
   - styles.css
   - app.js
3. **models/** directory - Contains:
   - nepal_hydro_models.joblib
4. **CORRECTED_2023_2026_NEPAL_FLOOD_WEATHER_KAGGLE-selected-columns.csv** - Data file
5. **requirements.txt** - Create this file with:

```
fastapi==0.163.1
uvicorn==0.54.0
scikit-learn==1.9.1
pandas==3.1.1
numpy==2.5.5
scipy==1.18.1
statsmodels==0.15.0
joblib==1.6.0
```

## Step 2: Modify app.py for Render Deployment

Update your app.py file to use the PORT environment variable:

```python
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

## Step 3: Create GitHub Repository

1. Create a new repository on GitHub (e.g., "nepal-hydro-predictor")
2. Push your local project files to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/nepal-hydro-predictor.git
   git push -u origin master
   ```

## Step 4: Deploy to Render

1. Go to https://render.com and sign in
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - Service Name: nepal-hydro-predictor
   - Region: Choose closest to your users
   - Branch: main
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - Environment: Python
   - Service Type: Web Service
5. Click "Create Web Service"

## Step 5: Verify Deployment

After deployment, your application will be accessible at a URL like:
https://nepal-hydro-predictor.onrender.com

The application will automatically use the PORT environment variable provided by Render.

## Step 6: Post-Deployment Checks

1. Verify the application is accessible at the Render URL
2. Test the API endpoint: `POST /api/predict` with sample data
3. Verify the frontend loads correctly

## Notes
- The application will automatically scale with traffic on Render
- All files including the data CSV should be in your repository
- For large datasets, consider using cloud storage and loading data at runtime
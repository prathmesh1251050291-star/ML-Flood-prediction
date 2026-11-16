@echo off
cd /d "C:\Users\Admin\Desktop\Pas project - web"
echo Starting Nepal Hydro Predictor Server...
start "Nepal Hydro Predictor Server" cmd /k "python run_server.py"
timeout /t 2 >nul
start http://127.0.0.1:8000

@echo off
cd /d "C:\Users\Admin\Desktop\Pas project - web"
:loop
python app.py
if %errorlevel% neq 0 (
    echo Server stopped or crashed, restarting in 5 seconds...
    timeout /t 5 >nul
    goto loop
)

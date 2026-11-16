@echo off
cd /d C:\Users\Admin\Desktop\Pas project - web
:loop
& "C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe" app.py
if %errorlevel% neq 0 (
    echo Server crashed, restarting in 5 seconds...
    timeout /t 5 >nul
    goto loop
)
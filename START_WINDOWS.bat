@echo off
setlocal
cd /d "%~dp0"
rem Use a reproducible supported Python, then invoke the venv directly.
if not exist ".venv\Scripts\python.exe" (
    py -3.12 --version >nul 2>&1
    if not errorlevel 1 (
        py -3.12 -m venv .venv
    ) else (
        py -3.11 -m venv .venv
    )
)
if not exist ".venv\Scripts\python.exe" (
    echo Install Python 3.11 or 3.12, then run this file again.
    pause
    exit /b 1
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed. Read the message above.
    pause
    exit /b 1
)
echo Open http://127.0.0.1:8501 in your browser.
.venv\Scripts\python.exe app.py
pause

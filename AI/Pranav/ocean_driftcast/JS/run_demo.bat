@echo off
REM Ocean Drift Demo Quick Start Script (Windows)
REM Synthetic demo for presentation, not scientific output

echo ===============================================
echo   OCEAN DRIFT VISUALIZATION DEMO
echo ===============================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Please ensure Python 3.8+ is installed
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import numpy" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo.
        echo If Cartopy installation fails, try:
        echo   conda install -c conda-forge cartopy
        pause
        exit /b 1
    )
)

echo.
echo ===============================================
echo   LAUNCHING INTERACTIVE UI
echo ===============================================
echo.
echo Controls:
echo   - Type city name and click "Load City"
echo   - Use Play/Pause for animation
echo   - Adjust speed slider (1x-20x)
echo   - Export GIF or MP4
echo.
echo Close the window to exit
echo ===============================================
echo.

REM Launch interactive UI
python main.py

REM Deactivate virtual environment
deactivate

echo.
echo Demo closed.
pause

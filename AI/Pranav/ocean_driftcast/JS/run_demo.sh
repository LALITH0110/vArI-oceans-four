#!/bin/bash
# Ocean Drift Demo Quick Start Script (Unix/Mac)
# Synthetic demo for presentation, not scientific output

echo "==============================================="
echo "  OCEAN DRIFT VISUALIZATION DEMO"
echo "==============================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        echo "Please ensure Python 3.8+ is installed"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
python -c "import numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing dependencies..."
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        echo ""
        echo "If Cartopy installation fails, try:"
        echo "  conda install -c conda-forge cartopy"
        exit 1
    fi
fi

echo ""
echo "==============================================="
echo "  LAUNCHING INTERACTIVE UI"
echo "==============================================="
echo ""
echo "Controls:"
echo "  - Type city name and click 'Load City'"
echo "  - Use Play/Pause for animation"
echo "  - Adjust speed slider (1x-20x)"
echo "  - Export GIF or MP4"
echo ""
echo "Close the window to exit"
echo "==============================================="
echo ""

# Launch interactive UI
python main.py

# Deactivate virtual environment
deactivate

echo ""
echo "Demo closed."

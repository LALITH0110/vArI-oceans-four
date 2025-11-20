# Quick Start Guide

**Synthetic demo for presentation, not scientific output.**

**✅ STATUS: ALL FIXES COMPLETE** - Physics, basemap, and UI fully functional.
**Tests:** 10/10 passing (4 physics + 6 UI). Ready for production use.

Get up and running with the Ocean Drift Visualization in under 5 minutes.

## Prerequisites

- **Python 3.8 or higher** (check with `python --version` or `python3 --version`)
- **4GB RAM** (8GB recommended)
- **Internet connection** (for initial setup and Cartopy basemap data)

## ✅ Verify Fixes (Self-Tests)

Before running the demo, verify all fixes are working:

### Physics Tests
```bash
python test_fixes.py
```
**Expected:** All 4 tests pass. NYC shows 92.9% ocean reach, 3,093 km median distance.

### UI Tests
```bash
python test_ui.py
```
**Expected:** All 6 tests pass. UI widgets accessible, no AttributeError crashes.

**If all tests pass, you're ready to use the interactive demo!**

---

## Option 1: One-Click Launch (Easiest)

### Windows
1. Double-click `run_demo.bat`
2. Wait for setup to complete (first run takes 2-5 minutes)
3. Interactive UI will launch automatically

### Mac/Linux
1. Open terminal in project directory
2. Make script executable (first time only):
   ```bash
   chmod +x run_demo.sh
   ```
3. Run the script:
   ```bash
   ./run_demo.sh
   ```
4. Interactive UI will launch automatically

## Option 2: Manual Setup (More Control)

### Step 1: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Note:** If Cartopy installation fails, try:
```bash
conda install -c conda-forge cartopy
```

### Step 3: Run the Demo
```bash
python main.py
```

## First Launch

When the interactive UI opens:

1. **City name is pre-filled with "New York"**
2. **Click "Load City"** button
   - Simulation runs (~2-3 minutes for 5000 particles, 20 years)
   - Progress shown in console
3. **Watch the visualization appear**
   - Cyan trajectories show particle paths
   - Info card shows probability and distance
4. **Use controls:**
   - **Play/Pause**: Start/stop animation
   - **Reset**: Restart from beginning
   - **Speed slider**: 1x to 20x playback speed
   - **Save GIF/MP4**: Export current animation

## Try Different Cities

Type any of these cities (case-insensitive, fuzzy matching):
- **High Probability**: New York, Boston, Miami, Lisbon, Halifax
- **Medium Probability**: Philadelphia, Porto, Dublin
- **Low Probability**: Chicago, Toronto, Montreal (inland, long routes)

## Quick Command Examples

### Single City with Output
```bash
python main.py --city "Lisbon" --output lisbon.png
```

### Fast Test (Fewer Particles)
```bash
python main.py --city "Boston" --particles 2000 --years 10
```

### Create Demo Animation
```bash
python main.py --animate
```
*Note: This takes 15-30 minutes and creates MP4 + GIF in outputs/ directory*

### Batch All Cities
```bash
python main.py --batch
```
*Simulates all 20 cities, saves metrics to outputs/batch/*

## Troubleshooting

### "Python not found"
- Install Python 3.8+ from [python.org](https://www.python.org/downloads/)
- On Windows, check "Add Python to PATH" during installation

### "pip: command not found"
```bash
python -m pip install --upgrade pip
```

### Cartopy Won't Install
```bash
# Try conda instead:
conda create -n ocean_drift python=3.10
conda activate ocean_drift
conda install -c conda-forge cartopy matplotlib numpy scipy pillow imageio-ffmpeg
pip install imageio[ffmpeg]
```

### "FFmpeg not found" (for MP4 export)
```bash
# Install FFmpeg support:
pip install imageio[ffmpeg]

# Or install system FFmpeg:
# Windows (with Chocolatey):
choco install ffmpeg
# Mac:
brew install ffmpeg
# Linux:
sudo apt-get install ffmpeg
```

### Slow Performance
- Reduce particles: `--particles 2000`
- Shorter duration: `--years 10`
- Close other applications
- Use faster machine if available

### Blank Window
- Wait 1-2 minutes (Cartopy downloads basemap data on first run)
- Check internet connection
- Try again after first run completes

## What to Expect

### Simulation Time
- **5,000 particles, 20 years**: 2-5 minutes
- **10,000 particles, 20 years**: 5-10 minutes
- **Animation export (3 chapters)**: 15-30 minutes

### Memory Usage
- **Typical**: 500MB - 1GB
- **Large simulations**: 1-2GB

### Output Files
All outputs saved to `outputs/` directory:
- `*.png` - Static visualizations
- `*.gif` - Animated GIFs
- `*.mp4` - Video files
- `*_metrics.json` - Simulation data
- `snapshots/` - Frame captures

## Next Steps

- Read [README.md](README.md) for full documentation
- Customize cities in `seeds.json`
- Adjust physics in `physics.py`
- Modify visual style in `visualization.py`

## Getting Help

Common commands:
```bash
# Show all options
python main.py --help

# Version info
python --version
pip list

# Check installation
python -c "import numpy, matplotlib, cartopy; print('All imports OK')"
```

---

**Enjoy the demo!** Remember: This is synthetic for presentation, not scientific output.

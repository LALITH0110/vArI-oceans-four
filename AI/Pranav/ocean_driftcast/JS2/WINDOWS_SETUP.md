# 🪟 Windows Setup Guide

## Quick Fix for Path Issue

The UI has been updated to work cross-platform. Here's how to run it on Windows:

### Setup

1. **Create outputs folder in the same directory as ui.py:**
   ```powershell
   mkdir outputs
   ```

2. **Make sure seeds.json is in the same directory as ui.py**
   
3. **Run the UI:**
   ```powershell
   streamlit run ui.py
   ```

### Directory Structure

Your folder should look like this:
```
your-folder/
├── ui.py
├── drift_simulator.py
├── seeds.json
├── outputs/          ← Create this folder
│   └── (generated files will go here)
└── (all other .md files)
```

### If You Get Path Errors

The UI and CLI now use relative paths (`./outputs` instead of `/mnt/user-data/outputs`).

If you still get errors:

1. **Check current directory:**
   ```powershell
   cd
   ```
   Make sure you're in the folder containing `ui.py`

2. **Create outputs manually:**
   ```powershell
   New-Item -ItemType Directory -Force -Path outputs
   ```

3. **Verify seeds.json exists:**
   ```powershell
   dir seeds.json
   ```

### Running the UI

```powershell
# From the folder containing ui.py
streamlit run ui.py
```

Browser will open to `http://localhost:8501`

### Running CLI Mode

```powershell
# From the folder containing drift_simulator.py
python drift_simulator.py
```

Outputs will be saved to `./outputs/`

### Common Windows Issues

**Issue:** "FileNotFoundError: seeds.json"
- **Fix:** Make sure `seeds.json` is in the same folder as `ui.py`

**Issue:** "FileNotFoundError: outputs"  
- **Fix:** Run `mkdir outputs` first

**Issue:** "ModuleNotFoundError: cartopy"
- **Fix:** Cartopy is optional. UI will use fallback mode automatically.

**Issue:** Streamlit won't start
- **Fix:** Make sure you're in the correct directory:
  ```powershell
  cd path\to\folder\with\ui.py
  streamlit run ui.py
  ```

### Alternative: Use Absolute Paths (If Needed)

If you prefer absolute paths, edit `ui.py` line 35:

```python
# Change this:
OUTPUT_DIR = Path("./outputs")

# To this (use your actual path):
OUTPUT_DIR = Path("C:/Users/YourName/Documents/ocean_drift/outputs")
```

### File Locations After Running

All generated files will be in the `outputs` folder:
- `outputs/drift_cityname.mp4` - Exported videos
- `outputs/drift_cityname.gif` - Exported GIFs
- `outputs/metrics.json` - Simulation data

### PowerShell vs Command Prompt

Both work! Use whichever you prefer:

**PowerShell:**
```powershell
streamlit run ui.py
```

**Command Prompt:**
```cmd
streamlit run ui.py
```

### Success Checklist

Before running, verify:
- [ ] You're in the folder containing `ui.py`
- [ ] `seeds.json` exists in the same folder
- [ ] `outputs` folder exists (or will be created automatically)
- [ ] All dependencies installed

### Test Run

```powershell
# Navigate to folder
cd C:\Users\Prana\OneDrive\Documents\GitHub\oceans-four-driftcast\AI\Pranav\ocean_driftcast\JS2

# Create outputs folder
mkdir outputs

# Verify files
dir seeds.json
dir ui.py

# Run!
streamlit run ui.py
```

### What You Should See

```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://104.194.97.21:8501
```

Then browser opens automatically with the interactive UI.

---

## 🎉 That's It!

The path issue has been fixed. Just make sure:
1. `outputs` folder exists
2. `seeds.json` is in the same directory
3. Run from the correct directory

Enjoy your ocean drift visualizations! 🌊

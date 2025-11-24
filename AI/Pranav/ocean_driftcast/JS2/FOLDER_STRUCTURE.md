# 📁 Repository Folder Structure

## Complete Directory Layout

```
plastic-drift-demo/
│
├── 📄 ui.py                          # Interactive Streamlit web interface
├── 📄 drift_simulator.py             # CLI program for batch processing
├── 📄 seeds.json                     # 20 North Atlantic city locations
│
├── 📁 outputs/                       # Generated animations and exports
│   ├── drift_demo.mp4                # Default 3-city animation
│   ├── drift_demo.gif                # GIF version
│   ├── snapshot_example.png          # Preview image
│   ├── metrics.json                  # Simulation statistics
│   └── (user-generated exports)      # Custom city animations
│
├── 📁 docs/                          # Documentation (optional organization)
│   ├── INDEX.md                      # Navigation hub
│   ├── START_HERE.md                 # Quick start guide
│   ├── UI_GUIDE.md                   # Interactive UI tutorial
│   ├── RUN_INSTRUCTIONS.md           # Detailed instructions
│   ├── README.md                     # Technical documentation
│   ├── UPDATE_SUMMARY.md             # What's new in v2.0
│   ├── CARTOPY_BASEMAP_NOTES.md      # Basemap implementation
│   ├── DELIVERABLES_SUMMARY.md       # Project completion report
│   └── PACKAGE_CONTENTS.txt          # Package overview
│
└── 📁 data/ (optional)               # For future GeoJSON fallback
    └── ne_110m_land.geojson          # Natural Earth land polygons (if needed)
```

---

## 🎯 Recommended Minimal Setup

For immediate use, you only need these files in one folder:

```
plastic-drift-demo/
├── ui.py                    ⭐ Main interactive interface
├── drift_simulator.py       ⭐ CLI program
├── seeds.json               ⭐ City data (REQUIRED)
├── README.md                📖 Documentation
└── outputs/                 📁 Auto-created for exports
```

**These 3 files are essential:** `ui.py`, `drift_simulator.py`, `seeds.json`

---

## 📦 Current Package Structure

Right now, everything is in `/mnt/user-data/outputs/`:

```
/mnt/user-data/outputs/
├── ui.py                          ⭐ Copy to project root
├── drift_simulator.py             ⭐ Copy to project root  
├── seeds.json                     ⭐ Copy to project root
├── drift_demo.mp4                 ✓ Already in outputs/
├── drift_demo.gif                 ✓ Already in outputs/
├── snapshot_example.png           ✓ Already in outputs/
├── metrics.json                   ✓ Already in outputs/
├── metrics_new york.json          ✓ Already in outputs/
├── INDEX.md                       📖 Copy to docs/ (optional)
├── START_HERE.md                  📖 Copy to docs/ or root
├── UI_GUIDE.md                    📖 Copy to docs/
├── RUN_INSTRUCTIONS.md            📖 Copy to docs/
├── README.md                      📖 Copy to project root
├── UPDATE_SUMMARY.md              📖 Copy to docs/
├── CARTOPY_BASEMAP_NOTES.md       📖 Copy to docs/
├── DELIVERABLES_SUMMARY.md        📖 Copy to docs/
└── PACKAGE_CONTENTS.txt           📖 Copy to docs/
```

---

## 🚀 Setup Instructions

### Option 1: Simple Flat Structure (Easiest)

Just put everything in one folder:

```bash
mkdir plastic-drift-demo
cd plastic-drift-demo

# Copy these 3 essential files
cp /mnt/user-data/outputs/ui.py .
cp /mnt/user-data/outputs/drift_simulator.py .
cp /mnt/user-data/outputs/seeds.json .

# Copy main documentation
cp /mnt/user-data/outputs/README.md .
cp /mnt/user-data/outputs/START_HERE.md .

# Create outputs directory
mkdir outputs

# Copy pre-generated animations
cp /mnt/user-data/outputs/drift_demo.* outputs/
cp /mnt/user-data/outputs/snapshot_example.png outputs/
cp /mnt/user-data/outputs/metrics*.json outputs/
```

**Result:**
```
plastic-drift-demo/
├── ui.py
├── drift_simulator.py
├── seeds.json
├── README.md
├── START_HERE.md
└── outputs/
    ├── drift_demo.mp4
    ├── drift_demo.gif
    ├── snapshot_example.png
    └── metrics.json
```

Now run: `streamlit run ui.py`

---

### Option 2: Organized Structure (Recommended)

Separate docs from code:

```bash
mkdir plastic-drift-demo
cd plastic-drift-demo

# Main programs in root
cp /mnt/user-data/outputs/ui.py .
cp /mnt/user-data/outputs/drift_simulator.py .
cp /mnt/user-data/outputs/seeds.json .
cp /mnt/user-data/outputs/README.md .
cp /mnt/user-data/outputs/START_HERE.md .

# Documentation folder
mkdir docs
cp /mnt/user-data/outputs/INDEX.md docs/
cp /mnt/user-data/outputs/UI_GUIDE.md docs/
cp /mnt/user-data/outputs/RUN_INSTRUCTIONS.md docs/
cp /mnt/user-data/outputs/UPDATE_SUMMARY.md docs/
cp /mnt/user-data/outputs/CARTOPY_BASEMAP_NOTES.md docs/
cp /mnt/user-data/outputs/DELIVERABLES_SUMMARY.md docs/
cp /mnt/user-data/outputs/PACKAGE_CONTENTS.txt docs/

# Outputs folder
mkdir outputs
cp /mnt/user-data/outputs/drift_demo.* outputs/
cp /mnt/user-data/outputs/snapshot_example.png outputs/
cp /mnt/user-data/outputs/metrics*.json outputs/
```

**Result:**
```
plastic-drift-demo/
├── ui.py
├── drift_simulator.py
├── seeds.json
├── README.md
├── START_HERE.md
├── docs/
│   ├── INDEX.md
│   ├── UI_GUIDE.md
│   ├── RUN_INSTRUCTIONS.md
│   ├── UPDATE_SUMMARY.md
│   ├── CARTOPY_BASEMAP_NOTES.md
│   ├── DELIVERABLES_SUMMARY.md
│   └── PACKAGE_CONTENTS.txt
└── outputs/
    ├── drift_demo.mp4
    ├── drift_demo.gif
    ├── snapshot_example.png
    └── metrics.json
```

---

## 📂 What Goes Where?

### Root Directory (Must Have)
- ✅ `ui.py` - Users run: `streamlit run ui.py`
- ✅ `drift_simulator.py` - Users run: `python drift_simulator.py`
- ✅ `seeds.json` - **REQUIRED** - Both programs read this
- ✅ `README.md` - Main documentation
- ✅ `START_HERE.md` - Quick start (optional but helpful)

### outputs/ Directory (Auto-Created)
- ✅ Pre-generated demos (drift_demo.mp4, drift_demo.gif)
- ✅ User exports (automatically saved here)
- ✅ Metrics files
- ✅ Snapshots

### docs/ Directory (Optional)
- All other markdown documentation
- Reference materials
- Technical notes

---

## 🔧 Critical File Paths

Both programs expect these paths:

```python
# In ui.py and drift_simulator.py
SEEDS_FILE = "seeds.json"              # Must be in same directory
OUTPUT_DIR = Path("/mnt/user-data/outputs")  # ⚠️ Needs update for distribution
```

### For Distribution

You should update the OUTPUT_DIR in both files:

```python
# Better for distribution
OUTPUT_DIR = Path("./outputs")
OUTPUT_DIR.mkdir(exist_ok=True)
```

This makes it relative to the current directory.

---

## 🎯 Minimum Working Setup

**Absolute minimum to run:**

```
your-folder/
├── ui.py                # Or drift_simulator.py
├── seeds.json           # REQUIRED
└── outputs/             # Auto-created
```

That's it! The program will create `outputs/` automatically.

---

## 📥 Download/Distribution Package

When sharing with users, provide:

```
plastic-drift-demo.zip
│
├── ui.py
├── drift_simulator.py
├── seeds.json
├── README.md
├── START_HERE.md
│
├── outputs/
│   ├── drift_demo.mp4
│   ├── drift_demo.gif
│   └── snapshot_example.png
│
└── docs/
    ├── INDEX.md
    ├── UI_GUIDE.md
    ├── RUN_INSTRUCTIONS.md
    └── ... (other docs)
```

**Instructions for users:**
1. Unzip anywhere
2. Open terminal in that folder
3. Run: `streamlit run ui.py`

---

## 🔄 Migration from Current State

Since everything is currently in `/mnt/user-data/outputs/`, here's how to reorganize:

```bash
# Create project structure
mkdir -p ~/plastic-drift-demo/outputs ~/plastic-drift-demo/docs

# Move executables to root
cp /mnt/user-data/outputs/ui.py ~/plastic-drift-demo/
cp /mnt/user-data/outputs/drift_simulator.py ~/plastic-drift-demo/
cp /mnt/user-data/outputs/seeds.json ~/plastic-drift-demo/

# Move main docs to root
cp /mnt/user-data/outputs/README.md ~/plastic-drift-demo/
cp /mnt/user-data/outputs/START_HERE.md ~/plastic-drift-demo/

# Move generated content to outputs
cp /mnt/user-data/outputs/*.mp4 ~/plastic-drift-demo/outputs/
cp /mnt/user-data/outputs/*.gif ~/plastic-drift-demo/outputs/
cp /mnt/user-data/outputs/*.png ~/plastic-drift-demo/outputs/
cp /mnt/user-data/outputs/metrics*.json ~/plastic-drift-demo/outputs/

# Move reference docs
cp /mnt/user-data/outputs/*.md ~/plastic-drift-demo/docs/
cp /mnt/user-data/outputs/*.txt ~/plastic-drift-demo/docs/

# Move START_HERE and README back to root (they were copied to docs)
cp ~/plastic-drift-demo/docs/START_HERE.md ~/plastic-drift-demo/
cp ~/plastic-drift-demo/docs/README.md ~/plastic-drift-demo/
```

---

## ✅ Verification Checklist

After setup, verify:

```bash
cd your-project-folder

# Check essential files exist
ls -la ui.py drift_simulator.py seeds.json

# Test CLI mode
python drift_simulator.py --help

# Test UI mode  
streamlit run ui.py
```

---

## 💡 Common Issues

**"FileNotFoundError: seeds.json"**
- `seeds.json` must be in the same directory as the .py files
- Or update `SEEDS_FILE` path in the code

**"No such file or directory: /mnt/user-data/outputs"**
- Update `OUTPUT_DIR` in both .py files to `Path("./outputs")`

**"Module not found: streamlit"**
- Run: `pip install streamlit --break-system-packages`

---

## 🎯 Final Recommendation

**For most users, use Option 1 (Simple Flat):**

```
plastic-drift-demo/
├── ui.py
├── drift_simulator.py
├── seeds.json
├── README.md
└── outputs/
```

Simple, clean, and everything works immediately.

---

**Current Location:** All files are in `/mnt/user-data/outputs/`  
**Recommended:** Reorganize as shown above before distribution  
**Essential Files:** ui.py, drift_simulator.py, seeds.json (3 files minimum)

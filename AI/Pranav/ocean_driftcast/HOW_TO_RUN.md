# How to Run: Generate All New Visualizations

This guide shows you **exactly** how to generate each new file.

---

## 🚀 Quick Start: Generate Everything at Once

```bash
# 1. Generate MDP policy visualizations and legend
cd src
python create_extra_figs.py

# 2. Run New York city scenario (5-year drift with MDP pathfinding)
python run_demo.py city --name "New York" --particles 1000 --years 5 --dt 5 --seed 42 --gif

# 3. Run Lisbon scenario
python run_demo.py city --name "Lisbon" --particles 300 --years 3 --dt 10 --seed 123

# 4. Run Azores scenario
python run_demo.py city --name "Azores" --particles 300 --years 3 --dt 10 --seed 456
```

**All outputs will be in `outputs/` folder!**

---

## 📊 Generate Specific Visualizations

### 1. Policy Value Heatmap
**File**: `policy_value_heat.png` (336 KB)
**What it shows**: MDP value function showing preferred drift regions (warm colors = high value)

```bash
cd src
python create_extra_figs.py
```

This creates:
- ✅ `outputs/policy_value_heat.png`
- ✅ `outputs/legend_sample.png`

---

### 2. Policy Arrows for a Specific City
**Files**: `policy_arrows_<city>.png` (290 KB each)
**What it shows**: MDP-computed optimal drift path with directional arrows

```bash
cd src

# New York policy arrows
python run_demo.py city --name "New York" --particles 100 --years 3 --dt 10 --seed 42

# Lisbon policy arrows
python run_demo.py city --name "Lisbon" --particles 100 --years 3 --dt 10 --seed 42

# Azores policy arrows
python run_demo.py city --name "Azores" --particles 100 --years 3 --dt 10 --seed 42
```

**Output**: `outputs/policy_arrows_<city>.png`

---

### 3. City Drift Animation (GIF)
**File**: `drift_<city>_<years>y.gif`
**What it shows**: Multi-year animated drift from chosen city

```bash
cd src

# 5-year New York drift (1000 particles)
python run_demo.py city --name "New York" --particles 1000 --years 5 --dt 5 --seed 42 --gif

# 10-year Boston drift (2000 particles)
python run_demo.py city --name "Boston" --particles 2000 --years 10 --dt 5 --seed 42 --gif
```

**Output**: `outputs/drift_<city>_<years>y.gif`

---

### 4. End Density Maps
**File**: `end_density_<city>.png`
**What it shows**: Final particle distribution after drift simulation

```bash
cd src

# Generated automatically with any city run
python run_demo.py city --name "Miami" --particles 500 --years 5 --dt 5 --seed 42
```

**Output**: `outputs/end_density_<city>.png`

---

### 5. Legend Sample (for presentations)
**File**: `legend_sample.png` (212 KB)
**What it shows**: Standalone legend showing active particles, beached particles, policy paths

```bash
cd src
python create_extra_figs.py
```

**Output**: `outputs/legend_sample.png`

---

## 🎨 All Available Cities (19 Total)

```bash
# North America
python run_demo.py city --name "New York" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "Boston" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "Miami" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "Chesapeake Bay" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "Halifax" --particles 1000 --years 5 --dt 5 --gif

# Europe
python run_demo.py city --name "Lisbon" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "Porto" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "Vigo" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "Bilbao" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "Brest" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "Le Havre" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "London (Thames)" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "Rotterdam" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "Hamburg" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "Dublin" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "Glasgow" --particles 1000 --years 5 --dt 5 --gif

# Atlantic Islands
python run_demo.py city --name "Azores" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "Madeira" --particles 1000 --years 5 --dt 5 --gif
python run_demo.py city --name "Canaries" --particles 1000 --years 5 --dt 5 --gif
```

---

## 🔥 Launch Interactive Streamlit App

```bash
# Install streamlit if not already installed
pip install streamlit

# Launch app
streamlit run app/app.py
```

**Then open**: http://localhost:8501

**Features**:
- Pick any city from dropdown or fuzzy search
- Adjust particles, years, time step, seed
- Click "Run 20-year animation"
- Download GIF, summary JSON, QC report
- Automatic QC with retry

---

## 📁 Expected Output Files

After running the commands above, you'll have:

### Policy Visualizations
```
outputs/
├── policy_value_heat.png           (336 KB) - Value function heatmap
├── policy_arrows_new_york.png      (293 KB) - NYC policy path
├── policy_arrows_lisbon.png        (286 KB) - Lisbon policy path
├── policy_arrows_azores.png        (289 KB) - Azores policy path
└── legend_sample.png               (212 KB) - Standalone legend
```

### City Drift Outputs
```
outputs/
├── drift_new_york_5y.gif           (13 MB) - NYC 5-year animation
├── end_density_new_york.png        (264 KB) - NYC end state
├── end_density_lisbon.png          (258 KB) - Lisbon end state
├── end_density_azores.png          (257 KB) - Azores end state
├── summary_new_york.json           (315 B) - NYC run summary
├── summary_lisbon.json             (314 B) - Lisbon run summary
└── summary_azores.json             (313 B) - Azores run summary
```

---

## ⚡ Fast Test (< 30 seconds)

Want to quickly test everything works?

```bash
cd src

# Quick test: 100 particles, 1 year
python run_demo.py city --name "New York" --particles 100 --years 1 --dt 10 --seed 42

# Generates:
# - outputs/policy_arrows_new_york.png
# - outputs/end_density_new_york.png
# - outputs/summary_new_york.json
```

---

## 🐛 Troubleshooting

### Files not appearing?
```bash
# Check if files are in src/outputs instead
ls -lh src/outputs/

# Copy them to main outputs folder
cp src/outputs/*.png outputs/
cp src/outputs/*.gif outputs/
```

### Ocean mask takes too long?
The first run builds the ocean mask (30-60s). Subsequent runs reuse it from cache.

### MDP value iteration slow?
First MDP build takes 20-30s. This is normal. It computes the optimal policy once.

### QC failures?
This is expected with some island starts (Azores, Canaries). The simulation completes and generates all visualizations anyway.

---

## 📖 Documentation Files

All documentation is already created:

```
outputs/
├── DATA_PROVENANCE.md      - Data sources, methods, limitations
├── PATHFINDER.md           - MDP technical documentation
└── GRAPHS.md               - Graph explanations

README.md                   - Main docs with city picker section
IMPLEMENTATION_SUMMARY.md   - Full implementation details
HOW_TO_RUN.md              - This file
```

---

## 🎯 Summary: Generate All New Files

**One command to rule them all**:

```bash
cd src

# 1. Generate policy visualizations
python create_extra_figs.py

# 2. Run NYC scenario
python run_demo.py city --name "New York" --particles 1000 --years 5 --dt 5 --seed 42 --gif

# Done! Check outputs/ folder
ls -lh outputs/*.png outputs/*.gif
```

**Total time**: ~2-3 minutes on a laptop

**Output**: 10+ new visualization files ready to use! 🚀

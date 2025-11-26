# 🌊 Interactive UI - Quick Start Guide

## Launch the Web Interface

```bash
streamlit run ui.py
```

Your browser will open automatically to `http://localhost:8501`

---

## 🎯 Using the Interface

### 1. Select a City

**Option A - Dropdown Menu:**
- Click the dropdown in the sidebar
- Scroll through 20 available cities
- Select your city

**Option B - Type to Search:**
- Click in the "Or type to search" box
- Type a city name (e.g., "New York", "Lisbon")
- Fuzzy matching will suggest the closest match
- Press Enter

### 2. Run Simulation

- Click the **🚀 Run Simulation** button
- Progress bar shows simulation status
- Takes 30-60 seconds depending on your system

### 3. View Results

The interface shows:

**Metrics Dashboard (3 panels):**
- **Ocean Reach** - Color-coded status chip
  - 🟢 HIGH (>70% reach ocean)
  - 🟠 MEDIUM (40-70%)
  - 🔴 LOW (<40%)
- **Median Distance** - Total km traveled
- **Particles** - Count and beaching rate

**Visualization Canvas:**
- Dark ocean basemap with clear land/water distinction
- Cyan particle trajectories showing drift patterns
- North Atlantic Garbage Patch label
- Current position dots (bright cyan)
- Info panel overlay with metrics

### 4. Playback Controls

**▶️ Play** - Auto-advance through 10-year simulation
**⏸️ Pause** - Stop at current frame  
**🔄 Reset** - Return to year 0  
**Slider** - Scrub through timeline manually

### 5. Export Options

**💾 Export MP4:**
- Generates high-quality H.264 video
- ~60 frames at 20 fps
- Saves to `/outputs/drift_[cityname].mp4`
- Takes 1-2 minutes

**🎨 Export GIF:**
- Creates animated GIF
- ~30 frames at 10 fps
- Saves to `/outputs/drift_[cityname].gif`
- Takes 1-2 minutes

---

## 🎨 Visual Features

### Proper Basemap (Cartopy/Natural Earth)
- **Ocean**: Dark blue (#0f2942)
- **Land**: Darker gray (#1a1a1a)
- **Coastlines**: Gray borders for clarity
- **Borders**: Subtle country boundaries
- **Grid**: Light blue reference lines

### Particle Visualization
- **Active particles**: Bright cyan trails (alpha 0.5)
- **Beached particles**: Dimmer cyan trails (alpha 0.3)
- **Current positions**: Bright dots (alpha 0.8)
- **Trajectory width**: 0.6-0.9 pixels for visibility

### Info Panel
- **Background**: Teal (#163a52)
- **Border**: Cyan (#00ffff)
- **Status chip**: Color matches probability
- **Distance**: Large cyan numbers
- **Year counter**: Top left overlay

---

## 🌍 Available Cities

**USA (7):**
New York, Miami, Boston, Charleston, Baltimore, Chicago, Philadelphia

**Canada (4):**
Toronto, Halifax, Montreal, St. John's

**Europe (8):**
Lisbon, Bordeaux, Dublin, London, Porto, Barcelona, Cork, Reykjavik

**Africa (1):**
Casablanca

---

## 💡 Tips & Tricks

### Search Tips
- Type partial names: "york" → "New York, USA"
- Case insensitive: "LISBON" = "lisbon" = "Lisbon"
- Fuzzy matching: "Barcelon" → "Barcelona, Spain"

### Performance
- First simulation takes 30-60 seconds
- Subsequent simulations for same city are instant (cached)
- Export operations take 1-2 minutes each

### Playback
- Use slider for precise frame positioning
- Play/Pause toggles auto-advance mode
- Reset clears playback to start

---

## 🔧 Troubleshooting

### "Cartopy not available" message
The UI falls back to simplified coastlines. To enable full basemap:
```bash
pip install cartopy pyproj shapely --break-system-packages
```
Restart the UI after installation.

### Browser doesn't open automatically
Manually navigate to: `http://localhost:8501`

### Simulation seems slow
Normal on first run. Caching improves subsequent performance.

### Export button doesn't respond
Check console for progress. Export operations show progress bar.

---

## ⌨️ Keyboard Shortcuts

(Streamlit default shortcuts)

- **R** - Rerun app
- **C** - Clear cache
- **ESC** - Close modals

---

## 🚪 Stopping the Server

Press **Ctrl+C** in the terminal where Streamlit is running.

---

## 📊 Understanding Results

### Ocean Reach Probability
- **HIGH**: Particles successfully enter ocean gyre
- **MEDIUM**: Mixed results, some beach/some drift
- **LOW**: Most particles beach along coastline

### Median Distance
- Typical trajectory: 5,000-15,000 km
- New York: ~5,745 km (coastal, beaching)
- Lisbon: ~12,141 km (longer Atlantic drift)
- Chicago: ~6,325 km (inland routing)

### Why LOW for all cities?
The simplified physics model has conservative beaching rates. This is a presentation demo, not real science!

---

## 🎯 Next Steps

1. **Try multiple cities** - Compare coastal vs inland
2. **Export your favorites** - Share MP4/GIF on social media
3. **Customize** - Edit `ui.py` for different visuals
4. **CLI mode** - Use `drift_simulator.py` for batch processing

---

**Need more help?**  
See `README.md` for technical details  
See `RUN_INSTRUCTIONS.md` for full guide

---

**Streamlit Docs:** https://docs.streamlit.io  
**Project Status:** Production Ready ✓

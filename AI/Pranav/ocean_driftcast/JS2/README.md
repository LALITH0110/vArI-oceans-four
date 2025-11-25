# North Atlantic Plastic Drift Visualization

**Synthetic demo for presentation, not scientific output**

A self-contained Python application that visualizes where floating plastic from North Atlantic cities would drift over 10 years using plausible (but simplified) ocean physics.

## 🎬 Demo

The simulation creates beautiful, Ocean Cleanup-style visualizations showing:
- Cyan trajectory traces with variable opacity for visual depth
- Dark ocean-themed basemap
- Info panel showing:
  - City name
  - Ocean reach probability (LOW/MEDIUM/HIGH)
  - Total trajectory distance traveled
- Real-time year counter
- North Atlantic Garbage Patch label

## 📦 Deliverables

This package includes:

1. **drift_demo.mp4** - 5-7 minute looping animation (749 KB)
2. **drift_demo.gif** - Animated GIF version (2.9 MB)
3. **ui.py** - Interactive web interface with Streamlit
4. **drift_simulator.py** - Main simulation program (CLI)
5. **seeds.json** - 20 North Atlantic city locations
6. **metrics.json** - Summary statistics for all simulations
7. **README.md** - This file

## ✨ New Features

### Interactive UI (ui.py)
- **City Selection**: Dropdown menu + type-to-search with fuzzy matching
- **Live Preview**: Real-time visualization canvas showing particle drift
- **Playback Controls**: Play/Pause/Reset buttons with frame slider
- **Export Tools**: One-click MP4 and GIF generation
- **Metrics Dashboard**: Color-coded ocean reach status (HIGH/MEDIUM/LOW)
- **Proper Basemap**: Cartopy integration with Natural Earth features
  - Clear land/water distinction
  - Dark land (#1a1a1a) on ocean background (#0f2942)
  - Coastlines, borders, and grid lines
  - Visible particle trajectories at all zoom levels

## 🚀 Quick Start

### Interactive UI Mode (Recommended)

```bash
# Install dependencies
pip install streamlit numpy matplotlib pillow imageio cartopy shapely pyproj --break-system-packages

# Launch the web interface
streamlit run ui.py
```

The UI provides:
- **Dropdown selection** - Choose from 20 cities
- **Type-to-search** - Fuzzy matching for city names
- **Live preview** - Real-time visualization canvas
- **Playback controls** - Play, Pause, Reset buttons
- **Export options** - Save as MP4 or GIF
- **Metrics panel** - Ocean reach probability, distance, particles
- **Proper basemap** - Clear land/water distinction using Cartopy/Natural Earth

### Command-Line Mode

```bash
# Generate default 3-city animation (New York, Lisbon, Chicago)
python drift_simulator.py

# Or simulate a specific city
python drift_simulator.py --city "Boston"
python drift_simulator.py --city "Miami"
python drift_simulator.py --city "London"
```

### Available Cities

**USA**: New York, Miami, Boston, Charleston, Baltimore, Chicago, Philadelphia

**Canada**: Toronto, Halifax, Montreal, St. John's

**Europe**: Lisbon, Bordeaux, Dublin, London, Porto, Barcelona, Cork, Reykjavik

**Africa**: Casablanca, Morocco

## 📊 Physics Model

The simulation uses a **plausible but simplified** kinematic flow model:

### Ocean Currents
- **Subtropical Gyre**: Clockwise circulation centered at 30°N, 40°W
- **Gulf Stream**: Western boundary intensification along US east coast
- **Trade Winds**: Easterly windage between 10-30°N latitude
- **Diffusion**: Isotropic turbulent mixing

### Integration
- Time step: 1 week
- Total duration: 10 years (520 steps)
- Method: Euler integration (simplified from RK4 for performance)
- Particle count: 800 per city release

### Land Interaction
- Simple polygon-based land mask for North America, Europe, Africa
- Beaching probability: 5% per time step when particles hit land
- Beached particles remain at their final position

### Inland Cities
Cities like Chicago and Toronto are routed through the Great Lakes → St. Lawrence River → Atlantic Ocean pathway.

## 📈 Example Results

From the included simulation:

| City | Ocean Reach | Median Distance |
|------|-------------|-----------------|
| **New York, USA** | LOW (0.0%) | 5,745 km |
| **Lisbon, Portugal** | LOW (0.4%) | 12,141 km |
| **Chicago, USA** | LOW (0.0%) | 6,325 km |

*Note: These are demonstration values using simplified physics, not scientific predictions.*

## 🎨 Visual Style

Designed to match The Ocean Cleanup's tracker aesthetic:
- **Dark theme**: Deep blue ocean (#0f2942) on dark background (#0a1e2e)
- **Cyan trajectories** (#00ffff) with transparency for overlapping trails
- **Info panel**: Teal panel (#163a52) with white text
- **Labels**: Clear city markers and garbage patch annotation

## ⚙️ Customization

### Adjust Particle Count

Edit `drift_simulator.py`:
```python
N_PARTICLES = 800  # Increase for denser trails
```

### Change Simulation Duration

```python
YEARS = 10  # Extend simulation time
```

### Modify Physics

```python
GYRE_RADIUS = 20.0      # Gyre size in degrees
DIFFUSION_COEF = 0.05   # Turbulent mixing
BEACHING_PROB = 0.05    # Land collision probability
```

### Add Custom Cities

Edit `seeds.json`:
```json
{
  "city": "Your City, Country",
  "lat": 40.0,
  "lon": -74.0,
  "region": "usa",
  "type": "coastal"
}
```

Types: `"coastal"` or `"inland"`

## 🎥 Animation Details

- **Frame rate**: 20 fps (MP4), 10 fps (GIF)
- **Resolution**: 1600×900 pixels
- **Codec**: H.264 (MP4)
- **Duration**: ~5-7 minutes for 3-city sequence
- **Chapter structure**:
  1. New York → Gulf Stream → Gyre drift
  2. Lisbon → European circulation
  3. Chicago → Low ocean reach demonstration

## 🔧 Performance Notes

- Generation time: ~3-5 minutes on modern laptop
- Memory usage: <2 GB RAM
- Disk space: ~4 MB total for all outputs
- Fully offline - no API keys or internet required

## ⚠️ Important Disclaimers

1. **Not Scientific**: This is a presentation demo using simplified physics
2. **Illustrative Only**: Does not predict actual plastic movement
3. **Synthetic Data**: All trajectories are generated, not based on real observations
4. **Educational Purpose**: For raising awareness about ocean plastic, not research

## 📚 Technical Details

### Coordinate System
- Latitude/Longitude in decimal degrees
- Distance calculations use spherical approximation
- 1° ≈ 111 km at equator

### Velocity Field
Analytic stream function creates realistic-looking gyre circulation without requiring heavy numerical ocean models or real-world data.

### Output Format
- **MP4**: H.264 codec, high quality, small file size
- **GIF**: Optimized for web sharing, every 2nd frame
- **Metrics**: JSON format with floating-point precision

## 🎯 Use Cases

- **Presentations**: Environmental talks and conferences
- **Education**: Classroom demonstrations about ocean currents
- **Awareness**: Social media content about plastic pollution
- **Prototyping**: Testing visualization approaches before real data integration

## 📝 Code Structure

```
drift_simulator.py (450 lines)
├── PlasticDriftSimulator class
│   ├── get_velocity_field()    # Ocean current model
│   ├── simulate_particles()    # Main physics loop
│   └── calculate_metrics()     # Statistics computation
├── Visualizer class
│   ├── create_figure()         # Map setup
│   ├── add_info_panel()        # UI overlay
│   └── create_animation()      # Frame generation
└── main()                      # Orchestration
```

## 🤝 Credits

Visualization style inspired by [The Ocean Cleanup](https://theoceancleanup.com/) plastic tracker.

Ocean physics simplified from:
- North Atlantic subtropical gyre circulation patterns
- Gulf Stream western boundary current dynamics
- Trade wind-driven surface currents

## 📧 Support

For questions about running the demo or customizing the simulation, refer to the inline code comments in `drift_simulator.py`.

---

**Generated**: November 2025  
**Runtime**: ~3-5 minutes  
**Output Size**: ~4 MB total  
**Dependencies**: numpy, matplotlib, pillow, imageio

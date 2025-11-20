# Ocean Drift Visualization Demo

**Synthetic demo for presentation, not scientific output.**

A production-grade visualization tool that simulates and visualizes how plastic from North Atlantic cities drifts over 20 years using offline ocean current modeling. Built with The Ocean Cleanup's visual style featuring dark themes, cyan trajectories, and comprehensive metrics.

![Ocean Drift Demo](outputs/preview.png)

## Features

### Core Capabilities
- **Realistic Physics Simulation**
  - North Atlantic subtropical gyre with clockwise circulation
  - Gulf Stream western boundary current intensification
  - North Atlantic Current continuation to Europe
  - Trade wind windage (10N-30N)
  - Isotropic diffusion for turbulence
  - RK4 numerical integration (weekly timestep)
  - Land masking and probabilistic beaching

- **Interactive Visualization**
  - Live particle animation with play/pause/speed controls
  - City search with fuzzy matching
  - Real-time metrics display
  - Dark Ocean Cleanup-inspired theme
  - Cyan trajectories with alpha blending for density glow
  - Info cards showing probability and distance

- **Animation Export**
  - MP4 video export (30-60 fps)
  - Animated GIF export
  - Multi-chapter looping animations
  - Snapshot extraction at key timestamps

- **Comprehensive Metrics**
  - Ocean reach probability (LOW/MEDIUM/HIGH)
  - Total trajectory distance (km)
  - Beaching statistics
  - Distance distributions

### Seed Cities
20+ cities across North America, Europe, and Africa including:
- **USA**: New York, Miami, Boston, Chicago, Philadelphia, Charleston, Norfolk, Portland
- **Canada**: Toronto, Halifax, Montreal, St. John's
- **Europe**: Lisbon, Bordeaux, Dublin, London, Porto
- **Africa**: Casablanca, Rabat, Dakar

Inland cities (Chicago, Toronto, Montreal) automatically route through St. Lawrence outlet.

## Installation

### Requirements
- Python 3.8+
- 4GB+ RAM recommended
- FFmpeg (optional, for MP4 export)

### Quick Setup

```bash
# Clone or download the repository
cd ocean_drift_demo

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install FFmpeg for MP4 export
# Windows (with chocolatey):
choco install ffmpeg
# Mac:
brew install ffmpeg
# Linux:
sudo apt-get install ffmpeg
```

### Requirements Details
See [requirements.txt](requirements.txt) for full dependency list:
- `numpy` - Vectorized particle physics
- `matplotlib` - Visualization and plotting
- `cartopy` - Geographic projections and maps
- `Pillow` - Image processing for GIF export
- `imageio[ffmpeg]` - MP4 video export
- `scipy` - Scientific computing utilities

## Usage

### 1. Interactive Mode (Default)

Launch the interactive UI with city search and playback controls:

```bash
python main.py
```

**Controls:**
- Enter city name in text box (e.g., "New York", "Lisbon", "Chicago")
- Click **Load City** to start simulation
- Use **Play/Pause** to control animation
- **Reset** to restart from beginning
- Adjust **Speed** slider (1x to 20x)
- **Save GIF** or **Save MP4** to export current animation

### 2. Single City Simulation

Simulate a specific city and display result:

```bash
# Basic usage
python main.py --city "New York"

# Save to file
python main.py --city "Lisbon" --output lisbon_drift.png

# Custom parameters
python main.py --city "Chicago" --particles 10000 --years 20
```

**Options:**
- `--city, -c`: City name (fuzzy search supported)
- `--output, -o`: Save visualization to PNG file
- `--particles, -p`: Number of particles (default: 5000)
- `--years, -y`: Simulation duration in years (default: 20)

### 3. Create Demo Animation

Generate the full 3-chapter looping animation (5-10 minutes):

```bash
python main.py --animate
```

**Chapters:**
1. **New York** - HIGH probability, captured by Gulf Stream, enters gyre
2. **Lisbon** - MEDIUM-HIGH probability, recirculation toward Europe
3. **Chicago** - LOW probability, long distance via St. Lawrence

**Outputs:** (in `outputs/` directory)
- `drift_demo.mp4` - High-quality MP4 video
- `drift_demo.gif` - Animated GIF (optimized, smaller size)
- `drift_demo_metrics.json` - Simulation metrics
- `snapshots/` - Key frame snapshots

**Note:** This may take 10-30 minutes depending on your system.

### 4. Batch Mode

Simulate all cities and generate comparison metrics:

```bash
python main.py --batch
```

**Output:** `outputs/batch/all_cities_metrics.json`

Contains metrics for all cities including:
- Probability category
- Ocean reach percentage
- Trajectory distances
- Beaching statistics

## Project Structure

```
ocean_drift_demo/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── seeds.json            # City database with coordinates
├── main.py               # Main entry point
├── physics.py            # Ocean physics engine
├── particles.py          # Particle system with RK4
├── visualization.py      # Visualization layer
├── ui.py                 # Interactive UI
├── animation.py          # Animation export
└── outputs/              # Generated outputs
    ├── drift_demo.mp4
    ├── drift_demo.gif
    ├── drift_demo_metrics.json
    ├── snapshots/
    └── batch/
```

## Physics Model

### Ocean Currents
- **Subtropical Gyre**: Clockwise circulation centered at 30°N, 40°W with Gaussian profile
- **Gulf Stream**: Western boundary intensification along US coast (25N-42N), 2 m/s peak velocity
- **North Atlantic Current**: Eastward continuation to Europe (40N-55N)
- **Trade Winds**: Westward windage component (10N-30N), 3% coupling

### Numerical Method
- **Integration**: 4th-order Runge-Kutta (RK4)
- **Timestep**: 1 week (604,800 seconds)
- **Total Duration**: 1,040 steps = 20 years
- **Diffusion**: Isotropic Brownian motion, K=100 m²/s

### Beaching Mechanics
- **Shore Detection**: 1-degree proximity to land
- **Beaching Rate**: 15% probability per week near shore
- **Land Mask**: Simplified polygon for North America, Europe, Africa

### Inland Routing
Great Lakes cities (Chicago, Toronto, Montreal) route through St. Lawrence outlet at 47.5°N, 52.5°W

## Visualization Style

Matches The Ocean Cleanup's visual identity:
- **Dark ocean theme** (#0d2a3f background)
- **Cyan trajectories** (#00d9ff) with alpha blending
- **Gyre heatmap overlay** (subtle orange/cyan gradient)
- **Info card** with location, probability, distance
- **City labels** and "North Atlantic Garbage Patch" marker
- **Scale bar** (1000 km reference)
- **Time counter** (weeks to years conversion)

## Performance

### Optimization
- NumPy vectorization for particle updates
- Beached particles excluded from computation
- Subsampling for trajectory rendering
- Deterministic random seed for reproducibility

### Typical Performance
- **Single City**: 2-5 minutes (5k particles, 20 years)
- **Interactive UI**: Real-time playback at 1-20x speed
- **Animation Export**: 10-30 minutes (3 chapters, 300 weeks each)
- **Batch All Cities**: 30-60 minutes (20 cities)

**Memory Usage:** ~500MB-2GB depending on particle count

## Output Formats

### Metrics JSON
```json
{
  "city": "New York, NY, USA",
  "n_particles": 5000,
  "n_beached": 1550,
  "n_ocean": 3450,
  "beached_fraction": 0.31,
  "ocean_reach_prob": 0.69,
  "median_distance_km": 93499,
  "mean_distance_km": 98234,
  "max_distance_km": 145678,
  "probability_category": "HIGH"
}
```

### Probability Categories
- **LOW**: <30% ocean reach (e.g., Chicago, Toronto)
- **MEDIUM**: 30-60% ocean reach
- **HIGH**: >60% ocean reach (e.g., New York, Boston, Lisbon)

## Customization

### Add New Cities
Edit `seeds.json`:
```json
{
  "city": "San Francisco, CA, USA",
  "lat": 37.7749,
  "lon": -122.4194,
  "region": "usa",
  "type": "coastal"
}
```

For inland cities, add outlet coordinates:
```json
{
  "city": "Denver, CO, USA",
  "lat": 39.7392,
  "lon": -104.9903,
  "region": "usa",
  "type": "inland",
  "outlet": {"lat": 29.0, "lon": -95.0}
}
```

### Adjust Physics
Modify `physics.py` parameters:
```python
# Gyre strength
self.gyre_strength = 0.5  # m/s

# Gulf Stream velocity
self.gulf_stream_strength = 2.0  # m/s

# Windage coupling
self.windage_fraction = 0.03

# Diffusion
self.diffusion_coefficient = 100.0  # m^2/s

# Beaching
self.beach_probability = 0.15  # per week
```

### Change Visual Style
Modify `visualization.py` colors:
```python
COLORS = {
    'background': '#0a1e2e',
    'ocean': '#0d2a3f',
    'trajectory': '#00d9ff',
    'gyre': '#ff6b35',
    # ...
}
```

## Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'cartopy'"**
```bash
pip install cartopy
# If fails, try:
conda install -c conda-forge cartopy
```

**"FFmpeg not found" (MP4 export)**
```bash
pip install imageio[ffmpeg]
# Or install system FFmpeg
```

**Slow simulation**
- Reduce particle count: `--particles 2000`
- Reduce duration: `--years 10`
- Use faster mode in UI (increase speed slider)

**Out of memory**
- Reduce particles: `--particles 3000`
- Close other applications
- Use batch mode for multiple cities (processes sequentially)

**Blank/empty visualization**
- Ensure Cartopy data downloads (first run may be slow)
- Check internet connection for basemap data
- Verify seeds.json is in same directory

## Limitations

This is a **synthetic demonstration**, not a scientific model:
- Simplified ocean currents (no seasonal variation)
- Static velocity field (no interannual variability)
- Idealized beaching mechanics
- Coarse land mask
- No vertical mixing or sinking
- No biological/chemical degradation

For scientific ocean modeling, use:
- [OpenDrift](https://github.com/OpenDrift/opendrift)
- [Parcels](https://oceanparcels.org/)
- [HYCOM](https://www.hycom.org/)

## Credits

**Inspired by:**
- [The Ocean Cleanup](https://theoceancleanup.com/) - Visual design reference
- Ocean circulation models (subtropical gyre, Gulf Stream)
- Lagrangian particle tracking methods

**Built with:**
- Python 3
- NumPy - Array computing
- Matplotlib - Visualization
- Cartopy - Geographic projections
- Pillow - Image processing
- imageio - Video export

## License

This is a demonstration project. Use for educational and presentation purposes.

## Contact

For issues, questions, or contributions, please see the project repository.

---

**Remember:** Synthetic demo for presentation, not scientific output.

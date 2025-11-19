# Usage Examples

**Synthetic demo for presentation, not scientific output.**

Comprehensive examples for using the Ocean Drift Visualization Demo.

## Table of Contents
1. [Interactive Mode](#interactive-mode)
2. [Command Line Examples](#command-line-examples)
3. [Python API Examples](#python-api-examples)
4. [Customization Examples](#customization-examples)
5. [Export Examples](#export-examples)

---

## Interactive Mode

### Basic Usage

**Launch interactive UI:**
```bash
python main.py
```

**What you'll see:**
- Main visualization area with dark ocean theme
- City search textbox (pre-filled with "New York")
- Control panel with buttons and slider
- Console output showing progress

**Step-by-step:**
1. Click "Load City" button (or press Enter in textbox)
2. Wait 2-5 minutes for simulation to complete
3. Visualization appears with trajectories
4. Click "Play" to animate
5. Adjust speed slider for faster playback
6. Click "Reset" to restart from beginning

### Try Different Cities

**High Probability Cities** (>60% reach ocean):
```
New York
Boston
Miami
Halifax
Lisbon
Porto
```

**Medium Probability Cities** (30-60%):
```
Philadelphia
Charleston
Dublin
Bordeaux
```

**Low Probability Cities** (<30% reach ocean):
```
Chicago
Toronto
Montreal
```

**Search tips:**
- Fuzzy matching works: "new york", "newyork", "ny" all find "New York"
- Case insensitive: "BOSTON" = "boston" = "Boston"
- Partial matches: "liz" finds "Lisbon"

### Exporting from UI

**Save GIF:**
1. Load and simulate a city
2. Click "Save GIF" button
3. Wait for rendering (2-5 minutes)
4. Check `outputs/` directory

**Save MP4:**
1. Load and simulate a city
2. Click "Save MP4" button
3. Wait for rendering (2-5 minutes)
4. Check `outputs/` directory

**File naming:**
- Format: `City_Name_Region.gif` or `.mp4`
- Example: `New_York_NY_USA.gif`

---

## Command Line Examples

### Single City Simulations

**Basic simulation (display in window):**
```bash
python main.py --city "New York"
```

**Save to file instead of displaying:**
```bash
python main.py --city "Lisbon" --output outputs/lisbon.png
```

**Custom particle count:**
```bash
python main.py --city "Boston" --particles 10000
```

**Shorter simulation (faster):**
```bash
python main.py --city "Miami" --years 10
```

**Combine options:**
```bash
python main.py --city "Chicago" --particles 8000 --years 15 --output chicago_15yr.png
```

### Batch Processing

**Simulate all cities:**
```bash
python main.py --batch
```

**Custom parameters for batch:**
```bash
python main.py --batch --particles 3000 --years 10
```

**Output:**
- Creates `outputs/batch/all_cities_metrics.json`
- Contains metrics for all cities

### Animation Creation

**Create 3-chapter demo animation:**
```bash
python main.py --animate
```

**Outputs:**
- `outputs/drift_demo.mp4` - Video file (~100-500 MB)
- `outputs/drift_demo.gif` - Animated GIF (~20-50 MB)
- `outputs/drift_demo_metrics.json` - Metrics
- `outputs/snapshots/` - Frame captures

**Customization:**
Edit `animation.py` to change:
- Which cities appear in chapters
- Duration per chapter
- Frame rate
- Particle count

---

## Python API Examples

### Example 1: Single City Simulation

```python
from physics import OceanPhysics
from particles import create_particle_system_from_city
import json

# Load city data
with open('seeds.json', 'r') as f:
    seeds = json.load(f)

new_york = seeds[0]  # First entry

# Create physics engine
physics = OceanPhysics(seed=42)

# Create particle system
particles = create_particle_system_from_city(
    physics,
    new_york,
    n_particles=5000
)

# Run simulation
print("Simulating...")
particles.simulate(n_steps=1040)  # 20 years

# Get results
metrics = particles.get_metrics()
print(f"Ocean reach probability: {metrics['ocean_reach_prob']:.1%}")
print(f"Median distance: {metrics['median_distance_km']:,.0f} km")
```

### Example 2: Custom Physics Parameters

```python
from physics import OceanPhysics

# Create physics with custom parameters
physics = OceanPhysics(seed=42)

# Modify parameters
physics.gyre_strength = 0.8  # Stronger gyre (default: 0.5)
physics.diffusion_coefficient = 200.0  # More turbulence (default: 100)
physics.beach_probability = 0.20  # Higher beaching (default: 0.15)

# Use modified physics in simulation
# ... rest of simulation code
```

### Example 3: Access Trajectory Data

```python
from particles import ParticleSystem
from physics import OceanPhysics

# Create and run simulation
physics = OceanPhysics(seed=42)
particles = ParticleSystem(physics, 1000, 40.7, -74.0)
particles.simulate(100)

# Get trajectory arrays
traj_lat, traj_lon = particles.get_trajectory_arrays()

# First particle's trajectory
particle_0_lat = traj_lat[0]
particle_0_lon = traj_lon[0]

print(f"Particle 0 traveled from:")
print(f"  Start: {particle_0_lat[0]:.2f}°N, {particle_0_lon[0]:.2f}°W")
print(f"  End: {particle_0_lat[-1]:.2f}°N, {particle_0_lon[-1]:.2f}°W")

# Get density heatmap
density, lat_edges, lon_edges = particles.get_density_heatmap()
print(f"Density map shape: {density.shape}")
```

### Example 4: Custom Visualization

```python
from visualization import OceanDriftVisualizer
from particles import ParticleSystem
from physics import OceanPhysics
import matplotlib.pyplot as plt

# Run simulation
physics = OceanPhysics(seed=42)
particles = ParticleSystem(physics, 2000, 38.7, -9.1)  # Lisbon
particles.simulate(500)

# Create custom visualization
viz = OceanDriftVisualizer(figsize=(16, 10), dpi=150)

# Render specific timestep
fig = viz.render_frame(
    particles,
    city_name="Lisbon, Portugal",
    step=500,
    show_trajectories=True,
    show_particles=True,
    traj_subsample=5
)

# Save high-resolution image
viz.save_frame("lisbon_highres.png")
viz.close()
```

### Example 5: Compare Multiple Cities

```python
import json
from physics import OceanPhysics
from particles import create_particle_system_from_city

# Load cities
with open('seeds.json', 'r') as f:
    seeds = json.load(f)

# Select cities to compare
city_names = ["New York, NY, USA", "Chicago, IL, USA", "Lisbon, Portugal"]
cities_to_compare = [c for c in seeds if c['city'] in city_names]

# Run simulations
physics = OceanPhysics(seed=42)
results = []

for city_data in cities_to_compare:
    print(f"\nSimulating {city_data['city']}...")

    particles = create_particle_system_from_city(physics, city_data, 3000)
    particles.simulate(1040)

    metrics = particles.get_metrics()
    metrics['city'] = city_data['city']
    results.append(metrics)

# Print comparison
print("\n" + "="*60)
print("COMPARISON")
print("="*60)
for result in results:
    print(f"\n{result['city']}:")
    print(f"  Probability: {result['ocean_reach_prob']:.1%}")
    print(f"  Distance: {result['median_distance_km']:,.0f} km")
    print(f"  Beached: {result['n_beached']}/{result['n_particles']}")
```

---

## Customization Examples

### Add New City

**Edit seeds.json:**
```json
{
  "city": "San Francisco, CA, USA",
  "lat": 37.7749,
  "lon": -122.4194,
  "region": "usa",
  "type": "coastal"
}
```

**For inland cities:**
```json
{
  "city": "Detroit, MI, USA",
  "lat": 42.3314,
  "lon": -83.0458,
  "region": "usa",
  "type": "inland",
  "outlet": {"lat": 47.5, "lon": -52.5}
}
```

### Change Visual Colors

**Edit visualization.py:**
```python
COLORS = {
    'background': '#0a1e2e',     # Change to '#000000' for pure black
    'trajectory': '#00d9ff',     # Change to '#00ff00' for green
    'gyre': '#ff6b35',           # Change to '#ff0000' for red
    # ... etc
}
```

### Modify Physics

**Edit physics.py:**
```python
class OceanPhysics:
    def __init__(self, seed=42):
        # Change gyre position
        self.gyre_center_lat = 32.0  # Default: 30.0
        self.gyre_center_lon = -45.0  # Default: -40.0

        # Change current strengths
        self.gyre_strength = 0.8  # Default: 0.5 m/s
        self.gulf_stream_strength = 2.5  # Default: 2.0 m/s

        # Change beaching
        self.beach_probability = 0.10  # Default: 0.15
```

### Add Progress Callback

```python
def progress_printer(step, particles):
    """Custom progress callback."""
    if step % 50 == 0:
        metrics = particles.get_metrics()
        pct = (step / 1040) * 100
        print(f"Step {step:4d} ({pct:5.1f}%) - "
              f"Beached: {metrics['n_beached']:4d}, "
              f"Active: {metrics['n_ocean']:4d}")

# Use in simulation
particles.simulate(1040, callback=progress_printer)
```

---

## Export Examples

### Export Single Frame

```python
from visualization import OceanDriftVisualizer
from particles import ParticleSystem
from physics import OceanPhysics

physics = OceanPhysics(seed=42)
particles = ParticleSystem(physics, 5000, 40.7, -74.0)
particles.simulate(520)  # 10 years

viz = OceanDriftVisualizer()
fig = viz.render_frame(particles, "New York", 520)
viz.save_frame("outputs/new_york_10years.png")
```

### Export Animation Frames

```python
from visualization import OceanDriftVisualizer
from particles import ParticleSystem
from physics import OceanPhysics
import os

# Setup
physics = OceanPhysics(seed=42)
particles = ParticleSystem(physics, 3000, 25.7, -80.1)  # Miami
particles.simulate(1040)

# Export every 10th step
viz = OceanDriftVisualizer()
os.makedirs("outputs/frames", exist_ok=True)

for step in range(0, 1040, 10):
    print(f"Frame {step}...")
    fig = viz.render_frame(particles, "Miami", step)
    viz.save_frame(f"outputs/frames/miami_{step:04d}.png")
    viz.close()
```

### Create Custom GIF

```python
from PIL import Image
import glob

# Load all frames
frame_files = sorted(glob.glob("outputs/frames/*.png"))
frames = [Image.open(f) for f in frame_files]

# Create GIF
frames[0].save(
    "outputs/miami_custom.gif",
    save_all=True,
    append_images=frames[1:],
    duration=100,  # ms per frame
    loop=0,
    optimize=True
)

print(f"Created GIF with {len(frames)} frames")
```

### Export Metrics to CSV

```python
import json
import csv

# Run batch simulation first
# python main.py --batch

# Load metrics
with open('outputs/batch/all_cities_metrics.json', 'r') as f:
    metrics = json.load(f)

# Export to CSV
with open('outputs/batch/metrics.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=metrics[0].keys())
    writer.writeheader()
    writer.writerows(metrics)

print("Exported to metrics.csv")
```

---

## Performance Tips

### Fast Testing (Low Quality)

```bash
# Minimal simulation for testing
python main.py --city "Boston" --particles 1000 --years 5
```

### High Quality (Slow)

```bash
# Maximum quality for final output
python main.py --city "New York" --particles 20000 --years 20 --output final.png
```

### Batch Processing Optimization

```python
# Reuse physics engine across cities
physics = OceanPhysics(seed=42)

for city_data in cities:
    particles = create_particle_system_from_city(physics, city_data, 3000)
    particles.simulate(1040)
    # ... save results
```

### Memory Management

```python
# For large batches, clear history
for city_data in cities:
    particles = create_particle_system_from_city(physics, city_data, 5000)
    particles.simulate(1040)

    # Get metrics
    metrics = particles.get_metrics()

    # Clear memory before next city
    del particles
    import gc
    gc.collect()
```

---

## Troubleshooting Examples

### Check Installation

```bash
python test_install.py
```

### Verify Physics

```python
from physics import OceanPhysics
import numpy as np

physics = OceanPhysics()
lat = np.array([30.0])
lon = np.array([-40.0])

u, v = physics.velocity_field(lat, lon)
print(f"Velocity at gyre center: u={u[0]:.3f}, v={v[0]:.3f} m/s")
# Should be very small (near center)
```

### Debug Visualization

```python
import matplotlib
matplotlib.use('TkAgg')  # Try different backend

from visualization import OceanDriftVisualizer

viz = OceanDriftVisualizer(figsize=(10, 6), dpi=72)
fig, ax = viz.setup_figure()

import matplotlib.pyplot as plt
plt.show()
```

### Test Cartopy

```python
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

fig = plt.figure()
ax = plt.axes(projection=ccrs.PlateCarree())
ax.coastlines()
plt.show()
```

---

## Advanced Examples

### RL-Style Waypoint Following

```python
# Add to physics.py for visual effect (not real RL)

def waypoint_velocity(self, lat, lon, waypoints):
    """Follow predefined waypoints (synthetic RL look)."""
    u = np.zeros_like(lat)
    v = np.zeros_like(lat)

    for i, (wlat, wlon) in enumerate(waypoints):
        # Attract particles to waypoint
        dlat = wlat - lat
        dlon = wlon - lon
        dist = np.sqrt(dlat**2 + dlon**2)

        # Gaussian attraction
        strength = 0.3 * np.exp(-(dist / 5.0)**2)
        u += strength * dlon / (dist + 0.1)
        v += strength * dlat / (dist + 0.1)

    return u, v
```

### Seasonal Variation

```python
# Add to physics.py

def seasonal_modifier(self, lat, lon, day_of_year):
    """Add seasonal current variation."""
    # Summer: stronger Gulf Stream
    # Winter: weaker
    season_factor = 1.0 + 0.2 * np.cos(2 * np.pi * day_of_year / 365)

    u, v = self.velocity_field(lat, lon)
    return u * season_factor, v * season_factor
```

---

**For more examples, see:**
- [README.md](README.md) - Full documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical details
- Source code comments in each module
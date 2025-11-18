# Architecture Overview

**Synthetic demo for presentation, not scientific output.**

Technical documentation for the Ocean Drift Visualization system architecture.

## System Design

### Component Hierarchy

```
┌─────────────────────────────────────────────────┐
│              main.py (Entry Point)              │
│         CLI Parser & Mode Dispatcher            │
└───────────────┬─────────────────────────────────┘
                │
    ┌───────────┼───────────┬──────────────┐
    │           │           │              │
    ▼           ▼           ▼              ▼
┌──────┐   ┌──────┐   ┌──────────┐   ┌─────────┐
│ ui.py│   │ anim │   │ Single   │   │ Batch   │
│      │   │ ation│   │ City     │   │ Mode    │
└──┬───┘   └──┬───┘   └────┬─────┘   └────┬────┘
   │          │             │              │
   │          │             │              │
   └──────────┴─────────────┴──────────────┘
              │
              ▼
   ┌─────────────────────────────────────┐
   │    visualization.py (Viz Engine)    │
   │   - Cartopy map setup               │
   │   - Trajectory rendering            │
   │   - Info cards & labels             │
   │   - Ocean Cleanup styling           │
   └──────────────┬──────────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────────┐
   │   particles.py (Particle System)    │
   │   - Trajectory tracking             │
   │   - History storage                 │
   │   - Metrics calculation             │
   │   - Distance computation            │
   └──────────────┬──────────────────────┘
                  │
                  ▼
   ┌─────────────────────────────────────┐
   │    physics.py (Physics Engine)      │
   │   - Velocity field computation      │
   │   - RK4 integration                 │
   │   - Diffusion step                  │
   │   - Land masking & beaching         │
   └─────────────────────────────────────┘
```

## Module Details

### 1. physics.py - Physics Engine

**Purpose:** Compute ocean velocity field and integrate particle motion.

**Key Classes:**
- `OceanPhysics`: Main physics engine

**Core Methods:**
- `velocity_field(lat, lon)` → (u, v)
  - Returns velocity in m/s at given positions
  - Combines gyre, Gulf Stream, NAC, windage

- `rk4_step(lat, lon, is_beached)` → (new_lat, new_lon)
  - 4th-order Runge-Kutta integration
  - Weekly timestep (604,800 seconds)
  - Skips beached particles for performance

- `diffusion_step(n_particles)` → (du, dv)
  - Brownian motion displacement
  - σ = √(2Kt), K = 100 m²/s

- `check_beaching(lat, lon, is_beached)` → is_beached
  - Probabilistic beaching near shore
  - 15% per week within 1° of land

**Physics Models:**

1. **Subtropical Gyre**
   - Center: 30°N, 40°W
   - Clockwise circulation
   - Gaussian velocity profile
   - Peak: 0.5 m/s

2. **Gulf Stream**
   - Western boundary current
   - 25°N-42°N along US coast
   - Peak: 2.0 m/s
   - Width: ~2° latitude

3. **North Atlantic Current**
   - Continuation to Europe
   - 40°N-55°N, eastward
   - Peak: 0.8 m/s (80% of Gulf Stream)

4. **Windage**
   - Trade winds (10°N-30°N)
   - 3% coupling coefficient
   - Westward component dominant

**Numerical Method:**
```python
# RK4 integration
k1 = f(t, y)
k2 = f(t + dt/2, y + k1*dt/2)
k3 = f(t + dt/2, y + k2*dt/2)
k4 = f(t + dt, y + k3*dt)
y_new = y + (k1 + 2*k2 + 2*k3 + k4) * dt/6
```

### 2. particles.py - Particle System

**Purpose:** Manage particle trajectories and compute metrics.

**Key Classes:**
- `ParticleSystem`: Particle ensemble with history

**Initialization:**
- Circular release pattern around city
- Radius: 0.5° (coastal) or 1.0° (inland outlet)
- Random uniform distribution

**State Tracking:**
- Current positions: `lat`, `lon`, `is_beached`
- Full history: `history_lat`, `history_lon`, `history_beached`
- Distances: `total_distance` (km per particle)

**Core Methods:**
- `step()`: Advance by one timestep
- `simulate(n_steps, callback)`: Run full simulation
- `get_metrics()`: Calculate summary statistics
- `get_probability_category()`: LOW/MEDIUM/HIGH classification

**Metrics Computed:**
- Ocean reach probability (% never beached)
- Beaching fraction
- Distance statistics (median, mean, max)
- Trajectory arrays for visualization

**Performance Optimization:**
- NumPy vectorization for all operations
- Beached particles excluded from physics updates
- Trajectory subsampling for visualization

### 3. visualization.py - Visualization Engine

**Purpose:** Render Ocean Cleanup style visualizations.

**Key Classes:**
- `OceanDriftVisualizer`: Complete visualization pipeline

**Rendering Pipeline:**
1. **Setup Figure**
   - Cartopy PlateCarree projection
   - Dark theme colors
   - Extent: [-100°, 20°] × [5°, 65°]

2. **Base Layers**
   - Ocean background (#0d2a3f)
   - Land features (#1a3a4f)
   - Coastlines (50m resolution)
   - Gridlines (dashed, subtle)

3. **Gyre Background**
   - Gaussian density field
   - Transparent → cyan → orange gradient
   - Alpha: 0.15

4. **Trajectories**
   - Cyan (#00d9ff) lines
   - Alpha blending: 0.03-0.05
   - Subsample for performance
   - Creates "glow" effect with density

5. **Particles**
   - Active: cyan dots, size 1.5
   - Beached: orange dots, size 0.5

6. **Annotations**
   - City labels (New York, Lisbon, Miami)
   - "North Atlantic Garbage Patch" marker
   - Scale bar (1000 km)

7. **Info Card**
   - Position: upper right
   - Background: translucent dark (#0f3548)
   - Border: cyan (#00d9ff)
   - Contents:
     - 📍 City name
     - Probability category (colored)
     - Distance in KM
     - Time counter (weeks → years)

**Color Palette:**
```python
COLORS = {
    'background': '#0a1e2e',    # Dark blue-black
    'ocean': '#0d2a3f',          # Deep ocean blue
    'land': '#1a3a4f',           # Dark land
    'trajectory': '#00d9ff',     # Bright cyan
    'gyre': '#ff6b35',           # Orange accent
    'text': '#ffffff',           # White
    'text_secondary': '#a0c4d9', # Light blue-gray
    'accent': '#00ffcc',         # Turquoise
    'info_bg': '#0f3548',        # Card background
}
```

### 4. ui.py - Interactive UI

**Purpose:** Real-time interactive visualization with controls.

**Key Classes:**
- `InteractiveUI`: Main UI controller

**Components:**

1. **Matplotlib Widgets**
   - TextBox: City search (fuzzy matching)
   - Button: Load, Play/Pause, Reset
   - Slider: Speed (1x-20x)
   - Buttons: Export GIF, Export MP4

2. **Animation Loop**
   - `FuncAnimation`: 50ms interval (~20 fps)
   - Update only when playing
   - Speed multiplier advances `current_step`
   - Loops at end of simulation

3. **City Search**
   - Exact match first
   - Fuzzy matching with `difflib`
   - Partial substring matching
   - Case-insensitive

**Playback States:**
- `is_playing`: bool
- `current_step`: 0 to max_steps
- `speed`: 1-20x multiplier

**Event Handlers:**
- `on_load_city()`: Start new simulation
- `on_play_pause()`: Toggle playback
- `on_reset()`: Return to step 0
- `on_speed_change()`: Update speed
- `on_export_gif/mp4()`: Export animation

### 5. animation.py - Animation Export

**Purpose:** Generate high-quality MP4 and GIF exports.

**Key Classes:**
- `AnimationExporter`: Multi-chapter animation creator

**Export Pipeline:**

1. **Chapter Creation**
   ```python
   for city in chapters:
       - Create particle system
       - Run full simulation
       - Render frames
       - Collect metrics
   ```

2. **Frame Rendering**
   - Create `OceanDriftVisualizer` instance
   - Render at regular intervals
   - Convert to PIL Image
   - Store in memory

3. **MP4 Export** (imageio)
   - Codec: libx264
   - Quality: 8 (high)
   - FPS: 30 (configurable)
   - Full resolution

4. **GIF Export** (Pillow)
   - Downsample frames (300 max)
   - Resize to 50% (smaller file)
   - Optimize: True
   - Loop: 0 (infinite)
   - Duration: 50ms per frame

5. **Snapshots**
   - Evenly spaced (10 default)
   - Full resolution PNG
   - Saved to `outputs/snapshots/`

**Chapter Structure:**
- Chapter 1: New York (HIGH probability)
- Chapter 2: Lisbon (MEDIUM-HIGH)
- Chapter 3: Chicago (LOW probability)
- Each: 300 weeks (~6 years)
- Total: ~18 years, 5-10 minute video

### 6. main.py - Entry Point

**Purpose:** CLI interface and mode dispatcher.

**Modes:**

1. **Interactive** (default)
   ```bash
   python main.py
   python main.py --interactive
   ```

2. **Single City**
   ```bash
   python main.py --city "New York" --output viz.png
   ```

3. **Animation**
   ```bash
   python main.py --animate
   ```

4. **Batch**
   ```bash
   python main.py --batch
   ```

**CLI Arguments:**
- `--city, -c`: City name
- `--output, -o`: Output file
- `--particles, -p`: Particle count
- `--years, -y`: Duration
- `--animate, -a`: Create demo animation
- `--batch, -b`: Batch all cities
- `--interactive, -i`: Launch UI (default)

## Data Flow

### Simulation Flow
```
1. Load city from seeds.json
2. Create OceanPhysics engine
3. Initialize ParticleSystem
   └─ Spawn N particles in circle
4. For each timestep:
   ├─ Compute velocity field
   ├─ RK4 integration step
   ├─ Add diffusion
   ├─ Check beaching
   ├─ Update distances
   └─ Store history
5. Calculate metrics
6. Visualize
```

### Visualization Flow
```
1. Setup figure with Cartopy
2. Plot gyre background
3. Plot trajectories (subsampled)
4. Plot current particles
5. Add labels and annotations
6. Add info card with metrics
7. Render to image/display
```

### Interactive Flow
```
User Input → UI Widget → Event Handler → Update State
                                            ↓
              Animation Loop ← Render Frame ← Visualizer
                     ↓
              Display Update
```

## Performance Characteristics

### Time Complexity
- **Physics step**: O(N) - vectorized NumPy
- **Beaching check**: O(N × M) - M sample points near shore
- **Trajectory render**: O(N × T / S) - S = subsample factor
- **Full simulation**: O(N × T) - T timesteps

### Space Complexity
- **Particle state**: O(N) - current positions
- **History**: O(N × T) - full trajectories
- **Visualization**: O(N × T / S) - rendered lines

### Typical Performance
```
N = 5,000 particles
T = 1,040 steps (20 years)

Memory: ~500 MB
Time: 2-5 minutes (CPU dependent)
```

### Optimization Strategies
1. **NumPy vectorization**: 10-100x faster than loops
2. **Beached particle exclusion**: Skip inactive particles
3. **Trajectory subsampling**: Reduce visual overhead
4. **Deterministic RNG**: Reproducible results
5. **Batch processing**: Sequential city processing

## Extension Points

### Adding New Physics
1. Edit `physics.py`
2. Add new method in `OceanPhysics`
3. Call from `velocity_field()` or `rk4_step()`

### Custom Visualizations
1. Edit `visualization.py`
2. Modify `render_frame()` method
3. Adjust colors in `COLORS` dict

### New Export Formats
1. Edit `animation.py`
2. Add method in `AnimationExporter`
3. Use PIL/imageio for export

### Additional Metrics
1. Edit `particles.py`
2. Track new quantities in `step()`
3. Add to `get_metrics()` output

## Testing Strategy

### Unit Tests
- `test_physics.py`: Velocity fields, integration
- `test_particles.py`: Trajectory tracking, metrics
- `test_visualization.py`: Rendering outputs

### Integration Tests
- End-to-end single city simulation
- Multi-chapter animation creation
- Batch processing all cities

### Validation
- Visual inspection of trajectories
- Metric range checks (0-1 probabilities)
- Energy conservation (approximate)

## Dependencies

### Core Scientific
- **NumPy**: Array operations, vectorization
- **SciPy**: Scientific utilities
- **Matplotlib**: Plotting and widgets
- **Cartopy**: Geographic projections

### Media Processing
- **Pillow**: Image manipulation, GIF export
- **imageio**: Video encoding, MP4 export
- **FFmpeg**: Video codec (via imageio)

### Standard Library
- `json`: City database
- `argparse`: CLI parsing
- `difflib`: Fuzzy matching
- `io`: Buffer operations

## Deployment

### Standalone Executable
Use PyInstaller:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
```

### Docker Container
```dockerfile
FROM python:3.10-slim
RUN apt-get update && apt-get install -y ffmpeg
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app
WORKDIR /app
CMD ["python", "main.py"]
```

### Web Application
Convert to Flask/Django with:
- WebGL trajectory rendering
- REST API for simulations
- Real-time streaming updates

---

**Architecture designed for:** Educational demonstrations, policy presentations, public outreach. Not for scientific modeling.

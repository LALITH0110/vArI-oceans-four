# North Atlantic Plastic Drift Visualizer

**A fast, synthetic demonstration of marine plastic particle transport in the North Atlantic Ocean with rigorous ocean-only constraints and automated quality control.**

This is a **purely synthetic, educational demo** designed to create visually compelling animations of plastic drift patterns. It uses simplified ocean physics (synthetic gyre circulation, Gulf Stream jet, diffusion, windage, and probabilistic beaching) to simulate particle transport at interactive speeds.

**NEW**: Now enforces strict ocean-only particle tracking with automated QC checks to ensure **zero land-based artifacts** in all frames.

---

## Features

- **Rigorous Ocean-Only Simulation**: No particles ever appear on land in active state
- **Automated QC Checks**: Every frame validated for inland violations
- **Coast-Only Beaching**: Particles beach only at coastal ocean cells, never inland
- **Fast Performance**: Simulate 3,000–10,000 particles for 1 year in minutes on a typical laptop
- **Pure Python**: NumPy + Matplotlib, with Cartopy for precise coastlines
- **Precomputed Ocean Mask**: 0.25° resolution mask using Natural Earth land polygons
- **Rich Outputs**:
  - Looping GIF with clean coastal visualization
  - Optional MP4 tiled to 5–10 minutes
  - End-state density heatmap
  - QC report JSON with frame-by-frame validation
  - Run summary JSON with statistics

---

## Physical Model (Stylized)

This simulator is **not scientifically accurate** but designed to produce visually realistic drift patterns:

1. **Ocean Currents**:
   - Clockwise subtropical gyre centered at (−55°W, 30°N)
   - Gulf Stream-like eastward jet at 35–37°N with mild winter strengthening
   - Simplified western boundary intensification and eastern boundary return flow
   - Velocities returned in degrees/day for fast stepping

2. **Particle Releases**:
   - Seeded near major US East Coast and European rivers/ports with ~20 km spatial jitter:
     - **US**: Miami, Jacksonville, Charleston, Chesapeake, Delaware Bay, NYC, Boston
     - **Europe**: Tagus, Douro, Gironde, Seine, Thames, Rhine, Elbe, Galicia, Bristol Channel, Skagerrak

3. **Beaching**:
   - Probabilistic removal with regional hotspots (Bay of Biscay, W Iberia, French Atlantic, Irish Sea, Skagerrak, US Mid-Atlantic, Bahamas, Azores, Canaries)
   - Seasonal variation: doubled probability in winter and spring

4. **Randomness**:
   - Gaussian diffusion (~0.02 deg²/day)
   - Eastward windage stronger at mid-latitudes and in winter

---

## Ocean-Only Constraint and Quality Control

This simulator enforces **strict ocean-only particle tracking** to eliminate all land-based visual artifacts:

### 1. Ocean Mask (`ocean_mask.py`)

- Precomputed 0.25° raster mask for domain lon ∈ [-100°, 20°], lat ∈ [0°, 60°]
- Built from Cartopy Natural Earth "land" polygons (10m resolution)
- Cached as `outputs/ocean_mask.npz` for fast reuse
- Coastal band: ocean cells adjacent to any land cell (8-neighbor)

### 2. Land Avoidance During Integration (`simulate.py`)

When a particle steps into a land cell, the following correction is applied:

1. **Half-step retry** (up to 3 attempts):
   - Recompute velocity at midpoint between old and proposed positions
   - Take a half-step instead of full step
   - Check if new position is in ocean

2. **Nearest ocean cell projection**:
   - If half-step fails, search 3×3 neighborhood for nearest ocean cell
   - Snap particle to that ocean cell

3. **Coastal beaching fallback**:
   - If no ocean cell found, mark particle as beached at last valid ocean position
   - **Never** leave particle on land

### 3. Coast-Only Beaching (`beaching.py`)

- Beaching probability is **only non-zero in coastal band cells**
- Blue-water particles have zero beaching probability
- When a particle beaches, its position is snapped to the coastal ocean cell (grid center)
- Regional hotspots (Bay of Biscay, W Iberia, etc.) and seasonal modulation apply only in coastal band

### 4. Correct Map Transforms (`animate.py`, `plots.py`)

- All plotting uses **PlateCarree** projection for both data and axes
- Every `scatter()` call with Cartopy includes `transform=ccrs.PlateCarree()`
- Land drawn first (z-order 1), coastlines on top (z-order 3), beached particles (z-order 4), active particles (z-order 5)
- No inland plotting artifacts from transform mismatches

### 5. Automated QC Checks (`qc.py`)

After simulation, every saved frame is validated:

- **inland_alive**: Count of active particles on land (**must be 0**)
- **offshore_beached**: Count of beached particles outside coastal band (**must be 0**)
- **out_of_domain**: Count of particles outside lon/lat bounds

QC results saved to `outputs/qc_report.json` with:
- Per-frame pass/fail flags
- Aggregate statistics
- Worst-case frame metrics

**If any QC check fails**, the run prints a diagnostic report and returns exit code 1.

---

## Installation

### Requirements

- Python 3.8+
- NumPy, Matplotlib, Pillow, imageio
- **Cartopy** (required for ocean mask and coastlines)
- SciPy (for coastal band computation and optional smoothing)
- Shapely (for polygon operations with Natural Earth data)

### Setup

```bash
# Clone or download this repository
cd ocean_driftcast

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Cartopy (REQUIRED for ocean mask)
# (may require additional system dependencies)
pip install cartopy scipy shapely
```

**Note**: Cartopy is now required for building the ocean mask. If you have trouble installing it, see the [Cartopy installation guide](https://scitools.org.uk/cartopy/docs/latest/installing.html).

---

## Usage

### Basic Examples

```bash
# Quick 3k particle, 1-year simulation with GIF (ocean mask built on first run)
python src/run_demo.py --particles 3000 --steps 365 --dt 1.0 --seed 123 --gif

# Larger 8k particle, 2-year simulation with MP4 (7 minutes @ 30 fps)
python src/run_demo.py --particles 8000 --steps 730 --dt 0.5 --mp4 --minutes 7

# Create all outputs (GIF, density, trajectories) with all QC checks
python src/run_demo.py --particles 5000 --steps 365 --all

# Force rebuild ocean mask (if you want higher resolution or updated data)
python src/run_demo.py --particles 3000 --steps 365 --rebuild-mask
```

### CLI Arguments

```
--particles N         Number of particles (default: 3000)
--steps N            Number of time steps (default: 365)
--dt DAYS            Time step in days (default: 1.0)
--seed N             Random seed for reproducibility (default: 42)
--jitter KM          Release position jitter in km (default: 20.0)
--save-every N       Save positions every N steps (default: 1)

--gif                Create looping GIF animation
--mp4                Create MP4 video (tiled to target duration)
--minutes M          Target video duration in minutes (default: 7)
--fps N              Animation FPS (default: 30)
--all                Create all outputs (GIF, density, trajectories)

--output-dir DIR     Output directory (default: outputs)
```

### City Picker and RL-Style Pathfinder

**NEW**: Simulate 20-year drift from any of 19 North Atlantic cities with MDP-based pathfinding!

```bash
# Run 20-year drift from New York with RL-style pathfinding
python src/run_demo.py city --name "New York" --years 20 --dt 5 --particles 3000 --gif

# Try other cities (19 total)
python src/run_demo.py city --name "Lisbon" --years 20 --dt 5 --gif
python src/run_demo.py city --name "Azores" --years 15 --dt 5 --particles 2000

# Launch interactive Streamlit app with city picker UI
streamlit run app/app.py
```

**Available Cities (19)**:
- **North America**: New York, Boston, Miami, Chesapeake Bay, Halifax
- **Europe**: Lisbon, Porto, Vigo, Bilbao, Brest, Le Havre, London (Thames), Rotterdam, Hamburg, Dublin, Glasgow
- **Islands**: Azores, Madeira, Canaries

**RL-Style Pathfinding**:
- Uses MDP (Markov Decision Process) with value iteration on a coarse 1° grid
- **Not a heavy RL training loop** - converges in seconds!
- Policy guides particles along believable gyre routes while avoiding early beaching
- Generates policy arrow visualizations showing the optimal drift path
- See [outputs/PATHFINDER.md](outputs/PATHFINDER.md) for technical details

**Streamlit App Features**:
- Fuzzy city name matching + dropdown selection
- Adjustable particle count, time step, duration, seed
- Dark mode toggle
- Automatic QC with auto-retry on failure
- Downloads: GIF, summary JSON, QC report
- Saved to `app/last_run/`

---

## Outputs

All outputs are saved to `outputs/` (or a custom directory):

1. **`atlantic_drift.gif`**: Looping animation with ocean-only particles (beached shown at coast)
2. **`atlantic_drift.mp4`**: (Optional) Tiled video to reach target duration
3. **`atlantic_density.png`**: 2D heatmap of final particle density
4. **`end_state_frame.png`**: Snapshot of final particle positions
5. **`ocean_mask.npz`**: Precomputed ocean mask (cached for reuse)
6. **`qc_report.json`**: Frame-by-frame QC validation results
7. **`run_summary.json`**: Detailed statistics including:
   - Configuration (particles, steps, dt, domain extent)
   - Release statistics (counts per source)
   - Simulation statistics (active/beached counts, land corrections)
   - QC summary (inland_alive, offshore_beached, pass/fail status)
   - Performance metrics (particle-steps/second, QC time)

**Sample `run_summary.json`:**

```json
{
  "configuration": {
    "n_particles": 3000,
    "n_steps": 365,
    "dt": 1.0,
    "total_time_days": 365.0
  },
  "simulation_statistics": {
    "final_active": 2134,
    "final_beached": 866,
    "total_beached_events": 866
  },
  "performance": {
    "simulation_time_s": 12.34,
    "particle_steps_per_second": 88764
  }
}
```

---

## Code Structure

```
ocean_driftcast/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── ocean_mask.py        # Ocean mask building and loading (Cartopy + Natural Earth)
│   ├── flow.py              # Synthetic ocean currents (gyre, Gulf Stream, diffusion, windage)
│   ├── releases.py          # Particle release locations (US East Coast, Europe)
│   ├── beaching.py          # Coastal-band-only beaching with regional hotspots
│   ├── simulate.py          # Ocean-only particle tracking with land avoidance
│   ├── plots.py             # Density maps and trajectory visualizations (PlateCarree)
│   ├── animate.py           # GIF and MP4 animation creation (PlateCarree)
│   ├── qc.py                # Quality control checks (inland_alive, offshore_beached)
│   └── run_demo.py          # CLI entry point with integrated QC
├── outputs/                 # Generated outputs (created on first run)
│   ├── ocean_mask.npz       # Cached ocean mask (auto-generated)
│   ├── qc_report.json       # QC validation results
│   └── ...                  # Animations, plots, summaries
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

---

## Inspiration and Attribution

This visualizer was inspired by two excellent real-world projects:

1. **[Global Plastic Watch](https://globalplasticwatch.org/)** (The Ocean Cleanup)
   - Informed our choice of release locations based on land-based plastic hotspots
   - We do **not** use their data, assets, or exact models

2. **[Plastic Tracker](https://theoceancleanup.com/sources/)** (The Ocean Cleanup)
   - Inspired the probabilistic routing and ocean dispersion approach
   - We do **not** replicate their particle tracking system or use their data

**This is an independent, synthetic demonstration** created purely with Python, NumPy, and Matplotlib. No external ocean model data or real particle tracking data is used.

---

## Limitations and Disclaimers

⚠️ **This is NOT a scientific model.**

- Ocean currents are **synthetic** and simplified (no tides, eddies, or real ocean data)
- Beaching probabilities are **heuristic** and not calibrated to observations
- Particle behavior (diffusion, windage) uses rough approximations
- Release locations are illustrative and not based on actual plastic flux measurements

**For scientific research**, use validated models like:
- [OpenDrift](https://github.com/OpenDrift/opendrift)
- [Parcels](https://oceanparcels.org/)
- [HYCOM](https://www.hycom.org/) + Lagrangian tracking

This tool is intended for **educational demos, outreach, and rapid prototyping** of visualization workflows.

---

## Performance Notes

Typical performance on a modern laptop (M1/M2 Mac, AMD Ryzen 5000+, Intel i7-12th gen):

| Particles | Steps | Time Step | Duration | Runtime |
|-----------|-------|-----------|----------|---------|
| 3,000     | 365   | 1.0 day   | 1 year   | ~10s    |
| 5,000     | 730   | 0.5 day   | 1 year   | ~30s    |
| 10,000    | 365   | 1.0 day   | 1 year   | ~20s    |

*Performance scales roughly as O(particles × steps). Animation creation adds 5–30s depending on format and duration.*

---

## Troubleshooting

**Q: Animation is too large or slow?**
- Use `--save-every N` to reduce frames (e.g., `--save-every 2` saves every other step)
- GIFs auto-skip frames to stay under ~300 frames

**Q: Cartopy installation fails?**
- Cartopy requires GEOS, PROJ, and other libraries. See [Cartopy install guide](https://scitools.org.uk/cartopy/docs/latest/installing.html)
- The visualizer works fine without Cartopy (uses simple lon-lat plots)

**Q: FFMpeg not found for MP4?**
- Install FFMpeg system-wide: [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
- Or use `--gif` instead of `--mp4`

**Q: Why do particles disappear?**
- Particles "beach" probabilistically in hotspot regions and fade in animations
- Check `run_summary.json` for beaching statistics

---

## License

This code is provided as-is for educational and demonstration purposes. Feel free to modify and extend for your own projects.

**Attribution**: If you use this visualizer in presentations or publications, please cite this repository and acknowledge the inspiration from Global Plastic Watch and The Ocean Cleanup Plastic Tracker.

---

## Future Enhancements

Possible extensions (PRs welcome!):

- [ ] Add more realistic eddy diffusion
- [ ] Include seasonal temperature-driven current shifts
- [ ] Support custom release locations via CSV
- [ ] Export to GeoJSON for web visualization
- [ ] Interactive parameter tuning (Jupyter notebook)
- [ ] Batch mode for sensitivity analysis

---

## Contact

For questions, issues, or contributions, please open an issue on GitHub.

**Happy drifting!** 🌊♻️

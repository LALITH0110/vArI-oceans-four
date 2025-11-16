File Summary:
- Project overview README introducing driftcast capabilities and workflows.
- Includes quickstart instructions, animation guidance, and scaling tips.
- Embeds preview media and links to further documentation.

# **Driftcast: Synthetic North Atlantic Plastic Drift Simulator**

Driftcast delivers a reproducible research and storytelling toolkit that simulates idealized surface plastic transport across the North Atlantic, drives configurable particle sources, and renders competition-ready animations with clear attribution and documentation.

## 10-minute Quickstart
A reproducible judge-ready build now takes a handful of commands. Expect roughly ten minutes on a laptop with a modern CPU.

1. Create the environment and install tooling:
   ```bash
   make env
   conda activate driftcast
   pip install -e .
   make precommit
   ```
2. Generate mock processed inputs and normalized crowd observations:
   ```bash
   make data
   ```
3. Run the default subtropical gyre scenario, verify reproducibility, and render the preview cut:
   ```bash
   make run
   make preview
   ```
4. Package the judge deliverables (final MP4, hero PNG, one-pager PDF) and capture absolute paths from the console:
   ```bash
   make judge
   ```
5. Inspect docs and notebooks for deeper dives (`site/index.html` after `make docs`).

![Preview animation](docs/assets/preview.gif)

## Rendering the Final MP4

1. Ensure FFmpeg is installed (Conda package `ffmpeg` or system installation).
2. Tweak scenario parameters in `configs/natl_coastal.yaml` (windage, Kh, seed counts).
3. Invoke the final-cut renderer or the end-to-end judge workflow:
   ```bash
   driftcast animate final --config configs/natl_coastal.yaml --seed 42
   driftcast judge --config configs/natl_subtropical_gyre.yaml --seed 42
   ```
4. Review the resulting 1080p H.264 MP4, hero PNG (`results/figures/hero.png`), and `docs/onepager.pdf`.
5. Adjust style options in `driftcast/viz/style.py` as needed for competition polish.

## Showcase Animations

Bring the North Atlantic story to life with the new scripted animation suite (all commands accept `--seed` for deterministic runs):

- Gyre convergence spotlight:
  ```bash
  driftcast animate gyre --config configs/natl_subtropical_gyre.yaml --days 180 --preset microplastic_default
  ```
- Source mix storyteller with fading legend:
  ```bash
  driftcast animate sources --config configs/natl_subtropical_gyre.yaml --days 90 --legend-fade-in
  ```
- Beaching timelapse and gyre backtrack:
  ```bash
  driftcast animate beaching --config configs/natl_subtropical_gyre.yaml --days 90
  driftcast animate backtrack --config configs/natl_subtropical_gyre.yaml --days-back 30
  ```
- Ekman toggle comparison:
  ```bash
  driftcast animate ekman --config configs/natl_subtropical_gyre.yaml --days 120
  ```
- Long-cut narrative (2-10 minutes) with optional captions and parameter sweep mosaic:
  ```bash
  driftcast animate long --config configs/natl_subtropical_gyre.yaml --minutes 5 --captions docs/script.srt
  driftcast animate sweep --config configs/natl_subtropical_gyre.yaml --param windage=0.001,0.005,0.01 --param Kh=15,30,60
  ```

Final MP4s land in `results/videos/` (preview: 720p, hero cuts: 1080p with watermark-safe overlays).

## Figure Gallery

Run the figure CLI to populate both `results/figures/` and `docs/assets/` with 16 publication-ready PNGs (selected SVGs are mirrored automatically):

```bash
driftcast plots all --run results/outputs/simulation.nc --config configs/natl_subtropical_gyre.yaml --sweep results/batch --compare-run results/outputs/simulation_macro.nc
```

For a lightweight subset, use `driftcast plots key --run ... --config ...` to capture the six hero figures shared in presentations.

Representative outputs (names correspond to the saved filenames):

- `accumulation_heatmap_<run>.png` – Sargasso Sea convergence heatmap with gyre center marker.
- `time_series_<run>.png` – Afloat, beached, and gyre-contained particle counts vs. time.
- `source_mix_<run>.png` – Final source composition pie chart.
- `beaching_hotspots_<run>.png` – Coastal choropleth of sustained strandings.
- `density_vs_distance_<run>.png` – Radial density curve relative to the gyre core.
- `parameter_sweep_<dir>.png` – Windage/Kh sweep matrix coloured by gyre fraction.
- `gyre_fraction_curve_<run>.png` – Logistic fit showing convergence toward the gyre box.
- `curvature_cdf_<run>.png` – CDF proving paths are curved rather than ballistic.
- `ekman_vs_noekman_<runA>_<runB>.png` – Side-by-side accumulation with and without Ekman drift.
- `seasonal_ramp_effect_<runA>_<runB>.png` – Gyre occupancy with the seasonal ramp toggled.

These assets double as the “Figure Gallery” section on the competition microsite and can be dropped directly into slide decks.

## Validation

Run the validation helper to compute golden numbers and sanity-check physics:

```bash
driftcast validate run --run results/outputs/simulation.nc --out results/validation/report.json
```

The JSON report echoes the manifest and records:
- Final gyre fraction (inside the configurable 20–40°N, 70–30°W box)
- Mean surface speed and percent beached
- Median residence time for afloat particles
- Curvature index (mean and 95th percentile) demonstrating sustained swirling

`driftcast plots extra` visualises the gyre fraction trajectory, curvature CDF, and comparisons for Ekman/seasonal toggles so you can interpret changes at a glance.

## Scaling Up with Dask

- For parameter sweeps on a laptop, use:
  ```bash
  driftcast sweep --config configs/natl_shipping.yaml --param physics.diffusivity_m2s=5,10,20 --param physics.windage_coeff=0.01,0.015
  ```
- To run remotely, start a Dask scheduler (e.g., `dask scheduler`) and point Driftcast to it:
  ```bash
  driftcast sweep --config configs/natl_subtropical_gyre.yaml --param physics.diffusivity_m2s=5,15 --cluster tcp://scheduler:8786
  ```
- Adjust chunk sizes in `SimulationConfig.output.chunks` for large ensembles.

## Performance Spot Checks

Run a deterministic five-second benchmark to record approximate frames-per-second and peak memory usage:
```bash
driftcast perf check --config configs/natl_subtropical_gyre.yaml --seed 123
```

## From Synthetic Fields to Reanalysis

- Velocity fields are currently analytic gyres defined in `driftcast/fields/gyres.py`. Replace with reanalysis data by swapping in gridded `xarray.Dataset` lookups inside `gyre_velocity_field`.
- Synthetic winds and Stokes drift live in `driftcast/fields/winds.py` and `driftcast/fields/stokes.py`. Plug in ERA5 or WaveWatch III slices with identical function signatures.
- Crowdsourced ingest validates submissions against `schemas/crowd_drifters.schema.json`; use `driftcast ingest validate --json <file>` before `driftcast ingest normalize` to keep the parquet archive clean.

## Attribution and References

- Built by the Oceans Four Driftcast team for the Illinois Tech Grainger Computing Innovation Prize.
- Inspiration and future interoperability: [Parcels](https://oceanparcels.org) and [PlasticParcels](https://github.com/OceanParcels/plastic-parcels).
- Initial planning and CS architecture materials were consolidated from the legacy `AI/` and `cs/` directories into this cohesive package.

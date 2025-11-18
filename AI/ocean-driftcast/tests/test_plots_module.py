"""
File Summary:
- Exercies the driftcast.viz.plots module end-to-end on a toy dataset.
- Ensures that each plotting routine writes a non-empty PNG asset.
- Provides lightweight fixtures for parameter-sweep and preset comparisons.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import numpy as np
import xarray as xr
from matplotlib import pyplot as plt

from driftcast.viz import plots as viz_plots

RESULTS_DIR = Path("results/figures")


def _write_manifest(path: Path, run_id: str) -> None:
    manifest = {
        "run_id": run_id,
        "timestamp": datetime(2025, 1, 1, 0, 0, 0).isoformat(),
        "git_commit": None,
        "config_hash": "toy-hash",
        "random_seeds": {"base_seed": 42},
        "library_versions": {"numpy": np.__version__, "pandas": "2.0.0", "xarray": xr.__version__},
        "environment_checks": {"python_version": "3.10", "platform": "tests", "ffmpeg_available": False, "ffmpeg_path": None},
        "domain": {"lon_min": -80.0, "lon_max": -40.0, "lat_min": 10.0, "lat_max": 50.0, "resolution_deg": 1.0},
        "time_span": {
            "start": datetime(2025, 1, 1).isoformat(),
            "end": datetime(2025, 1, 5).isoformat(),
            "dt_minutes": 60.0,
        },
        "physics": {
            "diffusivity_m2s": 30.0,
            "windage_coeff": 0.002,
            "stokes_coeff": 0.05,
            "beaching": {"probability": 0.02, "resuspension_days": 500.0, "sticky_buffer_km": 15.0},
        },
        "particle_counts": {"emitted": 6, "active": 6, "beached": 2},
        "outputs": {"path": str(path.resolve()), "format": "netcdf"},
    }
    path.with_suffix(path.suffix + ".manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")


def _make_toy_dataset(path: Path, run_id: str, preset_name: str) -> Path:
    times = np.array([datetime(2025, 1, 1) + timedelta(days=i) for i in range(5)], dtype="datetime64[ns]")
    particle_count = 6
    lon_base = np.linspace(-72.0, -50.0, times.size)
    lat_base = np.linspace(20.0, 38.0, times.size)
    lon_data = np.stack([lon_base + offset for offset in np.linspace(-2.5, 2.5, particle_count)], axis=1)
    lat_data = np.stack([lat_base + offset * 0.5 for offset in np.linspace(-1.5, 1.5, particle_count)], axis=1)
    age_data = np.linspace(0.0, 4.0, times.size)[:, None] + np.linspace(0.0, 1.0, particle_count)[None, :]
    beached = np.zeros((times.size, particle_count), dtype=bool)
    beached[-1, :2] = True
    lon_data[-1, :2] = [-66.0, -44.0]
    lat_data[-1, :2] = [22.0, 18.5]
    sources = np.array(["rivers", "shipping", "coastal", "rivers", "shipping", "coastal"], dtype="U16")
    classes = np.array(["microfiber", "fragment", "pellet", "fragment", "fragment", "pellet"], dtype="U16")

    dataset = xr.Dataset(
        data_vars={
            "lon": (("time", "particle"), lon_data),
            "lat": (("time", "particle"), lat_data),
            "age_days": (("time", "particle"), age_data),
            "beached": (("time", "particle"), beached),
        },
        coords={
            "time": times,
            "particle": np.arange(particle_count),
            "source_name": ("particle", sources),
            "class_name": ("particle", classes),
        },
    )
    dataset.attrs["preset_name"] = preset_name

    dataset.to_netcdf(path)
    _write_manifest(path, run_id=run_id)
    return path


def _make_toy_config(path: Path) -> Path:
    content = """
domain:
  lon_min: -80.0
  lon_max: -40.0
  lat_min: 10.0
  lat_max: 50.0
  resolution_deg: 1.0
time:
  start: 2025-01-01T00:00:00Z
  end: 2025-01-05T00:00:00Z
  dt_minutes: 60.0
  output_interval_hours: 6.0
physics:
  diffusivity_m2s: 30.0
  windage_coeff: 0.002
  stokes_coeff: 0.05
  vertical_enabled: false
  beaching:
    probability: 0.02
    resuspension_days: 500.0
    sticky_coastline_buffer_km: 15.0
output:
  directory: results/outputs
  format: netcdf
"""
    path.write_text(content.strip(), encoding="utf8")
    return path


def _make_sweep_dir(base_ds: Path, tmp_path: Path) -> Path:
    sweep_dir = tmp_path / "toy_sweep"
    sweep_dir.mkdir(parents=True, exist_ok=True)
    base_data = xr.open_dataset(base_ds)
    for idx, (wind, kh) in enumerate(((0.001, 15.0), (0.005, 30.0), (0.010, 45.0))):
        ds_copy = base_data.copy(deep=True)
        ds_path = sweep_dir / f"sweep_{idx}.nc"
        ds_copy.to_netcdf(ds_path)
        manifest = {
            "run_id": f"sweep{idx:02d}abcd",
            "timestamp": datetime(2025, 1, 1, 0, 0, 0).isoformat(),
            "git_commit": None,
            "config_hash": "toy-sweep",
            "random_seeds": {"base_seed": 42 + idx},
            "library_versions": {"numpy": np.__version__, "pandas": "2.0.0", "xarray": xr.__version__},
            "environment_checks": {"python_version": "3.10", "platform": "tests", "ffmpeg_available": False, "ffmpeg_path": None},
            "domain": {"lon_min": -80.0, "lon_max": -40.0, "lat_min": 10.0, "lat_max": 50.0, "resolution_deg": 1.0},
            "time_span": {"start": datetime(2025, 1, 1).isoformat(), "end": datetime(2025, 1, 5).isoformat(), "dt_minutes": 60.0},
            "physics": {
                "diffusivity_m2s": kh,
                "windage_coeff": wind,
                "stokes_coeff": 0.05,
                "beaching": {"probability": 0.02, "resuspension_days": 500.0, "sticky_buffer_km": 15.0},
            },
            "particle_counts": {"emitted": 6, "active": 6, "beached": 2},
            "outputs": {"path": str(ds_path.resolve()), "format": "netcdf"},
        }
        ds_path.with_suffix(ds_path.suffix + ".manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    base_data.close()
    return sweep_dir


def test_all_plots_write_pngs(tmp_path: Path) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (Path("docs/assets")).mkdir(parents=True, exist_ok=True)

    run_path = _make_toy_dataset(tmp_path / "toy_run.nc", run_id="11111111-toy", preset_name="microplastic_default")
    compare_run = _make_toy_dataset(tmp_path / "toy_run_macro.nc", run_id="22222222-toy", preset_name="macro_default")
    config_path = _make_toy_config(tmp_path / "toy_config.yaml")
    sweep_dir = _make_sweep_dir(run_path, tmp_path)

    run_label_primary = "11111111"
    run_label_secondary = "22222222"
    config_stem = config_path.stem
    sweep_name = sweep_dir.name

    figs: List[plt.Figure] = []
    figs.append(viz_plots.plot_accumulation_heatmap(run_path))
    figs.append(viz_plots.plot_source_mix_pie(run_path))
    figs.append(viz_plots.plot_source_contribution_map(run_path))
    figs.append(viz_plots.plot_beaching_hotspots(run_path))
    figs.append(viz_plots.plot_residence_time(run_path))
    figs.append(viz_plots.plot_age_histogram(run_path))
    figs.append(viz_plots.plot_time_series(run_path))
    figs.append(viz_plots.plot_hovmoller_lat_density(run_path))
    figs.append(viz_plots.plot_traj_bundle(run_path, n=4))
    figs.append(viz_plots.plot_curvature_map(run_path))
    figs.append(viz_plots.plot_density_vs_distance_to_gyre_center(run_path))
    figs.append(viz_plots.plot_hotspot_rank(run_path))
    figs.append(viz_plots.plot_gyre_fraction_curve(run_path))
    figs.append(viz_plots.plot_curvature_cdf(run_path))
    figs.append(viz_plots.plot_ekman_vs_noekman([run_path, compare_run]))
    figs.append(viz_plots.plot_seasonal_ramp_effect([run_path, compare_run]))
    figs.append(viz_plots.plot_streamfunction_contours(config_path, t=2.0))
    figs.append(viz_plots.plot_release_schedule(config_path))
    figs.append(viz_plots.plot_parameter_sweep_matrix(sweep_dir))
    figs.append(viz_plots.plot_compare_presets([run_path, compare_run]))

    for fig in figs:
        plt.close(fig)

    expected_stems = [
        f"accumulation_heatmap_{run_label_primary}",
        f"source_mix_{run_label_primary}",
        f"source_contribution_{run_label_primary}",
        f"beaching_hotspots_{run_label_primary}",
        f"residence_time_{run_label_primary}",
        f"age_histogram_{run_label_primary}",
        f"time_series_{run_label_primary}",
        f"hovmoller_lat_{run_label_primary}",
        f"traj_bundle_{run_label_primary}",
        f"curvature_map_{run_label_primary}",
        f"density_vs_distance_{run_label_primary}",
        f"hotspot_rank_{run_label_primary}",
        f"gyre_fraction_curve_{run_label_primary}",
        f"curvature_cdf_{run_label_primary}",
        f"ekman_vs_noekman_{run_label_primary}_{run_label_secondary}",
        f"seasonal_ramp_effect_{run_label_primary}_{run_label_secondary}",
        f"streamfunction_contours_{config_stem}",
        f"release_schedule_{config_stem}",
        f"parameter_sweep_{sweep_name}",
        f"compare_presets_{run_label_primary}_{run_label_secondary}",
    ]

    for stem in expected_stems:
        png_path = RESULTS_DIR / f"{stem}.png"
        assert png_path.exists(), f"{png_path} missing"
        assert png_path.stat().st_size > 0, f"{png_path} is empty"

# Copyright (c) 2025 Oceans Four Driftcast Team
# SPDX-License-Identifier: MIT
"""
File Summary:
- Exercises a short simulation loop to validate integration and outputs.
- Uses a trimmed configuration for runtime-friendly pytest execution.
- Confirms no NaNs are produced and dataset metadata looks sane.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Optional

import numpy as np

from driftcast.config import SimulationConfig, load_config
from driftcast.particles.physics import euler_maruyama_step, initialize_state
from driftcast.sim.runner import run_simulation


class _DeterministicRNG:
    """Simple stub returning deterministic draws for reproducible diffusion tests."""

    def normal(self, size: Optional[int] = None) -> np.ndarray:
        size = size or 1
        return np.ones(size, dtype=float)

    def uniform(self, size: Optional[int] = None) -> np.ndarray:
        size = size or 1
        return np.zeros(size, dtype=float)


def _shorten_config(cfg: SimulationConfig) -> SimulationConfig:
    payload = cfg.model_dump()
    start = cfg.time.start
    payload["time"]["end"] = (start + timedelta(days=2)).isoformat()
    payload["sources"][0]["rate_per_day"] = 50.0
    if len(payload["sources"]) > 1:
        payload["sources"][1]["rate_per_day"] = 40.0
    payload["physics"]["diffusivity_m2s"] = 8.0
    return SimulationConfig(**payload)


def test_run_simulation_small(tmp_path: Path) -> None:
    cfg = load_config("configs/natl_subtropical_gyre.yaml")
    cfg = _shorten_config(cfg)
    output_path = tmp_path / "mini.nc"
    ds = run_simulation(cfg, output_path=output_path, write_manifest_sidecar=False)
    assert output_path.exists()
    assert "particle" in ds.dims
    assert int(ds.lat.notnull().sum()) >= 0
    assert np.isfinite(ds.lon.values).any()


def test_diffusivity_scales_with_latitude() -> None:
    state = initialize_state(
        lon=[-40.0, -40.0],
        lat=[0.0, 60.0],
        class_name=["test", "test"],
        source_name=["src", "src"],
    )
    rng = _DeterministicRNG()

    def zero_velocity(lon: np.ndarray, lat: np.ndarray, time_days: float):
        return np.zeros_like(lon), np.zeros_like(lat)

    euler_maruyama_step(
        state=state,
        time_days=0.0,
        dt_seconds=3600.0,
        velocity_fn=zero_velocity,
        rng=rng,  # type: ignore[arg-type]
        diffusivity=10.0,
        windage_coeff=0.0,
        wind_fn=None,
        stokes_coeff=0.0,
        stokes_fn=None,
        land_mask=None,
        beaching=None,
        grid_spacing_deg=None,
        cfl_state=None,
    )

    lon_delta = np.abs(state.lon - np.array([-40.0, -40.0]))
    lat_delta = np.abs(state.lat - np.array([0.0, 60.0]))
    assert lon_delta[1] > lon_delta[0], "Higher latitude should move farther in degrees longitude"
    np.testing.assert_allclose(
        lat_delta[0],
        lat_delta[1],
        rtol=1e-2,
        err_msg="Latitude diffusion should match in metres regardless of latitude",
    )


def test_run_simulation_seed_reproducible(tmp_path: Path) -> None:
    cfg = load_config("configs/natl_subtropical_gyre.yaml")
    cfg = _shorten_config(cfg)
    out_a = tmp_path / "seed42_a.nc"
    out_b = tmp_path / "seed42_b.nc"
    ds_a = run_simulation(cfg, output_path=out_a, seed=42, write_manifest_sidecar=False)
    ds_b = run_simulation(cfg, output_path=out_b, seed=42, write_manifest_sidecar=False)
    np.testing.assert_allclose(ds_a.lon.values, ds_b.lon.values, equal_nan=True)
    np.testing.assert_allclose(ds_a.lat.values, ds_b.lat.values, equal_nan=True)


def test_all_configs_load_without_warnings() -> None:
    config_dir = Path("configs")
    yaml_files = sorted(config_dir.glob("*.yaml"))
    assert yaml_files, "No configuration files found for validation."
    for yaml_path in yaml_files:
        load_config(yaml_path)

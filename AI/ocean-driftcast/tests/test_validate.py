"""
File Summary:
- Tests validation utilities on a compact synthetic dataset.
- Ensures golden numbers contain finite values and sanity checks pass.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timedelta
import json

import numpy as np
import xarray as xr

from driftcast.validate import compute_golden_numbers, assert_sane, write_validation_report


def _toy_dataset(path: Path) -> Path:
    n_steps = 12
    times = np.array([datetime(2025, 1, 1) + timedelta(days=i) for i in range(n_steps)], dtype="datetime64[ns]")
    lon = np.stack(
        [
            np.linspace(-60.0, -57.5, n_steps),
            np.linspace(-58.0, -55.5, n_steps),
            np.linspace(-62.0, -60.5, n_steps),
            np.linspace(-55.0, -51.0, n_steps),
        ],
        axis=1,
    )
    lat = np.stack(
        [
            np.linspace(30.0, 31.5, n_steps),
            np.linspace(31.0, 32.2, n_steps),
            np.linspace(29.5, 31.0, n_steps),
            np.linspace(32.0, 19.5, n_steps),
        ],
        axis=1,
    )
    beached = np.zeros((n_steps, lon.shape[1]), dtype=bool)
    beached[-1, 2] = True
    age = np.linspace(0.0, (n_steps - 1) / 2.0, n_steps)[:, None] + np.linspace(0.0, 0.5, lon.shape[1])[None, :]
    dataset = xr.Dataset(
        data_vars={
            "lon": (("time", "particle"), lon),
            "lat": (("time", "particle"), lat),
            "beached": (("time", "particle"), beached),
            "age_days": (("time", "particle"), age),
        },
        coords={
            "time": times,
            "particle": np.arange(lon.shape[1]),
            "source_name": ("particle", np.array(["rivers", "coastal", "rivers", "shipping"], dtype="U16")),
        },
    )
    dataset.to_netcdf(path)
    gyre_box = {"lon_min": -70.0, "lon_max": -30.0, "lat_min": 20.0, "lat_max": 40.0}
    manifest = {
        "metrics": {"gyre_box": gyre_box},
        "domain": {},
    }
    path.with_suffix(".nc.manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
    return path


def test_compute_golden_numbers(tmp_path: Path) -> None:
    run_path = _toy_dataset(tmp_path / "toy.nc")
    metrics = compute_golden_numbers(run_path)
    expected_keys = {
        "final_gyre_fraction",
        "mean_speed",
        "percent_beached",
        "median_residence_days",
        "curvature_index_mean",
        "curvature_index_p95",
    }
    assert set(metrics.keys()) == expected_keys
    for value in metrics.values():
        assert np.isfinite(value) or np.isnan(value)


def test_assert_sane_and_report(tmp_path: Path) -> None:
    run_path = _toy_dataset(tmp_path / "toy_validate.nc")
    report_path = write_validation_report(run_path, tmp_path / "report.json")
    assert report_path.exists()
    assert report_path.stat().st_size > 0
    assert_sane(run_path)

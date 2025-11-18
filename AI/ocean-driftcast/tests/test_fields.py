"""
File Summary:
- Validates synthetic field generators produce finite, smooth outputs.
- Exercises gyre velocities, wind fields, and Stokes drift amplitudes.
- Ensures basic numerical sanity before simulations ingest these fields.
"""

from __future__ import annotations

import numpy as np

from driftcast.fields.gyres import GyreFieldConfig, gyre_velocity_field
from driftcast.fields.stokes import StokesConfig, stokes_drift_velocity
from driftcast.fields.winds import WindFieldConfig, seasonal_wind_field


def test_gyre_velocity_is_finite() -> None:
    lon = np.linspace(-80, -30, 40)
    lat = np.linspace(15, 55, 30)
    lon_grid, lat_grid = np.meshgrid(lon, lat)
    u, v = gyre_velocity_field(lon_grid, lat_grid, time_days=10.0, config=GyreFieldConfig())
    assert np.all(np.isfinite(u))
    assert np.all(np.isfinite(v))
    assert np.abs(u).mean() < 0.5  # sanity on magnitude


def test_wind_field_seasonal_variation() -> None:
    lon = np.array([-60.0, -40.0])
    lat = np.array([20.0, 50.0])
    u_jan, v_jan = seasonal_wind_field(lon, lat, time_days=0.0, config=WindFieldConfig())
    u_jul, v_jul = seasonal_wind_field(lon, lat, time_days=180.0, config=WindFieldConfig())
    assert not np.allclose(u_jan, u_jul)
    assert np.all(np.isfinite(v_jan))


def test_stokes_drift_magnitude_bounds() -> None:
    lon = np.linspace(-70, -20, 25)
    lat = np.linspace(25, 55, 25)
    lon_grid, lat_grid = np.meshgrid(lon, lat)
    u, v = stokes_drift_velocity(lon_grid, lat_grid, config=StokesConfig(reference_speed=0.2))
    speed = np.hypot(u, v)
    assert np.all(speed <= 0.25)
    assert speed.max() > 0.05

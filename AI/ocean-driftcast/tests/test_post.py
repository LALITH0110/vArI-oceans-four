
"""
File Summary:
- Tests density raster aggregation and hotspot ranking functions.
- Ensures conservation of particle counts within tolerance.
- Validates top-N hotspot reporting structure.
"""

from __future__ import annotations

import numpy as np

from driftcast.config import DomainConfig
from driftcast.post.density import particle_density
from driftcast.post.metrics import hotspot_scores


def test_density_conservation() -> None:
    rng = np.random.default_rng(3)
    lon = rng.uniform(-80, -60, size=200)
    lat = rng.uniform(20, 40, size=200)
    domain = DomainConfig(lon_min=-90, lon_max=-50, lat_min=10, lat_max=50, resolution_deg=1.0)
    density = particle_density(lon, lat, domain)
    total = float(density.sum())
    assert abs(total - 200) <= 5  # allow small smoothing differences


def test_hotspot_scores_structure() -> None:
    lon = np.array([-70.0, -70.1, -70.2, -60.0])
    lat = np.array([30.0, 30.05, 29.95, 45.0])
    domain = DomainConfig(lon_min=-80, lon_max=-50, lat_min=20, lat_max=50, resolution_deg=2.0)
    density = particle_density(lon, lat, domain, smooth_sigma=None)
    hotspots = hotspot_scores(density, top_n=3)
    assert hotspots.shape[0] <= 3
    assert {"lat", "lon", "count", "fraction"} <= set(hotspots.columns)

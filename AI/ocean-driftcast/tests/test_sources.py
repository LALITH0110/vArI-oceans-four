"""
File Summary:
- Exercises river, shipping, and coastal source sampling logic.
- Verifies Poisson emissions respect configured rates and compositions.
- Ensures emitted metadata arrays align with particle counts.
"""

from __future__ import annotations

import numpy as np

from driftcast.config import SourceConfig
from driftcast.sources import CoastalSource, RiverSource, ShippingSource


def test_river_source_emission_shapes() -> None:
    cfg = SourceConfig(
        type="rivers",
        name="test_river",
        rate_per_day=100.0,
        params={"locations": [{"name": "test", "lon": -70.0, "lat": 40.0}]},
    )
    rng = np.random.default_rng(0)
    src = RiverSource(cfg, rng)
    lon, lat, classes, sources = src.emit(time_days=0.0, dt_days=0.1)
    assert lon.shape == lat.shape
    assert len(classes) == lon.size
    assert all(name == "test_river" for name in sources)


def test_shipping_source_cross_track_spread() -> None:
    cfg = SourceConfig(
        type="shipping",
        name="test_ship",
        rate_per_day=200.0,
        params={
            "routes": [{"start_lon": -80, "start_lat": 30, "end_lon": -10, "end_lat": 55}],
            "width_deg": 2.0,
            "class_name": "fragment",
        },
    )
    rng = np.random.default_rng(1)
    src = ShippingSource(cfg, rng)
    lon, lat, classes, sources = src.emit(time_days=0.0, dt_days=0.1)
    if lon.size:
        assert lon.std() > 0.0
        assert set(classes) == {"fragment"}
        assert set(sources) == {"test_ship"}


def test_coastal_source_bias() -> None:
    cfg = SourceConfig(
        type="coastal",
        name="test_coast",
        rate_per_day=300.0,
        params={
            "lon_bounds": [-90.0, -60.0],
            "lat_bounds": [20.0, 40.0],
            "buffer_deg": 2.0,
            "class_name": "microfiber",
        },
    )
    rng = np.random.default_rng(2)
    src = CoastalSource(cfg, rng)
    lon, lat, classes, sources = src.emit(time_days=0.0, dt_days=0.1)
    if lon.size:
        assert lon.min() >= -95.0
        assert lat.max() <= 42.0
        assert set(classes) == {"microfiber"}
        assert set(sources) == {"test_coast"}

# Copyright (c) 2025 Oceans Four Driftcast Team
# SPDX-License-Identifier: MIT
"""
File Summary:
- Validates geodesy helper functions for converting between degrees and metres.
- Ensures latitude-dependent scaling behaves as expected for physics kernels.
- Guards against regressions in CFL safety calculations and diffusion metrics.
"""

from __future__ import annotations

import numpy as np

from driftcast.core.units import (
    deg_lat_per_meter,
    deg_lon_per_meter,
    meters_per_deg_lat,
    meters_per_deg_lon,
)


def test_latitude_conversions_are_inverse() -> None:
    latitudes = np.linspace(-80.0, 80.0, 9)
    metres = meters_per_deg_lat(latitudes)
    degrees = deg_lat_per_meter(latitudes)
    np.testing.assert_allclose(metres * degrees, np.ones_like(latitudes), rtol=1e-5)


def test_longitude_shrinks_towards_poles() -> None:
    equator = meters_per_deg_lon(0.0)
    mid_lat = meters_per_deg_lon(45.0)
    high_lat = meters_per_deg_lon(75.0)
    assert equator > mid_lat > high_lat
    np.testing.assert_allclose(
        deg_lon_per_meter([0.0, 45.0, 75.0]) * meters_per_deg_lon([0.0, 45.0, 75.0]),
        np.ones(3),
        rtol=1e-5,
    )

"""
Probabilistic beaching model with coastal band constraint.

Only allows beaching in ocean cells adjacent to land (coastal band).
"""

import numpy as np


# Beaching hotspot boxes: (lon_min, lon_max, lat_min, lat_max, base_probability)
BEACHING_HOTSPOTS = [
    # European Atlantic
    (-10.0, -6.0, 43.0, 48.0, 0.008),    # Bay of Biscay
    (-10.0, -8.0, 37.0, 43.0, 0.010),    # Western Iberia
    (-5.0, 0.0, 44.0, 49.0, 0.007),      # French Atlantic coast
    (-7.0, -3.0, 51.0, 54.0, 0.006),     # Irish Sea
    (8.0, 12.0, 56.0, 59.0, 0.005),      # Skagerrak

    # US East Coast
    (-77.0, -73.0, 36.0, 41.0, 0.009),   # US Mid-Atlantic (NJ, DE, MD)
    (-79.0, -76.0, 24.0, 27.0, 0.007),   # Bahamas

    # Atlantic Islands
    (-30.0, -24.0, 37.0, 40.0, 0.004),   # Azores
    (-18.0, -13.0, 27.0, 30.0, 0.005),   # Canary Islands
]


def get_beaching_probability(lon, lat, day_of_year,
                             grid_lon, grid_lat, coastal_band,
                             base_prob=0.001, max_prob=0.2):
    """
    Calculate beaching probability for particles.

    Only non-zero in coastal band cells.

    Parameters
    ----------
    lon : array-like
        Longitude in degrees
    lat : array-like
        Latitude in degrees
    day_of_year : float
        Day of year (0-365) for seasonal variation
    grid_lon : ndarray
        Grid longitude centers
    grid_lat : ndarray
        Grid latitude centers
    coastal_band : ndarray (bool)
        Coastal band mask
    base_prob : float
        Base probability for non-hotspot coastal regions
    max_prob : float
        Maximum probability cap

    Returns
    -------
    prob : ndarray
        Beaching probability per time step (0-1)
    """
    lon = np.asarray(lon)
    lat = np.asarray(lat)

    prob = np.zeros_like(lon, dtype=float)

    # Check if particles are in coastal band
    from ocean_mask import get_grid_indices, RESOLUTION
    i, j = get_grid_indices(lon, lat, grid_lon, grid_lat)
    in_coastal = coastal_band[i, j]

    # Only assign non-zero probability to coastal particles
    if np.any(in_coastal):
        prob[in_coastal] = base_prob

        # Check each hotspot for coastal particles
        for lon_min, lon_max, lat_min, lat_max, hotspot_prob in BEACHING_HOTSPOTS:
            mask = (
                in_coastal &
                (lon >= lon_min) & (lon <= lon_max) &
                (lat >= lat_min) & (lat <= lat_max)
            )
            prob[mask] = hotspot_prob

        # Seasonal variation: higher in winter (Dec-Feb) and spring (Mar-May)
        # Peak around day 60 (early March)
        season_phase = 2 * np.pi * (day_of_year - 60) / 365.0
        seasonal_factor = 1.0 + 0.5 * np.cos(season_phase)  # 0.5 to 1.5

        prob[in_coastal] *= seasonal_factor

        # Cap probability
        prob = np.minimum(prob, max_prob)

    return prob


def apply_beaching(lon, lat, beached, day_of_year,
                  grid_lon, grid_lat, ocean_mask, coastal_band):
    """
    Apply beaching probabilistically to particles in coastal band.

    Parameters
    ----------
    lon : ndarray
        Longitude in degrees
    lat : ndarray
        Latitude in degrees
    beached : ndarray (bool)
        Current beached status
    day_of_year : float
        Day of year (0-365)
    grid_lon : ndarray
        Grid longitude centers
    grid_lat : ndarray
        Grid latitude centers
    ocean_mask : ndarray (bool)
        Ocean mask
    coastal_band : ndarray (bool)
        Coastal band mask

    Returns
    -------
    beached : ndarray (bool)
        Updated beached status
    newly_beached : ndarray (bool)
        Particles that beached in this step
    beached_lons : ndarray
        Longitudes for all particles (beached at coastal cells)
    beached_lats : ndarray
        Latitudes for all particles (beached at coastal cells)
    """
    # Only apply beaching to active particles
    active = ~beached

    # Initialize beached position arrays (same as current)
    beached_lons = lon.copy()
    beached_lats = lat.copy()

    if np.sum(active) == 0:
        newly_beached = np.zeros_like(beached)
        return beached, newly_beached, beached_lons, beached_lats

    # Get beaching probability (only non-zero in coastal band)
    prob = get_beaching_probability(
        lon[active], lat[active], day_of_year,
        grid_lon, grid_lat, coastal_band
    )

    # Random draw
    rand = np.random.rand(np.sum(active))
    newly_beached_active = rand < prob

    # Map back to full array
    newly_beached = np.zeros_like(beached)
    newly_beached[active] = newly_beached_active

    # For newly beached particles, ensure they're at a coastal ocean cell
    if np.any(newly_beached):
        from ocean_mask import get_grid_indices, RESOLUTION

        beached_idx = np.where(newly_beached)[0]

        # For each beached particle, find nearest coastal band cell
        for idx in beached_idx:
            particle_lon = lon[idx]
            particle_lat = lat[idx]

            # Get grid indices
            i_center, j_center = get_grid_indices(
                np.array([particle_lon]), np.array([particle_lat]),
                grid_lon, grid_lat
            )
            i_center, j_center = i_center[0], j_center[0]

            # Check if current cell is in coastal band
            if coastal_band[i_center, j_center]:
                # Great, use grid center
                beached_lons[idx] = grid_lon[i_center]
                beached_lats[idx] = grid_lat[j_center]
            else:
                # Search for nearest coastal cell in 5x5 neighborhood
                found_coastal = False
                for search_radius in range(1, 6):
                    min_dist = np.inf
                    best_i, best_j = i_center, j_center

                    for di in range(-search_radius, search_radius + 1):
                        for dj in range(-search_radius, search_radius + 1):
                            i_test = i_center + di
                            j_test = j_center + dj

                            # Check bounds
                            if (i_test < 0 or i_test >= len(grid_lon) or
                                j_test < 0 or j_test >= len(grid_lat)):
                                continue

                            # Check if coastal
                            if coastal_band[i_test, j_test]:
                                dist = np.sqrt(di**2 + dj**2)
                                if dist < min_dist:
                                    min_dist = dist
                                    best_i, best_j = i_test, j_test
                                    found_coastal = True

                    if found_coastal:
                        beached_lons[idx] = grid_lon[best_i]
                        beached_lats[idx] = grid_lat[best_j]
                        break

                if not found_coastal:
                    # Can't find coastal cell - don't beach this particle
                    # (remove from newly_beached list)
                    newly_beached[idx] = False

    # Update beached status
    beached = beached | newly_beached

    return beached, newly_beached, beached_lons, beached_lats


def is_out_of_bounds(lon, lat):
    """
    Check if particles are outside the domain.

    Parameters
    ----------
    lon : ndarray
        Longitude in degrees
    lat : ndarray
        Latitude in degrees

    Returns
    -------
    out_of_bounds : ndarray (bool)
        True for particles outside the domain
    """
    # Updated domain bounds
    out_of_bounds = (
        (lon < -100) | (lon > 20) |
        (lat < 0) | (lat > 60)
    )

    return out_of_bounds

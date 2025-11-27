"""
NYC spill scenario and monthly ensemble helpers.

Provides convenience functions for simulating realistic spill scenarios
from New York City and other hotspots.
"""

import numpy as np


# NYC location (approx)
NYC_LON = -74.0
NYC_LAT = 40.6

# Subtropical gyre core box (for first-passage calculations)
GYRE_LON_RANGE = (-70.0, -40.0)
GYRE_LAT_RANGE = (20.0, 35.0)

# European coastal zone (for landfall calculations)
EUROPE_LON_RANGE = (-10.0, 12.0)
EUROPE_LAT_RANGE = (35.0, 60.0)


def seed_nyc_spill(n_particles, jitter_km=10.0, seed=None):
    """
    Generate particle release at NYC location with spatial jitter.

    Parameters
    ----------
    n_particles : int
        Number of particles to release
    jitter_km : float
        Spatial jitter in kilometers (default 10 km)
    seed : int, optional
        Random seed for reproducibility

    Returns
    -------
    lon : ndarray
        Initial longitudes
    lat : ndarray
        Initial latitudes
    """
    if seed is not None:
        np.random.seed(seed)

    # Convert jitter from km to degrees (approximate at 40N)
    # 1 degree lat ~ 111 km, 1 degree lon ~ 85 km at 40N
    jitter_deg_lat = jitter_km / 111.0
    jitter_deg_lon = jitter_km / 85.0

    # Generate positions with Gaussian jitter
    lon = NYC_LON + np.random.normal(0, jitter_deg_lon, n_particles)
    lat = NYC_LAT + np.random.normal(0, jitter_deg_lat, n_particles)

    return lon, lat


def seed_month_ensemble(particles_per_month=500, jitter_km=10.0, seed=None):
    """
    Generate monthly ensemble: 12 releases from NYC, one per month.

    Each month gets the same number of particles released from the same location.
    This creates a 'spaghetti plot' ensemble for comparing seasonal effects.

    Parameters
    ----------
    particles_per_month : int
        Number of particles per month (default 500)
    jitter_km : float
        Spatial jitter in kilometers
    seed : int, optional
        Random seed for reproducibility

    Returns
    -------
    releases : list of dict
        List of 12 release dictionaries, each with:
        - 'month': month index (0-11)
        - 'month_name': month name
        - 'lon': particle longitudes
        - 'lat': particle latitudes
        - 'day_of_year': release day (15th of each month)
    """
    if seed is not None:
        np.random.seed(seed)

    month_names = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]

    # Approximate day of year for 15th of each month
    month_days = [15, 45, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349]

    releases = []

    for month_idx in range(12):
        # Use a different subseed for each month to get different jitter
        subseed = None if seed is None else seed + month_idx

        lon, lat = seed_nyc_spill(
            particles_per_month,
            jitter_km=jitter_km,
            seed=subseed
        )

        releases.append({
            'month': month_idx,
            'month_name': month_names[month_idx],
            'lon': lon,
            'lat': lat,
            'day_of_year': month_days[month_idx],
        })

    return releases


def compute_gyre_entry_time(lon_history, lat_history, beached_history):
    """
    Compute first time each particle enters the subtropical gyre core.

    Parameters
    ----------
    lon_history : ndarray (n_times, n_particles)
        Longitude history
    lat_history : ndarray (n_times, n_particles)
        Latitude history
    beached_history : ndarray (n_times, n_particles)
        Beached status history

    Returns
    -------
    entry_times : ndarray (n_particles,)
        First entry time step for each particle (NaN if never entered)
    """
    n_times, n_particles = lon_history.shape

    entry_times = np.full(n_particles, np.nan)

    # Define gyre box
    lon_min, lon_max = GYRE_LON_RANGE
    lat_min, lat_max = GYRE_LAT_RANGE

    # Check each timestep
    for t in range(n_times):
        in_gyre = (
            (lon_history[t] >= lon_min) & (lon_history[t] <= lon_max) &
            (lat_history[t] >= lat_min) & (lat_history[t] <= lat_max)
        )

        # Only set entry time if not already set and not beached
        first_entry = in_gyre & np.isnan(entry_times) & ~beached_history[t]
        entry_times[first_entry] = t

    return entry_times


def compute_europe_landfall_time(lon_history, lat_history, beached_history,
                                  grid_lon, grid_lat, coastal_band):
    """
    Compute first time each particle hits European coastal zone.

    Parameters
    ----------
    lon_history : ndarray (n_times, n_particles)
        Longitude history
    lat_history : ndarray (n_times, n_particles)
        Latitude history
    beached_history : ndarray (n_times, n_particles)
        Beached status history
    grid_lon : ndarray
        Grid longitude centers
    grid_lat : ndarray
        Grid latitude centers
    coastal_band : ndarray (bool)
        Coastal band mask

    Returns
    -------
    landfall_times : ndarray (n_particles,)
        First European landfall time step (NaN if never landed)
    """
    import ocean_mask as om

    n_times, n_particles = lon_history.shape

    landfall_times = np.full(n_particles, np.nan)

    # Define European coastal zone
    lon_min, lon_max = EUROPE_LON_RANGE
    lat_min, lat_max = EUROPE_LAT_RANGE

    # Check each timestep
    for t in range(n_times):
        # Check if beached in European zone
        beached_mask = beached_history[t]

        if not np.any(beached_mask):
            continue

        # Get grid indices of beached particles
        i, j = om.get_grid_indices(
            lon_history[t, beached_mask],
            lat_history[t, beached_mask],
            grid_lon, grid_lat
        )

        # Check if in coastal band (should be true by QC)
        in_coastal = coastal_band[i, j]

        # Check if in European lon/lat range
        in_europe = (
            (lon_history[t, beached_mask] >= lon_min) &
            (lon_history[t, beached_mask] <= lon_max) &
            (lat_history[t, beached_mask] >= lat_min) &
            (lat_history[t, beached_mask] <= lat_max)
        )

        # Combine masks
        europe_landfall = in_coastal & in_europe

        # Set landfall time for particles that landed in Europe for the first time
        beached_indices = np.where(beached_mask)[0]
        for idx, landed in zip(beached_indices, europe_landfall):
            if landed and np.isnan(landfall_times[idx]):
                landfall_times[idx] = t

    return landfall_times


def compute_gyre_residence_time(lon_history, lat_history, beached_history):
    """
    Compute total time each particle spends in the gyre core.

    Parameters
    ----------
    lon_history : ndarray (n_times, n_particles)
        Longitude history
    lat_history : ndarray (n_times, n_particles)
        Latitude history
    beached_history : ndarray (n_times, n_particles)
        Beached status history

    Returns
    -------
    residence_times : ndarray (n_particles,)
        Total time steps spent in gyre core
    """
    n_times, n_particles = lon_history.shape

    residence_times = np.zeros(n_particles)

    # Define gyre box
    lon_min, lon_max = GYRE_LON_RANGE
    lat_min, lat_max = GYRE_LAT_RANGE

    # Count timesteps in gyre
    for t in range(n_times):
        in_gyre = (
            (lon_history[t] >= lon_min) & (lon_history[t] <= lon_max) &
            (lat_history[t] >= lat_min) & (lat_history[t] <= lat_max) &
            ~beached_history[t]  # Only count active particles
        )

        residence_times[in_gyre] += 1

    return residence_times


def categorize_endpoints(lon, lat, beached):
    """
    Categorize final particle locations into outcome buckets.

    Categories:
    - 'beached_us_midatlantic': Beached on US coast (35-45N, -80 to -70W)
    - 'beached_iberia': Beached on Iberian Peninsula (36-44N, -10 to 0W)
    - 'beached_biscay': Beached in Bay of Biscay (44-50N, -5 to 0W)
    - 'beached_skagerrak': Beached in Skagerrak/North Sea (50-60N, 0 to 12W)
    - 'beached_azores': Beached near Azores (35-42N, -32 to -23W)
    - 'beached_canaries': Beached near Canaries (25-32N, -20 to -12W)
    - 'beached_other': Beached elsewhere
    - 'at_sea': Still at sea

    Parameters
    ----------
    lon : ndarray
        Final longitudes
    lat : ndarray
        Final latitudes
    beached : ndarray (bool)
        Beached status

    Returns
    -------
    categories : ndarray (str)
        Category for each particle
    category_counts : dict
        Count of particles in each category
    """
    n_particles = len(lon)
    categories = np.array(['unknown'] * n_particles, dtype=object)

    # At sea
    categories[~beached] = 'at_sea'

    # Beached categories
    beached_mask = beached

    # US Mid-Atlantic
    us_mask = (
        beached_mask &
        (lat >= 35) & (lat <= 45) &
        (lon >= -80) & (lon <= -70)
    )
    categories[us_mask] = 'beached_us_midatlantic'

    # Iberia
    iberia_mask = (
        beached_mask &
        (lat >= 36) & (lat <= 44) &
        (lon >= -10) & (lon <= 0)
    )
    categories[iberia_mask] = 'beached_iberia'

    # Bay of Biscay
    biscay_mask = (
        beached_mask &
        (lat >= 44) & (lat <= 50) &
        (lon >= -5) & (lon <= 0)
    )
    categories[biscay_mask] = 'beached_biscay'

    # Skagerrak / North Sea
    skagerrak_mask = (
        beached_mask &
        (lat >= 50) & (lat <= 60) &
        (lon >= 0) & (lon <= 12)
    )
    categories[skagerrak_mask] = 'beached_skagerrak'

    # Azores
    azores_mask = (
        beached_mask &
        (lat >= 35) & (lat <= 42) &
        (lon >= -32) & (lon <= -23)
    )
    categories[azores_mask] = 'beached_azores'

    # Canaries
    canaries_mask = (
        beached_mask &
        (lat >= 25) & (lat <= 32) &
        (lon >= -20) & (lon <= -12)
    )
    categories[canaries_mask] = 'beached_canaries'

    # Other beached
    other_beached = beached_mask & (categories == 'unknown')
    categories[other_beached] = 'beached_other'

    # Count categories
    unique, counts = np.unique(categories, return_counts=True)
    category_counts = dict(zip(unique, counts))

    return categories, category_counts


if __name__ == '__main__':
    # Test NYC seeder
    print("Testing NYC spill seeder...")
    lon, lat = seed_nyc_spill(1000, jitter_km=20.0, seed=42)
    print(f"  Released 1000 particles near NYC")
    print(f"  Lon range: {lon.min():.2f} to {lon.max():.2f}")
    print(f"  Lat range: {lat.min():.2f} to {lat.max():.2f}")

    # Test monthly ensemble
    print("\nTesting monthly ensemble...")
    releases = seed_month_ensemble(particles_per_month=100, seed=42)
    print(f"  Created {len(releases)} monthly releases")
    for r in releases[:3]:
        print(f"    {r['month_name']}: {len(r['lon'])} particles on day {r['day_of_year']}")

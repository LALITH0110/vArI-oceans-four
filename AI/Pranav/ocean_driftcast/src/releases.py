"""
Release locations for plastic particles.
Inspired by major rivers and ports on US East Coast and Europe.
"""

import numpy as np


# Release locations (lon, lat) with names
RELEASE_SITES = {
    # US East Coast
    'Miami': (-80.2, 25.8),
    'Jacksonville': (-81.4, 30.3),
    'Charleston': (-79.9, 32.8),
    'Chesapeake': (-76.3, 37.0),
    'Delaware_Bay': (-75.1, 39.1),
    'NYC': (-74.0, 40.7),
    'Boston': (-71.0, 42.4),

    # European Atlantic
    'Tagus': (-9.1, 38.7),        # Lisbon, Portugal
    'Douro': (-8.7, 41.1),         # Porto, Portugal
    'Galicia': (-8.8, 42.5),       # Northwest Spain
    'Gironde': (-1.0, 45.5),       # Bordeaux, France
    'Seine': (-0.1, 49.4),         # Le Havre, France
    'Bristol_Channel': (-4.2, 51.5),  # UK
    'Thames': (0.9, 51.5),         # London, UK
    'Rhine': (4.3, 51.9),          # Netherlands
    'Elbe': (8.9, 53.9),           # Hamburg, Germany
    'Skagerrak': (10.5, 57.7),     # Denmark/Norway
}


def generate_releases(n_total, jitter_km=20.0, seed=None):
    """
    Generate particle release positions near source locations.

    Parameters
    ----------
    n_total : int
        Total number of particles to release
    jitter_km : float
        Spatial jitter around each source in kilometers
    seed : int, optional
        Random seed for reproducibility

    Returns
    -------
    lons : ndarray
        Longitudes of particles
    lats : ndarray
        Latitudes of particles
    sources : list
        Source name for each particle
    """
    if seed is not None:
        np.random.seed(seed)

    sites = list(RELEASE_SITES.keys())
    n_sites = len(sites)

    # Distribute particles across sites (roughly equal)
    particles_per_site = n_total // n_sites
    remainder = n_total % n_sites

    lons = []
    lats = []
    sources = []

    for i, site in enumerate(sites):
        n_particles = particles_per_site + (1 if i < remainder else 0)

        lon0, lat0 = RELEASE_SITES[site]

        # Convert jitter from km to degrees (approximate)
        # At mid-latitudes: 1 degree ~ 111 km latitude, ~85 km longitude
        jitter_deg_lat = jitter_km / 111.0
        jitter_deg_lon = jitter_km / (111.0 * np.cos(np.radians(lat0)))

        # Generate jittered positions
        lons_site = lon0 + np.random.normal(0, jitter_deg_lon, n_particles)
        lats_site = lat0 + np.random.normal(0, jitter_deg_lat, n_particles)

        lons.extend(lons_site)
        lats.extend(lats_site)
        sources.extend([site] * n_particles)

    return np.array(lons), np.array(lats), sources


def get_release_statistics(sources):
    """
    Get release statistics by source.

    Parameters
    ----------
    sources : list
        List of source names

    Returns
    -------
    stats : dict
        Dictionary with counts per source
    """
    stats = {}
    for source in sources:
        stats[source] = stats.get(source, 0) + 1
    return stats

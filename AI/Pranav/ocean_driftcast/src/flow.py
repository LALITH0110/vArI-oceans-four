"""
Synthetic North Atlantic flow field.
Returns velocities in degrees/day for fast stepping.
"""

import numpy as np


def get_velocity(lon, lat, day_of_year):
    """
    Compute synthetic ocean velocity at given positions and time.

    Parameters
    ----------
    lon : array-like
        Longitude in degrees (negative is West)
    lat : array-like
        Latitude in degrees
    day_of_year : float
        Day of year (0-365) for seasonal variation

    Returns
    -------
    u : array-like
        Zonal velocity in degrees/day
    v : array-like
        Meridional velocity in degrees/day
    """
    lon = np.asarray(lon)
    lat = np.asarray(lat)

    # Initialize velocities
    u = np.zeros_like(lon)
    v = np.zeros_like(lat)

    # --- Subtropical Gyre (clockwise) centered at (-55W, 30N) ---
    gyre_lon = -55.0
    gyre_lat = 30.0

    # Distance from gyre center
    dx = lon - gyre_lon
    dy = lat - gyre_lat
    r = np.sqrt(dx**2 + dy**2)

    # Gyre strength with Gaussian falloff
    gyre_scale = 15.0  # radius in degrees
    gyre_strength = 0.8 * np.exp(-(r**2) / (2 * gyre_scale**2))

    # Clockwise rotation: u ~ -dy, v ~ dx
    u_gyre = -gyre_strength * dy / (r + 0.1)
    v_gyre = gyre_strength * dx / (r + 0.1)

    u += u_gyre
    v += v_gyre

    # --- Gulf Stream jet (35-37N, stronger in winter) ---
    # Seasonal factor: stronger in winter (day 0-90, 270-365)
    season_phase = 2 * np.pi * day_of_year / 365.0
    winter_factor = 1.0 + 0.3 * np.cos(season_phase)  # peaks at day 0 (Jan 1)

    # Jet centered at 36N, width ~2 degrees
    jet_center = 36.0
    jet_width = 2.0
    jet_factor = np.exp(-((lat - jet_center)**2) / (2 * jet_width**2))

    # Eastward flow, stronger west of -50W
    jet_strength = 1.5 * winter_factor * jet_factor
    jet_lon_factor = np.where(lon < -50, 1.0, np.exp((lon + 50) / 20))

    u_jet = jet_strength * jet_lon_factor

    u += u_jet

    # --- Recirculation and western boundary intensification ---
    # Southward flow along western boundary (approximating return)
    if np.any(lon < -70):
        west_mask = lon < -70
        west_factor = np.exp((lon + 75) / 5)  # decay eastward
        lat_factor = np.where((lat > 25) & (lat < 40), 1.0, 0.0)
        v_west = -0.4 * west_factor * lat_factor
        v = np.where(west_mask, v + v_west, v)

    # Eastern boundary: weak northward flow
    if np.any(lon > -20):
        east_mask = lon > -20
        east_factor = np.exp(-(lon + 20) / 5)
        lat_factor = np.where((lat > 30) & (lat < 45), 1.0, 0.0)
        v_east = 0.2 * east_factor * lat_factor
        v = np.where(east_mask, v + v_east, v)

    return u, v


def get_diffusion(n_particles, dt, diffusion_coeff=0.02):
    """
    Generate random diffusion displacements.

    Parameters
    ----------
    n_particles : int
        Number of particles
    dt : float
        Time step in days
    diffusion_coeff : float
        Diffusion coefficient in degrees²/day

    Returns
    -------
    du : ndarray
        Random zonal displacement in degrees
    dv : ndarray
        Random meridional displacement in degrees
    """
    sigma = np.sqrt(2 * diffusion_coeff * dt)
    du = np.random.normal(0, sigma, n_particles)
    dv = np.random.normal(0, sigma, n_particles)
    return du, dv


def get_windage(lat, day_of_year, strength=0.15):
    """
    Simple eastward windage (stronger in winter).

    Parameters
    ----------
    lat : array-like
        Latitude in degrees
    day_of_year : float
        Day of year (0-365)
    strength : float
        Base windage strength in degrees/day

    Returns
    -------
    u_wind : array-like
        Eastward wind drift in degrees/day
    """
    # Seasonal variation: stronger in winter
    season_phase = 2 * np.pi * day_of_year / 365.0
    seasonal_factor = 1.0 + 0.5 * np.cos(season_phase)

    # Latitude dependence: stronger at mid-latitudes (30-50N)
    lat_factor = np.exp(-((lat - 40)**2) / (2 * 10**2))

    u_wind = strength * seasonal_factor * lat_factor
    return u_wind

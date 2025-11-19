"""
Synthetic demo for presentation, not scientific output.

Physics engine for ocean drift simulation with North Atlantic gyre,
Gulf Stream, windage, diffusion, and beaching mechanics.
"""

import numpy as np
from typing import Tuple, Optional

class OceanPhysics:
    """
    Offline kinematic ocean field with synthetic but plausible physics.
    Implements:
    - Clockwise subtropical gyre (centered ~30N, 40W)
    - Western boundary current (Gulf Stream) along US coast
    - Trade wind windage (10N-30N)
    - Isotropic diffusion for turbulence
    - Land masking and beaching probability
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)

        # Gyre parameters
        self.gyre_center_lat = 30.0
        self.gyre_center_lon = -40.0
        self.gyre_radius = 20.0  # degrees
        self.gyre_strength = 0.5  # m/s at peak

        # Gulf Stream parameters
        self.gulf_stream_strength = 2.0  # m/s
        self.gulf_stream_width = 2.0  # degrees

        # Windage parameters
        self.windage_fraction = 0.03
        self.wind_u = -5.0  # m/s, trade winds (westward)
        self.wind_v = 2.0   # m/s, slight northward component

        # Diffusion parameters
        self.diffusion_coefficient = 100.0  # m^2/s

        # Beaching parameters
        self.beach_probability = 0.15  # per week near shore
        self.shore_distance = 1.0  # degrees

        # Time step (weekly)
        self.dt = 7 * 24 * 3600  # seconds per week

        # Constants
        self.earth_radius = 6371000.0  # meters
        self.deg_to_rad = np.pi / 180.0

    def velocity_field(self, lat: np.ndarray, lon: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute ocean velocity (u, v) in m/s at given positions.

        Args:
            lat: Latitude array (degrees)
            lon: Longitude array (degrees)

        Returns:
            u, v: Velocity components in m/s (eastward, northward)
        """
        # Initialize velocities
        u = np.zeros_like(lat)
        v = np.zeros_like(lat)

        # 1. Subtropical gyre (clockwise circulation)
        u_gyre, v_gyre = self._gyre_velocity(lat, lon)
        u += u_gyre
        v += v_gyre

        # 2. Gulf Stream (western boundary current)
        u_gulf, v_gulf = self._gulf_stream_velocity(lat, lon)
        u += u_gulf
        v += v_gulf

        # 3. North Atlantic Current (continuation of Gulf Stream)
        u_nac, v_nac = self._north_atlantic_current(lat, lon)
        u += u_nac
        v += v_nac

        # 4. Windage component
        u_wind, v_wind = self._windage(lat, lon)
        u += u_wind
        v += v_wind

        return u, v

    def _gyre_velocity(self, lat: np.ndarray, lon: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Clockwise subtropical gyre circulation."""
        # Distance from gyre center
        dlat = lat - self.gyre_center_lat
        dlon = lon - self.gyre_center_lon

        # Normalized distance
        r = np.sqrt(dlat**2 + dlon**2) / self.gyre_radius

        # Velocity magnitude (Gaussian profile)
        vmag = self.gyre_strength * np.exp(-r**2)

        # Tangential velocity (clockwise)
        # At gyre center: no velocity
        # Velocity perpendicular to radius vector
        angle = np.arctan2(dlat, dlon)
        u = -vmag * np.sin(angle)  # Clockwise rotation
        v = vmag * np.cos(angle)

        return u, v

    def _gulf_stream_velocity(self, lat: np.ndarray, lon: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Western boundary current (Gulf Stream) along US coast.
        Flows northward along coast, then turns eastward around 40N.
        """
        u = np.zeros_like(lat)
        v = np.zeros_like(lat)

        # Gulf Stream path: follows coast from Florida to Cape Hatteras,
        # then veers northeast

        # Southern section (25N-35N): mainly northward along ~75W
        mask_south = (lat >= 25) & (lat <= 35) & (lon >= -80) & (lon <= -70)
        dist_from_coast_south = np.abs(lon + 75)
        stream_profile_south = np.exp(-(dist_from_coast_south / self.gulf_stream_width)**2)
        v[mask_south] += self.gulf_stream_strength * stream_profile_south[mask_south]
        u[mask_south] += 0.3 * self.gulf_stream_strength * stream_profile_south[mask_south]

        # Northern section (35N-42N): turns northeast
        mask_north = (lat >= 35) & (lat <= 42) & (lon >= -75) & (lon <= -65)
        # Center line moves from (-75, 35) to (-65, 42)
        center_lon = -75 + (lat - 35) * (10 / 7)
        dist_from_center = np.abs(lon - center_lon)
        stream_profile_north = np.exp(-(dist_from_center / self.gulf_stream_width)**2)
        v[mask_north] += 0.7 * self.gulf_stream_strength * stream_profile_north[mask_north]
        u[mask_north] += 1.5 * self.gulf_stream_strength * stream_profile_north[mask_north]

        return u, v

    def _north_atlantic_current(self, lat: np.ndarray, lon: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        North Atlantic Current (continuation of Gulf Stream toward Europe).
        """
        u = np.zeros_like(lat)
        v = np.zeros_like(lat)

        # NAC flows eastward between 40N-55N
        mask = (lat >= 40) & (lat <= 55) & (lon >= -50) & (lon <= -10)

        # Velocity decreases with distance from Gulf Stream
        lat_center = 47.0
        lat_profile = np.exp(-((lat - lat_center) / 5.0)**2)

        u[mask] += 0.8 * self.gulf_stream_strength * lat_profile[mask]
        v[mask] += 0.1 * self.gulf_stream_strength * lat_profile[mask]

        return u, v

    def _windage(self, lat: np.ndarray, lon: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Windage component (trade winds between 10N-30N).
        """
        u = np.zeros_like(lat)
        v = np.zeros_like(lat)

        # Trade wind belt (10N-30N)
        mask = (lat >= 10) & (lat <= 30)

        # Smooth transition
        weight = np.zeros_like(lat)
        weight[mask] = 1.0 - np.abs(lat[mask] - 20) / 10.0
        weight = np.maximum(weight, 0.0)

        u += self.windage_fraction * self.wind_u * weight
        v += self.windage_fraction * self.wind_v * weight

        return u, v

    def diffusion_step(self, n_particles: int) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate random displacement for diffusion (Brownian motion).

        Args:
            n_particles: Number of particles

        Returns:
            du, dv: Displacement in meters (eastward, northward)
        """
        sigma = np.sqrt(2 * self.diffusion_coefficient * self.dt)
        du = self.rng.normal(0, sigma, n_particles)
        dv = self.rng.normal(0, sigma, n_particles)
        return du, dv

    def meters_to_degrees(self, lat: np.ndarray, dx_m: np.ndarray, dy_m: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert displacement in meters to degrees.

        Args:
            lat: Latitude in degrees
            dx_m: Eastward displacement in meters
            dy_m: Northward displacement in meters

        Returns:
            dlon, dlat: Displacement in degrees
        """
        # Latitude is straightforward
        dlat = dy_m / (self.earth_radius * self.deg_to_rad)

        # Longitude depends on latitude
        lat_rad = lat * self.deg_to_rad
        dlon = dx_m / (self.earth_radius * np.cos(lat_rad) * self.deg_to_rad + 1e-10)

        return dlon, dlat

    def is_on_land(self, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
        """
        Simple land mask for North Atlantic basin.

        Args:
            lat, lon: Position arrays

        Returns:
            Boolean array indicating land positions
        """
        on_land = np.zeros(len(lat), dtype=bool)

        # North America (rough polygon)
        # East coast: blocks west of certain longitudes at each latitude
        na_mask = (lat >= 25) & (lat <= 60)

        # Define east coast boundary (longitude vs latitude)
        # Florida to Newfoundland
        east_coast_lon = np.interp(
            lat,
            [25, 30, 35, 40, 45, 50, 55, 60],
            [-80, -81, -76, -74, -67, -60, -57, -55]
        )
        on_land |= na_mask & (lon < east_coast_lon)

        # Europe and Africa (rough polygon)
        # West coast: blocks east of certain longitudes
        eu_mask = (lat >= 10) & (lat <= 60)

        # Define west coast boundary for Europe/Africa
        west_coast_lon = np.interp(
            lat,
            [10, 20, 30, 35, 40, 45, 50, 55, 60],
            [-17, -16, -9, -9, -9, -2, -5, -7, -10]
        )
        on_land |= eu_mask & (lon > west_coast_lon)

        # Mediterranean (block area east of ~0E, north of 35N, south of 45N)
        med_mask = (lat >= 30) & (lat <= 46) & (lon >= 0) & (lon <= 36)
        on_land |= med_mask

        # Caribbean (rough block)
        carib_mask = (lat >= 10) & (lat <= 25) & (lon >= -85) & (lon <= -60)
        on_land |= carib_mask

        return on_land

    def near_shore(self, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
        """
        Identify particles near shore (within shore_distance degrees of land).

        Args:
            lat, lon: Position arrays

        Returns:
            Boolean array indicating near-shore positions
        """
        # Check points in a small grid around each particle
        near = np.zeros(len(lat), dtype=bool)

        offsets = np.linspace(-self.shore_distance, self.shore_distance, 5)

        for dlat in offsets:
            for dlon in offsets:
                check_lat = lat + dlat
                check_lon = lon + dlon
                on_land = self.is_on_land(check_lat, check_lon)
                near |= on_land

        return near

    def check_beaching(self, lat: np.ndarray, lon: np.ndarray, is_beached: np.ndarray) -> np.ndarray:
        """
        Probabilistically beach particles near shore.

        Args:
            lat, lon: Current positions
            is_beached: Current beaching status

        Returns:
            Updated beaching status
        """
        # Only check active particles
        active = ~is_beached

        if not np.any(active):
            return is_beached

        # Check if near shore
        near = self.near_shore(lat[active], lon[active])

        # Probabilistic beaching
        beach_roll = self.rng.random(np.sum(active))
        newly_beached = near & (beach_roll < self.beach_probability)

        # Update beaching status
        is_beached_new = is_beached.copy()
        active_indices = np.where(active)[0]
        is_beached_new[active_indices[newly_beached]] = True

        return is_beached_new

    def rk4_step(self, lat: np.ndarray, lon: np.ndarray, is_beached: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        RK4 integration step for particle positions.

        Args:
            lat, lon: Current positions (degrees)
            is_beached: Boolean array of beached particles

        Returns:
            new_lat, new_lon: Updated positions (degrees)
        """
        # Only advance active particles
        active = ~is_beached

        if not np.any(active):
            return lat.copy(), lon.copy()

        # Work with active particles
        lat_active = lat[active]
        lon_active = lon[active]
        n_active = len(lat_active)

        # K1
        u1, v1 = self.velocity_field(lat_active, lon_active)
        du1, dv1 = self.diffusion_step(n_active)
        dx1 = u1 * self.dt + du1
        dy1 = v1 * self.dt + dv1
        dlon1, dlat1 = self.meters_to_degrees(lat_active, dx1, dy1)

        # K2
        lat2 = lat_active + 0.5 * dlat1
        lon2 = lon_active + 0.5 * dlon1
        u2, v2 = self.velocity_field(lat2, lon2)
        du2, dv2 = self.diffusion_step(n_active)
        dx2 = u2 * self.dt + du2
        dy2 = v2 * self.dt + dv2
        dlon2, dlat2 = self.meters_to_degrees(lat2, dx2, dy2)

        # K3
        lat3 = lat_active + 0.5 * dlat2
        lon3 = lon_active + 0.5 * dlon2
        u3, v3 = self.velocity_field(lat3, lon3)
        du3, dv3 = self.diffusion_step(n_active)
        dx3 = u3 * self.dt + du3
        dy3 = v3 * self.dt + dv3
        dlon3, dlat3 = self.meters_to_degrees(lat3, dx3, dy3)

        # K4
        lat4 = lat_active + dlat3
        lon4 = lon_active + dlon3
        u4, v4 = self.velocity_field(lat4, lon4)
        du4, dv4 = self.diffusion_step(n_active)
        dx4 = u4 * self.dt + du4
        dy4 = v4 * self.dt + dv4
        dlon4, dlat4 = self.meters_to_degrees(lat4, dx4, dy4)

        # Combine
        dlon = (dlon1 + 2*dlon2 + 2*dlon3 + dlon4) / 6.0
        dlat = (dlat1 + 2*dlat2 + 2*dlat3 + dlat4) / 6.0

        # Update positions
        new_lat = lat.copy()
        new_lon = lon.copy()
        new_lat[active] += dlat
        new_lon[active] += dlon

        # Ensure particles stay in valid range
        new_lat = np.clip(new_lat, -90, 90)
        new_lon = np.where(new_lon < -180, new_lon + 360, new_lon)
        new_lon = np.where(new_lon > 180, new_lon - 360, new_lon)

        return new_lat, new_lon

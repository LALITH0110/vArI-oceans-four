"""
Synthetic demo for presentation, not scientific output.

FIXED: Physics engine with proper beaching logic and offshore spawning.
"""

import numpy as np
from typing import Tuple

class OceanPhysics:
    """
    Offline kinematic ocean field with synthetic but plausible physics.
    FIXES:
    - Beaching only within 15km of coast AND after 4 weeks minimum
    - Proper distance-to-coast calculation
    - Offshore spawning validation
    """

    def __init__(self, seed: int = 42):
        self.rng = np.random.RandomState(seed)

        # Gyre parameters
        self.gyre_center_lat = 30.0
        self.gyre_center_lon = -40.0
        self.gyre_radius = 20.0
        self.gyre_strength = 0.5  # m/s

        # Gulf Stream parameters
        self.gulf_stream_strength = 2.0  # m/s
        self.gulf_stream_width = 2.0  # degrees

        # Windage parameters
        self.windage_fraction = 0.03
        self.wind_u = -5.0  # m/s
        self.wind_v = 2.0   # m/s

        # Diffusion parameters
        self.diffusion_coefficient = 100.0  # m^2/s

        # FIXED: Beaching parameters
        self.beach_probability = 0.15  # per week near shore
        self.beach_distance_km = 15.0  # FIXED: 15 km, not 111 km!
        self.beach_min_weeks = 4  # FIXED: minimum 4 weeks before beaching

        # Time step (weekly)
        self.dt = 7 * 24 * 3600  # seconds

        # Constants
        self.earth_radius = 6371000.0  # meters
        self.deg_to_rad = np.pi / 180.0
        self.deg_to_km = 111.32  # km per degree latitude

    def velocity_field(self, lat: np.ndarray, lon: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Compute ocean velocity (u, v) in m/s at given positions."""
        u = np.zeros_like(lat, dtype=float)
        v = np.zeros_like(lat, dtype=float)

        # 1. Subtropical gyre (clockwise)
        u_gyre, v_gyre = self._gyre_velocity(lat, lon)
        u += u_gyre
        v += v_gyre

        # 2. Gulf Stream
        u_gulf, v_gulf = self._gulf_stream_velocity(lat, lon)
        u += u_gulf
        v += v_gulf

        # 3. North Atlantic Current
        u_nac, v_nac = self._north_atlantic_current(lat, lon)
        u += u_nac
        v += v_nac

        # 4. Windage
        u_wind, v_wind = self._windage(lat, lon)
        u += u_wind
        v += v_wind

        return u, v

    def _gyre_velocity(self, lat: np.ndarray, lon: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Clockwise subtropical gyre circulation."""
        dlat = lat - self.gyre_center_lat
        dlon = lon - self.gyre_center_lon
        r = np.sqrt(dlat**2 + dlon**2) / self.gyre_radius
        vmag = self.gyre_strength * np.exp(-r**2)
        angle = np.arctan2(dlat, dlon)
        u = -vmag * np.sin(angle)  # Clockwise
        v = vmag * np.cos(angle)
        return u, v

    def _gulf_stream_velocity(self, lat: np.ndarray, lon: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Gulf Stream along US coast."""
        u = np.zeros_like(lat, dtype=float)
        v = np.zeros_like(lat, dtype=float)

        # Southern section (25N-35N)
        mask_south = (lat >= 25) & (lat <= 35) & (lon >= -80) & (lon <= -70)
        dist_south = np.abs(lon + 75)
        profile_south = np.exp(-(dist_south / self.gulf_stream_width)**2)
        v[mask_south] += self.gulf_stream_strength * profile_south[mask_south]
        u[mask_south] += 0.3 * self.gulf_stream_strength * profile_south[mask_south]

        # Northern section (35N-42N)
        mask_north = (lat >= 35) & (lat <= 42) & (lon >= -75) & (lon <= -65)
        center_lon = -75 + (lat - 35) * (10 / 7)
        dist_north = np.abs(lon - center_lon)
        profile_north = np.exp(-(dist_north / self.gulf_stream_width)**2)
        v[mask_north] += 0.7 * self.gulf_stream_strength * profile_north[mask_north]
        u[mask_north] += 1.5 * self.gulf_stream_strength * profile_north[mask_north]

        return u, v

    def _north_atlantic_current(self, lat: np.ndarray, lon: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """North Atlantic Current toward Europe."""
        u = np.zeros_like(lat, dtype=float)
        v = np.zeros_like(lat, dtype=float)

        mask = (lat >= 40) & (lat <= 55) & (lon >= -50) & (lon <= -10)
        lat_center = 47.0
        lat_profile = np.exp(-((lat - lat_center) / 5.0)**2)
        u[mask] += 0.8 * self.gulf_stream_strength * lat_profile[mask]
        v[mask] += 0.1 * self.gulf_stream_strength * lat_profile[mask]

        return u, v

    def _windage(self, lat: np.ndarray, lon: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Windage from trade winds (10N-30N)."""
        u = np.zeros_like(lat, dtype=float)
        v = np.zeros_like(lat, dtype=float)

        mask = (lat >= 10) & (lat <= 30)
        weight = np.zeros_like(lat, dtype=float)
        weight[mask] = 1.0 - np.abs(lat[mask] - 20) / 10.0
        weight = np.maximum(weight, 0.0)

        u += self.windage_fraction * self.wind_u * weight
        v += self.windage_fraction * self.wind_v * weight

        return u, v

    def diffusion_step(self, n_particles: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate random displacement for diffusion."""
        sigma = np.sqrt(2 * self.diffusion_coefficient * self.dt)
        du = self.rng.normal(0, sigma, n_particles)
        dv = self.rng.normal(0, sigma, n_particles)
        return du, dv

    def meters_to_degrees(self, lat: np.ndarray, dx_m: np.ndarray, dy_m: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Convert displacement in meters to degrees."""
        dlat = dy_m / (self.earth_radius * self.deg_to_rad)
        lat_rad = lat * self.deg_to_rad
        dlon = dx_m / (self.earth_radius * np.cos(lat_rad) * self.deg_to_rad + 1e-10)
        return dlon, dlat

    def is_on_land(self, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
        """Land mask for North Atlantic basin."""
        on_land = np.zeros(len(lat), dtype=bool)

        # North America - everything west of east coast line
        # FIXED: Move coastline further west so NYC offshore waters are ocean
        na_mask = (lat >= 25) & (lat <= 60)
        east_coast_lon = np.interp(
            lat,
            [25, 30, 35, 40, 45, 50, 55, 60],
            [-80.5, -81.5, -77.0, -75.5, -68.0, -61.0, -58.0, -56.0]
        )
        # Mark as land if west of coastline (no buffer needed)
        on_land |= na_mask & (lon < east_coast_lon)

        # Europe and Africa - everything east of west coast line
        eu_mask = (lat >= 10) & (lat <= 60)
        west_coast_lon = np.interp(
            lat,
            [10, 20, 30, 35, 40, 45, 50, 55, 60],
            [-17, -16, -9, -9, -9, -2, -5, -7, -10]
        )
        # FIXED: Add buffer
        on_land |= eu_mask & (lon > (west_coast_lon + 0.2))

        # Mediterranean
        med_mask = (lat >= 30) & (lat <= 46) & (lon >= 0) & (lon <= 36)
        on_land |= med_mask

        # Caribbean
        carib_mask = (lat >= 10) & (lat <= 25) & (lon >= -85) & (lon <= -60)
        on_land |= carib_mask

        return on_land

    def distance_to_coast_km(self, lat: np.ndarray, lon: np.ndarray) -> np.ndarray:
        """
        FIXED: Calculate distance to nearest coast in km.
        Uses sampling approach - checks nearby points.
        """
        n = len(lat)
        min_dist = np.full(n, 999.0)  # Start with large distance

        # Sample points at various offsets (in degrees)
        # 0.5 degree ≈ 55 km, so sample up to ±0.3 degrees
        offsets = np.linspace(-0.3, 0.3, 7)

        for dlat in offsets:
            for dlon in offsets:
                if dlat == 0 and dlon == 0:
                    continue

                check_lat = lat + dlat
                check_lon = lon + dlon
                on_land = self.is_on_land(check_lat, check_lon)

                # Calculate distance to this point
                dist_deg = np.sqrt(dlat**2 + dlon**2)
                dist_km = dist_deg * self.deg_to_km

                # Update minimum distance where land found
                min_dist = np.where(on_land, np.minimum(min_dist, dist_km), min_dist)

        return min_dist

    def check_beaching(self, lat: np.ndarray, lon: np.ndarray, is_beached: np.ndarray,
                      step_number: int) -> np.ndarray:
        """
        FIXED: Probabilistically beach particles near shore ONLY after minimum time.

        Args:
            lat, lon: Current positions
            is_beached: Current beaching status
            step_number: Current simulation step (for minimum time check)

        Returns:
            Updated beaching status
        """
        # Only check active particles
        active = ~is_beached

        if not np.any(active):
            return is_beached

        # FIXED: No beaching before minimum time
        if step_number < self.beach_min_weeks:
            return is_beached

        # FIXED: Calculate actual distance to coast in km
        dist_to_coast = self.distance_to_coast_km(lat[active], lon[active])

        # FIXED: Only beach if within beach_distance_km (15 km)
        near_coast = dist_to_coast <= self.beach_distance_km

        # Probabilistic beaching for particles near coast
        beach_roll = self.rng.random(np.sum(active))
        newly_beached = near_coast & (beach_roll < self.beach_probability)

        # Update beaching status
        is_beached_new = is_beached.copy()
        active_indices = np.where(active)[0]
        is_beached_new[active_indices[newly_beached]] = True

        return is_beached_new

    def rk4_step(self, lat: np.ndarray, lon: np.ndarray, is_beached: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """RK4 integration step for particle positions."""
        active = ~is_beached

        if not np.any(active):
            return lat.copy(), lon.copy()

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

        # Bounds
        new_lat = np.clip(new_lat, -90, 90)
        new_lon = np.where(new_lon < -180, new_lon + 360, new_lon)
        new_lon = np.where(new_lon > 180, new_lon - 360, new_lon)

        return new_lat, new_lon

    def spawn_offshore(self, center_lat: float, center_lon: float, n_particles: int,
                       radius_km: float = 20.0) -> Tuple[np.ndarray, np.ndarray]:
        """
        FIXED: Spawn particles offshore, ensuring they start in ocean.

        Args:
            center_lat, center_lon: Center position
            n_particles: Number of particles
            radius_km: Spawn radius in km

        Returns:
            lat, lon arrays of valid ocean positions
        """
        radius_deg = radius_km / self.deg_to_km

        lat_list = []
        lon_list = []

        attempts = 0
        max_attempts = n_particles * 10

        while len(lat_list) < n_particles and attempts < max_attempts:
            # Generate random positions in circle
            angles = self.rng.random(n_particles - len(lat_list)) * 2 * np.pi
            radii = self.rng.random(n_particles - len(lat_list)) * radius_deg

            # Convert to lat/lon offsets
            dlat = radii * np.cos(angles)
            dlon = radii * np.sin(angles) / np.cos(center_lat * self.deg_to_rad)

            candidate_lat = center_lat + dlat
            candidate_lon = center_lon + dlon

            # Check which are in ocean
            in_ocean = ~self.is_on_land(candidate_lat, candidate_lon)

            # Add valid positions
            lat_list.extend(candidate_lat[in_ocean].tolist())
            lon_list.extend(candidate_lon[in_ocean].tolist())

            attempts += 1

        # Return exactly n_particles (truncate if we got more)
        lat_array = np.array(lat_list[:n_particles])
        lon_array = np.array(lon_list[:n_particles])

        return lat_array, lon_array

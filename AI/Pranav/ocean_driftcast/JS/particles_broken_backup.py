"""
Synthetic demo for presentation, not scientific output.

Particle system for ocean drift simulation with trajectory tracking.
"""

import numpy as np
from typing import Tuple, List, Dict, Optional
from physics import OceanPhysics

class ParticleSystem:
    """
    Manages particle trajectories over time with full history tracking.
    """

    def __init__(self, physics: OceanPhysics, n_particles: int, release_lat: float, release_lon: float, release_radius: float = 0.5):
        """
        Initialize particle system.

        Args:
            physics: OceanPhysics instance
            n_particles: Number of particles to simulate
            release_lat: Release latitude (degrees)
            release_lon: Release longitude (degrees)
            release_radius: Spread radius for initial positions (degrees)
        """
        self.physics = physics
        self.n_particles = n_particles
        self.release_lat = release_lat
        self.release_lon = release_lon
        self.release_radius = release_radius

        # Initialize particle positions in circular release pattern
        angles = physics.rng.random(n_particles) * 2 * np.pi
        radii = physics.rng.random(n_particles) * release_radius

        self.lat = release_lat + radii * np.cos(angles)
        self.lon = release_lon + radii * np.sin(angles)

        # Particle state
        self.is_beached = np.zeros(n_particles, dtype=bool)

        # Trajectory history
        self.history_lat = [self.lat.copy()]
        self.history_lon = [self.lon.copy()]
        self.history_beached = [self.is_beached.copy()]

        # Metrics
        self.step_count = 0
        self.total_distance = np.zeros(n_particles)  # km

    def step(self):
        """
        Advance simulation by one time step.
        """
        # Store previous positions for distance calculation
        prev_lat = self.lat.copy()
        prev_lon = self.lon.copy()

        # RK4 integration
        self.lat, self.lon = self.physics.rk4_step(self.lat, self.lon, self.is_beached)

        # Check for beaching
        self.is_beached = self.physics.check_beaching(self.lat, self.lon, self.is_beached)

        # Calculate distance traveled
        active = ~self.is_beached
        if np.any(active):
            dlat = self.lat[active] - prev_lat[active]
            dlon = self.lon[active] - prev_lon[active]

            # Convert to meters using haversine approximation
            lat_rad = prev_lat[active] * np.pi / 180
            dx = dlon * np.cos(lat_rad) * 111.32  # km per degree longitude
            dy = dlat * 111.32  # km per degree latitude
            dist = np.sqrt(dx**2 + dy**2)

            self.total_distance[active] += dist

        # Store history
        self.history_lat.append(self.lat.copy())
        self.history_lon.append(self.lon.copy())
        self.history_beached.append(self.is_beached.copy())

        self.step_count += 1

    def simulate(self, n_steps: int, callback: Optional[callable] = None):
        """
        Run simulation for n_steps.

        Args:
            n_steps: Number of time steps
            callback: Optional callback function called after each step
        """
        for i in range(n_steps):
            self.step()

            if callback is not None:
                callback(i, self)

    def get_metrics(self) -> Dict:
        """
        Calculate summary metrics.

        Returns:
            Dictionary with metrics
        """
        n_beached = np.sum(self.is_beached)
        n_ocean = self.n_particles - n_beached

        # Ocean reach probability (never beached during simulation)
        ocean_reach_prob = n_ocean / self.n_particles

        # Median distance
        median_distance_km = np.median(self.total_distance)

        # Distance statistics
        mean_distance_km = np.mean(self.total_distance)
        max_distance_km = np.max(self.total_distance)

        return {
            'n_particles': self.n_particles,
            'n_beached': int(n_beached),
            'n_ocean': int(n_ocean),
            'beached_fraction': n_beached / self.n_particles,
            'ocean_reach_prob': ocean_reach_prob,
            'median_distance_km': float(median_distance_km),
            'mean_distance_km': float(mean_distance_km),
            'max_distance_km': float(max_distance_km),
            'n_steps': self.step_count,
            'years': self.step_count / 52.0
        }

    def get_probability_category(self) -> str:
        """
        Get probability category (LOW/MEDIUM/HIGH) based on ocean reach.

        Returns:
            Category string
        """
        metrics = self.get_metrics()
        prob = metrics['ocean_reach_prob']

        if prob < 0.3:
            return "LOW"
        elif prob < 0.6:
            return "MEDIUM"
        else:
            return "HIGH"

    def get_trajectory_arrays(self, subsample: int = 1) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """
        Get trajectory history as arrays.

        Args:
            subsample: Sample every N time steps

        Returns:
            List of lat arrays, List of lon arrays (one per particle)
        """
        trajectories_lat = []
        trajectories_lon = []

        for i in range(self.n_particles):
            traj_lat = np.array([self.history_lat[t][i] for t in range(0, len(self.history_lat), subsample)])
            traj_lon = np.array([self.history_lon[t][i] for t in range(0, len(self.history_lon), subsample)])

            trajectories_lat.append(traj_lat)
            trajectories_lon.append(traj_lon)

        return trajectories_lat, trajectories_lon

    def get_current_positions(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get current particle positions and status.

        Returns:
            lat, lon, is_beached
        """
        return self.lat.copy(), self.lon.copy(), self.is_beached.copy()

    def get_positions_at_step(self, step: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get particle positions at a specific time step.

        Args:
            step: Time step index

        Returns:
            lat, lon, is_beached at that step
        """
        if step < 0 or step >= len(self.history_lat):
            raise ValueError(f"Step {step} out of range [0, {len(self.history_lat)-1}]")

        return (
            self.history_lat[step].copy(),
            self.history_lon[step].copy(),
            self.history_beached[step].copy()
        )

    def get_density_heatmap(self, lat_bins: int = 100, lon_bins: int = 100) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate particle density heatmap over all time steps.

        Args:
            lat_bins: Number of latitude bins
            lon_bins: Number of longitude bins

        Returns:
            density: 2D histogram
            lat_edges: Latitude bin edges
            lon_edges: Longitude bin edges
        """
        # Concatenate all positions
        all_lat = np.concatenate(self.history_lat)
        all_lon = np.concatenate(self.history_lon)

        # Create 2D histogram
        lat_range = (5, 65)
        lon_range = (-100, 20)

        density, lat_edges, lon_edges = np.histogram2d(
            all_lat, all_lon,
            bins=[lat_bins, lon_bins],
            range=[lat_range, lon_range]
        )

        return density.T, lat_edges, lon_edges


def create_particle_system_from_city(physics: OceanPhysics, city_data: Dict, n_particles: int = 5000) -> ParticleSystem:
    """
    Create a particle system from city data, handling inland cities.

    Args:
        physics: OceanPhysics instance
        city_data: City dictionary from seeds.json
        n_particles: Number of particles

    Returns:
        ParticleSystem instance
    """
    lat = city_data['lat']
    lon = city_data['lon']

    # For inland cities, use ocean outlet
    if city_data.get('type') == 'inland' and 'outlet' in city_data:
        lat = city_data['outlet']['lat']
        lon = city_data['outlet']['lon']
        release_radius = 1.0  # Larger spread for inland outlets
    else:
        release_radius = 0.5

    return ParticleSystem(physics, n_particles, lat, lon, release_radius)

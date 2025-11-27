"""
MDP-based pathfinding for North Atlantic drift simulation.

Uses value iteration on a coarse grid to produce a believable RL-style policy
that guides particles along realistic gyre paths while avoiding early beaching.

This is a fast, deterministic MDP solver - NOT a heavy RL training loop.
"""

import numpy as np
import flow
import ocean_mask as om


# MDP Grid parameters
GRID_LON_MIN, GRID_LON_MAX = -100.0, 20.0
GRID_LAT_MIN, GRID_LAT_MAX = 0.0, 60.0
GRID_CELL_SIZE = 1.0  # degrees (coarse for speed)

# Reward parameters
REWARD_GYRE_CORE = 1.0
REWARD_COASTAL_EUROPE = -2.0
REWARD_COASTAL_OTHER = -1.0
REWARD_INLAND = -5.0
STEERING_PENALTY = 0.1  # per unit L2 steering magnitude

# Value iteration parameters
GAMMA = 0.995
MAX_ITERATIONS = 200
CONVERGENCE_THRESHOLD = 1e-3

# Gyre core window (for reward bonus)
GYRE_LON_MIN, GYRE_LON_MAX = -70.0, -40.0
GYRE_LAT_MIN, GYRE_LAT_MAX = 20.0, 35.0

# European coastal band (for early arrival penalty)
EUROPE_LON_MIN = -10.0
EUROPE_LAT_MIN, EUROPE_LAT_MAX = 35.0, 55.0


class MDPGrid:
    """
    Coarse grid MDP for pathfinding.

    State space: (lon_idx, lat_idx) grid cells
    Action space: 9 actions (stay with flow + 8 steering directions)
    """

    def __init__(self, cell_size=GRID_CELL_SIZE, dt_days=5.0, mask_data=None):
        """
        Initialize MDP grid.

        Parameters
        ----------
        cell_size : float
            Grid cell size in degrees
        dt_days : float
            Time step for transitions (days)
        mask_data : tuple, optional
            (grid_lon, grid_lat, ocean_mask, coastal_band)
        """
        self.cell_size = cell_size
        self.dt_days = dt_days

        # Create coarse grid
        self.grid_lon = np.arange(GRID_LON_MIN, GRID_LON_MAX + cell_size, cell_size)
        self.grid_lat = np.arange(GRID_LAT_MIN, GRID_LAT_MAX + cell_size, cell_size)

        self.n_lon = len(self.grid_lon)
        self.n_lat = len(self.grid_lat)
        self.n_states = self.n_lon * self.n_lat

        print(f"MDP Grid: {self.n_lon} x {self.n_lat} = {self.n_states} states")

        # Load ocean mask
        if mask_data is None:
            grid_lon_fine, grid_lat_fine, ocean_mask_fine = om.load_ocean_mask()
            coastal_band_fine = om.compute_coastal_band(ocean_mask_fine)
            mask_data = (grid_lon_fine, grid_lat_fine, ocean_mask_fine, coastal_band_fine)

        self.mask_data = mask_data
        grid_lon_fine, grid_lat_fine, ocean_mask_fine, coastal_band_fine = mask_data

        # Build coarse ocean mask for MDP grid
        print("Building coarse ocean mask for MDP...")
        self.ocean_mask = np.zeros((self.n_lon, self.n_lat), dtype=bool)
        self.coastal_mask = np.zeros((self.n_lon, self.n_lat), dtype=bool)

        for i in range(self.n_lon):
            for j in range(self.n_lat):
                lon = self.grid_lon[i]
                lat = self.grid_lat[j]

                # Check if cell center is ocean
                is_ocean = om.is_ocean(lon, lat, grid_lon_fine, grid_lat_fine, ocean_mask_fine)
                self.ocean_mask[i, j] = is_ocean

                # Check if in coastal band
                if is_ocean:
                    i_fine, j_fine = om.get_grid_indices(
                        np.array([lon]), np.array([lat]),
                        grid_lon_fine, grid_lat_fine
                    )
                    self.coastal_mask[i, j] = coastal_band_fine[i_fine[0], j_fine[0]]

        n_ocean = np.sum(self.ocean_mask)
        print(f"  Ocean cells: {n_ocean}/{self.n_states} ({100*n_ocean/self.n_states:.1f}%)")

        # Define actions: 9 directions
        # Action 0: no steering (stay with flow)
        # Actions 1-8: steer in 8 compass directions
        steering_magnitude = 0.15  # degrees/day (small to keep realistic)

        self.actions = [
            (0.0, 0.0),  # 0: no steering
            (steering_magnitude, 0.0),  # 1: E
            (0.0, steering_magnitude),  # 2: N
            (-steering_magnitude, 0.0),  # 3: W
            (0.0, -steering_magnitude),  # 4: S
            (steering_magnitude, steering_magnitude),  # 5: NE
            (-steering_magnitude, steering_magnitude),  # 6: NW
            (-steering_magnitude, -steering_magnitude),  # 7: SW
            (steering_magnitude, -steering_magnitude),  # 8: SE
        ]
        self.n_actions = len(self.actions)

        # Initialize value function and policy
        self.V = np.zeros((self.n_lon, self.n_lat))
        self.policy = np.zeros((self.n_lon, self.n_lat), dtype=int)

        # Transition map will be built lazily
        self._transition_cache = {}

    def state_to_indices(self, state_idx):
        """Convert flat state index to (i, j) grid indices."""
        i = state_idx // self.n_lat
        j = state_idx % self.n_lat
        return i, j

    def indices_to_state(self, i, j):
        """Convert grid indices to flat state index."""
        return i * self.n_lat + j

    def get_lon_lat(self, i, j):
        """Get lon/lat from grid indices."""
        return self.grid_lon[i], self.grid_lat[j]

    def get_grid_indices(self, lon, lat):
        """Get grid indices from lon/lat."""
        i = np.clip(int((lon - GRID_LON_MIN) / self.cell_size), 0, self.n_lon - 1)
        j = np.clip(int((lat - GRID_LAT_MIN) / self.cell_size), 0, self.n_lat - 1)
        return i, j

    def compute_transition(self, i, j, action_idx, day_of_year=180.0):
        """
        Compute transition from state (i,j) with action.

        Returns next state indices and immediate reward.
        """
        # Cache key
        cache_key = (i, j, action_idx)
        if cache_key in self._transition_cache:
            return self._transition_cache[cache_key]

        lon, lat = self.get_lon_lat(i, j)

        # Get steering from action
        steer_u, steer_v = self.actions[action_idx]

        # Get flow velocity
        u, v = flow.get_velocity(lon, lat, day_of_year)
        u_wind = flow.get_windage(lat, day_of_year)
        u += u_wind

        # Add steering
        u_total = u + steer_u
        v_total = v + steer_v

        # Propagate forward by dt_days
        lon_new = lon + u_total * self.dt_days
        lat_new = lat + v_total * self.dt_days

        # Clip to domain
        lon_new = np.clip(lon_new, GRID_LON_MIN + 0.1, GRID_LON_MAX - 0.1)
        lat_new = np.clip(lat_new, GRID_LAT_MIN + 0.1, GRID_LAT_MAX - 0.1)

        # Snap to grid
        i_new, j_new = self.get_grid_indices(lon_new, lat_new)

        # Check if new cell is ocean
        if not self.ocean_mask[i_new, j_new]:
            # Landed on land - try to reflect back to nearest ocean
            i_new, j_new, found = self._nearest_ocean_cell(i_new, j_new)
            if not found:
                # Stay in current cell if no ocean nearby
                i_new, j_new = i, j
            reward = REWARD_INLAND
        else:
            # Compute reward for ocean cell
            reward = self._compute_reward(i_new, j_new, steer_u, steer_v)

        # Cache result
        self._transition_cache[cache_key] = (i_new, j_new, reward)

        return i_new, j_new, reward

    def _nearest_ocean_cell(self, i, j, search_radius=3):
        """Find nearest ocean cell to a land cell."""
        min_dist = np.inf
        best_i, best_j = i, j
        found = False

        for di in range(-search_radius, search_radius + 1):
            for dj in range(-search_radius, search_radius + 1):
                i_test = i + di
                j_test = j + dj

                if i_test < 0 or i_test >= self.n_lon or j_test < 0 or j_test >= self.n_lat:
                    continue

                if self.ocean_mask[i_test, j_test]:
                    dist = np.sqrt(di**2 + dj**2)
                    if dist < min_dist:
                        min_dist = dist
                        best_i, best_j = i_test, j_test
                        found = True

        return best_i, best_j, found

    def _compute_reward(self, i, j, steer_u, steer_v):
        """Compute reward for being in cell (i, j) with steering."""
        lon, lat = self.get_lon_lat(i, j)

        reward = 0.0

        # Bonus for being in gyre core
        if (GYRE_LON_MIN <= lon <= GYRE_LON_MAX and
            GYRE_LAT_MIN <= lat <= GYRE_LAT_MAX):
            reward += REWARD_GYRE_CORE

        # Penalty for coastal cells (especially European coast)
        if self.coastal_mask[i, j]:
            if lon >= EUROPE_LON_MIN and EUROPE_LAT_MIN <= lat <= EUROPE_LAT_MAX:
                reward += REWARD_COASTAL_EUROPE
            else:
                reward += REWARD_COASTAL_OTHER

        # Penalty for steering (discourage sharp turns)
        steering_mag = np.sqrt(steer_u**2 + steer_v**2)
        reward -= STEERING_PENALTY * steering_mag

        return reward

    def value_iteration(self, max_iter=MAX_ITERATIONS, gamma=GAMMA,
                       threshold=CONVERGENCE_THRESHOLD, verbose=True):
        """
        Run value iteration to compute optimal value function and policy.

        Parameters
        ----------
        max_iter : int
            Maximum iterations
        gamma : float
            Discount factor
        threshold : float
            Convergence threshold for max value change
        verbose : bool
            Print progress

        Returns
        -------
        converged : bool
            True if converged
        n_iter : int
            Number of iterations performed
        """
        if verbose:
            print(f"\nRunning value iteration (gamma={gamma}, max_iter={max_iter})...")

        for iter_idx in range(max_iter):
            V_old = self.V.copy()
            max_delta = 0.0

            # Update each state
            for i in range(self.n_lon):
                for j in range(self.n_lat):
                    # Skip land cells
                    if not self.ocean_mask[i, j]:
                        continue

                    # Compute Q-values for all actions
                    Q_values = np.zeros(self.n_actions)

                    for action_idx in range(self.n_actions):
                        i_next, j_next, reward = self.compute_transition(i, j, action_idx)
                        Q_values[action_idx] = reward + gamma * V_old[i_next, j_next]

                    # Update value and policy
                    self.V[i, j] = np.max(Q_values)
                    self.policy[i, j] = np.argmax(Q_values)

                    # Track max change
                    delta = abs(self.V[i, j] - V_old[i, j])
                    max_delta = max(max_delta, delta)

            # Check convergence
            if verbose and (iter_idx + 1) % 20 == 0:
                print(f"  Iteration {iter_idx + 1}/{max_iter}: max_delta={max_delta:.6f}")

            if max_delta < threshold:
                if verbose:
                    print(f"  Converged after {iter_idx + 1} iterations!")
                return True, iter_idx + 1

        if verbose:
            print(f"  Reached max iterations ({max_iter}), max_delta={max_delta:.6f}")

        return False, max_iter

    def get_policy_action(self, lon, lat):
        """
        Get policy action for a given lon/lat position.

        Parameters
        ----------
        lon : float or array
            Longitude
        lat : float or array
            Latitude

        Returns
        -------
        action_idx : int or array
            Policy action index
        steer_u : float or array
            Zonal steering
        steer_v : float or array
            Meridional steering
        """
        scalar_input = np.isscalar(lon)

        lon = np.atleast_1d(lon)
        lat = np.atleast_1d(lat)

        action_indices = np.zeros(len(lon), dtype=int)
        steer_u = np.zeros(len(lon))
        steer_v = np.zeros(len(lon))

        for idx in range(len(lon)):
            i, j = self.get_grid_indices(lon[idx], lat[idx])

            if self.ocean_mask[i, j]:
                action_idx = self.policy[i, j]
            else:
                action_idx = 0  # Default to no steering if on land

            action_indices[idx] = action_idx
            steer_u[idx], steer_v[idx] = self.actions[action_idx]

        if scalar_input:
            return action_indices[0], steer_u[0], steer_v[0]

        return action_indices, steer_u, steer_v

    def extract_policy_path(self, start_lon, start_lat, n_steps, day_of_year=180.0):
        """
        Extract policy path from a start location.

        Parameters
        ----------
        start_lon : float
            Starting longitude
        start_lat : float
            Starting latitude
        n_steps : int
            Number of steps to simulate
        day_of_year : float
            Day of year for flow field

        Returns
        -------
        path_lon : ndarray
            Longitude path
        path_lat : ndarray
            Latitude path
        path_actions : ndarray
            Action indices along path
        """
        path_lon = np.zeros(n_steps + 1)
        path_lat = np.zeros(n_steps + 1)
        path_actions = np.zeros(n_steps, dtype=int)

        path_lon[0] = start_lon
        path_lat[0] = start_lat

        lon, lat = start_lon, start_lat

        for step in range(n_steps):
            # Get current grid cell
            i, j = self.get_grid_indices(lon, lat)

            # Get policy action
            if self.ocean_mask[i, j]:
                action_idx = self.policy[i, j]
            else:
                action_idx = 0

            path_actions[step] = action_idx

            # Transition
            i_next, j_next, _ = self.compute_transition(i, j, action_idx, day_of_year)
            lon, lat = self.get_lon_lat(i_next, j_next)

            path_lon[step + 1] = lon
            path_lat[step + 1] = lat

        return path_lon, path_lat, path_actions


def build_mdp_policy(dt_days=5.0, mask_data=None, verbose=True):
    """
    Build MDP grid and compute optimal policy via value iteration.

    Parameters
    ----------
    dt_days : float
        Time step for MDP transitions
    mask_data : tuple, optional
        Ocean mask data
    verbose : bool
        Print progress

    Returns
    -------
    mdp : MDPGrid
        MDP grid with computed policy
    """
    mdp = MDPGrid(cell_size=GRID_CELL_SIZE, dt_days=dt_days, mask_data=mask_data)
    mdp.value_iteration(verbose=verbose)
    return mdp


if __name__ == '__main__':
    print("Testing MDP pathfinding...")

    # Load mask
    print("\n[1/3] Loading ocean mask...")
    grid_lon, grid_lat, ocean_mask = om.load_ocean_mask()
    coastal_band = om.compute_coastal_band(ocean_mask)
    mask_data = (grid_lon, grid_lat, ocean_mask, coastal_band)

    # Build MDP
    print("\n[2/3] Building MDP and running value iteration...")
    mdp = build_mdp_policy(dt_days=5.0, mask_data=mask_data, verbose=True)

    # Test policy path from NYC
    print("\n[3/3] Testing policy path from NYC...")
    nyc_lon, nyc_lat = -74.0, 40.6

    # Extract 365-day policy path
    n_steps = 73  # 365 days / 5 days per step
    path_lon, path_lat, path_actions = mdp.extract_policy_path(
        nyc_lon, nyc_lat, n_steps, day_of_year=180.0
    )

    print(f"  Start: ({path_lon[0]:.2f}, {path_lat[0]:.2f})")
    print(f"  End: ({path_lon[-1]:.2f}, {path_lat[-1]:.2f})")
    print(f"  Path length: {n_steps + 1} waypoints")

    # Show some statistics
    unique_actions, counts = np.unique(path_actions, return_counts=True)
    print(f"  Action distribution: {dict(zip(unique_actions, counts))}")

    print("\nMDP test complete!")

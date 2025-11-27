"""
Simple RL-style scheduler for optimizing particle release timing.

Implements an epsilon-greedy contextual bandit to find the best release month
that minimizes beaching while maximizing gyre residence time.

This is a toy example for demonstration, not a rigorous scientific optimization.
"""

import numpy as np
import scenarios
import simulate


class MonthBandit:
    """
    Simple epsilon-greedy bandit for selecting release months.

    State: month index (0-11)
    Action: choose a month
    Reward: 1.0 - beach_fraction + 0.3 * gyre_time_score

    Both beach_fraction and gyre_time_score are normalized to [0,1].
    """

    def __init__(self, n_months=12, epsilon=0.2, seed=None):
        """
        Initialize bandit.

        Parameters
        ----------
        n_months : int
            Number of months (default 12)
        epsilon : float
            Exploration rate (default 0.2)
        seed : int, optional
            Random seed
        """
        self.n_months = n_months
        self.epsilon = epsilon
        self.seed = seed

        if seed is not None:
            np.random.seed(seed)

        # Initialize Q-values (expected reward for each month)
        self.Q = np.zeros(n_months)

        # Visit counts
        self.N = np.zeros(n_months, dtype=int)

        # Reward history
        self.reward_history = []
        self.month_history = []

    def select_month(self):
        """
        Select month using epsilon-greedy policy.

        Returns
        -------
        month : int
            Selected month index (0-11)
        """
        if np.random.rand() < self.epsilon:
            # Explore: random month
            month = np.random.randint(0, self.n_months)
        else:
            # Exploit: best month so far
            month = np.argmax(self.Q)

        return month

    def update(self, month, reward):
        """
        Update Q-value for selected month.

        Uses incremental averaging: Q_new = Q_old + (1/N) * (reward - Q_old)

        Parameters
        ----------
        month : int
            Month index
        reward : float
            Observed reward
        """
        self.N[month] += 1
        self.Q[month] += (reward - self.Q[month]) / self.N[month]

        self.reward_history.append(reward)
        self.month_history.append(month)

    def get_best_month(self):
        """
        Get the best month based on learned Q-values.

        Returns
        -------
        best_month : int
            Month index with highest Q-value
        best_q : float
            Q-value of best month
        """
        best_month = np.argmax(self.Q)
        best_q = self.Q[best_month]
        return best_month, best_q


def compute_reward(lon_history, lat_history, beached_history, total_steps):
    """
    Compute reward for a simulation run.

    Reward = 1.0 - beach_fraction + 0.3 * gyre_time_score

    Both components are in [0, 1]:
    - beach_fraction: fraction of particles beached at end
    - gyre_time_score: average fraction of time spent in gyre

    Parameters
    ----------
    lon_history : ndarray (n_times, n_particles)
        Longitude history
    lat_history : ndarray (n_times, n_particles)
        Latitude history
    beached_history : ndarray (n_times, n_particles)
        Beached status history
    total_steps : int
        Total simulation steps

    Returns
    -------
    reward : float
        Total reward
    beach_fraction : float
        Fraction beached
    gyre_time_score : float
        Normalized gyre residence time
    """
    n_particles = lon_history.shape[1]

    # Compute beaching fraction at end
    beach_fraction = np.sum(beached_history[-1]) / n_particles

    # Compute gyre residence time
    residence_times = scenarios.compute_gyre_residence_time(
        lon_history, lat_history, beached_history
    )

    # Normalize by total steps
    gyre_time_score = np.mean(residence_times) / total_steps

    # Clip to [0, 1] (should already be, but safety check)
    beach_fraction = np.clip(beach_fraction, 0.0, 1.0)
    gyre_time_score = np.clip(gyre_time_score, 0.0, 1.0)

    # Compute reward
    reward = (1.0 - beach_fraction) + 0.3 * gyre_time_score

    return reward, beach_fraction, gyre_time_score


def train_bandit(n_episodes=600, particles_per_episode=800, n_steps=365,
                 epsilon=0.2, mask_data=None, seed=None, verbose=True):
    """
    Train epsilon-greedy bandit to find optimal release month.

    Parameters
    ----------
    n_episodes : int
        Number of training episodes (default 600)
    particles_per_episode : int
        Particles per episode (default 800)
    n_steps : int
        Simulation steps per episode (default 365 = 1 year)
    epsilon : float
        Exploration rate (default 0.2)
    mask_data : tuple, optional
        (grid_lon, grid_lat, ocean_mask, coastal_band)
    seed : int, optional
        Random seed
    verbose : bool
        Print progress (default True)

    Returns
    -------
    bandit : MonthBandit
        Trained bandit object
    training_log : dict
        Training log with episodes, rewards, months, etc.
    """
    if verbose:
        print(f"Training bandit: {n_episodes} episodes, {particles_per_episode} particles each")
        print(f"  Epsilon: {epsilon}")
        print(f"  Simulation: {n_steps} steps")

    # Initialize bandit
    bandit = MonthBandit(n_months=12, epsilon=epsilon, seed=seed)

    # Training log
    training_log = {
        'episodes': [],
        'months': [],
        'rewards': [],
        'beach_fractions': [],
        'gyre_scores': [],
        'q_values': [],
        'visit_counts': [],
    }

    month_names = [
        'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
    ]

    # Training loop
    for episode in range(n_episodes):
        # Select month
        month = bandit.select_month()

        # Set random seed for this episode (for reproducibility)
        episode_seed = None if seed is None else seed + episode

        # Generate particles at NYC for this month
        lon_init, lat_init = scenarios.seed_nyc_spill(
            particles_per_episode,
            jitter_km=15.0,
            seed=episode_seed
        )

        # Run simulation (suppress output)
        if episode_seed is not None:
            np.random.seed(episode_seed)

        # Quick simulation with minimal output
        import sys
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()  # Suppress prints

        try:
            results = simulate.run_simulation(
                lon_init, lat_init,
                n_steps=n_steps,
                dt=1.0,
                save_every=max(1, n_steps // 50),  # Save less often for speed
                mask_data=mask_data
            )
        finally:
            sys.stdout = old_stdout

        # Compute reward
        reward, beach_frac, gyre_score = compute_reward(
            results['lon'], results['lat'], results['beached'], n_steps
        )

        # Update bandit
        bandit.update(month, reward)

        # Log
        training_log['episodes'].append(episode)
        training_log['months'].append(month)
        training_log['rewards'].append(reward)
        training_log['beach_fractions'].append(beach_frac)
        training_log['gyre_scores'].append(gyre_score)
        training_log['q_values'].append(bandit.Q.copy())
        training_log['visit_counts'].append(bandit.N.copy())

        # Progress
        if verbose and (episode + 1) % max(1, n_episodes // 20) == 0:
            pct = 100 * (episode + 1) / n_episodes
            best_month, best_q = bandit.get_best_month()
            print(f"  Episode {episode + 1}/{n_episodes} ({pct:.0f}%): "
                  f"month={month_names[month]}, reward={reward:.3f}, "
                  f"best_so_far={month_names[best_month]} (Q={best_q:.3f})")

    if verbose:
        print("\nTraining complete!")
        best_month, best_q = bandit.get_best_month()
        print(f"  Best month: {month_names[best_month]} (Q={best_q:.3f})")
        print(f"  Visit counts: {bandit.N}")

    return bandit, training_log


def run_best_month_simulation(bandit, n_particles=2000, n_steps=365,
                               mask_data=None, seed=None, verbose=True):
    """
    Run full simulation for the best learned month.

    Parameters
    ----------
    bandit : MonthBandit
        Trained bandit
    n_particles : int
        Number of particles (default 2000)
    n_steps : int
        Simulation steps (default 365)
    mask_data : tuple, optional
        Mask data
    seed : int, optional
        Random seed
    verbose : bool
        Print progress

    Returns
    -------
    results : dict
        Simulation results
    best_month : int
        Best month index
    """
    best_month, best_q = bandit.get_best_month()

    month_names = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]

    if verbose:
        print(f"\nRunning full simulation for best month: {month_names[best_month]}")
        print(f"  Q-value: {best_q:.3f}")
        print(f"  Particles: {n_particles}")
        print(f"  Steps: {n_steps}")

    # Generate particles
    lon_init, lat_init = scenarios.seed_nyc_spill(
        n_particles,
        jitter_km=15.0,
        seed=seed
    )

    # Set random seed
    if seed is not None:
        np.random.seed(seed)

    # Run simulation
    results = simulate.run_simulation(
        lon_init, lat_init,
        n_steps=n_steps,
        dt=1.0,
        save_every=1,
        mask_data=mask_data
    )

    # Compute metrics
    reward, beach_frac, gyre_score = compute_reward(
        results['lon'], results['lat'], results['beached'], n_steps
    )

    if verbose:
        print(f"\nBest month simulation metrics:")
        print(f"  Beach fraction: {beach_frac:.3f}")
        print(f"  Gyre time score: {gyre_score:.3f}")
        print(f"  Total reward: {reward:.3f}")

    # Add month info to results
    results['best_month'] = best_month
    results['best_month_name'] = month_names[best_month]
    results['metrics'] = {
        'reward': reward,
        'beach_fraction': beach_frac,
        'gyre_score': gyre_score,
    }

    return results, best_month


if __name__ == '__main__':
    # Quick test (very short for demo)
    print("Testing RL bandit (quick demo)...")

    # Need to load mask first
    import ocean_mask as om
    print("\nLoading mask...")
    grid_lon, grid_lat, ocean_mask = om.load_ocean_mask()
    coastal_band = om.compute_coastal_band(ocean_mask)
    mask_data = (grid_lon, grid_lat, ocean_mask, coastal_band)

    # Train for just 24 episodes (2 per month)
    bandit, log = train_bandit(
        n_episodes=24,
        particles_per_episode=200,
        n_steps=180,
        epsilon=0.3,
        mask_data=mask_data,
        seed=42,
        verbose=True
    )

    print("\nFinal Q-values:")
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for m, q in enumerate(bandit.Q):
        print(f"  {month_names[m]}: {q:.3f} (N={bandit.N[m]})")

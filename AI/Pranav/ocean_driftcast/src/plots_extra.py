"""
Extra plotting functions for NYC spill story and RL scheduler.

Includes KDE maps, seasonal heatmaps, Sankey diagrams, month grids, and more.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from scipy.stats import gaussian_kde
import scenarios

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False


def plot_path_kde(lon_history, lat_history, beached_history, output_path,
                  extent=(-100, 20, 0, 60), title='Path Density (KDE)'):
    """
    Create KDE heatmap of visited locations (excluding inland points).

    Parameters
    ----------
    lon_history : ndarray (n_times, n_particles)
        Longitude history
    lat_history : ndarray (n_times, n_particles)
        Latitude history
    beached_history : ndarray (n_times, n_particles)
        Beached status
    output_path : str
        Output file path
    extent : tuple
        Map extent
    title : str
        Plot title
    """
    print(f"Creating KDE path map: {output_path}")

    # Stack all positions from all timesteps (active particles only)
    all_lons = []
    all_lats = []

    for t in range(len(lon_history)):
        active = ~beached_history[t]
        all_lons.extend(lon_history[t, active])
        all_lats.extend(lat_history[t, active])

    all_lons = np.array(all_lons)
    all_lats = np.array(all_lats)

    print(f"  Total positions: {len(all_lons):,}")

    # Create KDE (subsample if too many points)
    if len(all_lons) > 50000:
        idx = np.random.choice(len(all_lons), 50000, replace=False)
        kde_lons = all_lons[idx]
        kde_lats = all_lats[idx]
    else:
        kde_lons = all_lons
        kde_lats = all_lats

    print(f"  Computing KDE on {len(kde_lons):,} points...")

    # Stack for KDE
    positions = np.vstack([kde_lons, kde_lats])
    kde = gaussian_kde(positions)

    # Evaluate on grid
    lon_grid = np.linspace(extent[0], extent[1], 200)
    lat_grid = np.linspace(extent[2], extent[3], 150)
    LON, LAT = np.meshgrid(lon_grid, lat_grid)
    grid_positions = np.vstack([LON.ravel(), LAT.ravel()])

    density = kde(grid_positions).reshape(LON.shape)

    # Plot
    if HAS_CARTOPY:
        fig = plt.figure(figsize=(14, 10))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_extent(extent, crs=ccrs.PlateCarree())

        # Density heatmap
        im = ax.contourf(LON, LAT, density, levels=20, cmap='YlOrRd',
                         transform=ccrs.PlateCarree(), alpha=0.8)

        # Coastlines
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black')
        ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.3)

        # Gridlines
        gl = ax.gridlines(draw_labels=True, linewidth=0.3, alpha=0.5)
        gl.top_labels = False
        gl.right_labels = False

        plt.colorbar(im, ax=ax, label='Density', shrink=0.8)
    else:
        fig, ax = plt.subplots(figsize=(14, 10))
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])

        im = ax.contourf(LON, LAT, density, levels=20, cmap='YlOrRd', alpha=0.8)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.grid(True, alpha=0.3)

        plt.colorbar(im, ax=ax, label='Density')

    ax.set_title(title, fontsize=16, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  Saved: {output_path}")


def plot_month_comparison_grid(monthly_results, output_path, extent=(-100, 20, 0, 60)):
    """
    Create 4x3 grid of final densities for 12 monthly releases.

    Parameters
    ----------
    monthly_results : list of dict
        List of 12 simulation results (one per month)
        Each dict has 'lon', 'lat', 'beached', 'month_name'
    output_path : str
        Output file path
    extent : tuple
        Map extent
    """
    print(f"Creating month comparison grid: {output_path}")

    fig, axes = plt.subplots(3, 4, figsize=(20, 14),
                             subplot_kw={'projection': ccrs.PlateCarree()} if HAS_CARTOPY else {})

    # Find global vmin/vmax for consistent colormap
    all_densities = []

    for result in monthly_results:
        lon_final = result['lon'][-1]
        lat_final = result['lat'][-1]
        beached_final = result['beached'][-1]
        active = ~beached_final

        if np.sum(active) > 0:
            # Create simple 2D histogram
            H, _, _ = np.histogram2d(
                lon_final[active], lat_final[active],
                bins=[40, 30],
                range=[[extent[0], extent[1]], [extent[2], extent[3]]]
            )
            all_densities.append(H)

    if all_densities:
        vmax = np.percentile(np.concatenate([d.ravel() for d in all_densities]), 95)
    else:
        vmax = 1

    # Plot each month
    for idx, result in enumerate(monthly_results):
        row = idx // 4
        col = idx % 4
        ax = axes[row, col]

        if HAS_CARTOPY:
            ax.set_extent(extent, crs=ccrs.PlateCarree())
            ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor='black')
            ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.5)
        else:
            ax.set_xlim(extent[0], extent[1])
            ax.set_ylim(extent[2], extent[3])

        # Get final state
        lon_final = result['lon'][-1]
        lat_final = result['lat'][-1]
        beached_final = result['beached'][-1]
        active = ~beached_final

        # Plot density
        if np.sum(active) > 0:
            H, xedges, yedges = np.histogram2d(
                lon_final[active], lat_final[active],
                bins=[40, 30],
                range=[[extent[0], extent[1]], [extent[2], extent[3]]]
            )

            if HAS_CARTOPY:
                im = ax.pcolormesh(xedges, yedges, H.T, cmap='Reds',
                                   vmin=0, vmax=vmax, alpha=0.7,
                                   transform=ccrs.PlateCarree())
            else:
                im = ax.pcolormesh(xedges, yedges, H.T, cmap='Reds',
                                   vmin=0, vmax=vmax, alpha=0.7)

        # Title
        ax.set_title(result['month_name'], fontsize=11, fontweight='bold')

        # Remove axis labels for cleaner look
        ax.set_xticks([])
        ax.set_yticks([])

    # Add colorbar
    fig.colorbar(im, ax=axes.ravel().tolist(), label='Particle Density',
                 shrink=0.8, pad=0.02)

    fig.suptitle('Monthly Release Comparison: End State Density',
                 fontsize=16, fontweight='bold', y=0.995)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  Saved: {output_path}")


def plot_first_passage_histograms(monthly_results, mask_data, output_path):
    """
    Plot histograms of first passage times to gyre and Europe.

    Parameters
    ----------
    monthly_results : list of dict
        Monthly simulation results
    mask_data : tuple
        (grid_lon, grid_lat, ocean_mask, coastal_band)
    output_path : str
        Output file path
    """
    print(f"Creating first passage histograms: {output_path}")

    grid_lon, grid_lat, ocean_mask, coastal_band = mask_data

    # Collect all first passage times
    all_gyre_times = []
    all_europe_times = []

    for result in monthly_results:
        # Gyre entry
        gyre_times = scenarios.compute_gyre_entry_time(
            result['lon'], result['lat'], result['beached']
        )
        valid_gyre = gyre_times[~np.isnan(gyre_times)]
        all_gyre_times.extend(valid_gyre)

        # Europe landfall
        europe_times = scenarios.compute_europe_landfall_time(
            result['lon'], result['lat'], result['beached'],
            grid_lon, grid_lat, coastal_band
        )
        valid_europe = europe_times[~np.isnan(europe_times)]
        all_europe_times.extend(valid_europe)

    all_gyre_times = np.array(all_gyre_times)
    all_europe_times = np.array(all_europe_times)

    # Plot
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Gyre entry histogram
    if len(all_gyre_times) > 0:
        ax1.hist(all_gyre_times, bins=30, color='steelblue', alpha=0.7, edgecolor='black')
        ax1.axvline(np.median(all_gyre_times), color='red', linestyle='--',
                    linewidth=2, label=f'Median: {np.median(all_gyre_times):.0f} days')
        ax1.set_xlabel('Time (days)', fontsize=12)
        ax1.set_ylabel('Count', fontsize=12)
        ax1.set_title('First Entry to Subtropical Gyre', fontsize=14, fontweight='bold')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

    # Europe landfall histogram
    if len(all_europe_times) > 0:
        ax2.hist(all_europe_times, bins=30, color='coral', alpha=0.7, edgecolor='black')
        ax2.axvline(np.median(all_europe_times), color='darkred', linestyle='--',
                    linewidth=2, label=f'Median: {np.median(all_europe_times):.0f} days')
        ax2.set_xlabel('Time (days)', fontsize=12)
        ax2.set_ylabel('Count', fontsize=12)
        ax2.set_title('First Landfall on European Coast', fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  Saved: {output_path}")
    print(f"    Gyre entries: {len(all_gyre_times)} ({100*len(all_gyre_times)/max(1, len(all_gyre_times) + 100):.1f}% entered)")
    print(f"    Europe landfalls: {len(all_europe_times)}")


def plot_rl_training_curve(training_log, output_path, window=20):
    """
    Plot RL training curve with rolling mean.

    Parameters
    ----------
    training_log : dict
        Training log from rl_env.train_bandit
    output_path : str
        Output file path
    window : int
        Rolling mean window size
    """
    print(f"Creating RL training curve: {output_path}")

    episodes = training_log['episodes']
    rewards = training_log['rewards']

    # Compute rolling mean
    rewards_array = np.array(rewards)
    rolling_mean = np.convolve(rewards_array, np.ones(window)/window, mode='valid')
    rolling_x = episodes[window-1:]

    # Plot
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(episodes, rewards, alpha=0.3, color='steelblue', label='Raw Reward')
    ax.plot(rolling_x, rolling_mean, linewidth=2, color='darkblue',
            label=f'Rolling Mean (window={window})')

    ax.set_xlabel('Episode', fontsize=12)
    ax.set_ylabel('Reward', fontsize=12)
    ax.set_title('RL Training Progress: Reward vs Episode', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  Saved: {output_path}")


def plot_rl_policy_bar(bandit, output_path):
    """
    Plot learned month preferences as bar chart.

    Parameters
    ----------
    bandit : MonthBandit
        Trained bandit
    output_path : str
        Output file path
    """
    print(f"Creating RL policy bar chart: {output_path}")

    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    # Get Q-values and visit counts
    q_values = bandit.Q
    visit_counts = bandit.N

    # Find best month
    best_month = np.argmax(q_values)

    # Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Q-values
    colors = ['gold' if i == best_month else 'steelblue' for i in range(12)]
    ax1.bar(month_names, q_values, color=colors, edgecolor='black', alpha=0.8)
    ax1.set_ylabel('Q-Value (Expected Reward)', fontsize=12)
    ax1.set_title('Learned Month Preferences', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')

    # Mark best
    ax1.scatter([best_month], [q_values[best_month]], s=200, c='red',
                marker='*', zorder=10, label='Best Month')
    ax1.legend(fontsize=11)

    # Visit counts
    ax2.bar(month_names, visit_counts, color='lightcoral', edgecolor='black', alpha=0.8)
    ax2.set_xlabel('Month', fontsize=12)
    ax2.set_ylabel('Visit Count', fontsize=12)
    ax2.set_title('Exploration Distribution', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  Saved: {output_path}")
    print(f"    Best month: {month_names[best_month]} (Q={q_values[best_month]:.3f})")


def plot_flow_sankey(lon_final, lat_final, beached_final, output_path):
    """
    Create simple Sankey diagram from source to outcome buckets.

    Uses horizontal bars instead of true Sankey (simpler implementation).

    Parameters
    ----------
    lon_final : ndarray
        Final longitudes
    lat_final : ndarray
        Final latitudes
    beached_final : ndarray (bool)
        Final beached status
    output_path : str
        Output file path
    """
    print(f"Creating flow Sankey: {output_path}")

    # Categorize endpoints
    categories, category_counts = scenarios.categorize_endpoints(
        lon_final, lat_final, beached_final
    )

    # Sort by count
    sorted_items = sorted(category_counts.items(), key=lambda x: -x[1])

    labels = []
    values = []
    colors = []

    color_map = {
        'at_sea': '#4a90e2',
        'beached_us_midatlantic': '#e74c3c',
        'beached_iberia': '#f39c12',
        'beached_biscay': '#9b59b6',
        'beached_skagerrak': '#1abc9c',
        'beached_azores': '#34495e',
        'beached_canaries': '#e67e22',
        'beached_other': '#95a5a6',
    }

    for cat, count in sorted_items:
        nice_name = cat.replace('_', ' ').title()
        labels.append(f'{nice_name}\n({count})')
        values.append(count)
        colors.append(color_map.get(cat, '#bdc3c7'))

    # Plot as horizontal bars
    fig, ax = plt.subplots(figsize=(12, 8))

    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, values, color=colors, edgecolor='black', alpha=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=11)
    ax.set_xlabel('Particle Count', fontsize=12)
    ax.set_title('Particle Fate: Source (NYC) to Outcomes', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, values)):
        ax.text(val + max(values)*0.01, i, f'{val}',
                va='center', fontsize=10, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  Saved: {output_path}")


def plot_winter_vs_summer(winter_result, summer_result, output_path, extent=(-100, 20, 0, 60)):
    """
    Side-by-side comparison of winter (DJF) vs summer (JJA) releases.

    Parameters
    ----------
    winter_result : dict
        Winter simulation results (Dec/Jan/Feb average)
    summer_result : dict
        Summer simulation results (Jun/Jul/Aug average)
    output_path : str
        Output file path
    extent : tuple
        Map extent
    """
    print(f"Creating winter vs summer comparison: {output_path}")

    if HAS_CARTOPY:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8),
                                       subplot_kw={'projection': ccrs.PlateCarree()})
    else:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

    for ax, result, season in [(ax1, winter_result, 'Winter (DJF)'),
                                (ax2, summer_result, 'Summer (JJA)')]:

        if HAS_CARTOPY:
            ax.set_extent(extent, crs=ccrs.PlateCarree())
            ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black')
            ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.5)
            gl = ax.gridlines(draw_labels=True, linewidth=0.3, alpha=0.5)
            gl.top_labels = False
            gl.right_labels = False
        else:
            ax.set_xlim(extent[0], extent[1])
            ax.set_ylim(extent[2], extent[3])
            ax.grid(True, alpha=0.3)

        # Plot final density
        lon_final = result['lon'][-1]
        lat_final = result['lat'][-1]
        beached_final = result['beached'][-1]
        active = ~beached_final

        if np.sum(active) > 0:
            if HAS_CARTOPY:
                ax.scatter(lon_final[active], lat_final[active], s=2, c='steelblue',
                          alpha=0.5, transform=ccrs.PlateCarree())
            else:
                ax.scatter(lon_final[active], lat_final[active], s=2, c='steelblue',
                          alpha=0.5)

        if np.sum(beached_final) > 0:
            if HAS_CARTOPY:
                ax.scatter(lon_final[beached_final], lat_final[beached_final],
                          s=1, c='coral', alpha=0.4, transform=ccrs.PlateCarree())
            else:
                ax.scatter(lon_final[beached_final], lat_final[beached_final],
                          s=1, c='coral', alpha=0.4)

        ax.set_title(f'{season} Release', fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  Saved: {output_path}")


def plot_gyre_core_zoom(lon_final, lat_final, beached_final, output_path):
    """
    Zoomed density plot of gyre core region (20-35N, 70-40W).

    Parameters
    ----------
    lon_final : ndarray
        Final longitudes
    lat_final : ndarray
        Final latitudes
    beached_final : ndarray (bool)
        Final beached status
    output_path : str
        Output file path
    """
    print(f"Creating gyre core zoom: {output_path}")

    # Gyre core extent
    extent = (-70, -40, 20, 35)

    # Filter particles in gyre region
    active = ~beached_final
    in_gyre = (
        (lon_final >= extent[0]) & (lon_final <= extent[1]) &
        (lat_final >= extent[2]) & (lat_final <= extent[3]) &
        active
    )

    if HAS_CARTOPY:
        fig = plt.figure(figsize=(12, 10))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.set_extent(extent, crs=ccrs.PlateCarree())

        ax.add_feature(cfeature.COASTLINE, linewidth=0.8, edgecolor='black')
        ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.5)

        gl = ax.gridlines(draw_labels=True, linewidth=0.5, alpha=0.5)
        gl.top_labels = False
        gl.right_labels = False

        if np.sum(in_gyre) > 0:
            ax.scatter(lon_final[in_gyre], lat_final[in_gyre],
                      s=3, c='darkblue', alpha=0.6, transform=ccrs.PlateCarree())
    else:
        fig, ax = plt.subplots(figsize=(12, 10))
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
        ax.grid(True, alpha=0.3)

        if np.sum(in_gyre) > 0:
            ax.scatter(lon_final[in_gyre], lat_final[in_gyre],
                      s=3, c='darkblue', alpha=0.6)

    ax.set_title(f'Subtropical Gyre Core Density\n{np.sum(in_gyre)} particles',
                fontsize=14, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()

    print(f"  Saved: {output_path}")


if __name__ == '__main__':
    print("Extra plotting functions loaded.")
    print("  - plot_path_kde")
    print("  - plot_month_comparison_grid")
    print("  - plot_first_passage_histograms")
    print("  - plot_rl_training_curve")
    print("  - plot_rl_policy_bar")
    print("  - plot_flow_sankey")
    print("  - plot_winter_vs_summer")
    print("  - plot_gyre_core_zoom")

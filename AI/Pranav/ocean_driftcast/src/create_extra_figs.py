"""
Generate extra visualization figures with improved legends.

Creates:
- legend_sample.png: Standalone legend for slides
- policy_value_heat.png: Value function heatmap
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import plotting_config as pc
import ocean_mask as om
import mdp

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False


def create_legend_sample(output_path='outputs/legend_sample.png'):
    """Create standalone legend sample for slides."""
    print(f"Creating legend sample: {output_path}")

    colors = pc.get_theme_colors('light')
    palette = pc.get_colorblind_palette('default')

    if HAS_CARTOPY:
        fig = plt.figure(figsize=(12, 8), facecolor=colors['bg'])
        ax = plt.axes(projection=ccrs.PlateCarree())
    else:
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.patch.set_facecolor(colors['bg'])

    extent = (-100, 20, 0, 60)

    # Setup map
    pc.setup_map_axes(ax, extent, theme='light', include_gridlines=True)

    # Create legend elements
    legend_elements = [
        Line2D([0], [0], marker='o', color='w',
               markerfacecolor=palette['active'],
               markeredgecolor='white',
               markersize=12, linewidth=0,
               label='Active Particles (at sea)'),
        Line2D([0], [0], marker='o', color='w',
               markerfacecolor=palette['beached'],
               markersize=12, linewidth=0,
               label='Beached Particles (coastal)'),
        Line2D([0], [0], color='gold', linewidth=3,
               linestyle='--', label='MDP Policy Path'),
        Line2D([0], [0], marker='>', color='#D4A017',
               markersize=10, linewidth=2,
               label='Policy Direction'),
    ]

    # Large legend
    legend = ax.legend(handles=legend_elements, loc='center',
                      fontsize=18, framealpha=0.95,
                      edgecolor='black', fancybox=True,
                      title='Ocean Drift Legend',
                      title_fontsize=20)
    legend.get_frame().set_facecolor('white')

    ax.set_title('Legend for North Atlantic Drift Visualizations',
                fontsize=24, fontweight='bold', pad=20,
                color=colors['text'])

    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches='tight',
               facecolor=colors['bg'])
    plt.close()

    print(f"  Saved: {output_path}")


def create_policy_value_heatmap(output_path='outputs/policy_value_heat.png'):
    """Create heatmap of MDP value function."""
    print(f"Creating policy value heatmap: {output_path}")

    # Load mask
    grid_lon, grid_lat, ocean_mask = om.load_ocean_mask()
    coastal_band = om.compute_coastal_band(ocean_mask)
    mask_data = (grid_lon, grid_lat, ocean_mask, coastal_band)

    # Build MDP
    print("  Building MDP policy...")
    mdp_grid = mdp.build_mdp_policy(dt_days=5.0, mask_data=mask_data, verbose=False)

    colors = pc.get_theme_colors('light')

    # Create figure
    if HAS_CARTOPY:
        fig = plt.figure(figsize=pc.FIGSIZE_LARGE, facecolor=colors['bg'])
        ax = plt.axes(projection=ccrs.PlateCarree())
        data_transform = ccrs.PlateCarree()
    else:
        fig, ax = plt.subplots(figsize=pc.FIGSIZE_LARGE)
        fig.patch.set_facecolor(colors['bg'])
        data_transform = None

    extent = (-100, 20, 0, 60)

    # Setup map
    pc.setup_map_axes(ax, extent, theme='light', include_gridlines=True)

    # Prepare value function for plotting
    V_plot = mdp_grid.V.copy()
    V_plot[~mdp_grid.ocean_mask] = np.nan  # Mask land

    # Plot value function as heatmap
    lon_edges = np.linspace(-100, 20, mdp_grid.n_lon + 1)
    lat_edges = np.linspace(0, 60, mdp_grid.n_lat + 1)

    if HAS_CARTOPY:
        mesh = ax.pcolormesh(lon_edges, lat_edges, V_plot.T,
                            cmap='cividis', alpha=0.7,
                            transform=data_transform,
                            vmin=np.nanpercentile(V_plot, 5),
                            vmax=np.nanpercentile(V_plot, 95))
    else:
        mesh = ax.pcolormesh(lon_edges, lat_edges, V_plot.T,
                            cmap='cividis', alpha=0.7,
                            vmin=np.nanpercentile(V_plot, 5),
                            vmax=np.nanpercentile(V_plot, 95))

    # Colorbar
    cbar = plt.colorbar(mesh, ax=ax, orientation='horizontal',
                       pad=0.05, shrink=0.8)
    cbar.set_label('Value Function V(s)', fontsize=14, fontweight='bold')

    ax.set_title('MDP Value Function - Preferred Drift Regions',
                fontsize=pc.TITLE_FONTSIZE,
                fontweight=pc.TITLE_FONTWEIGHT, pad=15,
                color=colors['text'])

    # Add info text
    text_str = (f"Higher values = policy prefers these regions\n"
                f"Grid: {mdp_grid.n_lon}×{mdp_grid.n_lat}, γ=0.995\n"
                f"Gyre core bonus visible as warm colors")
    ax.text(0.02, 0.02, text_str, transform=ax.transAxes,
           fontsize=10, verticalalignment='bottom',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
           color='black')

    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches='tight',
               facecolor=colors['bg'])
    plt.close()

    print(f"  Saved: {output_path}")


if __name__ == '__main__':
    print("Generating extra visualization figures...")
    print()

    os.makedirs('outputs', exist_ok=True)

    # Create figures
    create_legend_sample()
    print()

    create_policy_value_heatmap()
    print()

    print("All extra figures generated!")

"""
Generate specialized figures for documentation and presentations.

Creates legend samples, streamline plots, and other static visualizations.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.lines import Line2D
import plotting_config as pc

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False


def generate_legend_sample(output_path='outputs/legend_sample.png', theme='light'):
    """
    Generate standalone legend sample for slides/presentations.

    Parameters
    ----------
    output_path : str
        Output file path
    theme : str
        Color theme
    """
    print(f"Generating legend sample: {output_path}")

    colors = pc.get_theme_colors(theme)
    palette = pc.get_colorblind_palette('default')

    # Create minimal map
    extent = (-100, 20, 0, 60)

    if HAS_CARTOPY:
        fig = plt.figure(figsize=(12, 8), facecolor=colors['bg'])
        ax = plt.axes(projection=ccrs.PlateCarree())
    else:
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.patch.set_facecolor(colors['bg'])

    # Setup map
    pc.setup_map_axes(ax, extent, theme=theme, include_gridlines=True)

    # Create legend elements
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='Active Particles',
               markerfacecolor=palette['active'], markeredgecolor=pc.COLOR_ACTIVE_EDGE,
               markeredgewidth=pc.EDGE_WIDTH_ACTIVE, markersize=10,
               alpha=pc.ALPHA_ACTIVE, linestyle='none'),
        Line2D([0], [0], marker='o', color='w', label='Beached Particles',
               markerfacecolor=palette['beached'], markersize=8,
               alpha=pc.ALPHA_BEACHED, linestyle='none'),
    ]

    # Large, centered legend
    legend = ax.legend(handles=legend_elements, loc='center',
                      fontsize=16, framealpha=0.95,
                      edgecolor='black', fancybox=True,
                      shadow=True, title='Particle States',
                      title_fontsize=18)
    legend.get_frame().set_facecolor('white')

    ax.set_title('Legend Reference', fontsize=20, fontweight='bold',
                pad=20, color=colors['text'])

    plt.tight_layout()
    plt.savefig(output_path, dpi=pc.DPI_HIGH, bbox_inches='tight',
               facecolor=colors['bg'])
    plt.close()

    print(f"  Saved: {output_path}")


def generate_gyre_streamlines(output_path='outputs/gyre_streamlines.png',
                               theme='light', day_of_year=0):
    """
    Generate streamline plot of synthetic velocity field.

    Parameters
    ----------
    output_path : str
        Output file path
    theme : str
        Color theme
    day_of_year : float
        Day of year for seasonal field
    """
    print(f"Generating gyre streamlines: {output_path}")

    import flow

    colors = pc.get_theme_colors(theme)
    extent = (-100, 20, 0, 60)

    # Create velocity grid
    lon_grid = np.linspace(extent[0], extent[1], 150)
    lat_grid = np.linspace(extent[2], extent[3], 120)
    LON, LAT = np.meshgrid(lon_grid, lat_grid)

    # Compute velocities
    U = np.zeros_like(LON)
    V = np.zeros_like(LAT)

    for i in range(LON.shape[0]):
        for j in range(LON.shape[1]):
            u, v = flow.get_velocity(LON[i, j], LAT[i, j], day_of_year)
            # Add windage
            u_wind = flow.get_windage(LAT[i, j], day_of_year)
            U[i, j] = u + u_wind
            V[i, j] = v

    # Compute speed
    speed = np.sqrt(U**2 + V**2)

    # Create figure
    if HAS_CARTOPY:
        fig = plt.figure(figsize=pc.FIGSIZE_LARGE, facecolor=colors['bg'])
        ax = plt.axes(projection=ccrs.PlateCarree())
    else:
        fig, ax = plt.subplots(figsize=pc.FIGSIZE_LARGE)
        fig.patch.set_facecolor(colors['bg'])

    # Setup map
    pc.setup_map_axes(ax, extent, theme=theme, include_gridlines=True)

    # Streamlines colored by speed
    if HAS_CARTOPY:
        strm = ax.streamplot(LON, LAT, U, V, color=speed, cmap='viridis',
                            density=2.5, linewidth=1.5, arrowsize=1.5,
                            transform=ccrs.PlateCarree())
    else:
        strm = ax.streamplot(LON, LAT, U, V, color=speed, cmap='viridis',
                            density=2.5, linewidth=1.5, arrowsize=1.5)

    # Add gyre core marker
    gyre_lon, gyre_lat = -55.0, 30.0
    if HAS_CARTOPY:
        ax.plot(gyre_lon, gyre_lat, 'r*', markersize=20, markeredgecolor='white',
               markeredgewidth=2, label='Gyre Core', transform=ccrs.PlateCarree(),
               zorder=100)
    else:
        ax.plot(gyre_lon, gyre_lat, 'r*', markersize=20, markeredgecolor='white',
               markeredgewidth=2, label='Gyre Core', zorder=100)

    # Gulf Stream jet highlight (approximate)
    jet_lat = 36.0
    ax.axhline(jet_lat, color='orange', linestyle='--', linewidth=2,
              alpha=0.7, label='Gulf Stream Jet')

    # Colorbar
    cbar = plt.colorbar(strm.lines, ax=ax, fraction=0.03, pad=0.04, shrink=0.8)
    cbar.set_label('Current speed (°/day)', fontsize=pc.LABEL_FONTSIZE,
                   color=colors['text'])
    cbar.ax.tick_params(labelsize=pc.TICK_FONTSIZE, colors=colors['text'])

    # Legend
    legend = ax.legend(loc='lower left', fontsize=pc.LEGEND_FONTSIZE,
                      framealpha=pc.LEGEND_FRAMEALPHA,
                      edgecolor=pc.LEGEND_EDGECOLOR)
    legend.get_frame().set_facecolor(pc.LEGEND_FACECOLOR)

    season_name = "Winter" if day_of_year < 90 or day_of_year > 270 else "Summer"
    ax.set_title(f'Synthetic North Atlantic Circulation ({season_name}, Day {day_of_year:.0f})',
                fontsize=pc.TITLE_FONTSIZE, fontweight=pc.TITLE_FONTWEIGHT,
                pad=15, color=colors['text'])

    plt.tight_layout()
    plt.savefig(output_path, dpi=pc.DPI_HIGH, bbox_inches='tight',
               facecolor=colors['bg'])
    plt.close()

    print(f"  Saved: {output_path}")


def generate_coast_hits_by_region(categories, category_counts, output_path='outputs/coast_hits_by_region.png',
                                   theme='light'):
    """
    Generate bar chart of coastal landfall by region.

    Parameters
    ----------
    categories : ndarray
        Category labels for each particle
    category_counts : dict
        Counts by category
    output_path : str
        Output file path
    theme : str
        Color theme
    """
    print(f"Generating coast hits by region: {output_path}")

    colors = pc.get_theme_colors(theme)

    # Filter to only beached categories
    beached_categories = {k: v for k, v in category_counts.items()
                          if k.startswith('beached_') and k != 'beached_other'}

    if not beached_categories:
        print("  No beached particles to plot")
        return

    # Sort by count descending
    sorted_items = sorted(beached_categories.items(), key=lambda x: -x[1])

    labels = []
    values = []
    for cat, count in sorted_items:
        nice_name = cat.replace('beached_', '').replace('_', ' ').title()
        labels.append(nice_name)
        values.append(count)

    # Create figure
    fig, ax = plt.subplots(figsize=pc.FIGSIZE_MEDIUM)
    fig.patch.set_facecolor(colors['bg'])

    # Horizontal bar chart
    y_pos = np.arange(len(labels))
    bars = ax.barh(y_pos, values, color='steelblue', edgecolor='black', alpha=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=pc.LABEL_FONTSIZE, color=colors['text'])
    ax.set_xlabel('Particle Count', fontsize=pc.LABEL_FONTSIZE, color=colors['text'])
    ax.set_title('Coastal Landfall by Region', fontsize=pc.TITLE_FONTSIZE,
                fontweight=pc.TITLE_FONTWEIGHT, color=colors['text'])

    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, values)):
        ax.text(val + max(values)*0.01, i, f'{val}',
               va='center', fontsize=10, fontweight='bold', color=colors['text'])

    ax.grid(True, alpha=0.3, axis='x', color=colors['grid'])
    ax.set_facecolor(colors['bg'])
    ax.tick_params(colors=colors['text'])

    plt.tight_layout()
    plt.savefig(output_path, dpi=pc.DPI_HIGH, bbox_inches='tight',
               facecolor=colors['bg'])
    plt.close()

    print(f"  Saved: {output_path}")


if __name__ == '__main__':
    import os
    os.makedirs('outputs', exist_ok=True)

    print("Generating specialized figures...")
    print()

    generate_legend_sample()
    print()

    generate_gyre_streamlines(day_of_year=0)  # Winter
    print()

    # Example coast hits (would normally come from simulation)
    from scenarios import categorize_endpoints
    print("  (coast_hits_by_region requires simulation data - skipping standalone test)")
    print()

    print("Done!")

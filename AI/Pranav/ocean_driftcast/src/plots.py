"""
Professional plotting utilities for density maps and visualizations.

Updated with publication-ready styling, colorblind-safe palettes, and proper legends.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
import plotting_config as pc

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    HAS_CARTOPY = True
except ImportError:
    HAS_CARTOPY = False


def create_base_map(ax=None, extent=(-100, 20, 0, 60), theme='light'):
    """
    Create professional base map for North Atlantic.

    Parameters
    ----------
    ax : matplotlib axis, optional
        Axis to plot on
    extent : tuple
        Map extent (lon_min, lon_max, lat_min, lat_max)
    theme : str
        Color theme ('light', 'dark', or 'high_contrast')

    Returns
    -------
    ax : matplotlib axis
    """
    colors = pc.get_theme_colors(theme)

    if ax is None:
        if HAS_CARTOPY:
            fig = plt.figure(figsize=pc.FIGSIZE_LARGE, facecolor=colors['bg'])
            ax = plt.axes(projection=ccrs.PlateCarree())
        else:
            fig, ax = plt.subplots(figsize=pc.FIGSIZE_LARGE)
            fig.patch.set_facecolor(colors['bg'])

    if HAS_CARTOPY:
        ax.set_extent(extent, crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.LAND, facecolor=colors['land'],
                      edgecolor=pc.LAND_EDGECOLOR, zorder=1)
        ax.add_feature(cfeature.COASTLINE, linewidth=pc.COAST_LINEWIDTH,
                      edgecolor=colors['coast'], zorder=3)

        ax.set_facecolor(colors['ocean'])

        gl = ax.gridlines(draw_labels=True, linewidth=pc.GRID_LINEWIDTH,
                         alpha=pc.GRID_ALPHA, color=colors['grid'],
                         linestyle=pc.GRID_LINESTYLE)
        gl.top_labels = False
        gl.right_labels = False
    else:
        ax.set_xlim(extent[0], extent[1])
        ax.set_ylim(extent[2], extent[3])
        ax.set_xlabel('Longitude', fontsize=pc.LABEL_FONTSIZE, color=colors['text'])
        ax.set_ylabel('Latitude', fontsize=pc.LABEL_FONTSIZE, color=colors['text'])
        ax.set_facecolor(colors['ocean'])
        ax.grid(True, alpha=pc.GRID_ALPHA, color=colors['grid'],
               linestyle=pc.GRID_LINESTYLE, linewidth=pc.GRID_LINEWIDTH)
        ax.tick_params(colors=colors['text'])

    return ax


def plot_density_map(lon, lat, beached=None, output_path='density.png',
                     title='Particle Density', bins=120, extent=(-100, 20, 0, 60),
                     exclude_beached=False, theme='light', colorblind_safe=True,
                     save_mobile=False):
    """
    Create professional density heatmap of particle positions.

    Parameters
    ----------
    lon : ndarray
        Longitudes
    lat : ndarray
        Latitudes
    beached : ndarray (bool), optional
        Beached status
    output_path : str
        Output file path
    title : str
        Plot title
    bins : int
        Number of bins for 2D histogram
    extent : tuple
        Map extent
    exclude_beached : bool
        If True, exclude beached particles from density
    theme : str
        Color theme
    colorblind_safe : bool
        Use colorblind-safe colormap
    save_mobile : bool
        Also save a 720p mobile version
    """
    print(f"Creating density map: {output_path}")

    colors = pc.get_theme_colors(theme)

    # Filter particles
    if beached is not None:
        if exclude_beached:
            active = ~beached
            lon = lon[active]
            lat = lat[active]
            print(f"  Using {len(lon):,} active particles (excluding beached)")
        else:
            print(f"  Using {len(lon):,} particles (active + beached)")
    else:
        print(f"  Using {len(lon):,} particles")

    # Create figure
    if HAS_CARTOPY:
        fig = plt.figure(figsize=pc.FIGSIZE_LARGE, facecolor=colors['bg'])
        ax = plt.axes(projection=ccrs.PlateCarree())
        data_transform = ccrs.PlateCarree()
    else:
        fig, ax = plt.subplots(figsize=pc.FIGSIZE_LARGE)
        fig.patch.set_facecolor(colors['bg'])
        data_transform = None

    # Create 2D histogram
    lon_edges = np.linspace(extent[0], extent[1], bins)
    lat_edges = np.linspace(extent[2], extent[3], bins)
    H, xedges, yedges = np.histogram2d(lon, lat, bins=[lon_edges, lat_edges])

    # Smooth slightly
    try:
        from scipy.ndimage import gaussian_filter
        H = gaussian_filter(H, sigma=1.2)
    except ImportError:
        pass

    # Mask zeros
    H = np.ma.masked_where(H == 0, H)

    # Colormap
    if colorblind_safe:
        cmap = plt.cm.get_cmap(pc.CMAP_DENSITY)
    else:
        # Custom colormap
        custom_colors = ['#08306b', '#2171b5', '#6baed6', '#c6dbef',
                        '#fee090', '#fc8d59', '#d73027']
        cmap = LinearSegmentedColormap.from_list('density', custom_colors)

    cmap.set_bad(color='none')  # Transparent for zeros

    # Plot density
    if HAS_CARTOPY:
        im = ax.pcolormesh(xedges, yedges, H.T, cmap=cmap,
                          transform=data_transform, alpha=0.75,
                          vmin=np.percentile(H[H>0], 1),
                          vmax=np.percentile(H[H>0], 99))
    else:
        im = ax.pcolormesh(xedges, yedges, H.T, cmap=cmap, alpha=0.75,
                          vmin=np.percentile(H[H>0], 1),
                          vmax=np.percentile(H[H>0], 99))

    # Setup map
    pc.setup_map_axes(ax, extent, theme=theme, include_gridlines=True)

    # Colorbar with proper label
    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.04, shrink=0.8)
    cbar.set_label('Particle density (arb.)', fontsize=pc.LABEL_FONTSIZE,
                   color=colors['text'])
    cbar.ax.tick_params(labelsize=pc.TICK_FONTSIZE, colors=colors['text'])

    ax.set_title(title, fontsize=pc.TITLE_FONTSIZE, fontweight=pc.TITLE_FONTWEIGHT,
                pad=15, color=colors['text'])

    plt.tight_layout()
    plt.savefig(output_path, dpi=pc.DPI_HIGH, bbox_inches='tight',
               facecolor=colors['bg'])

    # Save mobile version
    if save_mobile:
        mobile_path = output_path.replace('.png', '_mobile.png')
        plt.savefig(mobile_path, dpi=pc.DPI_MOBILE, bbox_inches='tight',
                   facecolor=colors['bg'])
        print(f"  Saved mobile: {mobile_path}")

    plt.close()

    print(f"  Saved: {output_path}")


def plot_trajectories(lon_history, lat_history, beached_history,
                      output_path='trajectories.png', n_sample=500,
                      extent=(-100, 20, 0, 60), theme='light', save_mobile=False):
    """
    Plot sample trajectories with professional styling.

    Parameters
    ----------
    lon_history : ndarray (n_times, n_particles)
        Longitude history
    lat_history : ndarray (n_times, n_particles)
        Latitude history
    beached_history : ndarray (n_times, n_particles)
        Beached status history
    output_path : str
        Output file path
    n_sample : int
        Number of trajectories to plot
    extent : tuple
        Map extent
    theme : str
        Color theme
    save_mobile : bool
        Also save 720p version
    """
    print(f"Creating trajectory plot: {output_path}")

    colors = pc.get_theme_colors(theme)
    palette = pc.get_colorblind_palette('default')

    n_times, n_particles = lon_history.shape

    # Sample particles
    if n_particles > n_sample:
        idx = np.random.choice(n_particles, n_sample, replace=False)
    else:
        idx = np.arange(n_particles)

    # Create figure
    if HAS_CARTOPY:
        fig = plt.figure(figsize=pc.FIGSIZE_LARGE, facecolor=colors['bg'])
        ax = plt.axes(projection=ccrs.PlateCarree())
        data_transform = ccrs.PlateCarree()
    else:
        fig, ax = plt.subplots(figsize=pc.FIGSIZE_LARGE)
        fig.patch.set_facecolor(colors['bg'])
        data_transform = None

    # Plot trajectories
    for i in idx:
        lon_traj = lon_history[:, i]
        lat_traj = lat_history[:, i]
        beached_traj = beached_history[:, i]

        # Find beaching time
        beached_idx = np.where(beached_traj)[0]
        if len(beached_idx) > 0:
            end_idx = beached_idx[0] + 1
            alpha = 0.25
            color = palette['beached']
        else:
            end_idx = n_times
            alpha = 0.4
            color = palette['active']

        if HAS_CARTOPY:
            ax.plot(lon_traj[:end_idx], lat_traj[:end_idx],
                   color=color, alpha=alpha, linewidth=0.6,
                   transform=data_transform)
        else:
            ax.plot(lon_traj[:end_idx], lat_traj[:end_idx],
                   color=color, alpha=alpha, linewidth=0.6)

    # Setup map
    pc.setup_map_axes(ax, extent, theme=theme, include_gridlines=True)

    ax.set_title(f'Particle Trajectories (n={len(idx)})',
                fontsize=pc.TITLE_FONTSIZE, fontweight=pc.TITLE_FONTWEIGHT,
                pad=15, color=colors['text'])

    # Professional legend (positioned to avoid data)
    legend_elements = [
        Line2D([0], [0], color=palette['active'], alpha=0.4, linewidth=2,
               label='Active'),
        Line2D([0], [0], color=palette['beached'], alpha=0.25, linewidth=2,
               label='Beached')
    ]
    legend = ax.legend(handles=legend_elements, loc=pc.LEGEND_LOC,
                      fontsize=pc.LEGEND_FONTSIZE, framealpha=pc.LEGEND_FRAMEALPHA,
                      edgecolor=pc.LEGEND_EDGECOLOR)
    legend.get_frame().set_facecolor(pc.LEGEND_FACECOLOR)

    plt.tight_layout()
    plt.savefig(output_path, dpi=pc.DPI_HIGH, bbox_inches='tight',
               facecolor=colors['bg'])

    if save_mobile:
        mobile_path = output_path.replace('.png', '_mobile.png')
        plt.savefig(mobile_path, dpi=pc.DPI_MOBILE, bbox_inches='tight',
                   facecolor=colors['bg'])
        print(f"  Saved mobile: {mobile_path}")

    plt.close()

    print(f"  Saved: {output_path}")


def plot_particle_snapshot(lon, lat, beached, output_path='snapshot.png',
                           title='Particle Distribution', extent=(-100, 20, 0, 60),
                           theme='light', colorblind_style='default',
                           show_legend=True, save_mobile=False):
    """
    Plot single-frame particle snapshot with professional styling.

    Parameters
    ----------
    lon : ndarray
        Particle longitudes
    lat : ndarray
        Particle latitudes
    beached : ndarray (bool)
        Beached status
    output_path : str
        Output file path
    title : str
        Plot title
    extent : tuple
        Map extent
    theme : str
        Color theme
    colorblind_style : str
        Colorblind palette style
    show_legend : bool
        Whether to show legend
    save_mobile : bool
        Also save 720p version
    """
    print(f"Creating particle snapshot: {output_path}")

    colors = pc.get_theme_colors(theme)
    palette = pc.get_colorblind_palette(colorblind_style)

    # Create figure
    if HAS_CARTOPY:
        fig = plt.figure(figsize=pc.FIGSIZE_LARGE, facecolor=colors['bg'])
        ax = plt.axes(projection=ccrs.PlateCarree())
        data_transform = ccrs.PlateCarree()
    else:
        fig, ax = plt.subplots(figsize=pc.FIGSIZE_LARGE)
        fig.patch.set_facecolor(colors['bg'])
        data_transform = None

    # Setup map first
    pc.setup_map_axes(ax, extent, theme=theme, include_gridlines=True)

    # Separate active and beached
    active = ~beached

    # Adaptive marker sizing
    n_active = np.sum(active)
    n_beached = np.sum(beached)

    size_active = pc.adaptive_marker_size(n_active)
    size_beached = pc.MARKER_SIZE_BEACHED

    # Plot beached particles first (background)
    if n_beached > 0:
        if HAS_CARTOPY:
            ax.scatter(lon[beached], lat[beached], s=size_beached,
                      c=palette['beached'], alpha=pc.ALPHA_BEACHED,
                      edgecolors='none', zorder=4,
                      transform=data_transform,
                      label=f'Beached ({n_beached:,})')
        else:
            ax.scatter(lon[beached], lat[beached], s=size_beached,
                      c=palette['beached'], alpha=pc.ALPHA_BEACHED,
                      edgecolors='none', zorder=4,
                      label=f'Beached ({n_beached:,})')

    # Plot active particles on top
    if n_active > 0:
        if HAS_CARTOPY:
            ax.scatter(lon[active], lat[active], s=size_active,
                      c=palette['active'], alpha=pc.ALPHA_ACTIVE,
                      edgecolors=pc.COLOR_ACTIVE_EDGE,
                      linewidths=pc.EDGE_WIDTH_ACTIVE, zorder=5,
                      transform=data_transform,
                      label=f'Active ({n_active:,})')
        else:
            ax.scatter(lon[active], lat[active], s=size_active,
                      c=palette['active'], alpha=pc.ALPHA_ACTIVE,
                      edgecolors=pc.COLOR_ACTIVE_EDGE,
                      linewidths=pc.EDGE_WIDTH_ACTIVE, zorder=5,
                      label=f'Active ({n_active:,})')

    ax.set_title(title, fontsize=pc.TITLE_FONTSIZE,
                fontweight=pc.TITLE_FONTWEIGHT, pad=15,
                color=colors['text'])

    # Professional legend
    if show_legend:
        legend = ax.legend(loc=pc.LEGEND_LOC, fontsize=pc.LEGEND_FONTSIZE,
                          framealpha=pc.LEGEND_FRAMEALPHA,
                          edgecolor=pc.LEGEND_EDGECOLOR,
                          markerscale=pc.LEGEND_MARKERSCALE)
        legend.get_frame().set_facecolor(pc.LEGEND_FACECOLOR)

    plt.tight_layout()
    plt.savefig(output_path, dpi=pc.DPI_HIGH, bbox_inches='tight',
               facecolor=colors['bg'])

    if save_mobile:
        mobile_path = output_path.replace('.png', '_mobile.png')
        plt.savefig(mobile_path, dpi=pc.DPI_MOBILE, bbox_inches='tight',
                   facecolor=colors['bg'])
        print(f"  Saved mobile: {mobile_path}")

    plt.close()

    print(f"  Saved: {output_path}")


def plot_policy_arrows(policy_lon, policy_lat, mdp_grid, output_path='policy_arrows.png',
                       title='MDP Policy Path', extent=(-100, 20, 0, 60),
                       theme='light', cadence=10):
    """
    Plot MDP policy path as arrows on a map.

    Parameters
    ----------
    policy_lon : ndarray
        Policy path longitudes
    policy_lat : ndarray
        Policy path latitudes
    mdp_grid : mdp.MDPGrid
        MDP grid object with policy
    output_path : str
        Output file path
    title : str
        Plot title
    extent : tuple
        Map extent
    theme : str
        Color theme
    cadence : int
        Show arrows every N waypoints (for clarity)
    """
    print(f"Creating policy arrows plot: {output_path}")

    colors = pc.get_theme_colors(theme)

    # Create figure
    if HAS_CARTOPY:
        fig = plt.figure(figsize=pc.FIGSIZE_LARGE, facecolor=colors['bg'])
        ax = plt.axes(projection=ccrs.PlateCarree())
        data_transform = ccrs.PlateCarree()
    else:
        fig, ax = plt.subplots(figsize=pc.FIGSIZE_LARGE)
        fig.patch.set_facecolor(colors['bg'])
        data_transform = None

    # Setup map
    pc.setup_map_axes(ax, extent, theme=theme, include_gridlines=True)

    # Plot policy path as a line
    if HAS_CARTOPY:
        ax.plot(policy_lon, policy_lat, color='gold', alpha=0.6, linewidth=2.0,
               linestyle='--', transform=data_transform, zorder=10,
               label='Policy Path')
    else:
        ax.plot(policy_lon, policy_lat, color='gold', alpha=0.6, linewidth=2.0,
               linestyle='--', zorder=10, label='Policy Path')

    # Plot arrows at intervals
    arrow_color = '#D4A017'  # Desaturated yellow/gold
    arrow_width = 1.5

    for idx in range(0, len(policy_lon) - 1, cadence):
        lon_start = policy_lon[idx]
        lat_start = policy_lat[idx]
        lon_end = policy_lon[idx + 1]
        lat_end = policy_lat[idx + 1]

        dx = lon_end - lon_start
        dy = lat_end - lat_start

        if HAS_CARTOPY:
            ax.arrow(lon_start, lat_start, dx, dy,
                    head_width=0.5, head_length=0.3,
                    fc=arrow_color, ec=arrow_color, alpha=0.75,
                    linewidth=arrow_width, zorder=11,
                    transform=data_transform)
        else:
            ax.arrow(lon_start, lat_start, dx, dy,
                    head_width=0.5, head_length=0.3,
                    fc=arrow_color, ec=arrow_color, alpha=0.75,
                    linewidth=arrow_width, zorder=11)

    # Mark start and end
    if HAS_CARTOPY:
        ax.scatter([policy_lon[0]], [policy_lat[0]], s=100, c='lime',
                  edgecolors='white', linewidths=2, zorder=12,
                  transform=data_transform, label='Start')
        ax.scatter([policy_lon[-1]], [policy_lat[-1]], s=100, c='red',
                  edgecolors='white', linewidths=2, zorder=12,
                  transform=data_transform, label='End')
    else:
        ax.scatter([policy_lon[0]], [policy_lat[0]], s=100, c='lime',
                  edgecolors='white', linewidths=2, zorder=12, label='Start')
        ax.scatter([policy_lon[-1]], [policy_lat[-1]], s=100, c='red',
                  edgecolors='white', linewidths=2, zorder=12, label='End')

    ax.set_title(title, fontsize=pc.TITLE_FONTSIZE,
                fontweight=pc.TITLE_FONTWEIGHT, pad=15,
                color=colors['text'])

    # Add MDP info text
    text_str = (f"MDP: value iteration on {mdp_grid.n_lon}×{mdp_grid.n_lat} grid\n"
                f"Actions: {mdp_grid.n_actions}, γ={mdp_grid.cell_size}°")
    ax.text(0.02, 0.98, text_str, transform=ax.transAxes,
           fontsize=9, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7),
           color='black')

    # Legend
    legend = ax.legend(loc='lower right', fontsize=pc.LEGEND_FONTSIZE,
                      framealpha=pc.LEGEND_FRAMEALPHA,
                      edgecolor=pc.LEGEND_EDGECOLOR)
    legend.get_frame().set_facecolor(pc.LEGEND_FACECOLOR)

    plt.tight_layout()
    plt.savefig(output_path, dpi=pc.DPI_HIGH, bbox_inches='tight',
               facecolor=colors['bg'])
    plt.close()

    print(f"  Saved: {output_path}")


if __name__ == '__main__':
    print("Professional plotting utilities loaded.")
    print(f"  Cartopy available: {HAS_CARTOPY}")
    print(f"  High DPI: {pc.DPI_HIGH}")
    print(f"  Default theme: light")
